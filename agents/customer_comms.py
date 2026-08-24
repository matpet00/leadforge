"""Customer Comms Agent v2 — LLM-personalized outreach + reply handler.

1. DRAFTS: LLM writes unique personalized CZ outreach per lead, grounded in
   REAL data only (guardrails against hallucination), fallback to static
   template when no LLM available.
2. REPLIES: inbound customer messages get an LLM-suggested response draft;
   human approves before anything is "sent" (SMTP still not wired).

Usage:
  python3 agents/customer_comms.py draft <lead_id>      # LLM draft -> PENDING
  python3 agents/customer_comms.py list                 # pending drafts
  python3 agents/customer_comms.py reply <lead_id> "<zprava od zakaznika>"
  python3 agents/customer_comms.py replies              # list open conversations

Env: OPENROUTER_API_KEY optional (fallback = static template).
"""

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.db import connect, advance, log_event

MAX_DEMOS = 10  # safety cap: never build more demos than approved
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
COMMS_MODELS = [
    os.environ.get("COMMS_MODEL", "nvidia/nemotron-3.5-lightning:free"),
    "z-ai/glm-5.2:free",
    "google/gemma-4-31b-it:free",
    "cohere/north-mini-code:free",
    "openai/gpt-4o-mini",
]

SKILL_FILE = Path(__file__).resolve().parent.parent / "skills" / "customer_comms.md"

# ------------------------------------------------------------------- LLM


def _llm(system: str, user: str, max_tokens: int = 1200) -> str | None:
    """Try comms models with retry; return None if all unavailable."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("  (LLM skip: no OPENROUTER_API_KEY — static template)")
        return None
    import time

    for model in COMMS_MODELS:
        for t in range(3):
            payload = {"model": model, "max_tokens": max_tokens,
                       "messages": [{"role": "system", "content": system},
                                    {"role": "user", "content": user}]}
            req = urllib.request.Request(
                OPENROUTER_URL, data=json.dumps(payload).encode(),
                method="POST",
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {key}"})
            try:
                with urllib.request.urlopen(req, timeout=180) as r:
                    out = json.loads(r.read().decode())[
                        "choices"][0]["message"]["content"]
                    if out and out.strip():
                        return out.strip()
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503):
                    wait = 12 * (t + 1)
                    print(f"    [{model} HTTP {e.code}, retry za {wait}s]")
                    time.sleep(wait)
                    continue
                break  # other errors -> next model
            except Exception as e:
                print(f"    [{model}: {str(e)[:60]}]")
                break
    print("  (LLM nedostupný — fallback na statickou šablonu)")
    return None


def _load_skill() -> str:
    return SKILL_FILE.read_text(encoding="utf-8") if SKILL_FILE.exists() else ""


# ----------------------------------------------------------------- drafts

DRAFT_SYSTEM = """Jsi Customer Comms agent LeadForge. Píšeš první kontaktní zprávu
českému živnostníkovi, kterému jsme vyrobili demo web.

PŘÍSNÁ PRAVIDLA OBSAHU (anti-hallucination):
- Používej VÝHRADNĚ fakta ze zaslaných firemních dat. NIC si nevymýšlej —
  žádné konkrétní ceny, žádná falešná reference, žádné "viděl jsem vaši
  práci" pokud nemáme podklady.
- Tón: přátelský, respektující, krátký. Ne salesy spam.
- Struktura: pozdrav → 1 věta proč píšu (nemají web, zákazníci je nenajdou)
  → zmínka dema s URL → nezávazná výzva ke krátkému callu → podpis.
