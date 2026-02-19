#!/usr/bin/env python3
"""
Cloud Run Scheduled Re-Scrape Service
======================================
Lightweight HTTP wrapper around full_sweep.py for Cloud Scheduler invocation.

Endpoints:
    POST /scrape         — Run full A-Z surface sweep + deep scrape
    POST /scrape/surface — Surface sweep only (names, brokerages)
    POST /scrape/deep    — Deep scrape only (email extraction)
    GET  /health         — Health check
    GET  /status         — Last run status

Environment Variables:
    PORT              — Server port (default 8080, set by Cloud Run)
    DATABASE_URL      — Postgres connection for results upload (optional)
    GCS_BUCKET        — GCS bucket for results backup (optional)
"""
import json
import logging
import os
import sys
import threading
import traceback
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from integrations.reca_scraper_logic import RECAHttpScraper
from scripts.full_sweep import (
    CheckpointManager,
    generate_prefixes,
    deduplicate_agents,
    run_surface_sweep,
    run_deep_scrape,
    save_json,
    save_csv,
    CHECKPOINT_FILE,
    RESULTS_FILE,
    CSV_FILE,
    DEEP_RESULTS_FILE,
    DEEP_CSV_FILE,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cloud_scraper")

# ---------------------------------------------------------------------------
# Global state for tracking runs
# ---------------------------------------------------------------------------
run_status = {
    "last_run": None,
    "status": "idle",
    "agents_found": 0,
    "emails_found": 0,
    "error": None,
    "duration_seconds": 0,
}
run_lock = threading.Lock()


def do_surface_sweep() -> dict:
    """Execute a full surface sweep and return stats."""
    scraper = RECAHttpScraper()
    checkpoint = CheckpointManager(CHECKPOINT_FILE)
    checkpoint.load()

    prefixes = generate_prefixes()
    agents = run_surface_sweep(scraper, checkpoint, prefixes)
    agents = deduplicate_agents(agents)

    save_json(agents, RESULTS_FILE)
    save_csv(agents, CSV_FILE)

    return {"agents_found": len(agents), "results_file": str(RESULTS_FILE)}


def do_deep_scrape() -> dict:
    """Execute deep scrape on existing surface results."""
    if not RESULTS_FILE.exists():
        return {"error": "No surface results found. Run surface sweep first."}

    with open(RESULTS_FILE) as f:
        agents = json.load(f)

    scraper = RECAHttpScraper()
    checkpoint = CheckpointManager(CHECKPOINT_FILE)
    checkpoint.load()

    deep_agents = run_deep_scrape(scraper, checkpoint, agents)

    save_json(deep_agents, DEEP_RESULTS_FILE)
    save_csv(deep_agents, DEEP_CSV_FILE)

    emails_found = sum(1 for a in deep_agents if a.get("email"))
    return {
        "agents_processed": len(deep_agents),
        "emails_found": emails_found,
        "deep_results_file": str(DEEP_RESULTS_FILE),
    }


def do_full_scrape() -> dict:
    """Run surface + deep scrape end-to-end."""
    surface = do_surface_sweep()
    if "error" in surface:
        return surface
    deep = do_deep_scrape()
    return {**surface, **deep}


def run_scrape_async(mode: str):
    """Run scrape in a background thread, updating global status."""
    global run_status
    with run_lock:
        if run_status["status"] == "running":
            return False  # Already running
        run_status["status"] = "running"
        run_status["error"] = None

    def _run():
        global run_status
        start = datetime.now(timezone.utc)
        try:
            if mode == "surface":
                result = do_surface_sweep()
            elif mode == "deep":
                result = do_deep_scrape()
            else:
                result = do_full_scrape()

            elapsed = (datetime.now(timezone.utc) - start).total_seconds()
            with run_lock:
                run_status.update({
                    "last_run": start.isoformat(),
                    "status": "completed",
                    "agents_found": result.get("agents_found", 0),
                    "emails_found": result.get("emails_found", 0),
                    "error": result.get("error"),
                    "duration_seconds": round(elapsed, 1),
                })
            logger.info(f"Scrape ({mode}) completed in {elapsed:.1f}s: {result}")
        except Exception as e:
            elapsed = (datetime.now(timezone.utc) - start).total_seconds()
            with run_lock:
                run_status.update({
                    "last_run": start.isoformat(),
                    "status": "failed",
                    "error": str(e),
                    "duration_seconds": round(elapsed, 1),
                })
            logger.error(f"Scrape ({mode}) failed: {traceback.format_exc()}")

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return True


class ScrapeHandler(BaseHTTPRequestHandler):
    """HTTP handler for Cloud Run / Cloud Scheduler."""

    def _send_json(self, status: int, data: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"status": "healthy"})
        elif self.path == "/status":
            self._send_json(200, run_status)
        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        if self.path == "/scrape":
            mode = "full"
        elif self.path == "/scrape/surface":
            mode = "surface"
        elif self.path == "/scrape/deep":
            mode = "deep"
        else:
            self._send_json(404, {"error": "Not found"})
            return

        started = run_scrape_async(mode)
        if started:
            self._send_json(202, {
                "message": f"Scrape ({mode}) started",
                "check_status": "/status",
            })
        else:
            self._send_json(409, {
                "error": "A scrape is already running",
                "current_status": run_status,
            })


def main():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), ScrapeHandler)
    logger.info(f"Cloud Scrape service listening on :{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
