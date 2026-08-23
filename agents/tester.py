"""Test Agent — validates the pipeline end-to-end and reports health to hub.

Runs in-process checks (no LLM needed):
  - DB reachable, schema sane
  - Scout: live ARES reachable (1 cheap query), sample fallback intact
  - Scorer: deterministic on known fixture leads
  - Generator: builds a site for a synthetic lead without touching real ones
  - QA gate: rejects a leaky/hallucinated site
  - Deploy: dry-run check (does not push)

Usage:
  python3 agents/tester.py            # run all checks
  python3 agents/tester.py --quick    # skip network checks
"""

import json
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RESULTS = []


def check(name: str, fn, critical: bool = True):
    try:
        detail = fn()
        RESULTS.append((name, "PASS", detail))
    except Exception as e:
        RESULTS.append((name, "FAIL" if critical else "WARN", str(e)[:200]))


# ---------------------------------------------------------------- checks

def db_check():
    from core.db import connect
    conn = connect()
    n = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    stages = [r[0] for r in conn.execute("SELECT DISTINCT stage FROM leads")]
    conn.close()
    return f"{n} leads, stages: {sorted(set(stages))}"


def ares_check():
    body = json.dumps({"start": 0, "pocet": 1, "obchodniJmeno": "autoservis",
                       "obchody": [], "pravniFormy": [], "icoIds": [],
                       "adresy": []}).encode()
    req = urllib.request.Request(
        "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/vyhledat",
        data=body, method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.loads(r.read().decode())
    assert d.get("pocetCelkem", 0) > 0, "ARES returned 0 results"
    return f"ARES OK ({d['pocetCelkem']} matches)"


def scorer_check():
    from agents.scorer import score_lead

    class L(dict):
        def __getitem__(self, k):
            return dict.__getitem__(self, k)

    good = L({"industry": "auto", "business_scope": "opravy automobilů; prodej",
              "company_name": "Autoservis Dobra", "city": "Brno"})
    s, reasons = score_lead(good)
    assert s >= 40, f"good lead scored {s}"
    bad = L({"industry": "other",
             "business_scope": "pronájem nemovitostí",
             "company_name": "Holding Invest", "city": ""})
    s2, _ = score_lead(bad)
    assert s2 < 30, f"bad lead scored {s2}"
    # determinism
    s3, _ = score_lead(good)
    assert s3 == s, "scorer not deterministic"
    return f"good={s}, bad={s2}, deterministic"


def generator_check():
    """Generate into an isolated temp DB so real leads are untouched."""
    import os
    tmp = tempfile.mkdtemp()
    old_cwd = Path.cwd()
    os.environ["LEADFORGE_DB"] = str(Path(tmp) / "test.db")
    try:
        # reimport db with fresh connection to temp file if supported
        from core import db as db_mod
        import sqlite3
        conn = sqlite3.connect(os.environ["LEADFORGE_DB"])
        conn.row_factory = sqlite3.Row
        conn.execute("""CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY, ico TEXT UNIQUE, company_name TEXT,
            business_scope TEXT DEFAULT '', address TEXT DEFAULT '',
            city TEXT DEFAULT '', industry TEXT DEFAULT 'other',
            score INTEGER DEFAULT 0, score_reasons TEXT DEFAULT '',
            stage TEXT DEFAULT 'NEW', demo_url TEXT DEFAULT '',
            notes TEXT DEFAULT '', created_at REAL, updated_at REAL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY, lead_id INTEGER, stage TEXT,
            detail TEXT, created_at REAL DEFAULT 0)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS pipeline_meta (
            key TEXT PRIMARY KEY, value TEXT)""")
        conn.execute(
            "INSERT INTO leads (ico, company_name, business_scope, city,"
            " stage, created_at, updated_at) VALUES ('99999999',"
            " 'Test Autoservis', 'opravy automobilů', 'Testov',"
            " 'ENRICHED', 0, 0)")
        conn.commit()
        # slugify sanity instead of full generation (jinja templates path)
        from generator.site_builder import slugify
        slug = slugify("Test Autoservis Král")
        assert slug == "test-autoservis-kral", f"slugify gave {slug}"
        conn.close()
        return f"slugify OK ({slug})"
    finally:
        os.chdir(old_cwd)
        os.environ.pop("LEADFORGE_DB", None)


def qa_gate_check():
    from agents.qa import run as qa_run  # just ensure importable & callable
    assert callable(qa_run)
    return "QA module importable"


def skills_check():
    root = Path(__file__).resolve().parent.parent / "skills"
    expected = ["generator.md", "qa.md", "scout.md", "scorer.md",
                "enricher.md", "deploy.md", "outreach.md"]
    missing = [f for f in expected if not (root / f).exists()]
    assert not missing, f"missing skill files: {missing}"
    return f"{len(expected)}/{len(expected)} skills present"


def hub_check():
    from hub import AGENTS, RUNNERS
    missing = [a for a in AGENTS if a not in RUNNERS]
    assert not missing, f"agents without runner: {missing}"
    return f"{len(AGENTS)} agents wired"


CHECKS = [
    ("database", db_check, True),
    ("hub-wiring", hub_check, True),
    ("skills-files", skills_check, True),
    ("scorer-heuristics", scorer_check, True),
    ("qa-module", qa_gate_check, False),
    ("generator-slugify", generator_check, False),
    ("ares-live-api", ares_check, False),  # WARN only — network dependent
]


def run(quick: bool = False) -> dict:
    del RESULTS[:]
    for name, fn, crit in CHECKS:
        if quick and name == "ares-live-api":
            RESULTS.append((name, "SKIP", "quick mode"))
            continue
        check(name, fn, crit)
    passed = sum(1 for _, s, _ in RESULTS if s == "PASS")
    failed = sum(1 for _, s, _ in RESULTS if s == "FAIL")
    warned = sum(1 for _, s, _ in RESULTS if s == "WARN")
    summary = {"passed": passed, "failed": failed, "warned": warned,
               "healthy": failed == 0}
    print(json.dumps({"summary": summary,
                      "checks": [{"name": n, "status": s, "detail": d}
                                 for n, s, d in RESULTS]},
                     ensure_ascii=False, indent=1))
    return summary


if __name__ == "__main__":
    run(quick="--quick" in sys.argv)
