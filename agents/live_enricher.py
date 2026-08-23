"""Live enrichment — scrape business details from public sources.

Sources (all public, polite fetch):
  1. Domain probe — DNS + HTTP check of guessed domains → confirms no-website status
  2. Website HTML scrape — if a site EXISTS but is bad (parked, outdated), we can
     still pitch a redesign; extracts title/description for context
  3. Facebook page guess — facebook.com/<slug> existence check (HEAD request)
  4. Phone regex extraction from any found page

Rate-limiting: 1 req/sec per host, custom User-Agent identifying us.
"""

import json
import re
import time
import urllib.request
import urllib.error

from core.db import connect

UA = {"User-Agent": "LeadForge-Research/0.1 (business contact discovery; contact@example.cz)"}


def fetch(url: str, timeout: int = 10) -> tuple[int, str]:
    """Returns (status_code, body_snippet). 0 = unreachable."""
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(200_000).decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:
        return 0, ""


CZ_CHARS = str.maketrans("áčďéěíňóřšťúůýž", "acdeeinorstuuyz")


def domain_candidates(name: str) -> list[str]:
    slug = name.lower().translate(CZ_CHARS)
    slug = re.sub(r"\b(s\.?r\.?o\.?|a\.?s\.?|spole[čc]nost|firma)\b", " ", slug)
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    words = [w for w in slug.split("-") if w]
    cands = [slug + ".cz"]
    if len(words) > 1:
        cands.append("".join(words[:2]) + ".cz")
    return cands[:3]


PHONE_RE = re.compile(r"(\+420[\s/]?)?\d{3}[\s/]\d{3}[\s/]\d{3}")


def scrape_details(company_name: str, city: str) -> dict:
    """Main entry: gather everything findable about one business."""
    result = {
        "website": "", "website_status": "", "website_title": "",
        "facebook": "", "phone": "", "email": "", "source_notes": [],
    }
    for d in domain_candidates(company_name):
        code, body = fetch(f"https://{d}")
        time.sleep(1)
        if code == 200 and body:
            result["website"] = d
            result["website_status"] = "live"
            m = re.search(r"<title[^>]*>(.*?)</title>", body, re.S | re.I)
            result["website_title"] = m.group(1).strip()[:120] if m else ""
            pm = PHONE_RE.search(re.sub(r"<[^>]+>", " ", body))
            if pm:
                result["phone"] = re.sub(r"\s", "", pm.group(0))
            em = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", body)
            if em:
                result["email"] = em.group(0).lower()
            result["source_notes"].append(f"scraped {d}")
            break
        elif code in (301, 302, 403):
            result["website"] = d
            result["website_status"] = f"http-{code}"
            result["source_notes"].append(f"{d} responds {code} (possibly parked)")
            time.sleep(1)

    fb_slug = company_name.lower().translate(CZ_CHARS)
    fb_slug = re.sub(r"[^a-z0-9]+", "-", fb_slug).strip("-")[:40]
    code, _ = fetch(f"https://www.facebook.com/{fb_slug}")
    if code == 200:
        result["facebook"] = f"https://www.facebook.com/{fb_slug}"
        result["source_notes"].append("facebook page found")
    time.sleep(1)
    return result


def enrich_pending(limit: int = 10):
    """Enrich SCORED leads with live data."""
    conn = connect()
    rows = conn.execute(
        "SELECT * FROM leads WHERE stage='SCORED' LIMIT ?", (limit,)
    ).fetchall()
    for lead in rows:
        info = scrape_details(lead["company_name"], lead["city"])
        has_site = bool(info["website"])
        conn.execute(
            """UPDATE leads SET phone=?, email=?, website=?, notes=? WHERE id=?""",
            (
                info["phone"] or lead["phone"],
                info["email"] or lead["email"],
                info["website"],
                lead["notes"] + " | " + "; ".join(info["source_notes"]),
                lead["id"],
            ),
        )
        # A live site doesn't auto-disqualify if it looks abandoned — flag for review
        new_stage = "ENRICHED"
        detail = "; ".join(info["source_notes"]) or "nothing found online"
        from core.db import advance
        advance(conn, lead["id"], new_stage, detail)
    conn.commit()
    return len(rows)


if __name__ == "__main__":
    print(f"live-enriched {enrich_pending()} leads")
