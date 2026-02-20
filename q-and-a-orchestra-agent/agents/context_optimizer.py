# Context Optimizer Implementation
"""
Reduces API costs by 50-90% through intelligent context compression
Based on Headroom Context Optimization from Awesome LLM Apps
"""

import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging

@dataclass
class MinimalAgentData:
    """Optimized agent data structure for minimal tokens"""
    # Single character keys for maximum compression
    n: str  # name (max 20 chars)
    b: str  # brokerage (max 20)
    c: str  # city (max 15)
    f: str  # first_name (max 10)
    l: str  # last_name (max 10)
    t: str  # type (brokerage_type)
    d: str  # domain (if known)

class ContextCompressor:
    """Compresses agent context for minimal token usage"""
    
    def __init__(self):
        self.compression_stats = {
            'original_tokens': 0,
            'compressed_tokens': 0,
            'savings_percent': 0.0,
            'total_processed': 0
        }
        self.logger = logging.getLogger(__name__)
    
    def compress_agent(self, agent_data: Dict) -> str:
        """Compress single agent data"""
        # Extract and limit fields
        minimal = MinimalAgentData(
            n=self._clean_string(agent_data.get('name', ''), 20),
            b=self._clean_string(agent_data.get('brokerage', ''), 20),
            c=self._clean_string(agent_data.get('city', ''), 15),
            f=self._clean_string(agent_data.get('first_name', ''), 10),
            l=self._clean_string(agent_data.get('last_name', ''), 10),
            t=self._classify_brokerage(agent_data.get('brokerage', '')),
            d=self._extract_domain(agent_data.get('brokerage', ''))
        )
        
        # Convert to minimal JSON
        compressed = json.dumps(asdict(minimal), separators=(',', ':'))
        
        # Update stats
        original_size = len(json.dumps(agent_data))
        self.compression_stats['original_tokens'] += original_size
        self.compression_stats['compressed_tokens'] += len(compressed)
        self.compression_stats['total_processed'] += 1
        
        return compressed
    
    def decompress_agent(self, compressed_str: str) -> Dict:
        """Decompress agent data"""
        try:
            data = json.loads(compressed_str)
            return {
                'name': data['n'],
                'brokerage': data['b'],
                'city': data['c'],
                'first_name': data['f'],
                'last_name': data['l'],
                'brokerage_type': self._expand_brokerage_type(data['t']),
                'domain': data['d']
            }
        except Exception as e:
            self.logger.error(f"Decompression failed: {e}")
            return {}
    
    def compress_batch(self, agents: List[Dict]) -> List[str]:
        """Compress multiple agents"""
        return [self.compress_agent(agent) for agent in agents]
    
    def _clean_string(self, text: str, max_len: int) -> str:
        """Clean and limit string length"""
        if not text:
            return ""
        # Remove special characters, keep alphanumeric and spaces
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        return cleaned[:max_len].lower().strip()
    
    def _classify_brokerage(self, brokerage: str) -> str:
        """Classify brokerage type with single code"""
        if not brokerage:
            return 'i'
        
        b = brokerage.lower()
        if 'remax' in b or 're/max' in b:
            return 'r'  # remax
        elif 'royal lepage' in b:
            return 'l'  # royal lepage
        elif 'century 21' in b:
            return 'c'  # century 21
        elif 'exp' in b:
            return 'e'  # exp realty
        else:
            return 'i'  # independent
    
    def _expand_brokerage_type(self, code: str) -> str:
        """Expand single code back to full type"""
        mapping = {
            'r': 'remax',
            'l': 'royal_lepage',
            'c': 'century_21',
            'e': 'exp_realty',
            'i': 'independent'
        }
        return mapping.get(code, 'independent')
    
    def _extract_domain(self, brokerage: str) -> str:
        """Extract domain from brokerage"""
        if not brokerage:
            return ""
        
        # Clean and create domain
        clean = brokerage.lower()
        clean = clean.replace(' ', '').replace('.', '').replace('/', '')
        return f"{clean}.ca"
    
    def get_compression_report(self) -> Dict:
        """Get compression statistics"""
        if self.compression_stats['original_tokens'] > 0:
            savings = (1 - self.compression_stats['compressed_tokens'] / 
                      self.compression_stats['original_tokens']) * 100
            self.compression_stats['savings_percent'] = savings
        
        return self.compression_stats.copy()
    
    def reset_stats(self):
        """Reset compression statistics"""
        self.compression_stats = {
            'original_tokens': 0,
            'compressed_tokens': 0,
            'savings_percent': 0.0,
            'total_processed': 0
        }
