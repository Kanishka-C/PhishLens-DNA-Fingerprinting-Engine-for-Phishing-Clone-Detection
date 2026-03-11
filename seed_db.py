import asyncio
import argparse
from urllib.parse import urlparse

from modules.url_input import validate_and_prepare_url
from modules.retrieval import fetch_webpage
from modules.dom_parser import parse_html_to_dom
from modules.feature_extraction import extract_features
from modules.dna_generator import generate_dna
from modules.repository import add_trusted_site

async def process_url(url: str):
    """Fetches a URL, calculates its DNA, and stores it in the database."""
    print(f"[*] Processing {url}...")
    try:
        valid_url = validate_and_prepare_url(url)
        domain = urlparse(valid_url).netloc
        
        # We handle 'www.' internally in decision module, but let's strip it here too just in case
        if domain.startswith('www.'):
            domain = domain[4:]
            
        print(f"  - Fetching HTML content...")
        html_content = await fetch_webpage(valid_url)
        
        print(f"  - Parsing DOM and extracting structural features...")
        dom_tree = parse_html_to_dom(html_content)
        features = extract_features(dom_tree)
        
        print(f"  - Generating Webpage DNA Fingerprint...")
        dna = generate_dna(features)
        
        print(f"  - Writing signature to DNA Repository table for domain: {domain}...")
        add_trusted_site(domain, dna)
        
        print(f"[+] Successfully added {domain} to trusted repository!\n")
    except Exception as e:
        print(f"[-] Error processing {url}: {e}\n")

async def main():
    parser = argparse.ArgumentParser(description="Manually add legitimate websites to the DNA Fingerprinting Repository.")
    parser.add_argument('url', nargs='*', help="One or more URLs to add (e.g., https://example.com https://google.com)")
    parser.add_argument('-f', '--file', help="Path to a text file containing one URL per line.")
    
    args = parser.parse_args()
    
    urls_to_process = args.url
    
    if args.file:
        try:
            with open(args.file, 'r') as f:
                file_urls = [line.strip() for line in f if line.strip()]
                urls_to_process.extend(file_urls)
        except Exception as e:
             print(f"Error reading file {args.file}: {e}")
             return
             
    if not urls_to_process:
        print("No URLs provided. Use -h for help.")
        print("Example: python seed_db.py https://example.com https://github.com")
        return

    # Process all URLs securely from backend script
    for url in urls_to_process:
        await process_url(url)

if __name__ == "__main__":
    asyncio.run(main())
