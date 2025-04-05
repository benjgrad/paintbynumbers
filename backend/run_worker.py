import time
import logging
from app.job_queue import JobQueue
from app.worker import process_image

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def run_worker():
    queue = JobQueue()
    logger.info("Worker started")
    
    while True:
        try:
            # Get next job
            upload_id = queue.dequeue()
            
            if upload_id:
                logger.info(f"Processing upload {upload_id}")
                try:
                    success = process_image(upload_id)
                    if success:
                        queue.complete_job(upload_id)
                    else:
                        queue.fail_job(upload_id, "Processing failed")
                except Exception as e:
                    logger.exception(f"Error processing {upload_id}")
                    queue.fail_job(upload_id, str(e))
            else:
                # No jobs available, wait a bit
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Shutting down worker")
            break
        except Exception as e:
            logger.exception("Unexpected error in worker loop")
            time.sleep(1)

if __name__ == "__main__":
    run_worker() 