# Pattern Recognition Implementation
"""
Learns and recognizes email patterns per brokerage
Based on memory and learning patterns from Awesome LLM Apps
"""

import re
import json
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import logging

@dataclass
class EmailPattern:
    """Represents an email pattern"""
    template: str  # e.g., "{first}.{last}@{domain}"
    regex: str     # e.g., r"^[a-z]+\.[a-z]+@"
    confidence: float
    success_count: int
    failure_count: int
    brokerage_type: str
    examples: List[str]
    created_at: datetime
    last_used: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'template': self.template,
            'regex': self.regex,
            'confidence': self.confidence,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'brokerage_type': self.brokerage_type,
            'examples': self.examples[:5],  # Keep only 5 examples
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EmailPattern':
        """Create from dictionary"""
        return cls(
            template=data['template'],
            regex=data.get('regex', ''),
            confidence=data['confidence'],
            success_count=data['success_count'],
            failure_count=data.get('failure_count', 0),
            brokerage_type=data['brokerage_type'],
            examples=data['examples'],
            created_at=datetime.fromisoformat(data['created_at']),
            last_used=datetime.fromisoformat(data['last_used'])
        )

class PatternExtractor:
    """Extracts patterns from successful email extractions"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.common_patterns = {
            'first_last': {
                'regex': r'^(?P<first>[a-z]+)\.(?P<last>[a-z]+)@',
                'template': '{first}.{last}@{domain}'
            },
            'firstlast': {
                'regex': r'^(?P<first>[a-z]+)(?P<last>[a-z]+)@',
                'template': '{first}{last}@{domain}'
            },
            'first_initial_last': {
                'regex': r'^(?P<first>[a-z])(?P<last>[a-z]+)@',
                'template': '{first_initial}{last}@{domain}'
            },
            'first_last_initial': {
                'regex': r'^(?P<first>[a-z]+)\.(?P<last>[a-z])[a-z]*@',
                'template': '{first}.{last_initial}@{domain}'
            },
            'first_under_last': {
                'regex': r'^(?P<first>[a-z]+)_(?P<last>[a-z]+)@',
                'template': '{first}_{last}@{domain}'
            },
            'last_first': {
                'regex': r'^(?P<last>[a-z]+)(?P<first>[a-z]+)@',
                'template': '{last}{first}@{domain}'
            },
            'first_dot_last_initial': {
                'regex': r'^(?P<first>[a-z]+)\.(?P<last>[a-z])\d*@',
                'template': '{first}.{last_initial}@{domain}'
            }
        }
    
    def extract_pattern(self, email: str, agent: Dict, 
                       domain: str) -> Optional[EmailPattern]:
        """Extract pattern from a successful email match"""
        local_part = email.split('@')[0].lower()
        first = agent.get('first_name', '').lower()
        last = agent.get('last_name', '').lower()
        
        # Try to match known patterns
        for pattern_name, pattern_info in self.common_patterns.items():
            match = re.match(pattern_info['regex'], local_part)
            if match:
                # Verify the match corresponds to agent names
                if self._validate_match(match, first, last):
                    template = pattern_info['template'].replace('{domain}', domain)
                    
                    return EmailPattern(
                        template=template,
                        regex=pattern_info['regex'],
                        confidence=0.7,  # Initial confidence
                        success_count=1,
                        failure_count=0,
                        brokerage_type=self._classify_brokerage(
                            agent.get('brokerage', '')
                        ),
                        examples=[email],
                        created_at=datetime.now(),
                        last_used=datetime.now()
                    )
        
        # If no known pattern, try to infer custom pattern
        custom_pattern = self._infer_custom_pattern(
            local_part, first, last, domain, agent.get('brokerage', ''), email
        )
        if custom_pattern:
            return custom_pattern
        
        return None
    
    def _validate_match(self, match: re.Match, first: str, 
                       last: str) -> bool:
        """Validate that regex match corresponds to agent names"""
        groups = match.groupdict()
        
        # Check first name
        if 'first' in groups:
            if not first or not groups['first'].startswith(first[:3]):
                return False
        
        # Check last name
        if 'last' in groups:
            if not last or not groups['last'].startswith(last[:3]):
                return False
        
        return True
    
    def _infer_custom_pattern(self, local_part: str, first: str, 
                             last: str, domain: str, brokerage: str, email: str) -> Optional[EmailPattern]:
        """Infer custom pattern when no known pattern matches"""
        if not first or not last:
            return None
        
        # Try to find first and last name in the local part
        first_pos = local_part.find(first[:3])
        last_pos = local_part.find(last[:3])
        
        if first_pos >= 0 and last_pos >= 0:
            # Build template based on positions
            template = local_part
            template = template.replace(
                local_part[first_pos:first_pos+len(first)], '{first}'
            )
            template = template.replace(
                local_part[last_pos:last_pos+len(last)], '{last}'
            )
            template += '@' + domain
            
            return EmailPattern(
                template=template,
                regex=f'^{re.escape(local_part)}@',
                confidence=0.5,  # Lower confidence for custom patterns
                success_count=1,
                failure_count=0,
                brokerage_type=self._classify_brokerage(brokerage),
                examples=[email],
                created_at=datetime.now(),
                last_used=datetime.now()
            )
        
        return None
    
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

class PatternMatcher:
    """Matches patterns to new agents"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def match_patterns(self, agent: Dict, patterns: List[EmailPattern], 
                      domain: str) -> List[Tuple[EmailPattern, str]]:
        """Match patterns to agent and generate emails"""
        matches = []
        
        for pattern in patterns:
            # Check if pattern matches agent's brokerage type
            if pattern.brokerage_type != 'independent':
                agent_brokerage = self._classify_brokerage(agent.get('brokerage', ''))
                if pattern.brokerage_type != agent_brokerage:
                    continue
            
            # Generate email from pattern
            email = self._generate_email(pattern, agent, domain)
            if email:
                matches.append((pattern, email))
        
        # Sort by pattern confidence
        matches.sort(key=lambda x: x[0].confidence, reverse=True)
        
        return matches
    
    def _generate_email(self, pattern: EmailPattern, agent: Dict, 
                       domain: str) -> Optional[str]:
        """Generate email from pattern"""
        first = agent.get('first_name', '').lower()
        last = agent.get('last_name', '').lower()
        
        if not first or not last:
            return None
        
        try:
            email = pattern.template.replace('{first}', first)\
                                   .replace('{last}', last)\
                                   .replace('{first_initial}', first[0])\
                                   .replace('{last_initial}', last[0])\
                                   .replace('{domain}', domain)
            
            # Basic validation
            if self._is_valid_email(email):
                return email
        except Exception as e:
            self.logger.error(f"Error generating email: {e}")
        
        return None
    
    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
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

