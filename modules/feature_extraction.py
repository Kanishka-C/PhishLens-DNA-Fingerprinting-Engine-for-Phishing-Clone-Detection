from bs4 import BeautifulSoup, Tag
from typing import Dict, Any, List

def extract_features(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Extracts stable structural properties that define the webpage.
    Returns a dictionary of features:
    - tag_order: list of HTML tags
    - max_dom_depth: int
    - script_count: int
    - link_count: int
    """
    
    tag_order = []
    max_dom_depth = 0
    script_count = 0
    link_count = 0
    
    # Helper to traverse and compute depth recursively
    def traverse(element, current_depth):
        nonlocal max_dom_depth, script_count, link_count
        
        if current_depth > max_dom_depth:
            max_dom_depth = current_depth
            
        if isinstance(element, Tag):
            tag_name = getattr(element, 'name', None)
            if tag_name:
                # To reduce noise, we might only include structural tags, 
                # but for an exact clone fingerprint, all tags are good.
                tag_order.append(tag_name)
                
                if tag_name == 'script':
                    script_count += 1
                elif tag_name == 'a':
                    link_count += 1
                    
            for child in element.children:
                if isinstance(child, Tag):
                    traverse(child, current_depth + 1)
    
    # Start traversal from the 'html' root or just soup
    html_root = soup.find('html')
    if html_root:
        traverse(html_root, 1)
    else:
        # Fallback if no explicit html tag
        for child in soup.children:
             if isinstance(child, Tag):
                 traverse(child, 1)
                 
    features = {
        'tag_order': tag_order,
        'max_dom_depth': max_dom_depth,
        'script_count': script_count,
        'link_count': link_count
    }
    
    return features
