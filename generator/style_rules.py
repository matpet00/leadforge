"""Industry-appropriate template & palette constraints.

Hard rules: an industry only ever gets templates+palettes that make sense
for it. No green gardens on dark ember red, no barbershop in meadow green.

INDUSTRY_STYLE = {industry: (allowed_templates, palette_overrides)}
Palette overrides replace the template's default for that industry, so
e.g. terra+tradesman stays earthy but meadow+tradesman becomes fresh green.
"""

# industry -> allowed templates (all fit the trade visually)
INDUSTRY_TEMPLATES_STRICT = {
    "tradesman":  ["terra", "forge", "monolith", "horizon", "orchard"],
    "salon":      ["zen", "noir", "bloom", "candy", "aurora"],
    "auto":       ["pulse", "forge", "horizon", "monolith", "summit"],
    "gastronomy": ["terra", "ember", "noir", "orchard"],
    "health":     ["zen", "lagoon", "bloom", "horizon"],
    "sport":      ["pulse", "summit", "lagoon", "candy"],
}

# industry-specific palettes: (template, accent, bg0, bg1, text, muted)
INDUSTRY_PALETTES = {
    # gardens = greens, sky, soil-brown accents — never red/dark
    ("tradesman", "meadow"):  {"accent": "#4d7c0f", "bg0": "#f7fee7", "bg1": "#ecfccb", "text": "#1a2e05", "muted": "#65803c"},
    ("tradesman", "orchard"): {"accent": "#3f6212", "bg0": "#f7fee7", "bg1": "#eaf4d5", "text": "#1a2e05", "muted": "#6b8a3a"},
    ("tradesman", "terra"):   {"accent": "#7c5c33", "bg0": "#faf6ef", "bg1": "#efe6d4", "text": "#2d2317", "muted": "#8a7355"},
    ("tradesman", "forge"):   {"accent": "#84cc16", "bg0": "#18181b", "bg1": "#27272a", "text": "#e4e4e7", "muted": "#71717a"},
    ("tradesman", "monolith"):{ "accent": "#84cc16", "bg0": "#111111", "bg1": "#1c1c1c", "text": "#fafafa", "muted": "#a3a3a3"},
    ("tradesman", "horizon"): {"accent": "#3f6212", "bg0": "#f8fafc", "bg1": "#f0fdf0", "text": "#1a2e05", "muted": "#5a6b50"},

    # autoservice = steel blue/graphite/red accents, clean industrial
    ("auto", "pulse"):   {"accent": "#dc2626", "block": "#fee2e2", "ink": "#18181b"},
    ("auto", "forge"):   {"accent": "#38bdf8", "bg0": "#18181b", "bg1": "#27272a", "text": "#e4e4e7", "muted": "#71717a"},
    ("auto", "horizon"): {"accent": "#1e40af", "bg0": "#f8fafc", "bg1": "#eff6ff", "text": "#0f172a", "muted": "#64748b"},
    ("auto", "monolith"):{"accent": "#ef4444", "bg0": "#111111", "bg1": "#1c1c1c", "text": "#fafafa", "muted": "#a3a3a3"},
    ("auto", "summit"):  {"accent": "#2563eb", "bg0": "#0c1a2a", "bg1": "#12263c", "text": "#e0f2fe", "muted": "#7cb0d4"},

    # salon/beauty = rose, violet, champagne — elegant or soft
    ("salon", "zen"):    {"accent": "#9d5c78", "line": "#eedbe4", "wash": "#fdf8fa", "text": "#43263a", "muted": "#a87e93"},
    ("salon", "noir"):   {"accent": "#d4a574", "bg0": "#14100d", "bg1": "#201a15", "text": "#f5ede2", "muted": "#a89480"},
    ("salon", "bloom"):  {"accent": "#db2777", "bg0": "#fff5f9", "bg1": "#fce7f2", "text": "#500724", "muted": "#be6a93"},
    ("salon", "candy"):  {"accent": "#e5529c", "bg0": "#fdf4ff", "bg1": "#fae8ff", "text": "#701a75", "muted": "#c26bd4"},
    ("salon", "aurora"): {"accent": "#e879a6", "bg0": "#17111f", "bg1": "#241a30", "text": "#f3e8ff", "muted": "#c4b5fd"},

    # gastro/restaurant = warm appetite colors — amber, wine, cream
    ("gastronomy", "terra"):   {"accent": "#92400e", "bg0": "#fffbeb", "bg1": "#fef3c7", "text": "#451a03", "muted": "#92703f"},
    ("gastronomy", "ember"):   {"accent": "#ea580c", "bg0": "#1a120b", "bg1": "#292018", "text": "#fef3c7", "muted": "#d4a574"},
    ("gastronomy", "noir"):    {"accent": "#d4af37", "bg0": "#0a0a0a", "bg1": "#161616", "text": "#faf5eb", "muted": "#a89f91"},
    ("gastronomy", "orchard"): {"accent": "#65a30d", "bg0": "#fefce8", "bg1": "#f5f0dc", "text": "#365314", "muted": "#85934f"},

    # health = calm teal/mint/blue — trust and cleanliness
    ("health", "zen"):    {"accent": "#2f7d74", "line": "#d2ebe7", "wash": "#f7fcfb", "text": "#134e4a", "muted": "#5e8a84"},
    ("health", "lagoon"): {"accent": "#0891b2", "bg0": "#ecfeff", "bg1": "#cffafe", "text": "#083344", "muted": "#4f96a8"},
    ("health", "bloom"):  {"accent": "#0d9488", "bg0": "#f0fdfa", "bg1": "#ccfbf1", "text": "#134e4a", "muted": "#5ea89e"},
    ("health", "horizon"):{"accent": "#0369a1", "bg0": "#f8fafc", "bg1": "#f0f9ff", "text": "#082f49", "muted": "#5a83a3"},

    # sport = energy — vivid orange/electric blue/violet
    ("sport", "pulse"):  {"accent": "#f97316", "block": "#ffedd5", "ink": "#1c1917"},
    ("sport", "summit"): {"accent": "#0ea5e9", "bg0": "#0c1a2a", "bg1": "#12263c", "text": "#e0f2fe", "muted": "#7cb0d4"},
    ("sport", "lagoon"): {"accent": "#0284c7", "bg0": "#f0f9ff", "bg1": "#dff2fd", "text": "#082f49", "muted": "#4f96a8"},
    ("sport", "candy"):  {"accent": "#8b5cf6", "bg0": "#faf5ff", "bg1": "#f3e8ff", "text": "#3b0764", "muted": "#9a6bc4"},
}


def constrain(lead, template, default_palette):
    """Return a palette appropriate for this lead's industry+template."""
    key = (lead["industry"], template)
    if key in INDUSTRY_PALETTES:
        return dict(INDUSTRY_PALETTES[key])
    return default_palette


def is_allowed(lead, template) -> bool:
    allowed = INDUSTRY_TEMPLATES_STRICT.get(lead["industry"])
    return template in allowed if allowed else True
