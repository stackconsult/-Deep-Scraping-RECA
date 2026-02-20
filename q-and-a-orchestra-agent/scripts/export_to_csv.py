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
import gc

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
    print(f"   File size: {json_file.stat().st_size / (1024*1024):.2f} MB")
    
    # Load JSON data with progress indication
    try:
        print("   Loading JSON data (this may take a moment for large files)...")
        with open(json_file, 'r', encoding='utf-8') as f:
            agents = json.load(f)
    except Exception as e:
        print(f"❌ Error reading JSON file: {e}")
        return False
    
    print(f"✅ Loaded {len(agents):,} agents")
    
    # Ensure output directory exists
    csv_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if CSV already exists
    if csv_file.exists():
        print(f"⚠️  CSV file already exists at {csv_file}")
        response = input("   Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("   Export cancelled.")
            return False
    
    # Write CSV with progress tracking
    print(f"💾 Writing CSV to {csv_file}...")
    
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction='ignore')
            writer.writeheader()
            
            # Write each agent with progress
            for i, agent in enumerate(agents, 1):
                # Ensure all required fields exist
                row = {col: agent.get(col, '') for col in CSV_COLUMNS}
                writer.writerow(row)
                
                # Progress indicator
                if i % 1000 == 0:
                    percent = (i / len(agents)) * 100
                    print(f"   Progress: {i:,}/{len(agents):,} ({percent:.1f}%)")
        
        # Clear memory
        del agents
        gc.collect()
    
    except Exception as e:
        print(f"❌ Error writing CSV: {e}")
        # Clean up partial file
        if csv_file.exists():
            csv_file.unlink()
        return False
    
    # Get file size and stats
    file_size = csv_file.stat().st_size
    size_mb = file_size / (1024 * 1024)
    
    print(f"\n✅ CSV export complete!")
    print(f"   📁 Location: {csv_file}")
    print(f"   📊 Records: {len(agents):,}")
    print(f"   💾 Size: {size_mb:.2f} MB")
    print(f"   ⏰ Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return True

def main():
    """Main export function."""
    print("=" * 60)
    print("RECA Agent Data Export - JSON to CSV")
    print("Debugger Persona - Phase 1 Implementation")
    print("=" * 60)
    
    # Define file paths
    json_file = PROJECT_ROOT / "data" / "all_agents.json"
    csv_file = PROJECT_ROOT / "data" / "all_agents.csv"
    
    # Perform export
    success = export_to_csv(json_file, csv_file)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ EXPORT SUCCESSFUL!")
        print("The CSV file is ready for download.")
        print("\nNext steps:")
        print("1. Download the CSV file from the data directory")
        print("2. Verify the data looks correct")
        print("3. Proceed to Phase 2: Email Enrichment Testing")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ EXPORT FAILED")
        print("Please check the error messages above.")
        print("=" * 60)

if __name__ == "__main__":
    main()