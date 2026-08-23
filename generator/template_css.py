"""Template CSS personalities — 15 distinct visual languages.

Each function returns a CSS string that styles the shared shell structure
differently: hero treatment, card style, typography scale, section rhythms,
decorative elements. All use the palette vars from design_system.
"""

def _hero_photo_css(palette, overlay=0.55, height="88vh", align="left"):
    center = "text-align:center" if align == "center" else ""
    margin_auto = "margin-inline:auto" if align == "center" else ""
    maxw = "780px" if align == "center" else "1140px"
    return (f".hero{{min-height:{height};display:flex;align-items:center;{center}"
            f"background:linear-gradient(rgba(10,12,20,{overlay}),rgba(10,12,20,{min(overlay+0.25,0.9)})),"
            f"url('{{{{ photo }}}}') center/cover}}"
            f".hero .wrap{{padding:110px 22px;max-width:{maxw}}}"
            f".hero h1{{color:#fff;font-size:clamp(2.1rem,5vw,3.6rem);line-height:1.08;margin-bottom:16px}}"
            f".hero p{{color:rgba(255,255,255,.88);font-size:1.15rem;max-width:50ch;margin-bottom:30px;{margin_auto}}}"
            f".hero .kicker{{color:var(--accent)}}")


# ---------------------------------------------------------------- 15 templates

def aurora(p):  # dark premium glass
    return f"""
:root{{--bg0:{p['bg0']};--bg1:{p['bg1']};--accent:{p['accent']};--text:{p['text']};--muted:{p['muted']}}}
body{{background:radial-gradient(1000px 500px at 80% -10%,color-mix(in srgb,var(--accent) 14%,transparent),transparent),var(--bg0)}}
.nav{{--navbg:color-mix(in srgb,var(--bg0) 75%,transparent);--navline:rgba(148,163,184,.15);--logo:#fff}}
.hero{{{_hero_photo_css(p, overlay=.62)}}}
.hero .badge,.kicker{{}}
.badge{{display:inline-block;color:var(--accent);border:1px solid color-mix(in srgb,var(--accent) 45%,transparent);
background:color-mix(in srgb,var(--accent) 12%,transparent);padding:6px 16px;border-radius:99px;
font-size:.76rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;margin-bottom:20px}}
.btn{{display:inline-flex;background:linear-gradient(135deg,var(--accent),color-mix(in srgb,var(--accent) 60%,#fff));
color:#0b1024;padding:15px 34px;border-radius:14px;text-decoration:none;font-weight:800;
box-shadow:0 0 28px color-mix(in srgb,var(--accent) 45%,transparent);transition:transform .2s,box-shadow .2s}}
.btn:hover{{transform:translateY(-2px);box-shadow:0 0 42px color-mix(in srgb,var(--accent) 65%,transparent)}}
.services{{padding:90px 0}}
.card{{background:color-mix(in srgb,var(--bg1) 80%,transparent);border:1px solid rgba(148,163,184,.18);
backdrop-filter:blur(8px);border-radius:18px}}
.card:hover{{border-color:color-mix(in srgb,var(--accent) 45%,transparent);box-shadow:0 0 32px color-mix(in srgb,var(--accent) 18%,transparent)}}
.iconbg{{}}
.card .cicon{{background:color-mix(in srgb,var(--accent) 15%,transparent);box-shadow:inset 0 0 18px color-mix(in srgb,var(--accent) 22%,transparent)}}
.about{{background:var(--bg1)}}
.contact{{padding:84px 0}}
.ccard{{background:color-mix(in srgb,var(--bg1) 80%,transparent);border-color:rgba(148,163,184,.18)}}
.mapframe{{box-shadow:0 0 40px color-mix(in srgb,var(--accent) 12%,transparent);border-color:rgba(148,163,184,.2)}}
h2{{color:var(--text)}}"""


