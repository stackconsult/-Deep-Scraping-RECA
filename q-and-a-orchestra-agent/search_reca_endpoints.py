#!/usr/bin/env python3
"""
Search for alternative RECA endpoints and site structure.
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

def search_reca_endpoints():
    """Search for RECA search endpoints."""
    
    base_domains = [
        "https://myreca.ca",
        "https://www.myreca.ca", 
        "https://reca.ca",
        "https://www.reca.ca",
        "https://reports.myreca.ca",
        "https://secure.myreca.ca"
    ]
    
    search_paths = [
        "/publicsearch.aspx",
        "/search",
        "/public-search",
        "/member-search",
        "/licensee-search",
        "/find-a-realtor",
        "/member-directory"
    ]
    
    print("=== Searching for RECA Endpoints ===\n")
    
    for domain in base_domains:
        print(f"--- Checking domain: {domain} ---")
        
        # Try main domain first
        try:
            response = requests.get(domain, timeout=10, verify=False)
            print(f"✓ Main domain accessible (Status: {response.status_code})")
            
            # Look for search-related links
            soup = BeautifulSoup(response.text, 'html.parser')
            search_links = []
            
            # Find all links that might be search pages
            for link in soup.find_all('a', href=True):
                href = link.get('href', '').lower()
                text = link.get_text().lower()
                
                if any(keyword in href or keyword in text for keyword in ['search', 'public', 'member', 'licensee', 'realtor', 'directory']):
                    full_url = urljoin(domain, link['href'])
                    search_links.append((full_url, text))
            
            if search_links:
                print("  Found potential search links:")
                for url, text in search_links[:5]:  # Show first 5
                    print(f"    - {url} (text: '{text[:50]}...')")
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to access: {str(e)}")
        
        # Try specific search paths
        for path in search_paths:
            url = domain + path
            try:
                response = requests.get(url, timeout=10, verify=False)
                if response.status_code == 200:
                    print(f"✓ Found working search endpoint: {url}")
                    
                    # Check if it's the right kind of page
                    if 'asp.net' in response.text.lower() or 'viewstate' in response.text.lower():
                        print("  → Appears to be an ASP.NET form (good match)")
                elif response.status_code == 404:
                    pass  # Expected for many paths
                else:
                    print(f"? Unexpected status for {url}: {response.status_code}")
                    
            except requests.exceptions.RequestException:
                pass  # Expected for many combinations
        
        print()
    
    # Try to find the actual current RECA public search
    print("--- Checking for current RECA public search ---")
    try:
        # Google search for RECA public search
        search_url = "https://www.google.com/search?q=RECA+Alberta+public+search+site:myreca.ca"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            # Extract URLs from search results
            urls = re.findall(r'https?://[^\s<>"\']+', response.text)
            unique_urls = list(set(urls))
            
            print("Found potential URLs from search:")
            for url in unique_urls[:5]:
                if 'myreca.ca' in url or 'reca.ca' in url:
                    print(f"  - {url}")
                    
    except Exception as e:
        print(f"Could not perform search: {str(e)}")

if __name__ == "__main__":
    search_reca_endpoints()