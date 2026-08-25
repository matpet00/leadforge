"""Post-build site validator — catches common free-model build failures.

Checks:
1. Utility-framework classes used without loading the framework
   (Tailwind/Bootstrap classes present but no CDN link).
2. All <img>/hero URLs reachable (HEAD request) — kills hallucinated IDs.
3. Interactive elements wired: hamburger button must have toggle JS.
4. Browser-hostile calls: exit()/require() in inline scripts.
5. Minimal visible content in body.

Usage: python3 agents/site_validator.py generated/<slug>/index.html
Exit code 0 = pass, 1 = fail (prints problems).
"""

import re
import sys
import urllib.request
from pathlib import Path

TAILWIND_PAT = re.compile(
    r'class="[^"]*\b(?:flex|grid|hidden|block|inline-flex|items-center|justify-between|'
    r'justify-center|gap-\d+|grid-cols-\d+|md:[\w-]+|lg:[\w-]+|sm:[\w-]+|'
    r'text-(?:xs|sm|base|lg|xl|2xl|3xl|4xl|5xl)|font-(?:bold|medium|semibold)|'
    r'mb-\d+|mt-\d+|p-\d+|px-\d+|py-\d+|mx-auto|rounded(?:-lg|-xl|-full)?|'
    r'overflow-hidden|opacity-\d+|transition[\w-]*|hover:[\w-]+|'
    r'tracking-tight|max-w-[\w-]+|space-[xy]-\d+)\b[^"]*"')
_TAILWIND_TOKEN = re.compile(
    r'(?<![\w-])(?:flex|grid|hidden|block|inline-flex|items-center|justify-between|'
    r'justify-center|gap-\d+|grid-cols-\d+|md:[\w-]+|lg:[\w-]+|sm:[\w-]+|'
    r'text-(?:xs|sm|base|lg|xl|2xl|3xl|4xl|5xl)|font-(?:bold|medium|semibold)|'
    r'mb-\d+|mt-\d+|p-\d+|px-\d+|py-\d+|mx-auto|rounded(?:-lg|-xl|-full)?|'
    r'overflow-hidden|opacity-\d+|transition[\w-]*|hover:[\w-]+|'
    r'tracking-tight|max-w-[\w-]+|space-[xy]-\d+)(?![\w-])')


def head_ok(url: str, timeout: int = 12) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(url, method="HEAD",
                                     headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status < 400, f"HTTP {r.status}"
    except Exception as e:
        return False, str(e)[:60]


def validate(path: Path, check_images: bool = True) -> list[str]:
    h = path.read_text(encoding="utf-8")
    problems = []

    # 1. utility classes without framework (check whole class attribute,
    #    then extract bare tokens — avoids matching "services-grid" etc.)
    body = re.search(r'<body[^>]*>(.*)</body>', h, re.DOTALL)
    if body:
        utils = set()
        for attr in TAILWIND_PAT.findall(body.group(1)):
            utils.update(_TAILWIND_TOKEN.findall(attr))
        has_tw = ("cdn.tailwindcss.com" in h or "tailwindcss" in h)
        if utils and not has_tw:
            problems.append(
                f"UTILITY CLASSES bez frameworku ({len(utils)}): "
                + ", ".join(sorted(utils)[:15]))

    # 2. images reachable
    if check_images:
        for url in re.findall(r'<img[^>]*src="(https?://[^"]+)"', h):
            ok, info = head_ok(url)
            if not ok:
                problems.append(f"DEAD IMAGE {info}: {url[:80]}")

    # 3. hamburger needs JS toggle
    if "hamburger" in h.lower():
        scripts = " ".join(re.findall(r'<script[^>]*>(.*?)</script>', h,
                                      re.DOTALL))
        css = " ".join(re.findall(r'<style[^>]*>(.*?)</style>', h, re.DOTALL))
        has_js = bool(re.search(
            r'(hamburger|nav-toggle|menu)[^}]{0,200}(addEventListener|onclick)'
            r'|addEventListener[^}]{0,200}(hamburger)', scripts, re.I | re.S))
        if not has_js:
            problems.append("HAMBURGAR bez JS toggle (mrtvé menu na mobilu)")
        if ".hamburger-btn" not in css and ".hamburger-line" not in css:
            problems.append("HAMBURGAR bez CSS stylů (.hamburger-btn chybí)")

    # 4. browser-hostile calls
    for i, s in enumerate(re.findall(r'<script[^>]*>(.*?)</script>', h,
                                     re.DOTALL)):
        if re.search(r'(?<![.\w])exit\(\)', s):
            problems.append(f"BROWSER exit() v scriptu #{i} — použij return/throw")
        if re.search(r'(?<![.\w])require\(', s):
            problems.append(f"require() v browser scriptu #{i}")

    # 5. minimal content
    if body:
        stripped = re.sub(r'<script.*?</script>|<!--.*?-->', '',
                          body.group(1), flags=re.DOTALL)
        visible = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', stripped)).strip()
        if len(visible) < 200:
            problems.append(f"MÁLO OBSAHU: jen {len(visible)} znaků textu")
    return problems


if __name__ == "__main__":
    targets = sys.argv[1:] or ["generated/test-zahradnik/index.html"]
    failed = 0
    for t in targets:
        p = Path(t)
        probs = validate(p)
        print(f"\n=== {p} ===")
        if probs:
            failed += 1
            for x in probs:
                print("✗", x)
        else:
            print("✓ VŠE OK")
    sys.exit(1 if failed else 0)