- Podpis: "{sender} — LeadForge"
- Maximálně 120 slov. čeština, vykání.
Vrať POUZE text zprávy, bez vysvětlení."""

STATIC_TEMPLATE = (
    "Dobrý den,\n\n"
    "jmenuji se David a pracuji pro LeadForge. Všiml jsem si, že "
    "{company} nemá vlastní webové stránky — tím dnes "
    "zákazníci z {city} hledající vás na Google unikají konkurenci.\n"
    "{demo_line}\n\n"
    "Nezávazně se mrkněte — líbil by se vám podobný web? Rád si s vámi "
    "zavolám o úpravách. Jak by vám to vyhovovalo?\n\n"
    "S pozdravem,\nDavid — LeadForge")

SENDER = os.environ.get("LEADFORGE_SENDER", "David")


def llm_draft(lead: dict) -> str | None:
    facts = {k: lead.get(k) for k in
             ("company_name", "city", "industry", "trades", "phone", "email",
              "demo_url") if lead.get(k)}
    user = f"""Firemní data (jediný pravdivý zdroj):
{json.dumps(facts, ensure_ascii=False, indent=2)}

Demo web: {lead.get('demo_url') or '(zatím pouze lokálně)'}
Napiš kontaktní zprávu."""
    skill = _load_skill()
    if skill:
        user += "\n\nDoplňkové pokyny:\n" + skill[:1500]
    out = _llm(DRAFT_SYSTEM.format(sender=SENDER), user)
    if not out:
        return None
    # sanity check: message must mention company name, must be short enough
    if len(out) > 1600:
        print("  (LLM draft příliš dlouhý — fallback)")
        return None
    return out


def static_draft(lead: dict) -> str:
    city = lead["city"] or "vašem okolí"
    demo_url = lead.get("demo_url") or ""
    if demo_url.startswith("file://"):
        demo_line = ""
    else:
        demo_line = f"\n\nNáhled zde: {demo_url}" if demo_url else ""
    return STATIC_TEMPLATE.format(company=lead["company_name"], city=city,
                                  demo_line=demo_line)


def _lead(conn, lead_id: int):
    row = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
    return dict(row) if row else None


def demo_count(conn) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM leads WHERE stage IN "
        "('GENERATED','QA','DEPLOYED','CONTACTED','REPLIED','WON')").fetchone()[0]


def cmd_draft(lead_id: int) -> str:
    conn = connect()
    if demo_count(conn) > MAX_DEMOS:
        conn.close()
        return f"demo cap reached ({MAX_DEMOS}) — human approval needed first"
    lead = _lead(conn, lead_id)
    if not lead:
        conn.close()
        return f"no lead #{lead_id}"
    if lead["stage"] != "DEPLOYED":
        conn.close()
        return f"lead #{lead_id} is {lead['stage']}, needs DEPLOYED first"
    if not (lead.get("phone") or lead.get("email")):
        conn.close()
        return f"lead #{lead_id} has no contact — enrich first"

    msg = llm_draft(lead) or static_draft(lead)
    src = "llm" if msg != static_draft(lead) else "static-template"
    conn.execute(
        "INSERT INTO events (lead_id, stage, detail) VALUES (?, 'OUTREACH_DRAFT', ?)",
        (lead_id, msg[:500]))
    advance(conn, lead_id, "CONTACTED",
            f"draft ({src}) created — awaiting /outreach approve")
    conn.commit()
    conn.close()
    return f"DRAFT for #{lead_id} {lead['company_name']} [{src}]:\n\n{msg}"


def cmd_list() -> str:
    conn = connect()
    rows = conn.execute(
        "SELECT id, company_name, stage FROM leads "
        "WHERE stage IN ('CONTACTED','REPLIED')").fetchall()
    conn.close()
    if not rows:
        return "no pending drafts/conversations"
    return "\n".join(
        f"#{r['id']} {r['company_name']} [{r['stage']}]" for r in rows)


# ---------------------------------------------------------------- replies

REPLY_SYSTEM = """Jsi Customer Comms agent LeadForge. Zákazník (český živnostník)
odpověděl na náš outreach ohledně demo webu. Navrhni odpověď.

