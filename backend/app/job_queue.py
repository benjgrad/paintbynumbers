import redis
import json
import time
from typing import Optional

class JobQueue:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
        self.queue_key = "image_processing_queue"
        self.processing_key = "image_processing_in_progress"
        self.failed_key = "image_processing_failed"

    def enqueue(self, upload_id: str) -> bool:
        try:
            return bool(self.redis.lpush(self.queue_key, upload_id))
        except Exception as e:
            print(f"Error enqueueing job: {e}")
            return False

    def dequeue(self) -> Optional[str]:
        try:
            # Atomic move from queue to processing
            upload_id = self.redis.rpoplpush(self.queue_key, self.processing_key)
            return upload_id
        except Exception as e:
            print(f"Error dequeuing job: {e}")
            return None

    def complete_job(self, upload_id: str):
        try:
            self.redis.lrem(self.processing_key, 1, upload_id)
        except Exception as e:
            print(f"Error completing job: {e}")

    def fail_job(self, upload_id: str, error: str):
        try:
            self.redis.lrem(self.processing_key, 1, upload_id)
            self.redis.hset(self.failed_key, upload_id, error)
        except Exception as e:
            print(f"Error failing job: {e}") 