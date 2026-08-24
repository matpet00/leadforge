"""Design Judge -> Fix loop (LLM-as-judge).

1. Judge: vision model scores the site (screenshot + HTML), returns structured
   verdict JSON: {score, sub_scores, problems[], commands[]}.
2. Fixer: LLM loaded WITH skills/frontend_design.md rewrites the HTML,
   applying the judge's commands while keeping content truthful (no invented
   references/prices).
3. Optional --loop N repeats judge->fix until score >= target or N exhausted.

Usage:
  python3 agents/design_loop.py <slug>            # single judge->fix pass
  python3 agents/design_loop.py <slug> --loop 3   # up to 3 iterations
  python3 agents/design_loop.py --all             # every DEPLOYED lead

Env: OPENROUTER_API_KEY required. JUDGE_MODEL / FIXER_MODEL override models.
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
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "google/gemini-2.5-flash")
# Free-tier fallback chain for the judge (vision models).
JUDGE_FALLBACKS = [
    m for m in os.environ.get("JUDGE_FALLBACKS",
        "google/gemma-4-31b-it:free,nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free,"
        "google/gemma-4-26b-a4b-it:free").split(",") if m]
FIXER_MODEL = os.environ.get("FIXER_MODEL", "openai/gpt-4o-mini")
TARGET_SCORE = float(os.environ.get("TARGET_SCORE", "8.5"))
BASE = Path(__file__).resolve().parent.parent
SHOTS = Path("/root/shots")


def _chat(payload: dict, timeout: int = 240) -> str:
    import time
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    last = None
    for t in range(4):
        req = urllib.request.Request(
            OPENROUTER_URL, data=json.dumps(payload).encode(), method="POST",
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {key}"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503):
                wait = 20 * (t + 1)
                print(f"    [retry {t+1}/4 za {wait}s — HTTP {e.code}]")
                time.sleep(wait)
                continue
            raise
    raise last


def chat_text(model: str, system: str, user: str, max_tokens=4000) -> str:
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": user})
    return _chat({"model": model, "messages": msgs, "max_tokens": max_tokens})


# ------------------------------------------------------------------ judge

JUDGE_PROMPT = """Jsi extrémně kritický senior webdesignér a UX specialista. Hodnotíš
demo web českého živnostníka (fullpage screenshot + HTML zdroják).

