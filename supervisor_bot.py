"""Supervisor bot — two-way Telegram control of the pipeline.

Polls getUpdates, executes commands, replies in-chat.
Free-text messages are handled by the LLM (ox-alpha persona) with pipeline
tools: it can query the DB, trigger sweeps, regenerate leads, etc.

Commands:
  /status  — funnel digest
  /leads   — table of active leads
  /sweep   — run one orchestrator pass now
  /help    — list commands
Anything else → Supervisor LLM.
"""

import json
import os
import sqlite3
import time
import urllib.request

from core import telegram
from core.db import connect, funnel_report, recent_events
from core.config import llm_chat

TOKEN = telegram.TOKEN
OFFSET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "tg_offset")


def tg_api(method: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TOKEN}/{method}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    timeout = payload.get("timeout", 0) or 15
    with urllib.request.urlopen(req, timeout=timeout + 10) as r:
        return json.load(r)


def reply(chat_id: int, text: str):
    tg_api("sendMessage", {
        "chat_id": chat_id, "text": text[:4000],
        "parse_mode": "HTML", "disable_web_page_preview": True,
    })


def cmd_status() -> str:
    conn = connect()
    funnel = funnel_report(conn)
    total = sum(funnel.values())
    lines = [f"<b>LeadForge status</b> — {total} leads"]
    lines += [f"• {s}: {n}" for s, n in funnel.items() if n]
    lines.append("")
    for e in recent_events(conn, 5):
        lines.append(f"· {e['company_name']} → {e['stage']}")
    return "\n".join(lines)


def cmd_leads() -> str:
    conn = connect()
    rows = conn.execute(
        "SELECT id, company_name, industry, score, stage FROM leads "
        "WHERE stage NOT IN ('DISCARDED') ORDER BY score DESC LIMIT 15"
    ).fetchall()
    if not rows:
        return "No active leads."
    lines = ["<b>Active leads</b>"]
    lines += [f"{r['id']}. {r['company_name']} — {r['industry']}, score {r['score']}, {r['stage']}" for r in rows]
    return "\n".join(lines)


def cmd_sweep() -> str:
    from orchestrator import sweep, deploy_step
    conn = connect()
    actions = sweep(use_llm=True)
    n = deploy_step(conn)
    lines = [f"<b>Sweep done</b> — deployed {n}"]
    for k, v in actions.items():
        lines.append(f"• {k}: {v}")
    return "\n".join(lines)


def cmd_pause(arg: str = "") -> str:
    """arg: agent key or empty. /pause generator | /pause (list)"""
    from core import mesh
    TEAM = mesh.TEAM if hasattr(mesh, "TEAM") else globals()["TEAM"]
    if not arg:
        paused = mesh.get_control("paused_agents")
        return f"Paused agents: {paused or 'none'}"
    key = arg.strip().lstrip("@").lower()
    if key not in TEAM:
        return f"Unknown agent '{key}'. /team"
    paused = set(mesh.get_control("paused_agents")); paused.add(key)
    mesh.set_control("paused_agents", sorted(paused))
    return f"⏸️ {TEAM[key][0]} paused — will not respond until /resume {key}"


def cmd_resume(arg: str = "") -> str:
    from core import mesh
    TEAM = mesh.TEAM if hasattr(mesh, "TEAM") else globals()["TEAM"]
    key = arg.strip().lstrip("@").lower()
    if key == "all":
        mesh.set_control("paused_agents", [])
        return "✅ all agents resumed"
    if key not in TEAM:
        return f"Unknown agent '{key}'. /team"
    paused = [a for a in mesh.get_control("paused_agents") if a != key]
    mesh.set_control("paused_agents", paused)
    return f"▶️ {TEAM[key][0]} resumed"


def cmd_freeze() -> str:
    from core.mesh import set_control
    set_control("frozen", 1)
    return "🧊 FROZEN — agent chatter stopped; pipeline continues silently. /unfreeze to restore"


def cmd_unfreeze() -> str:
    from core.mesh import set_control
    set_control("frozen", 0)
    return "✅ chatter restored"


def cmd_red() -> str:
    from core.mesh import set_control
    set_control("halted", 1)
    telegram.post("Supervisor", "🚨 RED BUTTON PRESSED — full stop. Only humans can /resume.")
    return "🚨 HALTED. Pipeline loops and agents are stopped. /resume to restart."


