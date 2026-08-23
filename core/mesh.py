"""Agent mesh — agents that ACT, moderated by Supervisor, stoppable by humans.

Core pieces:
  AGENT_TOOLS: per-agent action functions (real code, not just chat)
  run_agent_task(agent_key, task_text): LLM decides which tool to use,
      we execute it for real, agent reports result in its persona
  Control state in DB meta table: paused_agents / frozen / halted
  Red button: /pause @agent, /freeze, /red — only human IDs can set
"""

import json
import os
import sqlite3
import urllib.request
from pathlib import Path

from core.db import connect, funnel_report
from core.config import llm_chat
from core import telegram

# ---------------------------------------------------------------- control state

CONTROL_DEFAULTS = {"paused_agents": "[]", "frozen": "0", "halted": "0"}

HUMAN_IDS = {8774245514}  # Peter; add David's id when he messages the bot


def get_control(key: str):
    conn = connect()
    row = conn.execute("SELECT value FROM pipeline_meta WHERE key=?", (key,)).fetchone()
    if row is None:
        return json.loads(CONTROL_DEFAULTS.get(key, "null"))
    return json.loads(row["value"])


def set_control(key: str, value):
    conn = connect()
    conn.execute(
        "INSERT INTO pipeline_meta (key,value) VALUES (?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, json.dumps(value)),
    )
    conn.commit()


def agent_paused(agent_key: str) -> bool:
    return agent_key in get_control("paused_agents")


def chatter_allowed() -> bool:
    return not get_control("frozen") and not get_control("halted")


def pipeline_allowed() -> bool:
    return not get_control("halted")

# ---------------------------------------------------------------- real tools