Zhodnoť design I OBSAH. Vrať POUZE validní JSON (bez markdown):
{
 "score": <float 1-10 celkem>,
 "sub_scores": {"typografie": <f>, "paleta": <f>, "layout": <f>, "copy": <f>, "důvěryhodnost": <f>},
 "problems": ["5 největších konkrétních problémů — co je ošklivé/generické 'AI look'/chybí"],
 "commands": ["5-7 KONKRÉTNÍCH příkazů pro fix agenta jako instrukce do HTML/CSS/kopií,
   např. 'zvětši hero h1 na clamp(3rem,6vw,5rem)', 'přidej sekci Proč my s 4 USP body',
   'vyměň klišé headline za benefit-driven'. Každý příkaz musí být proveditelná
   úprava existujícího HTML."]
}

Pravidla: buď bez lítosti; generické šablonovité řešení = max 5; chválu nepiš.
Pozor: pokud screenshot ukazuje prázdné plochy, zkontroluj v HTML, jestli tam
skutečně nic není (lazy-load obrázky se na screenshotu nemuset vykreslit)."""


def fetch_html(slug_or_url: str) -> tuple[str, str | None]:
    """Return (html, png_path|None). slug = generated/ dir or live URL."""
    if slug_or_url.startswith("http"):
        req = urllib.request.Request(slug_or_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read().decode("utf-8", "replace"), None
    p = BASE / "generated" / slug_or_url / "index.html"
    if not p.exists():
        # try live github pages as fallback
        try:
            return fetch_html(f"https://matpet00.github.io/demo-{slug_or_url}/")
        except Exception:
            raise FileNotFoundError(f"No HTML for {slug_or_url}")
    return p.read_text(encoding="utf-8"), None


def shot_for(slug: str) -> Path | None:
    for cand in SHOTS.glob(f"*{slug.split('-')[0]}*.png"):
        return cand
    return None


def judge_site(html: str, png: Path | None) -> dict:
    content = [{"type": "text", "text": JUDGE_PROMPT}]
    if png and png.exists():
        b64 = base64.b64encode(png.read_bytes()).decode()
        content.append({"type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}"}})
    content.append({"type": "text",
                    "text": "\n\nHTML ZDROJÁK (zkráceno na CSS + strukturu):\n"
                            + html[:60000]})
    payload = {"messages": [{"role": "user", "content": content}],
               "max_tokens": 2000}
    errors = []
    for model in [JUDGE_MODEL] + JUDGE_FALLBACKS:
        try:
            out = _chat({**payload, "model": model})
            m = re.search(r"\{.*\}", out, re.DOTALL)
            if not m:
                raise ValueError(f"no JSON: {out[:120]}")
            return json.loads(m.group(0))
        except Exception as e:
            print(f"    judge {model} selhal: {str(e)[:100]}")
            errors.append(f"{model}: {e}")
    raise RuntimeError("All judge models failed:\n" + "\n".join(errors))


# ------------------------------------------------------------------- fixer

def load_skill() -> str:
    p = BASE / "skills" / "frontend_design.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""


FIX_SYSTEM = """Jsi elitní frontend designer-agent LeadForge. Přepisuješ HTML demo webu
podle pokynů design kritika. Dodržuj PŘÍSNĚ skill file níže (distinctive design,
no generic AI look, typografie nese osobnost, signature element).

ŽELEZNÁ PRAVIDLA:
- Vrať POUZE kompletní finální HTML, žádné komentáře ani markdown fence.
- Zachovej pravdivý obsah: žádné vymyšlené reference, ceny, recenze zákazníků.
  Testimonials označené jako přednosti firmy mohou zůstat.
- Zachovej SEO blok, JSON-LD, tel: odkazy, IČO, kontaktní údaje.
- Self-contained: inline CSS povoleno, externí jen Google Fonts + Unsplash fotky.
- Responsivita + prefers-reduced-motion musí zůstat funkční.

=== SKILL FILE ===
{skill}
=== END SKILL ==="""


def fix_html(html: str, verdict: dict) -> str:
    cmds = "\n".join(f"- {c}" for c in verdict.get("commands", []))
    probs = "\n".join(f"- {p}" for p in verdict.get("problems", []))
    user = f"""Aktuální HTML webu ({verdict.get('score')}/10):

{html[:80000]}

NAJDENÉ PROBLÉMY:
{probs}

PŘÍKAZY KE ZPRACOVÁNÍ (aplikuj VŠECHNY):
{cmds}

Vrať kompletní přepracované HTML."""
    out = chat_text(FIXER_MODEL, FIX_SYSTEM.format(skill=load_skill()), user,
                    max_tokens=6000)  # free tier rejects higher max_tokens (402)
    out = re.sub(r"^```(html)?\n?|```\n?$", "", out.strip(),
                 flags=re.MULTILINE).strip()
    # free models sometimes prepend reasoning/thinking text — keep only HTML
    m = re.search(r"(<!DOCTYPE|<html)", out, re.IGNORECASE)
    if not m:
        raise ValueError(f"fixer returned no HTML ({len(out)} chars): "
                         + out[:150])
    if m.start() > 0:
        print(f"    [fixer: odstraneno {m.start()} znaku reasoning textu]")
        out = out[m.start():]
    # strip reasoning text INJECTED INSIDE the document (between tags)
    end = out.lower().rfind("</html>")
    if end != -1:
        tail = out[end + len("</html>"):]
        if tail.strip() and not re.sub(r"^[^<]*", "", tail,
                                       flags=re.DOTALL).strip():
            print("    [fixer: odstranen text za </html>]")
            out = out[:end + len("</html>")]
    # detect prose paragraphs inside the body (reasoning leak)
    body_m = re.search(r"<body[^>]*>(.*?)</body>", out, re.DOTALL | re.IGNORECASE)
    if body_m:
        body = body_m.group(1)
        stripped = re.sub(r"<script.*?</script>|<!--.*?-->", "", body,
                          flags=re.DOTALL)
        visible = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", stripped)).strip()
        if len(visible) < 200 and len(body) > 500:
            raise ValueError(
                f"fixer output looks broken: body={len(body)}B but only "
                f"{len(visible)} chars of content — likely reasoning inside")
        if re.search(r"(Actually|Looking more carefully|I need to output|"
                     r"But the |Wait, )", visible):
            raise ValueError("fixer leaked reasoning into the document body")
    return out


# ------------------------------------------------------------------- loop

def process(slug: str, iterations: int = 1) -> dict:
    html, _ = fetch_html(slug)
    history = []
    out_dir = BASE / "generated" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    for i in range(1, iterations + 1):
        png = shot_for(slug)
        print(f"[{slug}] iterace {i}: judge ({JUDGE_MODEL}, shot={png})...")
        verdict = judge_site(html, png)
        score = verdict.get("score")
        print(f"  score={score}  problems={len(verdict.get('problems', []))}")
        history.append({"iteration": i, "score": score, "verdict": verdict})
        if float(score) >= TARGET_SCORE:
            print(f"  ✓ target {TARGET_SCORE} dosažen, končím")
            break
        print("  fixer přepisuje HTML...")
        html = fix_html(html, verdict)
        (out_dir / "index.html").write_text(html, encoding="utf-8")
        print(f"  uloženo -> {out_dir/'index.html'}")
    (out_dir / "design_history.json").write_text(
        json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"slug": slug, "final_score": history[-1]["score"] if history else None,
            "iterations": len(history)}


def all_slugs() -> list[str]:
    from core.db import connect
    conn = connect()
    rows = conn.execute(
        "SELECT demo_url FROM leads WHERE stage='DEPLOYED'").fetchall()
    slugs = [r["demo_url"].rstrip("/").split("/")[-1].removeprefix("demo-")
             for r in rows]
    return [s for s in slugs if s]


if __name__ == "__main__":
    loop_val = (sys.argv[sys.argv.index("--loop") + 1]
                if "--loop" in sys.argv else None)
    args = [a for a in sys.argv[1:] if not a.startswith("--") and a != loop_val]
    iters = int(sys.argv[sys.argv.index("--loop") + 1]) if "--loop" in sys.argv else 1
    targets = all_slugs() if (not args or args == ["--all"]) else args
    results = [process(s, iters) for s in targets]
    print(json.dumps(results, ensure_ascii=False, indent=2))
