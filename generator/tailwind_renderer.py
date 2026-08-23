"""Tailwind one-pager renderer — modern utility-first demo variant."""

from jinja2 import Environment

TW_SHELL = """<!DOCTYPE html>
<html lang="cs" class="scroll-smooth">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ company }}{% if city %} — {{ city }}{% endif %}</title>
{{ seo_block }}
<script src="https://cdn.tailwindcss.com"></script>
<script>
tailwind.config = { theme: { extend: {
  colors: { brand: { DEFAULT: '{{ accent }}', dark: '{{ accent_dark }}' } },
  fontFamily: { sans: ['{{ font_family }}'] }
}}}
</script>
</head>
<body class="font-sans antialiased {{ body_bg }} {{ body_text }}">

<!-- NAV -->
<nav class="fixed top-0 inset-x-0 z-50 backdrop-blur-md {{ nav_bg }} border-b {{ nav_border }}">
  <div class="max-w-6xl mx-auto px-5 h-16 flex items-center justify-between">
    <a href="#top" class="text-xl font-extrabold tracking-tight">{{ logo_word }}<span class="text-brand">.</span></a>
    <div class="hidden md:flex gap-8 text-sm font-semibold">
      <a href="#sluzby" class="{{ link_cls }} hover:text-brand transition">Služby</a>
      <a href="#o-nas" class="{{ link_cls }} hover:text-brand transition">O nás</a>
      <a href="#galerie" class="{{ link_cls }} hover:text-brand transition">Galerie</a>
      <a href="#kontakt" class="{{ link_cls }} hover:text-brand transition">Kontakt</a>
    </div>
    <a href="tel:{{ phone }}" class="hidden md:inline-flex bg-brand text-white px-5 py-2.5 rounded-xl font-bold hover:opacity-90 hover:-translate-y-0.5 transition shadow-lg shadow-brand/25">{{ cta }}</a>
    <input type="checkbox" id="mnav" class="peer hidden">
    <label for="mnav" class="md:hidden cursor-pointer p-2 rounded-lg {{ link_cls }}" aria-label="Menu">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
    </label>
  </div>
  <div class="md:hidden hidden peer-checked:block border-t {{ nav_border }} {{ mobile_bg }}">
    <div class="px-5 py-3 flex flex-col gap-1 text-sm font-semibold">
      <a href="#sluzby" class="py-2.5 {{ link_cls }}">Služby</a>
      <a href="#o-nas" class="py-2.5 {{ link_cls }}">O nás</a>
      <a href="#galerie" class="py-2.5 {{ link_cls }}">Galerie</a>
      <a href="#kontakt" class="py-2.5 {{ link_cls }}">Kontakt</a>
    </div>
  </div>
</nav>

<!-- HERO -->
<header id="top" class="{{ hero_classes }}">
  <div class="max-w-6xl mx-auto px-5 {{ hero_inner }}">
    <span class="inline-block text-xs font-extrabold tracking-widest uppercase mb-5 px-4 py-1.5 rounded-full {{ badge_cls }}">{{ badge }}</span>
    <h1 class="text-4xl md:text-6xl font-black leading-[1.05] tracking-tight mb-5 max-w-3xl {{ h1_cls }}">{{ headline }}</h1>
    <p class="text-lg md:text-xl mb-8 max-w-xl {{ p_cls }}">{{ subhead }}</p>
    <div class="flex flex-wrap gap-4">
      <a href="tel:{{ phone }}" class="bg-brand text-white px-8 py-4 rounded-2xl font-bold hover:scale-105 hover:shadow-2xl hover:shadow-brand/30 transition inline-flex items-center gap-2">📞 {{ cta }}</a>
      <a href="#sluzby" class="px-8 py-4 rounded-2xl font-bold {{ btn2_cls }} transition">Naše služby</a>
    </div>
    {% if stats %}
    <div class="flex flex-wrap gap-10 mt-14">
      {% for st in stats %}
      <div><b class="block text-3xl md:text-4xl font-black text-brand">{{ st[0] }}</b><span class="text-sm {{ stat_lbl }}">{{ st[1] }}</span></div>
      {% endfor %}
    </div>
    {% endif %}
  </div>
</header>

<main>
<!-- SERVICES -->
<section id="sluzby" class="py-24 {{ services_bg }}">
  <div class="max-w-6xl mx-auto px-5">
    <div class="kicker text-brand text-xs font-extrabold uppercase tracking-[0.18em] mb-3">{{ services_kicker }}</div>
    <h2 class="text-3xl md:text-4xl font-black tracking-tight mb-12">{{ services_title }}</h2>
    <div class="grid sm:grid-cols-2 lg:grid-cols-{{ grid_cols }} gap-6">
      {% for s in services %}
      <article class="group p-7 rounded-3xl {{ card_cls }} hover:-translate-y-1.5 hover:shadow-2xl transition duration-300">
        <div class="w-12 h-12 rounded-2xl bg-brand/10 text-brand flex items-center justify-center mb-5 group-hover:bg-brand group-hover:text-white transition">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1z"/></svg>
        </div>
        <h3 class="font-bold text-lg mb-2">{{ s }}</h3>
        <p class="text-sm leading-relaxed opacity-70">{{ card_text }}</p>
      </article>
      {% endfor %}
    </div>
  </div>
</section>

<!-- ABOUT + GALLERY -->
<section id="o-nas" class="py-24 {{ about_bg }}">
  <div class="max-w-6xl mx-auto px-5 grid lg:grid-cols-2 gap-14 items-center">
    <div>
      <div class="kicker text-brand text-xs font-extrabold uppercase tracking-[0.18em] mb-3">O nás</div>
      <h2 class="text-3xl md:text-4xl font-black tracking-tight mb-6">{{ company }}</h2>
      <p class="text-lg opacity-80 mb-8 leading-relaxed">{{ about }}</p>
      {% if hours %}<p class="text-sm font-bold opacity-60">🕒 {{ hours }}</p>{% endif %}
    </div>
    {% if gallery %}
    <div class="grid grid-cols-2 gap-4">
      {% for g in gallery[:2] %}
      <div class="rounded-3xl bg-cover bg-center aspect-[4/5] shadow-xl hover:scale-[1.03] transition duration-500 {{ 'mt-10' if loop.index0 == 1 else '' }}"
           style="background-image:url('{{ g }}')" role="img" aria-label="Ukázka {{ loop.index }}"></div>
      {% endfor %}
    </div>
    {% endif %}
  </div>
</section>

{% if gallery and gallery|length > 2 %}
<section id="galerie" class="py-24 {{ services_bg }}">
  <div class="max-w-6xl mx-auto px-5">
    <h2 class="text-3xl md:text-4xl font-black tracking-tight mb-12">Naše práce</h2>
    <div class="grid sm:grid-cols-3 gap-5">
      {% for g in gallery %}
      <div class="aspect-video rounded-3xl bg-cover bg-center shadow-lg hover:scale-[1.03] hover:rotate-1 transition duration-500"
           style="background-image:url('{{ g }}')" role="img" aria-label="Ukázka práce"></div>
      {% endfor %}
    </div>
  </div>
</section>
{% endif %}

<!-- CONTACT -->
<section id="kontakt" class="py-24 {{ contact_bg }} {{ contact_text }}">
  <div class="max-w-6xl mx-auto px-5">
    <div class="kicker text-brand text-xs font-extrabold uppercase tracking-[0.18em] mb-3">Kontakt</div>
    <h2 class="text-3xl md:text-4xl font-black tracking-tight mb-12">Ozvěte se nám</h2>
    <div class="grid sm:grid-cols-3 gap-5 mb-14">
      {% if phone_display != '+420****0000' %}
      <a href="tel:{{ phone }}" class="p-6 rounded-3xl {{ cc_cls }} hover:-translate-y-1 transition block">
        <div class="text-2xl mb-2">📞</div><b class="block text-xs uppercase tracking-wider mb-1 opacity-60">Telefon</b>
        <span class="font-bold">{{ phone_display }}</span></a>
      {% endif %}
      {% if email %}
      <a href="mailto:{{ email }}" class="p-6 rounded-3xl {{ cc_cls }} hover:-translate-y-1 transition block">
        <div class="text-2xl mb-2">✉️</div><b class="block text-xs uppercase tracking-wider mb-1 opacity-60">E-mail</b>
        <span class="font-bold break-all">{{ email }}</span></a>
      {% endif %}
      <div class="p-6 rounded-3xl {{ cc_cls }}">
        <div class="text-2xl mb-2">📍</div><b class="block text-xs uppercase tracking-wider mb-1 opacity-60">Sídlo</b>
        <span class="font-bold">{{ address or city or 'Česká republika' }}</span>
      </div>
    </div>
    <!-- MAP -->
    <div id="kde" class="rounded-3xl overflow-hidden shadow-2xl {{ map_wrap }}">
      <iframe title="Mapa — {{ company }}" src="{{ maps_embed }}" width="100%" height="360"
              style="border:0" loading="lazy" allowfullscreen referrerpolicy="no-referrer-when-downgrade"></iframe>
    </div>
    <p class="mt-4 text-sm opacity-60 font-semibold">{{ address or city }}</p>
  </div>
</section>
</main>

<footer class="py-9 {{ footer_bg }} {{ footer_text }}">
  <div class="max-w-6xl mx-auto px-5 flex flex-wrap gap-3 justify-between text-sm">
    <span>&copy; {{ year }} {{ company }}{% if ico %} · IČO {{ ico }}{% endif %}</span>
    <span>{{ city }}</span>
  </div>
</footer>

<script>
// reveal on scroll
const io=new IntersectionObserver(es=>es.forEach((e,i)=>{
  if(e.isIntersecting){setTimeout(()=>e.target.classList.add('reveal-in'),i*80);io.unobserve(e.target)}
}),{threshold:.12});
document.querySelectorAll('main section, .hero-reveal').forEach(el=>{
  el.classList.add('reveal-out');io.observe(el)});
</script>
<style>
.reveal-out{opacity:0;transform:translateY(22px);transition:opacity .65s ease,transform .65s ease}
.reveal-in{opacity:1;transform:none!important}
@media(prefers-reduced-motion:reduce){.reveal-out{opacity:1;transform:none;transition:none}}
html{scroll-padding-top:80px}
</script>
</body></html>"""


