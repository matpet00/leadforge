"""Design Vision Agent — mockup-driven site building with model fallback.

Pipeline:
1. CONCEPT: ask an image-generation model (fallback chain over available
   OpenRouter image models) to render a full-page web-design MOCKUP for a
   given business/industry.
2. BUILD: a code LLM receives the mockup image + tech requirements
   (latest HTML5, semantic markup, vanilla JS, optional three.js hero,
   accessibility, SEO) plus our frontend_design skill file, and produces
   a complete self-contained index.html implementing that visual design.
3. The result can then be scored by agents/design_loop.py (judge).

Usage:
  python3 agents/design_vision.py <slug>            # business from DB
  python3 agents/design_vision.py --industry "zahradní služby" --name "Zahrady Petrov"
  python3 agents/design_vision.py <slug> --mockup path.png   # reuse existing mockup

Env: OPENROUTER_API_KEY required.
"""

import base64
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "generated"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Fallback chain for IMAGE GENERATION (ordered cheap->premium).
IMAGE_MODELS = [
    "google/gemini-2.5-flash-image",
    "google/gemini-3.1-flash-image-preview",
    "google/gemini-3.1-flash-image",
    "google/gemini-3-pro-image-preview",
]
# Fallback chain for the BUILDER (code) model.
BUILD_MODELS = [
    os.environ.get("BUILD_MODEL", "nvidia/nemotron-3.5-lightning:free"),
    "z-ai/glm-5.2:free",
    "thinkingmachines/inkling:free",
    "poolside/laguna-s-2.1:free",
    "google/gemma-4-31b-it:free",
    "cohere/north-mini-code:free",
    "openai/gpt-4o-mini",
]