def terra(p):  # warm craft serif
    return f"""
:root{{--bg0:{p['bg0']};--bg1:{p['bg1']};--accent:{p['accent']};--text:{p['text']};--muted:{p['muted']}}}
.nav{{--navbg:{p['bg0']}f2;--navline:{p['bg1']};--logo:var(--text)}}
.logo{{font-family:var(--font);font-style:italic}}
.hero{{display:grid;grid-template-columns:1.05fr .95fr;min-height:86vh;
background:linear-gradient(120deg,var(--bg0) 48%,{p['bg1']} 48%)}}
.hero-photo{{height:100%;min-height:400px;background:url('{{{{ photo }}}}') center/cover;
clip-path:polygon(6% 0,100% 0,100% 100%,0 100%,6% 0)}}
.hero .wrap{{padding:100px 40px;display:flex;flex-direction:column;justify-content:center;align-items:flex-start}}
@media(max-width:840px){{.hero{{grid-template-columns:1fr}}.hero-photo{{order:-1;min-height:250px;clip-path:none}}}}
.hero h1{{font-size:clamp(2.3rem,5vw,3.8rem);line-height:1.05;font-weight:700;margin-bottom:20px}}
.hero p{{font-size:1.13rem;color:var(--muted);margin-bottom:30px;max-width:44ch}}
.kicker::before{{content:'— ';color:var(--accent)}}
.btn{{display:inline-flex;background:var(--accent);color:#fff;padding:15px 36px;border-radius:4px;
text-decoration:none;font-weight:700;border:2px solid var(--accent);transition:background .2s,color .2s}}
.btn:hover{{background:transparent;color:var(--accent)}}
.services{{padding:92px 0;background:var(--bg0)}}
.card{{border:none;border-left:4px solid var(--accent);border-radius:0 12px 12px 0;background:#fff}}
.about{{background:var(--bg1)}}
.about .lead-p{{font-size:1.12rem;max-width:64ch}}
.contact{{padding:88px 0}}
.ccard{{border-radius:8px;background:#fff}}
.mapframe{{border-radius:8px}}
footer{{background:var(--bg1)}}"""


def pulse(p):  # bold energy
    return f"""
:root{{--bg0:#ffffff;--block:{p['block']};--accent:{p['accent']};--ink:{p['ink']};--text:{p['ink']};--muted:#52525b}}
.nav{{--navbg:#ffffffee;--navline:#e4e4e7;--logo:var(--ink)}}
.hero{{background:var(--ink);color:#fff;padding:130px 0 150px;
clip-path:polygon(0 0,100% 0,100% 88%,0 100%)}}
.hero h1{{font-size:clamp(2.6rem,7vw,5rem);text-transform:uppercase;line-height:.95;
letter-spacing:-.02em;font-weight:900;margin-bottom:22px}}
.hero h1 em{{font-style:normal;color:var(--accent)}}
.hero p{{color:#d4d4d8;font-size:1.18rem;margin-bottom:34px;max-width:46ch}}
.hero .wrap{{position:relative}}
.hero::after{{content:'';position:absolute;right:-60px;top:-60px;width:340px;height:340px;
background:var(--accent);border-radius:50%;opacity:.16;filter:blur(10px)}}
.badge{{display:inline-block;background:var(--accent);color:#fff;padding:7px 17px;border-radius:6px;
font-size:.78rem;font-weight:900;letter-spacing:.12em;text-transform:uppercase;margin-bottom:24px;transform:rotate(-1.5deg)}}
.btn{{display:inline-flex;background:var(--accent);color:#fff;padding:17px 40px;border-radius:10px;
text-decoration:none;font-weight:900;text-transform:uppercase;letter-spacing:.03em;font-size:1.02rem;
transition:transform .18s}}
.btn:hover{{transform:scale(1.04) rotate(-.5deg)}}
.services{{padding:96px 0;background:var(--block);clip-path:polygon(0 4%,100% 0,100% 96%,0 100%)}}
.services .kicker{{color:var(--accent)}}
.card{{background:#fff;border:none;border-radius:18px;box-shadow:8px 8px 0 var(--accent)}}
.card:hover{{transform:translate(-3px,-3px);box-shadow:12px 12px 0 var(--accent)}}
.about{{padding:96px 0;background:#fff}}
.contact{{background:var(--ink);color:#fff;clip-path:polygon(0 0,100% 5%,100% 100%,0 100%);padding:100px 0 90px}}
.contact :is(h2,.kicker){{color:#fff}}
.ccard{{background:rgba(255,255,255,.07);border-color:rgba(255,255,255,.14);color:#fff;border-radius:14px}}
.mapsec{{padding:90px 0}}
.mapframe{{border-radius:18px;border:4px solid var(--ink)}}"""


