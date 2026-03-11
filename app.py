from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import uvicorn

# Import modules
from modules.url_input import validate_and_prepare_url
from modules.retrieval import fetch_webpage
from modules.dom_parser import parse_html_to_dom
from modules.feature_extraction import extract_features
from modules.dna_generator import generate_dna
from modules.repository import get_all_trusted_sites, add_trusted_site
from modules.similarity import find_best_match
from modules.decision import classify_webpage
from modules.ssl_analyzer import analyze_ssl_certificate
from modules.endpoint_extractor import extract_endpoints

app = FastAPI(title="Website DNA Fingerprinting API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    url: str

@app.post("/api/analyze")
async def analyze_url(request: AnalyzeRequest):
    try:
        # 2. URL Input Module
        valid_url = validate_and_prepare_url(request.url)
        
        # 3. Webpage Retrieval Unit
        html_content = await fetch_webpage(valid_url)
        
        # 4. DOM Parsing Module
        dom_tree = parse_html_to_dom(html_content)
        
        # 5. Structural Feature Extraction Module
        features = extract_features(dom_tree)
        
        # 6. Webpage DNA Generator
        dna = generate_dna(features)
        
        # 7. Cybersecurity Features: SSL & Endpoints
        ssl_info = analyze_ssl_certificate(valid_url)
        endpoints = extract_endpoints(dom_tree, valid_url)
        
        # 8. DNA Repository lookup & 9. Similarity Analysis
        trusted_sites = get_all_trusted_sites()
        
        if not trusted_sites:
             return {
                 "status": "warning",
                 "message": "No trusted sites in repository. Please run seed_db.py first.",
                 "classification": "Unknown",
                 "score": 0.0,
                 "ssl_info": ssl_info,
                 "endpoints": endpoints
             }
             
        best_match_info = find_best_match(dna, trusted_sites)
        
        # 10. Decision & Classification Module
        classification, matched_domain, score = classify_webpage(valid_url, best_match_info)
        
        return {
            "status": "success",
            "url": valid_url,
            "classification": classification,
            "similarity_score": round(score, 4),
            "matched_domain": matched_domain,
            "dna_metadata": dna['metadata'],
            "ssl_info": ssl_info,
            "endpoints": endpoints
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Mount frontend static files if the directory exists
frontend_path = os.path.join(os.path.dirname(__file__), 'frontend')
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
