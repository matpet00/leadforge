"""Design variation engine — every site gets a unique visual identity.

Per-industry base + deterministic-but-varied picks from:
  - layout (hero split / centered / overlay)
  - font pairing (Google Fonts, 6 options)
  - color palette per industry (3 variants each)
  - decorative style (blobs / grid lines / waves / minimal)
  - card treatment (elevated / bordered / filled)

Same company always renders identically (seeded by ICO/name hash),
different companies look genuinely different.
"""

import hashlib
import random

# ---------------------------------------------------------------- palettes

PALETTES = {
    "tradesman": [
        {"accent": "#c2410c", "dark": "#431407", "soft": "#fff7ed", "mode": "warm"},
        {"accent": "#0f766e", "dark": "#042f2e", "soft": "#f0fdfa", "mode": "cool"},
        {"accent": "#b45309", "dark": "#451a03", "soft": "#fffbeb", "mode": "amber"},
    ],
    "salon": [
        {"accent": "#be185d", "dark": "#500724", "soft": "#fdf2f8", "mode": "rose"},
        {"accent": "#7c3aed", "dark": "#2e1065", "soft": "#f5f3ff", "mode": "violet"},
        {"accent": "#db2777", "dark": "#831843", "soft": "#fce7f3", "mode": "pink"},
    ],
    "auto": [
        {"accent": "#1d4ed8", "dark": "#172554", "soft": "#eff6ff", "mode": "blue"},
        {"accent": "#dc2626", "dark": "#450a0a", "soft": "#fef2f2", "mode": "red"},
        {"accent": "#334155", "dark": "#020617", "soft": "#f1f5f9", "mode": "steel"},
    ],
    "gastronomy": [
        {"accent": "#15803d", "dark": "#052e16", "soft": "#f0fdf4", "mode": "green"},
        {"accent": "#92400e", "dark": "#451a03", "soft": "#fefce8", "mode": "coffee"},
        {"accent": "#b91c1c", "dark": "#450a0a", "soft": "#fef2f2", "mode": "wine"},
    ],
    "health": [
        {"accent": "#0e7490", "dark": "#083344", "soft": "#ecfeff", "mode": "cyan"},
        {"accent": "#059669", "dark": "#022c22", "soft": "#ecfdf5", "mode": "mint"},
        {"accent": "#4f46e5", "dark": "#1e1b4b", "soft": "#eef2ff", "mode": "indigo"},
    ],
    "sport": [
        {"accent": "#ea580c", "dark": "#431407", "soft": "#fff7ed", "mode": "energy"},
        {"accent": "#16a34a", "dark": "#052e16", "soft": "#f0fdf4", "mode": "field"},
        {"accent": "#2563eb", "dark": "#172554", "soft": "#dbeafe", "mode": "arena"},
    ],
    "other": [
        {"accent": "#334155", "dark": "#0f172a", "soft": "#f8fafc", "mode": "slate"},
    ],
}

FONTS = [
    ("Inter:wght@400;600;800", "'Inter', system-ui, sans-serif"),
    ("Work+Sans:wght@400;600;800", "'Work Sans', system-ui, sans-serif"),
    ("Sora:wght@400;600;800", "'Sora', system-ui, sans-serif"),
    ("Manrope:wght@400;600;800", "'Manrope', system-ui, sans-serif"),
    ("Outfit:wght@400;600;800", "'Outfit', system-ui, sans-serif"),
    ("Plus+Jakarta+Sans:wght@400;600;800", "'Plus Jakarta Sans', system-ui, sans-serif"),
]

LAYOUTS = ["split", "centered", "overlay"]
DECOR = ["blobs", "gridlines", "waves", "diagonal"]
CARDS = ["elevated", "bordered", "filled"]

# Hand-picked stable Unsplash photos (free license, commercial OK).
# Curated per industry; hot-linked at render time with width params.
HERO_PHOTOS = {
    "tradesman": [
        "photo-1504307651254-35680f356dfd",
        "photo-1581094794329-c8112a89af12",
        "photo-1621905251189-08b45d6a269e",
    ],
    "salon": [
        "photo-1560066984-138dadb4c035",
        "photo-1522337660859-02fbefca4702",
        "photo-1562322140-8baeececf3df",
    ],
    "auto": [
        "photo-1486262715619-67b85e0b08d3",
        "photo-1493238792000-8113da705763",
        "photo-1530046339160-ce3e530c7d2f",
    ],
    "gastronomy": [
        "photo-1517248135467-4c7edcad34c4",
        "photo-1414235077428-338989a2e8c0",
        "photo-1552566626-52f8b828add9",
    ],
    "health": [
        "photo-1571019613454-1cb2f99b2d8b",
        "photo-1544367567-0f2fcb009e0b",
        "photo-1591343395082-e120087004b4",
    ],
    "sport": [
        "photo-1461896836934-ffe607ba8211",
        "photo-1552674605-db6ffd4facb5",
        "photo-1517836357463-d25dfeac3438",
    ],
}


def hero_photo(industry: str, rng) -> str | None:
    """Pick a deterministic hero photo URL, None if industry unknown."""
    ids = HERO_PHOTOS.get(industry)
    if not ids:
        return None
    pid = rng.choice(ids)
    return f"https://images.unsplash.com/{pid}?auto=format&fit=crop&w=1600&q=70"


def pick_variant(lead) -> dict:
    """Deterministic unique variant for this lead."""
    seed = int(hashlib.sha256(
        f"{lead['ico']}:{lead['company_name']}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    industry = lead["industry"] if lead["industry"] in PALETTES else "other"
    return {
        "palette": rng.choice(PALETTES[industry]),
        "font": rng.choice(FONTS),
        "layout": rng.choice(LAYOUTS),
        "decor": rng.choice(DECOR),
        "cards": rng.choice(CARDS),
        "hero_align": rng.choice(["left", "center"]),
        "hero_photo": hero_photo(industry, rng),
    }
