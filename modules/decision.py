from typing import Dict, Any, Tuple
from urllib.parse import urlparse

def classify_webpage(input_url: str, best_match_info: Dict[str, Any]) -> Tuple[str, str, float]:
    """
    Determines whether a webpage is legitimate or a clone.
    Returns (classification, matched_domain, score).
    """
    score = best_match_info['best_score']
    matched_site = best_match_info['matched_site']
    
    parsed_input = urlparse(input_url)
    input_domain = parsed_input.netloc.lower()
    # Strip www. to be safe
    if input_domain.startswith('www.'):
        input_domain = input_domain[4:]
        
    matched_domain = ""
    if matched_site:
        matched_domain = matched_site['domain'].lower()
        if matched_domain.startswith('www.'):
            matched_domain = matched_domain[4:]
            
    # thresholds
    # Cosine Similarity on TF-IDF N-grams is stricter than simple Levenshtein. 
    # A 0.80 match in structural N-grams is extremely high and indicates cloning.
    HIGH_SIMILARITY = 0.80
    MODERATE_SIMILARITY = 0.60
    
    if score >= HIGH_SIMILARITY:
        if matched_domain == input_domain:
            return ("Legitimate", matched_site['domain'], score)
        else:
            return ("Phishing clone", matched_site['domain'], score)
            
    elif score >= MODERATE_SIMILARITY:
        if matched_domain == input_domain:
            return ("Legitimate", matched_site['domain'], score) # Same domain, changed structure
        else:
            return ("Suspicious", matched_site['domain'], score)
            
    else:
        # If it doesn't match any of our protected targets, we consider it just another legitimate site.
        # But we classify it as 'Unknown / Legitimate'
        return ("Legitimate (No Match)", "None", score)
