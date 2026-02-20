import aiohttp
import logging
from typing import Optional
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

class PageFetcher:
    """Fetches web pages with rotation and error handling"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        try:
            self.ua = UserAgent()
        except Exception:
            self.ua = None
            
    async def fetch(self, url: str) -> Optional[str]:
        """Fetch page content"""
        headers = {
            'User-Agent': self.ua.random if self.ua else 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"Failed to fetch {url}: Status {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    async def url_exists(self, url: str) -> bool:
        """Check if URL exists (HEAD request)"""
        headers = {
            'User-Agent': self.ua.random if self.ua else 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.head(url, headers=headers, allow_redirects=True) as response:
                    return response.status == 200
        except Exception:
            return False
