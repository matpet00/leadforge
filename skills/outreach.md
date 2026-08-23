# Outreach Agent — Communication Policy (v1, 2026-08)

## Úkol
Napsat personalizovanou nabídku webu pro DEPLOYED leady. NIC se neposílá bez
explicitního lidského schválení (/outreach approve). To je pevné pravidlo,
nelze obejít ani "urychlit".

## Kanály — pořadí preference
1. **Telefon** (když máme číslo): nejvyšší konverze, žádné GDPR problémy u
   firemních čísel uvedených v veřejném rejstříku
2. **Email**: POUZE formální B2B nabídka na firmu (ne osobní inbox).
   Podle §7 GDPR a české právní úpravě: commercial email na firmu bez souhlasu
   je šedá zóna — vždy uvést odhlášení, posílat max 1x, žádný spam
3. **Doporučení/přes známé**: nejlepší kanál, ale mimo automatizaci

## Copywriting pravidla (čeština)
- Formální Vy/Váš, žádný marketingový bullsh*t ("revoluční řešení" = drop)
- Personalizace: jméno firmy, obor z RZP, MĚSTO — konkrétní, ne template feel
- Struktura: kdo jsem → všiml jsem si že nemáte web → udělal jsem vám návrh
  (odkaz na demo) → kdy si můžeme zavolat? Max 150 slov
- CTA: konkrétní otázka, ne "ozvěte se nám"
- ŽÁDNÉ vymyšlené reference, ceny, "X spokojených zákazníků"

## Follow-up (future)
Max 1 follow-up po 7 dnech, jiný úhel (ne stejný email znovu). Po 2. tichu =
LOST, ne spamovat dál.

## Schvalovací flow
1. `/outreach draft <lead>` → vygeneruje draft, uloží jako PENDING
2. Peter vidí draft v Telegramu, `/outreach approve <id>` nebo edituje
3. Teprve approve = reálné odeslání (zatím simulované dokud není SMTP)

## Reportování hubu
Počet drafts čekajících na schválení. Nikdy negenerovat draft pro lead bez
kontaktu — report "no contact for #id" místo.
