import asyncio
import logging
import os
import sys
import json
import time
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.queue_manager import QueueManager
from integrations.reca_scraper_logic import RECAHttpScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scraper_worker.log")
    ]
)
logger = logging.getLogger("scraper_worker")

class ScraperWorker:
    def __init__(self):
        self.queue = QueueManager()
        self.scraper = RECAHttpScraper()
        self.is_running = False
        
    async def start(self):
        logger.info("Starting scraper worker...")
        self.is_running = True
        
        # Ensure scraper is initialized
        try:
            self.scraper._fetch_initial_state()
            logger.info("Scraper initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize scraper: {e}")
            # We continue, maybe it's transient
        
        while self.is_running:
            try:
                # Dequeue with timeout to allow checking is_running
                job = self.queue.dequeue(timeout=5)
                
                if job:
                    await self.process_job(job)
                else:
                    # Idle
                    await asyncio.sleep(1)
                    
            except KeyboardInterrupt:
                logger.info("Stopping worker...")
                self.is_running = False
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(5)
                
    async def process_job(self, job: Dict[str, Any]):
        job_id = job.get("job_id")
        job_type = job.get("type")
        logger.info(f"Processing job {job_id} ({job_type})")
        
        try:
            if job_type == "scrape_request":
                payload = job.get("payload", {})
                search_params = payload.get("search_params", {})
                last_name = search_params.get("last_name")
                deep_scrape = payload.get("deep_scrape", False)
                session_id = job.get("session_id")
                
                if last_name:
                    logger.info(f"Scraping for: {last_name} (Session: {session_id})")
                    results = self.scraper.search_by_lastname(last_name)
                    logger.info(f"Found {len(results)} initial results")
                    
                    if deep_scrape:
                        logger.info(f"Deep scraping {len(results)} results")
                        for agent in results:
                             drill_id = agent.get("drill_id")
                             if drill_id:
                                 try:
                                     email = self.scraper.perform_drillthrough(drill_id)
                                     if email:
                                         agent["email"] = email
                                 except Exception as e:
                                     logger.error(f"Deep scrape error for {agent.get('name')}: {e}")
                                 
                                 # Rate limit
                                 await asyncio.sleep(1)
                                 
                    logger.info(f"Job {job_id} completed. Found {len(results)} results.")
                    
                    # Store results - for now just log/save to file
                    self._save_results(job_id, session_id, results)
                else:
                    logger.error(f"Job {job_id}: Missing last_name in payload")
            
            else:
                logger.warning(f"Unknown job type: {job_type}")
                
        except Exception as e:
            logger.error(f"Failed processing job {job_id}: {e}")

    def _save_results(self, job_id: str, session_id: str, results: list):
        """Save results to specific file."""
        filename = f"scrape_results_{job_id}_{int(time.time())}.json"
        try:
            with open(filename, 'w') as f:
                json.dump({
                    "job_id": job_id,
                    "session_id": session_id,
                    "timestamp": time.time(),
                    "results": results
                }, f, indent=2)
            logger.info(f"Results saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save results for {job_id}: {e}")

if __name__ == "__main__":
    worker = ScraperWorker()
    try:
        asyncio.run(worker.start())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user.")