def render_tw(lead, copy: dict, design: dict) -> str:
    """Render a Tailwind-styled site. design = get_design()-like dict with tw template."""
    from generator.tailwind_design import TW_TEMPLATES
    from generator.shell import maps_embed
    import time as _t

    tw = TW_TEMPLATES[design["template"]]
    accent = design["palette"].get("accent", tw["accent"])
    # darken accent ~35% for hover/gradient ends
    def darken(hex_c, f=0.62):
        h = hex_c.lstrip("#"); r,g,b = int(h[:2],16),int(h[2:4],16),int(h[4:],16)
        return f"#{int(r*f):02x}{int(g*f):02x}{int(b*f):02x}"
    style = tw["style"]

    if style == "saas":
        body_bg, body_text = "bg-white", "text-slate-900"
        nav_bg, nav_border, link_cls, mobile_bg = "bg-white/85", "border-slate-200", "text-slate-600", "bg-white"
        hero_classes = "pt-36 pb-24 bg-gradient-to-b from-indigo-50 to-white"
        badge = "Služby na míru"; badge_cls = "bg-indigo-100 text-indigo-700"
        card_cls = "bg-white border border-slate-200 shadow-sm"
        about_bg, services_bg = "bg-slate-50", "bg-white"
        contact_bg, contact_text, cc_cls = "bg-slate-900", "text-white", "bg-slate-800/70 border border-slate-700"
        footer_bg, footer_text, map_wrap = "bg-slate-950", "text-slate-400", ""
        btn2_cls = "border-2 border-slate-300 hover:border-slate-900"
    elif style == "gradient":
        body_bg, body_text = "bg-orange-50", "text-stone-900"
        nav_bg, nav_border, link_cls, mobile_bg = "bg-orange-50/85", "border-orange-200/60", "text-stone-700", "bg-orange-50"
        hero_classes = ("pt-36 pb-28 bg-gradient-to-br from-orange-400 via-rose-400 to-pink-500 "
                        "text-white relative overflow-hidden")
        badge = "Zahradní služba srdcem"; badge_cls = "bg-white/20 text-white"
        card_cls = "bg-white/80 backdrop-blur border border-orange-100"
        about_bg, services_bg = "bg-white", "bg-gradient-to-b from-white to-orange-50"
        contact_bg, contact_text, cc_cls = "bg-stone-900", "text-white", "bg-stone-800/60 border border-stone-700"
        footer_bg, footer_text, map_wrap = "bg-black", "text-stone-400", "shadow-2xl shadow-orange-300/40"
        btn2_cls = "border-2 border-white/50 text-white hover:bg-white/10"
    elif style == "dark":
        body_bg, body_text = "bg-slate-950", "text-emerald-50"
        nav_bg, nav_border, link_cls, mobile_bg = "bg-slate-950/85", "border-slate-800", "text-emerald-100/80", "bg-slate-950"
        hero_classes = "pt-40 pb-32 bg-[radial-gradient(ellipse_at_top,_rgba(16,185,129,.15),_transparent_55%)] bg-slate-950"
        badge = "Moderní řešení"; badge_cls = "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
        card_cls = "bg-slate-900 border border-slate-800"
        about_bg, services_bg = "bg-slate-900/50", "bg-slate-950"
        contact_bg, contact_text, cc_cls = "bg-slate-900/60", "text-white", "bg-slate-800/60 border border-slate-700"
        footer_bg, footer_text, map_wrap = "bg-black", "text-slate-500", "border border-slate-800"
        btn2_cls = "border-2 border-emerald-500/40 text-emerald-400 hover:bg-emerald-500/10"
    else:  # playful
        body_bg, body_text = "bg-sky-50", "text-cyan-950"
        nav_bg, nav_border, link_cls, mobile_bg = "bg-sky-50/90", "border-sky-200", "text-cyan-900", "bg-sky-50"
        hero_classes = "pt-36 pb-24 bg-[radial-gradient(circle_at_20%_20%,#e0f2fe,transparent_50%),radial-gradient(circle_at_80%_10%,#cffafe,transparent_45%)] bg-sky-50"
        badge = "Vše s úsměvem"; badge_cls = "bg-sky-200/70 text-sky-800"
        card_cls = "bg-white border-2 border-sky-100 rounded-[2rem]"
        about_bg, services_bg = "bg-white", "bg-sky-50"
        contact_bg, contact_text, cc_cls = "bg-gradient-to-r from-sky-600 to-cyan-600", "text-white", "bg-white/10 border border-white/20"
        footer_bg, footer_text, map_wrap = "bg-cyan-950", "text-sky-300", ""
        btn2_cls = "border-2 border-cyan-900/20 hover:border-cyan-800"

    words = [w for w in __import__("re").split(r"[\s—-]+", lead["company_name"]) if len(w) > 2]
    logo_word = words[0] if words else lead["company_name"]

    env = Environment()
    import re as _re, time as _t
    phone_raw = (lead["phone"] or "+420****0000").replace(" ", "")
    from generator.site_builder import seo_block, INDUSTRY_THEMES
    return env.from_string(TW_SHELL).render(
        company=lead["company_name"], logo_word=logo_word,
        city=lead["city"], ico=lead["ico"], address=lead["address"],
        phone=phone_raw,
        phone_display=lead["phone"] or "+420****0000",
        email=lead["email"], year=_t.strftime("%Y"),
        seo_block=seo_block(lead, copy),
        accent=accent, accent_dark=darken(accent), font_family=tw["font"],
        body_bg=body_bg, body_text=body_text, nav_bg=nav_bg,
        nav_border=nav_border, link_cls=link_cls, mobile_bg=mobile_bg,
        hero_classes=hero_classes, badge=INDUSTRY_THEMES.get(
            lead["industry"], INDUSTRY_THEMES["other"])["hero_label"],
        badge_cls=badge_cls, h1_cls="", p_cls="", stat_lbl="opacity-60",
        services_kicker="Naše nabídka", services_title="Co pro vás uděláme",
        card_text="Rádi vám poradí a vše zajistíme — od posouzení po dokončení.",
        grid_cols=3, card_cls=card_cls, about_bg=about_bg,
        services_bg=services_bg, contact_bg=contact_bg,
        contact_text=contact_text, cc_cls=cc_cls, footer_bg=footer_bg,
        footer_text=footer_text, map_wrap=map_wrap, btn2_cls=btn2_cls,
        hours="Po–Pá dle domluvy",
        gallery=design.get("gallery", []),
        maps_embed=maps_embed(lead["city"], lead["company_name"]),
        stats=[("10+", "let zkušeností"), ("100 %", "spokojenost"),
               ("24 h", "reakce")],
        **copy,
    )
