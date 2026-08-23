"""LeadForge Dashboard — funnel overview per company + demo quality.

Generates a self-contained HTML file (data/dashboard.html) showing:
  - funnel summary (counts per stage)
  - per-lead table: stage, score, contacts, website-check, demo URL,
    review score, offer status
  - demo links for quick preview

Usage: python3 dashboard.py   → writes data/dashboard.html
"""

import json
import time
from pathlib import Path

from core.db import connect

BASE = Path(__file__).resolve().parent
OUT = BASE / "data" / "dashboard.html"

STAGE_ORDER = ["NEW", "SCOUTED", "SCORED", "ENRICHED", "GENERATED", "QA",
               "DEPLOYED", "CONTACTED", "REPLIED", "WON", "LOST", "DISCARDED"]
STAGE_COLORS = {
    "NEW": "#94a3b8", "SCOUTED": "#64748b", "SCORED": "#0ea5e9",
    "ENRICHED": "#8b5cf6", "GENERATED": "#f59e0b", "QA": "#10b981",
    "DEPLOYED": "#22c55e", "CONTACTED": "#3b82f6", "REPLIED": "#eab308",
    "WON": "#16a34a", "LOST": "#dc2626", "DISCARDED": "#cbd5e1",
}


def funnel_rows(conn):
    return conn.execute(
        """SELECT id, company_name, industry, city, stage, score,
                  phone != '' AS has_phone, email != '' AS has_email,
                  website, demo_url,
                  COALESCE(json_extract(notes,'$[0].review_score'), '') AS review
           FROM leads ORDER BY
             CASE stage||'-'||score END""").fetchall()


def build_html():
    conn = connect()
    leads = [dict(r) for r in conn.execute(
        "SELECT * FROM leads ORDER BY score DESC").fetchall()]
    counts = {r["stage"]: r["n"] for r in conn.execute(
        "SELECT stage, COUNT(*) n FROM leads GROUP BY stage")}
    events = [dict(r) for r in conn.execute(
        "SELECT e.*, l.company_name FROM events e LEFT JOIN leads l "
        "ON l.id=e.lead_id ORDER BY e.id DESC LIMIT 30")]
    conn.close()

    active = [l for l in leads if l["stage"] not in ("DISCARDED",)]
    discarded = [l for l in leads if l["stage"] == "DISCARDED"]
    total_active = len(active)

    bars = "".join(
        f'<div class="bar"><span class="lbl">{s}</span>'
        f'<div class="track"><div class="fill" style="width:{min(100, counts.get(s,0)*100/max(total_active,1)*4)}%;'
        f'background:{STAGE_COLORS.get(s,"#999")}"></div></div>'
        f'<span class="num">{counts.get(s,0)}</span></div>'
        for s in STAGE_ORDER if s != "DISCARDED")

    lead_rows = ""
    for l in active:
        demo = f'<a href="{l["demo_url"]}" target="_blank">demo</a>' if l["demo_url"] and not l["demo_url"].startswith("file:") else ("—" if not l["demo_url"] else "local")
        web = f'⚠️ <a href="https://{l["website"]}" target="_blank">{l["website"]}</a>' if l["website"] else "—"
        contacts = " ".join(filter(None, [
            "📞" if l["phone"] else "", "✉️" if l["email"] else ""])) or "—"
        lead_rows += (
            f'<tr><td>{l["id"]}</td><td><b>{l["company_name"]}</b><br>'
            f'<small>{l["city"] or ""} · {l["industry"]}</small></td>'
            f'<td><span class="stage" style="background:{STAGE_COLORS.get(l["stage"],"#999")}">{l["stage"]}</span></td>'
            f'<td>{l["score"]}</td><td>{contacts}</td><td>{web}</td>'
            f'<td>{demo}</td></tr>')

    disc_rows = "".join(
        f'<li>{l["company_name"]} — {l["notes"][-60:] if l["notes"] else "score below threshold"}</li>'
        for l in discarded[:15])

    event_rows = "".join(
        f'<li><small>{e["company_name"] or "hub"}</small> · {e["stage"]}: {e["detail"]}</li>'
        for e in events)

    return f"""<!DOCTYPE html><html lang="cs"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LeadForge Dashboard</title>
<style>
*{{margin:0;box-sizing:border-box}}body{{font-family:system-ui,sans-serif;background:#f8fafc;color:#111827;padding:24px}}
h1{{font-size:1.5rem;margin-bottom:4px}} .sub{{color:#6b7280;margin-bottom:20px;font-size:.9rem}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px}}
@media(max-width:800px){{.grid2{{grid-template-columns:1fr}}}}
.card{{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:18px}}
.card h2{{font-size:1rem;margin-bottom:12px}}
.bar{{display:flex;align-items:center;gap:10px;margin-bottom:6px;font-size:.85rem}}
.lbl{{width:90px;text-align:right;color:#64748b}}.num{{width:30px;font-weight:700}}
.track{{flex:1;background:#f1f5f9;border-radius:6px;height:14px;overflow:hidden}}
.fill{{height:100%;border-radius:6px;transition:width .4s}}
table{{width:100%;border-collapse:collapse;font-size:.88rem}}
th,td{{padding:9px 10px;text-align:left;border-bottom:1px solid #f1f5f9;vertical-align:top}}
th{{color:#64748b;font-weight:600;font-size:.78rem;text-transform:uppercase}}
.stage{{display:inline-block;color:#fff;padding:3px 10px;border-radius:99px;font-size:.75rem;font-weight:600}}
ul{{list-style:none;font-size:.85rem}} li{{padding:6px 0;border-bottom:1px solid #f8fafc}}
a{{color:#2563eb;text-decoration:none}} a:hover{{text-decoration:underline}}
.kpi{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}}
.kpi div{{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:14px 20px}}
.kpi b{{font-size:1.6rem;display:block}} .kpi span{{color:#6b7280;font-size:.8rem}}
</style></head><body>
<h1>🏗️ LeadForge Dashboard</h1>
<div class="sub">generated {time.strftime('%Y-%m-%d %H:%M')}</div>
<div class="kpi">
<div><b>{total_active}</b><span>aktivní leady</span></div>
<div><b>{counts.get('DEPLOYED',0)}</b><span>live dema</span></div>
<div><b>{counts.get('CONTACTED',0)+counts.get('REPLIED',0)+counts.get('WON',0)}</b><span>kontaktováno</span></div>
<div><b>{len(discarded)}</b><span>zahozeno</span></div>
</div>
<div class="grid2">
<div class="card"><h2>Funnel</h2>{bars}
<p style="margin-top:10px;font-size:.82rem;color:#6b7280">Discarded: {len(discarded)} (web již mají / nízké skóre)</p></div>
<div class="card"><h2>Poslední události</h2><ul>{event_rows}</ul></div>
</div>
<div class="card"><h2>Aktivní leady ({total_active})</h2>
<table><tr><th>#</th><th>Firma</th><th>Stav</th><th>Skóre</th><th>Kontakt</th><th>Má web?</th><th>Demo</th></tr>
{lead_rows}</table></div>
<div class="card" style="margin-top:16px"><h2>Zahozené ({len(discarded)}, top 15)</h2><ul>{disc_rows}</ul></div>
</body></html>"""


def main():
    OUT.parent.mkdir(exist_ok=True)
    html = build_html()
    OUT.write_text(html, encoding="utf-8")
    print(f"dashboard written: {OUT}")


if __name__ == "__main__":
    main()