def zen(p):  # airy minimal
    return f"""
:root{{--bg0:{p['wash']};--bg1:#ffffff;--accent:{p['accent']};--text:{p['text']};--muted:{p['muted']};
--line:{p['line']}}}
body{{font-weight:400}}
.nav{{--navbg:{p['wash']}f5;--navline:{p['line']};--logo:var(--text)}}
.navlinks a{{font-weight:400;letter-spacing:.02em}}
.hero{{padding:140px 0 120px;background:
linear-gradient(to bottom,transparent 70%,#fff),url('{{{{ photo }}}}') center/cover;
position:relative}}
.hero::before{{content:'';position:absolute;inset:0;background:rgba(255,255,255,.82)}}
.hero h1{{font-size:clamp(2rem,4vw,3.1rem);font-weight:600;line-height:1.2;margin-bottom:20px;color:var(--text)}}
.hero p{{font-size:1.08rem;color:var(--muted);margin-bottom:36px;max-width:46ch}}
.wrap{{}}
.hero .wrap{{text-align:center;max-width:720px}}
.hero p{{margin-inline:auto}}
.btn{{display:inline-flex;background:transparent;color:var(--accent);padding:14px 38px;border-radius:2px;
border:1px solid var(--accent);text-decoration:none;font-weight:600;letter-spacing:.06em;transition:all .3s}}
.btn:hover{{background:var(--accent);color:#fff}}
.kicker{{letter-spacing:.28em;font-weight:400;font-size:.72rem}}
.card{{border:none;border-bottom:1px solid {p['line']};border-radius:0;background:transparent;padding:26px 6px}}
.card:hover{{transform:none;border-bottom-color:var(--accent)}}
.card .cicon{{background:transparent;color:var(--accent);border:1px solid {p['line']};width:52px;height:52px;border-radius:50%;margin-inline:auto}}
.card{{text-align:center}}
.services{{padding:100px 0;background:#fff}}
.about{{background:{p['wash']};padding:100px 0}}
.contact{{padding:96px 0;background:#fff}}
.ccard{{border:none;border-bottom:1px solid {p['line']};border-radius:0;text-align:left;background:transparent}}
.ccard:hover{{border-bottom-color:var(--accent);transform:none}}
.mapframe{{border-radius:0;height:300px;border:none;outline:1px solid {p['line']}}}"""


def monolith(p):  # brutalist modern
    return f"""
:root{{--bg0:{p['bg0']};--bg1:{p['bg1']};--accent:{p['accent']};--text:{p['text']};--muted:{p['muted']}}}
.nav{{--navbg:{p['bg0']}f0;--navline:#333;--logo:#fff}}
.logo{{text-transform:uppercase;letter-spacing:-.01em}}
.hero{{padding:150px 0 120px;background:
linear-gradient(180deg,transparent 85%,var(--bg1)),
repeating-linear-gradient(0deg,transparent,transparent 79px,#222 80px),
repeating-linear-gradient(90deg,transparent,transparent 79px,#222 80px),var(--bg0)}}
.hero h1{{font-size:clamp(2.8rem,8vw,6rem);text-transform:uppercase;line-height:.92;
letter-spacing:-.03em;margin-bottom:24px}}
.hero h1 span{{-webkit-text-stroke:2px var(--accent);color:transparent}}
.hero p{{color:var(--muted);font-size:1.15rem;margin-bottom:36px;max-width:50ch}}
.btn{{display:inline-flex;background:var(--accent);color:#111;padding:16px 42px;border-radius:0;
text-decoration:none;font-weight:800;text-transform:uppercase;letter-spacing:.05em;
transition:letter-spacing .25s}}
.btn:hover{{letter-spacing:.14em}}
.kicker{{text-transform:uppercase;letter-spacing:.2em;color:var(--accent)}}
.services{{padding:94px 0;background:var(--bg1)}}
.card{{background:var(--bg0);border:1px solid #333;border-radius:0}}
.card:hover{{border-color:var(--accent);transform:translateY(-4px)}}
.about{{background:var(--bg0);border-block:1px solid #333;padding:92px 0}}
.contact{{background:var(--bg1);padding:92px 0}}
.ccard{{border:1px solid #333;border-radius:0;background:var(--bg0)}}
.ccard:hover{{border-color:var(--accent)}}
.mapframe{{border-radius:0;border:1px solid #333}}"""


