# Agent Archetypes Package
"""
Complete implementation of agent archetypes from Awesome LLM Apps
for email enrichment system
"""

from .context_optimizer import ContextCompressor
from .sequential_executor import SequentialExecutor
from .pattern_recognition import PatternExtractor, PatternLearner, PatternMatcher, EmailPattern
from .model_router import SmartRouter, TaskType

__all__ = [
    'ContextCompressor',
    'SequentialExecutor',
    'PatternExtractor',
    'PatternLearner',
    'PatternMatcher',
    'EmailPattern',
    'SmartRouter',
    'TaskType'
]
