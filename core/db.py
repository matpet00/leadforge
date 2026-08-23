"""
LeadForge — automated demo-website funnel for Czech businesses without websites.

Pipeline stages:
  NEW -> SCOUTED -> SCORED -> ENRICHED -> GENERATED -> QA -> DEPLOYED -> CONTACTED -> REPLIED -> WON/LOST

Stdlib-only by design (works in restricted sandboxes): sqlite3, urllib, string.Template.
LLM/RZP adapters are pluggable; offline sample mode lets the full pipeline run end-to-end
without network access.
"""

import json
import os
import sqlite3
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "leads.db"

STAGES = [
    "NEW",        # raw record pulled from RZP
    "SCOUTED",    # normalized + deduplicated
    "SCORED",     # lead score >= threshold to continue
    "ENRICHED",   # contact info found (phone/email)
    "GENERATED",  # single-page website built
    "QA",         # quality gate passed
    "DEPLOYED",   # demo live at demo URL
    "CONTACTED",  # outreach message sent
    "REPLIED",    # prospect responded
]
TERMINAL = ["WON", "LOST", "DISCARDED"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ico TEXT UNIQUE,
    company_name TEXT NOT NULL,
    business_scope TEXT DEFAULT '',
    address TEXT DEFAULT '',
    city TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    email TEXT DEFAULT '',
    website TEXT DEFAULT '',
    industry TEXT DEFAULT 'other',
    score INTEGER DEFAULT 0,
    score_reasons TEXT DEFAULT '[]',
    stage TEXT DEFAULT 'NEW',
    demo_url TEXT DEFAULT '',
    outreach_message TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    created_at REAL,
    updated_at REAL
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER,
    stage TEXT,
    detail TEXT,
    created_at REAL,
    FOREIGN KEY(lead_id) REFERENCES leads(id)
);
CREATE TABLE IF NOT EXISTS pipeline_meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def log_event(conn, lead_id: int, stage: str, detail: str = ""):
    conn.execute(
        "INSERT INTO events (lead_id, stage, detail, created_at) VALUES (?,?,?,?)",
        (lead_id, stage, detail, time.time()),
    )


def advance(conn, lead_id: int, new_stage: str, detail: str = ""):
    assert new_stage in STAGES + TERMINAL, f"unknown stage {new_stage}"
    conn.execute(
        "UPDATE leads SET stage=?, updated_at=? WHERE id=?", (new_stage, time.time(), lead_id)
    )
    log_event(conn, lead_id, new_stage, detail)


def upsert_lead(conn, lead: dict) -> int:
    """Insert or update-by-ICO. Returns lead id."""
    cur = conn.execute(
        """
        INSERT INTO leads (ico, company_name, business_scope, address, city,
                           created_at, updated_at)
        VALUES (?,?,?,?,?,?,?)
        ON CONFLICT(ico) DO UPDATE SET
            company_name=excluded.company_name,
            business_scope=excluded.business_scope,
            updated_at=excluded.updated_at
        RETURNING id
        """,
        (
            lead.get("ico"),
            lead["company_name"],
            lead.get("business_scope", ""),
            lead.get("address", ""),
            lead.get("city", ""),
            time.time(),
            time.time(),
        ),
    )
    return cur.fetchone()[0]


def get_lead(conn, lead_id: int):
    return conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()


def leads_in_stage(conn, stage: str):
    return conn.execute("SELECT * FROM leads WHERE stage=? ORDER BY score DESC", (stage,)).fetchall()


def funnel_report(conn) -> dict:
    rows = conn.execute(
        "SELECT stage, COUNT(*) AS n FROM leads GROUP BY stage"
    ).fetchall()
    counts = {r["stage"]: r["n"] for r in rows}
    ordered = {s: counts.get(s, 0) for s in STAGES + TERMINAL}
    return ordered


def recent_events(conn, limit=30):
    return conn.execute(
        "SELECT e.*, l.company_name FROM events e JOIN leads l ON l.id=e.lead_id "
        "ORDER BY e.id DESC LIMIT ?",
        (limit,),
    ).fetchall()