def horizon(p):  # corporate clean
    return f"""
:root{{--bg0:{p['bg0']};--bg1:{p['bg1']};--accent:{p['accent']};--text:{p['text']};--muted:{p['muted']}}}
.nav{{--navbg:#fffffff5;--navline:#e2e8f0;--logo:var(--text)}}
.hero{{padding:120px 0;background:
linear-gradient(135deg,{p['bg1']} 0%,#fff 100%)}}
.hero .wrap{{display:grid;grid-template-columns:1.1fr .9fr;gap:50px;align-items:center}}
.hero-photo{{height:380px;border-radius:20px;background:url('{{{{ photo }}}}') center/cover;
box-shadow:24px 24px 0 var(--bg1),0 20px 50px rgba(29,78,216,.18)}}
@media(max-width:840px){{.hero .wrap{{grid-template-columns:1fr}}.hero-photo{{height:240px;order:-1}}}}
.hero h1{{font-size:clamp(2rem,4.4vw,3.3rem);margin-bottom:18px}}
.hero p{{color:var(--muted);margin-bottom:30px;font-size:1.1rem}}
.btn{{display:inline-flex;background:var(--accent);color:#fff;padding:15px 36px;border-radius:10px;
text-decoration:none;font-weight:700;transition:filter .2s,transform .2s}}
.btn:hover{{filter:brightness(1.12);transform:translateY(-1px)}}
.services{{padding:90px 0;background:#fff}}
.card{{border-radius:14px;border:1px solid #e2e8f0}}
.card:hover{{border-color:var(--accent)}}
.about{{background:var(--bg1);padding:90px 0}}
.contact{{padding:90px 0;background:#fff}}
.ccard{{border-radius:14px;border:1px solid #e2e8f0;background:#fff}}
.mapframe{{border-radius:14px}}"""


def bloom(p):  # organic rounded
    return f"""
:root{{--bg0:{p['bg0']};--bg1:{p['bg1']};--accent:{p['accent']};--text:{p['text']};--muted:{p['muted']};
--radius:26px}}
.nav{{--navbg:{p['bg0']}f2;--navline:#f9d5e5;--logo:var(--text)}}
.hero{{padding:110px 0;background:
radial-gradient(700px 350px at 15% 0%,color-mix(in srgb,var(--accent) 14%,transparent),transparent),
radial-gradient(600px 300px at 95% 30%,color-mix(in srgb,var(--accent) 10%,transparent),transparent),var(--bg0)}}
.hero .wrap{{display:grid;grid-template-columns:1fr .85fr;gap:46px;align-items:center}}
@media(max-width:840px){{.hero .wrap{{grid-template-columns:1fr}}}}
.hero-photo{{height:360px;border-radius:46% 54% 58% 42%/48% 44% 56% 52%;
background:url('{{{{ photo }}}}') center/cover;box-shadow:0 24px 60px color-mix(in srgb,var(--accent) 28%,transparent)}}
.hero h1{{font-size:clamp(2.1rem,4.6vw,3.4rem);margin-bottom:18px}}
.hero p{{color:var(--muted);margin-bottom:30px}}
.btn{{display:inline-flex;background:var(--accent);color:#fff;padding:16px 38px;border-radius:99px;
text-decoration:none;font-weight:800;transition:transform .25s,border-radius .25s}}
.btn:hover{{transform:translateY(-2px);border-radius:12px}}
.card{{border-radius:26px;border:none;box-shadow:0 10px 34px color-mix(in srgb,var(--accent) 12%,transparent)}}
.card .cicon{{border-radius:50%}}
.about{{background:var(--bg1);border-radius:60px 60px 0 0;padding:90px 0 80px}}
.contact{{background:var(--bg1);padding:20px 0 90px}}
.ccard{{border-radius:22px;background:#fff;border:none;box-shadow:0 8px 26px color-mix(in srgb,var(--accent) 10%,transparent)}}
.mapframe{{border-radius:26px}}"""


