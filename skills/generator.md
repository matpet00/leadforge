# Generator Agent — Design & Coding Policy (v2, 2026-08)

Research basis: top one-page templates (HTML5UP Spectral/Dimension, StartBootstrap
Creative/Grayscale/Resume) + current web standards. These are proven patterns from
the most popular open-source one-pagers — follow them.

## Structure (pattern shared by ALL top one-page templates)
1. **Fixed nav** — logo left, anchor links right, collapses to hamburger on mobile
2. **Full-height hero** — big headline, subline, ONE primary CTA button
3. **Services/features grid** — 3 columns desktop → 1 mobile, icon + short title + 1 sentence each
4. **About/trust strip** — photo or stats band (years, projects — ONLY if true)
5. **Contact section** — form OR prominent phone/email cards
6. **Footer** — IČO, address, copyright

## Visual style (2025-26 best practice)
- Mobile-first: base CSS for phones, min-width media queries up
- System font stack first line, optional Google Font for headings only (Inter/Work Sans)
- Spacing scale: 4/8/16/24/48px; section padding 64-96px vertical
- Max content width 1100-1200px centered; text max 65ch
- Contrast: WCAG AA minimum (4.5:1 body, 3:1 large text); never light-gray-on-white
- Accent color used ONLY for CTA + links + icons — 90% neutral palette
- Border-radius 8-12px on cards/buttons; subtle shadow (0 2px 8px rgba(0,0,0,.08))
- Smooth scroll for anchors; respect prefers-reduced-motion
- Dark mode: NOT required for these businesses — skip (consistency > trend)

## Coding policy
- Single self-contained HTML file, inline <style>, NO external JS frameworks
- Semantic HTML5: header/nav/main/section/footer, h1 exactly once
- Images: none required; if needed use inline SVG icons (stroke style, 24px grid)
- Performance budget: page < 50KB total, zero render-blocking requests
- Accessibility: alt texts, aria-labels on icon buttons, focus-visible styles,
  color contrast per above, lang=cs, logical heading order
- Meta: description ≤155 chars, og:title/description, LocalBusiness JSON-LD
- No console errors, no placeholder text in production output

## Copy rules (unchanged, still binding)
- Formal Vy/Váš; concrete over abstract; RZP scope is the only source of truth;
  NEVER invent prices/reviews/experience; clichés ("spolehlivý partner") sparingly.
