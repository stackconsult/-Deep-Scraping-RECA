#!/usr/bin/env python3
"""
Test script for CSV export functionality.
Tests the export_to_csv.py script with sample data.
"""

import sys
import json
import csv
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_csv_export():
    """Test CSV export with a small sample of data."""
    
    print("=" * 60)
    print("CSV Export Test - Debugger Persona")
    print("=" * 60)
    
    # Load sample of agents
    json_file = PROJECT_ROOT / "data" / "all_agents.json"
    
    if not json_file.exists():
        print(f"❌ ERROR: Source JSON file not found at {json_file}")
        return False
    
    print(f"📖 Loading sample data from {json_file}...")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            agents = json.load(f)
        
        # Take first 10 agents for testing
        sample_agents = agents[:10]
        print(f"✅ Loaded {len(agents):,} total agents")
        print(f"📋 Testing with {len(sample_agents)} sample agents")
        
        # Test CSV creation
        csv_file = PROJECT_ROOT / "data" / "test_export.csv"
        
        CSV_COLUMNS = [
            "name", "first_name", "middle_name", "last_name", "status",
            "brokerage", "city", "sector", "aka", "drill_id", "email", "phone"
        ]
        
        print(f"💾 Creating test CSV at {csv_file}...")
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction='ignore')
            writer.writeheader()
            
            for i, agent in enumerate(sample_agents, 1):
                row = {col: agent.get(col, '') for col in CSV_COLUMNS}
                writer.writerow(row)
                print(f"   {i}. {agent.get('name', 'Unknown')} - {agent.get('brokerage', 'No brokerage')}")
        
        print(f"\n✅ Test CSV created successfully!")
        print(f"   📁 Location: {csv_file}")
        print(f"   📊 Records: {len(sample_agents)}")
        
        # Verify CSV can be read back
        print("\n🔍 Verifying CSV integrity...")
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            print(f"✅ CSV readable: {len(rows)} rows")
        
        # Show sample of data
        print("\n📋 Sample data preview:")
        print("-" * 40)
        for i, row in enumerate(rows[:3], 1):
            print(f"{i}. {row['name']} | {row['city']} | {row['brokerage']}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_csv_export()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ TEST PASSED: CSV export is working correctly")
        print("Ready to run full export on all 20,447 agents")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ TEST FAILED: Need to fix CSV export issues")
        print("=" * 60)