from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil
import os
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .core.database import get_db, init_db
from .models.upload import Upload, ProcessingStatus
from .worker import enqueue_processing
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Image Upload API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Mount the uploads directory
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.post("/api/upload")
async def upload_image(
    file: UploadFile = File(...),
    color_count: int = Form(20, ge=2, le=30),  # Default 20, min 2, max 30
    db: AsyncSession = Depends(get_db)
):
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            return {"error": "File must be an image"}
        
        # Create unique filename with UUID
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_location = UPLOAD_DIR / unique_filename
        
        # Save the file
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
        
        # Create database record
        upload_id = str(uuid.uuid4())
        db_upload = Upload(
            id=upload_id,
            filename=unique_filename,
            original_name=file.filename,
            status=ProcessingStatus.PENDING,
            color_count=color_count
        )
        db.add(db_upload)
        await db.commit()
        logger.info(f"Successfully created upload record with ID: {upload_id}")

        # Enqueue for processing
        enqueue_processing(upload_id)
            
        return {
            "id": upload_id,
            "filename": unique_filename,
            "colorCount": color_count,
            "message": "Image uploaded and queued for processing"
        }
    except Exception as e:
        logger.error(f"Error in upload_image: {str(e)}")
        await db.rollback()
        return {"error": str(e)}

@app.get("/api/uploads")
async def get_uploads(db: AsyncSession = Depends(get_db)):
    try:
        logger.info("Fetching uploads from database...")
        result = await db.execute(
            select(Upload).order_by(Upload.uploaded_at.desc())
        )
        uploads = result.scalars().all()
        uploads_list = [upload.to_dict() for upload in uploads]
        logger.info(f"Found {len(uploads_list)} uploads")
        return {"uploads": uploads_list}
    except Exception as e:
        logger.error(f"Error in get_uploads: {str(e)}")
        return {"error": str(e)}

@app.get("/api/uploads/{upload_id}")
async def get_upload_status(upload_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(Upload).filter(Upload.id == upload_id)
        )
        upload = result.scalar_one_or_none()
        
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")
            
        return upload.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_upload_status: {str(e)}")
        return {"error": str(e)}

@app.get("/")
async def root():
    return {"message": "Image Upload API is running"}
