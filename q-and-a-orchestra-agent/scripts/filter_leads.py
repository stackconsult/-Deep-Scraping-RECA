#!/usr/bin/env python3
"""
Lead Filtering Script - Extract quality leads from scraped RECA data.

Filters:
- Keep only "Licensed" status agents
- Remove suspended/cancelled
- Validate email format
- Normalize city names
- Deduplicate by drill_id

Usage:
    python scripts/filter_leads.py --input data/all_agents_deep.json --output data/leads_clean.json
"""
import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Set


def is_valid_email(email: str) -> bool:
    """Validate email format using regex."""
    if not email:
        return False
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))


def normalize_city(city: str) -> str:
    """Normalize city names - title case and handle common variations."""
    if not city:
        return ""
    
    city = city.strip()
    
    # Common abbreviations
    replacements = {
        "Calg": "Calgary",
        "Edm": "Edmonton",
        "Red Deer": "Red Deer",
        "Ft": "Fort",
    }
    
    for abbr, full in replacements.items():
        if city.startswith(abbr):
            city = city.replace(abbr, full, 1)
    
    # Title case (handles CALGARY -> Calgary, calgary -> Calgary)
    return city.title()


def calculate_quality_score(agent: Dict) -> int:
    """
    Calculate lead quality score (0-100).
    
    Factors:
    - Has email: +40
    - Has phone: +30
    - Has brokerage: +20
    - Has city: +10
    """
    score = 0
    
    if agent.get("email"):
        score += 40
    if agent.get("phone"):
        score += 30
    if agent.get("brokerage"):
        score += 20
    if agent.get("city"):
        score += 10
    
    return score


def filter_leads(agents: List[Dict]) -> List[Dict]:
    """
    Filter and clean lead data.
    
    Returns only licensed agents with normalized data and quality scores.
    """
    filtered = []
    seen_drill_ids: Set[str] = set()
    
    for agent in agents:
        # Filter by status
        status = agent.get("status", "")
        if "Licensed" not in status:
            continue
        
        # Skip suspended/cancelled
        if any(word in status.lower() for word in ["suspend", "cancel", "withdrawal"]):
            continue
        
        # Deduplicate
        drill_id = agent.get("drill_id", "")
        if not drill_id:
            continue
        if drill_id in seen_drill_ids:
            continue
        seen_drill_ids.add(drill_id)
        
        # Validate email if present
        email = agent.get("email", "")
        if email and not is_valid_email(email):
            # Invalid email - clear it
            agent["email"] = ""
        
        # Normalize city
        agent["city"] = normalize_city(agent.get("city", ""))
        
        # Calculate quality score
        agent["quality_score"] = calculate_quality_score(agent)
        
        filtered.append(agent)
    
    return filtered


def print_stats(original: List[Dict], filtered: List[Dict]) -> None:
    """Print filtering statistics."""
    print("=" * 60)
    print("Lead Filtering Statistics")
    print("=" * 60)
    print(f"\nOriginal count:     {len(original)}")
    print(f"Filtered count:     {len(filtered)}")
    print(f"Removed:            {len(original) - len(filtered)}")
    print(f"Retention rate:     {len(filtered)/len(original)*100:.1f}%")
    
    # Quality breakdown
    with_email = sum(1 for a in filtered if a.get("email"))
    with_phone = sum(1 for a in filtered if a.get("phone"))
    with_both = sum(1 for a in filtered if a.get("email") and a.get("phone"))
    
    print(f"\nContact Info:")
    print(f"  With email:       {with_email} ({with_email/len(filtered)*100:.1f}%)")
    print(f"  With phone:       {with_phone} ({with_phone/len(filtered)*100:.1f}%)")
    print(f"  With both:        {with_both} ({with_both/len(filtered)*100:.1f}%)")
    
    # Quality scores
    avg_score = sum(a.get("quality_score", 0) for a in filtered) / len(filtered)
    high_quality = sum(1 for a in filtered if a.get("quality_score", 0) >= 70)
    
    print(f"\nQuality Scores:")
    print(f"  Average:          {avg_score:.1f}/100")
    print(f"  High quality (≥70): {high_quality} ({high_quality/len(filtered)*100:.1f}%)")
    
    # City breakdown (top 10)
    cities = {}
    for a in filtered:
        city = a.get("city", "Unknown")
        cities[city] = cities.get(city, 0) + 1
    
    print(f"\nTop 10 Cities:")
    for city, count in sorted(cities.items(), key=lambda x: -x[1])[:10]:
        print(f"  {city}: {count}")
    
    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Filter quality leads from RECA data")
    parser.add_argument("--input", "-i", required=True, help="Input JSON file")
    parser.add_argument("--output", "-o", required=True, help="Output JSON file")
    parser.add_argument("--min-quality", type=int, default=0, 
                       help="Minimum quality score (0-100, default: 0)")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ File not found: {args.input}")
        return
    
    print(f"Loading agents from {args.input}...")
    with open(input_path) as f:
        agents = json.load(f)
    
    print(f"Filtering leads...")
    filtered = filter_leads(agents)
    
    # Apply minimum quality filter
    if args.min_quality > 0:
        before = len(filtered)
        filtered = [a for a in filtered if a.get("quality_score", 0) >= args.min_quality]
        print(f"Applied quality filter (≥{args.min_quality}): removed {before - len(filtered)} leads")
    
    # Print statistics
    print_stats(agents, filtered)
    
    # Save
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(filtered, f, indent=2)
    
    print(f"\n✅ Saved {len(filtered)} quality leads to {args.output}")


if __name__ == "__main__":
    main()
