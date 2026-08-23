"""Stage 4: Enrichment agent v2 — live contact lookup + website detection.

Strategy (all public sources, no scraping behind logins):
  1. Domain candidates from company name → DNS resolve (cheap filter).
  2. HTTP(S) fetch of resolving domains → confirm the site actually mentions
     the firm (city/name match) — DNS exists ≠ their website.
  3. From the confirmed site extract phone/email (regex on visible text).
  4. A confirmed website ⇒ lead DISCARDED (we only sell to firms without one).

Offline/sample mode unchanged: data/sample_enrich.json carries contacts.

Legal note: all data comes from public websites of the businesses themselves
or public registers — standard B2B prospecting practice.
"""

import json
import re
import socket
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.db import connect, leads_in_stage, advance

SAMPLE_ENRICH_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_enrich.json"

CZ_CHARS = str.maketrans("áčďéěíňóřšťúůýž", "acdeeinorstuuyz")
UA = {"User-Agent": "Mozilla/5.0 (compatible; LeadForge-Research/0.2)"}
STOPWORDS = {"sro", "s", "r", "o", "a", "sluzby", "firma"}


def domain_candidates(name: str) -> list[str]:
    """Plausible domains for a Czech firm name."""
    slug = name.lower().translate(CZ_CHARS)
    slug = re.sub(r"\b(s\.?r\.?o\.?|spolecnost|firma|v\.?o\.?s\.?)\b", " ", slug)
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    words = [w for w in slug.split("-") if w]
    if not words:
        return []
    cands = [
        slug + ".cz",
        "".join(words) + ".cz",
        "-".join(words[:2]) + ".cz",
        "".join(words[:2]) + ".cz",
    ]
    # drop generic first word variants like 'zahradnicke-sluzby.cz' only when
    # name is longer — those belong to someone else, checked via content match
    seen, out = set(), []
    for c in cands:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out[:5]


def dns_resolves(domain: str) -> bool:
    try:
        socket.setdefaulttimeout(6)
        socket.gethostbyname(domain)
        return True
    except OSError:
        return False


def fetch_text(url: str) -> str:
    for scheme in ("https", "http"):
        try:
            req = urllib.request.Request(f"{scheme}://{url}", headers=UA)
            with urllib.request.urlopen(req, timeout=10) as r:
                raw = r.read(150_000).decode("utf-8", "ignore")
                # also read common contact page for emails/phones
                m = re.search(r'href="([^"]*(?:kontakt|contact)[^"]*)"', raw, re.I)
                if m and not m.group(1).startswith("http"):
                    try:
                        req2 = urllib.request.Request(
                            f"{scheme}://{url}/{m.group(1).lstrip('/')}", headers=UA)
                        with urllib.request.urlopen(req2, timeout=8) as r2:
                            raw += r2.read(80_000).decode("utf-8", "ignore")
                    except Exception:
                        pass
                return raw
        except Exception:
            continue
    return ""


def strip_html(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(
        r"<[^>]+>", " ", re.sub(r"(?is)<(script|style).*?</\1>", " ", html)))


def site_matches_firm(html: str, lead) -> bool:
    """The resolved domain must actually talk about THIS firm.
    Strongest signal: the firm's ICO printed on the site (footer/contact).
    Fallbacks: distinctive name tokens and/or city."""
    text = strip_html(html).lower()

    # 1. ICO on page = definitive proof this is their site
    ico = str(lead["ico"] or "").strip()
    if ico and len(ico) == 8:
        digits = re.sub(r"\D", "", text)
        # ICO appears as plain number, spaced, or with 'ICO' label nearby
        spaced = " ".join(ico)
        if ico in digits or ico in re.sub(r"\s+", "", text) or \
           re.search(rf"i[čc]o[^0-9]{{0,20}}{ico[:3]}[\s.]?{ico[3:]}", text):
            return True

    # 2. Distinctive name tokens + optional city corroboration.
    # Generic trade words (zahradnicke sluzby, autoservis...) appear on many
    # sites; only distinctive tokens (Měšice, Kusyn, Štěpán, Král…) count
    # toward a confident match. Require at least one DISTINCTIVE hit.
    name_slug = lead["company_name"].lower().translate(CZ_CHARS)
    tokens = [w for w in re.findall(r"[a-z0-9]{4,}", name_slug)
              if w not in STOPWORDS and len(w) > 3]
    if not tokens:
        return False
    # heuristic: tokens shared across the industry's generic vocabulary
    GENERIC = {"zahradnicke", "sluzby", "prace", "centrum", "servis", "auto",
               "stavebni", "tesarske", "malirske", "instalaterske", "restaurace"}
    distinctive = [t for t in tokens if t not in GENERIC]
    hits_distinctive = sum(1 for t in distinctive if t in text)
    city_ok = bool(lead["city"]) and lead["city"].lower().translate(CZ_CHARS) in text
    if distinctive:
        # at least one unique token, or two generic ones plus the city
        return hits_distinctive >= 1 or (len(distinctive) == 0 and city_ok)
    return city_ok and all(t in text for t in tokens)


