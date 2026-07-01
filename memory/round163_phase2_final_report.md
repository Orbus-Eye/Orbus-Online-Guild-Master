# Orbus Online — Round 16.3 Phase 2 Final Report

**Data**: 1 luglio 2026
**Scope**: Mondo & 8 Mastocontinenti V1 (puro flavor + social).
**Stato**: 🟡 **READY-TO-VERIFY** — Backend/API/admin/audit + 22 test + frontend + doc di memoria completati. In attesa E2E browser finale (`e1_tester` non triggerato per richiesta esplicita utente).

---

## 1. Sigillo Round 16.3 Phase 1

✅ `/app/memory/round163_phase1_final_report.md` header → `OFFICIALLY CLOSED ✅` con nota "HUMAN QA UI mobile deferita al playtest finale al termine dell'intero Round 16.3".
✅ `/app/memory/orbus_world_roadmap.md` Phase 1 → `CLOSED ✅`.
✅ Nessuna verifica UI mobile è richiesta prima della fine di R16.3.

## 2. Backend module `app/world/`

Struttura scelta: **single-file compatto** `app/world/__init__.py` (~460 righe), coerente con `app/world_boss/__init__.py`. Contiene:

- Seed idempotente 8 continenti (upsert su `slug`, `$setOnInsert`).
- Modelli inline (Pydantic body `TogglePayload`).
- Services async: `has_world_access`, `_get_active_presence`, `_validate_and_get_target`, `_activity_bucket`.
- 6 route pubbliche `/api/world/*` + 3 route admin `/api/admin/world/*`.
- Emit audit best-effort tramite `write_audit` esistente.

Collections MongoDB:

| Nome | Ruolo | Delete? |
|---|---|---|
| `world_continents` | Catalog 8 continenti | ❌ solo `is_active=false` |
| `guild_world_presence` | Presenza corrente + archiviata | ❌ `status: active\|archived` |
| `guild_world_presence_history` | Log append-only join/change | ❌ append-only |

## 3. Seed 8 continenti (idempotente)

| Slug | Nome IT | Dominio | Divinità patrona |
|---|---|---|---|
| `ambash` | Ambash | Magia | Sorgente Arcana |
| `velur` | Velur | Reincarnazione | Ruota delle Ere |
| `soe` | Soe | Natura | Radice Madre |
| `efreto` | Efreto | Elementi | Quattro Voci |
| `irthe` | Irthe | Morte | Silente Guardiano |
| `nathos` | Nathos | Vita | Cuore Verde |
| `ergolat` | Ergolat | Vuoto | Luna Morta (Alveora-connected) |
| `aveol` | Aveol | Ordine | Bilancia Eterna |

Seed è chiamato in `app/core/lifespan.py` al bootstrap (idempotente, non sovrascrive).

## 4. Access gate

`has_world_access(guild_id)` → `db.raids.count_documents({"guild_id": …, "status": "completed"}) >= 1`.

**Decisione documentata**: uso `db.raids` (raid endgame) e NON `db.expeditions` — coerente con la lore "il raid è il rito d'accesso al Mondo" e semanticamente allineato al gate "prima raid completata". Se una gilda non ha raid completed → `access:false` con:

```
{ access: false, reason: "first_raid_required",
  requirement: "Completa il tuo primo raid per accedere al Mondo di Orbus",
  cta: "/raids" }
```

## 5. Cooldown 30 giorni & no hard delete

- Su `join` iniziale: `next_change_available_at = now + 30d`, `change_count = 0`.
- Su `change`:
    - Se `now < next_change_available_at` → **HTTP 423 Locked** con `next_change_available_at` in response.
    - Altrimenti CAS `find_one_and_update({id, status:"active"}, $set:{status:"archived", archived_at})`; se fallisce → 409 `race_lost_on_archive`.
    - Nuovo doc inserito con `status:"active"`, `change_count += 1`, nuovo `next_change_available_at`.
- **Nessun `delete_one`/`delete_many`** in nessun path di produzione. History append-only in `guild_world_presence_history` con record `joined` e `changed`.

## 6. API pubbliche (`/api/world/*`)

| Metodo | Path | Descrizione |
|---|---|---|
| GET | `/overview` | `{access, continent, presence, next_change_available_at, guilds_in_continent_count, continents_available?}` |
| GET | `/continents` | Lista 8 continenti attivi |
| GET | `/continents/{slug}` | Dettaglio singolo continente |
| POST | `/continents/{slug}/join` | Prima scelta (gate accesso obbligatorio) |
| POST | `/continents/{slug}/change` | Cambio (gate accesso + cooldown 30gg) |
| GET | `/neighbors` | Max 8 gilde nel proprio continente con `activity` bucket |

Formato response `neighbors`:
```json
{
  "total_in_continent": 12,
  "nearby_guilds": [
    {"guild_id":"...", "name":"...", "level":7,
     "banner_text":"...", "activity":"attiva_settimana"},
    ...
  ]
}
```

