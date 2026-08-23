"""Dashboard — static HTML funnel view of the pipeline.

Run `python3 dashboard.py` after any sweep (or let orchestrator call it);
writes dashboard/index.html showing:
  - funnel counts per stage
  - table of all leads with score/industry/stage/demo link
  - latest events feed
"""

import html
import time
from pathlib import Path

from core.db import connect, funnel_report, recent_events

BASE = Path(__file__).resolve().parent
OUT = BASE / "dashboard" / "index.html"

STYLE = """
body{font-family:'Segoe UI',system-ui,sans-serif;margin:0;background:#0f172a;color:#e2e8f0}
.wrap{max-width:64rem;margin:0 auto;padding:2rem 1.5rem}
h1{font-weight:600}h1 span{color:#38bdf8;font-size:.9rem;font-weight:400;margin-left:.6rem}
.funnel{display:flex;gap:.5rem;flex-wrap:wrap;margin:1.5rem 0}
.stage{background:#1e293b;border-radius:10px;padding:1rem 1.3rem;min-width:7rem;text-align:center}
.stage .n{font-size:1.8rem;font-weight:700;color:#38bdf8}
.stage .l{font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:#94a3b8}
table{width:100%;border-collapse:collapse;margin-top:1rem;background:#1e293b;border-radius:10px;overflow:hidden}
th{background:#334155;padding:.6rem .8rem;text-align:left;font-size:.75rem;text-transform:uppercase;color:#cbd5e1}
td{padding:.55rem .8rem;border-top:1px solid #334155;font-size:.9rem}
a{color:#38bdf8;text-decoration:none}
.events{margin-top:1.5rem;background:#1e293b;border-radius:10px;padding:1rem 1.2rem;font-size:.85rem;line-height:1.9}
"""


def render():
    conn = connect()
    funnel = funnel_report(conn)
    total = sum(funnel.values())
    leads = conn.execute(
        "SELECT id, company_name, industry, score, stage, demo_url, city FROM leads "
        "ORDER BY CASE stage WHEN 'DEPLOYED' THEN 0 ELSE 1 END, score DESC"
    ).fetchall()
    events = recent_events(conn, 12)

    stages_html = "".join(
        f'<div class="stage"><div class="n">{n}</div><div class="l">{s.title()}</div></div>'
        for s, n in funnel.items()
    )
    rows = ""
    for l in leads:
        demo = (
            f'<a href="{html.escape(l["demo_url"])}">demo</a>'
            if l["demo_url"].startswith("http") else
            (l["demo_url"] or "—")
        )
        rows += (
            f"<tr><td>{l['id']}</td><td>{html.escape(l['company_name'])}</td>"
            f"<td>{l['industry']}</td><td>{l['score']}</td><td>{l['stage']}</td>"
            f"<td>{html.escape(l['city'] or '')}</td><td>{demo}</td></tr>"
        )
    ev = "".join(
        f"<div>· <b>{html.escape(e['company_name'])}</b> — {e['stage']}: {html.escape(e['detail'] or '')}</div>"
        for e in events
    )

    page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>LeadForge Dashboard</title><style>{STYLE}</style></head><body>
<div class="wrap">
<h1>LeadForge<span>updated {time.strftime('%Y-%m-%d %H:%M')} · {total} leads</span></h1>
<div class="funnel">{stages_html}</div>
<table><tr><th>ID</th><th>Company</th><th>Industry</th><th>Score</th><th>Stage</th><th>City</th><th>Demo</th></tr>
{rows}</table>
<div class="events"><b>Latest events</b>{ev}</div>
</div></body></html>"""
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(page, encoding="utf-8")
    return str(OUT)


if __name__ == "__main__":
    print("dashboard:", render())
