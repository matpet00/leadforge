"""Customer Comms Agent — talks to potential customers (human-approved).

Generates personalized Czech outreach messages for DEPLOYED leads and
handles reply flows. NOTHING sends without human approval via the hub.

Usage:
  python3 agents/customer_comms.py draft <lead_id>   # generate draft, save PENDING
  python3 agents/customer_comms.py list              # pending drafts
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.db import connect, advance, log_event

MAX_DEMOS = 10  # safety cap: never build more demos than approved


def _lead(conn, lead_id: int):
    row = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
    return dict(row) if row else None


def demo_count(conn) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM leads WHERE stage IN ('GENERATED','QA','DEPLOYED','CONTACTED','REPLIED','WON')").fetchone()[0]


def draft_message(lead: dict) -> str:
    """Personalized first-contact message. Static template (LLM optional later)."""
    city = lead["city"] or "vašem okolí"
    demo_url = lead["demo_url"] or ""
    if demo_url.startswith("file://"):
        demo_link = "(demo připraveno — link po schválení)"
        demo_line = ""
    else:
        demo_link = demo_url
        demo_line = f"\n\nNáhled zde: {demo_link}"
    return (
        f"Dobrý den,\n\n"
        f"jmenuji se David a pracuji pro LeadForge. Všiml jsem si, že "
        f"{lead['company_name']} nemá vlastní webové stránky — tím dnes "
        f"zákazníci z {city} hledající vás na Google unikají konkurenci.\n"
        f"{demo_line}\n\n"
        f"Nezávazně se mrkněte — líbil by se vám podobný web? Rád si s vámi "
        f"zavolám o úpravách. Jak by vám to vyhovovalo?\n\n"
        f"S pozdravem,\nDavid — LeadForge")


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
    if not (lead["phone"] or lead["email"]):
        conn.close()
        return f"lead #{lead_id} has no contact — enrich first"

    msg = draft_message(lead)
    conn.execute(
        "INSERT INTO events (lead_id, stage, detail) VALUES (?, 'OUTREACH_DRAFT', ?)",
        (lead_id, msg[:500]))
    advance(conn, lead_id, "CONTACTED", "draft created — awaiting /outreach approve")
    conn.commit()
    conn.close()
    return f"DRAFT for #{lead_id} {lead['company_name']}:\n\n{msg}"


def cmd_list() -> str:
    conn = connect()
    rows = conn.execute(
        "SELECT id, company_name, stage FROM leads WHERE stage='CONTACTED'").fetchall()
    conn.close()
    if not rows:
        return "no pending drafts"
    return "\n".join(f"#{r['id']} {r['company_name']} [{r['stage']}] — approve with /outreach approve {r['id']}"
                     for r in rows)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == "draft" and len(sys.argv) > 2:
        print(cmd_draft(int(sys.argv[2])))
    elif cmd == "list":
        print(cmd_list())
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
