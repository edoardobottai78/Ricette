#!/usr/bin/env python3
import json, re, sys
from pathlib import Path

INPUT_FILE  = Path("ricette.txt")
OUTPUT_FILE = Path("index.html")
RICETTE_DIR = Path("ricette")  # cartella con i file .txt delle ricette

CATEGORY_RULES = [
    ("Dolci & Dessert",         r"torta|dolce|cupcake|biscotto|castagnaccio|sablÃÂ©|sable|zuppetta di fragole|panna cotta|financier|cremoso|mousse|crumble|crostata|frolla|sorbetto|pan di spagna|bavarese|chantilly|zabaione dolce|bicchiere composta|bicchiere di frutti"),
    ("Pizza & Focaccia",        r"pizza|focaccia|schiacciata"),
    ("Tacos & Street Food",     r"tacos|taco|nachos|cono|coni|tramezzini"),
    ("Panini & Piadine",        r"panino|piadina|bun |burger|tartina"),
    ("Primi Piatti",            r"pasta|spaghetti|spaghetto|tagliatelle|pappardelle|rigatoni|paccheri|mezze maniche|tonnarelli|risotto|gnocchi|lasagne|ravioli|tortelli|cappellacci|passatelli|cous cous|riso |minestra|zuppa di|gnocco"),
    ("Secondi Piatti",          r"filetto|polpo|polpette|cozze fritte|cavolo cappuccio|bocconcini di pollo|jarret|fegatini|arancina|arancine|cecina gamberi|cannolo al nero|spaghetto mayo|tonno cbt|maialino|passata di ceci|polenta|cozze pesto|cavolo cappuccio viola"),
    ("Zuppe & Vellutate",       r"zuppetta|zuppa|crema di|vellutata|chowder|brodetto|brodo|minestra riso|passata"),
    ("Antipasti & Stuzzichini", r".*"),
]

CAT_META = {
    "Antipasti & Stuzzichini": {"emoji": "Ã°ÂÂ«Â", "color": "#C4853A", "svg": '<circle cx="32" cy="32" r="12" fill="none" stroke="currentColor" stroke-width="2.5"/><ellipse cx="32" cy="32" rx="6" ry="18" fill="none" stroke="currentColor" stroke-width="2"/><line x1="32" y1="14" x2="38" y2="8" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>'},
    "Primi Piatti":            {"emoji": "Ã°ÂÂÂ", "color": "#C4622D", "svg": '<path d="M16 36 Q24 20 32 36 Q40 20 48 36" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/><path d="M18 30 Q26 16 32 30 Q38 16 46 30" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/><ellipse cx="32" cy="40" rx="16" ry="5" fill="none" stroke="currentColor" stroke-width="2"/>'},
    "Secondi Piatti":          {"emoji": "Ã°ÂÂ¥Â©", "color": "#2D8653", "svg": '<path d="M20 38 Q20 24 32 22 Q44 24 44 38 Q44 46 32 46 Q20 46 20 38Z" fill="none" stroke="currentColor" stroke-width="2.5"/><path d="M26 22 Q24 14 28 12" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/><path d="M36 22 Q40 14 38 10" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>'},
    "Pizza & Focaccia":        {"emoji": "Ã°ÂÂÂ", "color": "#4A6ED4", "svg": '<path d="M32 16 L50 46 L14 46 Z" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linejoin="round"/><circle cx="28" cy="36" r="3" fill="currentColor" opacity=".5"/><circle cx="36" cy="30" r="2.5" fill="currentColor" opacity=".5"/><circle cx="32" cy="40" r="2" fill="currentColor" opacity=".5"/>'},
    "Panini & Piadine":        {"emoji": "Ã°ÂÂ¥Â", "color": "#A855C7", "svg": '<path d="M16 36 Q16 26 32 24 Q48 26 48 36 Q48 40 32 42 Q16 40 16 36Z" fill="none" stroke="currentColor" stroke-width="2.5"/><line x1="22" y1="33" x2="42" y2="33" stroke="currentColor" stroke-width="1.5" opacity=".5"/><path d="M20 30 Q32 26 44 30" stroke="currentColor" stroke-width="1.5" opacity=".4" fill="none"/>'},
    "Tacos & Street Food":     {"emoji": "Ã°ÂÂÂ®", "color": "#B05A1A", "svg": '<path d="M16 40 Q16 24 32 20 Q48 24 48 40" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/><line x1="16" y1="40" x2="48" y2="40" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/><circle cx="26" cy="34" r="2.5" fill="currentColor" opacity=".5"/><circle cx="36" cy="31" r="2" fill="currentColor" opacity=".5"/>'},
    "Dolci & Dessert":         {"emoji": "Ã°ÂÂÂ®", "color": "#D45A8A", "svg": '<path d="M22 42 L24 28 Q32 20 40 28 L42 42 Z" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linejoin="round"/><ellipse cx="32" cy="42" rx="10" ry="4" fill="none" stroke="currentColor" stroke-width="2"/><path d="M32 20 Q34 14 32 10" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" fill="none"/>'},
    "Zuppe & Vellutate":       {"emoji": "Ã°ÂÂÂ²", "color": "#1A8099", "svg": '<path d="M18 34 Q18 46 32 46 Q46 46 46 34 L44 28 L20 28 Z" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linejoin="round"/><line x1="14" y1="28" x2="50" y2="28" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/><path d="M26 24 Q26 18 28 16" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"/><path d="M36 24 Q36 18 38 16" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"/>'},
}

