from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def parse_html_to_dom(html_content: str) -> BeautifulSoup:
    """
    Transforms raw HTML into a structured format (DOM tree).
    Returns a BeautifulSoup object representing hierarchical relationships.
    """
    try:
        # We use lxml if available for speed, fallback to html.parser
        soup = BeautifulSoup(html_content, 'lxml')
        return soup
    except Exception as default_exception:
        logger.warning("Failed to parse with lxml, falling back to html.parser")
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup
        except Exception as e:
            logger.error(f"Failed to parse DOM: {e}")
            raise ValueError("Could not parse the HTML content into a DOM tree.")
