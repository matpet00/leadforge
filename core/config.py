"""Shared config: proxy hygiene + LLM client.

The Hermes sandbox injects http_proxy/https_proxy env vars pointing at
iron-proxy. When egress is disabled those vars are stale and break every
outbound call, so we strip them at import time.
"""

import json
import os
import urllib.request
from pathlib import Path

# --- local .env loading (sandbox workaround) ---------------------------------
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
if _ENV_FILE.exists():
    for line in _ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

# --- proxy hygiene -----------------------------------------------------------
for var in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"):
    os.environ.pop(var, None)
os.environ["NO_PROXY"] = "*"


def llm_chat(messages: list[dict], model: str = "openai/gpt-4o-mini",
             max_tokens: int = 800, temperature: float = 0.7) -> str:
    """Call OpenRouter chat completions. Returns assistant text."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps({
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.load(resp)
    return data["choices"][0]["message"]["content"]


if __name__ == "__main__":
    print("LLM check:", llm_chat(
        [{"role": "user", "content": "Reply with exactly: OK"}], max_tokens=5))
