#!/usr/bin/env python3
"""
Full A-Z Alberta Agent Sweep — RECA ProCheck
=============================================
Scrapes ALL licensed real estate agents from RECA using two-letter prefix queries.
Includes: checkpoint/resume, deduplication, deep scrape (emails), rate limiting,
and JSON + CSV export.

Usage:
    python scripts/full_sweep.py                         # Surface scrape only
    python scripts/full_sweep.py --deep                  # Surface + email extraction
    python scripts/full_sweep.py --resume                # Resume from checkpoint
    python scripts/full_sweep.py --deep --resume         # Resume with deep scrape
    python scripts/full_sweep.py --letters A B C         # Only scrape specific letters
"""

import sys
import os
import json
import csv
import time
import random
import string
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from integrations.reca_scraper_logic import RECAHttpScraper

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
CHECKPOINT_FILE = PROJECT_ROOT / "data" / "sweep_checkpoint.json"
RESULTS_FILE = PROJECT_ROOT / "data" / "all_agents.json"
CSV_FILE = PROJECT_ROOT / "data" / "all_agents.csv"
DEEP_RESULTS_FILE = PROJECT_ROOT / "data" / "all_agents_deep.json"
DEEP_CSV_FILE = PROJECT_ROOT / "data" / "all_agents_deep.csv"

BASE_DELAY = 2.0          # seconds between requests
MAX_DELAY = 60.0           # max backoff delay
JITTER_RANGE = 1.0         # random jitter range
MAX_RETRIES = 5            # max retries per query
DEEP_SCRAPE_DELAY = 1.5    # seconds between drillthrough requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(PROJECT_ROOT / "data" / "sweep.log"),
    ],
)
logger = logging.getLogger("full_sweep")


# ---------------------------------------------------------------------------
# Checkpoint Management
# ---------------------------------------------------------------------------
class CheckpointManager:
    """Persist sweep progress so we can resume after crashes."""

    def __init__(self, path: Path):
        self.path = path
        self.state: Dict = {
            "completed_prefixes": [],
            "failed_prefixes": [],
            "total_agents_found": 0,
            "started_at": None,
            "last_updated": None,
            "phase": "surface",  # "surface" or "deep"
            "deep_completed_ids": [],
        }

    def load(self) -> bool:
        if self.path.exists():
            with open(self.path, "r") as f:
                self.state = json.load(f)
            logger.info(
                f"Resumed checkpoint: {len(self.state['completed_prefixes'])} prefixes done, "
                f"{self.state['total_agents_found']} agents found so far"
            )
            return True
        return False

    def save(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self.state, f, indent=2)

    def mark_prefix_done(self, prefix: str, count: int):
        self.state["completed_prefixes"].append(prefix)
        self.state["total_agents_found"] += count
        self.save()

    def mark_prefix_failed(self, prefix: str):
        self.state["failed_prefixes"].append(prefix)
        self.save()

    def is_prefix_done(self, prefix: str) -> bool:
        return prefix in self.state["completed_prefixes"]

    def mark_deep_done(self, drill_id: str):
        self.state["deep_completed_ids"].append(drill_id)
        # Save every 10 deep scrapes to reduce IO
        if len(self.state["deep_completed_ids"]) % 10 == 0:
            self.save()

    def is_deep_done(self, drill_id: str) -> bool:
        return drill_id in self.state["deep_completed_ids"]


# ---------------------------------------------------------------------------
# Query Generation
# ---------------------------------------------------------------------------
def generate_prefixes(letters: Optional[List[str]] = None) -> List[str]:
    """
    Generate search prefixes. Start with single letters, then two-letter combos.
    RECA caps results per query, so two-letter prefixes catch overflow.
    """
    if letters:
        base_letters = [l.upper() for l in letters]
    else:
        base_letters = list(string.ascii_uppercase)

    prefixes = []
    for letter in base_letters:
        prefixes.append(letter)
        # Two-letter combos for denser letters
        for second in string.ascii_lowercase:
            prefixes.append(f"{letter}{second}")

    return prefixes


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------
def deduplicate_agents(agents: List[Dict]) -> List[Dict]:
    """Deduplicate agents by drill_id (primary) or name+brokerage (fallback)."""
    seen_ids: Set[str] = set()
    seen_keys: Set[str] = set()
    unique = []

    for agent in agents:
        drill_id = agent.get("drill_id", "")
        if drill_id:
            if drill_id in seen_ids:
                continue
            seen_ids.add(drill_id)
        else:
            key = f"{agent['first_name']}|{agent['last_name']}|{agent['brokerage']}"
            if key in seen_keys:
                continue
            seen_keys.add(key)

        unique.append(agent)

    return unique


