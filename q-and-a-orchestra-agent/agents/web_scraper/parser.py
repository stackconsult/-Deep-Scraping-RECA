from bs4 import BeautifulSoup
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class HTMLParser:
    """Parses HTML content using BeautifulSoup"""
    
    def parse(self, html: Optional[str]) -> Optional[BeautifulSoup]:
        """Parse HTML string into BeautifulSoup object"""
        if not html:
            return None
            
        try:
            return BeautifulSoup(html, 'lxml')
        except Exception as e:
            logger.warning(f"lxml parser failed: {e}, falling back to html.parser")
            try:
                return BeautifulSoup(html, 'html.parser')
            except Exception as e:
                logger.error(f"Failed to parse HTML: {e}")
                return None
