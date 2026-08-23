"""Web Review Agent — quality gate for generated demo sites.

Evaluates each deployed site on:
  - structure (semantic HTML, sections, single h1)
  - modern UX (mobile viewport, scroll effects, hover states, menu)
  - SEO (meta description, JSON-LD, og tags, title length)
  - performance budget (page size < 50KB, zero external requests)
  - accessibility (lang, alt/aria, focus-visible, reduced-motion)
  - code quality (inline CSS organized, no dead code, no placeholder text)

Each site gets a score 0-100 + concrete improvement list. Sites below
threshold are regenerated with the improvements applied (max MAX_ITERATIONS
per site to avoid endless polishing). Review results stored in lead notes +
events so the dashboard can show them.

Usage:
  python3 agents/reviewer.py            # review all DEPLOYED sites
  python3 agents/reviewer.py --fix      # review + regenerate weak sites
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.db import connect, advance, log_event

BASE = Path(__file__).resolve().parent.parent
GENERATED = BASE / "generated"

THRESHOLD = 75          # below this -> regenerate with fixes
MAX_ITERATIONS = 2      # per site; then accept and move on
SIZE_BUDGET_KB = 50


def review_html(html: str) -> dict:
    """Static analysis of one site. Returns {score, issues[], wins[]}."""
    score = 100
    issues, wins = [], []

    def deduct(points, issue):
        nonlocal score
        score -= points
        issues.append(issue)

    def add_win(w):
        wins.append(w)

    # --- structure ---
    if len(re.findall(r"<h1[ >]", html)) != 1:
        deduct(10, "h1 count != 1")
    else:
        add_win("single h1")
    for tag in ["header", "nav", "main", "section", "footer"]:
        if f"<{tag}" not in html:
            deduct(6, f"missing semantic <{tag}>")
    if html.count("<section") >= 3:
        add_win("multi-section layout")

    # --- modern UX / interactivity ---
    has_viewport = 'name="viewport"' in html
    has_media_queries = "@media" in html
    has_transitions = "transition" in css_block(html)
    has_hover = ":hover" in css_block(html)
    has_js_interactivity = "<script>" in html and "addEventListener" in html
    has_scroll_effects = "IntersectionObserver" in html or ".reveal" in html
    has_reduced_motion = "prefers-reduced-motion" in html

    if not has_viewport:
        deduct(15, "no mobile viewport meta")
    else:
        add_win("responsive viewport")
    if not has_media_queries:
        deduct(12, "no media queries (not responsive)")
    else:
        add_win("media queries")
    if not has_transitions:
        deduct(8, "no CSS transitions (feels static)")
    else:
        add_win("CSS transitions")
    if not has_hover:
        deduct(5, "no hover states")
    if not has_js_interactivity:
        deduct(8, "no JS interactivity")
    else:
        add_win("JS interactivity")
    if has_scroll_effects:
        add_win("scroll reveal effects")
    else:
        deduct(7, "no scroll animations")
    if not has_reduced_motion:
        deduct(4, "ignores prefers-reduced-motion")

    # hamburger for mobile nav
    if "menu-btn" in html or ("@media" in html and ".nav-links" in html):
        add_win("mobile navigation handling")

    # --- SEO ---
    m = re.search(r'<meta name="description" content="([^"]*)"', html)
    if not m:
        deduct(12, "missing meta description")
    elif len(m.group(1)) > 160:
        deduct(4, "meta description > 160 chars")
    else:
        add_win("meta description OK")
    if "application/ld+json" in html:
        add_win("JSON-LD structured data")
    else:
        deduct(10, "missing JSON-LD LocalBusiness")
    if 'property="og:' in html:
        add_win("OpenGraph tags")
    else:
        deduct(4, "missing OG tags")
    t = re.search(r"<title[^>]*>(.*?)</title>", html, re.S)
    if not t or not (10 < len(t.group(1).strip()) <= 65):
        deduct(5, "title missing or bad length")

    # --- performance ---
    size_kb = len(html.encode()) / 1024
    if size_kb > SIZE_BUDGET_KB:
        deduct(min(20, int(size_kb - SIZE_BUDGET_KB)), f"page {size_kb:.0f}KB > {SIZE_BUDGET_KB}KB budget")
    else:
        add_win(f"size {size_kb:.0f}KB within budget")
    external = re.findall(r'(?:src|href)="(https?://[^"]+)"', html)
    ext_non_meta = [u for u in external if "og:" not in u and "schema.org" not in u]
    if ext_non_meta:
        deduct(min(10, len(ext_non_meta) * 3), f"{len(ext_non_meta)} external resources: {ext_non_meta[:2]}")
    else:
        add_win("zero external requests (self-contained)")

    # --- accessibility ---
    if 'lang="' in html:
        add_win("lang attribute")
    else:
        deduct(6, "missing lang attribute")
    if "aria-label" in html or "aria-" in html:
        add_win("aria labels")
    if ":focus-visible" in html or ":focus" in css_block(html):
        add_win("focus styles")
    else:
        deduct(4, "no visible focus styles")

    # --- code quality ---
    if re.search(r"lorem ipsum|TODO|FIXME|placeholder", html, re.I):
        deduct(15, "placeholder text in production output!")
    empty_tags = len(re.findall(r"<(p|h\d|div)>\s*</\1>", html))
    if empty_tags:
        deduct(min(8, empty_tags * 2), f"{empty_tags} empty elements")
    inline_styles = len(re.findall(r'style="', html))
    if inline_styles > 10:
        deduct(5, f"{inline_styles} scattered inline styles (keep CSS centralized)")

    return {"score": max(0, min(100, round(score))),
            "issues": issues, "wins": wins,
            "size_kb": round(size_kb, 1)}


def css_block(html: str) -> str:
    m = re.search(r"(?s)<style>(.*?)</style>", html)
    return m.group(1) if m else ""


def strip_html(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(
        r"<[^>]+>", " ", re.sub(r"(?is)<(script|style).*?</\1>", " ", html)))


def review_design(html: str) -> dict:
    """Design-quality review: originality, visual hierarchy, creativity.
    This is the subjective half the static checks above can't see."""
    score = 0
    issues, wins = [], []
    css = css_block(html)

    def add(pts, why):
        nonlocal score
        score += pts
        wins.append(why)

    def miss(pts, why):
        nonlocal score
        score -= pts
        issues.append(why)

    # --- uniqueness signals (template sameness is the enemy) ---
    if "--accent" in css and css.count("#") >= 6:
        add(8, "custom color system")
    else:
        miss(10, "barely-there color identity")
    for pattern in ["gradient", "backdrop-filter", "clip-path", "blur(", "mix-blend"]:
        if pattern in css:
            add(6, f"modern CSS technique: {pattern}")
    if "clamp(" in css:
        add(5, "fluid typography (clamp)")
    else:
        miss(5, "static font sizes only")

    # --- visual hierarchy & depth ---
    depth_signals = sum(1 for p in ["box-shadow", "border-radius", "opacity"] if p in css)
    if depth_signals >= 2:
        add(depth_signals * 3, "depth & layering present")
    else:
        miss(8, "flat, no depth")
    if "letter-spacing" in css:
        add(4, "typographic detail")
    if re.search(r"\.hero[^\{]*\{[^}]*padding:\s*(9\d|1\d\d)px", css):
        add(6, "generous hero whitespace")
    else:
        miss(6, "cramped hero — no breathing room")

    # --- creativity / delight ---
    creative = sum(1 for p in ["animation", "@keyframes", "transform:", "::before", "::after",
                               "svg", "transition-delay", "nth-child"]
                   if p in html.lower())
    add(min(creative * 4, 20), f"{creative} creative elements")
    if creative == 0:
        miss(15, "zero decorative/creative elements — sterile")
    if "svg" in html.lower():
        add(5, "inline SVG artwork/icons")

    # --- content personality ---
    text = strip_html(html)
    czech_specific = sum(1 for w in ["rádi", "rád", "můžete", "stačí", "klidně",
                                     "domluvit", "poradit"] if w in text.lower())
    if czech_specific >= 2:
        add(6, "warm human copy tone")
    else:
        miss(6, "copy feels machine-generated")
    if len(text) < 600:
        miss(10, "too little content to feel real")
    elif len(text) > 1200:
        add(4, "rich content")

    # --- anti-blandness checklist ---
    same_as_default = all(x in css for x in ["max-width:1100px", "border-radius:14px",
                                             "#f5f7fa"])
    if same_as_default:
        miss(12, "looks like default template — no customization")

    return {"score": max(0, min(100, round(score))),
            "issues": issues, "wins": wins}


