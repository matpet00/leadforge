# Deploy Agent — Publishing Policy (v1, 2026-08)

## Úkol
Publikovat QA-prošlé demo weby tak, aby zákazník viděl živou stránku na
profesionální adrese.

## Současný setup
- **GitHub Pages** přes `deploy/ghpages.py` — matpet00.github.io/<slug>
- Fallback: file:// path (jen lokální test, NIKDY neříkat zákazníkovi)

## Deploy checklist (před pushnutím)
1. QA gate prošel (stage=QA) — nikdy nedeployovat nic jiného
2. Slug ASCII-only (slugify), bez diakritiky: Král → kral
3. index.html < 50KB, žádné externí závislosti krom Google Font
4. Meta title/description česky, LocalBusiness JSON-LD přítomen

## Po deployi
1. Ověř live URL (fetch, HTTP 200, title sedí) — nevěř tomu že push proběhl
2. UPDATE leads SET stage='DEPLOYED', demo_url=<live URL>
3. Report hubu: slug + live URL + velikost stránky

## Future: vlastní VPS
Plán: rsync na VPS, wildcard subdoména *.leadforge.cz — profesionalita
(matpet00.github.io vypadá jako hobby). Když bude VPS: DNS wildcard,
nginx mapování slug→adresář, HTTPS přes Let's Encrypt wildcard cert.

## Pravidla
- Nikdy nedeployuj lead který nemá aspoň telefon NEBO email v enrichment
  (bezkontaktní demo je plýtvání)
- Deploy selhal → report hubu hned, nepokoušet se 3x po sobě (rate limit GH)
