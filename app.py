from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import uvicorn
import logging
import time

# ── Logger Setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger('PhishLens')

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
    t_start = time.time()
    try:
        log.info("="*60)
        log.info(f"[1/9] REQUEST  → '{request.url}'")

        # 2. URL Input Module
        valid_url = validate_and_prepare_url(request.url)
        log.info(f"[2/9] URL OK   → {valid_url}")

        # 3. Webpage Retrieval
        log.info(f"[3/9] FETCH    → Downloading HTML from {valid_url} ...")
        html_content = await fetch_webpage(valid_url)
        log.info(f"[3/9] FETCH OK → {len(html_content):,} bytes received")

        # 4. DOM Parsing
        log.info("[4/9] DOM      → Parsing HTML into DOM tree ...")
        dom_tree = parse_html_to_dom(html_content)
        log.info("[4/9] DOM OK   → DOM tree built")

        # 5. Feature Extraction
        log.info("[5/9] FEATURES → Extracting structural features ...")
        features = extract_features(dom_tree)
        log.info(f"[5/9] FEATURES → Tags: {len(features.get('tag_order', []))}  |  Depth: {features.get('max_dom_depth')}  |  Scripts: {features.get('script_count')}  |  Links: {features.get('link_count')}")

        # 6. DNA Generation
        log.info("[6/9] DNA      → Generating structural DNA fingerprint ...")
        dna = generate_dna(features)
        log.info(f"[6/9] DNA OK   → Hash: {dna['structure_hash'][:20]}...")

        # 7. Cybersecurity extras
        log.info("[7/9] SECURITY → Running SSL & Endpoint analysis ...")
        ssl_info  = analyze_ssl_certificate(valid_url)
        endpoints = extract_endpoints(dom_tree, valid_url)
        ssl_status = 'Valid ✓' if ssl_info.get('valid_cert') else ('No SSL' if not ssl_info.get('has_ssl') else 'Invalid ✗')
        log.info(f"[7/9] SECURITY → SSL: {ssl_status}  |  APIs found: {len(endpoints.get('api_endpoints', []))}  |  Ext scripts: {len(endpoints.get('external_scripts', []))}")

        # 8. Repository lookup
        log.info("[8/9] REPO     → Loading trusted DNA repository ...")
        trusted_sites = get_all_trusted_sites()
        log.info(f"[8/9] REPO OK  → {len(trusted_sites)} trusted site(s) loaded")

        if not trusted_sites:
             log.warning("[8/9] REPO     → WARNING: Repository is empty! Run seed_db.py first.")
             return {
                 "status": "warning",
                 "message": "No trusted sites in repository. Please run seed_db.py first.",
                 "classification": "Unknown",
                 "score": 0.0,
                 "ssl_info": ssl_info,
                 "endpoints": endpoints
             }

        # 9. Similarity Analysis
        log.info("[9/9] SIMILARITY → Computing TF-IDF Cosine Similarity against all trusted sites ...")
        best_match_info = find_best_match(dna, trusted_sites)

        # 10. Decision
        classification, matched_domain, score = classify_webpage(valid_url, best_match_info)
        elapsed = time.time() - t_start
        log.info(f"[RESULT] → Score: {score*100:.2f}%  |  Matched: {matched_domain}  |  Verdict: {classification.upper()}  |  ({elapsed:.2f}s)")
        log.info("="*60)

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
        log.error(f"[ERROR] Pipeline failed for '{request.url}': {e}")
        log.info("="*60)
        raise HTTPException(status_code=400, detail=str(e))

# Mount frontend static files if the directory exists
frontend_path = os.path.join(os.path.dirname(__file__), 'frontend')
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
