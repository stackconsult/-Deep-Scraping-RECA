import asyncio
import time
from collections import deque

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, rate_limit: int = 1, period: float = 1.0):
        self.rate_limit = rate_limit
        self.period = period
        self.tokens = rate_limit
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()
        
    async def acquire(self):
        """Acquire a token, waiting if necessary"""
        async with self.lock:
            now = time.monotonic()
            time_passed = now - self.last_update
            self.last_update = now
            
            # Replenish tokens based on time passed
            new_tokens = time_passed * (self.rate_limit / self.period)
            self.tokens = min(self.rate_limit, self.tokens + new_tokens)
            
            if self.tokens < 1:
                wait_time = (1 - self.tokens) * (self.period / self.rate_limit)
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1
