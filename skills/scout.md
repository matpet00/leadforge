# Scout Agent — RZP Ingestion Policy (v1, 2026-08)

## Úkol
Najít v živnostenském rejstříku (RZP) firmy BEZ vlastního webu, kterým lze prodat
jednostránkový web. Scout je vstupní brána funnelu — špatný výběr tady plýtvá
všemi dalšími agenty.

## Zdroje dat
1. **Sample mode** (`data/sample_rzp.json`) — offline testy, vždy funguje
2. **Live mode** — XSLT/XML exporty z justice.cz nebo RZP open data.
   Pokud zdroj selže (403/timeout), NIKDY nevymýšlet data — reportuj "scout
   unavailable: <reason>" a skonči. Lepší prázdný scout než falešné leady.

## Výběr oborů (GOOD_INDUSTRIES)
Vyber jen obory, kde web reálně prodává:
- **tradesman**: strojní, zahradní, stavební, tesařské, malířské, instalatérské
- **salon**: kadeřnictví, kosmetika, masáže
- **auto**: autoservis, autolakovna, pneuservis
- **gastronomy**: restaurace, hospoda, catering

Vše ostatní → industry="other" → scorer to stejně zahodí. Nezbytečně nezatěžuj
pipeline. Obory jako velkoobchod, holdingy, pronájem nemovitostí přeskočit hned.

## Normalizace
- ICO vždy 8 číslic jako string
- company_name bez zkrácených právních forem na konci (s.r.o. nech, ale trim mezery)
- business_scope = spojené popisy živností "; "
- city parsuj z adresy (poslední segment před PSČ), když nejde → prázdné

## Deduplikace
Stejné ICO = stejný lead. `upsert_lead` to řeší, ale neposílej duplicity záměrně.

## Reportování hubu
Vždy uveď: kolik leadů nascoutováno, z jakého zdroje (sample/live), a jestli
nějaké obory byly vynechány. Při live výpadku navrhni retry za 24h.
