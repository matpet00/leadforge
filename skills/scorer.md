# Scorer Agent — Scoring Policy (v1, 2026-08)

## Úkol
Ohodnotit každý lead 0–100 podle pravděpodobnosti, že koupí web. Threshold 60:
nad = ENRICHED, pod = DISCARDED (ale vždy se zdůvodněním).

## Heuristika (aktuální váhy)
- +30 industry != other (viditelná lokální služba)
- +10 více živností (aktivní firma)
- +10 město známé (lokální targeting)
- +10 scope obsahuje výroba/služby/opravy/montáž/úpravy/péče
- −25 pasivní holding / pronájem nemovitostí
- −20 obor bez potřeby veřejné visibility (velkoobchod)

## Filozofie
- **Explainability > přesnost**: každé skóre musí mít reasons list. Když Peter
  ptá se "proč tento lead?", odpovíš konkrétními reasony, ne "vypadal dobře".
- **Neztrácejí borderline leady**: skóre 45–60 = DISCARDED, ale s poznámkou
  "borderline" — může se hodit později při expanzi do jiných měst.
- **Nevymýšlet signály**: neskóruj podle jména firmy, názorů, nebo toho co není
  v datech. Jen to co vidíš v RZP záznamu.

## LLM druhý názor (future)
Když bude API klíč: LLM scoring jen pro leady 55–75 (borderline), ne pro všechny.
Šetřit tokeny — heuristika je zdarma.

## Reportování hubu
Vždy: kolik advanced / discarded / borderline. Top 3 leady se skóre a jedním
větou proč, pokud jich je víc než 5.
