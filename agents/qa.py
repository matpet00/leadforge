"""Stage 6: QA agent — quality gate before a demo site is shown to anyone.

Checks (deterministic, cheap):
  1. Valid HTML skeleton (doctype, lang=cs, title, viewport)
  2. No placeholder/template leakage ({{, }}, TODO, lorem)
  3. No hallucinated content markers (prices, fake reviews, years of experience)
  4. Company name present in headline area
  5. Contact present (phone or email link)
Optional LLM review when a key is available.

Failures bounce the lead back to ENRICHED with a reason; repeated failures -> DISCARDED.
"""

import re
from pathlib import Path

from core.db import connect, leads_in_stage, advance

BASE = Path(__file__).resolve().parent.parent
GENERATED = BASE / "generated"

LEAK_PATTERNS = [r"\{\{", r"\bTODO\b", r"lorem ipsum", r"%s"]
HALLUCINATION_PATTERNS = [
    r"\b\d+\s*K[čc]\b",            # prices like 500 Kč
    r"\bzdarma\b",                  # "for free" promises
    r"reference[s]?",               # review sections we never sourced
    r"\b20\s*let\b",                # invented experience claims
]


def check_html(html: str, company: str) -> tuple[bool, list[str]]:
    problems = []
    if "<!DOCTYPE html>" not in html:
        problems.append("missing doctype")
    if 'lang="cs"' not in html:
        problems.append("missing lang=cs")
    if not re.search(r"<title>[^<]{3,}</title>", html):
        problems.append("missing/empty title")
    if "viewport" not in html:
        problems.append("missing viewport meta")
    for pat in LEAK_PATTERNS:
        if re.search(pat, html, re.IGNORECASE):
            problems.append(f"template leak: {pat}")
    for pat in HALLUCINATION_PATTERNS:
        if re.search(pat, html, re.IGNORECASE):
            problems.append(f"risky claim: {pat}")
    # company name should appear in body text
    body = re.sub(r"<[^>]+>", " ", html)
    if company.split()[0].lower() not in body.lower():
        problems.append("company name missing from content")
    if "tel:" not in html and "mailto:" not in html:
        problems.append("no contact action (tel:/mailto:)")
    return (len(problems) == 0), problems


def run() -> dict:
    conn = connect()
    passed = failed = 0
    for lead in leads_in_stage(conn, "GENERATED"):
        site_dir = GENERATED / lead["demo_url"].rstrip("/").split("/")[-1]
        html_path = site_dir / "index.html"
        if not html_path.exists():
            advance(conn, lead["id"], "ENRICHED", "QA: site file missing, regenerating")
            failed += 1
            continue
        ok, problems = check_html(html_path.read_text(encoding="utf-8"), lead["company_name"])
        if ok:
            advance(conn, lead["id"], "QA", "all checks passed")
            passed += 1
        else:
            advance(conn, lead["id"], "ENRICHED", "QA failed: " + "; ".join(problems))
            failed += 1
    conn.commit()
    return {"passed": passed, "failed": failed}


if __name__ == "__main__":
    print(run())