def title_to_filename(title):
    """Converti titolo in nome file, max 80 caratteri"""
    t = title.lower()
    t = re.sub(r'[Ã Ã¡Ã¢Ã£]', 'a', t)
    t = re.sub(r'[Ã¨Ã©ÃªÃ«]', 'e', t)
    t = re.sub(r'[Ã¬Ã­Ã®Ã¯]', 'i', t)
    t = re.sub(r'[Ã²Ã³Ã´Ãµ]', 'o', t)
    t = re.sub(r'[Ã¹ÃºÃ»Ã¼]', 'u', t)
    t = re.sub(r'[^a-z0-9\s-]', '', t)
    t = re.sub(r'\s+', '-', t.strip())
    # Limita a 80 caratteri (+ ".txt" = 84 totali, ben sotto il limite di 255)
    t = t[:80] if len(t) > 80 else t
    return t + '.txt'

def parse_recipe_file(content):
    """Legge un file ricetta e restituisce {ingredienti: [...], procedimento: str}"""
    ingredienti = []
    procedimento_lines = []
    section = None
    for line in content.splitlines():
        line = line.strip()
        if not line:
            if section == 'procedimento':
                procedimento_lines.append('')
            continue
        if line.upper() in ('INGREDIENTI', 'INGREDIENTI:'):
            section = 'ingredienti'
            continue
        if line.upper() in ('PROCEDIMENTO', 'PROCEDIMENTO:', 'PREPARAZIONE', 'PREPARAZIONE:'):
            section = 'procedimento'
            continue
        if section == 'ingredienti':
            ingredienti.append(line.lstrip('- '))
        elif section == 'procedimento':
            procedimento_lines.append(line)
    return {
        'ingredienti': ingredienti,
        'procedimento': '\n'.join(procedimento_lines).strip()
    }

def title_to_filename(title):
    """Converti titolo in nome file, max 80 caratteri"""
    t = title.lower()
    t = re.sub(r'[àáâã]', 'a', t)
    t = re.sub(r'[èéêë]', 'e', t)
    t = re.sub(r'[ìíîï]', 'i', t)
    t = re.sub(r'[òóôõ]', 'o', t)
    t = re.sub(r'[ùúûü]', 'u', t)
    t = re.sub(r'[^a-z0-9\s-]', '', t)
    t = re.sub(r'\s+', '-', t.strip())
    t = t[:80] if len(t) > 80 else t
    return t + '.txt'