def _post(payload: dict, timeout: int = 300) -> dict:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    req = urllib.request.Request(
        OPENROUTER_URL, data=json.dumps(payload).encode(), method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        body = ""
        if hasattr(e, "read"):
            try:
                body = e.read().decode()[:300]
            except Exception:
                pass
        raise RuntimeError(f"API error: {e} {body}") from e


# ------------------------------------------------------------ 1. concept

MOCKUP_PROMPT = """Vytvoř profesionální FULL-PAGE design mockup moderního webu pro:
Firma: {name} ({industry}){extra}

Požadavky na návrh:
- Jednostránkový web (hero, služby, galerie/reference, o nás, kontakt)
- Moderní, výrazný, NE generický 'AI look' — osobitá typografie a paleta
- Realistické vyplnění textem i obrázky (placeholder fotografie v tématu firmy)
- Desktopové rozložení 1440px, viditelná navigace i patička
- Design musí působit důvěryhodně pro malou českou firmu

Vygeneruj obrázek mockupu."""

MOCKUP_PROMPT_TECH = """
Navíc: navrhni tak, aby hero sekce mohla obsahovat interaktivní 3D/prvky
(three.js particle/geometry scéna v barvách značky) — ve statickém mockupu
stačí naznačit vizuál, který three.js implementuje."""


def generate_mockup(name: str, industry: str, extra: str = "",
                    tech: bool = True) -> tuple[bytes, str]:
    """Try each image model until one returns an image. Returns (png, model)."""
    prompt = MOCKUP_PROMPT.format(name=name, industry=industry,
                                  extra=f"\n{extra}" if extra else "")
    if tech:
        prompt += MOCKUP_PROMPT_TECH
    errors = []
    for model in IMAGE_MODELS:
        try:
            print(f"  mockup: zkusím {model} ...")
            data = _post({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "modalities": ["image", "text"],
            })
            msg = data["choices"][0]["message"]
            imgs = msg.get("images") or []
            if imgs:
                url = imgs[0]["image_url"]["url"]
                b64 = url.split(",", 1)[1] if "," in url else url
                print(f"  ✓ mockup od {model}")
                return base64.b64decode(b64), model
            errors.append(f"{model}: no image in response")
        except Exception as e:
            print(f"  ✗ {model}: {e}")
            errors.append(f"{model}: {e}")
    raise RuntimeError("All image models failed:\n" + "\n".join(errors))


# ------------------------------------------- 1b. text-mockup degradation

SPEC_PROMPT = """Jsi senior art director. Pro web firmy "{name}" ({industry})
vytvoř EXAKTNÍ design specifikaci jako JSON (bez markdown fence):
{{
 "concept": "jedna věta — designová vize",
 "palette": {{"primary": "#hex", "secondary": "#hex", "accent": "#hex",
              "bg": "#hex", "text": "#hex"}},
 "typography": {{"heading": "Google Font + weight + clamp() velikosti",
                 "body": "Google Font"}},
 "hero": {{"layout": "popis kompozice", "headline": "konkrétní CZ headline",
           "three_js_scene": "co má vykreslit three.js (geometrie/barvy/pohyb)",
           "cta": "text tlačítka"}},
 "sections": ["5-7 sekcí s popisem obsahu a layoutu"],
 "decor": ["signature vizuální prvky dle oboru"],
 "cards": "styl karet služeb (stíny, radius, hover)",
 "footer": "co obsahuje"
}}
Obor-appropriate: zahradník=zelené/organické, autoservis=ocel/červená,
salon=růže/šampaňské. Žádný generický 'AI look'."""

TEXT_SPEC_MODELS = [
    os.environ.get("SPEC_MODEL", "z-ai/glm-5.2:free"),
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3.5-lightning:free",
    "thinkingmachines/inkling:free",
    "google/gemma-4-26b-a4b-it:free",
    "cohere/north-mini-code:free",
    "openai/gpt-4o-mini",
]


def _post_retry(payload: dict, tries: int = 4, timeout: int = 300) -> dict:
    """POST with backoff retry on 429/5xx."""
    import time
    last = None
    for t in range(tries):
        try:
            return _post(payload, timeout=timeout)
        except RuntimeError as e:
            last = e
            if "429" in str(e) or "500" in str(e) or "502" in str(e) or "503" in str(e):
                wait = 15 * (t + 1)
                print(f"    retry {t+1}/{tries} za {wait}s")
                time.sleep(wait)
                continue
            raise
    raise last


def generate_text_spec(name: str, industry: str) -> dict:
    """Fallback when no image model is affordable: free LLM writes the
    design specification that the builder implements."""
    errors = []
    for model in TEXT_SPEC_MODELS:
        try:
            print(f"  text-spec: zkusím {model} ...")
            data = _post_retry({"model": model, "max_tokens": 2000,
                                "messages": [{"role": "user", "content":
                                              SPEC_PROMPT.format(name=name,
                                                                 industry=industry)}]})
            out = data["choices"][0]["message"]["content"]
            m = re.search(r"\{.*\}", out, re.DOTALL)
            if not m:
                raise ValueError("no JSON")
            print(f"  ✓ spec od {model}")
            return json.loads(m.group(0))
        except Exception as e:
            print(f"  ✗ {model}: {e}")
            errors.append(f"{model}: {e}")
    raise RuntimeError("All spec models failed:\n" + "\n".join(errors))


# -------------------------------------------------------------- 2. build

SKILL_FILE = BASE / "skills" / "frontend_design.md"

BUILD_SYSTEM = """Jsi elitní frontend engineer-agent LeadForge. Dostaneš GRAFICKÝ NÁVRH
(mockup) webu jako obrázek + firemní data. Tvým úkolem je POSTAVIT web
přesně podle návrhu.

TECH POŽADAVKY:
- Nejnovější HTML5 best practices: sémantické značky (<header>,<nav>,<main>,
  <section>,<article>,<footer>), ARIA atributy, lang="cs", meta description,
  Open Graph tagy, JSON-LD (LocalBusiness).
- Moderní CSS: custom properties, clamp() fluid typografie, grid/flex,
  scroll-behavior, prefers-reduced-motion, prefers-color-scheme pokud sedí.
- Vanilla JavaScript (ES2023): IntersectionObserver scroll-reveal,
  mobilní hamburger menu, plynulé animace. Žádné frameworky.
- THREE.JS HERO: import přes ES module z CDN (unpkg/jsdelivr, three@latest),
  interaktivní scéna odpovídající oboru (particles/geometrie v barvách
  značky), reagující na mouse move; graceful fallback bez WebGL.
- Self-contained jeden soubor index.html. Externí zdroje POVOLeny:
  Google Fonts, Unsplash fotky, three.js CDN.
- Performance: lazy-loading obrázků, font-display=swap, žádné blokující skripty.

ZAKÁZANÉ POSTUPY (tvrdé pravidlo):
- ŽÁDNÉ utility CSS frameworky (Tailwind, Bootstrap...) ani jejich třídy
  (flex, grid, hidden, md:flex, text-xl, mx-auto...). Používej VLASTNÍ
  sémantické třídy a styly je v <style>. Každá class v HTML musí mít
  odpovídající CSS definici.
- HAMBURGAR MENU: pokud existuje button.hamburger-btn, MUSÍ existovat i
  JS toggle listener a CSS pro .hamburger-line. Otestuj logicky.
- FOTKY: používej POUZE tyto ověřené Unsplash photo-ID:
  zahrada: photo-1416879595882-3373a0480b5b, photo-1466692476868-aef1dfb1e735,
  photo-1523348837708-15d4a09cfac2, photo-1585320806297-9794b3e4eeae
  auto: photo-1486262715619-67b85e0b08d3, photo-1530046339160-ce3e530c7d2f
  květiny/interiér: photo-1490750967868-88aa4486c946
  (URL format: https://images.unsplash.com/<ID>?w=800&q=70&fit=crop)
  Nikdy si nevymýšlej vlastní photo-ID.
- ŽÁDNÉ exit()/require() v browser skriptech — early return řeš přes if/else.

ŽELEZNÁ PRAVIDLA OBSAHU:
- Používej POUZE dodaná firemní data. Nic si nevymýšlej (žádné ceny,
  reference, recenze). Služby odvozené z oboru povoleny.
- Kontakty, IČO, tel:, e-mail přenás přesně.

Vrať POUZE kompletní finální HTML začínající <!DOCTYPE html>.
Žádné vysvětlování, žádné reasoning, žádné markdown fence.

=== SKILL FILE (design zásady) ===
{skill}
=== END SKILL ==="""


def build_site(mockup_png: bytes | None, name: str, industry: str,
               facts: dict, spec_path: Path | None = None) -> tuple[str, str]:
    """Send mockup (or text spec fallback) + facts to builder models."""
    skill = SKILL_FILE.read_text(encoding="utf-8") if SKILL_FILE.exists() else ""
    facts_txt = json.dumps(facts, ensure_ascii=False, indent=2)
    user = f"""FIREMNÍ DATA (jediný pravdivý zdroj obsahu):
{facts_txt}

Obor: {industry}
Postav kompletní single-page web dle návrhu a technických požadavků."""
    if mockup_png:
        b64 = base64.b64encode(mockup_png).decode()
        user = ("GRAFICKÝ NÁVRH (mockup) je jako obrázek v této zprávě — "
                "implementuj ho 1:1.\n\n" + user)
        content = [{"type": "text", "text": user},
                   {"type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"}}]
    else:
        spec = ""
        if spec_path and spec_path.exists():
            spec = spec_path.read_text(encoding="utf-8")
        user = ("GRAFICKÝ NÁVRH není k dispozici — místo něj implementuj PŘESNĚ "
                "tuto design specifikaci od art directora:\n\n" + spec +
                "\n\n" + user)
        content = [{"type": "text", "text": user}]
    errors = []
    for model in BUILD_MODELS:
        try:
            print(f"  build: zkusím {model} ...")
            data = _post_retry({"model": model,
                                "messages": [{"role": "system",
                                              "content": BUILD_SYSTEM.format(skill=skill)},
                                             {"role": "user", "content": content}],
                                "max_tokens": 16000})
            out = data["choices"][0]["message"]["content"] or ""
            out = re.sub(r"^```(html)?\n?|```\n?$", "", out.strip(),
                         flags=re.MULTILINE).strip()
            m = re.search(r"(<!DOCTYPE|<html)", out, re.IGNORECASE)
            if not m:
                raise ValueError(f"output is not HTML ({len(out)} chars)")
            if m.start() > 0:
                print(f"    [build: odstraněno {m.start()} znaků reasoning textu]")
                out = out[m.start():]
            print(f"  ✓ web od {model} ({len(out)//1024} KB)")
            return out, model
        except Exception as e:
            print(f"  ✗ {model}: {e}")
            errors.append(f"{model}: {e}")
    raise RuntimeError("All build models failed:\n" + "\n".join(errors))


