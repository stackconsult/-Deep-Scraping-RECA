#!/usr/bin/env python3
"""
Email Enrichment Engine for RECA Agents
Implements multiple strategies to find emails for real estate agents
"""

import os
import json
import time
import re
import requests
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailEnrichmentEngine:
    """Engine to enrich RECA agent data with email addresses."""
    
    def __init__(self, cache_dir: str = "cache/enrichment"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Rate limiting
        self.last_request_time = {}
        self.min_delay = 5.0  # seconds between requests to same domain
        
        # Email patterns to try
        self.email_patterns = [
            "{first}@{domain}",
            "{first}.{last}@{domain}",
            "{firstinitial}{last}@{domain}",
            "{first}{lastinitial}@{domain}",
            "{first}.{lastinitial}@{domain}",
            "{last}@{domain}",
            "{last}{firstinitial}@{domain}"
        ]
        
        # Common email domains for brokerages
        self.common_domains = [
            "@gmail.com", "@outlook.com", "@yahoo.ca", "@hotmail.com",
            "@icloud.com", "@telus.net", "@shaw.ca", "@rogers.com"
        ]
    
    def _rate_limit(self, domain: str):
        """Implement rate limiting per domain."""
        now = time.time()
        last_time = self.last_request_time.get(domain, 0)
        
        if now - last_time < self.min_delay:
            wait_time = self.min_delay - (now - last_time)
            logger.info(f"Rate limiting {domain}. Waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
        
        self.last_request_time[domain] = time.time()
    
    def _extract_domain_from_brokerage(self, brokerage: str, city: str) -> Optional[str]:
        """Extract domain from brokerage name."""
        # Try to find website from brokerage name
        search_terms = [
            f"{brokerage} {city} website",
            f"{brokerage} real estate {city}",
            f"{brokerage} Calgary" if city.lower() == "calgary" else f"{brokerage} {city}"
        ]
        
        # For now, try common patterns
        # Remove common words and create domain guess
        clean_name = re.sub(r'\b(realty|real estate|properties|group|team)\b', '', brokerage, flags=re.IGNORECASE)
        clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', clean_name).strip()
        
        if clean_name:
            domain_guess = clean_name.lower().replace(' ', '') + '.ca'
            return domain_guess
        
        return None
    
    def _generate_email_patterns(self, agent: Dict, domain: str) -> List[str]:
        """Generate possible email addresses for an agent."""
        first = agent.get('first_name', '').lower()
        last = agent.get('last_name', '').lower()
        first_initial = first[0] if first else ''
        last_initial = last[0] if last else ''
        
        emails = []
        for pattern in self.email_patterns:
            try:
                email = pattern.format(
                    first=first,
                    last=last,
                    firstinitial=first_initial,
                    lastinitial=last_initial,
                    domain=domain
                )
                emails.append(email)
            except:
                continue
        
        return emails
    
    def _validate_email_format(self, email: str) -> bool:
        """Basic email format validation."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _check_domain_exists(self, domain: str) -> bool:
        """Check if domain has MX records (basic validation)."""
        try:
            # Simple HTTP check as fallback
            response = requests.get(f"http://{domain}", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def _scrape_brokerage_website(self, brokerage: str, city: str, agent_name: str) -> Optional[str]:
        """Scrape brokerage website for agent email."""
        domain = self._extract_domain_from_brokerage(brokerage, city)
        if not domain:
            return None
        
        self._rate_limit(domain)
        
        try:
            # Try to find contact page or agent listing
            urls_to_try = [
                f"http://{domain}",
                f"https://{domain}",
                f"http://{domain}/contact",
                f"http://{domain}/agents",
                f"http://{domain}/our-team",
                f"http://{domain}/about"
            ]
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; RECA-Directory-Updater/1.0)'
            }
            
            for url in urls_to_try:
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        # Look for email addresses in page
                        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', response.text)
                        
                        # Try to find email matching agent name
                        for email in emails:
                            if self._validate_email_format(email):
                                # Check if email might belong to agent
                                email_local = email.split('@')[0].lower()
                                agent_first = agent.get('first_name', '').lower()
                                agent_last = agent.get('last_name', '').lower()
                                
                                if (agent_first in email_local or 
                                    agent_last in email_local or
                                    agent_first[0] + agent_last in email_local):
                                    return email
                        
                        # If no direct match, return first valid email
                        for email in emails:
                            if self._validate_email_format(email) and not any(domain in email for domain in self.common_domains):
                                return email
                
                except requests.exceptions.RequestException:
                    continue
        
        except Exception as e:
            logger.warning(f"Failed to scrape {domain}: {e}")
        
        return None
    
    def _try_pattern_generation(self, agent: Dict, brokerage: str, city: str) -> Optional[str]:
        """Generate email patterns and validate."""
        domain = self._extract_domain_from_brokerage(brokerage, city)
        if not domain:
            return None
        
        # Check if domain exists
        if not self._check_domain_exists(domain):
            return None
        
        # Generate patterns
        patterns = self._generate_email_patterns(agent, domain)
        
        # For now, return the most common pattern
        # In production, you might validate these
        if patterns:
            return patterns[0]  # Return {first}@{domain} as primary guess
        
        return None
    
    def enrich_agent(self, agent: Dict) -> Dict:
        """Enrich a single agent with email."""
        enriched_agent = agent.copy()
        
        # Initialize enrichment field
        enriched_agent["enrichment"] = {
            "email": None,
            "email_source": None,
            "email_confidence": 0.0,
            "enriched_at": datetime.now().isoformat(),
            "validation_status": None,
            "enrichment_method": None
        }
        
        # Try different strategies
        email = None
        source = None
        confidence = 0.0
        method = None
        
        # Strategy 1: Scrape brokerage website
        email = self._scrape_brokerage_website(
            agent.get('brokerage', ''),
            agent.get('city', ''),
            agent.get('name', '')
        )
        
        if email:
            source = "brokerage_website"
            confidence = 0.8
            method = "web_scraping"
        
        # Strategy 2: Pattern generation (if no email found)
        if not email:
            email = self._try_pattern_generation(
                agent,
                agent.get('brokerage', ''),
                agent.get('city', '')
            )
            
            if email:
                source = "pattern_generation"
                confidence = 0.5
                method = "pattern_matching"
        
        # Update enrichment data
        if email:
            enriched_agent["enrichment"]["email"] = email
            enriched_agent["enrichment"]["email_source"] = source
            enriched_agent["enrichment"]["email_confidence"] = confidence
            enriched_agent["enrichment"]["validation_status"] = "unvalidated"
            enriched_agent["enrichment"]["enrichment_method"] = method
        else:
            enriched_agent["enrichment"]["email_source"] = "not_found"
            enriched_agent["enrichment"]["email_confidence"] = 0.0
        
        return enriched_agent
    
    def enrich_agents(self, agents: List[Dict], checkpoint_file: Optional[str] = None) -> List[Dict]:
        """Enrich a list of agents with emails."""
        enriched_agents = []
        
        # Load checkpoint if exists
        processed_count = 0
        if checkpoint_file:
            checkpoint_path = Path(checkpoint_file)
            if checkpoint_path.exists():
                with open(checkpoint_path, 'r') as f:
                    checkpoint = json.load(f)
                    processed_count = checkpoint.get('processed_count', 0)
                    enriched_agents = checkpoint.get('enriched_agents', [])
        
        # Start from where we left off
        start_index = processed_count
        total = len(agents)
        
        logger.info(f"Starting enrichment from agent {start_index + 1}/{total}")
        
        for i in range(start_index, total):
            agent = agents[i]
            
            logger.info(f"Processing agent {i + 1}/{total}: {agent.get('name', 'Unknown')}")
            
            enriched_agent = self.enrich_agent(agent)
            enriched_agents.append(enriched_agent)
            
            # Save checkpoint every 50 agents
            if checkpoint_file and (i + 1) % 50 == 0:
                checkpoint = {
                    'processed_count': i + 1,
                    'enriched_agents': enriched_agents,
                    'updated_at': datetime.now().isoformat()
                }
                with open(checkpoint_file, 'w') as f:
                    json.dump(checkpoint, f, indent=2)
                
                # Report progress
                emails_found = sum(1 for a in enriched_agents if a.get('enrichment', {}).get('email'))
                logger.info(f"Checkpoint: {emails_found} emails found so far")
        
        return enriched_agents


def main():
    """Test the email enrichment engine."""
    # Load sample agents
    agents_file = Path("data/all_agents.json")
    
    if not agents_file.exists():
        logger.error(f"Agents file not found: {agents_file}")
        return
    
    with open(agents_file, 'r') as f:
        agents = json.load(f)
    
    # Take first 10 for testing
    sample_agents = agents[:10]
    
    # Initialize enrichment engine
    engine = EmailEnrichmentEngine()
    
    # Enrich agents
    enriched = engine.enrich_agents(
        sample_agents,
        checkpoint_file="data/enrichment_checkpoint.json"
    )
    
    # Save results
    output_file = Path("data/agents_enriched_sample.json")
    with open(output_file, 'w') as f:
        json.dump(enriched, f, indent=2)
    
    # Report
    emails_found = sum(1 for a in enriched if a.get('enrichment', {}).get('email'))
    logger.info(f"Enriched {len(enriched)} agents")
    logger.info(f"Found {emails_found} emails")
    logger.info(f"Results saved to {output_file}")


if __name__ == "__main__":
    main()