"""Replace emoji with inline SVG icons — emoji don't render in headless
browsers (empty boxes on screenshots) and vary across OS."""

from pathlib import Path

GEN = Path(__file__).resolve().parent / "generator"

PHONE_SVG = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">'
             '<path d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.9 21 3 13.1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.2.2 2.4.6 3.6.1.3 0 .7-.2 1l-2.3 2.2z"/></svg>')
MAIL_SVG = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
            '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M22 7l-10 6L2 7"/></svg>')
PIN_SVG = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">'
           '<path d="M12 2C8.1 2 5 5.1 5 9c0 5.2 7 13 7 13s7-7.8 7-13c0-3.9-3.1-7-7-7zm0 9.5A2.5 2.5 0 1112 6a2.5 2.5 0 010 5.5z"/></svg>')
CLOCK_SVG = ('<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
             '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>')

# ---- shell.py: contact cards ----
p = GEN / "shell.py"
src = p.read_text()
src = src.replace('<span class="ci">📞</span>', f'<span class="ci">{PHONE_SVG}</span>')
src = src.replace('<span class="ci">✉️</span>', f'<span class="ci">{MAIL_SVG}</span>')
src = src.replace('<span class="ci">📍</span>', f'<span class="ci">{PIN_SVG}</span>')
p.write_text(src)
print("shell.py done")

# ---- site_builder.py: hero button + hours ----
p = GEN / "site_builder.py"
src = p.read_text()
import re as _re
n_before = src.count("📞")
src = src.replace('📞 {copy["cta"]}', f'{PHONE_SVG} {{copy["cta"]}}')
src = _re.sub(r'📞 \{\{ cta \}\}', f'{PHONE_SVG} {{{{ cta }}}}', src)
src = src.replace('🕒 ', f'{CLOCK_SVG} ')
p.write_text(src)
print(f"site_builder done ({n_before} phone emoji found)")

# ---- tailwind_renderer.py ----
p = GEN / "tailwind_renderer.py"
src = p.read_text()
src = src.replace(">📞 {{ cta }}<", f">{PHONE_SVG} {{{{ cta }}}}<")
src = src.replace('<div class="text-2xl mb-2">📞</div>', f'<div class="text-brand mb-2">{PHONE_SVG}</div>')
src = src.replace('<div class="text-2xl mb-2">✉️</div>', f'<div class="text-brand mb-2">{MAIL_SVG}</div>')
src = src.replace('<div class="text-2xl mb-2">📍</div>', f'<div class="text-brand mb-2">{PIN_SVG}</div>')
src = src.replace("🕒 {{ hours }}", f"{CLOCK_SVG} {{{{ hours }}}}")
p.write_text(src)
print("tailwind_renderer done")
