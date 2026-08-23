"""Stage 5: Site generator agent — builds a single-page website from lead data.

Two copy modes:
  - llm:    Czech copy generated per-lead via LLM (best quality)
  - static: deterministic template copy from business_scope keywords (fallback,
            zero cost, works offline)

Design system: one shared Jinja2 base layout, industry-specific color/hero
variants. Output: fully self-contained HTML (inline CSS, no build step) so
deployment is a single file upload.
"""

import json
import re
import unicodedata
from pathlib import Path

from core.db import connect, leads_in_stage, advance
from core.config import llm_chat

BASE = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE / "templates"

INDUSTRY_THEMES = {
    "tradesman":  {"accent": "#c2410c", "hero_label": "Řemeslné služby"},
    "salon":      {"accent": "#be185d", "hero_label": "Salon krásy"},
    "auto":       {"accent": "#1d4ed8", "hero_label": "Autoservis"},
    "gastronomy": {"accent": "#15803d", "hero_label": "Restaurace"},
    "other":      {"accent": "#334155", "hero_label": "Naše služby"},
}


def slugify(name: str) -> str:
    text = unicodedata.normalize("NFKD", name.lower())
    text = text.encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:40]


def extract_services(scope_text: str, max_n: int = 4) -> list[str]:
    """Split RZP trade descriptions into presentable service bullets."""
    parts = [p.strip() for p in scope_text.split(";") if p.strip()]
    cleaned = []
    for p in parts[:max_n]:
        p = p[0].upper() + p[1:] if p else p
        cleaned.append(p)
    return cleaned or ["Kompletní nabídka služeb na klíč"]


def static_copy(lead) -> dict:
    services = extract_services(lead["business_scope"])
    city = lead["city"] or "vašem okolí"
    return {
        "headline": f"{lead['company_name']} — spolehlivě a profesionálně",
        "subhead": f"Jsou tu pro vás v {city}. Kontaktujte nás ještě dnes.",
        "services": services,
        "cta": "Zavolejte nám",
        "about": (
            f"{lead['company_name']} je prověřovaná firma s oprávněním pro: "
            + "; ".join(s.lower() for s in services)
            + ". Pracujeme pořádně, férově a za dohodnutou cenu."
        ),
    }


def llm_copy(lead) -> dict:
    prompt = f"""Napiš obsah jednoduchého webu pro českou firmu. Obchodní jméno:
{lead['company_name']}. Předmět podnikání: {lead['business_scope']}. Město: {lead['city']}.

Vrať POUZE validní JSON (bez markdown) ve tvaru:
{{"headline": "...", "subhead": "...", "services": ["...", "..."], "cta": "...", "about": "2-3 věty"}}
Česky, přirozeně, žádné výmysly o cenách ani referencích."""
    raw = llm_chat([{"role": "user", "content": prompt}], temperature=0.6)
    raw = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    data = json.loads(raw)
    # guard against empty fields from LLM
    fallback = static_copy(lead)
    for k, v in fallback.items():
        if not data.get(k):
            data[k] = v
    return data


def seo_block(lead, copy: dict) -> str:
    """LocalBusiness JSON-LD + meta tags — the deterministic 80% of local SEO."""
    import json as _json
    schema = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": lead["company_name"],
        "description": copy.get("about", "")[:300],
        "address": {"@type": "PostalAddress",
                    "streetAddress": lead["address"],
                    "addressLocality": lead["city"],
                    "addressCountry": "CZ"},
        "telephone": lead["phone"] or None,
        "email": lead["email"] or None,
        "areaServed": lead["city"] or "CZ",
        "knowsAbout": [s.strip() for s in lead["business_scope"].split(";") if s.strip()],
    }
    schema = {k: v for k, v in schema.items() if v}
    meta_desc = copy.get("subhead", "")[:160]
    return (
        f'<meta name="description" content="{meta_desc}">\n'
        f'<meta name="geo.placename" content="{lead["city"]}">\n'
        '<meta property="og:type" content="website">\n'
        f'<meta property="og:title" content="{copy.get("headline", lead["company_name"])}">\n'
        f'<meta property="og:description" content="{meta_desc}">\n'
        f'<script type="application/ld+json">{_json.dumps(schema, ensure_ascii=False)}</script>'
    )


