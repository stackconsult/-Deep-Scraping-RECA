# Smart Model Router Implementation
"""
Routes requests to the most cost-effective model
Based on model routing patterns from Awesome LLM Apps
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, time
import logging
import json
from collections import defaultdict

class TaskType(Enum):
    """Types of tasks to route"""
    SIMPLE_VALIDATION = "simple_validation"
    PATTERN_GENERATION = "pattern_generation"
    WEB_SCRAPING = "web_scraping"
    COMPLEX_EXTRACTION = "complex_extraction"
    SYNTHESIS = "synthesis"
    PLANNING = "planning"

@dataclass
class ModelInfo:
    """Information about an available model"""
    name: str
    provider: str
    location: str  # 'local' or 'cloud'
    cost_per_input_token: float
    cost_per_output_token: float
    max_tokens: int
    capabilities: List[str]
    reliability: float  # 0-1
    speed: str  # 'fast', 'medium', 'slow'
    available: bool = True
    last_used: Optional[datetime] = None
    
    def get_estimated_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost"""
        return (input_tokens * self.cost_per_input_token + 
                output_tokens * self.cost_per_output_token)

@dataclass
class RoutingDecision:
    """Result of routing decision"""
    selected_model: str
    task_type: str
    estimated_cost: float
    estimated_time: float
    confidence: float
    alternatives: List[str]
    reasoning: str

class ModelRegistry:
    """Registry of available models"""
    
    def __init__(self):
        self.models: Dict[str, ModelInfo] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_model(self, model: ModelInfo):
        """Register a new model"""
        self.models[model.name] = model
        self.logger.info(f"Registered model: {model.name}")
    
    def get_model(self, name: str) -> Optional[ModelInfo]:
        """Get model by name"""
        return self.models.get(name)
    
    def get_models_for_task(self, task_type: TaskType) -> List[ModelInfo]:
        """Get models capable of handling a task"""
        capable = []
        task_str = task_type.value
        
        for model in self.models.values():
            if not model.available:
                continue
            
            # Check if model can handle the task
            if task_str in model.capabilities:
                capable.append(model)
        
        # Sort by reliability (most reliable first)
        capable.sort(key=lambda m: m.reliability, reverse=True)
        return capable
    
    def get_all_models(self) -> List[ModelInfo]:
        """Get all registered models"""
        return list(self.models.values())
    
    def update_model_availability(self, name: str, available: bool):
        """Update model availability"""
        if name in self.models:
            self.models[name].available = available
            self.logger.info(f"Model {name} availability set to {available}")

