"""Page shell v3 — one flexible shell + 15 template CSS personalities.

Every site includes:
  - sticky nav with WORKING hamburger (checkbox hack, no JS dependency)
  - hero (industry photo)
  - services grid
  - about
  - CONTACT section: phone card, email card, opening hours card
  - "Kde nás najdete" with Google Maps embed (city-based, no API key needed)
  - footer with ICO

The template personality is injected as CSS variables + template-specific
CSS block, so each of the 15 designs looks genuinely different.
"""

SHELL = """<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ company }}{% if city %} — {{ city }}{% endif %}</title>
{{ seo_block }}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family={{ google_font }}&display=swap" rel="stylesheet">
<style>
{{ base_css }}
{{ tpl_css }}
</style>
</head>
<body>
<input type="checkbox" id="navtoggle" class="navtoggle" aria-hidden="true">
<nav class="nav">
  <div class="wrap navrow">
    <a class="logo" href="#top">{{ logo_text }}<span>{{ logo_dot }}</span></a>
    <ul class="navlinks">
      <li><a href="#sluzby">Služby</a></li>
      <li><a href="#o-nas">O nás</a></li>
      <li><a href="#kontakt">Kontakt</a></li>
      <li><a href="#kde">Kde nás najdete</a></li>
    </ul>
    <label for="navtoggle" class="burger" aria-label="Otevřít menu">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M3 6h18M3 12h18M3 18h18"/></svg>
    </label>
  </div>
  <ul class="mobilenav">
    <li><a href="#sluzby">Služby</a></li>
    <li><a href="#o-nas">O nás</a></li>
    <li><a href="#kontakt">Kontakt</a></li>
    <li><a href="#kde">Kde nás najdete</a></li>
  </ul>
</nav>

<header id="top" class="hero">
{{ hero_html }}
</header>

<main>
<section id="sluzby" class="services"><div class="wrap">
  <div class="kicker reveal">{{ services_kicker }}</div>
  <h2 class="reveal">{{ services_title }}</h2>
  <div class="grid">
  {% for s in services %}
    <article class="card reveal">
      <div class="cicon" aria-hidden="true">{{ cicon }}</div>
      <h3>{{ s }}</h3>
      <p>{{ card_text }}</p>
    </article>
  {% endfor %}
  </div>
</div></section>

<section id="o-nas" class="about"><div class="wrap">
  <div class="kicker reveal">{{ about_kicker }}</div>
  <h2 class="reveal">{{ company }}</h2>
  <p class="reveal lead-p">{{ about }}</p>
  {% if hours %}<p class="hours reveal"><strong>Otevírací doba:</strong> {{ hours }}</p>{% endif %}
</div></section>

<section id="kontakt" class="contact"><div class="wrap">
  <div class="kicker reveal">Kontakt</div>
  <h2 class="reveal">Ozvěte se nám</h2>
  <div class="contact-grid">
    {% if phone_display != '+420****0000' %}
    <a class="ccard reveal" href="tel:{{ phone }}">
      <span class="ci">📞</span><b>Telefon</b><span>{{ phone_display }}</span>
    </a>
    {% endif %}
    {% if email %}
    <a class="ccard reveal" href="mailto:{{ email }}">
      <span class="ci">✉️</span><b>E-mail</b><span>{{ email }}</span>
    </a>
    {% endif %}
    <div class="ccard reveal">
      <span class="ci">📍</span><b>Sídlo</b><span>{{ address or city or 'Česká republika' }}</span>
    </div>
  </div>
  {% if cta_note %}<p class="cta-note reveal">{{ cta_note }}</p>{% endif %}
</div></section>

<section id="kde" class="mapsec"><div class="wrap">
  <div class="kicker reveal">Kde nás najdete</div>
  <h2 class="reveal">{{ map_title }}</h2>
  <div class="mapframe reveal">
    <iframe title="Mapa — {{ company }}" src="{{ maps_embed }}" loading="lazy" allowfullscreen referrerpolicy="no-referrer-when-downgrade"></iframe>
  </div>
  <p class="addr reveal">{{ address or city }}{% if city and address and city not in address %}, {{ city }}{% endif %}</p>
</div></section>
</main>

<footer><div class="wrap frow">
  <span>&copy; {{ year }} {{ company }}{% if ico %} · IČO {{ ico }}{% endif %}</span>
  <span>{{ city }}</span>
</div></footer>

<script>
addEventListener('scroll',()=>document.querySelector('.nav').classList.toggle('scrolled',scrollY>8),{passive:true});
// close mobile menu on link click
document.querySelectorAll('.mobilenav a').forEach(a=>a.addEventListener('click',()=>{
  document.getElementById('navtoggle').checked=false;
}));
if('IntersectionObserver' in window){
  const io=new IntersectionObserver(es=>es.forEach((e,i)=>{
    if(e.isIntersecting){setTimeout(()=>e.target.classList.add('in'),i*70);io.unobserve(e.target)}
  }),{threshold:.12});
  document.querySelectorAll('.reveal').forEach(el=>io.observe(el));
}else{document.querySelectorAll('.reveal').forEach(el=>el.classList.add('in'))}
</script>
</body></html>"""

