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

# Secondary photos for gallery/about sections — richer visual storytelling
GALLERY_PHOTOS = {
    "tradesman": [
        "photo-1504328345606-18bbc8c9d7d1",  # tools
        "photo-1530124566582-a618bc2615dc",  # workshop
        "photo-1581244277943-fe4a9c777189",  # craftsman at work
        "photo-1416879595882-3373a0480b5b",  # garden path
        "photo-1466692476868-aef1dfb1e735",  # plants
        "photo-1523348837708-15d4a09cfac2",  # hands planting
    ],
    "salon": [
        "photo-1522336572468-97b06e8ef143",
        "photo-1633681926022-84c23e8cb2d6",
        "photo-1595476108010-b4d1f102b1b1",
        "photo-1519415943484-9fa1873496d4",
        "photo-1487412947147-5cebf100ffc2",
        "photo-1516975080664-ed2fc6a32937",
    ],
    "auto": [
        "photo-1487754180451-c456f719a1fc",
        "photo-1503376780353-7e6692767b70",
        "photo-1552519507-da3b142c6e3d",
        "photo-1615906655593-ad0386982a0f",
        "photo-1625047509168-a7026f36de04",
        "photo-1632823471565-1ecdf5c6da05",
    ],
    "gastronomy": [
        "photo-1504674900247-0877df9cc836",
        "photo-1467003909585-2f8a72700288",
        "photo-1540189549336-e6e99c3679fe",
        "photo-1476224203421-9ac39bcb3327",
        "photo-1414235077428-338989a2e8c0",
        "photo-1551218808-94e220e084d2",
    ],
    "health": [
        "photo-1571019613454-1cb2f99b2d8b",
        "photo-1545205597-3d9d02c29597",
        "photo-1552196563-55cd4e45efb3",
        "photo-1599901860904-17e6ed7083a0",
        "photo-1576091160550-2173dba999ef",
        "photo-1538108149393-fbbd81895907",
    ],
    "sport": [
        "photo-1461896836934-ffe607ba8211",
        "photo-1571019614242-c5c5dee9f50b",
        "photo-1540479859555-17af45c78602",
        "photo-1517838277536-f5f99be501cd",
        "photo-1526506118085-60ce8714f8c5",
        "photo-1534438327276-14e5300c3a48",
    ],
}


def hero_photo(industry: str, rng) -> str | None:
    """Pick a deterministic hero photo URL, None if industry unknown."""
    ids = HERO_PHOTOS.get(industry)
    if not ids:
        return None
    pid = rng.choice(ids)
    return f"https://images.unsplash.com/{pid}?auto=format&fit=crop&w=1600&q=70"


def gallery_photos(industry: str, rng, n: int = 3) -> list[str]:
    """Deterministic selection of gallery photos for an industry."""
    ids = GALLERY_PHOTOS.get(industry, [])
    if not ids:
        return []
    picks = rng.sample(ids, min(n, len(ids)))
    return [f"https://images.unsplash.com/{pid}?auto=format&fit=crop&w=800&q=65"
            for pid in picks]


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
