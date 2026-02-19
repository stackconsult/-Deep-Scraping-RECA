#!/usr/bin/env python3
"""
Direct Deep Scrape - Extract emails and phones from existing agents.

This script skips the surface sweep and directly performs drillthrough
on all agents in data/all_agents.json to extract contact information.
"""
import json
import time
import random
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s,%(msecs)03d [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from integrations.reca_scraper_logic import RECAHttpScraper

# Constants
INPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "all_agents.json"
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "all_agents_deep.json"
CHECKPOINT_FILE = Path(__file__).resolve().parent.parent / "data" / "deep_checkpoint.json"

DEEP_SCRAPE_DELAY = 1.5  # seconds between requests
JITTER_RANGE = 0.5


def load_agents() -> List[Dict]:
    """Load existing agents from JSON file."""
    if not INPUT_FILE.exists():
        logger.error(f"Input file not found: {INPUT_FILE}")
        return []
    
    with open(INPUT_FILE) as f:
        agents = json.load(f)
    
    logger.info(f"Loaded {len(agents)} agents from {INPUT_FILE}")
    return agents


def load_checkpoint() -> set:
    """Load completed drill IDs from checkpoint."""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE) as f:
            data = json.load(f)
            return set(data.get("completed", []))
    return set()


def save_checkpoint(completed: set):
    """Save completed drill IDs to checkpoint."""
    CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({"completed": list(completed)}, f, indent=2)


def save_agents(agents: List[Dict]):
    """Save agents to output file."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(agents, f, indent=2)
    logger.info(f"Saved {len(agents)} agents to {OUTPUT_FILE}")


def run_deep_scrape():
    """Perform deep scrape on all agents."""
    # Load agents
    agents = load_agents()
    if not agents:
        return
    
    # Load checkpoint
    completed_ids = load_checkpoint()
    logger.info(f"Resuming: {len(completed_ids)} agents already scraped")
    
    # Initialize scraper
    logger.info("Initializing RECA scraper...")
    scraper = RECAHttpScraper()
    
    total = len(agents)
    enriched = 0
    failed = 0
    skipped = 0
    
    for i, agent in enumerate(agents, 1):
        drill_id = agent.get("drill_id", "")
        if not drill_id:
            continue
        
        # Skip already completed
        if drill_id in completed_ids:
            skipped += 1
            continue
        
        name = agent.get("name", "unknown")
        
        # Progress every 100
        if i % 100 == 0:
            logger.info(f"Progress: {i}/{total} ({i/total*100:.1f}%) - {enriched} emails, {failed} failed")
        
        try:
            # Perform drillthrough
            contact_info = scraper.perform_drillthrough(drill_id)
            
            if contact_info:
                email = contact_info.get("email", "")
                phone = contact_info.get("phone", "")
                
                agent["email"] = email
                agent["phone"] = phone
                
                if email or phone:
                    enriched += 1
                    contact_str = f"Email: {email}" if email else ""
                    if phone:
                        contact_str += f", Phone: {phone}" if contact_str else f"Phone: {phone}"
                    logger.info(f"[{i}/{total}] {name}: {contact_str}")
            else:
                agent["email"] = ""
                agent["phone"] = ""
                
        except Exception as e:
            failed += 1
            logger.warning(f"[{i}/{total}] {name} failed: {e}")
            
            # Re-initialize on failure
            scraper._initialized = False
            try:
                scraper._fetch_initial_state()
            except Exception:
                pass
        
        # Mark as completed
        completed_ids.add(drill_id)
        
        # Save checkpoint every 50 agents
        if i % 50 == 0:
            save_checkpoint(completed_ids)
            save_agents(agents)
        
        # Rate limit
        delay = DEEP_SCRAPE_DELAY + random.uniform(0, JITTER_RANGE)
        time.sleep(delay)
    
    # Final save
    save_checkpoint(completed_ids)
    save_agents(agents)
    
    # Summary
    email_count = sum(1 for a in agents if a.get("email"))
    phone_count = sum(1 for a in agents if a.get("phone"))
    
    logger.info("=" * 60)
    logger.info("DEEP SCRAPE COMPLETE")
    logger.info(f"Total agents: {total}")
    logger.info(f"Emails found: {email_count} ({email_count/total*100:.1f}%)")
    logger.info(f"Phones found: {phone_count} ({phone_count/total*100:.1f}%)")
    logger.info(f"Failed: {failed}")
    logger.info(f"Skipped: {skipped}")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_deep_scrape()
