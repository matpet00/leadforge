"""Outreach agent — draft offer messages with human-in-the-loop approval.

Flow:
  request draft -> status=PENDING, shown in Telegram
  human replies approve -> APPROVED (by whom, when) — only then sendable
  site changed after approval? -> approval auto-expires (site_version mismatch)
  SMTP not wired yet: 'send' logs to outbox table and marks SENT_SIMULATED.

DB tables: outreach(id, lead_id, demo_url, subject, body, status,
                    created_by, approved_by, approved_at, sent_at, site_version)
"""

import json
import time

from core.db import connect
from core.config import llm_chat


SCHEMA = """
CREATE TABLE IF NOT EXISTS outreach (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL,
    demo_url TEXT DEFAULT '',
    subject TEXT DEFAULT '',
    body TEXT DEFAULT '',
    status TEXT DEFAULT 'PENDING',          -- PENDING/APPROVED/DISCARDED/SENT_SIMULATED/SENT
    created_by TEXT DEFAULT 'outreach-agent',
    approved_by TEXT DEFAULT '',
    approved_at REAL DEFAULT 0,
    sent_at REAL DEFAULT 0,
    site_version TEXT DEFAULT '',            -- hash of site html at approval time
    created_at REAL DEFAULT 0,
    FOREIGN KEY(lead_id) REFERENCES leads(id)
);
"""


def _ensure(conn):
    conn.executescript(SCHEMA)


def _site_hash(html: str) -> str:
    import hashlib
    return hashlib.sha1(html.encode()).hexdigest()[:12]


def draft_for(lead_ref: str) -> dict | None:
    """Create a PENDING draft for a deployed lead."""
    conn = connect(); _ensure(conn)
    row = conn.execute(
        "SELECT * FROM leads WHERE id=? OR LOWER(company_name) LIKE ?",
        (lead_ref if str(lead_ref).isdigit() else -1, f"%{str(lead_ref).lower()}%")
    ).fetchone()
    if not row or row["stage"] != "DEPLOYED":
        return None

    services = [s.strip() for s in row["business_scope"].split(";") if s.strip()][:3]
    name_part = row["company_name"].split(",")[0].split(" s.r.o")[0]
    prompt = (
        f"Napiš krátký nabídkový email v češtině pro firmu '{row['company_name']}' "
        f"(činnost: {'; '.join(services)}, město: {row['city']}). "
        f"Nabízíme jim profesionální web; ukázku mají na {row['demo_url']}. "
        f"Tón: přátelský, věcný, žádné laciné marketingové fráze. Max 120 slov. "
        f"Vrať JSON: {{\"subject\":\"...\",\"body\":\"...\"}}"
    )
    raw = llm_chat([{"role": "user", "content": prompt}], max_tokens=400, temperature=0.6)
    data = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])

    html_path = None
    from pathlib import Path
    from generator.site_builder import slugify
    p = Path(__file__).resolve().parent.parent / "generated" / slugify(row["company_name"]) / "index.html"
    html = p.read_text(encoding="utf-8") if p.exists() else ""

    cur = conn.execute(
        """INSERT INTO outreach (lead_id, demo_url, subject, body, status, site_version, created_at)
           VALUES (?,?,?,?,?,?,?)""",
        (row["id"], row["demo_url"], data.get("subject",""), data.get("body",""),
         "PENDING", _site_hash(html), time.time()),
    )
    conn.commit()
    return {"draft_id": cur.lastrowid, "lead": row["company_name"],
            "subject": data.get("subject"), "body": data.get("body"),
            "demo": row["demo_url"]}


def approve(draft_id: int, human: str) -> str:
    conn = connect()
    row = conn.execute("SELECT * FROM outreach WHERE id=?", (draft_id,)).fetchone()
    if not row:
        return f"draft #{draft_id} not found"
    if row["status"] != "PENDING":
        return f"draft #{draft_id} is {row['status']}, not PENDING"

    from pathlib import Path
    from generator.site_builder import slugify
    lead = conn.execute("SELECT company_name FROM leads WHERE id=?", (row["lead_id"],)).fetchone()
    p = Path(__file__).resolve().parent.parent / "generated" / slugify(lead["company_name"]) / "index.html"
    current_hash = _site_hash(p.read_text(encoding="utf-8")) if p.exists() else ""
    if current_hash != row["site_version"]:
        conn.execute("UPDATE outreach SET status='EXPIRED' WHERE id=?", (draft_id,))
        conn.commit()
        return ("⚠️ approval refused: the site changed since this draft was written. "
                "Request a new draft so the link matches.")

    conn.execute("UPDATE outreach SET status='APPROVED', approved_by=?, approved_at=? WHERE id=?",
                 (human, time.time(), draft_id))
    conn.commit()
    return f"✅ draft #{draft_id} approved by {human}. Use send {draft_id}"


def send(draft_id: int, recipient: str) -> str:
    """Simulated send until SMTP is wired. Refuses unapproved drafts."""
    conn = connect()
    row = conn.execute("SELECT * FROM outreach WHERE id=?", (draft_id,)).fetchone()
    if not row:
        return f"draft #{draft_id} not found"
    if row["status"] != "APPROVED":
        return f"🚫 draft #{draft_id} is {row['status']} — approval required before sending"
    conn.execute("UPDATE outreach SET status='SENT_SIMULATED', sent_at=? WHERE id=?",
                 (time.time(), draft_id))
    conn.commit()
    # real SMTP goes here in production
    return (f"📤 [SIMULATED] would send draft #{draft_id} to {recipient}\n"
            f"Subject: {row['subject']}\n\n{row['body'][:300]}…")


def list_drafts(status: str | None = None) -> str:
    conn = connect(); _ensure(conn)
    q = ("SELECT o.id, o.status, o.subject, l.company_name FROM outreach o "
         "JOIN leads l ON l.id=o.lead_id")
    rows = conn.execute(q + (" WHERE o.status=?" if status else "") + " ORDER BY o.id DESC LIMIT 10",
                        (status,) if status else ()).fetchall()
    return "\n".join(f"#{r['id']} [{r['status']}] {r['company_name']}: {r['subject'][:50]}"
                     for r in rows) or "no drafts"


if __name__ == "__main__":
    print(list_drafts())
