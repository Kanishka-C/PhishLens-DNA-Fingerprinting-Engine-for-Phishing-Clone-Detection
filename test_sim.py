import asyncio
from modules.repository import get_all_trusted_sites
from modules.dom_parser import parse_html_to_dom
from modules.feature_extraction import extract_features
from modules.dna_generator import generate_dna
from modules.similarity import calculate_similarity

async def main():
    trusted = get_all_trusted_sites()
    insta_db = next((s for s in trusted if s['domain'] == 'instagram.com'), None)

    if not insta_db:
        print("Instagram not found in DB")
        return

    print("--- Instagram in DB ---")
    print(f"Tag length: {len(insta_db['dna']['tag_sequence'].split(','))}")

    with open('clones/instagram_phish.html', 'r', encoding='utf-8') as f:
        html = f.read()

    dom = parse_html_to_dom(html)
    feats = extract_features(dom)
    dna = generate_dna(feats)

    print("\n--- Instagram Local Clone ---")
    print(f"Tag length: {len(dna['tag_sequence'].split(','))}")

    score = calculate_similarity(dna, insta_db['dna'])
    print(f'\nCosine Similarity Score: {score}')

if __name__ == "__main__":
    asyncio.run(main())
