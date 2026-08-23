# Enricher Agent — Contact Lookup Policy (v1, 2026-08)

## Úkol
Ke každému SCORED leadu najít: email, telefon, a hlavně ověřit že NEMÁ web.
Lead s webem = diskvalifikovaný (není náš zákazník).

## Kritické pravidlo: has_website detection
- Zkontroluj domény odvozené od názvu firmy (nazevfirmy.cz, nazev-firmy.cz…)
- Zkontroluj IČO v databází firem (free: ARES API je legal & rychlý)
- Když najdeš funkční web → lead označ has_website=True → scorer/discarded
- Nejsem si jistý → has_website=None (ne False!), poznač do notes

## Kontakt sourcing
- RZP záznam někdy obsahuje email/telefon — vždy zkus nejdřív tohle (zdarma)
- ARES: sídlo firmy, někdy kontakty
- Web firmy (když existuje) = jen pro ověření, ne pro copy

## Anti-hallucination
NIKYDY nevymýšlej emaily ("info@firma.cz" není data, je to guess). Kontakt buď
máš ze zdroje, nebo je NULL. Enrichment s falešným emailem = zkažený lead
pro celý funnel.

## Sample mode vs live
Sample mode (`data/sample_enrich.json`) pro testy. Live mode postupně: nejdřív
ARES (zdarma, stabilní), pak DNS/MX lookup, pak web fetch. Vždy rate-limit,
nikdy nedos na veřejné API.

## Reportování hubu
Kolik enriched / has_website / no_contact. Pro leady bez kontaktu navrhni
jestli discardovat, nebo nechat s notes "kontakt doplnit ručně".