def tool_fetch_site(url_or_name: str) -> str:
    """Download a live demo site (GitHub Pages or generated file) and return
    its text content + key SEO elements for evaluation."""
    import re
    import urllib.request as _u
    from pathlib import Path

    target = url_or_name.strip()
    html = ""
    if target.startswith("http"):
        try:
            req = _u.Request(target, headers={"User-Agent": "LeadForge-QA/0.1"})
            with _u.urlopen(req, timeout=15) as r:
                html = r.read(300_000).decode("utf-8", errors="ignore")
        except Exception as e:
            return f"fetch failed: {e}"
    else:
        from generator.site_builder import slugify
        conn = connect()
        # match on the ASCII slug too (handles Czech diacritics: Král -> kral)
        row = conn.execute(
            "SELECT company_name FROM leads WHERE id=? OR LOWER(company_name) LIKE ? "
            "OR LOWER(company_name) LIKE ?",
            (target if target.isdigit() else -1,
             f"%{target.lower()}%",
             f"%{target.lower().replace('kral','král').replace('novak','novák')}%")
        ).fetchone()
        if not row and len(target) > 3:
            # last resort: prefix match on slugified name
            rows = conn.execute("SELECT company_name FROM leads").fetchall()
            for r2 in rows:
                if slugify(r2["company_name"]).startswith(slugify(target)[:8]):
                    class W: company_name = r2["company_name"]
                    row = W
                    break
        if not row:
            return f"no lead matching '{target}'"
        p = Path(__file__).resolve().parent.parent / "generated" / slugify(row["company_name"]) / "index.html"
        if not p.exists():
            return f"no local file for '{target}'"
        html = p.read_text(encoding="utf-8")

    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | __import__("re").I)
    desc = re.search(r'name="description" content="([^"]*)"', html)
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S | __import__("re").I)
    services = re.findall(r"<li[^>]*>(.*?)</li>", html)
    body = re.sub(r"<style.*?</style>|<script.*?</script>", "", html, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", body)
    text = re.sub(r"\s+", " ", text).strip()
    has_schema = "ld+json" in html
    has_tel = "tel:" in html
    return (f"TITLE: {title.group(1).strip() if title else '-'}\n"
            f"META DESC: {desc.group(1) if desc else '-'}\n"
            f"H1: {h1.group(1).strip() if h1 else '-'}\n"
            f"SERVICES: {services}\n"
            f"HAS_SCHEMA: {has_schema} | HAS_TEL: {has_tel}\n"
            f"TEXT ({len(text)} chars): {text[:1500]}")


def tool_regenerate_site(lead_name_or_id: str) -> str:
    """Rebuild a lead's site through Generator + QA + Deploy chain."""
    from generator.site_builder import run as gen_run, slugify
    from agents import qa as qa_mod
    from deploy import ghpages

    conn = connect()
    row = conn.execute("SELECT * FROM leads WHERE id=? OR LOWER(company_name) LIKE ?",
                       (lead_name_or_id if str(lead_name_or_id).isdigit() else -1,
                        f"%{lead_name_or_id}%")).fetchone()
    if not row:
        return f"no lead matching '{lead_name_or_id}'"
    # force back into ENRICHED so generator picks it up
    conn.execute("UPDATE leads SET stage='ENRICHED' WHERE id=?", (row["id"],))
    conn.commit()

    gen = gen_run(use_llm=True)
    qa_res = qa_mod.run()
    lead2 = conn.execute("SELECT * FROM leads WHERE id=?", (row["id"],)).fetchone()
    deployed = ""
    if lead2["stage"] == "QA":
        ok, result = ghpages.deploy_lead(lead2)
        if ok:
            conn.execute("UPDATE leads SET demo_url=?, stage='DEPLOYED' WHERE id=?",
                         (result, row["id"]))
            conn.commit()
            deployed = result
    return (f"regenerated '{row['company_name']}' ({gen}), QA: {qa_res}. "
            f"Live: {deployed or 'not deployed (QA fail or error)'}")


def tool_list_leads() -> str:
    conn = connect()
    rows = conn.execute("SELECT id, company_name, score, stage FROM leads "
                        "WHERE stage NOT IN ('DISCARDED') ORDER BY score DESC").fetchall()
    return "\n".join(f"{r['id']}. {r['company_name']} [{r['stage']}] score={r['score']}"
                     for r in rows) or "no active leads"


def tool_show_lead(lead_ref: str) -> str:
    conn = connect()
    row = conn.execute("SELECT * FROM leads WHERE id=? OR LOWER(company_name) LIKE ?",
                       (lead_ref if str(lead_ref).isdigit() else -1, f"%{str(lead_ref).lower()}%")).fetchone()
    if not row:
        return f"no lead matching '{lead_ref}'"
    d = dict(row)
    d.pop("notes", None)
    return json.dumps(d, ensure_ascii=False, indent=1)


def tool_discard_lead(lead_ref: str) -> str:
    from core.db import advance
    conn = connect()
    row = conn.execute("SELECT * FROM leads WHERE id=?",
                       (lead_ref if str(lead_ref).isdigit() else -1,)).fetchone()
    if not row:
        return f"no lead #{lead_ref}"
    advance(conn, row["id"], "DISCARDED", "discarded by human via Telegram")
    conn.commit()
    return f"lead {row['id']} ({row['company_name']}) discarded"


TOOLS_BY_AGENT = {
    "generator": [tool_regenerate_site, tool_fetch_site],
    "qa": [tool_fetch_site, tool_show_lead],
    "supervisor": [tool_list_leads, tool_show_lead, tool_regenerate_site, tool_discard_lead, tool_fetch_site],
}

TOOL_MANIFEST = {
    "fetch_site(url_or_name)": "download and extract a live/generated site's content for review",
    "regenerate_site(name_or_id)": "rebuild a lead's website end-to-end (generate->QA->deploy)",
    "list_leads()": "list active leads with scores and stages",
    "show_lead(name_or_id)": "full details of one lead",
    "discard_lead(id)": "mark lead as discarded (human decisions only)",
}


def load_skill(agent_key: str) -> str:
    """Load skills/<agent>.md if it exists — teaches the agent without code."""
    p = Path(__file__).resolve().parent.parent / "skills" / f"{agent_key}.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def execute_tool(call: str) -> str:
    call = call.strip()
    name, _, argpart = call.partition("(")
    arg = argpart.rstrip(")").strip().strip("'\"")
    mapping = {
        "fetch_site": tool_fetch_site,
        "regenerate_site": tool_regenerate_site,
        "list_leads": lambda _: tool_list_leads(),
        "show_lead": tool_show_lead,
        "discard_lead": tool_discard_lead,
    }
    fn = mapping.get(name.strip())
    if not fn:
        return f"unknown tool '{name}'"
    try:
        return fn(arg)
    except Exception as e:
        return f"tool error: {e}"

# ---------------------------------------------------------------- agent reasoning

PERSONAS = {
    "supervisor": ("👑 Supervisor", "You coordinate the team, make strategy calls, keep quality high."),
    "scout": ("📥 Scout", "You find new Czech businesses in the RZP registry."),
    "scorer": ("⚖️ Scorer", "You rank leads by likelihood to buy a website."),
    "enricher": ("🔎 Enricher", "You find contact info and check existing websites."),
    "generator": ("🏗️ Generator", "You build single-page demo sites with great Czech copy and clean design."),
    "qa": ("🧪 QA", "You are the strict quality gate: leaks, hallucinations, bad design, broken links."),
    "deploy": ("🚀 Deploy", "You publish demos to GitHub Pages."),
    "outreach": ("✉️ Outreach", "You draft personalized Czech offer emails; nothing sends without human approval."),
}


def system_prompt(agent_key: str, extra_context: str = "") -> str:
    title, persona = PERSONAS[agent_key]
    tools = ", ".join(t.__name__ for t in TOOLS_BY_AGENT.get(agent_key, [])) or "none"
    skill = load_skill(agent_key)
    return (
        f"You are {title} of LeadForge (model ox-alpha). {persona}\n"
        f"Available tools: {tools}. Tool manifest: {json.dumps(TOOL_MANIFEST, ensure_ascii=False)}\n"
        + (f"\n=== YOUR SKILL FILE ===\n{skill}\n=== END SKILL ===\n" if skill else "")
        + "\nIf a tool would accomplish the request, reply ONLY with TOOL_CALL: <call>.\n"
        "Otherwise answer briefly in your own voice (Czech if user writes Czech), max 3 sentences."
        + (f"\nContext: {extra_context}" if extra_context else "")
    )


def run_agent_task(agent_key: str, task_text: str) -> tuple[str, bool]:
    """Returns (reply_text, acted_bool). Executes at most ONE tool call."""
    conn = connect()
    funnel = {k: v for k, v in funnel_report(conn).items() if v}
    prompt = system_prompt(agent_key, json.dumps(funnel, ensure_ascii=False))
    out = llm_chat([{"role": "system", "content": prompt},
                    {"role": "user", "content": task_text}], max_tokens=350, temperature=0.4)
    if out.strip().startswith("TOOL_CALL:"):
        result = execute_tool(out.split(":", 1)[1])
        title = PERSONAS[agent_key][0]
        summary = llm_chat(
            [{"role": "system", "content":
                f"You are {title}. You executed a tool. Report the outcome in 1-2 short sentences, your voice."},
             {"role": "user", "content": f"Task: {task_text}\nTool output: {result}"}],
            max_tokens=150, temperature=0.4)
        return summary, True
    return out, False


# ---------------------------------------------------------------- moderation

MODERATOR_PROMPT = (
    "You moderate an agent team chat about web-lead generation. Given an agent message, "
    "decide: POST it (useful, clear), EDIT it (repost shorter/clearer version), or DROP it "
    "(empty, repetitive, off-topic). Reply as JSON: {\"action\":\"post|edit|drop\",\"text\":\"...\"}"
)


def moderate(agent_title: str, text: str) -> str | None:
    try:
        raw = llm_chat([{"role": "system", "content": MODERATOR_PROMPT},
                        {"role": "user", "content": f"Agent: {agent_title}\nMessage: {text}"}],
                       max_tokens=250, temperature=0.0)
        data = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
        if data["action"] == "drop":
            return None
        return data.get("text") or text
    except Exception:
        return text  # moderator down -> post as-is rather than lose message
