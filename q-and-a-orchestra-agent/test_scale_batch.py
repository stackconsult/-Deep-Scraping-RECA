#!/usr/bin/env python3
"""
Scale Test Script for EnhancedHybridEmailAgent
Runs a larger batch (50 agents) to verify stability, rate limiting, and performance at scale.
"""

import json
import asyncio
import logging
import os
import random
import time
from datetime import datetime
from enhanced_hybrid_agent import EnhancedHybridEmailAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def run_scale_test():
    print("🚀 Starting Scale Test (Target: 50 Agents)")
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
    # Licensed agents with Brokerage info
    test_candidates = [
        a for a in all_agents 
        if a.get('status') == 'Licensed' 
        and a.get('brokerage') 
        and len(a.get('brokerage')) > 5
    ]
    
    if len(test_candidates) < 50:
        print(f"⚠️ Warning: Only found {len(test_candidates)} candidates. Running with all of them.")
        test_batch = test_candidates
    else:
        # Random sample of 50
        # Set seed for reproducibility if needed, but random is good for variety here
        test_batch = random.sample(test_candidates, 50)
    
    print(f"📋 Selected Batch Size: {len(test_batch)}")

    # 3. Initialize Agent with robust config
    print("\n🤖 Initializing EnhancedHybridEmailAgent...")
    config = {
        'use_context_compression': True,
        'use_smart_routing': True,
        'use_pattern_learning': True,
        'use_sequential_execution': True,
        'priority': 'balanced',
        'budget_per_agent': 0.05,  # Increased budget for scale test
        'max_retries': 2
    }
    agent = EnhancedHybridEmailAgent(config)

    # 4. Run Processing
    start_time = time.time()
    print("\n⚡ Processing batch (this may take a few minutes)...")
    
    # Process in chunks of 10 to avoid overwhelming everything at once if needed, 
    # but process_batch handles concurrency (default 5). 
    # Let's just pass the whole batch and let the agent manage semaphore.
    results = await agent.process_batch(test_batch)
    
    duration = time.time() - start_time
    print(f"\n✅ Batch processing complete in {duration:.2f} seconds")

    # 5. Analyze Results
    print("\n📊 Scale Test Results Analysis:")
    print("=" * 60)
    
    successful = 0
    failed = 0
    errors = 0
    
    for i, result in enumerate(results):
        if 'error' in result:
            errors += 1
            print(f"Error for agent {i}: {result['error']}")
        elif result.get('emails'):
            successful += 1
            print(f"Success for agent {i}: {result['emails']}")
        else:
            failed += 1 # No error, but no email found
            print(f"No result for agent {i}")
            
    print(f"Total Processed: {len(results)}")
    print(f"✅ Success (Email Found): {successful} ({(successful/len(results))*100:.1f}%)")
    print(f"⚠️  No Result (Valid):     {failed}")
    print(f"❌ Errors:                {errors}")
    
    # 6. Performance Report
    print("\n📈 Final Performance Metrics")
    print("-" * 60)
    report = agent.get_performance_report()
    
    print(f"Patterns Learned/Used: {report['metrics']['patterns_used']}")
    print(f"Cache Hits: {report['metrics']['cache_hits']}")
    
    # Save detailed results to file
    output_file = f"data/scale_test_results_{int(time.time())}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total': len(results),
                'success': successful,
                'failed': failed,
                'errors': errors,
                'duration': duration
            },
            'results': results
        }, f, indent=2)
        
    print(f"\n💾 Detailed results saved to {output_file}")

if __name__ == "__main__":
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    asyncio.run(run_scale_test())