# ------------------------------------------------------------------ main

FIX_SYSTEM = """Jsi frontend QA-fix agent. Dostaneš HTML s konkrétními nalezenými
problémy. Oprav POUZE tyto problémy, nic jiného neměň.

Pravidla:
- Utility třídy (flex/grid/hidden/text-xl/md:...) → nahraď vlastními
  sémantickými třídami a definuj je v <style>. NEBO přidej ekvivalentní CSS.
- Mrtvé obrázky (404) → vyměň za ověřená Unsplash photo-ID nebo odstraň.
- Chybějící hamburger toggle → doplň JS listener + CSS.
- exit()/require() v JS → přepiš na if/else guard.
Vrať POUZE kompletní opravené HTML, žádný komentář."""


def _fix_problems(html: str, problems: list[str], name: str,
                  industry: str) -> str:
    plist = "\n".join(f"- {p}" for p in problems)
    from agents.customer_comms import _llm as _comms_llm
    out = _comms_llm(FIX_SYSTEM, f"""HTML:
{html[:80000]}

NALEZENÉ PROBLÉMY:
{plist}

Oprav a vrať kompletní HTML.""", max_tokens=16000) or ""
    m = re.search(r"(<!DOCTYPE|<html)", out, re.IGNORECASE)
    if not m or "</html>" not in out.lower():
        print("  (fix pass vrátil nesmysl — ponechávám původní HTML)")
        return html
    return re.sub(r"^```(html)?\n?|```\n?$", "", out.strip(),
                  flags=re.MULTILINE).strip()[m.start():]



