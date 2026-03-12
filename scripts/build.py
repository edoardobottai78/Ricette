#!/usr/bin/env python3
"""
build.py — Legge ricette.txt e genera index.html
Formato supportato:
  Titolo
  Titolo | Note su una riga
  ---
  Titolo
  ingrediente 1
  ingrediente 2
  procedimento...
  ---
"""

import json, re, sys
from pathlib import Path

UNSPLASH_KEY = "f_95Zpj5cCokVF6wE_wzrIZv4SloLmioUiyD5_BM3ZU"
INPUT_FILE   = Path("ricette.txt")
OUTPUT_FILE  = Path("index.html")

CATEGORY_RULES = [
    ("Dolci & Dessert",         r"torta|dolce|cupcake|biscotto|castagnaccio|sablé|sable|zuppetta di fragole|panna cotta|financier|cremoso|mousse|crumble|crostata|frolla|sorbetto|pan di spagna|bavarese|chantilly|zabaione dolce|bicchiere composta"),
    ("Pizza & Focaccia",        r"pizza|focaccia|schiacciata"),
    ("Tacos & Street Food",     r"tacos|taco|nachos|cono|coni|tramezzini"),
    ("Panini & Piadine",        r"panino|piadina|bun |burger"),
    ("Primi Piatti",            r"pasta|spaghetti|spaghetto|tagliatelle|pappardelle|rigatoni|paccheri|mezze maniche|tonnarelli|risotto|gnocchi|lasagne|ravioli|tortelli|cappellacci|passatelli|cous cous|riso |minestra|zuppa di|gnocco"),
    ("Secondi Piatti",          r"filetto|polpo|polpette|cozze fritte|cavolo cappuccio|bocconcini di pollo|jarret|fegatini|arancina|arancine|cecina gamberi|cannolo al nero|spaghetto mayo|tonno cbt|maialino|passata di ceci|polenta baccalà|polenta nero|cozze pesto"),
    ("Zuppe & Vellutate",       r"zuppetta|zuppa|crema di|vellutata|chowder|brodetto|brodo|minestra riso|passata"),
    ("Antipasti & Stuzzichini", r".*"),
]

CAT_EMOJI = {
    "Antipasti & Stuzzichini": "🫒",
    "Primi Piatti":            "🍝",
    "Secondi Piatti":          "🥩",
    "Pizza & Focaccia":        "🍕",
    "Panini & Piadine":        "🥖",
    "Tacos & Street Food":     "🌮",
    "Dolci & Dessert":         "🍮",
    "Zuppe & Vellutate":       "🍲",
}

CAT_COLORS = {
    "Antipasti & Stuzzichini": "#e8a838",
    "Primi Piatti":            "#d05a2f",
    "Secondi Piatti":          "#4a9e6b",
    "Pizza & Focaccia":        "#6b8fd1",
    "Panini & Piadine":        "#c75e8a",
    "Tacos & Street Food":     "#a06bdb",
    "Dolci & Dessert":         "#e86b6b",
    "Zuppe & Vellutate":       "#5bb8c4",
}

CAT_GRADIENTS = {
    "Antipasti & Stuzzichini": ["#8B1A1A", "#D4956A"],
    "Primi Piatti":            ["#5C1A0A", "#C4622D"],
    "Secondi Piatti":          ["#0A3D1F", "#2D8653"],
    "Pizza & Focaccia":        ["#1A1A5E", "#4A6ED4"],
    "Panini & Piadine":        ["#4A0A5E", "#A855C7"],
    "Tacos & Street Food":     ["#3D1A00", "#B05A1A"],
    "Dolci & Dessert":         ["#5E0A2E", "#D45A8A"],
    "Zuppe & Vellutate":       ["#0A2E3D", "#1A8099"],
}


def categorize(title):
    t = title.lower()
    for cat, pattern in CATEGORY_RULES:
        if re.search(pattern, t):
            return cat
    return "Antipasti & Stuzzichini"


