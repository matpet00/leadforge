"""Design system v3 — 15 professional site personalities, industry-aware.

Templates (each a complete standalone design philosophy):
  AURORA    dark premium, glass cards, glow accents
  TERRA     warm craft, serif display, earthy cream
  PULSE     bold energy, huge type, angled blocks
  ZEN       airy minimal, thin lines, whitespace
  MONOLITH  brutalist-modern: massive type, black/white + one accent
  HORIZON   corporate clean: blue tones, structured grid, trustworthy
  BLOOM     organic rounded: soft shapes, gradients, friendly
  FORGE     industrial: steel textures, strong borders, utilitarian
  MEADOW    natural fresh: greens, light, airy photos
  NOIR      elegant dark: near-black, gold/champagne accent, luxury
  CANDY     playful bright: pastel cards, rounded everything
  SUMMIT    mountain-strong: deep navy, sharp edges, confident
  LAGOON    aqua fresh: teal/cyan, water vibes, smooth curves
  EMBER     warm fire: red/orange on charcoal, passionate
  ORCHARD   village-local: warm green/beige, honest and simple

Industry bias maps each trade to its 4 best-fit templates.
Every template includes: contact section with phone/email cards,
Google Maps embed for the company city, opening-hours style info block.
"""

import hashlib

TEMPLATES = ["aurora", "terra", "pulse", "zen", "monolith", "horizon",
             "bloom", "forge", "meadow", "noir", "candy", "summit",
             "lagoon", "ember", "orchard"]

INDUSTRY_TEMPLATES = {
    "tradesman":  ["forge", "terra", "monolith", "ember"],
    "salon":      ["zen", "noir", "bloom", "candy"],
    "auto":       ["pulse", "forge", "horizon", "monolith"],
    "gastronomy": ["terra", "noir", "ember", "bloom"],
    "health":     ["zen", "lagoon", "horizon", "bloom"],
    "sport":      ["pulse", "summit", "ember", "candy"],
}


def pick_template(lead) -> str:
    seed = int(hashlib.sha256(
        f"{lead['ico']}:{lead['company_name']}".encode()).hexdigest()[:8], 16)
    bias = INDUSTRY_TEMPLATES.get(lead["industry"], TEMPLATES)
    if seed % 10 < 7:
        return bias[seed % len(bias)]
    return TEMPLATES[seed % len(TEMPLATES)]


# palette per template per industry: (accent, bg0/page, bg1/section, text, muted)
PALETTES = {
    "aurora": {
        "_":        {"accent": "#818cf8", "bg0": "#0b1024", "bg1": "#141a33", "text": "#e2e8f0", "muted": "#94a3b8"},
    },
    "terra": {
        "_":        {"accent": "#9a3412", "bg0": "#fdf6ee", "bg1": "#f5ead9", "text": "#292524", "muted": "#78716c"},
    },
    "pulse": {
        "_":        {"accent": "#ea580c", "block": "#ffedd5", "ink": "#1c1917"},
    },
    "zen": {
        "_":        {"accent": "#57534e", "line": "#d6d3d1", "wash": "#faf9f7", "text": "#292524", "muted": "#78716c"},
    },
    "monolith": {
        "_":        {"accent": "#facc15", "bg0": "#111111", "bg1": "#1c1c1c", "text": "#fafafa", "muted": "#a3a3a3"},
    },
    "horizon": {
        "_":        {"accent": "#1d4ed8", "bg0": "#f8fafc", "bg1": "#eff6ff", "text": "#0f172a", "muted": "#64748b"},
    },
    "bloom": {
        "_":        {"accent": "#db2777", "bg0": "#fff5f9", "bg1": "#fce7f2", "text": "#500724", "muted": "#be6a93"},
    },
    "forge": {
        "_":        {"accent": "#f97316", "bg0": "#18181b", "bg1": "#27272a", "text": "#e4e4e7", "muted": "#71717a"},
    },
    "meadow": {
        "_":        {"accent": "#4d7c0f", "bg0": "#f7fee7", "bg1": "#ecfccb", "text": "#1a2e05", "muted": "#65803c"},
    },
    "noir": {
        "_":        {"accent": "#d4af37", "bg0": "#0a0a0a", "bg1": "#161616", "text": "#faf5eb", "muted": "#a89f91"},
    },
    "candy": {
        "_":        {"accent": "#ec4899", "bg0": "#fdf4ff", "bg1": "#fae8ff", "text": "#701a75", "muted": "#c26bd4"},
    },
    "summit": {
        "_":        {"accent": "#0ea5e9", "bg0": "#0c1a2a", "bg1": "#12263c", "text": "#e0f2fe", "muted": "#7cb0d4"},
    },
    "lagoon": {
        "_":        {"accent": "#0891b2", "bg0": "#ecfeff", "bg1": "#cffafe", "text": "#083344", "muted": "#4f96a8"},
    },
    "ember": {
        "_":        {"accent": "#ef4444", "bg0": "#1a0e0c", "bg1": "#2a1512", "text": "#fee2e2", "muted": "#c98a80"},
    },
    "orchard": {
        "_":        {"accent": "#65a30d", "bg0": "#fefce8", "bg1": "#f5f0dc", "text": "#365314", "muted": "#85934f"},
    },
}

# Google Fonts pairing per template
FONTS = {
    "aurora":   ("Sora:wght@300;400;600", "'Sora', system-ui, sans-serif"),
    "terra":    ("Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700", "'Fraunces', Georgia, serif"),
    "pulse":    ("Archivo:wght@500;700;900", "'Archivo', system-ui, sans-serif"),
    "zen":      ("Shippori+Mincho:wght@400;600", "'Shippori Mincho', 'Times New Roman', serif"),
    "monolith": ("Space+Grotesk:wght@400;600;700", "'Space Grotesk', system-ui, sans-serif"),
    "horizon":  ("IBM+Plex+Sans:wght@400;600;700", "'IBM Plex Sans', system-ui, sans-serif"),
    "bloom":    ("Nunito:wght@400;600;800", "'Nunito', system-ui, sans-serif"),
    "forge":    ("Oswald:wght@400;600;700", "'Oswald', system-ui, sans-serif"),
    "meadow":   ("Quicksand:wght@400;600;700", "'Quicksand', system-ui, sans-serif"),
    "noir":     ("Cormorant+Garamond:wght@400;600;700", "'Cormorant Garamond', Georgia, serif"),
    "candy":    ("Baloo+2:wght@400;600;800", "'Baloo 2', system-ui, sans-serif"),
    "summit":   ("Barlow+Condensed:wght@400;600;800", "'Barlow Condensed', system-ui, sans-serif"),
    "lagoon":   ("Karla:wght@400;600;800", "'Karla', system-ui, sans-serif"),
    "ember":    ("Bitter:wght@400;600;800", "'Bitter', Georgia, serif"),
    "orchard":  ("Source+Sans+3:wght@400;600;700", "'Source Sans 3', system-ui, sans-serif"),
}


def get_design(lead) -> dict:
    import random
    import hashlib
    seed = int(hashlib.sha256(
        f"{lead['ico']}:{lead['company_name']}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    tpl = pick_template(lead)
    gf, stack = FONTS[tpl]
    return {
        "template": tpl,
        "palette": PALETTES[tpl]["_"],
        "google_font": gf.replace("|", "&family="),
        "font_stack": stack,
        "photo_seed": seed % 3,
        "layout_seed": seed % 100,
    }
