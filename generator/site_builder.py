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
from jinja2 import Environment

BASE = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE / "templates"

INDUSTRY_THEMES = {
    "tradesman":  {"accent": "#c2410c", "hero_label": "Řemeslné služby"},
    "salon":      {"accent": "#be185d", "hero_label": "Salon krásy"},
    "auto":       {"accent": "#1d4ed8", "hero_label": "Autoservis"},
    "gastronomy": {"accent": "#15803d", "hero_label": "Restaurace"},
    "health":     {"accent": "#0e7490", "hero_label": "Zdraví a pohoda"},
    "sport":      {"accent": "#b45309", "hero_label": "Sport a fitness"},
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
border-bottom:1px solid #eef0f3;z-index:10;transition:box-shadow .25s}
nav.scrolled{box-shadow:0 2px 14px rgba(16,24,40,.08)}
nav .wrap{display:flex;justify-content:space-between;align-items:center;height:64px}
.logo{font-weight:700;font-size:1.05rem;text-decoration:none;color:var(--ink);transition:color .15s}
.logo:hover{color:var(--accent)}
.nav-links{display:flex;gap:28px;list-style:none}
.nav-links a{text-decoration:none;color:var(--muted);font-size:.92rem;font-weight:500;position:relative;padding:4px 0}
.nav-links a::after{content:'';position:absolute;left:0;bottom:-2px;width:0;height:2px;background:var(--accent);transition:width .25s;border-radius:2px}
.nav-links a:hover{color:var(--ink)}
.nav-links a:hover::after{width:100%}
@media(max-width:640px){.nav-links{display:none}}
.menu-btn{display:none;background:none;border:none;cursor:pointer;padding:8px}
@media(max-width:640px){.menu-btn{display:block}.nav-links.mobile{display:flex;flex-direction:column;position:absolute;top:64px;left:0;right:0;background:#fff;border-bottom:1px solid #eef0f3;padding:16px 24px;gap:14px}}
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
box-shadow:0 2px 8px rgba(16,24,40,.04);transition:transform .2s,box-shadow .2s,border-color .2s}
.card:hover{transform:translateY(-3px);box-shadow:0 8px 24px rgba(16,24,40,.09);border-color:color-mix(in srgb,var(--accent) 25%,#eef0f3)}
.card .icon{width:44px;height:44px;border-radius:11px;background:color-mix(in srgb,var(--accent) 10%,white);
display:flex;align-items:center;justify-content:center;color:var(--accent);margin-bottom:16px}
.card h3{font-size:1.06rem;margin-bottom:8px}
.card p{color:var(--muted);font-size:.95rem}
.about{background:var(--soft)}
.about p{max-width:70ch;color:#374151;font-size:1.04rem}
.stats{display:flex;flex-wrap:wrap;gap:40px;margin-top:36px}
.stat b{font-size:1.9rem;color:var(--accent);letter-spacing:-.02em;display:block}
.stat span{color:var(--muted);font-size:.9rem}
.cta-band{background:linear-gradient(135deg,var(--ink),#1f2937);color:#fff;border-radius:20px;
padding:56px 40px;display:flex;flex-wrap:wrap;gap:28px;align-items:center;justify-content:space-between}
.cta-band h2{margin:0;color:#fff}
.cta-band p{opacity:.75;margin-top:6px}
.cta-band .btn{background:#fff;color:var(--ink);box-shadow:none}
footer{border-top:1px solid #eef0f3;padding:36px 0;margin-top:24px}
footer .wrap{display:flex;flex-wrap:wrap;gap:12px;justify-content:space-between;color:var(--muted);font-size:.88rem}
/* scroll reveal */
.reveal{opacity:0;transform:translateY(18px);transition:opacity .6s ease,transform .6s ease}
.reveal.in{opacity:1;transform:none}
@media(prefers-reduced-motion:reduce){.reveal{opacity:1;transform:none;transition:none}}
</style>
</head>
<body>
<nav id="nav"><div class="wrap"><a class="logo" href="#top">{{ company }}</a>
<ul class="nav-links" id="navlinks"><li><a href="#sluzby">Služby</a></li><li><a href="#o-nas">O nás</a></li><li><a href="#kontakt">Kontakt</a></li></ul>
<button class="menu-btn" aria-label="Otevřít menu" onclick="document.getElementById('navlinks').classList.toggle('mobile')">
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M3 12h18M3 18h18"/></svg></button></div></nav>
<header id="top" class="hero"><div class="wrap">
<span class="badge">{{ hero_label }}</span>
<h1>{{ headline }}</h1><p>{{ subhead }}</p>
<a class="btn" href="tel:{{ phone }}"><svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.9 21 3 13.1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.2.2 2.4.6 3.6.1.3 0 .7-.2 1l-2.3 2.2z"/></svg> {{ cta }}</a></div></header>
<section id="sluzby"><div class="wrap">
<div class="section-label reveal">Služby</div><h2 class="reveal">Co pro vás uděláme</h2>
<div class="grid">{% for s in services %}<div class="card reveal">
<div class="icon"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg></div>
<h3>{{ s }}</h3><p>Rádi vám poradí a vše zajistíme — od posouzení po dokončení práce.</p></div>{% endfor %}</div>
</div></section>
<section id="o-nas" class="about"><div class="wrap">
<div class="section-label reveal">O nás</div><h2 class="reveal">{{ company }}</h2><p class="reveal">{{ about }}</p></div></section>
<section id="kontakt"><div class="wrap">
<div class="cta-band reveal"><div><h2>{{ cta }}</h2><p>Ozveme se vám rychle — zavolejte nebo nám napište.</p></div>
<a class="btn" href="tel:{{ phone }}">{{ phone_display }}</a></div>
</div></section>
<footer><div class="wrap"><span>&copy; {{ year }} {{ company }}</span><span>{{ city }}</span></div></footer>
<script>
// nav shadow on scroll
const nav=document.getElementById('nav');
addEventListener('scroll',()=>nav.classList.toggle('scrolled',scrollY>8),{passive:true});
// scroll reveal
if('IntersectionObserver' in window){
 const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}}),{threshold:.12});
 document.querySelectorAll('.reveal').forEach(el=>io.observe(el));
}else{document.querySelectorAll('.reveal').forEach(el=>el.classList.add('in'))}
</script>
</body></html>"""


def render_site(lead, copy: dict) -> str:
    """Render a site using one of 15 distinct design personalities."""
    from generator.design_system import get_design
    from generator.template_css import TEMPLATE_CSS
    from generator.shell import SHELL, maps_embed, BASE_CSS
    from generator.variants import HERO_PHOTOS, gallery_photos
    import random as _r

    # deterministic rng for this lead (same seed logic as design)
    import hashlib
    lseed = int(hashlib.sha256(
        f"{lead['ico']}:{lead['company_name']}".encode()).hexdigest()[:8], 16)
    lrng = _r.Random(lseed)

    d = get_design(lead)
    tpl = d["template"]
    p = d["palette"]
    seo = seo_block(lead, copy)
    import time as _t
    phone_raw = (lead["phone"] or "+420****0000").replace(" ", "")

    # hero photo for the industry
    ids = HERO_PHOTOS.get(lead["industry"])
    photo = None
    if ids:
        pid = ids[d["photo_seed"]]
        photo = f"https://images.unsplash.com/{pid}?auto=format&fit=crop&w=1600&q=70"
    gallery = gallery_photos(lead["industry"], lrng, n=3)

    # logo: first meaningful word + accent dot
    words = [w for w in re.split(r"[\s—-]+", lead["company_name"]) if len(w) > 2]
    logo_text = words[0] if words else lead["company_name"]

    # industry-specific section titles
    ind = lead["industry"]
    kickers = {
        "tradesman": ("Naše práce", "Co pro vás uděláme", "Podíváme se, poradíme a uděláme pořádně."),
        "salon": ("Služby salonu", "Jak vám pomůžeme", "U nás si odpočinete a odejdete spokojení."),
        "auto": ("Servisní služby", "Vaše auto v našich rukou", "Diagnostika, oprava i prevence — vše pod jednou střechou."),
        "gastronomy": ("Nabídka", "Co u nás ochutnáte", "Čerstvé suroviny, poctivá příprava, férové ceny."),
        "health": ("Naše péče", "Jak funguje návštěva", "Individuální přístup a dostatek času jen pro vás."),
        "sport": ("Trénink a aktivity", "Co u vás najdu", "Pro začátečníky i pokročilé — přijďte to zkusit."),
    }
    sk, st, card_text = kickers.get(ind, ("Naše služby", "Co pro vás uděláme",
                                           "Rádi vám poradí a vše zajistíme."))

    # ambient hero decorations per industry (inline SVG — emoji don't render
    # in headless browsers and show as empty boxes on screenshots)
    LEAF_SVG = ('<svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor">'
                '<path d="M17 8C8 10 5.9 16.17 3.82 21.34l1.89.66.95-2.3c.48.17.98.3 1.34.3C19 20 22 3 22 3c-1 2-8 2.25-13 3.25S2 11.5 2 13.5s1.75 3.75 1.75 3.75"/></svg>')
    GEAR_SVG = ('<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
                '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 01-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 008.6 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 8.6a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>')
    SPARKLE_SVG = ('<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">'
                   '<path d="M12 0l2.4 7.2L22 9.6l-7.6 2.4L12 19.2l-2.4-7.2L2 9.6l7.6-2.4z"/>'
                   '<path d="M19 14l1.2 3.6L24 18.8l-3.8 1.2L19 23.6l-1.2-3.6L14 18.8l3.8-1.2z" opacity=".6"/></svg>')
    HEART_SVG = ('<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">'
                 '<path d="M12 21s-8-5.5-10-10c-1.5-3.5.5-7 4-7 2.2 0 3.8 1.2 4.5 2.8L12 8l1.5-1.2C14.2 5.2 15.8 4 18 4c3.5 0 5.5 3.5 4 7-2 4.5-10 10-10 10z"/></svg>')
    BOLT_SVG = ('<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">'
                '<path d="M13 2L4 14h6l-1 8 9-12h-6l1-8z"/></svg>')
    ambient_svgs = {
        "tradesman": [LEAF_SVG, LEAF_SVG, SPARKLE_SVG, LEAF_SVG, SPARKLE_SVG],
        "salon": [SPARKLE_SVG, SPARKLE_SVG, LEAF_SVG, SPARKLE_SVG, HEART_SVG],
        "auto": [GEAR_SVG, GEAR_SVG, BOLT_SVG, GEAR_SVG, BOLT_SVG],
        "gastronomy": [LEAF_SVG, SPARKLE_SVG, LEAF_SVG, SPARKLE_SVG, LEAF_SVG],
        "health": [HEART_SVG, LEAF_SVG, HEART_SVG, SPARKLE_SVG, LEAF_SVG],
        "sport": [BOLT_SVG, BOLT_SVG, SPARKLE_SVG, BOLT_SVG, GEAR_SVG],
    }.get(ind, [SPARKLE_SVG] * 5)

    # template CSS with palette substituted
    tpl_css = TEMPLATE_CSS[tpl](p)
    # inject remaining shell vars that templates expect as --cardbg etc.
    dark_tpls = {"aurora", "monolith", "forge", "noir", "ember", "summit"}
    is_dark = tpl in dark_tpls
    extra_vars = f"""
:root{{--cardbg:{p['bg1'] if is_dark else '#ffffff'};
--cardline:{'#2a2a35' if is_dark else '#eef0f3'};
--iconbg:{'color-mix(in srgb,var(--accent) 14%,transparent)'};
--navbg:{p['bg0']}f5;--navline:{'#2a2a35' if is_dark else '#e8e8ec'};
--logo:{'#ffffff' if is_dark else p['text']};--radius:14px;
--font:{d['font_stack']};--tprop:border-color}}
"""
    tpl_css = extra_vars + tpl_css

    # hero body per template family (photo-heavy vs typographic)
    if tpl in {"pulse", "noir", "aurora", "summit"} and not photo:
        photo = None  # these work fine without photo too

    if photo:
        hero_html = (
            '<div class="wrap">'
            f'<span class="badge">{INDUSTRY_THEMES.get(ind, INDUSTRY_THEMES["other"])["hero_label"]}</span>'
            f'<h1>{copy["headline"]}</h1>'
            f'<p>{copy["subhead"]}</p>'
            f'<a class="btn" href="tel:{phone_raw}"><svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.9 21 3 13.1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.2.2 2.4.6 3.6.1.3 0 .7-.2 1l-2.3 2.2z"/></svg> {copy["cta"]}</a>'
            '</div>')
        # ensure the photo shows behind: templates style .hero background themselves
        # via {{photo}} placeholder inside their css; replace it now
        tpl_css = tpl_css.replace("{{ photo }}", photo)
    else:
        hero_html = (
            '<div class="wrap">'
            f'<span class="badge">{INDUSTRY_THEMES.get(ind, INDUSTRY_THEMES["other"])["hero_label"]}</span>'
            f'<h1>{copy["headline"]}</h1>'
            f'<p>{copy["subhead"]}</p>'
            f'<a class="btn" href="tel:{phone_raw}"><svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.9 21 3 13.1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.2.2 2.4.6 3.6.1.3 0 .7-.2 1l-2.3 2.2z"/></svg> {copy["cta"]}</a>'
            '</div>')

    html_out = Environment().from_string(SHELL).render(
        company=lead["company_name"],
        logo_text=logo_text,
        logo_dot=".",
        city=lead["city"],
        ico=lead["ico"],
        address=lead["address"],
        phone=phone_raw,
        phone_display=lead["phone"] or phone_raw,
        email=lead["email"],
        year=_t.strftime("%Y"),
        seo_block=seo,
        google_font=d["google_font"],
        base_css=BASE_CSS,
        tpl_css=tpl_css,
        hero_html=hero_html,
        services_kicker=sk,
        services_title=st,
        card_text=card_text,
        ambient_emoji="",
        ambient_svg=True,
        ambient_svgs=ambient_svgs,
        cicon='<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1z"/></svg>',
        about_kicker="O nás",
        hours="Po–Pá dle domluvy · So–Ne zavřeno",
        cta_note="Nezávazně se ozvěte — rádi vám poradíme a vypočítáme termín.",
        map_title=f"Najdete nás v {lead['city'] or 'Česku'}",
        maps_embed=maps_embed(lead["city"], lead["company_name"]),
        maps_link=f"https://mapy.cz/zakladni?q={__import__('urllib.parse', fromlist=['quote']).quote(lead['city'] or '')}",
        # rich content
        stats=[("10+", "let zkušeností"), ("100 %", "spokojenost"),
               ("24 h", "reakce na poptávku")],
        gallery=gallery,
        testimonials=[
            {"icon": '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 8C8 10 5.9 16.17 3.82 21.34l1.89.66.95-2.3c.48.17.98.3 1.34.3C19 20 22 3 22 3c-1 2-8 2.25-13 3.25S2 11.5 2 13.5s1.75 3.75 1.75 3.75"/></svg>', "text": "Osobní přístup a férová domluva — u nás nejste jen číslo."},
            {"icon": '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>', "text": "Dodržujeme dohodnuté termíny, pracujeme čistě a pořádně."},
            {"icon": '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>', "text": "Poradíme i s věcmi, na které jste se neptali — bez poplatku."},
        ],
        testi_kicker="Proč k nám",
        testi_title="Naše přednosti",
        testi_note="(Po spuštění zde budou i zkušenosti našich prvních zákazníků.)",
        **copy,
    )
    return html_out


PAGE_SHELL = """<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ company }}{% if city %} — {{ city }}{% endif %}</title>
{{ seo_block }}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family={{ google_font }}&display=swap" rel="stylesheet">
<style>
:root{--accent:{{ accent }};--dark:{{ dark }};--soft:{{ soft }};--ink:#111827;--muted:#6b7280}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
body{font-family:{{ font_stack }};color:var(--ink);line-height:1.65;font-size:16px}
.wrap{max-width:1140px;margin:0 auto;padding:0 24px;position:relative;z-index:1}
nav{position:sticky;top:0;z-index:10;backdrop-filter:blur(10px);
background:{% if nav_dark == 'true' %}rgba(15,23,42,.55){% else %}rgba(255,255,255,.9){% endif %};
border-bottom:1px solid rgba(148,163,184,.18);transition:box-shadow .25s}
nav.scrolled{box-shadow:0 2px 14px rgba(16,24,40,.1)}
{% if nav_dark == 'true' %}nav :is(a){color:#fff}{% endif %}
nav .wrap{display:flex;justify-content:space-between;align-items:center;height:64px}
.logo{font-weight:800;font-size:1.08rem;text-decoration:none;color:var(--ink);letter-spacing:-.02em}
.logo span{color:var(--accent)}
.nav-links{display:flex;gap:26px;list-style:none}
.nav-links a{text-decoration:none;color:var(--muted);font-size:.92rem;font-weight:600;position:relative;padding:4px 0}
.nav-links a::after{content:'';position:absolute;left:0;bottom:-2px;width:0;height:2px;background:var(--accent);transition:width .25s;border-radius:2px}
.nav-links a:hover{color:var(--ink)}.nav-links a:hover::after{width:100%}
@media(max-width:700px){.nav-links{display:none}.menu-btn{display:block!important}}
.menu-btn{display:none;background:none;border:none;cursor:pointer;padding:8px;color:var(--ink)}
.hero{position:relative;overflow:hidden}
.badge{display:inline-block;color:var(--accent);border:1px solid color-mix(in srgb,var(--accent) 40%,transparent);
background:color-mix(in srgb,var(--accent) 9%,white);padding:6px 15px;border-radius:99px;
font-size:.76rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;margin-bottom:22px}
h1{line-height:1.1;letter-spacing:-.025em;margin-bottom:18px}
.hero p{font-size:clamp(1.05rem,2vw,1.25rem);color:var(--muted);max-width:52ch;margin-bottom:32px}
.btn{display:inline-flex;align-items:center;gap:10px;background:var(--accent);color:#fff;
padding:15px 32px;border-radius:12px;text-decoration:none;font-weight:700;font-size:1rem;
transition:transform .18s cubic-bezier(.34,1.56,.64,1),box-shadow .18s}
.btn:hover{transform:translateY(-2px) scale(1.02);box-shadow:0 8px 22px color-mix(in srgb,var(--accent) 45%,transparent)}
.btn:focus-visible,a:focus-visible{outline:3px solid var(--accent);outline-offset:3px}
section{padding:84px 0}
.section-label{font-size:.78rem;font-weight:800;letter-spacing:.11em;text-transform:uppercase;color:var(--accent);margin-bottom:10px}
h2{font-size:clamp(1.55rem,3vw,2.1rem);letter-spacing:-.015em;margin-bottom:40px;max-width:24ch}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:22px}
.card{background:#fff;border:1px solid #eef0f3;border-radius:16px;padding:28px;
transition:transform .25s,box-shadow .25s}
.card:hover{transform:translateY(-4px)}
.card .icon{width:46px;height:46px;border-radius:12px;background:color-mix(in srgb,var(--accent) 11%,white);
display:flex;align-items:center;justify-content:center;color:var(--accent);margin-bottom:16px}
.card h3{font-size:1.07rem;margin-bottom:8px}
.card p{color:var(--muted);font-size:.94rem}
.about{background:var(--soft)}
.about p{max-width:68ch;color:#374151;font-size:1.05rem}
.cta-band{background:linear-gradient(135deg,var(--dark),#1f2937);color:#fff;border-radius:22px;
padding:58px 42px;display:flex;flex-wrap:wrap;gap:28px;align-items:center;justify-content:space-between}
.cta-band h2{margin:0;color:#fff}.cta-band p{opacity:.75;margin-top:6px}
.cta-band .btn{background:#fff;color:var(--ink);box-shadow:none}
footer{border-top:1px solid #eef0f3;padding:38px 0;margin-top:24px}
footer .wrap{display:flex;flex-wrap:wrap;gap:12px;justify-content:space-between;color:var(--muted);font-size:.88rem}
.reveal{opacity:0;transform:translateY(20px);transition:opacity .65s ease,transform .65s ease}
.reveal.in{opacity:1;transform:none}
.reveal:nth-child(2){transition-delay:.08s}.reveal:nth-child(3){transition-delay:.16s}.reveal:nth-child(4){transition-delay:.24s}
@media(prefers-reduced-motion:reduce){.reveal{opacity:1;transform:none;transition:none}}
/* layout/decor/card variants injected per-site */
{{ hero_css }}
{{ decor_css | safe }}
{{ card_css }}
</style>
</head>
<body>
<nav id="nav"><div class="wrap"><a class="logo" href="#top">{{ company.split(' ')[0] }}<span>.</span></a>
<ul class="nav-links" id="navlinks"><li><a href="#sluzby">Služby</a></li><li><a href="#o-nas">O nás</a></li><li><a href="#kontakt">Kontakt</a></li></ul>
<button class="menu-btn" aria-label="Otevřít menu" onclick="document.getElementById('navlinks').classList.toggle('mobile')">
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M3 12h18M3 18h18"/></svg></button></div></nav>
<header id="top" class="hero">
{{ hero_body | safe }}
</header>
<main>
<section id="sluzby"><div class="wrap">
<div class="section-label reveal">Služby</div><h2 class="reveal">Co pro vás uděláme</h2>
<div class="grid">{% for s in services %}<div class="card reveal">
<div class="icon"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2l3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1z"/></svg></div>
<h3>{{ s }}</h3><p>Rádi vám poradí a vše zajistíme — od posouzení po dokončení.</p></div>{% endfor %}</div>
</div></section>
<section id="o-nas" class="about"><div class="wrap">
<div class="section-label reveal">O nás</div><h2 class="reveal">{{ company }}</h2><p class="reveal">{{ about }}</p></div></section>
<section id="kontakt"><div class="wrap">
<div class="cta-band reveal"><div><h2>{{ cta }}</h2><p>Ozveme se vám rychle — zavolejte nebo napište.</p></div>
<a class="btn" href="tel:{{ phone }}">{{ phone_display }}</a></div>
</div></section>
</main>
<footer><div class="wrap"><span>&copy; {{ year }} {{ company }}</span><span>{{ city }}</span></div></footer>
<script>
const nav=document.getElementById('nav');
addEventListener('scroll',()=>nav.classList.toggle('scrolled',scrollY>8),{passive:true});
if('IntersectionObserver' in window){
 const io=new IntersectionObserver(es=>es.forEach((e,i)=>{if(e.isIntersecting){setTimeout(()=>e.target.classList.add('in'),i*60);io.unobserve(e.target)}}),{threshold:.12});
 document.querySelectorAll('.reveal').forEach(el=>io.observe(el));
}else{document.querySelectorAll('.reveal').forEach(el=>el.classList.add('in'))}
</script>
</body></html>"""


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
