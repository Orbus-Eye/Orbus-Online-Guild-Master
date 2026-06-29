# ROUND 13a — Recovery + Lore Pack — Progress Log

> File creato per sopravvivere a eventuali restart context. Ogni fase
> aggiorna questa sezione con stato e count.

## FASE 0 — Baseline (DONE)

Snapshot DB pre-recovery:
- `db.dungeons.count_documents({})` = **32** (di cui `is_active=True` = 32)
- `db.raid_dungeons.count_documents({})` = **8**
- `db.items.count_documents({})` = **121** (attivi/legacy = 120, inactive = 1, test = 0)
- Rarity distribution: Common=42, Uncommon=28, Rare=22, Epic=24, Legendary=5, Signature=0
- `required_adventurer_level > 1`: **0** (gap)
- `required_adventurer_level` explicit (any val): **0** (gap)
- `display_name_it` esistenti: **37** (legacy pre-R11.3; verrà completato)
- `lore_reviewed`: **0**
- `flavor_text_it`: **0**

## FASE 1 — Additività R11.3 (DONE)

Verificato: 22 baseline dungeon + 10 nuovi R11.3 = 32 → **additivi**.
- Slug nuovi presenti: echoes-of-the-broken-thread, shattered-seal-of-ergolat,
  obelisks-of-the-void, plague-warrens-of-irthe, moonlit-strings-of-alevora,
  ashkaroth-crypt-court, eclipthra-veiled-sanctum, gralca-tide-of-the-deep,
  xal-zoraax-throat-of-silence, tip-of-oblivion-trial.
- Raid: 3 baseline (broken-bastion-siege, necropolis-bells, dragon-vault)
  + 5 nuovi R11.3 (rituale-del-vuoto-orde, figli-di-irthe-rising,
  alevora-marionetta-grande, tempio-del-vuoto-eterno, valys-mordivac-final-whisper)
  = 8. Additivi.

**Decisione**: NON seed altri +10/+5. Usiamo i 10+5 R11.3 come "i nuovi".

## FASE 2 — Dungeon/Raid lore rework (IN PROGRESS)

…

## FASE 3+4 — Item lore + req_level (PENDING)

## FASE 5 — API + UI visibility (PENDING)

## FASE 6 — Guide + Test + E2E (PENDING)
