#!/usr/bin/env python3
"""
Incremental Scraper - Detect changes in existing agents without full re-scrape.

Strategy:
1. Load existing agents from database or JSON
2. For each agent, query RECA by drill_id
3. Compare current data with stored data
4. Update only changed records
5. Flag new agents not in database

Usage:
    python scripts/incremental_scraper.py --database DATABASE_URL
    python scripts/incremental_scraper.py --input data/leads_clean.json --output data/leads_updated.json
"""
import argparse
import json
import hashlib
import sys
import time
import random
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime, timezone

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from integrations.reca_scraper_logic import RECAHttpScraper


def compute_hash(agent: Dict) -> str:
    """Compute hash of agent fields for change detection."""
    # Fields to monitor for changes
    fields = [
        agent.get("first_name", ""),
        agent.get("last_name", ""),
        agent.get("status", ""),
        agent.get("brokerage", ""),
        agent.get("city", ""),
        agent.get("email", ""),
        agent.get("phone", ""),
    ]
    
    data = "|".join(str(f) for f in fields)
    return hashlib.sha256(data.encode()).hexdigest()


def detect_changes(old_agent: Dict, new_agent: Dict) -> List[Dict[str, str]]:
    """
    Detect what changed between old and new agent data.
    
    Returns list of change dicts with: field_name, old_value, new_value
    """
    changes = []
    fields_to_check = ["status", "brokerage", "city", "email", "phone"]
    
    for field in fields_to_check:
        old_val = old_agent.get(field, "")
        new_val = new_agent.get(field, "")
        
        if old_val != new_val:
            changes.append({
                "field_name": field,
                "old_value": str(old_val),
                "new_value": str(new_val),
            })
    
    return changes


def incremental_update(
    existing_agents: List[Dict],
    scraper: RECAHttpScraper,
    delay: float = 2.0
) -> Dict:
    """
    Perform incremental update by checking each existing agent.
    
    Returns dict with:
    - updated: list of updated agents
    - unchanged: count of unchanged agents
    - failed: list of drill_ids that failed
    - changes: list of all changes detected
    """
    results = {
        "updated": [],
        "unchanged": 0,
        "failed": [],
        "changes": [],
    }
    
    total = len(existing_agents)
    print(f"Checking {total} existing agents for updates...")
    
    for i, agent in enumerate(existing_agents, 1):
        drill_id = agent.get("drill_id")
        if not drill_id:
            continue
        
        name = agent.get("name", "unknown")
        
        if i % 100 == 0:
            print(f"  Progress: {i}/{total} ({i/total*100:.1f}%)")
        
        try:
            # Search by last name to get current data
            last_name = agent.get("last_name", "")
            if not last_name:
                continue
            
            # Query RECA for current data
            current_agents = scraper.search_by_lastname(last_name)
            
            # Find matching agent by drill_id
            current_agent = None
            for a in current_agents:
                if a.get("drill_id") == drill_id:
                    current_agent = a
                    break
            
            if not current_agent:
                # Agent not found - may have been removed
                print(f"  ⚠️  Agent {name} (drill_id: {drill_id[:20]}...) not found in RECA")
                results["failed"].append(drill_id)
                continue
            
            # Detect changes
            changes = detect_changes(agent, current_agent)
            
            if changes:
                print(f"  🔄 Changes detected for {name}:")
                for change in changes:
                    print(f"     {change['field_name']}: {change['old_value']} → {change['new_value']}")
                
                # Update agent with new data
                for key, value in current_agent.items():
                    agent[key] = value
                
                agent["updated_at"] = datetime.now(timezone.utc).isoformat()
                results["updated"].append(agent)
                results["changes"].extend([{**change, "drill_id": drill_id, "name": name} for change in changes])
            else:
                results["unchanged"] += 1
            
            # Rate limit
            time.sleep(delay + random.uniform(0, 0.5))
            
        except Exception as e:
            print(f"  ❌ Error checking {name}: {e}")
            results["failed"].append(drill_id)
            time.sleep(delay * 2)  # Longer delay on error
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Incremental RECA scraper for change detection")
    parser.add_argument("--input", "-i", help="Input JSON file with existing agents")
    parser.add_argument("--output", "-o", help="Output JSON file for updated agents")
    parser.add_argument("--database", help="Database URL (alternative to file input)")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between requests (seconds)")
    args = parser.parse_args()
    
    if not args.input and not args.database:
        print("❌ Must provide either --input or --database")
        return
    
    if args.database:
        print("❌ Database mode not yet implemented - use --input for now")
        return
    
    # Load existing agents
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ File not found: {args.input}")
        return
    
    print(f"Loading existing agents from {args.input}...")
    with open(input_path) as f:
        existing_agents = json.load(f)
    
    print(f"Loaded {len(existing_agents)} agents")
    
    # Initialize scraper
    print("Initializing RECA scraper...")
    scraper = RECAHttpScraper()
    
    # Perform incremental update
    results = incremental_update(existing_agents, scraper, delay=args.delay)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Incremental Update Summary")
    print("=" * 60)
    print(f"Total checked:      {len(existing_agents)}")
    print(f"Updated:            {len(results['updated'])}")
    print(f"Unchanged:          {results['unchanged']}")
    print(f"Failed:             {len(results['failed'])}")
    print(f"Total changes:      {len(results['changes'])}")
    
    if results['changes']:
        print(f"\nChange Breakdown:")
        change_types = {}
        for change in results['changes']:
            field = change['field_name']
            change_types[field] = change_types.get(field, 0) + 1
        
        for field, count in sorted(change_types.items(), key=lambda x: -x[1]):
            print(f"  {field}: {count}")
    
    print("=" * 60)
    
    # Save updated agents
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(existing_agents, f, indent=2)
        print(f"\n✅ Saved updated agents to {args.output}")
        
        # Save change log
        changelog_path = output_path.parent / "change_log.json"
        with open(changelog_path, "w") as f:
            json.dump(results['changes'], f, indent=2)
        print(f"✅ Saved change log to {changelog_path}")


if __name__ == "__main__":
    main()
