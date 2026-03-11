import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import Dict, List, Any

def extract_endpoints(soup: BeautifulSoup, base_url: str) -> Dict[str, List[str]]:
    """
    Extracts potential API endpoints, external scripts, and interesting links from the DOM.
    Returns categorized endpoints.
    """
    external_scripts = set()
    api_endpoints = set()
    internal_links = set()
    external_links = set()
    
    base_domain = urlparse(base_url).netloc
    
    # Extract Scripts
    for script in soup.find_all('script'):
        src = script.get('src')
        if src:
            absolute_url = urljoin(base_url, src)
            if urlparse(absolute_url).netloc != base_domain:
                external_scripts.add(absolute_url)
            else:
                # Local scripts might have API calls inside
                pass
                
        # Simple regex to find API-like patterns in inline scripts
        if script.string:
            # Look for fetch('...', axios.get('...'), or /api/ patterns
            matches = re.findall(r'[\'"](/api/[^\'"]+|https?://[^\'"]+/api/[^\'"]+)[\'"]', script.string)
            for match in matches:
                 api_endpoints.add(urljoin(base_url, match))

    # Extract Links
    for a_tag in soup.find_all('a'):
        href = a_tag.get('href')
        if href and not href.startswith('#') and not href.startswith('javascript:'):
            absolute_url = urljoin(base_url, href)
            parsed_href = urlparse(absolute_url)
            
            if parsed_href.netloc != base_domain:
                external_links.add(absolute_url)
            else:
                internal_links.add(absolute_url)
                # Check if it looks like an API or data endpoint
                if '/api/' in parsed_href.path or parsed_href.path.endswith('.json'):
                    api_endpoints.add(absolute_url)

    # Forms can also point to endpoints
    for form in soup.find_all('form'):
        action = form.get('action')
        if action:
            api_endpoints.add(urljoin(base_url, action))

    return {
        "api_endpoints": sorted(list(api_endpoints))[:10], # Limit to top 10 to avoid bloat
        "external_scripts": sorted(list(external_scripts))[:10],
        "external_links_count": len(external_links),
        "internal_links_count": len(internal_links)
    }
