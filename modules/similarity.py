from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, Any, List

def calculate_similarity(input_dna: Dict[str, Any], trusted_dna: Dict[str, Any]) -> float:
    """
    Measures structural similarity between two webpage fingerprints
    using TF-IDF Vectorization and Cosine Similarity on N-Grams of HTML tags.
    Returns a float between 0.0 and 1.0.
    """
    seq1 = input_dna.get('tag_sequence', '')
    seq2 = trusted_dna.get('tag_sequence', '')
    
    # Exact match fast path
    if input_dna.get('structure_hash') == trusted_dna.get('structure_hash'):
        return 1.0
        
    # If sequences are empty, they can't be compared meaningfully
    if not seq1 or not seq2:
        return 0.0
        
    # We treat the comma-separated tag sequence as a text document.
    # We use an n-gram range of (1, 3) to capture not just individual tags,
    # but structural patterns like ('div', 'div,h1', 'div,h1,p')
    # This prevents evasion by simply reordering tags.
    vectorizer = TfidfVectorizer(token_pattern=r'(?u)[a-zA-Z0-9\-]+', ngram_range=(1, 3))
    
    try:
        tfidf_matrix = vectorizer.fit_transform([seq1, seq2])
        # Compute cosine similarity between the two documents (vectors)
        score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(score)
    except ValueError:
        return 0.0

def find_best_match(input_dna: Dict[str, Any], repository_sites: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Finds the most similar trusted site in the repository.
    """
    best_score = 0.0
    best_match = None
    
    for site in repository_sites:
        score = calculate_similarity(input_dna, site['dna'])
        if score > best_score:
            best_score = score
            best_match = site
            
    return {
        'best_score': best_score,
        'matched_site': best_match
    }