# ---------------------------------------------------------------------------
# Rate-Limited Search with Retry
# ---------------------------------------------------------------------------
def search_with_retry(
    scraper: RECAHttpScraper, prefix: str, max_retries: int = MAX_RETRIES
) -> Optional[List[Dict]]:
    """Search with exponential backoff on failure."""
    for attempt in range(1, max_retries + 1):
        try:
            results = scraper.search_by_lastname(prefix)
            return results
        except Exception as e:
            delay = min(BASE_DELAY * (2 ** attempt) + random.uniform(0, JITTER_RANGE), MAX_DELAY)
            logger.warning(
                f"Attempt {attempt}/{max_retries} for '{prefix}' failed: {e}. "
                f"Retrying in {delay:.1f}s..."
            )
            time.sleep(delay)

            # Re-initialize session on persistent failures
            if attempt >= 3:
                logger.info(f"Re-initializing scraper session after {attempt} failures")
                scraper._initialized = False
                try:
                    scraper._fetch_initial_state()
                except Exception:
                    pass

    return None


# ---------------------------------------------------------------------------
# Export Helpers
# ---------------------------------------------------------------------------
CSV_COLUMNS = [
    "name", "first_name", "middle_name", "last_name", "status",
    "brokerage", "city", "sector", "aka", "drill_id", "email",
]


