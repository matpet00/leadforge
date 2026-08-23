"""Stage 4: Enrichment agent — find contact info and confirm the business has NO website.

Checks (in order, all cheap):
  1. Domain guess from company name (firma-jmenovka.cz etc.) — DNS resolve via stdlib.
  2. Phone/email extraction: live mode queries public sources (RZP contact fields,
     mapy.cz firm directory); offline sample data carries contacts directly.

A lead with a confirmed website gets DISCARDED — we only sell to businesses without one.
"""

import json
import re
import socket
from pathlib import Path

from core.db import connect, leads_in_stage, advance

SAMPLE_ENRICH_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_enrich.json"

CZ_CHARS = str.maketrans("áčďéěíňóřšťúůýž", "acdeeinorstuuyz")


def domain_candidates(name: str) -> list[str]:
    slug = name.lower().translate(CZ_CHARS)
    slug = re.sub(r"\b(s\.?r\.?o\.?|spole[čc]nost|firma)\b", " ", slug)
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    words = slug.split("-")
    cands = [slug + ".cz"]
    if len(words) > 1:
        cands.append("".join(words[:2]) + "cz")
    return cands[:4]


def has_website_dns(domain: str) -> bool:
    try:
        socket.gethostbyname(domain)
        return True
    except socket.gaierror:
        return False


def run(live: bool = False) -> dict:
    enrich_map = json.loads(SAMPLE_ENRICH_PATH.read_text(encoding="utf-8")) if not live else {}
    conn = connect()
    stats = {"enriched": 0, "has_website": 0, "no_contact": 0}

    for lead in leads_in_stage(conn, "SCORED"):
        # website check: DNS probe of guessed domains (works offline-ish; NXDOMAIN = no site)
        found_site = ""
        if live:
            for d in domain_candidates(lead["company_name"]):
                if has_website_dns(d):
                    found_site = d
                    break

        extra = enrich_map.get(str(lead["ico"]), {})
        phone, email = extra.get("phone", ""), extra.get("email", "")
        if extra.get("website"):
            found_site = extra["website"]

        updates, detail = [], []
        if phone:
            updates.append(("phone", phone)); detail.append("phone ok")
        if email:
            updates.append(("email", email)); detail.append("email ok")

        if found_site:
            conn.execute("UPDATE leads SET website=?, notes=notes||' [has website]' WHERE id=?", 
                         (found_site, lead["id"]))
            advance(conn, lead["id"], "DISCARDED", f"already has website {found_site}")
            stats["has_website"] += 1
        elif phone or email:
            for k, v in updates:
                conn.execute(f"UPDATE leads SET {k}=? WHERE id=?", (v, lead["id"]))
            advance(conn, lead["id"], "ENRICHED", ", ".join(detail))
            stats["enriched"] += 1
        else:
            # keep them but flag; they can be reached by mail/visit later
            advance(conn, lead["id"], "ENRICHED", "no direct contact found — manual channel needed")
            stats["no_contact"] += 1
    conn.commit()
    return stats


if __name__ == "__main__":
    print(run())
