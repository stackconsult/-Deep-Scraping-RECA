import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
import logging
from datetime import datetime

from .fetcher import PageFetcher
from .parser import HTMLParser
from .extractor import ContactExtractor
from .validator import DataValidator
from .cache import ResponseCache
from .rate_limiter import RateLimiter
from .schemas import ContactInfo, AgentProfile

class StructuredScraper:
    """Structured web scraper for real estate websites"""
    
    def __init__(self, cache_ttl: int = 3600, rate_limit: int = 1):
        self.fetcher = PageFetcher()
        self.parser = HTMLParser()
        self.extractor = ContactExtractor()
        self.validator = DataValidator()
        self.cache = ResponseCache(ttl=cache_ttl)
        self.rate_limiter = RateLimiter(rate_limit)
        self.logger = logging.getLogger(__name__)
        
        # Common real estate website patterns
        self.site_patterns = {
            'remax': {
                'agent_url_pattern': '/agents/{name}-{id}',
                'contact_selectors': {
                    'email': '.agent-email',
                    'phone': '.agent-phone',
                    'bio': '.agent-bio'
                }
            },
            'royal_lepage': {
                'agent_url_pattern': '/agent/{name}/{id}',
                'contact_selectors': {
                    'email': '.contact-email',
                    'phone': '.contact-phone',
                    'bio': '.agent-description'
                }
            }
        }
    
    async def scrape_agent(self, agent_data: Dict) -> AgentProfile:
        """Scrape agent information from their brokerage website"""
        brokerage = agent_data.get('brokerage', '')
        agent_name = agent_data.get('name', '')
        
        # Check cache first
        cache_key = f"scrape_{agent_name}_{brokerage}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        # Find agent page URL
        agent_url = await self._find_agent_url(agent_data)
        if not agent_url:
            result = AgentProfile(
                found=False,
                error="Agent page not found"
            )
            self.cache.set(cache_key, result)
            return result
        
        # Respect rate limiting
        await self.rate_limiter.acquire()
        
        # Fetch page
        html = await self.fetcher.fetch(agent_url)
        if not html:
            result = AgentProfile(
                found=False,
                error="Failed to fetch page"
            )
            self.cache.set(cache_key, result)
            return result
        
        # Parse HTML
        soup = self.parser.parse(html)
        
        # Extract contact information
        contact_info = await self.extractor.extract_contact(
            soup, agent_data, self._get_site_config(brokerage)
        )
        
        # Validate extracted data
        validated = await self.validator.validate(contact_info, agent_data)
        
        # Create profile
        profile = AgentProfile(
            found=True,
            agent_name=agent_name,
            brokerage=brokerage,
            url=agent_url,
            contact_info=validated,
            scraped_at=datetime.now(),
            confidence=self._calculate_confidence(validated)
        )
        
        # Cache result
        self.cache.set(cache_key, profile)
        
        return profile
    
    async def _find_agent_url(self, agent_data: Dict) -> Optional[str]:
        """Find agent page URL"""
        brokerage = agent_data.get('brokerage', '')
        domain = self._extract_domain(brokerage)
        
        if not domain:
            return None
        
        # Try common URL patterns
        first_name = agent_data.get('first_name', '').lower()
        last_name = agent_data.get('last_name', '').lower()
        
        patterns = [
            f"https://{domain}/agents/{first_name}-{last_name}",
            f"https://{domain}/agent/{first_name}-{last_name}",
            f"https://{domain}/realtor/{first_name}-{last_name}",
            f"https://{domain}/team/{first_name}-{last_name}",
            f"https://{domain}/about/{first_name}-{last_name}"
        ]
        
        # Try each pattern
        for url in patterns:
            await self.rate_limiter.acquire()
            if await self.fetcher.url_exists(url):
                return url
        
        # Note: In a real implementation, we would use a search engine or the site's search
        # but for this archetype we'll stick to direct URL patterns
        
        return None
    
    def _get_site_config(self, brokerage: str) -> Dict:
        """Get configuration for specific brokerage site"""
        brokerage_lower = brokerage.lower()
        
        for site, config in self.site_patterns.items():
            if site in brokerage_lower:
                return config
        
        # Return default configuration
        return {
            'agent_url_pattern': '/agents/{name}',
            'contact_selectors': {
                'email': '.email, [href*="mailto:"]',
                'phone': '.phone, [href*="tel:"]',
                'bio': '.bio, .description'
            }
        }
    
    def _extract_domain(self, brokerage: str) -> Optional[str]:
        """Extract domain from brokerage name"""
        if not brokerage:
            return None
            
        clean = brokerage.lower()
        
        # Handle "O/A" (Operating As) - prioritize the brand name
        if ' o/a ' in clean:
            clean = clean.split(' o/a ')[1]
        elif ' o/a' in clean:
            clean = clean.split(' o/a')[1]
            
        # Replace & with 'and' before removing special chars
        clean = clean.replace('&', 'and')
        
        # Remove strict legal suffixes only
        replacements = [
            ' inc.', ' inc', ' ltd.', ' ltd', ' corp.', ' corp', 
            ' corporation', ' limited', ' llc', ' ulc', ' llp'
        ]
        
        for r in replacements:
            if clean.endswith(r):
                clean = clean[:-len(r)]
            elif r in clean:
                clean = clean.replace(r, '')
        
        # Handle special big brands (manual overrides for cleaner domains)
        if 'century 21' in clean:
            return 'century21.ca'
        if 're/max' in clean or 'remax' in clean:
            return 'remax.ca'
        if 'royal lepage' in clean:
            return 'royallepage.ca'
        if 'sothebys' in clean or "sotheby's" in clean:
            return 'sothebysrealty.ca'
        if 'exp realty' in clean:
            return 'exprealty.ca'
            
        # Remove special chars and spaces
        clean = clean.replace('.', '').replace(',', '').replace("'", "").replace('/', '').replace('(', '').replace(')', '').replace(' ', '')
        
        # Return .ca for Canadian context as default guess
        return f"{clean}.ca"
    
    def _calculate_confidence(self, contact_info: ContactInfo) -> float:
        """Calculate confidence score for extracted data"""
        score = 0.0
        
        if contact_info.email:
            score += 0.4
            if contact_info.email_verified:
                score += 0.2
        
        if contact_info.phone:
            score += 0.2
        
        if contact_info.bio:
            score += 0.1
        
        if contact_info.social_links:
            score += 0.1
        
        return min(score, 1.0)
