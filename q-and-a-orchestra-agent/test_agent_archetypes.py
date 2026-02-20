#!/usr/bin/env python3
"""
Complete Agent Archetypes Test Suite
Tests all implemented archetypes with integration
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

# Import all archetypes
from agents.context_optimizer import ContextCompressor
from agents.sequential_executor import SequentialExecutor
from agents.pattern_recognition import PatternExtractor, PatternMatcher, PatternLearner, EmailPattern
from agents.model_router import SmartRouter, TaskType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ArchetypeTestSuite:
    """Test suite for all agent archetypes"""
    
    def __init__(self):
        self.compressor = ContextCompressor()
        self.executor = SequentialExecutor()
        self.pattern_extractor = PatternExtractor()
        self.pattern_matcher = PatternMatcher()
        self.pattern_learner = PatternLearner()
        self.router = SmartRouter()
        
        self.test_results = {
            'context_optimizer': {},
            'sequential_executor': {},
            'pattern_recognition': {},
            'model_router': {},
            'integration': {}
        }
    
    async def run_all_tests(self):
        """Run all archetype tests"""
        print("\n🚀 Agent Archetypes Test Suite")
        print("=" * 60)
        
        # Test each archetype
        await self.test_context_optimizer()
        await self.test_sequential_executor()
        await self.test_pattern_recognition()
        await self.test_model_router()
        
        # Test integration
        await self.test_full_integration()
        
        # Generate report
        self.generate_report()
    
    async def test_context_optimizer(self):
        """Test context compression"""
        print("\n📊 Testing Context Optimizer")
        print("-" * 40)
        
        test_agents = [
            {
                'name': 'John Smith',
                'first_name': 'John',
                'last_name': 'Smith',
                'brokerage': 'RE/MAX Excellence',
                'city': 'Calgary'
            },
            {
                'name': 'Sarah Johnson',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'brokerage': 'Royal LePage Riverbend',
                'city': 'Edmonton'
            }
        ]
        
        # Test compression
        compressed = self.compressor.compress_batch(test_agents)
        
        # Test decompression
        decompressed = [self.compressor.decompress_agent(c) for c in compressed]
        
        # Calculate savings
        report = self.compressor.get_compression_report()
        
        print(f"  Original tokens: {report['original_tokens']}")
        print(f"  Compressed tokens: {report['compressed_tokens']}")
        print(f"  Savings: {report['savings_percent']:.1f}%")
        print(f"  Agents processed: {report['total_processed']}")
        
        # Verify data integrity
        integrity_check = all(
            agent['first_name'] == decomp['first_name'] and
            agent['last_name'] == decomp['last_name']
            for agent, decomp in zip(test_agents, decompressed)
        )
        
        print(f"  Data integrity: {'✅' if integrity_check else '❌'}")
        
        self.test_results['context_optimizer'] = {
            'savings_percent': report['savings_percent'],
            'data_integrity': integrity_check,
            'tokens_saved': report['original_tokens'] - report['compressed_tokens']
        }
    
    async def test_sequential_executor(self):
        """Test sequential agent execution"""
        print("\n🔄 Testing Sequential Executor")
        print("-" * 40)
        
        test_agent = {
            'name': 'Mike Wilson',
            'first_name': 'Mike',
            'last_name': 'Wilson',
            'brokerage': 'Century 21 Downtown',
            'city': 'Calgary',
            'drill_id': 'test_001'
        }
        
        # Execute workflow
        result = await self.executor.execute(test_agent)
        
        print(f"  Workflow success: {'✅' if result.success else '❌'}")
        print(f"  Execution time: {result.execution_time:.2f}s")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Emails found: {result.data.get('email_count', 0)}")
        
        if result.metadata.get('workflow_state'):
            workflow = result.metadata['workflow_state']
            print(f"  Steps completed: {workflow['steps_completed']}/{workflow['total_steps']}")
        
        # Get workflow stats
        stats = self.executor.get_workflow_stats()
        print(f"  Workflow success rate: {stats['success_rate']:.1f}%")
        
        self.test_results['sequential_executor'] = {
            'success': result.success,
            'execution_time': result.execution_time,
            'emails_found': result.data.get('email_count', 0),
            'workflow_success_rate': stats['success_rate']
        }
    
    async def test_pattern_recognition(self):
        """Test pattern recognition and learning"""
        print("\n🧠 Testing Pattern Recognition")
        print("-" * 40)
        
        # Test pattern extraction
        test_cases = [
            {
                'email': 'john.smith@remax.net',
                'agent': {
                    'first_name': 'John',
                    'last_name': 'Smith',
                    'brokerage': 'RE/MAX Excellence'
                },
                'domain': 'remax.net'
            },
            {
                'email': 'sarahj@royallepage.ca',
                'agent': {
                    'first_name': 'Sarah',
                    'last_name': 'Johnson',
                    'brokerage': 'Royal LePage'
                },
                'domain': 'royallepage.ca'
            }
        ]
        
        extracted_patterns = []
        for case in test_cases:
            pattern = self.pattern_extractor.extract_pattern(
                case['email'], case['agent'], case['domain']
            )
            if pattern:
                extracted_patterns.append(pattern)
                print(f"  Extracted pattern: {pattern.template}")
        
        # Test pattern matching
        test_agent = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'brokerage': 'RE/MAX Premier'
        }
        
        if extracted_patterns:
            matches = self.pattern_matcher.match_patterns(
                test_agent, extracted_patterns, 'remax.net'
            )
            
            print(f"  Pattern matches: {len(matches)}")
            for pattern, email in matches[:2]:
                print(f"    {pattern.template} -> {email}")
        
        # Test learning
        for pattern in extracted_patterns:
            self.pattern_learner.learn_from_result(pattern, True, 0.9)
        
        # Get best patterns
        best_patterns = self.pattern_learner.get_best_patterns('remax')
        print(f"  Best patterns for RE/MAX: {len(best_patterns)}")
        
        # Get learning stats
        stats = self.pattern_learner.get_learning_stats()
        print(f"  Total patterns learned: {stats['total_patterns_learned']}")
        
        self.test_results['pattern_recognition'] = {
            'patterns_extracted': len(extracted_patterns),
            'patterns_matched': len(matches) if extracted_patterns else 0,
            'patterns_learned': stats['total_patterns_learned']
        }
    
    async def test_model_router(self):
        """Test smart model routing"""
        print("\n🧭 Testing Smart Model Router")
        print("-" * 40)
        
        # Test routing for different tasks
        test_tasks = [
            (TaskType.SIMPLE_VALIDATION, {'email': 'test@example.com'}),
            (TaskType.COMPLEX_EXTRACTION, {'content': 'Long text...'}),
            (TaskType.PATTERN_GENERATION, {'patterns': []})
        ]
        
        routing_decisions = []
        
        for task_type, data in test_tasks:
            decision = await self.router.route(task_type, data)
            routing_decisions.append(decision)
            
            print(f"  Task: {task_type.value}")
            print(f"    Selected model: {decision.selected_model}")
            print(f"    Estimated cost: ${decision.estimated_cost:.4f}")
            print(f"    Confidence: {decision.confidence:.2f}")
            print(f"    Reasoning: {decision.reasoning}")
        
        # Test execution with routing
        async def mock_execution(model_name: str, data: Dict) -> Dict:
            return {'result': f'Mock execution by {model_name}', 'data': data}
        
        result = await self.router.execute_with_routing(
            TaskType.WEB_SCRAPING,
            {'url': 'https://example.com'},
            mock_execution
        )
        
        print(f"  Execution with routing: {'✅' if 'result' in result else '❌'}")
        
        # Get routing stats
        stats = self.router.get_routing_stats()
        print(f"  Total routes: {stats['total_routes']}")
        print(f"  Cost savings: ${stats['cost_savings']:.4f}")
        
        self.test_results['model_router'] = {
            'decisions_made': len(routing_decisions),
            'execution_success': 'result' in result,
            'cost_savings': stats['cost_savings']
        }
    
    async def test_full_integration(self):
        """Test full integration of all archetypes"""
        print("\n🔗 Testing Full Integration")
        print("-" * 40)
        
        test_agents = [
            {
                'name': 'Alice Brown',
                'first_name': 'Alice',
                'last_name': 'Brown',
                'brokerage': 'RE/MAX Mountain View',
                'city': 'Banff',
                'drill_id': 'integration_001'
            },
            {
                'name': 'Bob Davis',
                'first_name': 'Bob',
                'last_name': 'Davis',
                'brokerage': 'Exp Realty Urban',
                'city': 'Calgary',
                'drill_id': 'integration_002'
            }
        ]
        
        integration_results = []
        
        for agent in test_agents:
            print(f"\n  Processing: {agent['name']}")
            
            # Step 1: Compress context
            compressed = self.compressor.compress_agent(agent)
            
            # Step 2: Route to appropriate model
            task_type = TaskType.COMPLEX_EXTRACTION
            decision = await self.router.route(task_type, agent)
            
            # Step 3: Execute with sequential agents
            result = await self.executor.execute(agent)
            
            # Step 4: Learn from results
            if result.success and result.data.get('emails'):
                for email in result.data['emails'][:1]:  # Learn from first email
                    pattern = self.pattern_extractor.extract_pattern(
                        email, agent, agent.get('brokerage', '').lower() + '.ca'
                    )
                    if pattern:
                        self.pattern_learner.learn_from_result(pattern, True, 0.9)
            
            integration_results.append({
                'agent': agent['name'],
                'success': result.success,
                'emails': result.data.get('email_count', 0),
                'compression_ratio': len(json.dumps(agent)) / len(compressed),
                'selected_model': decision.selected_model
            })
            
            print(f"    Success: {'✅' if result.success else '❌'}")
            print(f"    Emails: {result.data.get('email_count', 0)}")
            print(f"    Compression: {integration_results[-1]['compression_ratio']:.1f}x")
            print(f"    Model: {decision.selected_model}")
        
        # Calculate overall metrics
        total_success = sum(1 for r in integration_results if r['success'])
        avg_compression = sum(r['compression_ratio'] for r in integration_results) / len(integration_results)
        
        print(f"\n  Integration Summary:")
        print(f"    Success rate: {total_success}/{len(integration_results)} ({total_success/len(integration_results)*100:.1f}%)")
        print(f"    Avg compression: {avg_compression:.1f}x")
        
        self.test_results['integration'] = {
            'success_rate': total_success / len(integration_results),
            'avg_compression': avg_compression,
            'agents_processed': len(integration_results)
        }
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n📊 Test Report Summary")
        print("=" * 60)
        
        # Context Optimizer
        co = self.test_results['context_optimizer']
        print(f"\nContext Optimizer:")
        print(f"  ✅ Token savings: {co['savings_percent']:.1f}%")
        print(f"  ✅ Data integrity: {'Maintained' if co['data_integrity'] else 'Compromised'}")
        print(f"  ✅ Tokens saved: {co['tokens_saved']}")
        
        # Sequential Executor
        se = self.test_results['sequential_executor']
        print(f"\nSequential Executor:")
        print(f"  ✅ Workflow success: {'Yes' if se['success'] else 'No'}")
        print(f"  ✅ Execution time: {se['execution_time']:.2f}s")
        print(f"  ✅ Emails found: {se['emails_found']}")
        print(f"  ✅ Success rate: {se['workflow_success_rate']:.1f}%")
        
        # Pattern Recognition
        pr = self.test_results['pattern_recognition']
        print(f"\nPattern Recognition:")
        print(f"  ✅ Patterns extracted: {pr['patterns_extracted']}")
        print(f"  ✅ Patterns matched: {pr['patterns_matched']}")
        print(f"  ✅ Patterns learned: {pr['patterns_learned']}")
        
        # Model Router
        mr = self.test_results['model_router']
        print(f"\nModel Router:")
        print(f"  ✅ Routing decisions: {mr['decisions_made']}")
        print(f"  ✅ Execution success: {'Yes' if mr['execution_success'] else 'No'}")
        print(f"  ✅ Cost savings: ${mr['cost_savings']:.4f}")
        
        # Integration
        ig = self.test_results['integration']
        print(f"\nFull Integration:")
        print(f"  ✅ Overall success rate: {ig['success_rate']*100:.1f}%")
        print(f"  ✅ Average compression: {ig['avg_compression']:.1f}x")
        print(f"  ✅ Agents processed: {ig['agents_processed']}")
        
        # Overall assessment
        print(f"\n🎯 Overall Assessment:")
        all_tests_passed = (
            co['data_integrity'] and
            se['success'] and
            pr['patterns_extracted'] > 0 and
            mr['execution_success'] and
            ig['success_rate'] > 0
        )
        
        if all_tests_passed:
            print("  ✅ All archetypes working correctly!")
            print("  ✅ Ready for production integration!")
        else:
            print("  ⚠️  Some tests failed - review logs")
        
        # Save detailed report
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_file}")

async def main():
    """Run the test suite"""
    suite = ArchetypeTestSuite()
    await suite.run_all_tests()

if __name__ == "__main__":
    print("Starting Agent Archetypes Test Suite...")
    asyncio.run(main())