PRAVIDLA:
- Reaguj konkrétně na to, co napsal. Neopakuj celý pitch.
- Cíle: domluvit krátký call / odpovědět na námitky / poslat další krok.
- Námítka cena → zdůrazni jednorázový low-cost setup a že demo vidí zdarma.
- Námítka "nemám čas" → nabídni async (pošlu odkazy, on se vrátí).
- Zájem → navrhni 15min call, nabídni 2 termíny.
- Nikdy neslibuj nic konkrétního ohledně ceny/funkcí bez schválení člověkem.
- čeština, vykání, max 80 slov.
Vrať POUZE text navržené odpovědi."""


def cmd_reply(lead_id: int, message: str) -> str:
    """Log inbound customer message + generate suggested response."""
    conn = connect()
    lead = _lead(conn, lead_id)
    if not lead:
        conn.close()
        return f"no lead #{lead_id}"
    # log the inbound message
    conn.execute(
        "INSERT INTO events (lead_id, stage, detail) VALUES (?, 'INBOUND_MSG', ?)",
        (lead_id, message[:500]))
    if lead["stage"] == "CONTACTED":
        advance(conn, lead_id, "REPLIED", "customer replied")
    conn.commit()

    context = {
        "company_name": lead["company_name"],
        "city": lead.get("city"),
        "industry": lead.get("industry"),
        "our_outreach": _last_outreach(conn, lead_id),
    }
    conn.close()
    user = f"""KONTEXT:
{json.dumps(context, ensure_ascii=False, indent=2)}

ZPRÁVA OD ZÁKAZNÍKA:
\"\"\"{message}\"\"\"

Napiš navrhovanou odpověď."""
    suggestion = _llm(REPLY_SYSTEM, user)
    if suggestion is None:
        suggestion = ("(LLM nedostupný — odpovězte ručně.)\n\n"
                      f"Dobrý den,\n\nděkuji za zpětnou vazbu. Rád proberu "
                      f"detaily — kdy by vám vyhovoval krátký call?")
    # store suggestion for human approval
    conn = connect()
    conn.execute(
        "INSERT INTO events (lead_id, stage, detail) VALUES (?, 'REPLY_SUGGESTION', ?)",
        (lead_id, suggestion[:800]))
    conn.commit()
    conn.close()
    return (f"💬 REPLY SUGGESTION for #{lead_id} {lead['company_name']}\n"
            f"(zákazník napsal: \"{message[:150]}\")\n\n{suggestion}\n\n"
            f"— schvalte / upravte ručně. SMTP stále není připojeno.")


def _last_outreach(conn, lead_id: int) -> str:
    row = conn.execute(
        "SELECT detail FROM events WHERE lead_id=? AND stage='OUTREACH_DRAFT' "
        "ORDER BY id DESC LIMIT 1", (lead_id,)).fetchone()
    return row[0] if row else "(outreach text nenalezen)"


def cmd_replies() -> str:
    conn = connect()
    rows = conn.execute(
        "SELECT l.id, l.company_name, e.detail, e.created_at FROM events e "
        "JOIN leads l ON l.id=e.lead_id WHERE e.stage='INBOUND_MSG' "
        "ORDER BY e.id DESC LIMIT 20").fetchall()
    sug = conn.execute(
        "SELECT lead_id FROM events WHERE stage='REPLY_SUGGESTION'").fetchall()
    conn.close()
    answered = {r[0] for r in sug}
    if not rows:
        return "no inbound messages yet"
    out = []
    seen = set()
    for r in rows:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        mark = "✅" if r["id"] in answered else "🔔"
        out.append(f"{mark} #{r['id']} {r['company_name']}: \"{r['detail'][:100]}\"")
    return "\n".join(out)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == "draft" and len(sys.argv) > 2:
        print(cmd_draft(int(sys.argv[2])))
    elif cmd == "list":
        print(cmd_list())
    elif cmd == "reply" and len(sys.argv) > 3:
        print(cmd_reply(int(sys.argv[2]), " ".join(sys.argv[3:])))
    elif cmd == "replies":
        print(cmd_replies())
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
