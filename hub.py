"""Agent Hub — ox-alpha as main orchestrator.

Agents report to the hub, receive tasks from it, and are configured via
skills/<agent>.md files. No LLM key required for routing; agents run real
pipeline code.

Usage:
  python3 hub.py status
  python3 hub.py ask <agent> "<task>"
  python3 hub.py sweep                 # run all agents in order, collect reports
  python3 hub.py skill show <agent>
  python3 hub.py skill set <agent> <file.md>
  python3 hub.py skill append <agent> <file.md>
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core import mesh
from core.db import connect, funnel_report, recent_events

ROOT = Path(__file__).resolve().parent
SKILLS = ROOT / "skills"

AGENTS = ["scout", "scorer", "enricher", "generator", "qa", "deploy", "outreach"]


# ---------------------------------------------------------------- agent runners

def _run_scout(task: str) -> str:
    try:
        from agents import live_scout as scout_mod
        r = scout_mod.run()
        return f"scout: {r}"
    except Exception:
        from agents import scout as scout_sample
        n = len(scout_sample.run())
        return f"scouted {n} lead(s) (sample fallback)"


def _run_scorer(task: str) -> str:
    from agents import scorer
    return f"scored: {scorer.run()}"


def _run_enricher(task: str) -> str:
    from agents import enricher
    return f"enriched: {enricher.run()}"


def _run_generator(task: str) -> str:
    from generator import site_builder
    use_llm = "llm" in task.lower()
    return f"generated: {site_builder.run(use_llm=use_llm)}"


def _run_qa(task: str) -> str:
    from agents import qa
    return f"qa: {qa.run()}"


def _run_deploy(task: str) -> str:
    conn = connect()
    from orchestrator import deploy_step
    n = deploy_step(conn)
    conn.close()
    return f"deployed {n} demo(s)"


def _run_outreach(task: str) -> str:
    conn = connect()
    rows = conn.execute(
        "SELECT id, company_name FROM leads WHERE stage='DEPLOYED'").fetchall()
    conn.close()
    if not rows:
        return "no deployed leads awaiting outreach"
    return ("awaiting human approval for " + ", ".join(
        f"#{r['id']} {r['company_name']}" for r in rows))


RUNNERS = {
    "scout": _run_scout, "scorer": _run_scorer, "enricher": _run_enricher,
    "generator": _run_generator, "qa": _run_qa, "deploy": _run_deploy,
    "outreach": _run_outreach,
}


# ---------------------------------------------------------------- hub API

def report(agent_key: str, text: str):
    """Agent -> hub report channel (printed + logged to DB events)."""
    title = mesh.PERSONAS.get(agent_key, (agent_key,))[0]
    print(f"[{title} -> hub] {text}")
    try:
        conn = connect()
        conn.execute(
            "INSERT INTO events (lead_id, stage, detail) VALUES (NULL, 'HUB', ?)",
            (f"{agent_key}: {text}",))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"(hub log skipped: {e})", file=sys.stderr)


def call_agent(agent_key: str, task: str = "") -> str:
    """Hub -> agent dispatch. Runs the agent's real code, returns its report."""
    if agent_key not in RUNNERS:
        return f"unknown agent '{agent_key}'. known: {', '.join(AGENTS)}"
    if mesh.agent_paused(agent_key):
        return f"{agent_key} is paused (/resume to unpause)"
    if not mesh.pipeline_allowed():
        return "pipeline halted (/resume to restart)"
    try:
        result = RUNNERS[agent_key](task)
        report(agent_key, result)
        return result
    except Exception as e:
        report(agent_key, f"error: {e}")
        return f"{agent_key} failed: {e}"


def sweep() -> dict:
    """Run every agent once in pipeline order; collect reports."""
    out = {}
    for agent in AGENTS[:-1]:  # outreach needs approval, not auto-run
        out[agent] = call_agent(agent)
    conn = connect()
    fr = funnel_report(conn)
    events = recent_events(conn, 5)
    conn.close()
    out["funnel"] = {k: v for k, v in fr.items() if v}
    out["recent_events"] = [f"[{e['company_name']}] {e['stage']}: {e['detail']}" for e in events]
    return out


# ---------------------------------------------------------------- skills mgmt

def skill_path(agent_key: str) -> Path:
    return SKILLS / f"{agent_key}.md"


def skill_show(agent_key: str) -> str:
    p = skill_path(agent_key)
    if not p.exists():
        return f"(no skill file for {agent_key})"
    return p.read_text(encoding="utf-8")


def skill_set(agent_key: str, src: str, append: bool = False) -> str:
    p = skill_path(agent_key)
    SKILLS.mkdir(exist_ok=True)
    new_text = Path(src).read_text(encoding="utf-8")
    if append and p.exists():
        p.write_text(p.read_text(encoding="utf-8") + "\n\n" + new_text, encoding="utf-8")
    else:
        p.write_text(new_text, encoding="utf-8")
    return f"skill {'appended to' if append else 'written for'} {agent_key} ({p})"


# ---------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(description="LeadForge agent hub")
    ap.add_argument("cmd", choices=["status", "ask", "sweep", "skill"])
    ap.add_argument("args", nargs="*")
    a = ap.parse_args()

    if a.cmd == "status":
        conn = connect()
        fr = funnel_report(conn)
        print(json.dumps({"funnel": {k: v for k, v in fr.items() if v}},
                         ensure_ascii=False, indent=1))
        for e in recent_events(conn, 10):
            print(f"· [{e['company_name']}] {e['stage']}: {e['detail']}")
        conn.close()
    elif a.cmd == "ask":
        agent, task = a.args[0], " ".join(a.args[1:])
        print(call_agent(agent, task))
    elif a.cmd == "sweep":
        print(json.dumps(sweep(), ensure_ascii=False, indent=1))
    elif a.cmd == "skill":
        action, agent = a.args[0], a.args[1]
        if action == "show":
            print(skill_show(agent))
        elif action == "set":
            print(skill_set(agent, a.args[2]))
        elif action == "append":
            print(skill_set(agent, a.args[2], append=True))


if __name__ == "__main__":
    main()
