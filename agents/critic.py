"""Design Critic Agent — vision-based design review via CV model.

Takes a screenshot (local PNG or URL), sends it to a vision-capable LLM
(OpenRouter by default, free Pollinations as fallback), and returns a harsh,
actionable design critique: score 1-10 + problems + concrete improvements.

Requires OPENROUTER_API_KEY in env for the primary path. Without it, falls
back to rule-based self-critique (weaker but never blocks the pipeline).

Usage:
  python3 agents/critic.py <screenshot.png|https://...>
  python3 agents/critic.py --all        # critique all DEPLOYED sites
"""

import base64
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
# free/cheap vision models on openrouter:
VISION_MODEL = os.environ.get("CRITIC_MODEL", "google/gemini-2.0-flash-exp:free")
POLLINATIONS = "https://text.pollinations.ai/openai"

PROMPT = """Jsi extrémně kritický senior webdesignér. Toto je fullpage screenshot
demo webu pro českého řemeslníka/zahradníka. Ohodnoť:

1. SKÓRE 1-10 (jak by web obstál proti konkurenci)
2. 3 NEJVĚTŠÍ PROBLÉMY (konkrétně — co je ošklivé/chybí/působí amatérsky)
3. 3 KONKRÉTNÍ VYLEPŠENÍ (co by posunulo web na 8+/10)

Buď bez lítosti — cílem je profesionální web, ne školní projekt.
Odpovídej česky, max 200 slov."""


def screenshot_to_b64(source: str) -> str:
    if source.startswith("http"):
        req = urllib.request.Request(source, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
    else:
        raw = Path(source).read_bytes()
    return base64.b64encode(raw).decode()


def critique_openrouter(b64_image: str) -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    payload = {
        "model": VISION_MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url",
                 "image_url": {"url": f"data:image/png;base64,{b64_image}"}},
                {"type": "text", "text": PROMPT},
            ],
        }],
    }
    req = urllib.request.Request(
        OPENROUTER_URL, data=json.dumps(payload).encode(), method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read().decode())
        return d["choices"][0]["message"]["content"]


def self_critique(html: str) -> str:
    """Rule-based fallback when no vision API available."""
    css_m = re.search(r'(?s)<style>(.*?)</style>', html)
    css = css_m.group(1) if css_m else ""
    score = 5
    issues, wins = [], []
    if "unsplash" in html:
        wins.append("fotky z Unsplash"); score += 1
    else:
        issues.append("žádné fotografie")
    if "ambient" in css:
        wins.append("animované dekorace"); score += 1
    if "gallery" in html:
        wins.append("galerie"); score += 1
    if "@keyframes" in css:
        score += 1
    else:
        issues.append("statické — žádné animace")
    if "maps.google" in html:
        score += 1
    if len(css) > 6000:
        score += 1
    out = f"[SELF-CRITIQUE ~{min(score,10)}/10]\n"
    out += "Silné: " + ("; ".join(wins) or "-") + "\n"
    out += "Slabiny: " + ("; ".join(issues) or "-") + "\n"
    out += ("Upozornění: plné CV hodnocení vyžaduje OPENROUTER_API_KEY "
            "(vision model uvidí to, co statická analýza neumí — kompozici, "
            "typografii, barevné ladění, first-impression efekt).")
    return out


def critique_site(source: str, html_path: str | None = None) -> tuple[str, str]:
    """Returns (source_label, critique_text)."""
    try:
        b64 = screenshot_to_b64(source)
        return "openrouter-vision", critique_openrouter(b64)
    except Exception as e:
        reason = str(e)[:100]
        if html_path and Path(html_path).exists():
            html = Path(html_path).read_text(encoding="utf-8")
            return f"self ({reason[:40]})", self_critique(html)
        return "self", f"cannot critique: {reason}"


def run_all() -> dict:
    from core.db import connect
    conn = connect()
    rows = conn.execute(
        "SELECT id, company_name, demo_url FROM leads WHERE stage='DEPLOYED'").fetchall()
    out = {}
    for r in rows:
        d = dict(r)
        slug = d["demo_url"].rstrip("/").split("/")[-1].removeprefix("demo-")
        path = Path(__file__).resolve().parent.parent / "generated" / slug / "index.html"
        shot = Path("/tmp/shots") / f"{slug.split('-')[2] if '-' in slug else slug}-desktop.png"
        src, text = critique_site(str(shot), str(path))
        print(f"\n===== {d['company_name']} [{src}] =====")
        print(text[:800])
        out[d["company_name"]] = {"source": src, "critique": text}
    return out


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "--all"
    if arg == "--all":
        run_all()
    else:
        html = None
        src, txt = critique_site(arg, html)
        print(f"[{src}]\n{txt}")
