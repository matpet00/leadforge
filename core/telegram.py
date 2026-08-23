"""Telegram bridge — mission-control feed for the agent pipeline.

One-way: agents post stage transitions to a Telegram group.
Two-way comes later (command handler reading /getUpdates).

Config via project .env:
  TELEGRAM_BOT_TOKEN=...
  TELEGRAM_CHAT_ID=-100...

Usage:
    from core.telegram import post
    post("Generator", "Building demo for AutoServis Král…")

All failures are swallowed (logged to console) — Telegram being down must
never break the pipeline.
"""

import json
import os
import urllib.request
from pathlib import Path

_ENV = Path(__file__).resolve().parent.parent / ".env"
if _ENV.exists():
    for line in _ENV.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_GROUP_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID", "")

EMOJI = {
    "Scout": "📥", "Scorer": "⚖️", "Enricher": "🔎", "Generator": "🏗️",
    "QA": "🧪", "Deploy": "🚀", "Outreach": "✉️", "Supervisor": "👑",
    "System": "⚙️",
}


def enabled() -> bool:
    return bool(TOKEN and CHAT_ID)


def post(agent: str, text: str) -> bool:
    """Post '<emoji> [Agent] text' to the ops group. Returns success."""
    prefix = f"{EMOJI.get(agent, '🤖')} [{agent}]"
    msg = f"{prefix} {text}"
    print(f"  tg| {msg}")  # local mirror always visible in orchestrator logs
    if not enabled():
        return False
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data=json.dumps({
                "chat_id": CHAT_ID,
                "text": msg,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        print(f"  tg! telegram error: {e}")
        return False


def status_digest(funnel: dict, total: int) -> str:
    lines = [f"<b>Pipeline digest</b> — {total} leads"]
    for stage, n in funnel.items():
        if n:
            lines.append(f"• {stage}: {n}")
    return "\n".join(lines)


if __name__ == "__main__":
    ok = post("System", "bridge test — if you see this, the ops channel works ✅")
    print("sent:", ok, "| configured:", enabled())
