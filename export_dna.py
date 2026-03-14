"""
PhishLens - DNA Fingerprint Data Export
Writes all pipeline metrics to a structured text/CSV report file.
"""
import csv
import json
import asyncio
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from modules.repository import get_all_trusted_sites
from modules.dom_parser import parse_html_to_dom
from modules.feature_extraction import extract_features
from modules.dna_generator import generate_dna

# ── Load Data ─────────────────────────────────────────────────────────────────
trusted     = get_all_trusted_sites()
insta_db    = next((s for s in trusted if s['domain'] == 'instagram.com'), None)
if not insta_db:
    raise SystemExit("instagram.com not found in DB. Run seed_db.py first.")

with open('clones/instagram_phish.html', 'r', encoding='utf-8') as f:
    clone_html = f.read()

clone_dom   = parse_html_to_dom(clone_html)
clone_feats = extract_features(clone_dom)
clone_dna   = generate_dna(clone_feats)

trusted_seq  = insta_db['dna']['tag_sequence']
clone_seq    = clone_dna['tag_sequence']
trusted_tags = trusted_seq.split(',')
clone_tags   = clone_seq.split(',')
t_meta       = insta_db['dna']['metadata']
c_meta       = clone_dna['metadata']

# ── TF-IDF + Cosine ───────────────────────────────────────────────────────────
vectorizer = TfidfVectorizer(token_pattern=r'(?u)[a-zA-Z0-9\-]+', ngram_range=(1, 3))
tfidf_mat  = vectorizer.fit_transform([trusted_seq, clone_seq])
cos_score  = float(cosine_similarity(tfidf_mat[0:1], tfidf_mat[1:2])[0][0])

feature_names = vectorizer.get_feature_names_out()
t_vec = np.asarray(tfidf_mat[0].todense()).flatten()
c_vec = np.asarray(tfidf_mat[1].todense()).flatten()

# N-grams helper
def ngrams(tags, n):
    return [' > '.join(tags[i:i+n]) for i in range(len(tags)-n+1)]

out_file = 'dna_report.txt'

with open(out_file, 'w', encoding='utf-8') as f:

    # ── Section 1: Tag Order ──────────────────────────────────────────────────
    f.write('=' * 70 + '\n')
    f.write('SECTION 1: TAG ORDER (Full Structural Sequence)\n')
    f.write('=' * 70 + '\n')
    f.write(f'\n[Trusted - instagram.com]  ({len(trusted_tags)} tags)\n')
    f.write(',  '.join(trusted_tags) + '\n\n')
    f.write(f'[Clone - localhost]  ({len(clone_tags)} tags)\n')
    f.write(',  '.join(clone_tags) + '\n\n')

    # ── Section 2: Structural Metadata ───────────────────────────────────────
    f.write('=' * 70 + '\n')
    f.write('SECTION 2: STRUCTURAL METADATA (Max Depth, Links, Scripts, Tag Count)\n')
    f.write('=' * 70 + '\n')
    f.write(f'\n{"Metric":<25} {"Trusted":>15} {"Clone":>15} {"Delta":>10}\n')
    f.write('-' * 65 + '\n')
    rows = [
        ('Max DOM Depth',   t_meta['max_depth'], c_meta['max_depth']),
        ('Script Count',    t_meta['scripts'],   c_meta['scripts']),
        ('Link Count',      t_meta['links'],     c_meta['links']),
        ('Total Tag Count', len(trusted_tags),   len(clone_tags)),
    ]
    for label, tv, cv in rows:
        f.write(f'{label:<25} {tv:>15} {cv:>15} {cv-tv:>+10}\n')
    f.write('\n')

    # ── Section 3: Top TF-IDF Values ─────────────────────────────────────────
    f.write('=' * 70 + '\n')
    f.write('SECTION 3: TOP TF-IDF VALUES (Top 20 weighted structural N-Grams)\n')
    f.write('=' * 70 + '\n')
    f.write(f'\n{"N-Gram Feature":<40} {"Trusted TF-IDF":>18} {"Clone TF-IDF":>15}\n')
    f.write('-' * 75 + '\n')
    top_idx = np.argsort(t_vec + c_vec)[-20:][::-1]
    for i in top_idx:
        f.write(f'{feature_names[i]:<40} {t_vec[i]:>18.6f} {c_vec[i]:>15.6f}\n')
    f.write('\n')

    # ── Section 4: Full TF-IDF Vectors ───────────────────────────────────────
    f.write('=' * 70 + '\n')
    f.write('SECTION 4: FULL TF-IDF VECTORS (all non-zero features)\n')
    f.write('=' * 70 + '\n')
    f.write(f'\n{"Index":<8} {"N-Gram Feature":<40} {"Trusted":>12} {"Clone":>12}\n')
    f.write('-' * 75 + '\n')
    nz = np.where((t_vec > 0) | (c_vec > 0))[0]
    for idx in nz:
        f.write(f'{idx:<8} {feature_names[idx]:<40} {t_vec[idx]:>12.6f} {c_vec[idx]:>12.6f}\n')
    f.write('\n')

    # ── Section 5: N-Gram Tag Order Analysis ─────────────────────────────────
    f.write('=' * 70 + '\n')
    f.write('SECTION 5: N-GRAM TAG ORDER ANALYSIS\n')
    f.write('=' * 70 + '\n')
    for n, label in [(2, 'Bi-grams'), (3, 'Tri-grams')]:
        f.write(f'\n--- {label} ---\n')
        f.write(f'\n{"Trusted Top 15":<45} {"Count":>6}    {"Clone Top 15":<45} {"Count":>6}\n')
        f.write('-' * 110 + '\n')
        t_ng = Counter(ngrams(trusted_tags, n)).most_common(15)
        c_ng = Counter(ngrams(clone_tags,   n)).most_common(15)
        for i in range(max(len(t_ng), len(c_ng))):
            tg, tc = t_ng[i] if i < len(t_ng) else ('', '')
            cg, cc = c_ng[i] if i < len(c_ng) else ('', '')
            f.write(f'{tg:<45} {tc:>6}    {cg:<45} {cc:>6}\n')
    f.write('\n')

    # ── Section 6: Cosine Similarity ─────────────────────────────────────────
    f.write('=' * 70 + '\n')
    f.write('SECTION 6: COSINE SIMILARITY ANALYSIS\n')
    f.write('=' * 70 + '\n')
    verdict = 'Phishing Clone' if cos_score >= 0.80 else ('Suspicious' if cos_score >= 0.60 else 'Legitimate (No Match)')
    f.write(f'\nTrusted Domain   : instagram.com\n')
    f.write(f'Analysed Clone   : localhost:9001/instagram_phish.html\n')
    f.write(f'Cosine Score     : {cos_score:.6f}  ({cos_score*100:.2f}%)\n')
    f.write(f'Threshold (High) : 0.80  (>= 80% = Phishing Clone if domain mismatch)\n')
    f.write(f'Threshold (Mid)  : 0.60  (>= 60% = Suspicious)\n')
    f.write(f'Verdict          : {verdict}\n')
    f.write(f'Domain Match     : NO  (localhost != instagram.com)\n')
    f.write('\n')

print(f'Report written to: {out_file}')
