#!/usr/bin/env python3
"""
DataBreach.com API Client for email enrichment.
Handles authentication, rate limiting, and caching.
"""

import os
import json
import time
import hashlib
import requests
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataBreachClient:
    """Client for DataBreach.com API with rate limiting and caching."""
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: str = "cache/databreach"):
        self.api_key = api_key or os.getenv('DATABREACH_API_KEY')
        if not self.api_key:
            raise ValueError("DataBreach API key required. Set DATABREACH_API_KEY environment variable.")
        
        self.base_url = "https://api.databreach.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'RECA-Enricher/1.0'
        })
        
        # Rate limiting: 100 requests per minute
        self.requests_per_minute = 100
        self.request_times = []
        
        # Cache setup
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = timedelta(hours=24)
        
        # Retry configuration
        self.max_retries = 5
        self.base_retry_delay = 1.0
        
    def _rate_limit(self):
        """Implement rate limiting using token bucket algorithm."""
        now = time.time()
        
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        # Check if we're at the limit
        if len(self.request_times) >= self.requests_per_minute:
            # Calculate wait time
            oldest_request = min(self.request_times)
            wait_time = 60 - (now - oldest_request)
            
            if wait_time > 0:
                logger.info(f"Rate limit reached. Waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
        
        # Record this request
        self.request_times.append(now)
    
    def _get_cache_key(self, params: Dict) -> str:
        """Generate cache key from search parameters."""
        # Create deterministic string from params
        param_str = json.dumps(params, sort_keys=True)
        return hashlib.sha256(param_str.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get full path for cache file."""
        return self.cache_dir / f"{cache_key}.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file exists and is still valid."""
        if not cache_path.exists():
            return False
        
        file_mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - file_mtime < self.cache_ttl
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Retrieve data from cache if valid."""
        cache_path = self._get_cache_path(cache_key)
        
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                logger.debug(f"Cache hit for key: {cache_key[:8]}...")
                return data
            except Exception as e:
                logger.warning(f"Failed to read cache: {e}")
        
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict):
        """Save data to cache."""
        cache_path = self._get_cache_path(cache_key)
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved to cache: {cache_key[:8]}...")
        except Exception as e:
            logger.warning(f"Failed to save to cache: {e}")
    
    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """Make API request with retry logic and rate limiting."""
        self._rate_limit()
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(
                    f"{self.base_url}/{endpoint}",
                    params=params,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limited from server side
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited by server. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                elif response.status_code in [500, 502, 503, 504]:
                    # Server error, retry with backoff
                    if attempt < self.max_retries - 1:
                        delay = self.base_retry_delay * (2 ** attempt)
                        logger.warning(f"Server error {response.status_code}. Retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                
                # Other errors, don't retry
                response.raise_for_status()
                
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    delay = self.base_retry_delay * (2 ** attempt)
                    logger.warning(f"Request failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    raise
        
        raise Exception(f"Max retries exceeded for request to {endpoint}")
    
    def search_person(self, 
                     first_name: str,
                     last_name: str,
                     city: Optional[str] = None,
                     company: Optional[str] = None,
                     require_email: bool = True) -> Dict:
        """
        Search for a person in DataBreach.com.
        
        Args:
            first_name: First name of the person
            last_name: Last name of the person
            city: Optional city filter
            company: Optional company/brokerage filter
            require_email: Only return results with email addresses
            
        Returns:
            Dictionary with search results or empty if no matches
        """
        # Build search parameters
        params = {
            'first_name': first_name,
            'last_name': last_name,
            'require_email': str(require_email).lower()
        }
        
        if city:
            params['city'] = city
        if company:
            params['company'] = company
        
        # Check cache first
        cache_key = self._get_cache_key(params)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        # Make API request
        logger.info(f"Searching DataBreach for: {first_name} {last_name}, {city}, {company}")
        result = self._make_request('search/person', params)
        
        # Save to cache
        self._save_to_cache(cache_key, result)
        
        return result
    
    def get_person_details(self, person_id: str) -> Dict:
        """Get detailed information for a specific person."""
        cache_key = f"details_{person_id}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        result = self._make_request(f'person/{person_id}', {})
        self._save_to_cache(cache_key, result)
        
        return result
    
    def get_usage_stats(self) -> Dict:
        """Get current API usage statistics."""
        # This would be implemented based on DataBreach API docs
        # For now, return local tracking
        return {
            'requests_this_minute': len(self.request_times),
            'cache_files': len(list(self.cache_dir.glob("*.json"))),
            'rate_limit': self.requests_per_minute
        }
    
    def clear_cache(self, older_than: Optional[timedelta] = None):
        """Clear cache files."""
        if older_than is None:
            older_than = self.cache_ttl
        
        cutoff = datetime.now() - older_than
        cleared = 0
        
        for cache_file in self.cache_dir.glob("*.json"):
            file_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if file_mtime < cutoff:
                cache_file.unlink()
                cleared += 1
        
        logger.info(f"Cleared {cleared} expired cache files")
        return cleared


# Test function
def test_client():
    """Test the DataBreach client with sample data."""
    client = DataBreachClient()
    
    # Test search
    result = client.search_person(
        first_name="John",
        last_name="Smith",
        city="Calgary",
        company="ABC Realty"
    )
    
    print(f"Search result: {json.dumps(result, indent=2)}")
    print(f"Usage stats: {client.get_usage_stats()}")


if __name__ == "__main__":
    test_client()