def cmd_resume_all() -> str:
    from core.mesh import set_control
    set_control("halted", 0); set_control("frozen", 0); set_control("paused_agents", [])
    telegram.post("Supervisor", "▶️ Resumed — team back online.")
    return "✅ everything resumed"


SUPERVISOR_SYSTEM = """You are the Supervisor agent of LeadForge — an automated system that
finds Czech businesses without websites, builds demo sites, and sells web packages.
You are running as model ox-alpha. You talk to the project owner (Peter) in his
Telegram ops chat. Style: concise, concrete, friendly, technical when needed.
You have already-run command results available; if the user asks something you
cannot answer without data, say what command gives it (/status /leads /sweep).
Answer in the language the user writes in (usually Czech or English)."""

TEAM = {
    "supervisor": ("👑 Supervisor", "orchestration, corrections, strategy — that's me"),
    "scout": ("📥 Scout", "finds new businesses in RZP registry"),
    "scorer": ("⚖️ Scorer", "ranks leads by likelihood to buy"),
    "enricher": ("🔎 Enricher", "scrapes contacts & checks existing websites"),
    "generator": ("🏗️ Generator", "builds demo websites with Czech copy"),
    "qa": ("🧪 QA", "quality gate before anything goes live"),
    "deploy": ("🚀 Deploy", "publishes demos"),
    "outreach": ("✉️ Outreach", "drafts offer emails for your approval — coming soon"),
}

AGENT_PERSONAS = {
    "scout": "You are Scout from LeadForge: you find new Czech businesses in the RZP registry. Short, factual replies about sourcing/leads.",
    "scorer": "You are Scorer from LeadForge: you rank leads by likelihood to buy a website. Talk in scores, reasons, conversion logic.",
    "enricher": "You are Enricher from LeadForge: you find contact details and check which businesses already have websites.",
    "generator": "You are Generator from LeadForge: you build single-page demo websites with AI-written Czech copy.",
    "qa": "You are QA from LeadForge: strict quality gate. You check generated sites for leaks, hallucinated claims, missing contacts.",
    "deploy": "You are Deploy from LeadForge: you publish demo sites and track their URLs.",
}


def cmd_team() -> str:
    lines = ["<b>LeadForge team</b> — tag an agent like <code>@qa recheck autoservis-kral</code>:"]
    lines += [f"{title} — {desc}" for title, desc in TEAM.values()]
    return "\n".join(lines)


def route_message(text: str) -> tuple[str | None, str]:
    """Returns (agent_key_or_None, clean_text). Detects '@agent ...' prefix."""
    low = text.lower()
    for key in TEAM:
        if low.startswith(f"@{key} ") or low.startswith(f"@{key}:"):
            return key, text.split(" ", 1)[1] if " " in text else ""
    return None, text


def agent_answer(agent_key: str, user_text: str) -> str:
    persona = AGENT_PERSONAS.get(agent_key, SUPERVISOR_SYSTEM)
    conn = connect()
    funnel = {k: v for k, v in funnel_report(conn).items() if v}
    context = f"\nPipeline state: {json.dumps(funnel)}."
    title = TEAM[agent_key][0]
    return llm_chat(
        [{"role": "system", "content": f"{persona}{context}\nSign off briefly as {title}."},
         {"role": "user", "content": user_text}],
        max_tokens=300, temperature=0.6,
    )


def supervisor_answer(user_text: str) -> str:
    conn = connect()
    funnel = {k: v for k, v in funnel_report(conn).items() if v}
    context = f"Current pipeline state: {json.dumps(funnel)}."
    return llm_chat(
        [{"role": "system", "content": SUPERVISOR_SYSTEM + "\n" + context},
         {"role": "user", "content": user_text}],
        max_tokens=400, temperature=0.5,
    )