def lead_facts(slug_or_name: str) -> dict:
    """Pull real company facts from DB by slug or name fragment."""
    try:
        from core.db import connect
        conn = connect()
        cols = [r[1] for r in conn.execute(
            "PRAGMA table_info(leads)").fetchall()]
        name_col = "name" if "name" in cols else (
            "company_name" if "company_name" in cols else None)
        if not name_col:
            return {}
        like_col = "demo_url" if "demo_url" in cols else name_col
        rows = conn.execute(
            f"SELECT * FROM leads WHERE {like_col} LIKE ? OR {name_col} LIKE ?",
            (f"%{slug_or_name}%", f"%{slug_or_name}%")).fetchall()
        if rows:
            r = dict(rows[0])
            keys = [k for k in ("name", "company_name", "industry", "city",
                                "ico", "phone", "email", "address", "trades")
                    if k in r and r[k]]
            return {k: r.get(k) for k in keys}
    except Exception as e:
        print(f"  (DB lookup skip: {e})")
    return {}


def process(target: str, industry_hint: str = "", name_hint: str = "",
            reuse_mockup: Path | None = None, tech: bool = True) -> dict:
    facts = lead_facts(target)
    name = facts.get("name") or facts.get("company_name") or name_hint or target
    industry = facts.get("industry") or industry_hint or "živnostník"
    slug = target.strip("/").split("/")[-1].removeprefix("demo-")
    out_dir = OUT / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[{slug}] {name} ({industry})")

    if reuse_mockup and reuse_mockup.exists():
        mockup, img_model = reuse_mockup.read_bytes(), "(reuse)"
    else:
        try:
            mockup, img_model = generate_mockup(name, industry,
                                                extra=str(facts), tech=tech)
        except RuntimeError as e:
            print(f"  ⚠ image modely nedostupné ({str(e).splitlines()[0][:80]}...)")
            print("  → degradace na textovou design specifikaci")
            spec = generate_text_spec(name, industry)
            (out_dir / "design_spec.json").write_text(
                json.dumps(spec, ensure_ascii=False, indent=2),
                encoding="utf-8")
            mockup, img_model = None, f"text-spec:{spec.get('concept','')[:40]}"
    if mockup:
        (out_dir / "mockup.png").write_bytes(mockup)
        print(f"  mockup -> {out_dir/'mockup.png'} ({len(mockup)//1024} KB, {img_model})")

    html, build_model = build_site(mockup, name, industry, facts,
                                   spec_path=out_dir / "design_spec.json")

    # post-build validation gate
    from agents.site_validator import validate
    tmp = out_dir / "index.html"
    tmp.write_text(html, encoding="utf-8")
    for attempt in range(2):
        probs = validate(tmp)
        if not probs:
            print("  ✓ validator: VŠE OK")
            break
        print(f"  ⚠ validator našel {len(probs)} problémů:")
        for x in probs:
            print("   -", x[:120])
        if attempt == 0:
            print("  → fix pass přes problémy...")
            html = _fix_problems(html, probs, name, industry)
            tmp.write_text(html, encoding="utf-8")
        else:
            print("  ✗ i po fixu problémy — ukládám tak, ale hlásím")

    meta = {"slug": slug, "mockup_model": img_model,
            "build_model": build_model, "tech_hero": tech,
            "facts": facts}
    (out_dir / "vision_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✓ {out_dir/'index.html'} ({len(html)//1024} KB)")
    return meta


if __name__ == "__main__":
    args = sys.argv[1:]
    industry = name_hint = ""
    reuse = None
    if "--industry" in args:
        i = args.index("--industry"); industry = args[i + 1]; del args[i:i+2]
    if "--name" in args:
        i = args.index("--name"); name_hint = args[i + 1]; del args[i:i+2]
    if "--mockup" in args:
        i = args.index("--mockup"); reuse = Path(args[i + 1]); del args[i:i+2]
    if not args:
        sys.exit("usage: design_vision.py <slug> [--industry X] [--name Y] "
                 "[--mockup path.png]")
    results = [process(a, industry, name_hint, reuse) for a in args]
    print(json.dumps(results, ensure_ascii=False, indent=2))
