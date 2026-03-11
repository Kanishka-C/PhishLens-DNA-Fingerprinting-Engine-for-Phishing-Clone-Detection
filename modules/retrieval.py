import httpx
import logging

logger = logging.getLogger(__name__)

async def fetch_webpage(url: str) -> str:
    """
    Fetches the webpage content for analysis.
    Handles timeouts, redirections, and errors.
    Returns raw HTML content of the webpage.
    """
    timeout = httpx.Timeout(10.0, connect=5.0) # 10s read, 5s connect timeout
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }
    
    try:
        # Disable SSL verification to prevent CERTIFICATE_VERIFY_FAILED errors in some environments
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, verify=False) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            # Ensure we are getting HTML content
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type and 'application/xhtml+xml' not in content_type:
                logger.warning(f"URL {url} returned non-HTML content type: {content_type}")
                
            return response.text
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred while fetching {url}: {e}")
        raise ValueError(f"Failed to fetch webpage: HTTP Status {e.response.status_code}")
    except httpx.RequestError as e:
        logger.error(f"Request error occurred while fetching {url}: {e}")
        raise ValueError(f"Failed to fetch webpage: Connection error or timeout")
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        raise ValueError(f"Unexpected error during retrieval: {str(e)}")
