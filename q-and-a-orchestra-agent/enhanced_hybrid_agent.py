#!/usr/bin/env python3
"""
Enhanced Hybrid Email Agent with All Archetypes
Complete implementation integrating all agent archetypes from Awesome LLM Apps
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

# Import all archetypes
from agents.context_optimizer import ContextCompressor
from agents.sequential_executor import SequentialExecutor
from agents.pattern_recognition import PatternExtractor, PatternMatcher, PatternLearner
from agents.model_router import SmartRouter, TaskType

# Import existing components
from google_integration.ollama_client import OllamaHybridClient
from google_integration.gemini_client import GeminiHybridClient
from google_integration.mem0_memory import Mem0MemoryManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedHybridEmailAgent:
    """Enhanced hybrid agent with all archetypes integrated"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the enhanced hybrid agent"""
        # Core components
        self.ollama = OllamaHybridClient()
        self.gemini = GeminiHybridClient()
        self.memory = Mem0MemoryManager()
        
        # Archetypes
        self.compressor = ContextCompressor()
        self.executor = SequentialExecutor()
        self.pattern_extractor = PatternExtractor()
        self.pattern_matcher = PatternMatcher()
        self.pattern_learner = PatternLearner()
        self.router = SmartRouter()
        
        # Configuration
        self.config = config or self._default_config()
        
        # Performance metrics
        self.metrics = {
            'total_processed': 0,
            'successful_extractions': 0,
            'cache_hits': 0,
            'patterns_used': 0,
            'cost_saved': 0.0,
            'compression_savings': 0.0,
            'routing_decisions': 0
        }
        
        # Load learned patterns from memory
        asyncio.create_task(self._load_patterns_from_memory())
        
        logger.info("Enhanced Hybrid Email Agent initialized with all archetypes")
    
    def _default_config(self) -> Dict:
        """Default configuration"""
        return {
            'use_context_compression': True,
            'use_smart_routing': True,
            'use_pattern_learning': True,
            'use_sequential_execution': True,
            'compression_threshold': 100,  # Compress if >100 tokens
            'budget_per_agent': 0.01,  # $0.01 per agent max
            'priority': 'balanced'  # 'cost_sensitive', 'quality_first', 'speed_first', 'balanced'
        }
    
    async def process_agent(self, agent_data: Dict) -> Dict:
        """Process a single agent with all archetypes"""
        start_time = datetime.now()
        self.metrics['total_processed'] += 1
        
        try:
            # Step 1: Check memory for existing results
            cached_result = await self._check_agent_memory(agent_data.get('drill_id'))
            if cached_result:
                self.metrics['cache_hits'] += 1
                return cached_result
            
            # Step 2: Apply context compression if enabled
            if self.config['use_context_compression']:
                original_size = len(json.dumps(agent_data))
                compressed_context = self.compressor.compress_agent(agent_data)
                compression_ratio = original_size / len(compressed_context)
                self.metrics['compression_savings'] += original_size - len(compressed_context)
                
                if compression_ratio > 1.2:  # Only use if significant savings
                    agent_data['_compressed'] = compressed_context
                    agent_data['_compression_ratio'] = compression_ratio
            
            # Step 3: Determine task type and route
            task_type = self._determine_task_type(agent_data)
            
            if self.config['use_smart_routing']:
                decision = await self.router.route(
                    task_type,
                    agent_data,
                    budget_constraint=self.config['budget_per_agent'],
                    priority=self.config['priority']
                )
                self.metrics['routing_decisions'] += 1
                selected_model = decision.selected_model
                routing_metadata = decision.__dict__
            else:
                selected_model = 'llama3.3:70b'  # Default
                routing_metadata = {}
            
            # Step 4: Execute with appropriate method
            if self.config['use_sequential_execution']:
                # Use sequential executor
                result = await self._execute_sequential(agent_data, selected_model)
            else:
                # Use direct model execution
                result = await self._execute_direct(agent_data, selected_model, task_type)
            
            # Step 5: Apply pattern learning if enabled
            if self.config['use_pattern_learning'] and result.get('emails'):
                await self._learn_from_extraction(agent_data, result)
            
            # Step 6: Store in memory
            await self._store_result(agent_data, result)
            
            # Step 7: Update metrics
            if result.get('emails'):
                self.metrics['successful_extractions'] += 1
            
            # Add metadata
            result['processing_metadata'] = {
                **result.get('processing_metadata', {}),
                'archetypes_used': self._get_used_archetypes(),
                'routing_metadata': routing_metadata,
                'compression_ratio': agent_data.get('_compression_ratio'),
                'processing_time': (datetime.now() - start_time).total_seconds()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing agent {agent_data.get('name', 'unknown')}: {e}")
            return {
                'error': str(e),
                'agent_name': agent_data.get('name', ''),
                'emails': [],
                'method': 'error'
            }
    
    async def process_batch(self, agents: List[Dict], 
                           batch_size: int = 10) -> List[Dict]:
        """Process multiple agents in batches"""
        results = []
        
        for i in range(0, len(agents), batch_size):
            batch = agents[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(agents)-1)//batch_size + 1}")
            
            # Process batch in parallel
            tasks = [self.process_agent(agent) for agent in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    results.append({
                        'error': str(result),
                        'emails': []
                    })
                else:
                    results.append(result)
        
        return results
    
    async def _execute_sequential(self, agent_data: Dict, model: str) -> Dict:
        """Execute using sequential executor"""
        # Enhance agent data with model preference
        agent_data['_preferred_model'] = model
        
        # Execute workflow
        result = await self.executor.execute(agent_data)
        
        if result.success:
            return result.data
        else:
            return {
                'error': result.error,
                'emails': [],
                'method': 'sequential_failed'
            }
    
    async def _execute_direct(self, agent_data: Dict, model: str, 
                             task_type: TaskType) -> Dict:
        """Execute directly with selected model"""
        # Prepare content based on task type
        content = self._prepare_content(agent_data, task_type)
        
        # Route to appropriate client
        if model.startswith('gemini'):
            result = await self.gemini.extract_emails(
                content=content,
                agent_data=agent_data,
                model=model
            )
        else:
            # Determine if using cloud or local for Ollama
            use_cloud = 'cloud' in model
            
            # Execute with Ollama
            result = await self.ollama.extract_emails(
                content=content,
                agent_data=agent_data,
                use_cloud=use_cloud
            )
        
        return result
    
    def _determine_task_type(self, agent_data: Dict) -> TaskType:
        """Determine task type based on agent data"""
        brokerage = agent_data.get('brokerage', '').lower()
        
        # Complex extraction for large brokerages
        if any(b in brokerage for b in ['remax', 'royal lepage', 'century 21']):
            return TaskType.COMPLEX_EXTRACTION
        
        # Pattern generation if we have history
        if self.pattern_learner.get_best_patterns(self._classify_brokerage(brokerage)):
            return TaskType.PATTERN_GENERATION
        
        # Default to web scraping
        return TaskType.WEB_SCRAPING
    
    def _prepare_content(self, agent_data: Dict, task_type: TaskType) -> str:
        """Prepare content based on task type"""
        if task_type == TaskType.PATTERN_GENERATION:
            # Include pattern hints
            patterns = self.pattern_learner.get_best_patterns(
                self._classify_brokerage(agent_data.get('brokerage', '')),
                top_k=3
            )
            pattern_hints = "\nKnown patterns:\n" + "\n".join(p.template for p in patterns)
            return f"Extract emails using these patterns:\n{pattern_hints}\n\nAgent: {json.dumps(agent_data)}"
        
        else:
            # Standard content
            return f"Extract email addresses for this real estate agent: {json.dumps(agent_data)}"
    
    async def _learn_from_extraction(self, agent_data: Dict, result: Dict):
        """Learn from successful extraction"""
        emails = result.get('emails', [])
        if not emails:
            return
        
        # Extract pattern from first email
        email = emails[0]
        domain = self._extract_domain(agent_data.get('brokerage', ''))
        
        pattern = self.pattern_extractor.extract_pattern(email, agent_data, domain)
        if pattern:
            # Learn from successful pattern
            self.pattern_learner.learn_from_result(pattern, True, 0.9)
            self.metrics['patterns_used'] += 1
            
            # Store in Mem0
            await self.memory.add_skill(
                skill_name=f"{pattern.brokerage_type}_pattern_{pattern.success_count}",
                pattern=pattern.template,
                brokerage_type=pattern.brokerage_type,
                confidence=pattern.confidence,
                success_count=pattern.success_count
            )
    
    async def _check_agent_memory(self, agent_id: str) -> Optional[Dict]:
        """Check if we already have results for this agent"""
        if not agent_id:
            return None
        
        history = await self.memory.get_agent_history(agent_id)
        if history:
            # Return most recent successful result
            for record in reversed(history):
                if record.get('extraction_result', {}).get('emails'):
                    logger.info(f"Found cached result for agent {agent_id}")
                    return record['extraction_result']
        
        return None
    
    async def _store_result(self, agent_data: Dict, result: Dict):
        """Store result in memory"""
        agent_id = agent_data.get('drill_id')
        if not agent_id:
            return
        
        # Store touch point
        await self.memory.add_touch_point(
            agent_id=agent_id,
            agent_data=agent_data,
            extraction_result=result,
            strategy={'name': 'enhanced_hybrid', 'archetypes': self._get_used_archetypes()}
        )
    
    async def _load_patterns_from_memory(self):
        """Load existing patterns from memory"""
        # This would load patterns from Mem0 on startup
        # For now, patterns are learned during runtime
        pass
    
    def _classify_brokerage(self, brokerage: str) -> str:
        """Classify brokerage type"""
        if not brokerage:
            return 'independent'
        
        b = brokerage.lower()
        if 'remax' in b or 're/max' in b:
            return 'remax'
        elif 'royal lepage' in b:
            return 'royal_lepage'
        elif 'century 21' in b:
            return 'century_21'
        elif 'exp' in b:
            return 'exp_realty'
        else:
            return 'independent'
    
    def _extract_domain(self, brokerage: str) -> str:
        """Extract domain from brokerage"""
        if not brokerage:
            return ""
        
        clean = brokerage.lower()
        clean = clean.replace(' ', '').replace('.', '').replace('/', '')
        return f"{clean}.ca"
    
    def _get_used_archetypes(self) -> List[str]:
        """Get list of archetypes used"""
        used = []
        if self.config['use_context_compression']:
            used.append('context_optimizer')
        if self.config['use_smart_routing']:
            used.append('model_router')
        if self.config['use_sequential_execution']:
            used.append('sequential_executor')
        if self.config['use_pattern_learning']:
            used.append('pattern_recognition')
        
        return used
    
    def get_performance_report(self) -> Dict:
        """Get comprehensive performance report"""
        return {
            'metrics': self.metrics,
            'compression_stats': self.compressor.get_compression_report(),
            'workflow_stats': self.executor.get_workflow_stats(),
            'pattern_stats': self.pattern_learner.get_learning_stats(),
            'routing_stats': self.router.get_routing_stats(),
            'memory_stats': self.memory.get_memory_stats(),
            'ollama_stats': self.ollama.get_usage_stats(),
            'configuration': self.config
        }
    
    def update_config(self, new_config: Dict):
        """Update configuration"""
        self.config.update(new_config)
        logger.info(f"Configuration updated: {new_config}")

# Example usage
async def demonstrate_enhanced_agent():
    """Demonstrate the enhanced agent with all archetypes"""
    print("🚀 Enhanced Hybrid Email Agent Demo")
    print("=" * 60)
    
    # Initialize agent
    agent = EnhancedHybridEmailAgent({
        'use_context_compression': True,
        'use_smart_routing': True,
        'use_pattern_learning': True,
        'use_sequential_execution': True,
        'priority': 'balanced'
    })
    
    # Test agents
    test_agents = [
        {
            'name': 'John Smith',
            'first_name': 'John',
            'last_name': 'Smith',
            'brokerage': 'RE/MAX Excellence',
            'city': 'Calgary',
            'drill_id': 'demo_001'
        },
        {
            'name': 'Sarah Johnson',
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'brokerage': 'Royal LePage Riverbend',
            'city': 'Edmonton',
            'drill_id': 'demo_002'
        },
        {
            'name': 'Mike Wilson',
            'first_name': 'Mike',
            'last_name': 'Wilson',
            'brokerage': 'Century 21 Downtown',
            'city': 'Calgary',
            'drill_id': 'demo_003'
        }
    ]
    
    # Process agents
    print("\n📊 Processing agents with all archetypes...")
    results = await agent.process_batch(test_agents)
    
    # Display results
    for i, (agent_data, result) in enumerate(zip(test_agents, results)):
        print(f"\nAgent {i+1}: {agent_data['name']}")
        print(f"  Brokerage: {agent_data['brokerage']}")
        print(f"  Emails Found: {result.get('emails', [])}")
        print(f"  Method: {result.get('method', 'unknown')}")
        
        if 'processing_metadata' in result:
            metadata = result['processing_metadata']
            print(f"  Archetypes Used: {', '.join(metadata.get('archetypes_used', []))}")
            print(f"  Processing Time: {metadata.get('processing_time', 0):.2f}s")
            
            if metadata.get('compression_ratio'):
                print(f"  Compression: {metadata['compression_ratio']:.1f}x")
            
            if metadata.get('routing_metadata'):
                routing = metadata['routing_metadata']
                print(f"  Selected Model: {routing.get('selected_model', 'N/A')}")
                print(f"  Est. Cost: ${routing.get('estimated_cost', 0):.4f}")
    
    # Performance report
    print("\n📈 Performance Report")
    print("-" * 40)
    report = agent.get_performance_report()
    
    metrics = report['metrics']
    print(f"Total Processed: {metrics['total_processed']}")
    print(f"Successful Extractions: {metrics['successful_extractions']}")
    print(f"Cache Hits: {metrics['cache_hits']}")
    print(f"Patterns Used: {metrics['patterns_used']}")
    print(f"Compression Savings: {metrics['compression_savings']} tokens")
    print(f"Routing Decisions: {metrics['routing_decisions']}")
    
    compression = report['compression_stats']
    print(f"\nCompression Stats:")
    print(f"  Savings: {compression['savings_percent']:.1f}%")
    
    routing = report['routing_stats']
    print(f"\nRouting Stats:")
    print(f"  Cost Savings: ${routing['cost_savings']:.4f}")
    
    patterns = report['pattern_stats']
    print(f"\nPattern Stats:")
    print(f"  Patterns Learned: {patterns['total_patterns_learned']}")
    
    print("\n✅ Demo complete! All archetypes working together.")

if __name__ == "__main__":
    asyncio.run(demonstrate_enhanced_agent())
