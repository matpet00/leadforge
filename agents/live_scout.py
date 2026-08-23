"""Live Scout — live RZP ingestion via the official ARES API (Ministry of Finance).

Source: https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/... — public, free,
no registration. Firm data comes from public registers (zákon 304/2013 Sb.).
Only registered business data is used (name, seat, ICO, trades). Rate-limited
to be polite to the state service.

Falls back to sample mode when network/API unavailable.
"""

import json
import time
import urllib.request
from pathlib import Path

from core.db import connect, upsert_lead, advance, log_event

SAMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_rzp.json"

ARES_SEARCH = ("https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/"
               "ekonomicke-subjekty/vyhledat")
ARES_DETAIL = ("https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/"
               "ekonomicke-subjekty/{ico}")

# polite rate limit (requests per second)
RATE = 1.0
_last_call = [0.0]

# search terms that surface businesses in our good industries
SEARCH_TERMS = {
    "tradesman": ["strojírenské služby", "zahradnické", "stavební práce",
                  "tesařství", "malířské práce", "instalatér"],
    "salon": ["kadeřnictví", "kosmetický salón", "masáže"],
    "auto": ["autoservis", "pneuservis", "autolakovna"],
    "gastronomy": ["restaurace", "hospoda", "catering"],
}


def _throttle():
    wait = RATE - (time.time() - _last_call[0])
    if wait > 0:
        time.sleep(wait)
    _last_call[0] = time.time()


def _ares_search(term: str, count: int = 10) -> list[dict]:
    """Search ARES by business name; returns raw subject dicts."""
    body = json.dumps({
        "start": 0,
        "pocet": count,
        "obchodniJmeno": term,
        "obchody": [], "pravniFormy": [], "icoIds": [], "adresy": [],
    }).encode()
    req = urllib.request.Request(
        ARES_SEARCH, data=body, method="POST",
        headers={"Content-Type": "application/json",
                 "Accept": "application/json"})
    _throttle()
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode())
    return data.get("ekonomickeSubjekty") or []


def normalize_ares(sub: dict) -> dict | None:
    """Normalize one ARES subject into our lead shape. None = skip."""
    reg = sub.get("seznamRegistraci") or {}
    if reg.get("stavZdrojeRzp") != "AKTIVNI":
        return None  # not an active trade register subject
    sidlo = sub.get("sidlo") or {}
    return {
        "ico": str(sub.get("ico") or "").zfill(8),
        "company_name": sub.get("obchodniJmeno") or "",
        "address": sidlo.get("textovaAdresa") or "",
        "city": sidlo.get("nazevObce") or "",
        # ARES search doesn't carry trade descriptions; scope refined at enrich
        "business_scope": sub.get("obchodniJmeno") or "",
        "source": "ares-live",
    }


def run_live(max_per_term: int = 5) -> dict:
    """Fetch leads for all SEARCH_TERMS via ARES. Returns summary."""
    conn = connect()
    added = skipped = errors = 0
    tried = 0
    for industry, terms in SEARCH_TERMS.items():
        for term in terms:
            tried += 1
            try:
                subs = _ares_search(term, count=max_per_term)
            except Exception as e:
                errors += 1
                print(f"  ! ARES search '{term}' failed: {e}")
                continue
            for s in subs:
                lead = normalize_ares(s)
                if not lead:
                    skipped += 1
                    continue
                lead["industry"] = industry
                lid = upsert_lead(conn, lead)
                if lid:
                    conn.execute("UPDATE leads SET industry=? WHERE id=?",
                                 (industry, lid))
                    advance(conn, lid, "SCOUTED", f"scouted via ARES ({term})")
                    added += 1
            time.sleep(0.2)
    conn.commit()
    conn.close()
    return {"tried_terms": tried, "added": added, "skipped_nonrzp": skipped,
            "errors": errors}


def run() -> list:
    """Main entry — live mode with automatic fallback to sample."""
    try:
        result = run_live()
        if result["errors"] == result["tried_terms"]:  # everything failed
            raise RuntimeError("all ARES searches failed")
        log_event_msg = f"live scout: {result}"
        print(f"[scout] {log_event_msg}")
        return [result]
    except Exception as e:
        print(f"[scout] live unavailable ({e}) — falling back to sample")
        from pathlib import Path as _P
        raw = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
        conn = connect()
        out = []
        for r in raw:
            lid = upsert_lead(conn, r)
            if lid:
                out.append(lid)
        conn.commit()
        conn.close()
        return out


if __name__ == "__main__":
    print(run())
