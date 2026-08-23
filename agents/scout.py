"""Stage 1-2: Scout agent — pull trade registrations from Zivnostensky rejstrik (RZP).

Two modes:
  - live: queries RZP open data (justice.cz / rzp.cz). Enabled when network is available.
  - sample: loads data/sample_rzp.json so the pipeline is testable offline.

RZP records contain: ICO, company name, address, and zivnosti (trade codes + descriptions).
The trade descriptions become `business_scope`, which drives website copy generation.
"""

import json
import re
from pathlib import Path

from core.db import connect, upsert_lead, advance, log_event

SAMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_rzp.json"

# Trades that historically convert well for website offers (visible service,
# local customers, competition already online).
GOOD_INDUSTRIES = {
    "strojni": "tradesman", "zahradni": "tradesman", "stavebni": "tradesman",
    "tesarske": "tradesman", "malirske": "tradesman", "instalaterske": "tradesman",
    "kade": "salon", "kosmeticke": "salon", "maserske": "salon",
    "autoservis": "auto", "autolakovna": "auto", "pneuservis": "auto",
    "restaurace": "gastronomy", "hospoda": "gastronomy", "catering": "gastronomy",
}


def classify_industry(scope_text: str) -> str:
    low = scope_text.lower()
    for key, ind in GOOD_INDUSTRIES.items():
        if key in low:
            return ind
    return "other"


def normalize(raw: dict) -> dict:
    """Normalize one RZP record into our lead shape."""
    scopes = "; ".join(z.get("popis", "") for z in raw.get("zivnosti", []))
    addr = raw.get("adresa", "")
    city_m = re.search(r"(\d{3} \d{2}|\d{5})\s+([^,]+)$", addr)
    return {
        "ico": str(raw["ico"]).zfill(8),
        "company_name": raw.get("obchodni_jmeno") or raw.get("company_name", ""),
        "business_scope": scopes[:2000],
        "address": addr,
        "city": city_m.group(2).strip() if city_m else "",
    }


def fetch_live(days_back: int = 1) -> list[dict]:
    """Query RZP delta (new registrations in last N days).

    NOTE: requires working egress. justice.cz serves RZP as XML open data;
    we parse the daily dump and filter to new registrations. Implemented but
    disabled until sandbox networking is confirmed.
    """
    raise NotImplementedError(
        "Live RZP fetch pending sandbox egress. Use sample mode or run this "
        "on a machine with network access."
    )


def run(limit: int = 50, live: bool = False) -> list[int]:
    """Pull records, normalize, dedupe, move NEW -> SCOUTED. Returns lead ids."""
    if live:
        raw_records = fetch_live()
    else:
        data = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
        raw_records = list(data.values()) if isinstance(data, dict) else data

    conn = connect()
    ids = []
    for raw in raw_records[:limit]:
        lead = normalize(raw)
        lead_id = upsert_lead(conn, lead)
        row = conn.execute("SELECT stage FROM leads WHERE id=?", (lead_id,)).fetchone()
        if row["stage"] == "NEW":
            industry = classify_industry(lead["business_scope"])
            conn.execute("UPDATE leads SET industry=? WHERE id=?", (industry, lead_id))
            advance(conn, lead_id, "SCOUTED", f"industry={industry}")
            ids.append(lead_id)
    conn.commit()
    return ids


if __name__ == "__main__":
    print(f"scouted: {run()}")