def forge(p):  # industrial
    return f"""
:root{{--bg0:{p['bg0']};--bg1:{p['bg1']};--accent:{p['accent']};--text:{p['text']};--muted:{p['muted']}}}
.nav{{--navbg:{p['bg0']}f2;--navline:#3f3f46;--logo:#fff}}
.logo{{text-transform:uppercase;letter-spacing:.06em}}
.hero{{padding:140px 0;background:
linear-gradient(105deg,var(--bg0) 55%,transparent 55%),url('{{{{ photo }}}}') center/cover}}
.hero h1{{font-size:clamp(2.4rem,6vw,4.4rem);text-transform:uppercase;line-height:1;margin-bottom:20px}}
.hero h1 b{{color:var(--accent)}}
.hero p{{color:var(--muted);margin-bottom:34px;max-width:46ch}}
.btn{{display:inline-flex;background:var(--accent);color:#18181b;padding:16px 40px;border-radius:0;
text-decoration:none;font-weight:800;text-transform:uppercase;letter-spacing:.04em;
border:2px solid var(--accent);transition:all .2s}}
.btn:hover{{background:transparent;color:var(--accent)}}
.kicker{{letter-spacing:.18em}}
.services{{padding:92px 0;background:
repeating-linear-gradient(45deg,var(--bg1) 0 14px,color-mix(in srgb,#000 22%,var(--bg1)) 14px 15px)}}
.card{{border-radius:4px;border:2px solid #3f3f46;background:var(--bg0);position:relative}}
.card::before{{content:'';position:absolute;top:8px;right:8px;width:6px;height:6px;
border-radius:50%;background:var(--accent);box-shadow:0 12px 0 var(--accent),0 -12px 0 var(--accent)}}
.card:hover{{border-color:var(--accent);transform:translateY(-3px)}}
.card .cicon{{border-radius:4px}}
.about{{background:var(--bg0);border-top:3px solid var(--accent);padding:90px 0}}
.contact{{background:var(--bg1);padding:90px 0}}
.ccard{{border-radius:4px;border:1px solid #3f3f46;background:var(--bg0)}}
.ccard b{{color:var(--accent)}}
.mapframe{{border-radius:4px;border:1px solid #3f3f46}}"""


def meadow(p):  # natural fresh
    return f"""
:root{{--bg0:{p['bg0']};--bg1:{p['bg1']};--accent:{p['accent']};--text:{p['text']};--muted:{p['muted']}}}
.nav{{--navbg:{p['bg0']}f2;--navline:#dbe9c4;--logo:var(--text)}}
.hero{{padding:130px 0;background:
linear-gradient(180deg,transparent 60%,{p['bg0']} 100%),url('{{{{ photo }}}}') center/cover}}
.hero h1{{color:#fff;font-size:clamp(2.2rem,5vw,3.6rem);text-shadow:0 2px 24px rgba(0,0,0,.4);margin-bottom:18px}}
.hero p{{color:#fff;opacity:.94;font-size:1.15rem;margin-bottom:32px;text-shadow:0 1px 14px rgba(0,0,0,.35)}}
.btn{{display:inline-flex;background:#fff;color:var(--accent);padding:16px 38px;border-radius:99px;
text-decoration:none;font-weight:700;transition:transform .25s}}
.btn:hover{{transform:translateY(-3px)}}
.services{{padding:90px 0;background:var(--bg0)}}
.card{{border-radius:20px;background:#fff;border:1px solid #e7f0d3}}
.card .cicon{{border-radius:50%;background:var(--bg1)}}
.about{{background:var(--bg1);padding:88px 0}}
.contact{{padding:88px 0;background:var(--bg0)}}
.ccard{{border-radius:20px;background:#fff;border:1px solid #e7f0d3}}
.mapframe{{border-radius:20px}}"""


