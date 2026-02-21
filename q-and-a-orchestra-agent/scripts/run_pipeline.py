#!/usr/bin/env python3
"""
Master Pipeline Script for RECA Data Enrichment
Chains the following steps:
1. Enrichment (Email finding via Hybrid Agent)
2. Validation (Quality checks and stats)
3. Ingestion (Loading into Postgres)

Usage:
    python scripts/run_pipeline.py --input data/all_agents.json --batch-size 10 --sample 50
"""

import argparse
import subprocess
import sys
import logging
import os
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(command: list, check: bool = True):
    """Run a shell command and stream output."""
    logger.info(f"🚀 Running: {' '.join(command)}")
    try:
        process = subprocess.run(
            command,
            check=check,
            text=True,
            capture_output=False  # Let output stream to stdout
        )
        return process.returncode
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Command failed with exit code {e.returncode}")
        sys.exit(e.returncode)

def main():
    parser = argparse.ArgumentParser(description="Run full RECA enrichment pipeline")
    parser.add_argument("--input", default="data/all_agents.json", help="Input source JSON")
    parser.add_argument("--output-dir", default="data", help="Directory for output artifacts")
    parser.add_argument("--batch-size", type=str, default="10", help="Batch size for enrichment")
    parser.add_argument("--sample", type=int, help="Run on a sample size (optional)")
    parser.add_argument("--skip-ingest", action="store_true", help="Skip database ingestion step")
    parser.add_argument("--db-url", help="Database URL (overrides env var)")
    
    args = parser.parse_args()
    
    # Setup paths
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    enriched_file = Path(args.output_dir) / "all_agents_enriched.json"
    
    # --- Step 1: Enrichment ---
    logger.info("=== STEP 1: EMAIL ENRICHMENT ===")
    enrich_cmd = [
        sys.executable, "scripts/production_enrichment.py",
        "--input", str(input_path),
        "--output", str(enriched_file),
        "--batch-size", str(args.batch_size)
    ]
    
    if args.sample:
        enrich_cmd.extend(["--sample", "--size", str(args.sample)])
        
    run_command(enrich_cmd)
    
    if not enriched_file.exists():
        logger.error("Enrichment failed to produce output file.")
        sys.exit(1)

    # --- Step 2: Validation ---
    logger.info("=== STEP 2: DATA VALIDATION ===")
    validate_cmd = [
        sys.executable, "scripts/validate_data.py",
        "--input", str(enriched_file)
    ]
    run_command(validate_cmd)
    
    # --- Step 3: Database Ingestion ---
    if not args.skip_ingest:
        logger.info("=== STEP 3: DATABASE INGESTION ===")
        
        # Check environment
        db_url = args.db_url or os.getenv("DATABASE_URL")
        if not db_url:
            logger.warning("⚠️  DATABASE_URL not set. Skipping ingestion.")
        else:
            ingest_cmd = [
                sys.executable, "scripts/db_ingest.py",
                "--input", str(enriched_file),
                "--create-table" # Ensure schema exists
            ]
            
            # Pass DB URL via env if provided arg
            env = os.environ.copy()
            if args.db_url:
                env["DATABASE_URL"] = args.db_url
                
            try:
                subprocess.run(ingest_cmd, check=True, env=env)
            except subprocess.CalledProcessError:
                logger.error("❌ Database ingestion failed.")
                sys.exit(1)
    else:
        logger.info("Skipping database ingestion (--skip-ingest set)")

    logger.info("✅ Pipeline completed successfully.")

if __name__ == "__main__":
    main()
