#!/usr/bin/env python3
"""
Export RECA agent data from JSON to CSV format.
Converts the scraped agent data into a downloadable CSV file.
"""

import json
import csv
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Define CSV columns in desired order
CSV_COLUMNS = [
    "name",
    "first_name",
    "middle_name", 
    "last_name",
    "status",
    "brokerage",
    "city",
    "sector",
    "aka",
    "drill_id",
    "email",
    "phone"
]

def export_to_csv(json_file: Path, csv_file: Path):
    """Export agent data from JSON to CSV."""
    
    # Check if JSON file exists
    if not json_file.exists():
        print(f"❌ Error: JSON file not found at {json_file}")
        return False
    
    print(f"📖 Reading agents from {json_file}...")
    
    # Load JSON data
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            agents = json.load(f)
    except Exception as e:
        print(f"❌ Error reading JSON file: {e}")
        return False
    
    print(f"✅ Loaded {len(agents):,} agents")
    
    # Ensure output directory exists
    csv_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write CSV
    print(f"💾 Writing CSV to {csv_file}...")
    
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction='ignore')
            writer.writeheader()
            
            # Write each agent
            for i, agent in enumerate(agents, 1):
                # Ensure all required fields exist
                row = {col: agent.get(col, '') for col in CSV_COLUMNS}
                writer.writerow(row)
                
                # Progress indicator
                if i % 5000 == 0:
                    print(f"   Processed {i:,} agents...")
    
    except Exception as e:
        print(f"❌ Error writing CSV: {e}")
        return False
    
    # Get file size
    file_size = csv_file.stat().st_size
    size_mb = file_size / (1024 * 1024)
    
    print(f"✅ CSV export complete!")
    print(f"   📁 Location: {csv_file}")
    print(f"   📊 Records: {len(agents):,}")
    print(f"   💾 Size: {size_mb:.2f} MB")
    
    return True

def main():
    """Main export function."""
    print("=" * 60)
    print("RECA Agent Data Export - JSON to CSV")
    print("=" * 60)
    
    # Define file paths
    json_file = PROJECT_ROOT / "data" / "all_agents.json"
    csv_file = PROJECT_ROOT / "data" / "all_agents.csv"
    
    # Check for existing CSV
    if csv_file.exists():
        response = input(f"⚠️  CSV file already exists at {csv_file}. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Export cancelled.")
            return
    
    # Perform export
    success = export_to_csv(json_file, csv_file)
    
    if success:
        print("\n" + "=" * 60)
        print("Export successful! You can now download the CSV file.")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Export failed. Please check the error messages above.")
        print("=" * 60)

if __name__ == "__main__":
    main()