def noir(p):  # elegant dark luxury
    return f"""
:root{{--bg0:{p['bg0']};--bg1:{p['bg1']};--accent:{p['accent']};--text:{p['text']};--muted:{p['muted']}}}
.nav{{--navbg:{p['bg0']}f0;--navline:#262626;--logo:var(--accent)}}
.logo{{font-family:var(--font);font-weight:600;letter-spacing:.04em}}
.hero{{padding:160px 0 130px;text-align:center;background:
radial-gradient(800px 400px at 50% -10%,color-mix(in srgb,var(--accent) 12%,transparent),transparent),var(--bg0)}}
.hero h1{{font-family:var(--font);font-size:clamp(2.4rem,5.5vw,4.2rem);font-weight:600;
line-height:1.1;margin-bottom:20px}}
.hero p{{color:var(--muted);font-size:1.14rem;margin-bottom:38px;max-width:48ch;margin-inline:auto}}
.btn{{display:inline-flex;background:transparent;color:var(--accent);padding:15px 44px;border-radius:2px;
border:1px solid var(--accent);text-decoration:none;font-weight:600;letter-spacing:.14em;
text-transform:uppercase;font-size:.86rem;transition:all .35s}}
.btn:hover{{background:var(--accent);color:#0a0a0a}}
.kicker{{color:var(--accent);letter-spacing:.3em;font-size:.72rem}}
.services{{padding:96px 0;background:var(--bg1)}}
.card{{background:transparent;border:none;border-top:1px solid #262626;border-radius:0;padding-top:30px}}
.card .cicon{{background:transparent;border:1px solid var(--accent);color:var(--accent);border-radius:50%;
width:54px;height:54px;margin-inline:auto}}
.card{{text-align:center}}
.card:hover{{border-top-color:var(--accent)}}
.about{{background:var(--bg0);padding:94px 0;text-align:center}}
.about .lead-p{{margin-inline:auto;text-align:left}}
.contact{{padding:92px 0;background:var(--bg1)}}
.ccard{{background:transparent;border:1px solid #262626;border-radius:2px;text-align:center}}
.ccard:hover{{border-color:var(--accent)}}
.mapframe{{border-radius:2px;border:1px solid #262626;height:320px}}"""


def candy(p):  # playful bright
    return f"""
:root{{--bg0:{p['bg0']};--bg1:{p['bg1']};--accent:{p['accent']};--text:{p['text']};--muted:{p['muted']};
--radius:24px}}
.nav{{--navbg:{p['bg0']}f5;--navline:#f5d0fe;--logo:var(--text)}}
.hero{{padding:120px 0;background:
radial-gradient(500px 260px at 10% 10%,#fbcfe8 0%,transparent 60%),
radial-gradient(500px 280px at 90% 20%,#ddd6fe 0%,transparent 55%),var(--bg0)}}
.hero .wrap{{text-align:center;max-width:740px}}
.hero h1{{font-size:clamp(2.2rem,5vw,3.7rem);margin-bottom:18px}}
.hero h1 ::selection{{background:var(--accent)}}
.hero p{{color:var(--muted);font-size:1.14rem;margin-bottom:32px}}
.btn{{display:inline-flex;background:var(--accent);color:#fff;padding:17px 42px;border-radius:99px;
text-decoration:none;font-weight:800;font-size:1.05rem;box-shadow:0 6px 0 color-mix(in srgb,var(--accent) 55%,#000);
transition:transform .15s,box-shadow .15s}}
.btn:hover{{transform:translateY(3px);box-shadow:0 2px 0 color-mix(in srgb,var(--accent) 55%,#000)}}
.services{{padding:92px 0}}
.card{{border-radius:28px;border:2px solid #f5d0fe;background:#fff}}
.card:hover{{transform:rotate(-1deg) translateY(-4px)}}
.card .cicon{{border-radius:16px}}
.about{{background:var(--bg1);padding:88px 0}}
.contact{{padding:88px 0}}
.ccard{{border-radius:24px;border:2px solid #f5d0fe;background:#fff}}
.mapframe{{border-radius:28px;border:3px solid #f5d0fe}}"""


