"""Stage 3: Scoring agent — rank leads by likelihood to buy a website.

Heuristics first (free, fast, explainable); LLM scoring is an optional second
opinion later. Score >= 60 advances to ENRICHED, otherwise DISCARDED.

Signals:
  + industry in known-good set (visible local service)        +30
  + multiple trades registered (active business)              +10
  + city present (local targeting possible)                   +10
  + scope mentions 'výroba', 'služby', 'opravy'               +10
  - legal form s.r.o. without any web footprint hint          neutral (checked in enrich)
  - scope looks like passive holding / real estate only       -25
  - trade requires no public visibility (e.g. velkoobchod)    -20
"""

import json

from core.db import connect, leads_in_stage, advance

POSITIVE_WORDS = ["výroba", "služby", "opravy", "montáž", "úpravy", "péče"]
NEGATIVE_INDUSTRIES = ["velkoobchod", "velkoobchodní", "činnost fondu", "pronájem nemovitostí"]


def score_lead(lead) -> tuple[int, list[str]]:
    reasons = []
    score = 0
    scope = lead["business_scope"].lower()

    if lead["industry"] != "other":
        score += 30
        reasons.append(f"industry={lead['industry']} (+30)")
    if len(lead["business_scope"].split(";")) > 1:
        score += 10
        reasons.append("multiple trades (+10)")
    if lead["city"]:
        score += 10
        reasons.append(f"city={lead['city']} (+10)")
    for w in POSITIVE_WORDS:
        if w in scope:
            score += 10
            reasons.append(f"scope contains '{w}' (+10)")
            break
    for w in NEGATIVE_INDUSTRIES:
        if w in scope:
            score -= 25
            reasons.append(f"negative signal '{w}' (-25)")
    return max(0, min(100, score)), reasons


def run(min_score: int = 60) -> dict:
    conn = connect()
    advanced = discarded = 0
    for lead in leads_in_stage(conn, "SCOUTED"):
        s, reasons = score_lead(lead)
        conn.execute(
            "UPDATE leads SET score=?, score_reasons=? WHERE id=?",
            (s, json.dumps(reasons, ensure_ascii=False), lead["id"]),
        )
        if s >= min_score:
            advance(conn, lead["id"], "SCORED", f"score={s}")
            advanced += 1
        else:
            advance(conn, lead["id"], "DISCARDED", f"score={s} below threshold")
            discarded += 1
    conn.commit()
    return {"advanced": advanced, "discarded": discarded}


if __name__ == "__main__":
    print(run())