class CostCalculator:
    """Calculates costs for model usage"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        # Rough estimation: 1 token per 4 characters
        return len(text) // 4
    
    def estimate_task_tokens(self, task_type: TaskType, data: Dict) -> Tuple[int, int]:
        """Estimate input/output tokens for a task"""
        # Input tokens based on data size
        input_text = json.dumps(data, separators=(',', ':'))
        input_tokens = self.estimate_tokens(input_text)
        
        # Output tokens based on task type
        output_estimates = {
            TaskType.SIMPLE_VALIDATION: (50, 100),
            TaskType.PATTERN_GENERATION: (100, 200),
            TaskType.WEB_SCRAPING: (200, 400),
            TaskType.COMPLEX_EXTRACTION: (300, 600),
            TaskType.SYNTHESIS: (150, 300),
            TaskType.PLANNING: (200, 500)
        }
        
        min_output, max_output = output_estimates.get(task_type, (100, 200))
        output_tokens = (min_output + max_output) // 2
        
        return input_tokens, output_tokens
    
    def calculate_cost(self, model: ModelInfo, input_tokens: int, 
                      output_tokens: int) -> float:
        """Calculate total cost"""
        return model.get_estimated_cost(input_tokens, output_tokens)

class PerformanceTracker:
    """Tracks model performance over time"""
    
    def __init__(self):
        self.stats: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)
    
    def record_execution(self, model_name: str, task_type: TaskType, 
                         success: bool, execution_time: float, cost: float):
        """Record model execution"""
        if model_name not in self.stats:
            self.stats[model_name] = {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'total_time': 0.0,
                'total_cost': 0.0,
                'task_stats': {}
            }
        
        model_stats = self.stats[model_name]
        task_str = task_type.value
        
        # Update overall stats
        model_stats['total_executions'] += 1
        model_stats['total_time'] += execution_time
        model_stats['total_cost'] += cost
        
        if success:
            model_stats['successful_executions'] += 1
        else:
            model_stats['failed_executions'] += 1
        
        # Update task-specific stats
        if task_str not in model_stats['task_stats']:
            model_stats['task_stats'][task_str] = {
                'executions': 0,
                'successes': 0,
                'total_time': 0.0
            }
        
        task_stats = model_stats['task_stats'][task_str]
        task_stats['executions'] += 1
        task_stats['total_time'] += execution_time
        
        if success:
            task_stats['successes'] += 1
    
    def get_success_rate(self, model_name: str, task_type: TaskType) -> float:
        """Get success rate for model and task"""
        if model_name not in self.stats:
            return 0.0
        
        task_str = task_type.value
        task_stats = self.stats[model_name]['task_stats'].get(task_str, {})
        
        if task_stats.get('executions', 0) == 0:
            return 0.0
        
        return task_stats['successes'] / task_stats['executions']
    
    def get_model_stats(self, model_name: str) -> Dict:
        """Get full statistics for a model"""
        return self.stats.get(model_name, {})
    
    def get_all_stats(self) -> Dict:
        """Get statistics for all models"""
        return self.stats.copy()

class RoutingRules:
    """Defines routing rules for different scenarios"""
    
    def __init__(self):
        self.rules = {
            'time_constraints': {
                'peak_hours': (time(9, 0), time(17, 0)),
                'off_hours': (time(17, 0), time(9, 0))
            },
            'budget_constraints': {
                'daily_limit': 10.0,
                'urgent_tasks': 2.0,
                'batch_tasks': 0.5
            },
            'quality_requirements': {
                'high_stakes': ['synthesis', 'complex_extraction', 'planning'],
                'low_stakes': ['simple_validation']
            },
            'model_preferences': {
                'cost_sensitive': ['mistral:7b', 'qwen2.5-coder:32b'],
                'quality_first': ['llama3.3:70b', 'gemini-1.5-flash'],
                'speed_first': ['mistral:7b', 'gemini-1.5-flash']
            }
        }
    
    def should_use_premium(self, task_type: str, 
                          current_time: time) -> bool:
        """Determine if premium model should be used"""
        # Use premium for high-stakes tasks during business hours
        if task_type in self.rules['quality_requirements']['high_stakes']:
            start, end = self.rules['time_constraints']['peak_hours']
            if start <= current_time <= end:
                return True
        
        return False
    
    def get_budget_limit(self, task_type: str, 
                        is_urgent: bool = False) -> float:
        """Get budget limit for task"""
        if is_urgent:
            return self.rules['budget_constraints']['urgent_tasks']
        elif task_type in self.rules['quality_requirements']['low_stakes']:
            return self.rules['budget_constraints']['batch_tasks']
        
        return self.rules['budget_constraints']['daily_limit']
    
    def get_preferred_models(self, priority: str) -> List[str]:
        """Get preferred models for a priority"""
        return self.rules['model_preferences'].get(priority, [])

class SmartRouter:
    """Intelligent model router for cost optimization"""
    
    def __init__(self):
        self.registry = ModelRegistry()
        self.cost_calc = CostCalculator()
        self.performance = PerformanceTracker()
        self.rules = RoutingRules()
        self.logger = logging.getLogger(__name__)
        
        # Routing statistics
        self.routing_stats = {
            'total_routes': 0,
            'model_usage': defaultdict(int),
            'cost_savings': 0.0,
            'fallbacks': 0
        }
        
        # Initialize with default models
        self._setup_default_models()
    
    def _setup_default_models(self):
        """Setup default models"""
        # Local models (free)
        self.registry.register_model(ModelInfo(
            name="mistral:7b",
            provider="ollama",
            location="local",
            cost_per_input_token=0.0,
            cost_per_output_token=0.0,
            max_tokens=8192,
            capabilities=["simple_validation", "pattern_generation"],
            reliability=0.95,
            speed="fast"
        ))
        
        # Cloud models
        self.registry.register_model(ModelInfo(
            name="qwen2.5-coder:32b",
            provider="ollama",
            location="cloud",
            cost_per_input_token=0.0005,
            cost_per_output_token=0.0005,
            max_tokens=32768,
            capabilities=["pattern_generation", "web_scraping", "complex_extraction"],
            reliability=0.98,
            speed="medium"
        ))
        
        self.registry.register_model(ModelInfo(
            name="llama3.3:70b",
            provider="ollama",
            location="cloud",
            cost_per_input_token=0.001,
            cost_per_output_token=0.001,
            max_tokens=131072,
            capabilities=["complex_extraction", "synthesis", "planning"],
            reliability=0.99,
            speed="medium"
        ))
        
        # Gemini models
        self.registry.register_model(ModelInfo(
            name="gemini-1.5-flash",
            provider="google",
            location="cloud",
            cost_per_input_token=0.075/1_000_000,
            cost_per_output_token=0.30/1_000_000,
            max_tokens=1048576,
            capabilities=["complex_extraction", "synthesis", "planning", "web_scraping"],
            reliability=0.99,
            speed="fast"
        ))
    
    async def route(self, task_type: TaskType, data: Dict, 
                   budget_constraint: Optional[float] = None,
                   priority: str = "balanced") -> RoutingDecision:
        """Route task to best model"""
        self.routing_stats['total_routes'] += 1
        
        # Get candidate models
        candidates = self.registry.get_models_for_task(task_type)
        
        if not candidates:
            raise ValueError(f"No models available for task: {task_type.value}")
        
        # Score each candidate
        scored_models = []
        for model in candidates:
            score = await self._score_model(model, task_type, data, 
                                          budget_constraint, priority)
            scored_models.append((model.name, score, model))
        
        # Sort by score (higher is better)
        scored_models.sort(key=lambda x: x[1], reverse=True)
        
        # Select best model
        best_model_name, best_score, best_model = scored_models[0]
        
        # Estimate cost and time
        input_tokens, output_tokens = self.cost_calc.estimate_task_tokens(
            task_type, data
        )
        estimated_cost = self.cost_calc.calculate_cost(
            best_model, input_tokens, output_tokens
        )
        estimated_time = self._estimate_time(best_model, input_tokens)
        
        # Get alternatives
        alternatives = [m[0] for m in scored_models[1:3]]
        
        # Create reasoning
        reasoning = self._generate_reasoning(
            best_model, task_type, best_score, priority
        )
        
        # Update stats
        self.routing_stats['model_usage'][best_model_name] += 1
        best_model.last_used = datetime.now()
        
        decision = RoutingDecision(
            selected_model=best_model_name,
            task_type=task_type.value,
            estimated_cost=estimated_cost,
            estimated_time=estimated_time,
            confidence=best_score,
            alternatives=alternatives,
            reasoning=reasoning
        )
        
        self.logger.info(f"Routed {task_type.value} to {best_model_name} "
                        f"(score: {best_score:.2f}, cost: ${estimated_cost:.4f})")
        
        return decision
    
    async def _score_model(self, model: ModelInfo, task_type: TaskType, 
                          data: Dict, budget: Optional[float], 
                          priority: str) -> float:
        """Score model for this task"""
        score = 0.0
        
        # Capability match (40% weight)
        if task_type.value in model.capabilities:
            score += 0.4
        else:
            return 0.0  # Can't handle the task
        
        # Cost efficiency (30% weight)
        input_tokens, output_tokens = self.cost_calc.estimate_task_tokens(
            task_type, data
        )
        estimated_cost = self.cost_calc.calculate_cost(
            model, input_tokens, output_tokens
        )
        
        if budget and estimated_cost > budget:
            score -= 0.5  # Penalty for exceeding budget
        else:
            # Lower cost = higher score
            if estimated_cost == 0:
                cost_score = 1.0  # Free models get highest score
            else:
                cost_score = 1.0 / (1.0 + estimated_cost * 100)
            score += cost_score * 0.3
        
        # Reliability (20% weight)
        score += model.reliability * 0.2
        
        # Performance history (10% weight)
        perf_score = self.performance.get_success_rate(model.name, task_type)
        score += perf_score * 0.1
        
        # Priority adjustments
        if priority == "cost_sensitive" and model.cost_per_input_token == 0:
            score += 0.1  # Bonus for free models
        elif priority == "quality_first" and model.reliability >= 0.99:
            score += 0.1  # Bonus for high reliability
        elif priority == "speed_first" and model.speed == "fast":
            score += 0.1  # Bonus for fast models
        
        return min(score, 1.0)
    
    def _estimate_time(self, model: ModelInfo, input_tokens: int) -> float:
        """Estimate processing time in seconds"""
        base_times = {
            "fast": 0.5,
            "medium": 2.0,
            "slow": 5.0
        }
        
        base_time = base_times.get(model.speed, 2.0)
        
        # Adjust based on input size
        size_factor = min(input_tokens / 1000, 3.0)  # Max 3x slower for large inputs
        
        return base_time * size_factor
    
    def _generate_reasoning(self, model: ModelInfo, task_type: TaskType, 
                           score: float, priority: str) -> str:
        """Generate reasoning for routing decision"""
        reasons = []
        
        if task_type.value in model.capabilities:
            reasons.append(f"Capable of {task_type.value}")
        
        if model.cost_per_input_token == 0:
            reasons.append("No cost (local model)")
        elif priority == "cost_sensitive":
            reasons.append("Cost-effective option")
        
        if model.reliability >= 0.99:
            reasons.append("High reliability")
        
        if model.speed == "fast":
            reasons.append("Fast processing")
        
        if priority == "quality_first" and model.location == "cloud":
            reasons.append("Premium cloud model")
        
        return "; ".join(reasons) if reasons else "Best available option"
    
    async def execute_with_routing(self, task_type: TaskType, data: Dict, 
                                 execution_func: Callable,
                                 budget_constraint: Optional[float] = None,
                                 priority: str = "balanced") -> Dict:
        """Execute task with automatic routing and fallback"""
        # Route to best model
        decision = await self.route(task_type, data, budget_constraint, priority)
        
        try:
            # Execute with selected model
            start_time = datetime.now()
            result = await execution_func(decision.selected_model, data)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Track performance
            self.performance.record_execution(
                decision.selected_model, task_type, True, execution_time,
                decision.estimated_cost
            )
            
            # Add routing metadata
            result['routing_metadata'] = {
                'selected_model': decision.selected_model,
                'estimated_cost': decision.estimated_cost,
                'estimated_time': decision.estimated_time,
                'actual_time': execution_time,
                'confidence': decision.confidence,
                'reasoning': decision.reasoning
            }
            
            # Calculate cost savings
            if decision.estimated_cost > 0:
                # Compare to most expensive alternative
                alternatives = self.registry.get_models_for_task(task_type)
                if alternatives:
                    most_expensive = max(alternatives, 
                                       key=lambda m: m.cost_per_input_token)
                    if most_expensive.name != decision.selected_model:
                        alt_cost = self.cost_calc.calculate_cost(
                            most_expensive, *self.cost_calc.estimate_task_tokens(
                                task_type, data
                            )
                        )
                        savings = alt_cost - decision.estimated_cost
                        self.routing_stats['cost_savings'] += savings
            
            return result
            
        except Exception as e:
            self.logger.error(f"Execution failed with {decision.selected_model}: {e}")
            
            # Try fallback
            return await self._handle_fallback(
                task_type, data, decision.selected_model, e, execution_func
            )
    
    async def _handle_fallback(self, task_type: TaskType, data: Dict,
                             failed_model: str, error: Exception,
                             execution_func: Callable) -> Dict:
        """Handle execution failure with fallback models"""
        self.routing_stats['fallbacks'] += 1
        
        # Get alternative models
        alternatives = self.registry.get_models_for_task(task_type)
        alternatives = [m for m in alternatives if m.name != failed_model]
        
        for model in alternatives:
            try:
                self.logger.info(f"Trying fallback model: {model.name}")
                result = await execution_func(model.name, data)
                
                # Track fallback success
                self.performance.record_execution(
                    model.name, task_type, True, 0.0, 0.0
                )
                
                result['fallback_used'] = True
                result['fallback_from'] = failed_model
                result['fallback_to'] = model.name
                
                return result
                
            except Exception as e:
                self.logger.error(f"Fallback {model.name} also failed: {e}")
                self.performance.record_execution(
                    model.name, task_type, False, 0.0, 0.0
                )
        
        # All models failed
        return {
            'error': f"All models failed for task {task_type.value}",
            'primary_error': str(error),
            'fallback_attempts': len(alternatives),
            'fallback_used': True
        }
    
    def get_routing_stats(self) -> Dict:
        """Get routing statistics"""
        stats = self.routing_stats.copy()
        
        # Add performance stats
        stats['model_performance'] = self.performance.get_all_stats()
        
        # Calculate cost efficiency
        if stats['total_routes'] > 0:
            stats['avg_cost_savings_per_route'] = (
                stats['cost_savings'] / stats['total_routes']
            )
        
        return stats
    
    def reset_stats(self):
        """Reset routing statistics"""
        self.routing_stats = {
            'total_routes': 0,
            'model_usage': defaultdict(int),
            'cost_savings': 0.0,
            'fallbacks': 0
        }