def save_json(agents: List[Dict], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(agents, f, indent=2)
    logger.info(f"Saved {len(agents)} agents to {path}")


def save_csv(agents: List[Dict], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(agents)
    logger.info(f"Saved {len(agents)} agents to {path}")


# ---------------------------------------------------------------------------
# Surface Sweep
# ---------------------------------------------------------------------------
def run_surface_sweep(
    scraper: RECAHttpScraper,
    checkpoint: CheckpointManager,
    prefixes: List[str],
) -> List[Dict]:
    """Run surface scrape across all prefixes."""
    all_agents: List[Dict] = []

    # Load existing results if resuming
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE, "r") as f:
            all_agents = json.load(f)
        logger.info(f"Loaded {len(all_agents)} existing agents from {RESULTS_FILE}")

    total = len(prefixes)
    skipped = 0

    for i, prefix in enumerate(prefixes, 1):
        if checkpoint.is_prefix_done(prefix):
            skipped += 1
            continue

        logger.info(f"[{i}/{total}] Searching prefix '{prefix}'...")

        results = search_with_retry(scraper, prefix)

        if results is None:
            logger.error(f"FAILED prefix '{prefix}' after {MAX_RETRIES} retries — skipping")
            checkpoint.mark_prefix_failed(prefix)
            continue

        count = len(results)
        all_agents.extend(results)
        checkpoint.mark_prefix_done(prefix, count)

        if count > 0:
            logger.info(f"  → Found {count} agents for '{prefix}' (running total: {len(all_agents)} raw)")
        
        # Periodic dedupe + save every 26 prefixes (every letter cycle)
        if i % 26 == 0:
            all_agents = deduplicate_agents(all_agents)
            save_json(all_agents, RESULTS_FILE)

        # Rate limit
        delay = BASE_DELAY + random.uniform(0, JITTER_RANGE)
        time.sleep(delay)

    # Final dedupe and save
    all_agents = deduplicate_agents(all_agents)
    save_json(all_agents, RESULTS_FILE)
    save_csv(all_agents, CSV_FILE)

    if skipped > 0:
        logger.info(f"Skipped {skipped} already-completed prefixes")

    return all_agents


# ---------------------------------------------------------------------------
# Deep Scrape (Email Extraction)
# ---------------------------------------------------------------------------
def run_deep_scrape(
    scraper: RECAHttpScraper,
    checkpoint: CheckpointManager,
    agents: List[Dict],
) -> List[Dict]:
    """Drillthrough each agent to extract email addresses."""
    checkpoint.state["phase"] = "deep"
    checkpoint.save()

    total = len(agents)
    enriched = 0
    skipped = 0
    failed = 0

    for i, agent in enumerate(agents, 1):
        drill_id = agent.get("drill_id", "")
        if not drill_id:
            continue

        if checkpoint.is_deep_done(drill_id):
            skipped += 1
            continue

        name = agent.get("name", "unknown")
        logger.info(f"[{i}/{total}] Deep scraping {name} (drill_id: {drill_id[:20]}...)")

        try:
            email = scraper.perform_drillthrough(drill_id)
            if email:
                agent["email"] = email
                enriched += 1
                logger.info(f"  → Email: {email}")
            else:
                agent["email"] = ""
                logger.info(f"  → No email found")
        except Exception as e:
            agent["email"] = ""
            failed += 1
            logger.warning(f"  → Drillthrough failed: {e}")

            # Re-initialize on failure
            scraper._initialized = False
            try:
                scraper._fetch_initial_state()
            except Exception:
                pass

        checkpoint.mark_deep_done(drill_id)

        # Save progress every 50 agents
        if i % 50 == 0:
            save_json(agents, DEEP_RESULTS_FILE)
            logger.info(f"  [checkpoint] {enriched} emails found, {failed} failures so far")

        # Rate limit
        delay = DEEP_SCRAPE_DELAY + random.uniform(0, JITTER_RANGE)
        time.sleep(delay)

    # Final save
    save_json(agents, DEEP_RESULTS_FILE)
    save_csv(agents, DEEP_CSV_FILE)

    logger.info(
        f"Deep scrape complete: {enriched} emails found, {failed} failures, "
        f"{skipped} skipped (already done)"
    )
    return agents


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Full A-Z Alberta Agent Sweep")
    parser.add_argument("--deep", action="store_true", help="Enable deep scrape (email extraction)")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--letters", nargs="+", help="Only scrape specific letters (e.g. A B C)")
    parser.add_argument("--delay", type=float, default=BASE_DELAY, help="Base delay between requests")
    args = parser.parse_args()

    # Ensure data directory exists
    (PROJECT_ROOT / "data").mkdir(exist_ok=True)

    # Checkpoint
    checkpoint = CheckpointManager(CHECKPOINT_FILE)
    if args.resume:
        if not checkpoint.load():
            logger.info("No checkpoint found — starting fresh")
    else:
        checkpoint.state["started_at"] = datetime.now(timezone.utc).isoformat()

    # Initialize scraper
    logger.info("Initializing RECA scraper session...")
    scraper = RECAHttpScraper()

    # Generate prefixes
    prefixes = generate_prefixes(args.letters)
    logger.info(f"Generated {len(prefixes)} search prefixes")

    # Surface sweep
    logger.info("=" * 60)
    logger.info("PHASE 1: Surface Sweep (A-Z)")
    logger.info("=" * 60)
    agents = run_surface_sweep(scraper, checkpoint, prefixes)
    logger.info(f"Surface sweep complete: {len(agents)} unique agents found")

    # Deep scrape
    if args.deep:
        logger.info("=" * 60)
        logger.info("PHASE 2: Deep Scrape (Email Extraction)")
        logger.info("=" * 60)
        agents = run_deep_scrape(scraper, checkpoint, agents)

    # Summary
    logger.info("=" * 60)
    logger.info("SWEEP COMPLETE")
    logger.info(f"  Total unique agents: {len(agents)}")
    if args.deep:
        with_email = sum(1 for a in agents if a.get("email"))
        logger.info(f"  Agents with email:   {with_email}")
        logger.info(f"  Results: {DEEP_CSV_FILE}")
    else:
        logger.info(f"  Results: {CSV_FILE}")
    logger.info(f"  Failed prefixes: {checkpoint.state.get('failed_prefixes', [])}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