def summit(p):  # mountain strong
    return f"""
:root{{--bg0:{p['bg0']};--bg1:{p['bg1']};--accent:{p['accent']};--text:{p['text']};--muted:{p['muted']}}}
.nav{{--navbg:{p['bg0']}f2;--navline:#234;--logo:#fff}}
.hero{{padding:150px 0 170px;background:
linear-gradient(180deg,rgba(12,26,42,.55) 0%,{p['bg0']} 96%),url('{{{{ photo }}}}') center/cover;
clip-path:polygon(0 0,100% 0,100% calc(100% - 60px),50% 100%,0 calc(100% - 60px))}}
.hero h1{{font-family:var(--font);font-size:clamp(2.6rem,6.5vw,4.8rem);text-transform:uppercase;
line-height:.95;letter-spacing:.01em;margin-bottom:22px}}
.hero p{{color:var(--muted);font-size:1.16rem;margin-bottom:34px;max-width:48ch}}
.btn{{display:inline-flex;background:var(--accent);color:#fff;padding:17px 42px;border-radius:6px;
text-decoration:none;font-weight:800;text-transform:uppercase;letter-spacing:.06em;transition:filter .2s}}
.btn:hover{{filter:brightness(1.15)}}
.services{{padding:110px 0 90px;background:var(--bg0)}}
.card{{background:var(--bg1);border:1px solid #234;border-radius:8px}}
.card:hover{{border-color:var(--accent)}}
.card .cicon{{border-radius:8px}}
.about{{background:var(--bg1);padding:90px 0}}
.contact{{padding:90px 0;background:var(--bg0)}}
.ccard{{background:var(--bg1);border:1px solid #234;border-radius:8px}}
.ccard b{{color:var(--accent)}}
.mapframe{{border-radius:8px;border:1px solid #234}}"""


def lagoon(p):  # aqua fresh
    return f"""
:root{{--bg0:{p['bg0']};--bg1:{p['bg1']};--accent:{p['accent']};--text:{p['text']};--muted:{p['muted']}}}
.nav{{--navbg:{p['bg0']}f2;--navline:#baecf5;--logo:var(--text)}}
.hero{{padding:130px 0 140px;background:
radial-gradient(900px 420px at 85% 10%,color-mix(in srgb,var(--accent) 16%,transparent),transparent),
linear-gradient(175deg,transparent 82%,var(--bg1) 82%),url('{{{{ photo }}}}') center/cover}}
.hero h1{{font-size:clamp(2.2rem,4.8vw,3.6rem);color:#fff;text-shadow:0 2px 20px rgba(8,51,68,.5);
margin-bottom:18px}}
.hero p{{color:#fff;opacity:.95;font-size:1.13rem;margin-bottom:32px;max-width:46ch;
text-shadow:0 1px 12px rgba(8,51,68,.45)}}
.btn{{display:inline-flex;background:var(--accent);color:#fff;padding:16px 40px;border-radius:14px;
text-decoration:none;font-weight:700;transition:border-radius .3s,transform .2s}}
.btn:hover{{border-radius:99px;transform:translateY(-2px)}}
.services{{padding:92px 0;background:#fff}}
.card{{border-radius:20px;border:1px solid #cffafe}}
.card:hover{{border-color:var(--accent)}}
.about{{background:var(--bg1);padding:88px 0}}
.contact{{padding:88px 0;background:#fff}}
.ccard{{border-radius:18px;border:1px solid #cffafe}}
.mapframe{{border-radius:20px}}"""