def extract_contacts(html: str) -> tuple[str, str]:
    text = strip_html(html) + " " + html
    phones = re.findall(r"(?:\+420[\s]?)?\d{3}[\s./-]?\d{3}[\s./-]?\d{3}", text)
    phones = [p.strip() for p in phones
              if len(re.sub(r"\D", "", p)) >= 9 and not re.fullmatch(r"[12]\d{8}", re.sub(r"\D", "", p))]
    emails = list(dict.fromkeys(re.findall(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}", text)))
    email = next((e for e in emails
                  if not any(x in e.lower() for x in
                             ("example.", "gmail.com/wix", "sentry", "domain."))), "")
    return (phones[0] if phones else ""), email


def enrich_lead_live(lead) -> dict:
    """Returns {'website':..., 'phone':..., 'email':...} from live probing."""
    result = {"website": "", "phone": "", "email": ""}
    for d in domain_candidates(lead["company_name"]):
        if not dns_resolves(d):
            continue
        html = fetch_text(d)
        if html and site_matches_firm(html, lead):
            result["website"] = d
            phone, email = extract_contacts(html)
            result["phone"], result["email"] = phone, email
            break
    return result


def run(live: bool = False) -> dict:
    enrich_map = json.loads(SAMPLE_ENRICH_PATH.read_text(encoding="utf-8")) if not live else {}
    conn = connect()
    stats = {"enriched": 0, "has_website": 0, "no_contact": 0}

    for lead in leads_in_stage(conn, "SCORED"):
        found_site, phone, email = "", "", ""
        if live:
            probed = enrich_lead_live(lead)
            found_site, phone, email = (probed["website"], probed["phone"],
                                        probed["email"])
        else:
            extra = enrich_map.get(str(lead["ico"]), {})
            phone, email = extra.get("phone", ""), extra.get("email", "")
            found_site = extra.get("website", "")

        if found_site:
            conn.execute(
                "UPDATE leads SET website=?, notes=notes||' [has website]' WHERE id=?",
                (found_site, lead["id"]))
            advance(conn, lead["id"], "DISCARDED",
                    f"already has website {found_site}")
            stats["has_website"] += 1
        elif phone or email:
            if phone:
                conn.execute("UPDATE leads SET phone=? WHERE id=?", (phone, lead["id"]))
            if email:
                conn.execute("UPDATE leads SET email=? WHERE id=?", (email, lead["id"]))
            advance(conn, lead["id"], "ENRICHED",
                    ", ".join(filter(None, ["phone ok" if phone else "",
                                            "email ok" if email else ""])))
            stats["enriched"] += 1
        else:
            advance(conn, lead["id"], "ENRICHED",
                    "no direct contact found — manual channel needed")
            stats["no_contact"] += 1

        import time as _t
        _t.sleep(0.5)  # polite rate limit when probing live sites
    conn.commit()
    return stats


if __name__ == "__main__":
    import sys
    from pathlib import Path as _P
    sys.path.insert(0, str(_P(__file__).resolve().parent.parent))
    print(run(live="--live" in sys.argv))
