#!/usr/bin/env python3
"""
Data Validation Script — flags missing emails, duplicates, and summary stats.

Usage:
    python scripts/validate_data.py [--input reca_agents.json] [--format json|csv]
"""
import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path


def load_json(path: str):
    with open(path) as f:
        return json.load(f)


def load_csv(path: str):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def validate(agents: list) -> dict:
    """Run validation checks and return a report dict."""
    total = len(agents)
    if total == 0:
        return {"error": "No agents found in input file."}

    # --- Missing emails ---
    missing_email = [a for a in agents if not a.get("email")]
    email_coverage = ((total - len(missing_email)) / total) * 100

    # --- Enrichment Stats ---
    enrichment_attempts = sum(1 for a in agents if a.get("enrichment_status"))
    enrichment_success = sum(1 for a in agents if a.get("enrichment_status") == "success")
    enrichment_rate = (enrichment_success / enrichment_attempts * 100) if enrichment_attempts > 0 else 0.0

    # --- Validation Status ---
    validation_statuses = Counter()
    confidence_scores = []
    
    for a in agents:
        meta = a.get("enrichment_metadata", {})
        if meta:
            # Check validation status if available, or infer
            if meta.get("validated_emails"):
                validation_statuses["valid"] += 1
            elif a.get("enrichment_status") == "success":
                validation_statuses["unverified"] += 1
            
            # Collect confidence
            if meta.get("confidence"):
                confidence_scores.append(meta.get("confidence"))

    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

    # --- Duplicate drill_ids ---
    drill_ids = [a.get("drill_id", "") for a in agents if a.get("drill_id")]
    id_counts = Counter(drill_ids)
    duplicates = {k: v for k, v in id_counts.items() if v > 1}

    # --- Status breakdown ---
    statuses = Counter(a.get("status", "unknown") for a in agents)

    # --- City breakdown (top 10) ---
    cities = Counter(a.get("city", "unknown") for a in agents)
    top_cities = cities.most_common(10)

    report = {
        "total_agents": total,
        "email_coverage_pct": round(email_coverage, 1),
        "missing_email_count": len(missing_email),
        "enrichment_attempts": enrichment_attempts,
        "enrichment_success": enrichment_success,
        "enrichment_success_rate": round(enrichment_rate, 1),
        "validation_breakdown": dict(validation_statuses),
        "avg_confidence_score": round(avg_confidence, 2),
        "duplicate_drill_ids": duplicates,
        "duplicate_count": sum(v - 1 for v in duplicates.values()),
        "status_breakdown": dict(statuses),
        "top_10_cities": dict(top_cities),
    }
    return report


def print_report(report: dict) -> None:
    """Pretty-print the validation report."""
    print("=" * 60)
    print("  RECA Data Validation Report")
    print("=" * 60)

    if "error" in report:
        print(f"\n  ❌  {report['error']}\n")
        return

    print(f"\n  Total agents:       {report['total_agents']}")
    print(f"  Email coverage:     {report['email_coverage_pct']}%")
    print(f"  Missing emails:     {report['missing_email_count']}")
    
    if report['enrichment_attempts'] > 0:
        print(f"\n  Enrichment Stats:")
        print(f"    Attempts:         {report['enrichment_attempts']}")
        print(f"    Success:          {report['enrichment_success']}")
        print(f"    Rate:             {report['enrichment_success_rate']}%")
        print(f"    Avg Confidence:   {report['avg_confidence_score']}")
        print(f"    Valid Emails:     {report['validation_breakdown'].get('valid', 0)}")

    print(f"\n  Duplicate drill_ids: {report['duplicate_count']}")

    if report["duplicate_drill_ids"]:
        print("\n  Duplicate IDs:")
        for did, cnt in report["duplicate_drill_ids"].items():
            print(f"    - {did}: {cnt}x")

    print("\n  Status breakdown:")
    for status, cnt in sorted(report["status_breakdown"].items(), key=lambda x: -x[1]):
        print(f"    {status}: {cnt}")

    print("\n  Top 10 cities:")
    for city, cnt in report["top_10_cities"].items():
        print(f"    {city}: {cnt}")

    print("\n" + "=" * 60)

    # Exit code: 1 if serious issues
    if report["email_coverage_pct"] < 50:
        print("  ⚠️  WARNING: Email coverage below 50%")
    if report["duplicate_count"] > 0:
        print(f"  ⚠️  WARNING: {report['duplicate_count']} duplicate entries found")


def main():
    parser = argparse.ArgumentParser(description="Validate RECA scrape data")
    parser.add_argument("--input", "-i", default="reca_agents.json",
                        help="Path to scraped data file")
    parser.add_argument("--format", "-f", choices=["json", "csv"], default=None,
                        help="Input format (auto-detected from extension if omitted)")
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f"❌  File not found: {args.input}")
        sys.exit(1)

    fmt = args.format or ("csv" if path.suffix == ".csv" else "json")

    if fmt == "csv":
        agents = load_csv(str(path))
    else:
        agents = load_json(str(path))

    report = validate(agents)
    print_report(report)

    # Also dump machine-readable report
    report_path = path.parent / "validation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Report saved to: {report_path}")


if __name__ == "__main__":
    main()
