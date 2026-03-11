from typing import Dict, Any
import hashlib
import json

def generate_dna(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a unique fingerprint for each webpage.
    Encodes extracted features into a compact representation.
    """
    
    # The tag sequence is the primary indicator of the structure.
    # We can join tags into a single string to use sequence matching later.
    tag_sequence_str = ",".join(features.get('tag_order', []))
    
    # Create a compact metadata summary
    metadata = {
        'max_depth': features.get('max_dom_depth', 0),
        'scripts': features.get('script_count', 0),
        'links': features.get('link_count', 0)
    }
    
    # Create a quick structure hash for exact matches
    # Since tag lists can vary slightly even on legitimate sites based on dynamic content,
    # similarity is better. However, a hash is a good fast fallback/identifier.
    hashable_string = f"{tag_sequence_str}|{metadata['max_depth']}|{metadata['scripts']}|{metadata['links']}"
    structure_hash = hashlib.sha256(hashable_string.encode('utf-8')).hexdigest()
    
    dna = {
        'tag_sequence': tag_sequence_str,
        'metadata': metadata,
        'structure_hash': structure_hash
    }
    
    return dna
