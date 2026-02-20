from bs4 import BeautifulSoup
from typing import Dict, Optional, List
import re
from .schemas import ContactInfo

class ContactExtractor:
    """Extracts contact information from parsed HTML"""
    
    def __init__(self):
        self.email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})'
        ]
        
        self.phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',
            r'tel:([\d\-\.\(\)\s]+)'
        ]
        
        self.social_domains = {
            'linkedin': 'linkedin.com',
            'facebook': 'facebook.com',
            'twitter': 'twitter.com',
            'instagram': 'instagram.com',
            'youtube': 'youtube.com'
        }
    
    async def extract_contact(self, soup: BeautifulSoup, 
                            agent_data: Dict, 
                            site_config: Dict) -> ContactInfo:
        """Extract contact information from page"""
        contact = ContactInfo()
        
        # Extract email
        contact.email = await self._extract_email(soup, site_config)
        contact.email_verified = self._verify_email_format(contact.email)
        
        # Extract phone
        contact.phone = await self._extract_phone(soup, site_config)
        
        # Extract bio
        contact.bio = await self._extract_bio(soup, site_config)
        
        # Extract social links
        contact.social_links = await self._extract_social_links(soup)
        
        return contact
    
    async def _extract_email(self, soup: BeautifulSoup, 
                           site_config: Dict) -> Optional[str]:
        """Extract email address"""
        # Try specific selectors first
        selectors = site_config.get('contact_selectors', {}).get('email', '')
        
        if selectors:
            for selector in selectors.split(','):
                elements = soup.select(selector.strip())
                for element in elements:
                    # Check href attribute for mailto links
                    href = element.get('href', '')
                    if href.startswith('mailto:'):
                        return href.replace('mailto:', '').strip()
                    
                    # Check text content
                    text = element.get_text(strip=True)
                    if self._is_email(text):
                        return text
        
        # Fall back to pattern matching in text
        # Limit text extraction to relevant sections if possible
        text_content = soup.get_text(" ", strip=True)
        for pattern in self.email_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                email = match.group(1) if match.groups() else match.group(0)
                if email.startswith('mailto:'):
                    email = email.replace('mailto:', '')
                return email.strip()
        
        # Check all links
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('mailto:'):
                return href.replace('mailto:', '').strip()
        
        return None
    
    async def _extract_phone(self, soup: BeautifulSoup, site_config: Dict) -> Optional[str]:
        """Extract phone number"""
        selectors = site_config.get('contact_selectors', {}).get('phone', '')
        
        if selectors:
            for selector in selectors.split(','):
                elements = soup.select(selector.strip())
                for element in elements:
                    text = element.get_text(strip=True)
                    # Basic cleaning
                    cleaned = re.sub(r'[^\d]', '', text)
                    if len(cleaned) >= 10:
                        return text
        
        # Fallback to pattern matching
        text_content = soup.get_text(" ", strip=True)
        for pattern in self.phone_patterns:
            match = re.search(pattern, text_content)
            if match:
                return match.group(0)
                
        return None

    async def _extract_bio(self, soup: BeautifulSoup, site_config: Dict) -> Optional[str]:
        """Extract agent biography"""
        selectors = site_config.get('contact_selectors', {}).get('bio', '')
        
        if selectors:
            for selector in selectors.split(','):
                element = soup.select_one(selector.strip())
                if element:
                    return element.get_text("\n", strip=True)
        
        # Generic bio selectors
        generic_selectors = ['.agent-bio', '#agent-bio', '.bio', '.about-agent', '.agent-description']
        for selector in generic_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text("\n", strip=True)
                
        return None

    async def _extract_social_links(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract social media links"""
        links = {}
        for a in soup.find_all('a', href=True):
            href = a['href'].lower()
            for platform, domain in self.social_domains.items():
                if domain in href:
                    links[platform] = a['href']
        return links
    
    def _is_email(self, text: str) -> bool:
        """Check if text is an email"""
        email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
        return bool(re.match(email_pattern, text.strip()))
    
    def _verify_email_format(self, email: str) -> bool:
        """Verify email format"""
        if not email:
            return False
        return self._is_email(email)
