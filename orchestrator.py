"""Orchestrator — continuous pipeline loop.

Repeatedly finds leads stuck at a stage and pushes them through the next
agent until no progress is possible. Stages requiring external resources
(live RZP, LLM key, deployment target) are skipped gracefully with a note.

Usage:
  python3 orchestrator.py --once     # single sweep
  python3 orchestrator.py --loop --interval 300   # continuous mode
"""

import argparse
import time
import traceback

from core.db import connect, funnel_report, recent_events
from core.telegram import post, status_digest
from agents import scout, scorer, enricher, qa
from generator import site_builder

AGENT_FOR_STAGE = {
    "scout": "Scout", "score": "Scorer", "enrich": "Enricher",
    "generate": "Generator", "qa": "QA", "deploy": "Deploy",
}


def sweep(use_llm: bool = False) -> dict:
    """One pass over all stages. Returns per-stage action summary."""
    actions = {}
    steps = [
        ("scout", lambda: {"scouted": len(scout.run())}),
        ("score", scorer.run),
        ("enrich", enricher.run),
        ("generate", lambda: site_builder.run(use_llm=use_llm)),
        ("qa", qa.run),
    ]
    for name, fn in steps:
        try:
            result = fn()
            actions[name] = result
            post(AGENT_FOR_STAGE[name], f"{result}")
        except Exception as e:
            actions[name] = {"error": str(e)}
            post(AGENT_FOR_STAGE[name], f"⚠️ error: {e}")
            traceback.print_exc()
    return actions


def deploy_step(conn) -> int:
    """Deploy QA-passed sites. Local 'deploy' for now: mark DEPLOYED with file path.
    Real deployment (rsync to VPS) plugs in here."""
    from core.db import advance
    n = 0
    for lead in conn.execute("SELECT * FROM leads WHERE stage='QA'").fetchall():
        slug = lead["demo_url"].rstrip("/").split("/")[-1] if lead["demo_url"] else ""
        conn.execute("UPDATE leads SET demo_url=? WHERE id=?",
                     (f"file://{slug}/index.html", lead["id"]))
        advance(conn, lead["id"], "DEPLOYED", f"demo ready: {slug}")
        n += 1
    conn.commit()
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--interval", type=int, default=300)
    ap.add_argument("--llm", action="store_true", help="use LLM copy generation")
    args = ap.parse_args()

    while True:
        print(f"\n=== sweep {time.strftime('%H:%M:%S')} ===")
        actions = sweep(use_llm=args.llm)
        for k, v in actions.items():
            print(f"  {k}: {v}")
        conn = connect()
        n = deploy_step(conn)
        if n:
            post("Deploy", f"🚀 {n} demo(s) deployed")
        print(f"  deploy: {n}")
        report = funnel_report(conn)
        total = sum(report.values())
        post("Supervisor", status_digest(report, total))
        print("  funnel:", {k: v for k, v in report.items() if v})
        for e in recent_events(conn, 3):
            print(f"    · [{e['company_name']}] {e['stage']}: {e['detail']}")
        conn.close()
        if not args.loop:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