def cmd_outreach(arg: str = "") -> str:
    """/outreach draft <lead> | /outreach approve <id> | /outreach send <id> <email> | /outreach list"""
    import outreach
    parts = arg.split(None, 2)
    if not parts:
        return outreach.list_drafts()
    sub = parts[0].lower()
    if sub == "list":
        return outreach.list_drafts()
    if sub == "draft" and len(parts) > 1:
        d = outreach.draft_for(parts[1])
        if not d:
            return "lead not found or not DEPLOYED"
        return (f"✉️ DRAFT #{d['draft_id']} — {d['lead']} [PENDING]\n"
                f"Subject: {d['subject']}\n\n{d['body']}\n\n"
                f"Demo: {d['demo']}\nApprove: /outreach approve {d['draft_id']}")
    if sub == "approve" and len(parts) > 1:
        # human-only check happens via HUMAN_IDS in handle_message
        return outreach.approve(int(parts[1]), "telegram-human")
    if sub == "send" and len(parts) >= 2:
        recipient = parts[2] if len(parts) > 2 else "unknown@pending"
        return outreach.send(int(parts[1]), recipient)
    return "usage: /outreach draft <lead> | list | approve <id> | send <id> <email>"


COMMANDS = {
    "/status": cmd_status, "/leads": cmd_leads, "/sweep": cmd_sweep,
    "/team": cmd_team,
    "/pause": cmd_pause, "/resume": cmd_resume,
    "/freeze": cmd_freeze, "/unfreeze": cmd_unfreeze,
    "/red": cmd_red,
    "/outreach": cmd_outreach,
    "/help": lambda: ("Commands: /status /leads /sweep /team\n"
                      "Outreach: /outreach draft <lead> · /outreach approve <id> · "
                      "/outreach send <id> <email> (needs approval) · /outreach list\n"
                      "Control: /pause @agent · /resume @agent|all · /freeze · /unfreeze · /red · /resume (full)\n"
                      "@agent ... talks to a specific agent.\n"
                      "Anything else goes to the Supervisor."),
}


def read_offset() -> int:
    try:
        return int(open(OFFSET_FILE).read().strip())
    except Exception:
        return 0


def write_offset(v: int):
    os.makedirs(os.path.dirname(os.path.abspath(OFFSET_FILE)), exist_ok=True)
    with open(OFFSET_FILE, "w") as f:
        f.write(str(v))


def handle_message(chat_id: int, text: str, from_id: int):
    print(f"<- {text}")
    try:
        if text.startswith("/"):
            cmd, _, arg = text.partition(" ")
            fn = COMMANDS.get(cmd.split("@")[0])
            out = fn(arg.strip()) if fn else "Unknown command. /help"
        else:
            agent_key, clean = route_message(text)
            from core import mesh
            if agent_key:
                if mesh.agent_paused(agent_key):
                    out = f"⏸️ {mesh.TEAM[agent_key][0]} is paused. /resume {agent_key}"
                elif not mesh.chatter_allowed():
                    out = ("🔇 Agent chat is muted (freeze/red active). "
                           "Use /unfreeze or /resume.")
                else:
                    answer, acted = mesh.run_agent_task(agent_key, clean)
                    moderated = mesh.moderate(mesh.TEAM[agent_key][0], answer)
                    if moderated is None:
                        out = f"({mesh.TEAM[agent_key][0]} had nothing useful to add)"
                    else:
                        telegram.post(mesh.TEAM[agent_key][0], moderated)
                        out = moderated  # avoid double-posting to same chat
            else:
                if not mesh.pipeline_allowed() and from_id not in mesh.HUMAN_IDS:
                    out = "🚨 system halted by red button."
                else:
                    out = supervisor_answer(text)
    except Exception as e:
        out = f"⚠️ {e}"
    reply(chat_id, out)
    print("-> replied")


def poll_once():
    offset = read_offset()
    data = tg_api("getUpdates", {"offset": offset + 1, "timeout": 25})
    for u in data.get("result", []):
        write_offset(u["update_id"])
        msg = u.get("message", {})
        chat_id = msg.get("chat", {}).get("id")
        from_id = msg.get("from", {}).get("id", 0)
        text = (msg.get("text") or "").strip()
        if not chat_id or not text:
            continue
        # auto-allowlist any human who talks to the bot
        if from_id and not msg.get("from", {}).get("is_bot"):
            from core.mesh import HUMAN_IDS
            HUMAN_IDS.add(from_id)
        handle_message(chat_id, text, from_id)


def main():
    telegram.post("Supervisor", "Supervisor online. Commands: /status /leads /sweep /help — or just talk to me.")
    while True:
        try:
            poll_once()
        except Exception as e:
            print("poll error:", e)
            time.sleep(5)


if __name__ == "__main__":
    main()
