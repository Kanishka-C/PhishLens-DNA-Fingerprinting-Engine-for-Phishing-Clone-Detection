from urllib.parse import urlparse
import re

def validate_and_prepare_url(url: str) -> str:
    """
    Validates and prepares the input URL.
    - Checks URL format
    - Ensures it has a scheme (defaults to https)
    """
    url = url.strip()
    
    # Check if a scheme exists, if not, prepend 'https://'
    if not re.match(r'^https?://', url, re.IGNORECASE):
        url = 'https://' + url
        
    parsed = urlparse(url)
    # Basic validation for an actual domain, or allow localhost
    domain = parsed.netloc.split(':')[0] # remove port if present
    if not domain or (not '.' in domain and domain not in ('localhost', '127.0.0.1')):
        raise ValueError(f"Invalid URL format: {url}")
        
    return url