def run(fix: bool = False) -> dict:
    conn = connect()
    rows = conn.execute(
        "SELECT id, company_name, demo_url FROM leads WHERE stage IN ('DEPLOYED','QA')").fetchall()
    report = {"reviewed": 0, "passed": 0, "needs_fix": [], "fixed": [],
              "maxed_out": []}

    for r in rows:
        d = dict(r)
        raw = (d["demo_url"] or "")
        if raw.startswith("http"):
            slug = raw.rstrip("/").split("/")[-1]
            if not (GENERATED / slug / "index.html").exists():
                slug = slug.removeprefix("demo-")
        else:
            raw = raw.replace("file://", "").strip("/")
            slug = raw.split("/")[0] if "/" in raw else raw.replace("index.html", "").strip("/")
        path = GENERATED / slug / "index.html"
        if not path.exists():
            continue
        result = review_html(path.read_text(encoding="utf-8"))
        design = review_design(path.read_text(encoding="utf-8"))
        # combined score: technical 50% + design 50%
        combined = round(result["score"] * 0.5 + design["score"] * 0.5)
        result["combined"] = combined
        report["reviewed"] += 1

        # iteration counter from notes
        iters = len(re.findall(r"\[review", d.get("notes", "") or ""))
        status = "PASS" if combined >= THRESHOLD else (
            "FIX" if fix and iters < MAX_ITERATIONS else "ACCEPTED")
        detail = (f"tech={result['score']} design={design['score']} "
                  f"combined={combined} {status}; "
                  f"issues: {'; '.join((result['issues'] + design['issues'])[:3]) or 'none'}")
        conn.execute(
            "UPDATE leads SET notes=COALESCE(notes,'')||? WHERE id=?",
            (f" [review:{result['score']}:{status}]", d["id"]))
        log_event(conn, d["id"], "REVIEW",
                  f"score {result['score']} ({status}) — "
                  f"{'; '.join(result['issues'][:2]) or 'clean'}")
        print(f"[🔍 Reviewer] {d['company_name']}: {result['score']} {status}")
        for i in result["issues"]:
            print(f"    · {i}")

        if status == "PASS":
            report["passed"] += 1
        elif status == "FIX":
            report["needs_fix"].append({"lead_id": d["id"], "slug": slug,
                                        "score": result["score"],
                                        "issues": result["issues"]})
        elif status == "ACCEPTED" and result["score"] < THRESHOLD:
            report["maxed_out"].append(d["company_name"])

    conn.commit()
    conn.close()

    if fix and report["needs_fix"]:
        from generator.site_builder import run as gen_run
        from agents import qa as qa_mod
        conn = connect()
        for item in report["needs_fix"]:
            conn.execute("UPDATE leads SET stage='ENRICHED' WHERE id=?",
                         (item["lead_id"],))
        conn.commit()
        conn.close()
        gen_result = gen_run(use_llm=False)
        qa_result = qa_mod.run()
        report["fixed"] = gen_result.get("built", [])
        print(f"[🔍 Reviewer] regenerated {report['fixed']}, QA: {qa_result}")

    return report


if __name__ == "__main__":
    print(run(fix="--fix" in sys.argv))
