#!/usr/bin/env python3
"""
Debug script to test RECA drillthrough functionality.
This will help identify why phone/email extraction is failing.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from integrations.reca_scraper_logic import RECAHttpScraper
import json
from datetime import datetime

def test_drillthrough():
    """Test drillthrough with a sample agent."""
    scraper = RECAHttpScraper()
    
    print("=== RECA Drillthrough Debug Test ===")
    print(f"Timestamp: {datetime.now()}")
    
    # Test a few sample drill IDs from the checkpoint
    sample_drill_ids = [
        "302iT2R0x643",  # First in list
        "302iT2R0x294",  # Second in list
        "302iT2R0x827",  # Third in list
    ]
    
    for drill_id in sample_drill_ids:
        print(f"\n--- Testing drill ID: {drill_id} ---")
        
        try:
            # First, let's check if we can even reach the base URL
            print("Testing base URL accessibility...")
            response = scraper.session.get(scraper.BASE_URL, timeout=10)
            print(f"Base URL status: {response.status_code}")
            
            if response.status_code == 404:
                print("ERROR: Base URL returns 404! This is the root cause.")
                print("The RECA site structure has changed.")
                continue
            
            # Try the drillthrough
            print("Attempting drillthrough...")
            result = scraper.perform_drillthrough(drill_id)
            
            if result:
                print(f"Result: {result}")
                if result.get('email'):
                    print(f"✅ Email found: {result['email']}")
                else:
                    print("❌ No email extracted")
                    
                if result.get('phone'):
                    print(f"✅ Phone found: {result['phone']}")
                else:
                    print("❌ No phone extracted")
            else:
                print("❌ Drillthrough returned None")
                
        except Exception as e:
            print(f"❌ Error during drillthrough: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Let's also try a fresh search to see if we can get new drill IDs
    print("\n--- Testing fresh search ---")
    try:
        agents = scraper.search_by_lastname("A")
        if agents:
            print(f"Found {len(agents)} agents with last name starting with 'A'")
            if agents and agents[0].get('drill_id'):
                test_drill_id = agents[0]['drill_id']
                print(f"Testing fresh drill ID: {test_drill_id}")
                result = scraper.perform_drillthrough(test_drill_id)
                print(f"Fresh drillthrough result: {result}")
        else:
            print("No agents found in fresh search")
    except Exception as e:
        print(f"Error in fresh search: {str(e)}")

if __name__ == "__main__":
    test_drillthrough()