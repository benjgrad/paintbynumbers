import logging
import cv2
import numpy as np
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models.upload import Upload, ProcessingStatus
from .job_queue import JobQueue
from sklearn.cluster import MeanShift, estimate_bandwidth
import matplotlib.pyplot as plt
from scipy import ndimage
import random
from pillow_heif import register_heif_opener
from PIL import Image
import io

# Register HEIF opener with Pillow
register_heif_opener()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Use synchronous SQLite URL for the worker
SYNC_DATABASE_URL = "sqlite:///uploads.db"

def resize_image(image, target_width=2048):
    """Resize image to target width while maintaining aspect ratio if image is smaller"""
    height, width = image.shape[:2]
    
    # Always resize to target width for consistent processing time
    scale = target_width / width
    new_width = int(target_width)
    new_height = int(height * scale)
    return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)

def create_filled_version(segments_smoothed, unique_colors, h, w, min_area):
    """Create a filled version of the paint by numbers"""
    filled_image = np.zeros((h, w, 3), dtype=np.uint8)
    filled_image.fill(255)  # Start with white background
    
    # Fill each region with its color, but only if it passes size threshold
    for color_idx, color in enumerate(unique_colors):
        # Create binary mask for this color
        mask = (segments_smoothed == color_idx).astype(np.uint8)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter small regions
        valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
        
        # Create mask from valid contours
        valid_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.drawContours(valid_mask, valid_contours, -1, 1, -1)  # Fill contours
        
        # Only fill regions that pass the size threshold
        filled_image[valid_mask == 1] = color
    
    return filled_image

