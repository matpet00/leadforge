"""Deploy helper — pushes all generated demo sites (incl. Tailwind variants)
to GitHub Pages under matpet00.github.io/<repo>/."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

os.environ.setdefault("GITHUB_TOKEN", "")
os.environ.setdefault("GITHUB_USERNAME", "")

from deploy import ghpages
from core.db import connect


class FakeLead(dict):
    """ghpages.deploy_lead expects a lead-like row; wrap plain dicts."""
    def __getitem__(self, k):
        return dict.__getitem__(self, k)


def deploy_slug(slug: str, company: str, lead_id=None) -> tuple[bool, str]:
    site_file = Path(__file__).resolve().parent / "generated" / slug / "index.html"
    if not site_file.exists():
        return False, "site file missing"
    lead = FakeLead(company_name=company, id=lead_id or 0)
    # ghpages.repo_name derives from company name + 'demo' prefix
    name = f"demo-{slug}" if not slug.startswith("demo-") else slug
    ok, msg = ghpages.create_repo(name)
    if not ok and "422" not in str(msg):
        return False, f"repo create failed: {msg}"
    import time
    time.sleep(1)
    ok2, msg2 = ghpages.push_file(name, site_file, "deploy: tailwind variant")
    if not ok2:
        return False, f"push failed: {msg2}"
    url = ghpages.enable_pages(name)
    if not url:
        return False, "pages enable failed (may already exist — check URL)"
    return True, url


if __name__ == "__main__":
    slug, company = sys.argv[1], sys.argv[2]
    ok, result = deploy_slug(slug, company)
    print(("OK " if ok else "FAIL ") + result)
