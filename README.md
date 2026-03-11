# PhishLens: Website DNA Fingerprinting Engine

PhishLens is a deterministic, non-ML cybersecurity engine designed to detect phishing clones by analyzing the structural HTML DOM footprint of websites. It converts a website's structural tag sequence into a mathematical vector and compares it against trusted repositories using **TF-IDF Vectorization and Cosine Similarity on N-Grams**.

## Features
- **Structural DNA Fingerprinting**: Deterministically detects clones regardless of stolen images or altered CSS.
- **Advanced Similarity Engine**: Uses Scikit-Learn (TF-IDF Cosine Similarity) to calculate structural proximity.
- **Attack Surface Extractor**: Dissects the target's DOM and inline scripts with regex to map active API endpoints, external scripts, and external links.
- **SSL Certificate Validation**: Safely retrieves and analyzes the target's SSL certificate details (Validity, Issuer, Expiry) via direct socket connections.
- **Local DNA Repository**: A lightweight SQLite database used to store the structural DNA of known safe sites for real-time comparison.

## Architecture
- **Backend**: Python 3.11 with FastAPI (`app.py`), `BeautifulSoup4` for DOM parsing, and `scikit-learn` for mathematical sequence scoring.
- **Frontend**: Vanilla HTML/JS/CSS with a premium dark-mode, glassmorphism UI.

## Local Development Setup

1. **Clone the repository and enter the directory**:
   ```bash
   git clone <repository_url>
   cd WebsiteDNAFingerprinting
   ```

2. **Set up the virtual environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
   ```

3. **Install Dependencies**:
   ```bash
   pip install fastapi uvicorn beautifulsoup4 httpx python-Levenshtein lxml scikit-learn
   ```

4. **Seed the Database with Trusted Sites**:
   The `dna_repository.db` is ignored by git for security. You must generate it locally.
   ```bash
   python seed_db.py https://federalbank.co.in https://instagram.com
   ```

5. **Start the Engine**:
   ```bash
   uvicorn app:app --reload
   ```

6. **Access the Dashboard**:
   Open a browser and navigate to `http://127.0.0.1:8000` to access the PhishLens Analyst UI.

## Testing a Phishing Clone
To see the engine in action, you can fetch a site and host it locally on a different port (e.g., `localhost:9000`) and feed that URL into the main dashboard. It will recognize the mismatched domain and high structural similarity, flagging it as a "Phishing clone".
