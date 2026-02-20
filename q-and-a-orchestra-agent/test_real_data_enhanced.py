#!/usr/bin/env python3
"""
Test script for EnhancedHybridEmailAgent using real data from data/all_agents.json
"""

import json
import asyncio
import logging
import os
import random
from enhanced_hybrid_agent import EnhancedHybridEmailAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_with_real_data():
    print("🚀 Starting Enhanced Hybrid Email Agent Test with Real Data")
    print("=" * 60)

    # 1. Load Real Data
    data_path = 'data/all_agents.json'
    if not os.path.exists(data_path):
        print(f"❌ Error: Data file not found at {data_path}")
        return

    print(f"📂 Loading data from {data_path}...")
    try:
        with open(data_path, 'r') as f:
            all_agents = json.load(f)
        print(f"✅ Loaded {len(all_agents)} agents.")
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        return

    # 2. Filter for meaningful test cases
    # We want agents that are Licensed and have a Brokerage listed to test the extraction logic
    test_candidates = [
        a for a in all_agents 
        if a.get('status') == 'Licensed' 
        and a.get('brokerage') 
        and len(a.get('brokerage')) > 5
    ]
    
    if not test_candidates:
        print("❌ No suitable test candidates found (Licensed with Brokerage).")
        return

    print(f"🔍 Found {len(test_candidates)} suitable candidates for testing.")
    
    # Select a small batch (e.g., 5 random agents)
    # Using a fixed seed for reproducibility if needed, or random for variety
    batch_size = 5
    test_batch = random.sample(test_candidates, min(batch_size, len(test_candidates)))
    
    print("\n📋 Selected Test Batch:")
    for i, agent in enumerate(test_batch):
        print(f"  {i+1}. {agent.get('name')} | {agent.get('brokerage')} | {agent.get('city', 'N/A')}")

    # 3. Initialize Agent
    print("\n🤖 Initializing EnhancedHybridEmailAgent...")
    # We can tune config here if needed
    config = {
        'use_context_compression': True,
        'use_smart_routing': True,
        'use_pattern_learning': True,
        'use_sequential_execution': True,
        'priority': 'balanced',
        'budget_per_agent': 0.02 # Slightly higher budget for testing
    }
    agent = EnhancedHybridEmailAgent(config)

    # 4. Run Processing
    print("\n⚡ Processing batch...")
    results = await agent.process_batch(test_batch)

    # 5. Display Results
    print("\n📊 Results:")
    print("=" * 60)
    
    for i, (agent_data, result) in enumerate(zip(test_batch, results)):
        print(f"\nAgent: {agent_data.get('name')}")
        print(f"Brokerage: {agent_data.get('brokerage')}")
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
        else:
            emails = result.get('emails', [])
            if emails:
                print(f"✅ Emails Found: {emails}")
            else:
                print("⚠️  No emails found")
            
            print(f"Method: {result.get('method', 'unknown')}")
            
            # Show metadata highlights
            meta = result.get('processing_metadata', {})
            print(f"Archetypes: {', '.join(meta.get('archetypes_used', []))}")
            if meta.get('compression_ratio'):
                print(f"Compression: {meta['compression_ratio']:.2f}x")
            
            routing = meta.get('routing_metadata', {})
            if routing:
                print(f"Model: {routing.get('selected_model')} (Cost: ${routing.get('estimated_cost', 0):.5f})")

    # 6. Performance Report
    print("\n📈 Final Performance Report")
    print("-" * 60)
    report = agent.get_performance_report()
    metrics = report['metrics']
    
    print(f"Total Processed: {metrics['total_processed']}")
    print(f"Successful Extractions: {metrics['successful_extractions']}")
    print(f"Patterns Used: {metrics['patterns_used']}")
    print(f"Estimated Cost Saved: ${report['routing_stats'].get('cost_savings', 0):.4f}")
    
    print("\n✅ Test Complete.")

if __name__ == "__main__":
    asyncio.run(test_with_real_data())