def ember(p):  # warm fire
    return f"""
:root{{--bg0:{p['bg0']};--bg1:{p['bg1']};--accent:{p['accent']};--text:{p['text']};--muted:{p['muted']}}}
.nav{{--navbg:{p['bg0']}f2;--navline:#3f2723;--logo:#fff}}
.hero{{padding:140px 0;background:
linear-gradient(100deg,var(--bg0) 42%,rgba(26,14,12,.72) 100%),url('{{{{ photo }}}}') center/cover}}
.hero h1{{font-size:clamp(2.3rem,5.4vw,4rem);line-height:1.06;margin-bottom:20px}}
.hero h1 strong{{color:var(--accent)}}
.hero p{{color:var(--muted);margin-bottom:34px;max-width:46ch}}
.btn{{display:inline-flex;background:var(--accent);color:#fff;padding:16px 40px;border-radius:8px;
text-decoration:none;font-weight:800;transition:all .25s}}
.btn:hover{{background:#dc2626;transform:translateY(-2px);box-shadow:0 10px 30px rgba(239,68,68,.35)}}
.services{{padding:92px 0;background:
radial-gradient(700px 300px at 50% 0%,color-mix(in srgb,var(--accent) 9%,transparent),transparent),var(--bg1)}}
.card{{background:linear-gradient(160deg,var(--bg0),color-mix(in srgb,var(--accent) 7%,var(--bg0)));
border:1px solid #4a2c26;border-radius:18px}}
.card:hover{{box-shadow:0 10px 40px color-mix(in srgb,var(--accent) 25%,transparent)}}
.card:hover{{border-color:var(--accent)}}
.about{{background:var(--bg0);padding:90px 0;border-left:4px solid var(--accent)}}
.contact{{background:var(--bg1);padding:90px 0}}
.ccard{{background:var(--bg0);border:1px solid #3f2723;border-radius:12px}}
.ccard b{{color:var(--accent)}}
.mapframe{{border-radius:12px;border:1px solid #3f2723}}"""


def orchard(p):  # village local
    return f"""
:root{{--bg0:{p['bg0']};--bg1:{p['bg1']};--accent:{p['accent']};--text:{p['text']};--muted:{p['muted']}}}
.nav{{--navbg:{p['bg0']}f5;--navline:#e5dfc3;--logo:var(--text)}}
.hero{{display:grid;grid-template-columns:1fr 1fr;min-height:82vh;background:var(--bg0)}}
.hero .wrap{{padding:90px 40px;display:flex;flex-direction:column;justify-content:center;align-items:flex-start}}
.hero-photo{{height:100%;min-height:380px;background:url('{{{{ photo }}}}') center/cover;
border-radius:0 0 0 80px}}
@media(max-width:840px){{.hero{{grid-template-columns:1fr}}.hero-photo{{order:-1;min-height:230px;border-radius:0}}}}
.hero h1{{font-size:clamp(2.1rem,4.6vw,3.4rem);margin-bottom:18px}}
.hero p{{color:var(--muted);margin-bottom:30px;font-size:1.1rem}}
.btn{{display:inline-flex;background:var(--accent);color:#fff;padding:15px 36px;border-radius:10px;
text-decoration:none;font-weight:700;transition:transform .2s}}
.btn:hover{{transform:translateY(-2px)}}
.services{{padding:88px 0;background:#fff}}
.card{{border-radius:16px;border:1px solid #eee9d5;background:var(--bg0)}}
.card .cicon{{border-radius:50%}}
.about{{background:var(--bg1);padding:88px 0}}
.contact{{padding:88px 0;background:#fff}}
.ccard{{border-radius:16px;border:1px solid #eee9d5;background:var(--bg0)}}
.mapframe{{border-radius:16px}}"""


TEMPLATE_CSS = {
    "aurora": aurora, "terra": terra, "pulse": pulse, "zen": zen,
    "monolith": monolith, "horizon": horizon, "bloom": bloom,
    "forge": forge, "meadow": meadow, "noir": noir, "candy": candy,
    "summit": summit, "lagoon": lagoon, "ember": ember, "orchard": orchard,
}
