"""Deploy agent — publishes demo sites to GitHub Pages.

Strategy: one repo per customer (clean separation, easy handover when sold),
site pushed to `gh-pages`-less simple main branch, Pages enabled via API.
Live URL pattern: https://<user>.github.io/<repo-slug>/

Env needed: GITHUB_TOKEN, GITHUB_USERNAME (in project .env).
"""

import base64
import json
import os
import time
import urllib.request
import urllib.error
from pathlib import Path

from core.db import connect, advance
from core import telegram

API = "https://api.github.com"


def _req(method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
    token = os.environ["GITHUB_TOKEN"]
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        API + path, data=data, method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.load(r) if r.status != 204 else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        return e.code, {"message": body}


def repo_name(lead) -> str:
    url = lead["demo_url"] or f"lead-{lead['id']}"
    slug = url.rstrip("/").split("/")[-1]
    slug = slug.replace("index.html", "").strip("/")
    if not slug or slug.startswith("lead-"):
        from generator.site_builder import slugify
        slug = slugify(lead["company_name"])
    return f"demo-{slug}"


def create_repo(name: str) -> tuple[bool, str]:
    code, resp = _req("POST", "/user/repos", {
        "name": name,
        "private": False,
        "auto_init": True,
        "description": "Demo website — LeadForge",
    })
    if code == 201:
        return True, "created"
    if code == 422:
        return True, "already exists"
    return False, resp.get("message", str(code))


def push_file(name: str, local_path, commit_msg: str) -> tuple[bool, str]:
    content = base64.b64encode(local_path.read_bytes()).decode()
    # get existing sha if file exists
    code, resp = _req("GET", f"/repos/{os.environ['GITHUB_USERNAME']}/{name}/contents/index.html")
    sha = resp.get("sha") if code == 200 else None
    payload = {"message": commit_msg, "content": content}
    if sha:
        payload["sha"] = sha
    code, resp = _req(
        "PUT",
        f"/repos/{os.environ['GITHUB_USERNAME']}/{name}/contents/index.html",
        payload,
    )
    return code in (200, 201), resp.get("message", str(code))[:120]


def enable_pages(name: str) -> str:
    user = os.environ["GITHUB_USERNAME"]
    code, resp = _req("POST", f"/repos/{user}/{name}/pages", {"source": {"branch": "main"}})
    url = resp.get("html_url", "")
    if code in (201, 409):  # 409 = already enabled
        return f"https://{user}.github.io/{name}/"
    return ""


def site_file_for(lead) -> Path:
    from generator.site_builder import slugify
    slug = slugify(lead["company_name"])
    return Path(__file__).resolve().parent.parent / "generated" / slug / "index.html"


def deploy_lead(lead) -> tuple[bool, str]:
    name = repo_name(lead)
    ok, msg = create_repo(name)
    if not ok:
        return False, f"repo create failed: {msg}"
    time.sleep(1)
    site_file = site_file_for(lead)
    if not site_file.exists():
        return False, "site file missing"
    ok, msg = push_file(name, site_file, "deploy: updated site")
    if not ok:
        return False, f"push failed: {msg}"
    url = enable_pages(name)
    if not url:
        return False, "pages enable failed"
    return True, url


def run_deploy_stage() -> int:
    """Deploy all QA-passed leads to GitHub Pages."""
    conn = connect()
    n = 0
    rows = conn.execute("SELECT * FROM leads WHERE stage='QA'").fetchall()
    for lead in rows:
        telegram.post("Deploy", f"publishing {repo_name(lead)}…")
        ok, result = deploy_lead(lead)
        if ok:
            conn.execute("UPDATE leads SET demo_url=? WHERE id=?", (result, lead["id"]))
            advance(conn, lead["id"], "DEPLOYED", f"live at {result}")
            telegram.post("Deploy", f"🚀 live: {result}")
            n += 1
        else:
            advance(conn, lead["id"], "QA", f"deploy retry: {result}")
            telegram.post("Deploy", f"⚠️ failed: {result}")
    conn.commit()
    return n


if __name__ == "__main__":
    print(f"deployed {run_deploy_stage()} sites")
