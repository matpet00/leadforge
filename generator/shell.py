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
<div class="ambient" aria-hidden="true">
  <span>{{ ambient_emoji }}</span><span>{{ ambient_emoji }}</span>
  <span>{{ ambient_emoji }}</span><span>{{ ambient_emoji }}</span>
  <span>{{ ambient_emoji }}</span>
</div>
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
  {% if stats %}
  <div class="stats reveal">
    {% for st in stats %}<div class="stat"><b>{{ st[0] }}</b><span>{{ st[1] }}</span></div>{% endfor %}
  </div>
  {% endif %}
  {% if hours %}<p class="hours reveal"><strong>Otevírací doba:</strong> {{ hours }}</p>{% endif %}
  {% if gallery %}
  <div class="gallery">
    {% for g in gallery %}<div class="gitem reveal" style="background-image:url('{{ g }}')" role="img" aria-label="Ukázka práce {{ loop.index }}"></div>{% endfor %}
  </div>
  {% endif %}
</div></section>

{% if testimonials %}
<section id="prednosti" class="testimonials"><div class="wrap">
  <div class="kicker reveal">{{ testi_kicker }}</div>
  <h2 class="reveal">{{ testi_title }}</h2>
  <div class="testi-grid">
    {% for t in testimonials %}
    <blockquote class="tcard reveal">
      <div class="ticon" aria-hidden="true">{{ t.icon }}</div>
      <p>{{ t.text }}</p>
    </blockquote>
    {% endfor %}
  </div>
  <p class="testi-note reveal">{{ testi_note }}</p>
</div></section>
{% endif %}

<section id="kontakt" class="contact"><div class="wrap">
  <div class="kicker reveal">Kontakt</div>
  <h2 class="reveal">Ozvěte se nám</h2>
  <div class="contact-grid">
    {% if phone_display != '+420****0000' %}
    <a class="ccard reveal" href="tel:{{ phone }}">
      <span class="ci"><svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.9 21 3 13.1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.2.2 2.4.6 3.6.1.3 0 .7-.2 1l-2.3 2.2z"/></svg></span><b>Telefon</b><span>{{ phone_display }}</span>
    </a>
    {% endif %}
    {% if email %}
    <a class="ccard reveal" href="mailto:{{ email }}">
      <span class="ci"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M22 7l-10 6L2 7"/></svg></span><b>E-mail</b><span>{{ email }}</span>
    </a>
    {% endif %}
    <div class="ccard reveal">
      <span class="ci"><svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C8.1 2 5 5.1 5 9c0 5.2 7 13 7 13s7-7.8 7-13c0-3.9-3.1-7-7-7zm0 9.5A2.5 2.5 0 1112 6a2.5 2.5 0 010 5.5z"/></svg></span><b>Sídlo</b><span>{{ address or city or 'Česká republika' }}</span>
    </div>
  </div>
  {% if cta_note %}<p class="cta-note reveal">{{ cta_note }}</p>{% endif %}
</div></section>

<section id="kde" class="mapsec"><div class="wrap">
  <div class="kicker reveal">Kde nás najdete</div>
  <h2 class="reveal">{{ map_title }}</h2>
  <div class="mapframe reveal">
    <iframe title="Mapa — {{ company }}" src="{{ maps_embed }}" loading="lazy" allowfullscreen referrerpolicy="no-referrer-when-downgrade"
            onerror="this.style.display='none';document.getElementById('mapfallback').style.display='flex'"></iframe>
    <div class="mapfb">
      <div class="mapfb-pin">📍</div>
      <b>{{ address or city }}</b>
      <a class="btn" href="{{ maps_link }}" target="_blank" rel="noopener">Otevřít v mapách</a>
    </div>
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
height:340px;position:relative;background:var(--soft,#f0f4ec)}
.mapframe iframe{width:100%;height:100%;border:0;position:absolute;inset:0;z-index:1}
.mapfb{position:absolute;inset:0;display:flex;flex-direction:column;gap:12px;
align-items:center;justify-content:center;color:var(--muted)}
.mapfb-pin{font-size:2.2rem}
.addr{margin-top:14px;color:var(--muted);font-weight:600}
footer{border-top:1px solid var(--navline);padding:36px 0;margin-top:30px}
.frow{display:flex;flex-wrap:wrap;gap:12px;justify-content:space-between;color:var(--muted);font-size:.88rem}
.reveal{opacity:0;transform:translateY(18px);transition:opacity .6s ease,transform .6s ease}
.reveal.in{opacity:1;transform:none}
@media(prefers-reduced-motion:reduce){.reveal{opacity:1;transform:none;transition:none}}
.hours{margin-top:18px;color:var(--muted)}
.hours strong{color:var(--text)}
/* gallery */
.gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin-top:36px}
.gitem{height:190px;border-radius:var(--radius,14px);background-size:cover;background-position:center;
transition:transform .3s,filter .3s;filter:saturate(.92)}
.gitem:hover{transform:scale(1.025) rotate(-.4deg);filter:saturate(1.1)}
@media(max-width:640px){.gitem{height:140px}}
/* stats */
.stats{display:flex;flex-wrap:wrap;gap:44px;margin-top:34px}
.stat b{font-size:2.2rem;font-weight:800;color:var(--accent);letter-spacing:-.02em;display:block;line-height:1.1}
.stat span{color:var(--muted);font-size:.88rem}
/* testimonials */
.testimonials{background:var(--bg1,var(--soft,#f5f7fa))}
.testi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px}
.tcard{background:var(--cardbg,#fff);border-radius:var(--radius,14px);padding:28px 24px;
border-top:3px solid var(--accent);box-shadow:0 4px 16px rgba(16,24,40,.06)}
.ticon{font-size:1.8rem;margin-bottom:12px}
.tcard p{color:var(--text)}
.testi-note{margin-top:24px;color:var(--muted);font-size:.9rem;text-align:center}
/* industry ambient decorations (floating leaves / gears / bubbles...) */
.ambient{position:absolute;inset:0;pointer-events:none;overflow:hidden;z-index:0}
.ambient span{position:absolute;display:block;opacity:.5;animation:floaty 14s ease-in-out infinite}
.ambient span:nth-child(1){left:8%;top:18%;animation-delay:0s;font-size:28px}
.ambient span:nth-child(2){left:78%;top:12%;animation-delay:-4s;font-size:22px;animation-duration:17s}
.ambient span:nth-child(3){left:62%;top:64%;animation-delay:-8s;font-size:26px;animation-duration:20s}
.ambient span:nth-child(4){left:22%;top:70%;animation-delay:-2s;font-size:20px;animation-duration:15s}
.ambient span:nth-child(5){left:88%;top:48%;animation-delay:-6s;font-size:24px;animation-duration:18s}
@keyframes floaty{
  0%,100%{transform:translateY(0) rotate(0deg)}
  25%{transform:translateY(-16px) rotate(8deg)}
  50%{transform:translateY(-4px) rotate(-5deg)}
  75%{transform:translateY(-14px) rotate(4deg)}
}
@media(prefers-reduced-motion:reduce){.ambient span{animation:none}}
"""


def maps_embed(city: str, company: str = "") -> str:
    """Google Maps embed without API key (maps.google.com output=embed)."""
    q = f"{company} {city}".strip() if company else city
    from urllib.parse import quote
    return f"https://maps.google.com/maps?q={quote(q)}&t=&z=13&ie=UTF8&iwloc=&output=embed"
