# Round 16.5 P0 — Post-Apply Rapid Audit

**Data**: 2026-07-01
**Modalità**: `--read-only` (nessuna modifica al DB)
**Fonte dati**: `/app/memory/round164_audit_raw_data.json` (audit rieseguito
dopo l'apply della migration `round165_balance_p0_gates_and_legendary_levels`)

---

## TL;DR

- ✅ **Data population OK**: 22 dungeon con `required_level` popolato e 5
  Legendary con `min_level >= 8` (2 outlier a 9).
- ⚠️ **Il gate `required_level` NON è ancora runtime-enforced.** L'apply P0
  ha soltanto scritto la data. Il runtime esistente
  (`expeditions.level_gate.legacy_min_level_for_dungeon`) usa il campo
  legacy `min_adventurer_level` che rimane `None` sui 22 dungeon
  interessati, cadendo sul fallback `difficulty`. Vedi tabella "Runtime
  gate reale vs P0 gate scritto" sotto.
- 📊 **Prova matematica lv4 vs lv7**: senza runtime enforcement del nuovo
  gate, un `team_medio_reale` (lv 4-5, team_power=200) batte
  `silent-monastery-5p` (lv7, rec_pow=155) al **93.7%** in Monte Carlo,
  identico al pre-fix.

---

## 1. Prova diretta — Il fix P0 da solo NON risolve il problema formula-side

`team_medio_reale` (lv 4-5, team_power=200) vs dungeon per fascia
`required_level` (Monte Carlo 10 000 iters):

| req_lvl | dungeon | rec_pow | base_sc | MC eff_sc | verdict |
|---:|---|---:|---:|---:|---|
| 5 | salt-marsh-5p | 100 | 95% | **93.8%** | overshoot |
| 5 | lich-sanctum | 94 | 95% | **93.5%** | overshoot |
| 6 | iron-foundry-5p | 140 | 95% | **93.7%** | overshoot |
| 6 | dragons-hoard | 100 | 95% | **93.7%** | overshoot |
| 6 | storm-spire | 110 | 95% | **94.5%** | overshoot |
| **7** | **silent-monastery-5p** | 155 | 95% | **93.7%** | 🚨 **key case** |
| 8 | pirate-fleet-5p | 170 | 80% | **80.6%** | overshoot |
| 9 | obsidian-arena-5p | 210 | 40% | **39.6%** | **prima soglia sotto 30% assente**, ma <60% |
| 10 | clockwork-vault-5p | 230 | 20% | 20.5% | ok |
| 11 | voidspire-5p | 250 | 10% | 10.2% | ok |
| 12 | infernal-pit-5p | 290 | 10% | 9.9% | ok |

**Interpretazione**: il team lv 4-5 supera i dungeon `required_level=7`
con success chance **93.7%** perché la formula
`compute_success_chance(team_power=200, rec_pow=155)` restituisce
base_sc=95%, e il **gate `required_level` non viene consultato dal
runtime**. La formula non "sa" che il team ha lv 4-5 vs dungeon lv 7.

## 2. Runtime gate reale vs P0 gate scritto

Il runtime di dispatch dungeon usa `min_adventurer_level`. Il P0 ha
scritto `required_level`. Non sono lo stesso campo:

| slug | required_level (P0) | min_adventurer_level (runtime) | difficulty | runtime gate REALE |
|---|---:|---:|---:|---:|
| silent-monastery-5p | **7** | `None` | 2 | fallback → **lv3** |
| pirate-fleet-5p | 8 | `None` | 2 | fallback → **lv3** |
| obsidian-arena-5p | 9 | `None` | 3 | fallback → **lv7** |
| infernal-pit-5p | 12 | `None` | 4 | fallback → **lv12** |

Il fallback `difficulty→min_lvl` mappa `1→1, 2→3, 3→7, 4→12`. Molti
dungeon 5p `difficulty=2` (silent-monastery-5p, pirate-fleet-5p,
iron-foundry-5p) hanno gate runtime lv3 anche se il nuovo `required_level`
dice lv6-8.

## 3. Team outlier lv 6-7 vs endgame

`team_forte_outlier` (lv 6-7, team_power=356) — spinge il caso "player
equip-stacking" evidenziato dall'audit R16.4:

| req_lvl | dungeon | rec_pow | MC success | verdict |
|---:|---|---:|---:|---|
| 8 | pirate-fleet-5p | 170 | **93.3%** | overshoot |
| 9 | obsidian-arena-5p | 210 | 93.7% | overshoot |
| 10 | clockwork-vault-5p | 230 | 94.3% | overshoot |
| 11 | voidspire-5p | 250 | 93.9% | overshoot |
| 12 | infernal-pit-5p | 290 | 93.8% | overshoot |
| 13 | celestial-citadel-5p | 320 | 86.2% | overshoot |
| 14 | world-tree-roots-5p | 360 | 45.4% | quasi ok |

L'audit R16.4 rilevava già "equip stacking a lv4 raddoppia team power".
Con P0 questa dinamica è invariata (P0 non tocca `equip_power` né la
formula).

## 4. Coerenza data-side ✅

Aspetti che invece SONO risolti dall'apply P0:

- Tutti i 22 dungeon hanno ora `required_level >= 1`.
- Curva senza buchi > 2 (lv 1→2→3→4→5→6→7→8→9→10→11→12→13→14).
- 5 Legendary con `min_level >= 8` (drake_slayer_blade, arcane_adept_orb
  a 9; gli altri a 8) — coerente con l'obiettivo di rendere Legendary un
  equipaggiamento late-game.
- 3 dungeon `progression_tag=story_catchup` (wolf-den-5p, frost-cave-5p,
  salt-marsh-5p): marker esplicito per contenuto narrativo bypassabile.

## 5. Conclusione audit

- **Data population**: ✅ eseguita correttamente.
- **Runtime enforcement del nuovo `required_level`**: ❌ **NON attivo**.
- **Problema utente originale ("team lv4 batte dungeon lv7")**:
  parzialmente indirizzato solo per i dungeon con `difficulty >= 3` (che
  il fallback runtime già gattava a lv7+). Per i dungeon `difficulty=2`
  con nuovo `required_level >= 6` il problema persiste finché il runtime
  non legge il nuovo campo.

Prossimo passo suggerito nel report finale: **P1 = wiring del runtime
gate al nuovo `required_level`** (una singola modifica in
`expeditions/level_gate.py::legacy_min_level_for_dungeon`).