def create_paint_by_numbers(image, n_colors=20):
    """Convert image to paint by numbers style"""
    logger.info("Starting paint by numbers conversion")
    
    # Get original dimensions for final output
    original_h, original_w = image.shape[:2]
    
    # For high resolution output, target 4K width if the original is larger
    target_width = min(3840, max(2048, original_w))  # Never go below 2K, cap at 4K
    
    # Calculate processing width - use 2K for consistent processing time
    process_width = 2048
    
    # Resize image to processing size
    image = resize_image(image, target_width=process_width)
    
    # Convert to RGB for better color processing
    if len(image.shape) == 2:  # Grayscale
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    elif image.shape[2] == 3:  # BGR
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    h, w = image.shape[:2]
    
    # Apply Gaussian blur with adaptive kernel size
    logger.debug("Applying Gaussian blur")
    kernel_size = max(3, int(w / 100))  # Adaptive kernel size based on width
    if kernel_size % 2 == 0:  # Ensure kernel size is odd
        kernel_size += 1
    sigma = kernel_size / 3  # Proportional sigma
    image = cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma)
    
    # Step 1: Downscale for faster processing
    process_width = 1024  # Process at lower resolution
    scale = process_width / w
    process_height = int(h * scale)
    small_image = cv2.resize(image, (process_width, process_height), interpolation=cv2.INTER_AREA)
    
    # Apply bilateral filtering with reduced parameters
    logger.debug("Applying bilateral filtering")
    d = 9  # Fixed smaller diameter
    sigma_color = 50  # Reduced from 75
    sigma_space = 50  # Reduced from 75
    filtered = cv2.bilateralFilter(small_image, d=d, sigmaColor=sigma_color, sigmaSpace=sigma_space)
    
    # Step 2: Mean Shift Segmentation on downscaled image
    logger.debug("Performing mean shift segmentation")
    flat_image = filtered.reshape((-1, 3))
    
    # Use fixed bandwidth and reduced samples for faster processing
    bandwidth = 0.8  # Fixed bandwidth instead of estimation
    
    # Use KMeans directly instead of Mean Shift for faster processing
    from sklearn.cluster import KMeans
    kmeans = KMeans(n_clusters=n_colors, random_state=42, max_iter=100)
    labels = kmeans.fit_predict(flat_image)
    unique_colors = np.uint8(kmeans.cluster_centers_)
    
    # Upscale the labels back to target size
    labels_image = labels.reshape(process_height, process_width)
    labels = cv2.resize(labels_image.astype(np.float32), (w, h), 
                       interpolation=cv2.INTER_NEAREST).astype(np.int32)
    
    # Step 3: Create edge mask using adaptive thresholding
    logger.debug("Creating edge mask")
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                cv2.THRESH_BINARY, 9, 2)
    
    # Step 4: Simplified morphological operations
    logger.debug("Applying morphological operations")
    kernel = np.ones((3, 3), np.uint8)  # Fixed small kernel
    
    # Reshape labels back to image dimensions
    segments = labels
    
    # Apply median filter to remove noise
    segments_smoothed = ndimage.median_filter(segments, size=3)
    
    # Calculate minimum area threshold
    min_area = (w * h) // 50000  # Increased divisor for fewer small regions
    
    # Step 5: Create outline image
    logger.debug("Creating outlines")
    outline_image = np.zeros((h, w, 3), dtype=np.uint8)
    outline_image.fill(255)  # White background
    
    # Create filled version with only valid regions
    filled_image = create_filled_version(segments_smoothed, unique_colors, h, w, min_area)
    
    # Draw region boundaries
    for color_idx in range(len(unique_colors)):
        mask = (segments_smoothed == color_idx).astype(np.uint8)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter small regions
        contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
        
        # Draw contours with thin lines
        cv2.drawContours(outline_image, contours, -1, (0, 0, 0), 1)
        cv2.drawContours(filled_image, contours, -1, (0, 0, 0), 1)
        
        # Add numbers to regions
        for contour in contours:
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                
                # Calculate adaptive font scale based on image width
                base_font_scale = 0.4  # Increased base font size from 0.3
                font_scale = max(base_font_scale, (target_width / 2048) * base_font_scale)  # Scale up with resolution
                
                # Draw number with white background for better visibility
                number = str(color_idx + 1)
                font = cv2.FONT_HERSHEY_SIMPLEX
                thickness = max(1, int(target_width / 2048))  # Adaptive thickness
                
                # Get text size
                (text_width, text_height), _ = cv2.getTextSize(number, font, font_scale, thickness)
                
                # Draw white background rectangle with increased padding
                padding = max(2, int(target_width / 640))  # Adaptive padding
                
                # Add numbers to both versions
                for target_image in [outline_image, filled_image]:
                    cv2.rectangle(target_image, 
                                (cX - text_width//2 - padding, cY - text_height//2 - padding),
                                (cX + text_width//2 + padding, cY + text_height//2 + padding),
                                (255, 255, 255), -1)
                    cv2.putText(target_image, number, (cX - text_width//2, cY + text_height//2),
                              font, font_scale, (0, 0, 0), thickness)
    
    # Calculate final dimensions maintaining aspect ratio
    final_scale = target_width / original_w
    final_width = int(target_width)
    final_height = int(original_h * final_scale)
    
    # Ensure minimum size for visibility
    final_width = max(3840, final_width)
    final_height = max(int(3840 * (original_h / original_w)), final_height)
    
    # Upscale both versions to final resolution with appropriate interpolation
    outline_image = cv2.resize(outline_image, (final_width, final_height), interpolation=cv2.INTER_LANCZOS4)
    filled_image = cv2.resize(filled_image, (final_width, final_height), interpolation=cv2.INTER_LANCZOS4)
    
    # Redraw contours at high resolution for sharpness
    for color_idx in range(len(unique_colors)):
        mask = cv2.resize((segments_smoothed == color_idx).astype(np.uint8), 
                         (final_width, final_height), 
                         interpolation=cv2.INTER_NEAREST)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter small regions using scaled min_area
        scaled_min_area = (final_width * final_height) // 50000
        contours = [cnt for cnt in contours if cv2.contourArea(cnt) > scaled_min_area]
        
        # Draw sharp contours
        cv2.drawContours(outline_image, contours, -1, (0, 0, 0), max(1, int(final_width / 2048)))
        cv2.drawContours(filled_image, contours, -1, (0, 0, 0), max(1, int(final_width / 2048)))
        
        # Add numbers with proper scaling
        for contour in contours:
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                
                # Calculate font scale based on final resolution
                base_font_scale = 0.4  # Increased base size
                font_scale = max(base_font_scale, (final_width / 2048) * base_font_scale)
                
                number = str(color_idx + 1)
                font = cv2.FONT_HERSHEY_SIMPLEX
                thickness = max(1, int(final_width / 1024))  # Thicker font for visibility
                
                # Get text size
                (text_width, text_height), _ = cv2.getTextSize(number, font, font_scale, thickness)
                
                # Increased padding for better visibility
                padding = max(2, int(final_width / 512))
                
                # Add numbers to both versions with white background
                for target_image in [outline_image, filled_image]:
                    cv2.rectangle(target_image, 
                                (cX - text_width//2 - padding, cY - text_height//2 - padding),
                                (cX + text_width//2 + padding, cY + text_height//2 + padding),
                                (255, 255, 255), -1)
                    cv2.putText(target_image, number, (cX - text_width//2, cY + text_height//2),
                              font, font_scale, (0, 0, 0), thickness)
    
    # Create color palette reference at new size with larger height
    palette_height = int(final_height * 0.08)  # Increased from 0.05 for better visibility
    palette = np.zeros((palette_height, final_width, 3), dtype=np.uint8)
    palette.fill(255)
    
    # Calculate width for each color in palette
    n_unique_colors = len(unique_colors)
    color_width = final_width // n_unique_colors
    
    # Draw palette with larger numbers
    for i, color in enumerate(unique_colors):
        x1 = i * color_width
        x2 = (i + 1) * color_width if i < n_unique_colors - 1 else final_width
        
        # Draw color rectangle
        cv2.rectangle(palette, (x1, 0), (x2, palette_height), color.tolist(), -1)
        
        # Add number with larger font
        number = str(i + 1)
        font_scale_palette = max(0.8, (final_width / 2048) * 1.5)  # Larger palette numbers
        thickness = max(1, int(final_width / 1024))
        
        (text_width, text_height), _ = cv2.getTextSize(number, font, font_scale_palette, thickness)
        text_x = x1 + (x2 - x1)//2 - text_width//2
        text_y = palette_height - max(20, int(palette_height / 3))
        
        # Draw number with white background
        padding = max(4, int(final_width / 512))
        cv2.rectangle(palette,
                     (text_x - padding, text_y - text_height - padding),
                     (text_x + text_width + padding, text_y + padding),
                     (255, 255, 255), -1)
        cv2.putText(palette, number, (text_x, text_y),
                    font, font_scale_palette, (0, 0, 0), thickness)
    
    # Combine images with palettes
    outline_final = np.vstack([outline_image, palette])
    filled_final = np.vstack([filled_image, palette])
    
    return cv2.cvtColor(outline_final, cv2.COLOR_RGB2BGR), cv2.cvtColor(filled_final, cv2.COLOR_RGB2BGR)

def convert_heic_to_jpeg(file_path):
    """Convert HEIC file to JPEG format and return as numpy array"""
    try:
        # Open the HEIC file with Pillow
        with Image.open(file_path) as img:
            # Convert to RGB mode
            img = img.convert('RGB')
            # Save to bytes buffer
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG')
            buffer.seek(0)
            # Convert to numpy array
            jpeg_array = np.frombuffer(buffer.getvalue(), dtype=np.uint8)
            # Decode the JPEG buffer to image
            return cv2.imdecode(jpeg_array, cv2.IMREAD_COLOR)
    except Exception as e:
        logger.error(f"Error converting HEIC file: {e}")
        return None

def process_image(upload_id: str):
    """Process an uploaded image"""
    logger.info(f"Processing image {upload_id}")
    
    # Create database session
    engine = create_engine(SYNC_DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get upload from database
        upload = session.query(Upload).filter(Upload.id == upload_id).first()
        if not upload:
            raise ValueError(f"Upload {upload_id} not found")
        
        # Update status to processing
        upload.status = ProcessingStatus.PROCESSING
        session.commit()
        
        # Construct file paths, always using .jpg extension for processed files
        uploads_dir = Path("uploads")
        input_path = uploads_dir / upload.filename
        base_filename = Path(upload.filename).stem
        output_path = uploads_dir / f"processed_{base_filename}.jpg"
        filled_path = uploads_dir / f"processed_filled_{base_filename}.jpg"
        
        # Check if input file exists
        if not input_path.exists():
            raise ValueError("Input file not found")
        
        # Read the image based on file extension
        file_extension = input_path.suffix.lower()
        if file_extension in ['.heic', '.heif']:
            # Handle HEIC/HEIF files
            image = convert_heic_to_jpeg(input_path)
            if image is None:
                raise ValueError("Failed to convert HEIC file")
        else:
            # Handle regular image files
            image = cv2.imread(str(input_path))
            
        if image is None:
            raise ValueError("Failed to read image file")
            
        # Create paint by numbers version with specified color count
        outline_image, filled_image = create_paint_by_numbers(image, n_colors=upload.color_count)
        
        # Save the processed images as JPG
        cv2.imwrite(str(output_path), outline_image)
        cv2.imwrite(str(filled_path), filled_image)
        
        # Update upload record with processed filenames (using .jpg extension)
        upload.processed_filename = f"processed_{base_filename}.jpg"
        upload.filled_filename = f"processed_filled_{base_filename}.jpg"
        upload.status = ProcessingStatus.COMPLETED
        session.commit()
        
        logger.info(f"Successfully processed image {upload_id}")
        
    except Exception as e:
        logger.error(f"Error processing image {upload_id}")
        logger.error(str(e))
        # Update status to failed
        if upload:
            upload.status = ProcessingStatus.FAILED
            upload.error_message = str(e)
            session.commit()
    finally:
        session.close()

def enqueue_processing(upload_id: str):
    """Enqueue an image for processing"""
    queue = JobQueue()
    return queue.enqueue(upload_id) 