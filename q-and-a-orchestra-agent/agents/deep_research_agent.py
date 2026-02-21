import logging
import json
import asyncio
from typing import Dict, Any, List, Optional
from duckduckgo_search import DDGS
from agents.web_scraper.fetcher import PageFetcher
from agents.web_scraper.parser import HTMLParser
from google_integration.gemini_client import GeminiHybridClient
from google_integration.ollama_client import OllamaHybridClient

logger = logging.getLogger(__name__)

class DeepResearchAgent:
    """
    Agent that performs deep web research to find contact information
    when standard scraping fails. Uses Search -> Scrape -> Synthesize loop.
    """
    
    def __init__(self, gemini_client: Optional[GeminiHybridClient] = None, 
                 ollama_client: Optional[OllamaHybridClient] = None):
        self.fetcher = PageFetcher()
        self.parser = HTMLParser()
        self.gemini = gemini_client or GeminiHybridClient()
        self.ollama = ollama_client or OllamaHybridClient()
        self.ddgs = DDGS()
        
    async def execute(self, agent_data: Dict[str, Any], max_results: int = 3) -> Dict[str, Any]:
        """
        Execute deep research for a specific agent.
        """
        agent_name = agent_data.get('name', '')
        brokerage = agent_data.get('brokerage', '')
        city = agent_data.get('city', '')
        
        if not agent_name:
            return {'error': 'Missing agent name', 'emails': []}
            
        logger.info(f"Starting Deep Research for: {agent_name} at {brokerage}")
        
        # 1. Search Query Generation
        queries = [
            f"{agent_name} {brokerage} {city} email contact",
            f"{agent_name} real estate agent {city} email",
            f"{agent_name} {brokerage} profile"
        ]
        
        # 2. Perform Web Search
        links = []
        for query in queries[:1]: # Start with most specific
            try:
                # Add delay to avoid rate limits
                await asyncio.sleep(2.0)
                
                # Run sync DDGS in thread
                results = await asyncio.to_thread(lambda: list(self.ddgs.text(query, max_results=max_results)))
                for r in results:
                    links.append(r['href'])
            except Exception as e:
                logger.warning(f"Search failed for query '{query}': {e}")
        
        # Deduplicate links
        links = list(set(links))
        logger.info(f"Found {len(links)} potential sources: {links}")
        
        if not links:
            return {'error': 'No search results found', 'emails': []}
            
        # 3. Scrape & Analyze Pages
        found_emails = []
        confidence = 0.0
        sources = []
        
        # Process links concurrently but with limited concurrency to be polite
        # Process max 3 links
        links = links[:3]
        
        for link in links:
            # Add delay between page fetches
            await asyncio.sleep(1.0)
            res = await self._process_link(link, agent_data)
            
            if res and res.get('emails'):
                found_emails.extend(res['emails'])
                sources.append(res.get('source'))
                # Aggregate confidence (simple max for now)
                confidence = max(confidence, res.get('confidence', 0.0))
        
        # Deduplicate emails
        found_emails = list(set(found_emails))
        
        result = {
            'emails': found_emails,
            'confidence': confidence,
            'sources': sources,
            'method': 'deep_research'
        }
        
        if found_emails:
            logger.info(f"Deep Research success: {found_emails}")
        else:
            logger.info("Deep Research found no emails.")
            
        return result

    async def _process_link(self, url: str, agent_data: Dict) -> Optional[Dict]:
        """Fetch and analyze a single URL."""
        try:
            # Fetch
            html = await self.fetcher.fetch(url)
            if not html:
                return None
                
            # Parse text content (lightweight)
            soup = self.parser.parse(html)
            if not soup:
                return None
                
            text_content = soup.get_text(separator=' ', strip=True)[:10000] # Limit context window
            
            # Analyze with LLM
            # Prefer Gemini for reasoning, fallback to Ollama
            if self.gemini.enabled:
                result = await self.gemini.extract_emails(
                    content=f"Source URL: {url}\nPage Content: {text_content}",
                    agent_data=agent_data,
                    model="gemini-1.5-flash"
                )
            else:
                result = await self.ollama.extract_emails(
                    content=f"Source URL: {url}\nPage Content: {text_content}",
                    agent_data=agent_data,
                    use_cloud=False
                )
                
            if result and result.get('emails'):
                result['source'] = url
                return result
                
        except Exception as e:
            logger.warning(f"Failed to process {url}: {e}")
            
        return None