def unsplash_query(title):
    replacements = {
        "spaghetti": "spaghetti pasta", "risotto": "risotto italian",
        "pizza": "pizza italian", "focaccia": "focaccia bread",
        "tacos": "tacos street food", "panino": "gourmet sandwich",
        "piadina": "flatbread italian", "torta": "cake italian",
        "cupcake": "cupcake frosting", "zuppa": "soup italian",
        "cozze": "mussels seafood", "gamberi": "shrimp seafood",
        "polpo": "octopus grilled", "baccalà": "salt cod fish",
        "arancina": "arancini sicilian", "gnocchi": "gnocchi potato",
        "lasagne": "lasagna baked", "ravioli": "ravioli pasta",
        "castagnaccio": "chestnut cake rustic", "polpette": "meatballs italian",
        "pollo": "chicken dish italian", "manzo": "beef steak",
    }
    q = title.lower()
    for it, en in replacements.items():
        if it in q:
            return en + " food photography"
    return " ".join(title.split()[:3]) + " italian food photography"


def parse_recipes(text):
    """
    Supporta due formati:
    1. Una riga: Titolo | note opzionali
    2. Blocco separato da ---:
       Titolo
       corpo della ricetta (ingredienti, procedimento)
       ---
    """
    recipes = []
    seen = set()
    rid = 1

    # Normalizza fine riga
    lines = text.splitlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Salta righe vuote e commenti
        if not line or line.startswith("#"):
            i += 1
            continue

        # Separatore di blocco
        if line == "---":
            i += 1
            continue

        # Controlla se le righe successive (fino a ---) formano un blocco
        # Raccogli righe del blocco
        block_lines = []
        j = i
        while j < len(lines):
            l = lines[j].strip()
            if l == "---":
                j += 1
                break
            if not l and block_lines:
                # Riga vuota dentro un blocco: potrebbe essere fine blocco se non c'è ---
                # Guarda avanti: se la prossima riga non vuota è un nuovo titolo, chiudi
                k = j + 1
                while k < len(lines) and not lines[k].strip():
                    k += 1
                # Considera la riga vuota come fine blocco
                j = k
                break
            if l and not l.startswith("#"):
                block_lines.append(l)
            j += 1

        i = j

        if not block_lines:
            continue

        # Prima riga del blocco = titolo (eventualmente con | per note inline)
        first = block_lines[0]
        if "|" in first:
            parts = first.split("|", 1)
            title = parts[0].strip()
            note  = parts[1].strip()
            body_lines = block_lines[1:]
        else:
            title = first
            note  = ""
            body_lines = block_lines[1:]

        # Se c'è body, uniscilo alla nota
        if body_lines:
            body_text = "\n".join(body_lines)
            note = (note + "\n" + body_text).strip() if note else body_text

        # Deduplica
        key = title.lower()[:40]
        if key in seen:
            continue
        seen.add(key)

        cat = categorize(title)
        recipes.append({
            "id":    rid,
            "title": title,
            "cat":   cat,
            "note":  note,
            "query": unsplash_query(title),
        })
        rid += 1

    return recipes