class PatternLearner:
    """Learns and improves patterns over time"""
    
    def __init__(self):
        self.pattern_history = defaultdict(list)
        self.learning_rate = 0.1
        self.decay_rate = 0.05
        self.logger = logging.getLogger(__name__)
    
    def learn_from_result(self, pattern: EmailPattern, 
                         success: bool, confidence: float = 1.0):
        """Learn from pattern application result"""
        # Update confidence based on result
        if success:
            # Boost confidence for success
            pattern.confidence = min(
                pattern.confidence + self.learning_rate * confidence,
                1.0
            )
            pattern.success_count += 1
        else:
            # Reduce confidence for failure
            pattern.confidence = max(
                pattern.confidence - self.learning_rate,
                0.1
            )
            pattern.failure_count += 1
        
        pattern.last_used = datetime.now()
        
        # Store in history
        self.pattern_history[pattern.brokerage_type].append({
            'pattern': pattern,
            'success': success,
            'confidence': confidence,
            'timestamp': datetime.now()
        })
        
        # Prune old history (keep last 1000 entries per type)
        if len(self.pattern_history[pattern.brokerage_type]) > 1000:
            self.pattern_history[pattern.brokerage_type] = \
                self.pattern_history[pattern.brokerage_type][-1000:]
    
    def get_best_patterns(self, brokerage_type: str, 
                         top_k: int = 5, min_confidence: float = 0.5) -> List[EmailPattern]:
        """Get best patterns for a brokerage type"""
        # Get recent patterns from history
        recent_patterns = [
            entry['pattern'] for entry in 
            self.pattern_history[brokerage_type][-100:]  # Last 100 uses
        ]
        
        if not recent_patterns:
            return []
        
        # Group by template and aggregate
        template_scores = defaultdict(lambda: {
            'confidence': 0.0,
            'success_count': 0,
            'failure_count': 0,
            'examples': [],
            'pattern': None
        })
        
        for pattern in recent_patterns:
            key = pattern.template
            if template_scores[key]['pattern'] is None:
                template_scores[key]['pattern'] = pattern
            
            template_scores[key]['confidence'] += pattern.confidence
            template_scores[key]['success_count'] += pattern.success_count
            template_scores[key]['failure_count'] += pattern.failure_count
            template_scores[key]['examples'].extend(pattern.examples)
        
        # Convert back to patterns and sort
        best_patterns = []
        for template, scores in template_scores.items():
            # Calculate average confidence
            uses = len([p for p in recent_patterns if p.template == template])
            avg_confidence = scores['confidence'] / uses
            
            # Calculate success rate
            total_attempts = scores['success_count'] + scores['failure_count']
            success_rate = scores['success_count'] / total_attempts if total_attempts > 0 else 0
            
            # Combined score (confidence + success rate)
            final_confidence = (avg_confidence * 0.6 + success_rate * 0.4)
            
            if final_confidence >= min_confidence:
                base_pattern = scores['pattern']
                best_patterns.append(EmailPattern(
                    template=base_pattern.template,
                    regex=base_pattern.regex,
                    confidence=final_confidence,
                    success_count=scores['success_count'],
                    failure_count=scores['failure_count'],
                    brokerage_type=brokerage_type,
                    examples=list(set(scores['examples']))[:5],  # Unique examples
                    created_at=base_pattern.created_at,
                    last_used=datetime.now()
                ))
        
        # Sort by confidence and return top k
        best_patterns.sort(key=lambda p: p.confidence, reverse=True)
        return best_patterns[:top_k]
    
    def get_learning_stats(self) -> Dict:
        """Get learning statistics"""
        stats = {
            'total_patterns_learned': 0,
            'patterns_by_type': {},
            'avg_confidence_by_type': {},
            'total_uses': 0
        }
        
        for brokerage_type, history in self.pattern_history.items():
            patterns = set(entry['pattern'].template for entry in history)
            stats['patterns_by_type'][brokerage_type] = len(patterns)
            stats['total_patterns_learned'] += len(patterns)
            stats['total_uses'] += len(history)
            
            # Calculate average confidence
            if history:
                avg_conf = sum(entry['pattern'].confidence for entry in history) / len(history)
                stats['avg_confidence_by_type'][brokerage_type] = avg_conf
        
        return stats
