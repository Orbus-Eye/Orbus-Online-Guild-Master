# Round 16.5 P0.3 — Fallback `difficulty` diff analysis (opzione D2)

**Data**: 2026-07-01
**Modalità**: read-only su `orbus_r16`
**Scopo**: verificare che la rimozione del fallback `difficulty → min_level`
(step 3 dell'attuale gate resolver) sia sicura, prima di modificare il
codice.

---

## Setup: mappa fallback attualmente in produzione

`_DUNGEON_DIFFICULTY_TO_MIN_LEVEL` = `{1: 1, 2: 3, 3: 7, 4: 12}`
Applicata come step 3 in `legacy_min_level_for_dungeon()` **solo** se
`required_level` e `min_adventurer_level` sono entrambi assenti/0/None.

## Risultati diagnostici

| metrica | valore |
|---|---:|
| Dungeon totali in DB | 22 |
| Dungeon attivi (`is_active=True`) | 22 |
| Dungeon con `required_level` popolato | 22 |
| Dungeon con `min_adventurer_level` popolato | 0 |
| Dungeon che dipendono **solo** dal fallback difficulty | **0** |
| Dungeon impattati dal cambio (`delta != 0`) | **0** |
| Dungeon **attivi** che perderebbero il gate diventando `0` | **0** ✅ |

## Verdetto

**REMOZIONE SAFE.** Dopo l'apply P0.2, tutti i 22 dungeon attivi hanno
`required_level >= 1` come primo campo canonico. Il fallback
`difficulty→min_level` non viene mai attivato in produzione.

## Elenco dungeon con verifica per-doc

| slug | required_level | min_adventurer_level | difficulty | gate_ora | gate_dopo | delta |
|---|---:|---:|---:|---:|---:|---:|
| sewer-nest | 1 | None | 1 | 1 | 1 | 0 |
| goblin-warrens | 2 | None | 1 | 2 | 2 | 0 |
| bandit-hideout | 2 | None | 1 | 2 | 2 | 0 |
| druid-grove | 3 | None | 2 | 3 | 3 | 0 |
| shadow-crypts | 3 | None | 2 | 3 | 3 | 0 |
| wolf-den-5p | 3 | None | 1 | 3 | 3 | 0 |
| cursed-mines | 4 | None | 2 | 4 | 4 | 0 |
| sunken-library | 4 | None | 2 | 4 | 4 | 0 |
| frost-cave-5p | 4 | None | 1 | 4 | 4 | 0 |
| lich-sanctum | 5 | None | 3 | 5 | 5 | 0 |
| salt-marsh-5p | 5 | None | 1 | 5 | 5 | 0 |
| dragons-hoard | 6 | None | 3 | 6 | 6 | 0 |
| storm-spire | 6 | None | 3 | 6 | 6 | 0 |
| iron-foundry-5p | 6 | None | 2 | 6 | 6 | 0 |
| silent-monastery-5p | 7 | None | 2 | 7 | 7 | 0 |
| pirate-fleet-5p | 8 | None | 2 | 8 | 8 | 0 |
| obsidian-arena-5p | 9 | None | 3 | 9 | 9 | 0 |
| clockwork-vault-5p | 10 | None | 3 | 10 | 10 | 0 |
| voidspire-5p | 11 | None | 3 | 11 | 11 | 0 |
| infernal-pit-5p | 12 | None | 4 | 12 | 12 | 0 |
| celestial-citadel-5p | 13 | None | 4 | 13 | 13 | 0 |
| world-tree-roots-5p | 14 | None | 4 | 14 | 14 | 0 |

**Tutti i delta sono 0.** Nessuna regressione runtime possibile.

## Note sui dungeon test (`r165test-*`)

Presenti solo nel DB `orbus_r16_test` (isolato), non nel DB prod. Non
rientrano nel conteggio sopra. Sono usati nei test HTTP P0.3 per
verificare il fallback legacy e il caso "entrambi assenti" (che *deve*
continuare a funzionare → gate=0, no-op).

## Decisione

Procedo con A.2 (rimozione del fallback `difficulty`) senza pausa.
Il checkpoint #1 non è triggerato: 0 dungeon impattati.
