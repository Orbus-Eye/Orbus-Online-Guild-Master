# ROUND 13b — 6 Seasonal Categories with Incremental Tracking (FINAL)

> Stato: **COMPLETO**. Pronto per E2E tester utente.
> Baseline test: 9 R13a PASS + 16 R13b PASS = **25/25** + 1 skip atteso.

## Architettura

### Schema `season_participations.season_stats`
```python
{
    "dungeon_clears": int,
    "raid_clears": int,
    "raid_score": int,
    "contracts_completed": int,
    "training_score": int,
    "territory_score_at_start": int,   # snapshot al join
    "last_updated_at": ISO,
}
```

### Helper `app/seasons/season_stats.py`
- `get_active_season(db)` — single source of truth.
- `increment_seasonal_stat(db, *, guild_id, field, delta, source, source_collection=None, source_id=None, flag_key=None)` — best-effort, no-raise, no-op se no active season o se flag CAS già set.
- `_compute_current_territory_score(db, guild_id)` — sum dei levels in `guild_structures.structures`.
- `ALLOWED_FIELDS = {dungeon_clears, raid_clears, raid_score, contracts_completed, training_score}` — territory letto via delta.

### Hook applicati
| Modulo | File | Evento | Field | Idempotency |
|---|---|---|---|---|
| Expedition | `app/expeditions/services.py:_complete_one_expedition` | success | `dungeon_clears +=1` | CAS `expeditions.id + season_stat_recorded` |
| Raid | `app/raids/__init__.py:complete_raid` | victory/partial | `raid_clears +=1`, `raid_score +=N` | CAS `raids.id + season_stat_recorded_clear/_score` |
| Contract daily | `app/contracts/services.py:claim_daily` | claim | `contracts_completed +=1` | claimed=True CAS upstream |
| Contract weekly | `app/contracts/services.py:claim_weekly` | claim | `contracts_completed +=1` | claimed=True CAS upstream |
| Contract milestone | `app/contracts/services.py:claim_milestone` | claim | `contracts_completed +=1` | claimed=True CAS upstream |
| Training | `app/training/services.py:apply_specialization` | success | `training_score += sig.power_score` | specialization CAS (one per adv) |
| Territory | n/a | (snapshot at_start su `get_or_create_participation`) | letto via delta | no increment |

## Leaderboard

### 6 nuove categorie seasonal
| slug | label_it |
|---|---|
| `dungeon_clears` | Dungeon completati (stagione) |
| `raid_clears` | Raid completati (stagione) |
| `raid_score` | Punteggio Raid (stagione) |
| `territory_score` | Sviluppo Territoriale (stagione) |
| `contracts_completed` | Contratti completati (stagione) |
| `training_score` | Allenamenti (stagione) |

`GET /api/leaderboard/categories?scope=season` → **12 categorie totali** (6 pre-esistenti + 6 nuove).

### Lifecycle
- **Activate season**: nuova participation creata da `get_or_create_participation` con `season_stats` default + `territory_score_at_start = current_sum_structures_level`. Sub-doc inizializzato sia per nuove participations sia (lazy) per participation legacy senza il sub-doc.
- **Active**: ogni hook incrementa solo se `season.status == "active"`.
- **End**: increment helper trova `status != "active"`, no-op silenzioso. I valori dei contatori restano frozen.
- **Archive**: nessun nuovo evento conta. Cache snapshot resta per consultazione.
- **New season activate**: nuove `season_participations` con `season_stats` resettato a 0; le vecchie restano intatte come storico (no hard delete).

## Test BE
```
backend_round13a_test.py:  9 PASSED
backend_round13b_seasonal_increment_test.py: 16 PASSED + 1 SKIPPED
Total: 25 PASSED + 1 SKIPPED
```

### Test BE R13b coverage
- 01 SEASONAL_CATEGORIES include i 6 nuovi slug → totale 12
- 02 `/api/leaderboard/categories?scope=season` ritorna 12
- 03 ognuno dei 6 endpoint HTTP 200 (parametrico × 6)
- 04 helper rifiuta unknown field
- 05 helper no-op se no active season (SKIP — esiste season active in preview)
- 06 idempotency CAS: replay non duplica
- 07 territory delta sempre ≥ 0
- 08 PII guard su tutti i 6 endpoint (no email/oid/owner_user_id)
- 09 categoria sconosciuta → HTTP 400 con detail strutturato
- 10 ALLOWED_FIELDS whitelist coerente con calculators
- 11 `/api/leaderboard?scope=season` senza category → 422
- 12 smoke regression: dungeons/raids/items/recruitment/peak_power ancora 200

## OpenAPI
- Path count: **136 (invariato vs R13a)** — i 6 nuovi calc passano dal path generico `/api/leaderboard` con param `category`, no nuovo path.

## Frontend
- `Leaderboard.jsx` già usa `/api/leaderboard/categories` dinamicamente → automaticamente espone i 6 nuovi tabs.
- `Guide.jsx` sezione `lb-stagionale` aggiornata con elenco 12 categorie + descrizione 1-riga delle 6 R13b.

## Vincoli rispettati
✅ NO deploy produzione  
✅ NO hard delete / NO cleanup LB / NO reset participation pregresse  
✅ NO P2W / NO premium / NO reward power changes  
✅ NO ALLOWLIST change  
✅ NO PII / no _id / no owner_user_id leak  
✅ Tutti gli hook idempotenti (CAS source row o claimed flag pre-esistente)  
✅ Italiano user-facing su label/description  
✅ Audit `season_stat_incremented` per ogni event applicato