BASE_TEMPLATE = """<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ company }}{% if city %} — {{ hero_label }}, {{ city }}{% endif %}</title>
{{ seo_block }}
<style>
:root{--accent:{{ accent }};--ink:#111827;--muted:#6b7280;--bg:#fff;--soft:#f5f7fa}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
body{font-family:Inter,system-ui,-apple-system,'Segoe UI',sans-serif;color:var(--ink);line-height:1.65;font-size:16px}
.wrap{max-width:1100px;margin:0 auto;padding:0 24px}
nav{position:sticky;top:0;background:rgba(255,255,255,.92);backdrop-filter:blur(8px);
border-bottom:1px solid #eef0f3;z-index:10}
nav .wrap{display:flex;justify-content:space-between;align-items:center;height:64px}
.logo{font-weight:700;font-size:1.05rem;text-decoration:none;color:var(--ink)}
.nav-links{display:flex;gap:28px;list-style:none}
.nav-links a{text-decoration:none;color:var(--muted);font-size:.92rem;font-weight:500}
.nav-links a:hover{color:var(--ink)}
@media(max-width:640px){.nav-links{display:none}}
.hero{padding:104px 0 88px;background:
radial-gradient(1200px 400px at 70% -10%,color-mix(in srgb,var(--accent) 14%,transparent),transparent),var(--soft)}
.hero .badge{display:inline-block;color:var(--accent);border:1px solid color-mix(in srgb,var(--accent) 35%,transparent);
background:color-mix(in srgb,var(--accent) 8%,white);padding:6px 14px;border-radius:99px;
font-size:.78rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin-bottom:22px}
.hero h1{font-size:clamp(2rem,5vw,3.3rem);line-height:1.12;letter-spacing:-.02em;max-width:21ch;margin-bottom:18px}
.hero p{font-size:clamp(1.05rem,2vw,1.25rem);color:var(--muted);max-width:52ch;margin-bottom:32px}
.btn{display:inline-flex;align-items:center;gap:10px;background:var(--accent);color:#fff;
padding:15px 30px;border-radius:11px;text-decoration:none;font-weight:600;font-size:1rem;
box-shadow:0 2px 10px color-mix(in srgb,var(--accent) 40%,transparent);transition:transform .15s,box-shadow .15s}
.btn:hover{transform:translateY(-1px);box-shadow:0 4px 16px color-mix(in srgb,var(--accent) 50%,transparent)}
.btn:focus-visible,a:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
section{padding:72px 0}
.section-label{font-size:.8rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
color:var(--accent);margin-bottom:10px}
h2{font-size:clamp(1.5rem,3vw,2rem);letter-spacing:-.01em;margin-bottom:36px;max-width:24ch}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px}
.card{background:#fff;border:1px solid #eef0f3;border-radius:14px;padding:26px;
box-shadow:0 2px 8px rgba(16,24,40,.04)}
.card h3{font-size:1.06rem;margin-bottom:8px}
.card p{color:var(--muted);font-size:.95rem}
.about{background:var(--soft)}
.about p{max-width:70ch;color:#374151;font-size:1.04rem}
.cta-band{background:linear-gradient(135deg,var(--ink),#1f2937);color:#fff;border-radius:20px;
padding:56px 40px;display:flex;flex-wrap:wrap;gap:28px;align-items:center;justify-content:space-between}
.cta-band h2{margin:0;color:#fff}
.cta-band p{opacity:.75;margin-top:6px}
.cta-band .btn{background:#fff;color:var(--ink);box-shadow:none}
footer{border-top:1px solid #eef0f3;padding:36px 0;margin-top:24px}
footer .wrap{display:flex;flex-wrap:wrap;gap:12px;justify-content:space-between;color:var(--muted);font-size:.88rem}
</style>
</head>
<body>
<nav><div class="wrap"><a class="logo" href="#top">{{ company }}</a>
<ul class="nav-links"><li><a href="#sluzby">Služby</a></li><li><a href="#o-nas">O nás</a></li><li><a href="#kontakt">Kontakt</a></li></ul></div></nav>
<header id="top" class="hero"><div class="wrap">
<span class="badge">{{ hero_label }}</span>
<h1>{{ headline }}</h1><p>{{ subhead }}</p>
<a class="btn" href="tel:{{ phone }}">📞 {{ cta }}</a></div></header>
<section id="sluzby"><div class="wrap">
<div class="section-label">Služby</div><h2>Co pro vás uděláme</h2>
<div class="grid">{% for s in services %}<div class="card"><h3>{{ s }}</h3><p>Rádi vám poradí a vše zajistíme — od posouzení po dokončení práce.</p></div>{% endfor %}</div>
</div></section>
<section id="o-nas" class="about"><div class="wrap">
<div class="section-label">O nás</div><h2>{{ company }}</h2><p>{{ about }}</p></div></section>
<section id="kontakt"><div class="wrap">
<div class="cta-band"><div><h2>{{ cta }}</h2><p>Ozveme se vám rychle — zavolejte nebo nám napište.</p></div>
<a class="btn" href="tel:{{ phone }}">{{ phone_display }}</a></div>
</div></section>
<footer><div class="wrap"><span>&copy; {{ year }} {{ company }}</span><span>{{ city }}</span></div></footer>
</body></html>"""


def render_site(lead, copy: dict) -> str:
    theme = INDUSTRY_THEMES.get(lead["industry"], INDUSTRY_THEMES["other"])
    from jinja2 import Environment
    seo = seo_block(lead, copy)
    import time as _t
    phone_raw = (lead["phone"] or "+420000000000").replace(" ", "")
    html_out = Environment().from_string(BASE_TEMPLATE).render(
        company=lead["company_name"],
        city=lead["city"],
        phone=phone_raw,
        phone_display=lead["phone"] or phone_raw,
        year=_t.strftime("%Y"),
        accent=theme["accent"],
        hero_label=theme["hero_label"],
        seo_block=seo,
        **copy,
    )
    return html_out


def run(use_llm: bool = False) -> dict:
    conn = connect()
    built = []
    for lead in leads_in_stage(conn, "ENRICHED"):
        try:
            copy = llm_copy(lead) if use_llm else static_copy(lead)
            html = render_site(lead, copy)
            out_dir = BASE / "generated" / slugify(lead["company_name"])
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "index.html").write_text(html, encoding="utf-8")
            conn.execute("UPDATE leads SET demo_url=? WHERE id=?",
                         (f"https://demo.example.cz/{out_dir.name}", lead["id"]))
            advance(conn, lead["id"], "GENERATED", f"site at {out_dir.name}")
            built.append(out_dir.name)
        except Exception as e:
            advance(conn, lead["id"], "ENRICHED", f"generation failed: {e}")
    conn.commit()
    return {"built": built}


if __name__ == "__main__":
    import sys
    print(run(use_llm="--llm" in sys.argv))
