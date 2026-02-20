from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)

class ResponseCache:
    """Simple in-memory cache for web responses"""
    
    def __init__(self, ttl: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = timedelta(seconds=ttl)
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.cache:
            return None
            
        entry = self.cache[key]
        if datetime.now() > entry['expires_at']:
            del self.cache[key]
            return None
            
        return entry['value']
        
    def set(self, key: str, value: Any):
        """Set value in cache"""
        self.cache[key] = {
            'value': value,
            'expires_at': datetime.now() + self.ttl
        }
        
    def clear(self):
        """Clear cache"""
        self.cache.clear()
        
    def cleanup(self):
        """Remove expired entries"""
        now = datetime.now()
        keys_to_remove = [
            k for k, v in self.cache.items() 
            if now > v['expires_at']
        ]
        for k in keys_to_remove:
            del self.cache[k]