def build_html(recipes):
    recipes_json = json.dumps(recipes, ensure_ascii=False)
    cats_json    = json.dumps(list(dict.fromkeys(r["cat"] for r in recipes)), ensure_ascii=False)
    emoji_json   = json.dumps(CAT_EMOJI, ensure_ascii=False)
    colors_json  = json.dumps(CAT_COLORS, ensure_ascii=False)
    grads_json   = json.dumps(CAT_GRADIENTS, ensure_ascii=False)
    total        = len(recipes)
    n_cats       = len(set(r["cat"] for r in recipes))

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Le Mie Ricette</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,400&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--bg:#0f0e0c;--surface:#1a1915;--surface2:#242320;--accent:#e8a838;--text:#f0ece4;--muted:#9a948a;--border:#2e2c28;}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;min-height:100vh;overflow-x:hidden;}}
.hero{{padding:80px 40px 60px;text-align:center;background:radial-gradient(ellipse 80% 60% at 50% 0%,rgba(232,168,56,.15) 0%,transparent 70%);border-bottom:1px solid var(--border);}}
.hero-label{{font-size:11px;letter-spacing:4px;text-transform:uppercase;color:var(--accent);margin-bottom:20px;font-weight:500;}}
.hero h1{{font-family:'Playfair Display',serif;font-size:clamp(3rem,8vw,7rem);font-weight:900;line-height:.9;letter-spacing:-2px;background:linear-gradient(135deg,var(--text) 40%,var(--accent));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:24px;}}
.hero p{{color:var(--muted);font-size:1rem;max-width:500px;margin:0 auto 40px;line-height:1.7;}}
.stats{{display:flex;justify-content:center;gap:40px;flex-wrap:wrap;}}
.stat-num{{font-family:'Playfair Display',serif;font-size:2.2rem;font-weight:700;color:var(--accent);}}
.stat-label{{font-size:.75rem;color:var(--muted);letter-spacing:2px;text-transform:uppercase;}}
.search-wrap{{padding:32px 40px;max-width:700px;margin:0 auto;}}
.search-box{{display:flex;align-items:center;background:var(--surface);border:1px solid var(--border);border-radius:50px;padding:14px 24px;gap:12px;transition:border-color .2s;}}
.search-box:focus-within{{border-color:var(--accent);}}
.search-box input{{background:none;border:none;outline:none;color:var(--text);font-family:'DM Sans',sans-serif;font-size:1rem;width:100%;}}
.search-box input::placeholder{{color:var(--muted);}}
.nav-wrap{{padding:0 40px 32px;overflow-x:auto;scrollbar-width:none;}}
.nav-wrap::-webkit-scrollbar{{display:none;}}
.nav-tabs{{display:flex;gap:8px;width:max-content;}}
.tab-btn{{background:var(--surface);border:1px solid var(--border);border-radius:50px;padding:10px 20px;color:var(--muted);font-family:'DM Sans',sans-serif;font-size:.85rem;cursor:pointer;transition:all .2s;white-space:nowrap;display:flex;align-items:center;gap:8px;}}
.tab-btn:hover{{border-color:var(--accent);color:var(--text);}}
.tab-btn.active{{background:var(--accent);border-color:var(--accent);color:#0f0e0c;font-weight:600;}}
.tab-count{{background:rgba(0,0,0,.2);border-radius:20px;padding:1px 7px;font-size:.75rem;}}
.cat-section{{padding:0 40px 60px;display:none;}}
.cat-section.visible{{display:block;}}
.cat-header{{display:flex;align-items:center;gap:16px;margin-bottom:32px;padding-bottom:16px;border-bottom:1px solid var(--border);}}
.cat-emoji{{font-size:2rem;}}
.cat-title{{font-family:'Playfair Display',serif;font-size:2rem;font-weight:700;}}
.cat-count-badge{{margin-left:auto;background:var(--surface2);border:1px solid var(--border);border-radius:50px;padding:4px 14px;font-size:.8rem;color:var(--muted);}}
.recipe-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:24px;}}
.recipe-card{{background:var(--surface);border:1px solid var(--border);border-radius:20px;overflow:hidden;cursor:pointer;transition:transform .25s,border-color .25s,box-shadow .25s;}}
.recipe-card:hover{{transform:translateY(-4px);border-color:var(--accent);box-shadow:0 12px 40px rgba(0,0,0,.5);}}
.card-img-wrap{{position:relative;height:200px;overflow:hidden;}}
.card-img-wrap img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:none;transition:opacity .5s;}}
.card-overlay{{position:absolute;inset:0;background:linear-gradient(to top,rgba(15,14,12,.6) 0%,transparent 55%);}}
.card-placeholder{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:3.5rem;}}
.card-body{{padding:20px;}}
.card-cat-label{{font-size:.72rem;letter-spacing:2px;text-transform:uppercase;color:var(--muted);display:flex;align-items:center;margin-bottom:10px;}}
.card-dot{{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:8px;flex-shrink:0;}}
.card-title{{font-family:'Playfair Display',serif;font-size:1.15rem;font-weight:700;line-height:1.3;}}
.card-footer{{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;border-top:1px solid var(--border);}}
.card-arrow{{width:32px;height:32px;border-radius:50%;background:var(--surface2);display:flex;align-items:center;justify-content:center;color:var(--muted);flex-shrink:0;transition:background .2s,color .2s;}}
.recipe-card:hover .card-arrow{{background:var(--accent);color:#0f0e0c;}}
.has-note{{font-size:.75rem;color:var(--muted);}}
.modal-overlay{{position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:1000;display:flex;align-items:flex-start;justify-content:center;padding:40px 20px;overflow-y:auto;opacity:0;pointer-events:none;transition:opacity .3s;}}
.modal-overlay.open{{opacity:1;pointer-events:all;}}
.modal{{background:var(--surface);border:1px solid var(--border);border-radius:24px;width:100%;max-width:760px;overflow:hidden;transform:translateY(20px);transition:transform .3s;margin:auto;}}
.modal-overlay.open .modal{{transform:translateY(0);}}
.modal-hero{{position:relative;height:300px;overflow:hidden;background:var(--surface2);}}
.modal-hero img{{width:100%;height:100%;object-fit:cover;display:none;transition:opacity .5s;}}
.modal-hero-overlay{{position:absolute;inset:0;background:linear-gradient(to top,rgba(26,25,21,1) 0%,transparent 60%);}}
.modal-close{{position:absolute;top:20px;right:20px;width:40px;height:40px;border-radius:50%;background:rgba(0,0,0,.6);border:1px solid rgba(255,255,255,.1);color:white;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:1.2rem;transition:background .2s;}}
.modal-close:hover{{background:rgba(232,168,56,.8);}}
.modal-content{{padding:32px;}}
.modal-cat{{font-size:.72rem;letter-spacing:3px;text-transform:uppercase;color:var(--accent);margin-bottom:12px;}}
.modal-title{{font-family:'Playfair Display',serif;font-size:2rem;font-weight:900;line-height:1.1;margin-bottom:24px;}}
.modal-note{{color:var(--muted);font-size:.95rem;line-height:1.8;white-space:pre-wrap;background:var(--surface2);border-left:3px solid var(--accent);padding:20px 24px;border-radius:0 8px 8px 0;}}
.modal-empty{{color:var(--muted);font-size:.9rem;font-style:italic;opacity:.6;}}
.no-results{{text-align:center;padding:80px 40px;color:var(--muted);display:none;}}
.no-results.visible{{display:block;}}
@media(max-width:600px){{
  .hero h1{{font-size:3rem;}}
  .cat-section,.nav-wrap,.search-wrap{{padding-left:20px;padding-right:20px;}}
  .recipe-grid{{grid-template-columns:1fr;}}
}}
</style>
</head>
<body>
<header class="hero">
  <p class="hero-label">La mia cucina</p>
  <h1>Le Mie<br>Ricette</h1>
  <p>Una collezione personale in continuo aggiornamento.</p>
  <div class="stats">
    <div class="stat"><div class="stat-num">{total}</div><div class="stat-label">Ricette</div></div>
    <div class="stat"><div class="stat-num">{n_cats}</div><div class="stat-label">Categorie</div></div>
    <div class="stat"><div class="stat-num">∞</div><div class="stat-label">Gusto</div></div>
  </div>
</header>
<div class="search-wrap">
  <div class="search-box">
    <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
    <input type="text" id="searchInput" placeholder="Cerca una ricetta..." oninput="filterRecipes(this.value)">
  </div>
</div>
<div class="nav-wrap"><div class="nav-tabs" id="navTabs"></div></div>
<div id="sectionsContainer"></div>
<div class="no-results" id="noResults"><div style="font-size:3rem;margin-bottom:16px">🔍</div><p>Nessuna ricetta trovata.</p></div>
<div class="modal-overlay" id="modalOverlay" onclick="closeModal(event)">
  <div class="modal">
    <div class="modal-hero" id="modalHero">
      <div id="modalHeroPlaceholder" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:6rem;"></div>
      <img id="modalPhoto" alt="" onload="this.style.display='block';this.style.opacity=1">
      <div class="modal-hero-overlay"></div>
      <button class="modal-close" onclick="document.getElementById('modalOverlay').classList.remove('open');document.body.style.overflow=''">&times;</button>
    </div>
    <div class="modal-content">
      <div class="modal-cat" id="modalCat"></div>
      <h2 class="modal-title" id="modalTitle"></h2>
      <div id="modalBody"></div>
    </div>
  </div>
</div>
<script>
const RECIPES={recipes_json};
const CATS={cats_json};
const CAT_EMOJI={emoji_json};
const CAT_COLORS={colors_json};
const CAT_GRADS={grads_json};
const UNSPLASH_KEY="{UNSPLASH_KEY}";
const photoCache={{}};
async function fetchPhoto(rid,query){{
  if(photoCache[rid])return photoCache[rid];
  try{{
    const r=await fetch(`https://api.unsplash.com/search/photos?query=${{encodeURIComponent(query)}}&per_page=3&orientation=landscape&client_id=${{UNSPLASH_KEY}}`);
    const d=await r.json();
    if(d.results&&d.results.length){{
      const url=d.results[rid%d.results.length].urls.regular+"&w=400&h=260&fit=crop&auto=format&q=80";
      photoCache[rid]=url;return url;
    }}
  }}catch(e){{}}
  return null;
}}
const observer=new IntersectionObserver(entries=>{{
  entries.forEach(e=>{{
    if(!e.isIntersecting)return;
    const img=e.target;
    fetchPhoto(+img.dataset.rid,img.dataset.query).then(url=>{{
      if(url){{img.src=url;img.onload=()=>{{img.style.display='block';img.style.opacity=1;img.previousElementSibling.style.opacity=0;}}}}
    }});
    observer.unobserve(img);
  }});
}},{{rootMargin:'300px'}});
function buildTabs(){{
  const nav=document.getElementById('navTabs');
  const all=document.createElement('button');
  all.className='tab-btn active';
  all.innerHTML=`Tutte <span class="tab-count">${{RECIPES.length}}</span>`;
  all.onclick=()=>showCat('all',all);
  nav.appendChild(all);
  CATS.forEach(cat=>{{
    const n=RECIPES.filter(r=>r.cat===cat).length;
    const btn=document.createElement('button');
    btn.className='tab-btn';
    btn.innerHTML=`${{CAT_EMOJI[cat]}} ${{cat}} <span class="tab-count">${{n}}</span>`;
    btn.onclick=()=>showCat(cat,btn);
    nav.appendChild(btn);
  }});
}}
function buildSections(){{
  const container=document.getElementById('sectionsContainer');
  const allSec=document.createElement('div');
  allSec.className='cat-section visible';
  allSec.dataset.cat='all';
  CATS.forEach(cat=>allSec.appendChild(buildGroup(cat,RECIPES.filter(r=>r.cat===cat))));
  container.appendChild(allSec);
  CATS.forEach(cat=>{{
    const sec=document.createElement('div');
    sec.className='cat-section';
    sec.dataset.cat=cat;
    sec.appendChild(buildGroup(cat,RECIPES.filter(r=>r.cat===cat)));
    container.appendChild(sec);
  }});
}}
function buildGroup(cat,recipes){{
  const div=document.createElement('div');
  div.style.marginBottom='60px';
  div.innerHTML=`<div class="cat-header"><span class="cat-emoji">${{CAT_EMOJI[cat]}}</span><h2 class="cat-title">${{cat}}</h2><span class="cat-count-badge">${{recipes.length}} ricette</span></div>`;
  const grid=document.createElement('div');
  grid.className='recipe-grid';
  recipes.forEach(r=>grid.appendChild(buildCard(r)));
  div.appendChild(grid);
  return div;
}}
function buildCard(r){{
  const card=document.createElement('div');
  card.className='recipe-card';
  card.dataset.title=r.title.toLowerCase();
  card.dataset.cat=r.cat.toLowerCase();
  const color=CAT_COLORS[r.cat]||'#e8a838';
  const[g1,g2]=CAT_GRADS[r.cat]||['#1a1915','#3a3930'];
  const hasNote=r.note&&r.note.trim().length>0;
  card.innerHTML=`
    <div class="card-img-wrap" style="background:linear-gradient(135deg,${{g1}},${{g2}})">
      <div class="card-placeholder" style="opacity:.45">${{CAT_EMOJI[r.cat]}}</div>
      <img data-rid="${{r.id}}" data-query="${{r.query}}" alt="${{r.title}}">
      <div class="card-overlay"></div>
    </div>
    <div class="card-body">
      <div class="card-cat-label"><span class="card-dot" style="background:${{color}}"></span>${{r.cat}}</div>
      <h3 class="card-title">${{r.title}}</h3>
    </div>
    <div class="card-footer">
      <span class="has-note">${{hasNote?'📋 Ricetta completa':'Clicca per i dettagli'}}</span>
      <div class="card-arrow"><svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M5 12h14M12 5l7 7-7 7"/></svg></div>
    </div>`;
  card.onclick=()=>openModal(r);
  const img=card.querySelector('img[data-rid]');
  if(img)observer.observe(img);
  return card;
}}
function showCat(cat,btn){{
  document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.cat-section').forEach(s=>s.classList.toggle('visible',s.dataset.cat===cat));
  document.getElementById('searchInput').value='';
  document.getElementById('noResults').classList.remove('visible');
  document.querySelectorAll('.recipe-card').forEach(c=>c.style.display='');
}}
function filterRecipes(val){{
  const q=val.toLowerCase();
  let found=0;
  document.querySelectorAll('.cat-section').forEach(s=>s.classList.toggle('visible',s.dataset.cat==='all'));
  document.querySelectorAll('.tab-btn').forEach((b,i)=>b.classList.toggle('active',i===0));
  document.querySelectorAll('.recipe-card').forEach(card=>{{
    const match=!q||card.dataset.title.includes(q)||card.dataset.cat.includes(q);
    card.style.display=match?'':'none';
    if(match)found++;
  }});
  document.getElementById('noResults').classList.toggle('visible',found===0);
}}
function openModal(r){{
  const[g1,g2]=CAT_GRADS[r.cat]||['#1a1915','#3a3930'];
  document.getElementById('modalHeroPlaceholder').textContent=CAT_EMOJI[r.cat];
  document.getElementById('modalHeroPlaceholder').style.background=`linear-gradient(135deg,${{g1}},${{g2}})`;
  const mp=document.getElementById('modalPhoto');
  mp.style.display='none';mp.src='';
  fetchPhoto(r.id,r.query).then(url=>{{if(url)mp.src=url;}});
  document.getElementById('modalCat').textContent=`${{CAT_EMOJI[r.cat]}} ${{r.cat}}`;
  document.getElementById('modalTitle').textContent=r.title;
  const body=document.getElementById('modalBody');
  if(r.note&&r.note.trim()){{
    body.innerHTML=`<div class="modal-note">${{r.note.trim().replace(/</g,'&lt;').replace(/>/g,'&gt;')}}</div>`;
  }}else{{
    body.innerHTML=`<p class="modal-empty">Nessuna nota per questa ricetta.</p>`;
  }}
  document.getElementById('modalOverlay').classList.add('open');
  document.body.style.overflow='hidden';
}}
function closeModal(e){{
  if(e&&e.target!==document.getElementById('modalOverlay'))return;
  document.getElementById('modalOverlay').classList.remove('open');
  document.body.style.overflow='';
}}
document.addEventListener('keydown',e=>{{if(e.key==='Escape'){{document.getElementById('modalOverlay').classList.remove('open');document.body.style.overflow='';}}}});
buildTabs();
buildSections();
</script>
</body>
</html>"""


def main():
    if not INPUT_FILE.exists():
        print(f"ERRORE: {INPUT_FILE} non trovato", file=sys.stderr)
        sys.exit(1)
    text = INPUT_FILE.read_text(encoding="utf-8")
    recipes = parse_recipes(text)
    print(f"✓ Ricette trovate: {len(recipes)}")
    html = build_html(recipes)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"✓ index.html generato ({len(html):,} bytes)")

if __name__ == "__main__":
    main()