Activity bucket: `attiva_oggi | attiva_settimana | attiva_mese | inattiva`. Nessun dato competitivo esposto (nessun rank, gold, power).

## 7. API admin (`/api/admin/world/*`)

| Metodo | Path | Gate | Descrizione |
|---|---|---|---|
| GET | `/continents-stats` | admin | Aggregate `{slug, name_it, is_active, guilds_count}` |
| POST | `/dev/grant-first-raid/{guild_id}` | admin + `APP_ENV != production` | Inserisce fake completed raid marchiato `_dev_first_raid_grant=True` |
| PATCH | `/continents/{slug}` | admin | Toggle `is_active` (mai hard delete) |

Test verifica 403 per non-admin su tutti e 3 gli endpoint.

## 8. Audit events

3 nuovi `event_type` UPPERCASE aggiunti alla whitelist `EVENT_TYPES` in `app/audit/log.py`:

```
WORLD_CONTINENT_JOINED
WORLD_CONTINENT_CHANGED
WORLD_ACCESS_GRANTED   (emesso dal dev grant utility)
```

Whitelist admin audit filter (`app/admin/audit_routes.py::AUDIT_EVENT_WHITELIST`) estesa append-only con gli stessi 3 valori (test T20 verifica accettazione 200 per ognuno).

## 9. Frontend mobile-first

| File | Ruolo |
|---|---|
| `frontend/src/pages/World.jsx` | Overview 3-branch: blocked / no-continent / with-continent |
| `frontend/src/pages/WorldContinent.jsx` | Dettaglio continente (lore + tags + status) |
| `frontend/src/pages/WorldNeighbors.jsx` | Lista 8 gilde vicine |
| `frontend/src/components/WorldMiniCard.jsx` | Mini-card riassuntiva in Dashboard V2 |
| `frontend/src/App.js` | 3 nuove route protette (`/world`, `/world/continents/:slug`, `/world/neighbors`) |
| `frontend/src/components/navMenu.js` | Nuova macro-sezione "Mondo" (posizionata dopo "Missioni") con badge NEW |

Mobile-first checklist:
- `pb-32 md:pb-8` main container (bottom-nav clear)
- CTA `w-full md:w-auto`
- Tap target `min-h-[44px]`
- Nessun `overflow-x-auto` forzato / `w-[fixed_px]`
- Modal `ChooseModal` con `⚠ Cooldown 30 giorni` warning esplicito prima di join/change

Design: coerente con `WorldBoss.jsx` (bordi sottili `border-border/60`, accento `text-amber`, testi `text-[11px]/[12px]`, font mono).

## 10. Test pytest (22 richiesti)

**File**: `backend/tests/backend_round163_phase2_test.py`
**Risultato locale**: **22/22 PASS** in 2.57s

| # | Test | Verifica |
|---|---|---|
| T01 | `test_world_continents_seed_creates_8_continents` | 8 slug corretti in DB |
| T02 | `test_world_continents_seed_idempotent` | 2° chiamata `inserted=0` |
| T03 | `test_world_access_denied_without_completed_raid` | Gate 403 con `reason=first_raid_required` |
| T04 | `test_world_access_granted_after_completed_raid` | Tester con 365+ raid → access:true |
| T05 | `test_world_overview_no_continent_lists_all_8` | `continents_available` len=8 |
| T06 | `test_world_overview_with_continent_returns_presence` | Include continent + presence + next_change |
| T07 | `test_join_continent_creates_presence` | POST /join → 200, `change_count=0` |
| T08 | `test_join_continent_forbidden_without_access` | Clean user → 403 |
| T09 | `test_join_continent_forbidden_if_already_active` | 2nd join → 409 |
| T10 | `test_change_continent_forbidden_before_30_days` | HTTP 423 |
| T11 | `test_change_continent_allowed_after_30_days` | Fast-forward cooldown → 200 |
| T12+T13 | `test_change_continent_archives_previous_and_increments` | 1 archived + 1 active + `change_count += 1` |
| T14 | `test_neighbors_returns_from_same_continent` | Lista ≤ 8, contiene `total_in_continent` |
| T15 | `test_neighbors_forbidden_without_continent` | Senza presence → 409 |
| T16 | `test_admin_continents_stats_admin_only` | admin 200, non-admin 403, len(stats)=8 |
| T17 | `test_admin_toggle_continent_is_active` | Off + Restore idempotenti |
| T18 | `test_audit_world_continent_joined_emitted` | ≥1 riga `WORLD_CONTINENT_JOINED` |
| T19 | `test_audit_world_continent_changed_emitted` | ≥1 riga `WORLD_CONTINENT_CHANGED` |
| T20 | `test_audit_filter_whitelist_accepts_world_events` | Admin filter 200 per ognuno dei 3 event |
| T21 | `test_change_continent_never_hard_deletes_history` | 2 history + 2 presence dopo change (nessuna delete) |
| T22 | `test_openapi_not_broken` | `/api/world/*` + `/api/admin/world/*` ≥ 8 path |
| T23 | `test_raid_recovery_and_world_boss_still_work` | Regression: `resolve_stuck_raid`, `resolve_stuck_world_boss_event`, `has_world_access` importabili |

