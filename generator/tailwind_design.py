"""Tailwind CSS demo variants — modern utility-first look.

Uses the Tailwind Play CDN (free, no build step) so demos stay single-file
while showcasing a completely different aesthetic than our custom templates.
These are "additional variants" alongside the 15 design personalities —
same content sections (hero/services/about/gallery/stats/contact/maps),
Tailwind styling.

Template keys: tw-<name>, rendered by render_site_tw() in site_builder.
"""

TW_HEAD = """<script src="https://cdn.tailwindcss.com"></script>
<script>
tailwind.config = {
  theme: { extend: { colors: { brand: ACCENT_HEX }, fontFamily: { sans: FONT_STACK } } }
}
</script>"""

# Tailwind template personalities: (name, accent, hero_style, font)
TW_TEMPLATES = {
    # clean SaaS-like: white bg, indigo accents, rounded-2xl cards
    "tw-saas": {"accent": "#4f46e5", "font": "'Inter', system-ui, sans-serif",
                "style": "saas"},
    # warm gradient: orange-pink gradients on light bg
    "tw-gradient": {"accent": "#f97316", "font": "'Plus Jakarta Sans', system-ui",
                    "style": "gradient"},
    # dark mode: slate-900 bg, emerald accents
    "tw-dark": {"accent": "#10b981", "font": "'Outfit', system-ui",
                "style": "dark"},
    # playful: sky-blue with big rounded elements
    "tw-playful": {"accent": "#0ea5e9", "font": "'Nunito', system-ui",
                   "style": "playful"},
}

TW_INDUSTRY_BIAS = {
    "tradesman": ["tw-gradient", "tw-dark"],
    "salon": ["tw-playful", "tw-gradient"],
    "auto": ["tw-dark", "tw-saas"],
    "gastronomy": ["tw-gradient", "tw-saas"],
    "health": ["tw-saas", "tw-playful"],
    "sport": ["tw-dark", "tw-playful"],
}


def pick_tw_template(lead) -> str:
    import hashlib
    seed = int(hashlib.sha256(
        f"{lead['ico']}:tw".encode()).hexdigest()[:8], 16)
    bias = TW_INDUSTRY_BIAS.get(lead["industry"], list(TW_TEMPLATES))
    return bias[seed % len(bias)]