30
(title):
    t = title.lower()
    for cat, pattern in CATEGORY_RULES:
        if re.search(pattern, t):
            return cat
    return "Antipasti & Stuzzichini"

def parse_recipes(text):
    recipes = []
    seen = set()
    rid = 1
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "|" in line:
            parts = line.split("|", 1)
            title = parts[0].strip()
            note  = parts[1].strip()
        else:
            title = line
            note  = ""
        key = title.lower()[:40]
        if key in seen:
            continue
        seen.add(key)
        cat = categorize(title)
        # Prova a caricare il file ricetta se esiste
        fname = title_to_filename(title)
        fpath = RICETTE_DIR / fname
        ingredienti = []
        procedimento = ""
        if fpath.exists():
            data = parse_recipe_file(fpath.read_text(encoding="utf-8"))
            ingredienti = data['ingredienti']
            procedimento = data['procedimento']
        recipes.append({
            "id": rid,
            "title": title,
            "cat": cat,
            "note": note,
            "ingredienti": ingredienti,
            "procedimento": procedimento,
            "filename": fname,
        })
        rid += 1
    return recipes

def build_html(recipes):
    recipes_json = json.dumps(recipes, ensure_ascii=False)
    cats_ordered = list(dict.fromkeys(r["cat"] for r in recipes))
    cats_json    = json.dumps(cats_ordered, ensure_ascii=False)
    meta_json    = json.dumps(CAT_META, ensure_ascii=False)
    total        = len(recipes)
    con_ricetta  = sum(1 for r in recipes if r['ingredienti'] or r['procedimento'])

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Le Mie Ricette</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Mono:wght@300;400&display=swap" rel="stylesheet">
<style>
:root{{
  --bg:#F7F4EF;--ink:#1C1A17;--muted:#9A948A;--border:#DDD8D0;--accent:#C4853A;--surface:#EFEBE4;
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
html{{scroll-behavior:smooth;}}
body{{background:var(--bg);color:var(--ink);font-family:'Cormorant Garamond',Georgia,serif;min-height:100vh;overflow-x:hidden;}}
.site-header{{padding:64px 48px 48px;border-bottom:1px solid var(--border);display:flex;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;gap:24px;}}
.header-left h1{{font-size:clamp(3rem,7vw,6rem);font-weight:300;line-height:.9;letter-spacing:-2px;}}
.header-left h1 em{{font-style:italic;color:var(--accent);}}
.header-meta{{font-family:'DM Mono',monospace;font-size:11px;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-top:16px;}}
.header-right{{text-align:right;}}
.total-count{{font-size:5rem;font-weight:300;color:var(--border);line-height:1;letter-spacing:-3px;}}
.total-label{{font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);letter-spacing:3px;text-transform:uppercase;}}
.search-wrap{{padding:24px 48px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:16px;}}
.search-wrap input{{background:none;border:none;outline:none;font-family:'Cormorant Garamond',serif;font-size:1.2rem;color:var(--ink);width:100%;font-style:italic;}}
.search-wrap input::placeholder{{color:var(--muted);}}
.search-icon{{color:var(--muted);flex-shrink:0;}}
.cat-nav{{display:flex;overflow-x:auto;scrollbar-width:none;border-bottom:1px solid var(--border);padding:0 48px;}}
.cat-nav::-webkit-scrollbar{{display:none;}}
.cat-tab{{background:none;border:none;border-bottom:2px solid transparent;padding:16px 0;margin-right:32px;font-family:'DM Mono',monospace;font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);cursor:pointer;white-space:nowrap;transition:color .2s,border-color .2s;flex-shrink:0;}}
.cat-tab:hover{{color:var(--ink);}}
.cat-tab.active{{color:var(--ink);border-bottom-color:var(--accent);}}
.main{{padding:0 48px 80px;}}
.cat-block{{display:none;}}
.cat-block.visible{{display:block;}}
.cat-heading{{display:flex;align-items:center;gap:20px;padding:48px 0 24px;border-bottom:1px solid var(--border);}}
.cat-icon{{width:48px;height:48px;flex-shrink:0;}}
.cat-name{{font-size:2.4rem;font-weight:300;letter-spacing:-1px;}}
.cat-n{{margin-left:auto;font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);letter-spacing:2px;}}
.recipe-list{{list-style:none;}}
.recipe-row{{display:flex;align-items:center;padding:18px 0;border-bottom:1px solid var(--border);cursor:pointer;transition:background .15s;position:relative;}}
.recipe-row:hover{{background:var(--surface);margin:0 -48px;padding:18px 48px;}}
.recipe-num{{font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);width:36px;flex-shrink:0;}}
.recipe-name{{font-size:1.35rem;font-weight:400;flex:1;line-height:1.3;}}
.recipe-has-content{{font-family:'DM Mono',monospace;font-size:9px;color:var(--accent);letter-spacing:1px;margin-left:12px;flex-shrink:0;}}
.recipe-arrow{{color:var(--muted);margin-left:12px;flex-shrink:0;transition:transform .2s,color .2s;}}
.recipe-row:hover .recipe-arrow{{transform:translateX(4px);color:var(--accent);}}
/* MODAL */
.modal-overlay{{position:fixed;inset:0;background:rgba(28,26,23,.7);backdrop-filter:blur(4px);z-index:100;display:flex;align-items:center;justify-content:center;padding:24px;opacity:0;pointer-events:none;transition:opacity .25s;}}
.modal-overlay.open{{opacity:1;pointer-events:all;}}
.modal{{background:var(--bg);border:1px solid var(--border);border-radius:4px;width:100%;max-width:640px;max-height:88vh;overflow-y:auto;transform:translateY(16px);transition:transform .25s;}}
.modal-overlay.open .modal{{transform:translateY(0);}}
.modal-header{{padding:40px 40px 0;display:flex;align-items:flex-start;justify-content:space-between;gap:16px;}}
.modal-icon{{width:56px;height:56px;flex-shrink:0;opacity:.6;}}
.modal-close{{background:none;border:none;font-size:1.5rem;color:var(--muted);cursor:pointer;line-height:1;transition:color .2s;padding:4px;}}
.modal-close:hover{{color:var(--ink);}}
.modal-body{{padding:24px 40px 40px;}}
.modal-cat{{font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:12px;}}
.modal-title{{font-size:2.2rem;font-weight:300;line-height:1.1;letter-spacing:-1px;margin-bottom:28px;}}
.modal-divider{{border:none;border-top:1px solid var(--border);margin:0 0 28px;}}
/* INGREDIENTI */
.section-label{{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:14px;}}
.ingredienti-list{{list-style:none;margin-bottom:32px;}}
.ingredienti-list li{{padding:10px 0;border-bottom:1px solid var(--border);font-size:1.05rem;display:flex;align-items:baseline;gap:10px;}}
.ingredienti-list li::before{{content:'Ã¢ÂÂ';color:var(--accent);font-size:.9rem;flex-shrink:0;}}
/* PROCEDIMENTO */
.procedimento-text{{font-size:1.05rem;line-height:1.9;color:#4A4540;white-space:pre-wrap;font-style:italic;}}
.modal-empty{{font-size:1rem;color:var(--muted);font-style:italic;}}
.no-results{{display:none;padding:80px 0;text-align:center;color:var(--muted);font-style:italic;font-size:1.3rem;}}
.no-results.visible{{display:block;}}
@media(max-width:600px){{
  .site-header,.search-wrap,.cat-nav,.main{{padding-left:24px;padding-right:24px;}}
  .recipe-row:hover{{margin:0 -24px;padding:18px 24px;}}
  .modal-header,.modal-body{{padding-left:24px;padding-right:24px;}}
  .site-header{{padding-top:40px;flex-direction:column;align-items:flex-start;}}
  .header-right{{text-align:left;}}
}}
</style>
</head>
<body>
<header class="site-header">
  <div class="header-left">
    <h1>Le Mie<br><em>Ricette</em></h1>
    <p class="header-meta">Collezione personale &nbsp;ÃÂ·&nbsp; Sempre aggiornata</p>
  </div>
  <div class="header-right">
    <div class="total-count">{total}</div>
    <div class="total-label">ricette</div>
  </div>
</header>
<div class="search-wrap">
  <svg class="search-icon" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
  <input type="text" id="searchInput" placeholder="Cerca una ricettaÃ¢ÂÂ¦" oninput="filterRecipes(this.value)">
</div>
<nav class="cat-nav" id="catNav"></nav>
<main class="main" id="main"></main>
<div class="no-results" id="noResults">Nessuna ricetta trovata.</div>
<div class="modal-overlay" id="modalOverlay" onclick="closeModal(event)">
  <div class="modal">
    <div class="modal-header">
      <svg class="modal-icon" id="modalIcon" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg"></svg>
      <button class="modal-close" onclick="closeModalDirect()">&times;</button>
    </div>
    <div class="modal-body">
      <div class="modal-cat" id="modalCat"></div>
      <h2 class="modal-title" id="modalTitle"></h2>
      <hr class="modal-divider">
      <div id="modalContent"></div>
    </div>
  </div>
</div>
<script>
const RECIPES={recipes_json};
const CATS={cats_json};
const META={meta_json};
function buildNav(){{
  const nav=document.getElementById('catNav');
  const allBtn=document.createElement('button');
  allBtn.className='cat-tab active';
  allBtn.textContent='Tutte';
  allBtn.onclick=()=>showCat('all',allBtn);
  nav.appendChild(allBtn);
  CATS.forEach(cat=>{{
    const btn=document.createElement('button');
    btn.className='cat-tab';
    btn.textContent=cat;
    btn.onclick=()=>showCat(cat,btn);
    nav.appendChild(btn);
  }});
}}
function buildSections(){{
  const main=document.getElementById('main');
  const allSec=document.createElement('div');
  allSec.className='cat-block visible';
  allSec.dataset.cat='all';
  CATS.forEach(cat=>{{
    const recipes=RECIPES.filter(r=>r.cat===cat);
    if(recipes.length)allSec.appendChild(buildCatBlock(cat,recipes));
  }});
  main.appendChild(allSec);
  CATS.forEach(cat=>{{
    const recipes=RECIPES.filter(r=>r.cat===cat);
    if(!recipes.length)return;
    const sec=document.createElement('div');
    sec.className='cat-block';
    sec.dataset.cat=cat;
    sec.appendChild(buildCatBlock(cat,recipes));
    main.appendChild(sec);
  }});
}}
function buildCatBlock(cat,recipes){{
  const m=META[cat];
  const wrap=document.createElement('div');
  wrap.innerHTML=`<div class="cat-heading">
    <svg class="cat-icon" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" style="color:${{m.color}}">${{m.svg}}</svg>
    <span class="cat-name">${{cat}}</span>
    <span class="cat-n">${{recipes.length}} ricette</span>
  </div>`;
  const ul=document.createElement('ul');
  ul.className='recipe-list';
  recipes.forEach((r,i)=>{{
    const li=document.createElement('li');
    li.className='recipe-row';
    li.dataset.title=r.title.toLowerCase();
    li.dataset.cat=r.cat.toLowerCase();
    const hasContent=r.ingredienti.length>0||r.procedimento;
    li.innerHTML=`
      <span class="recipe-num">${{String(i+1).padStart(2,'0')}}</span>
      <span class="recipe-name">${{r.title}}</span>
      ${{hasContent?'<span class="recipe-has-content">Ã¢ÂÂ RICETTA COMPLETA</span>':''}}
      <svg class="recipe-arrow" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M5 12h14M12 5l7 7-7 7"/></svg>`;
    li.onclick=()=>openModal(r);
    ul.appendChild(li);
  }});
  wrap.appendChild(ul);
  return wrap;
}}
function showCat(cat,btn){{
  document.querySelectorAll('.cat-tab').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.cat-block').forEach(s=>s.classList.toggle('visible',s.dataset.cat===cat));
  document.getElementById('searchInput').value='';
  document.querySelectorAll('.recipe-row').forEach(r=>r.style.display='');
  document.getElementById('noResults').classList.remove('visible');
}}
function filterRecipes(val){{
  const q=val.toLowerCase();
  let found=0;
  document.querySelectorAll('.cat-block').forEach(s=>s.classList.toggle('visible',s.dataset.cat==='all'));
  document.querySelectorAll('.cat-tab').forEach((b,i)=>b.classList.toggle('active',i===0));
  document.querySelectorAll('.recipe-row').forEach(row=>{{
    const match=!q||row.dataset.title.includes(q)||row.dataset.cat.includes(q);
    row.style.display=match?'':'none';
    if(match)found++;
  }});
  document.getElementById('noResults').classList.toggle('visible',found===0);
}}
function openModal(r){{
  const m=META[r.cat];
  document.getElementById('modalIcon').innerHTML=m.svg;
  document.getElementById('modalIcon').style.color=m.color;
  document.getElementById('modalCat').textContent=r.cat.toUpperCase();
  document.getElementById('modalTitle').textContent=r.title;
  const el=document.getElementById('modalContent');
  const hasIng=r.ingredienti&&r.ingredienti.length>0;
  const hasProc=r.procedimento&&r.procedimento.trim();
  const hasNote=r.note&&r.note.trim();
  if(!hasIng&&!hasProc&&!hasNote){{
    el.innerHTML=`<p class="modal-empty">Nessuna ricetta aggiunta.</p>`;
  }} else {{
    let html='';
    if(hasIng){{
      html+=`<p class="section-label">Ingredienti</p><ul class="ingredienti-list">`;
      r.ingredienti.forEach(i=>{{html+=`<li>${{i.replace(/</g,'&lt;').replace(/>/g,'&gt;')}}</li>`;}});
      html+=`</ul>`;
    }}
    if(hasProc){{
      html+=`<p class="section-label">Procedimento</p>`;
      html+=`<p class="procedimento-text">${{r.procedimento.trim().replace(/</g,'&lt;').replace(/>/g,'&gt;')}}</p>`;
    }}
    if(hasNote&&!hasIng&&!hasProc){{
      html+=`<p class="procedimento-text">${{r.note.trim().replace(/</g,'&lt;').replace(/>/g,'&gt;')}}</p>`;
    }}
    el.innerHTML=html;
  }}
  document.getElementById('modalOverlay').classList.add('open');
  document.body.style.overflow='hidden';
}}
function closeModal(e){{
  if(e&&e.target!==document.getElementById('modalOverlay'))return;
  closeModalDirect();
}}
function closeModalDirect(){{
  document.getElementById('modalOverlay').classList.remove('open');
  document.body.style.overflow='';
}}
document.addEventListener('keydown',e=>{{if(e.key==='Escape')closeModalDirect();}});
buildNav();
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
    con_ricetta = sum(1 for r in recipes if r['ingredienti'] or r['procedimento'])
    print(f"Ã¢ÂÂ Ricette trovate: {len(recipes)} (con ricetta completa: {con_ricetta})")
    html = build_html(recipes)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"Ã¢ÂÂ index.html generato ({len(html):,} bytes)")

if __name__ == "__main__":
    main()
