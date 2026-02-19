#!/usr/bin/env python3
"""
Normalize Scraped Data
---------------------
Fixes casing issues in city names (e.g., "EDMONTON" -> "Edmonton").
"""
import json
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def normalize_city(city: str) -> str:
    if not city:
        return ""
    return city.strip().title()

def main():
    parser = argparse.ArgumentParser(description="Normalize RECA data")
    parser.add_argument("--input", "-i", default="data/all_agents.json", help="Input JSON file")
    parser.add_argument("--output", "-o", default=None, help="Output JSON file (default: overwrite input)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"File not found: {input_path}")
        return

    output_path = Path(args.output) if args.output else input_path

    logger.info(f"Loading {input_path}...")
    try:
        with open(input_path, "r") as f:
            agents = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        return

    count = 0
    for agent in agents:
        original = agent.get("city", "")
        normalized = normalize_city(original)
        if original != normalized:
            agent["city"] = normalized
            count += 1
    
    logger.info(f"Normalized {count} city names.")
    
    logger.info(f"Saving to {output_path}...")
    try:
        with open(output_path, "w") as f:
            json.dump(agents, f, indent=2)
        logger.info("Done.")
    except Exception as e:
        logger.error(f"Failed to save output file: {e}")

if __name__ == "__main__":
    main()
