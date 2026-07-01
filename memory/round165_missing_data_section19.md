# Round 16.5 P0 — Section 19 Data Collection (READ-ONLY)

**Data generazione**: 2026-07-01 20:31:24
**DB**: `orbus_r16`
**Script**: `/app/backend/app/scripts/round165_section19_data_collection.py`

> ⚠️  Questo report è **read-only**. Nessun unequip automatico eseguito.
> Le eventuali decisioni sui Legendary orfani sono elencate nel report
> finale `round165_p0_final_report.md`.

---

## 1. Distribuzione livelli avventurieri

- Totale avventurieri: **1985**
  (attivi: 1984, retired: 1)
- Statistiche (attivi): {'count_active': 1984, 'count_retired': 1, 'mean': 1.05, 'median': 1.0, 'min': 1, 'max': 9, 'p90': 1}

### Bande

- **lv1-3**: 1967
- **lv4-6**: 8
- **lv7-9**: 9

---

## 2. Legendary equipaggiati (istanze)

- Fonte dati usata: `inventory_items.equipped_by`
- Totale istanze equipaggiate: **0**

- (nessun Legendary attualmente equipaggiato)

---

## 3. Orphaned Legendaries (adv sotto il nuovo `min_level`)

- Totale istanze orfane: **0**
- Avventurieri unici impattati: **0**
- Gilde uniche impattate: **0**
- Item unici impattati: (nessuno)

### Tabella dettaglio

**Nessun orphan Legendary rilevato.** ✅

**Catalogo `min_level` di riferimento** (post-apply R16.5 P0):
```
{
  "arcane_adept_orb": 9,
  "drake_slayer_blade": 9,
  "drake_slayer_chest": 8,
  "drake_slayer_helm": 8,
  "goblin_hunter_ring": 8
}
```

---

## Note metodologiche

1. La distinzione tra fonti (inventory_items vs adventurer.equipment) è
   dovuta a due schemi possibili nel codebase. Lo script prova entrambi
   e usa il path con più dati.
2. `is_retired=True` esclude gli avventurieri in pensione dal conteggio
   attivo, ma NON dagli orphan check (non dovrebbero avere equip in ogni
   caso, ma li flagghiamo comunque per completezza).
3. Nessuna scrittura è stata eseguita sul DB. Le write methods di
   pymongo sono state monkey-patched all'avvio dello script.