BASE_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
body{line-height:1.65;font-size:16px;color:var(--text);background:var(--bg0);font-family:var(--font)}
img,svg{display:block}
.wrap{max-width:1140px;margin:0 auto;padding:0 22px;position:relative;z-index:1}
.navtoggle{position:absolute;opacity:0;pointer-events:none}
.nav{position:sticky;top:0;z-index:50;background:var(--navbg);backdrop-filter:blur(10px);
border-bottom:1px solid var(--navline);transition:box-shadow .25s}
.nav.scrolled{box-shadow:0 4px 18px rgba(0,0,0,.12)}
.navrow{display:flex;justify-content:space-between;align-items:center;height:64px}
.logo{font-weight:800;font-size:1.15rem;text-decoration:none;color:var(--logo);letter-spacing:-.02em}
.logo span{color:var(--accent)}
.navlinks{display:flex;gap:26px;list-style:none}
.navlinks a{text-decoration:none;color:var(--muted);font-size:.92rem;font-weight:600;position:relative;padding:4px 0}
.navlinks a::after{content:'';position:absolute;left:0;bottom:-3px;width:0;height:2px;background:var(--accent);transition:width .25s}
.navlinks a:hover{color:var(--accent)}.navlinks a:hover::after{width:100%}
.burger{display:none;cursor:pointer;color:var(--logo);padding:6px;border-radius:8px}
.mobilenav{display:none;list-style:flex-direction:column;list-style:none;
background:var(--bg1);border-bottom:1px solid var(--navline);padding:10px 22px 16px;margin:0}
.mobilenav a{display:block;padding:11px 4px;text-decoration:none;color:var(--muted);font-weight:600;border-bottom:1px solid var(--navline)}
.mobilenav li:last-child a{border-bottom:none}
#navtoggle:checked ~ .nav .mobilenav{display:block}
#navtoggle:checked ~ .nav .burger svg{transform:rotate(90deg)}
.burger svg{transition:transform .25s}
@media(max-width:760px){.navlinks{display:none}.burger{display:block}}
.hero{position:relative;overflow:hidden}
.kicker{font-size:.78rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;
color:var(--accent);margin-bottom:10px}
h2{font-size:clamp(1.55rem,3vw,2.15rem);letter-spacing:-.015em;margin-bottom:34px;line-height:1.15}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px}
.card{background:var(--cardbg);border-radius:var(--radius,14px);padding:26px;transition:transform .25s,var(--tprop) .25s}
.card:hover{transform:translateY(-4px)}
.cicon{width:46px;height:46px;border-radius:12px;background:var(--iconbg);display:flex;
align-items:center;justify-content:center;color:var(--accent);margin-bottom:15px}
.card h3{font-size:1.07rem;margin-bottom:8px}
.card p{color:var(--muted);font-size:.94rem}
.contact-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:18px;margin-bottom:26px}
.ccard{background:var(--cardbg);border-radius:var(--radius,14px);padding:24px;display:flex;
flex-direction:column;gap:5px;text-decoration:none;color:inherit;border:1px solid var(--cardline);
transition:transform .25s,border-color .25s}
.ccard:hover{transform:translateY(-3px);border-color:var(--accent)}
.cc .ci,.ccard .ci{font-size:1.5rem;margin-bottom:6px}
.ccard b{font-size:.82rem;text-transform:uppercase;letter-spacing:.08em;color:var(--accent)}
.ccard span:last-child{color:var(--muted);font-weight:600}
.cta-note{margin-top:8px;color:var(--muted)}
.mapframe{border-radius:var(--radius,14px);overflow:hidden;border:1px solid var(--cardline);
height:340px;box-shadow:var(--mapshadow,0 8px 28px rgba(16,24,40,.08))}
.mapframe iframe{width:100%;height:100%;border:0}
.addr{margin-top:14px;color:var(--muted);font-weight:600}
footer{border-top:1px solid var(--navline);padding:36px 0;margin-top:30px}
.frow{display:flex;flex-wrap:wrap;gap:12px;justify-content:space-between;color:var(--muted);font-size:.88rem}
.reveal{opacity:0;transform:translateY(18px);transition:opacity .6s ease,transform .6s ease}
.reveal.in{opacity:1;transform:none}
@media(prefers-reduced-motion:reduce){.reveal{opacity:1;transform:none;transition:none}}
.hours{margin-top:18px;color:var(--muted)}
.hours strong{color:var(--text)}
"""


def maps_embed(city: str, company: str = "") -> str:
    """Google Maps embed without API key (maps.google.com output=embed)."""
    q = f"{company} {city}".strip() if company else city
    from urllib.parse import quote
    return f"https://maps.google.com/maps?q={quote(q)}&t=&z=13&ie=UTF8&iwloc=&output=embed"
