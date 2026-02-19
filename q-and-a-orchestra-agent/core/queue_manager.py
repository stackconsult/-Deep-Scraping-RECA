import json
import logging
from typing import Any, Dict, Optional
import redis

logger = logging.getLogger(__name__)

class QueueManager:
    """Simple Redis-based queue for async job processing."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", queue_name: str = "reca_scraper_queue"):
        self.redis_url = redis_url
        self.queue_name = queue_name
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        
    def enqueue(self, job_data: Dict[str, Any]) -> str:
        """Push a job to the queue."""
        try:
            job_json = json.dumps(job_data)
            self.redis_client.rpush(self.queue_name, job_json)
            logger.info(f"Enqueued job: {job_data.get('job_id', 'unknown')}")
            return job_data.get('job_id', '')
        except Exception as e:
            logger.error(f"Failed to enqueue job: {e}")
            raise

    def dequeue(self, timeout: int = 0) -> Optional[Dict[str, Any]]:
        """Pop a job from the queue (blocking with timeout)."""
        try:
            # blpop returns (queue_name, data) or None
            result = self.redis_client.blpop(self.queue_name, timeout=timeout)
            if result:
                _, job_json = result
                return json.loads(job_json)
            return None
        except Exception as e:
            logger.error(f"Failed to dequeue job: {e}")
            return None
            
    def get_queue_length(self) -> int:
        """Get current queue length."""
        try:
            return self.redis_client.llen(self.queue_name)
        except Exception:
            return 0
