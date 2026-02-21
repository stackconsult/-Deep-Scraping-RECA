
import asyncio
import json
import logging
from enhanced_hybrid_agent import EnhancedHybridEmailAgent

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_failures():
    print("🚀 Testing Previous Failures with New Logic")
    
    # The 8 failure cases from the last run
    failures = [
        {
            "name": ". Satbir Singh",
            "first_name": ".",
            "last_name": "Satbir Singh",
            "brokerage": "Triple Gold Ltd. o/a Initia Real Estate",
            "city": "Edmonton",
            "drill_id": "failure_1"
        },
        {
            "name": "RAFIK HAMDI BERJAK",
            "first_name": "RAFIK",
            "last_name": "BERJAK",
            "brokerage": "STERLING REALTY (ALBERTA) LTD. O/A STERLING REAL ESTATE",
            "city": "Edmonton",
            "drill_id": "failure_2"
        },
        {
            "name": "Juan Pablo Soto Aguilar",
            "first_name": "Juan",
            "last_name": "Soto Aguilar",
            "brokerage": "Power Properties Ltd.  O/A Power Properties",
            "city": "Calgary",
            "drill_id": "failure_3"
        },
        {
            "name": "Muhammad Asif Siddique Gill",
            "first_name": "Muhammad",
            "last_name": "Gill",
            "brokerage": "Elite Ownership Group Ltd. O/A Re/Max Elite",
            "city": "Edmonton",
            "drill_id": "failure_4"
        },
        {
            "name": "Amanda Phyllis May Edwards",
            "first_name": "Amanda",
            "last_name": "Edwards",
            "brokerage": "AYRE & OXFORD INC.",
            "city": "Edmonton",
            "drill_id": "failure_5"
        },
        {
            "name": ". Amandeep Singh",
            "first_name": ".",
            "last_name": "Amandeep Singh",
            "brokerage": "Diamond Realty & Associates Ltd",
            "city": "Calgary",
            "drill_id": "failure_6"
        },
        {
            "name": "Kirsten Dorothea Kemprud Evans",
            "first_name": "Kirsten",
            "last_name": "Evans",
            "brokerage": "RE/MAX Real Estate Calgary South Ltd. O/A RE/MAX First",
            "city": "Calgary",
            "drill_id": "failure_7"
        },
        {
            "name": "Miladin Peric",
            "first_name": "Miladin",
            "last_name": "Peric",
            "brokerage": "HOMES & GARDENS REAL ESTATE LIMITED",
            "city": "Edmonton",
            "drill_id": "failure_8"
        }
    ]

    agent = EnhancedHybridEmailAgent({
        'use_context_compression': True,
        'use_smart_routing': True,
        'use_sequential_execution': True,
        'use_pattern_learning': True
    })
    
    print(f"\n⚡ Processing {len(failures)} agents...")
    results = await agent.process_batch(failures)
    
    success_count = 0
    for i, result in enumerate(results):
        name = failures[i]['name']
        emails = result.get('emails', [])
        status = "✅" if emails else "❌"
        if emails: success_count += 1
        
        domain = result.get('domain', 'N/A')
        website = result.get('website', 'N/A') # Might be in root or search step
        if not website:
             # Try to find it in the search step data if it exists in the result structure
             pass
             
        print(f"{status} {name}")
        print(f"   Brokerage: {failures[i]['brokerage']}")
        print(f"   Emails: {emails}")
        print(f"   Method: {result.get('extraction_method', 'N/A')}")
        print(f"   Domain: {domain}")
        print("-" * 40)

    print(f"\nResults: {success_count}/{len(failures)} recovered")

if __name__ == "__main__":
    asyncio.run(test_failures())
