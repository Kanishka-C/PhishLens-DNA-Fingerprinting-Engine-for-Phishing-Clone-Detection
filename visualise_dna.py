"""
PhishLens - DNA Fingerprint Visualisation
Generates a multi-panel comparative chart showing all pipeline metrics
between the trusted website and the phishing clone.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from modules.repository import get_all_trusted_sites
from modules.dom_parser import parse_html_to_dom
from modules.feature_extraction import extract_features
from modules.dna_generator import generate_dna

# ── 1. Load Data ─────────────────────────────────────────────────────────────
trusted = get_all_trusted_sites()
insta_db = next((s for s in trusted if s['domain'] == 'instagram.com'), None)
if not insta_db:
    raise SystemExit("instagram.com not found in DB. Run seed_db.py first.")

with open('clones/instagram_phish.html', 'r', encoding='utf-8') as f:
    clone_html = f.read()

clone_dom   = parse_html_to_dom(clone_html)
clone_feats = extract_features(clone_dom)
clone_dna   = generate_dna(clone_feats)

trusted_seq = insta_db['dna']['tag_sequence']          # comma-separated
clone_seq   = clone_dna['tag_sequence']

trusted_tags = trusted_seq.split(',')
clone_tags   = clone_seq.split(',')

# ── 2. TF-IDF + Cosine ───────────────────────────────────────────────────────
vectorizer  = TfidfVectorizer(token_pattern=r'(?u)[a-zA-Z0-9\-]+', ngram_range=(1, 3))
tfidf_mat   = vectorizer.fit_transform([trusted_seq, clone_seq])
cos_score   = float(cosine_similarity(tfidf_mat[0:1], tfidf_mat[1:2])[0][0])

feature_names = vectorizer.get_feature_names_out()
t_vec = np.asarray(tfidf_mat[0].todense()).flatten()
c_vec = np.asarray(tfidf_mat[1].todense()).flatten()

# Top 12 highest-TF-IDF features (union of top-k from each)
top_idx = np.argsort(t_vec + c_vec)[-12:][::-1]
top_names  = [feature_names[i] for i in top_idx]
top_t_vals = [t_vec[i] for i in top_idx]
top_c_vals = [c_vec[i] for i in top_idx]

# ── 3. N-gram Counts ─────────────────────────────────────────────────────────
def ngrams(tags, n):
    return [' › '.join(tags[i:i+n]) for i in range(len(tags)-n+1)]

t_tri = Counter(ngrams(trusted_tags, 3)).most_common(8)
c_tri = Counter(ngrams(clone_tags,   3)).most_common(8)

# ── 4. Tag frequency counts ──────────────────────────────────────────────────
t_cnt = Counter(trusted_tags).most_common(10)
c_cnt = Counter(clone_tags).most_common(10)

# ── 5. Metadata comparison ───────────────────────────────────────────────────
t_meta = insta_db['dna']['metadata']
c_meta = clone_dna['metadata']

# ── 6. Plot ───────────────────────────────────────────────────────────────────
DARK   = '#0f1117'
CARD   = '#1a1d2e'
BLUE   = '#3b82f6'
RED    = '#ef4444'
GREEN  = '#22c55e'
AMBER  = '#f59e0b'
TXT    = '#e2e8f0'
SUBTLE = '#64748b'

plt.rcParams.update({
    'figure.facecolor':  DARK,
    'axes.facecolor':    CARD,
    'axes.edgecolor':    SUBTLE,
    'axes.labelcolor':   TXT,
    'xtick.color':       TXT,
    'ytick.color':       TXT,
    'text.color':        TXT,
    'grid.color':        '#2a2d3e',
    'grid.linewidth':    0.5,
    'font.family':       'DejaVu Sans',
})

fig = plt.figure(figsize=(22, 20), facecolor=DARK)
fig.suptitle('PhishLens  ·  DNA Fingerprint Comparative Analysis\nInstagram (Trusted) vs Phishing Clone',
             fontsize=19, fontweight='bold', color=TXT, y=0.98)

gs = gridspec.GridSpec(4, 3, figure=fig, hspace=0.55, wspace=0.38,
                       top=0.94, bottom=0.04, left=0.06, right=0.97)

# ── Panel A: Metadata bar chart ───────────────────────────────────────────────
axA = fig.add_subplot(gs[0, 0])
labels   = ['Max Depth', 'Scripts', 'Links', 'Tag Count']
t_vals_m = [t_meta['max_depth'], t_meta['scripts'], t_meta['links'], len(trusted_tags)]
c_vals_m = [c_meta['max_depth'], c_meta['scripts'], c_meta['links'], len(clone_tags)]
x = np.arange(len(labels));  w = 0.35
b1 = axA.bar(x - w/2, t_vals_m, w, color=BLUE,  label='Trusted', zorder=3)
b2 = axA.bar(x + w/2, c_vals_m, w, color=RED,   label='Clone',   zorder=3)
axA.set_xticks(x); axA.set_xticklabels(labels, fontsize=9)
axA.set_title('Structural Metadata', fontweight='bold')
axA.legend(fontsize=8); axA.grid(axis='y', zorder=0)
axA.set_ylabel('Count')

# ── Panel B: Tag Order Distribution (top 10 tags) ─────────────────────────────
axB = fig.add_subplot(gs[0, 1])
all_top_tags = list(dict.fromkeys([t for t,_ in t_cnt] + [t for t,_ in c_cnt]))[:10]
t_freq = [Counter(trusted_tags).get(tag, 0) for tag in all_top_tags]
c_freq = [Counter(clone_tags  ).get(tag, 0) for tag in all_top_tags]
x2 = np.arange(len(all_top_tags))
axB.bar(x2 - w/2, t_freq, w, color=BLUE, label='Trusted', zorder=3)
axB.bar(x2 + w/2, c_freq, w, color=RED,  label='Clone',   zorder=3)
axB.set_xticks(x2); axB.set_xticklabels(all_top_tags, rotation=40, ha='right', fontsize=8)
axB.set_title('Top Tag Frequency (Tag Order)', fontweight='bold')
axB.legend(fontsize=8); axB.grid(axis='y', zorder=0)

# ── Panel C: Cosine Similarity Gauge ─────────────────────────────────────────
axC = fig.add_subplot(gs[0, 2])
axC.set_aspect('equal')
theta  = np.linspace(np.pi, 0, 300)
# background arcs: danger / warning / safe
for (lo, hi, col) in [(0, 0.5, RED), (0.5, 0.75, AMBER), (0.75, 1.0, GREEN)]:
    t = np.linspace(np.pi*(1-lo), np.pi*(1-hi), 100)
    axC.plot(np.cos(t), np.sin(t), lw=14, color=col, solid_capstyle='round', alpha=0.25)
needle_angle = np.pi * (1 - cos_score)
axC.annotate('', xy=(0.62*np.cos(needle_angle), 0.62*np.sin(needle_angle)),
             xytext=(0, 0),
             arrowprops=dict(arrowstyle='->', color=TXT, lw=3))
axC.text(0, -0.18, f'{cos_score*100:.1f}%', ha='center', va='center',
         fontsize=26, fontweight='bold',
         color=GREEN if cos_score < 0.8 else RED)
axC.text(0, -0.42, 'Cosine Similarity Score', ha='center', fontsize=9, color=SUBTLE)
verdict = 'Phishing Clone' if cos_score >= 0.80 else ('Suspicious' if cos_score >= 0.60 else 'No Match')
axC.text(0, -0.60, verdict, ha='center', fontsize=11, fontweight='bold',
         color=RED if verdict == 'Phishing Clone' else AMBER)
axC.set_xlim(-1.1, 1.1); axC.set_ylim(-0.8, 1.1)
axC.axis('off')
axC.set_title('Cosine Similarity Gauge', fontweight='bold')

# ── Panel D: TF-IDF Values (top N-grams, Trusted) ────────────────────────────
axD = fig.add_subplot(gs[1, :2])
x3   = np.arange(len(top_names)); w3 = 0.38
axD.bar(x3 - w3/2, top_t_vals, w3, color=BLUE, label='Trusted', zorder=3)
axD.bar(x3 + w3/2, top_c_vals, w3, color=RED,  label='Clone',   zorder=3)
axD.set_xticks(x3); axD.set_xticklabels(top_names, rotation=38, ha='right', fontsize=7.5)
axD.set_title('Top TF-IDF Feature Values (Structural N-Grams)', fontweight='bold')
axD.set_ylabel('TF-IDF Weight'); axD.legend(fontsize=8); axD.grid(axis='y', zorder=0)

# ── Panel E: TF-IDF Vector scatter ────────────────────────────────────────────
axE = fig.add_subplot(gs[1, 2])
# Plot only features where at least one vector is non-zero
nz = np.where((t_vec > 0) | (c_vec > 0))[0]
axE.scatter(t_vec[nz], c_vec[nz], s=18, alpha=0.55, color=BLUE, zorder=3)
lim = max(t_vec[nz].max(), c_vec[nz].max()) * 1.1
axE.plot([0, lim], [0, lim], '--', color=SUBTLE, lw=1, label='Perfect match')
axE.set_xlabel('Trusted TF-IDF', fontsize=9)
axE.set_ylabel('Clone TF-IDF',   fontsize=9)
axE.set_title('TF-IDF Vector Space', fontweight='bold')
axE.legend(fontsize=8); axE.grid(zorder=0)

# ── Panel F: Top Trusted N-Grams ──────────────────────────────────────────────
axF = fig.add_subplot(gs[2, 0])
grams_t, counts_t = zip(*t_tri) if t_tri else ([], [])
axF.barh(list(grams_t)[::-1], list(counts_t)[::-1], color=BLUE, zorder=3)
axF.set_title('Top 3-Tag N-Grams · Trusted', fontweight='bold', fontsize=10)
axF.set_xlabel('Frequency'); axF.grid(axis='x', zorder=0)
axF.tick_params(axis='y', labelsize=7.5)

# ── Panel G: Top Clone N-Grams ────────────────────────────────────────────────
axG = fig.add_subplot(gs[2, 1])
grams_c, counts_c = zip(*c_tri) if c_tri else ([], [])
axG.barh(list(grams_c)[::-1], list(counts_c)[::-1], color=RED, zorder=3)
axG.set_title('Top 3-Tag N-Grams · Clone', fontweight='bold', fontsize=10)
axG.set_xlabel('Frequency'); axG.grid(axis='x', zorder=0)
axG.tick_params(axis='y', labelsize=7.5)

# ── Panel H: Cumulative Tag Order Curve ───────────────────────────────────────
axH = fig.add_subplot(gs[2, 2])
uniq = sorted(set(trusted_tags + clone_tags))
t_cum = np.cumsum([Counter(trusted_tags).get(u, 0) for u in uniq])
c_cum = np.cumsum([Counter(clone_tags  ).get(u, 0) for u in uniq])
axH.plot(t_cum, color=BLUE, label='Trusted', lw=2)
axH.plot(c_cum, color=RED,  label='Clone',   lw=2, linestyle='--')
axH.set_title('Cumulative Tag Order Curve', fontweight='bold')
axH.set_xlabel('Unique Tags (sorted)'); axH.set_ylabel('Cumulative Count')
axH.legend(fontsize=8); axH.grid(zorder=0)

# ── Panel I: Summary Stats Table ─────────────────────────────────────────────
axI = fig.add_subplot(gs[3, :])
axI.axis('off')
rows = [
    ['Metric',              'Trusted (instagram.com)', 'Phishing Clone (localhost)', 'Δ Delta'],
    ['Total Tags',          str(len(trusted_tags)),   str(len(clone_tags)),          str(len(clone_tags)-len(trusted_tags))],
    ['Max DOM Depth',       str(t_meta['max_depth']), str(c_meta['max_depth']),      str(c_meta['max_depth']-t_meta['max_depth'])],
    ['Script Count',        str(t_meta['scripts']),   str(c_meta['scripts']),        str(c_meta['scripts']-t_meta['scripts'])],
    ['Link Count',          str(t_meta['links']),     str(c_meta['links']),          str(c_meta['links']-t_meta['links'])],
    ['Cosine Similarity',   '1.000 (Self)',            f'{cos_score:.4f}',            f'{cos_score-1:.4f}'],
    ['Verdict',             'Legitimate',              verdict,                       '—'],
]
col_widths = [0.22, 0.26, 0.30, 0.14]
col_colors = [[BLUE, BLUE, RED, AMBER]] + [[CARD]*4]*(len(rows)-1)
tbl = axI.table(cellText=rows[1:], colLabels=rows[0],
                cellLoc='center', loc='center', bbox=[0,0,1,1])
tbl.auto_set_font_size(False)
tbl.set_fontsize(9.5)
for (r, c), cell in tbl.get_celld().items():
    cell.set_facecolor(CARD if r > 0 else BLUE)
    cell.set_text_props(color=TXT, fontweight='bold' if r == 0 else 'normal')
    cell.set_edgecolor(SUBTLE)
axI.set_title('Pipeline Metrics Summary', fontweight='bold', pad=8)

# ── Save ──────────────────────────────────────────────────────────────────────
out = 'dna_visualisation.png'
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor=DARK)
print(f'Saved → {out}')