Tutti i test usano cleanup pre/post via `_cleanup_test_state()`.

## 11. Regression completa

```
$ pytest tests/backend_round161_phase{1,2,3}_test.py \
         tests/backend_round16A_phase{1,2,3}_test.py \
         tests/backend_round1611_raid_recovery_test.py \
         tests/backend_round163_phase{1,2}_test.py \
         tests/backend_phase14_4_round15_test.py \
         tests/backend_dev_seed_test.py
================= 108 passed, 2 skipped, 2 warnings in 10.73s =================
```

**108 PASS / 2 skipped / 0 fail** = 86 pre-esistenti + **22 nuovi Phase 2**. Zero regressioni.
Target minimo utente: ≥ 108 test. ✅ Raggiunto esattamente.

## 12. Vincoli rispettati

| Vincolo | Stato |
|---|---|
| NO deploy | ✅ solo preview |
| NO hard delete | ✅ verificato T21 |
| NO modifiche a economia/XP/drop/PvP/arena | ✅ nessun touch a `expeditions/`, `pvp/`, `dungeons/`, `formulas.py`, `market/`, `forge/` |
| NO eventi continentali (Phase 3) | ✅ non implementati |
| NO entrate passive (Phase 3) | ✅ non implementate |
| NO risorse continentali (Phase 4) | ✅ non implementate |
| NO Forgia Leggendaria / Arfus (Phase 5) | ✅ non implementate |
| NO patti / PvP continentale / stalla (Phase 6-8) | ✅ non implementati |
| NO P2W | ✅ scelta puramente flavor, nessun bonus/malus di gioco |
| NO scheduler globale | ✅ solo idempotent seed a boot |
| UI italiana + dual-lang persistito | ✅ IT primario, EN affiancato nel seed |
| Cooldown UTC | ✅ `datetime.now(timezone.utc)` ovunque |
| Zero regressioni | ✅ verificato con 108/110 test |

## 13. Files toccati / creati

### Backend (5 file)
| File | Tipo | Note |
|---|---|---|
| `backend/app/world/__init__.py` | NEW ~460 righe | modulo compatto single-file |
| `backend/app/core/app_factory.py` | MOD | mount `router` + `admin_router` |
| `backend/app/core/lifespan.py` | MOD | invoke `seed_world_continents()` at boot |
| `backend/app/audit/log.py` | MOD | +3 event types |
| `backend/app/admin/audit_routes.py` | MOD | +3 event types alla whitelist admin filter |

### Frontend (5 file)
| File | Tipo |
|---|---|
| `frontend/src/pages/World.jsx` | NEW |
| `frontend/src/pages/WorldContinent.jsx` | NEW |
| `frontend/src/pages/WorldNeighbors.jsx` | NEW |
| `frontend/src/components/WorldMiniCard.jsx` | NEW |
| `frontend/src/App.js` | MOD (+3 route + 3 import) |
| `frontend/src/components/navMenu.js` | MOD (+1 sezione "Mondo") |
| `frontend/src/pages/Dashboard.jsx` | MOD (+1 card `WorldMiniCard`) |

### Tests (1 file)
- `backend/tests/backend_round163_phase2_test.py` — NEW, 22 test.

### Memory (3 file)
- `memory/round163_phase2_final_report.md` — NEW (questo file)
- `memory/round163_phase1_final_report.md` — MOD (header sigillo)
- `memory/orbus_world_roadmap.md` — MOD (Phase 1 CLOSED, Phase 2 READY-TO-VERIFY)

### OpenAPI count
Post-Phase 2: 9 nuovi path (`/api/world/{overview,continents,continents/{slug},continents/{slug}/join,continents/{slug}/change,neighbors}` + `/api/admin/world/{continents-stats,dev/grant-first-raid/{guild_id},continents/{slug}}`).

---

## Prossima Phase proposta

**R16.3 Phase 3 — Eventi continentali admin + Incarichi di Sede (entrate passive con cap)**. Stima 2-2.5gg dev + 0.5gg test.

**Deliverable summary**:
- ✅ 9 endpoint world (6 public + 3 admin)
- ✅ 4 pagine/component React mobile-first
- ✅ Idempotenza seed + CAS join/change
- ✅ 22 nuovi test PASS
- ✅ Regression 108/110 PASS · 0 fail
- ✅ Zero cambi economia/XP/drop/PvP
- ✅ Zero hard delete
- 🟡 UI E2E finale: deferita al playtest R16.3 completo (Phase 2-8).
