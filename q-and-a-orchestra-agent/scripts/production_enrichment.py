#!/usr/bin/env python3
"""
Production Email Enrichment Script
Wraps the EnhancedHybridEmailAgent to process the full RECA agent dataset.
Supports checkpointing, batch processing, and graceful resumption.
"""

import asyncio
import json
import logging
import os
import argparse
import time
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import agent
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_hybrid_agent import EnhancedHybridEmailAgent
from config.settings import settings
from core.logging_setup import setup_logging

# Configure logging
setup_logging(
    log_level=settings.LOG_LEVEL if settings else "INFO",
    enable_json=settings.ENABLE_JSON_LOGGING if settings else False,
    service_name="reca-production-enrichment"
)
logger = logging.getLogger(__name__)

class EnrichmentOrchestrator:
    def __init__(self, input_file: str, output_file: str, batch_size: int = 10, resume: bool = True):
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        self.batch_size = batch_size
        self.resume = resume
        
        # Initialize Agent
        self.agent = EnhancedHybridEmailAgent({
            'use_context_compression': True,
            'use_smart_routing': True,
            'use_pattern_learning': True,
            'use_sequential_execution': True,
            'priority': 'balanced',
            'budget_per_agent': 0.02,
            'max_retries': 2
        })
        
        self.stats = {
            "total": 0,
            "processed": 0,
            "success": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0
        }

    def load_data(self) -> List[Dict[str, Any]]:
        """Load source data."""
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")
            
        with open(self.input_file, 'r') as f:
            data = json.load(f)
            self.stats["total"] = len(data)
            return data

    def load_processed_data(self) -> Dict[str, Dict[str, Any]]:
        """Load already processed data if resuming."""
        if not self.resume or not self.output_file.exists():
            return {}
            
        try:
            with open(self.output_file, 'r') as f:
                data = json.load(f)
                # Map by drill_id for easy lookup
                processed_map = {item.get('drill_id', f"idx_{i}"): item for i, item in enumerate(data)}
                logger.info(f"Resuming with {len(processed_map)} already processed agents.")
                return processed_map
        except json.JSONDecodeError:
            logger.warning("Output file exists but is invalid JSON. Starting fresh.")
            return {}

    def save_checkpoint(self, data: List[Dict[str, Any]]):
        """Save progress to output file."""
        temp_file = self.output_file.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=2)
        os.replace(temp_file, self.output_file)
        logger.info(f"Checkpoint saved. Processed: {self.stats['processed']}/{self.stats['total']}")

    async def process(self):
        """Main processing loop."""
        logger.info(f"Starting enrichment process. Input: {self.input_file}, Output: {self.output_file}")
        
        all_agents = self.load_data()
        processed_map = self.load_processed_data()
        
        # Convert processed map back to list to maintain order if possible, 
        # or just start building the final list
        final_list = []
        
        # Identify pending agents
        pending_agents = []
        for agent in all_agents:
            drill_id = agent.get('drill_id')
            if drill_id and drill_id in processed_map:
                final_list.append(processed_map[drill_id])
                self.stats["skipped"] += 1
            else:
                pending_agents.append(agent)
        
        # Apply limit if set
        if hasattr(self, 'limit') and self.limit:
            logger.info(f"Limiting processing to first {self.limit} pending agents.")
            pending_agents = pending_agents[:self.limit]
        
        logger.info(f"Agents to process: {len(pending_agents)} (Skipped {self.stats['skipped']})")
        
        # Process in batches
        for i in range(0, len(pending_agents), self.batch_size):
            batch = pending_agents[i : i + self.batch_size]
            logger.info(f"Processing batch {i // self.batch_size + 1}/{(len(pending_agents) + self.batch_size - 1) // self.batch_size}")
            
            try:
                results = await self.agent.process_batch(batch)
                
                for original, result in zip(batch, results):
                    # Merge result into original agent data
                    enriched = original.copy()
                    
                    if result.get('emails'):
                        enriched['email'] = result['emails'][0] # Primary email
                        enriched['emails'] = result['emails']   # All emails
                        enriched['enrichment_status'] = 'success'
                        enriched['enrichment_metadata'] = result
                        self.stats["success"] += 1
                    else:
                        enriched['enrichment_status'] = 'failed'
                        enriched['enrichment_metadata'] = result
                        self.stats["failed"] += 1
                        
                    if 'error' in result:
                        self.stats["errors"] += 1
                        
                    final_list.append(enriched)
                    self.stats["processed"] += 1
                
                # Save checkpoint after every batch
                self.save_checkpoint(final_list)
                
            except Exception as e:
                logger.error(f"Batch failed: {e}")
                # Don't crash the whole run, but maybe pause?
                await asyncio.sleep(5)
        
        logger.info("Enrichment complete.")
        logger.info(f"Final Stats: {self.stats}")

async def main():
    parser = argparse.ArgumentParser(description="RECA Production Email Enrichment")
    parser.add_argument("--input", default="data/all_agents.json", help="Input JSON file")
    parser.add_argument("--output", default="data/all_agents_enriched.json", help="Output JSON file")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for concurrency")
    parser.add_argument("--no-resume", action="store_true", help="Start fresh, ignoring existing output")
    parser.add_argument("--sample", action="store_true", help="Run on a small sample of data")
    parser.add_argument("--size", type=int, default=10, help="Sample size (if --sample used)")
    
    args = parser.parse_args()
    
    orchestrator = EnrichmentOrchestrator(
        input_file=args.input,
        output_file=args.output,
        batch_size=args.batch_size,
        resume=not args.no_resume
    )
    
    # Apply sampling if requested
    if args.sample:
        logger.info(f"Running in SAMPLE mode. Processing first {args.size} agents only.")
        # We need to hook into the process method or modify the loaded data
        # Let's subclass or just modify the orchestrator instance method slightly? 
        # Easier to just modify the load_data method or pre-process.
        # Since load_data is called inside process, let's just monkey-patch or modify the class to support limiting.
        # Better yet, let's modify the class to accept a limit.
        orchestrator.limit = args.size
    else:
        orchestrator.limit = None
    
    await orchestrator.process()

if __name__ == "__main__":
    asyncio.run(main())
