# Orbus Online — Round 16.3 Phase 3 Final Report

**Data**: 1 luglio 2026
**Scope**: Eventi Continentali V1 + Incarichi di Sede (entrate passive con cap).
**Stato**: 🟡 **READY-TO-VERIFY** — Backend/API/admin/audit + 28 test pytest + frontend + doc di memoria completati. Ready per E2E browser finale.

---

## 0. Sigillo Phase 2 + Cleanup dev

✅ `round163_phase2_final_report.md` header → `OFFICIALLY CLOSED ✅` con nuova sezione "E2E Verification (e1_tester 4/4 PASS)" + WARN filtro `is_active` (design confermato).
✅ `orbus_world_roadmap.md` Phase 2 → `CLOSED ✅`.
✅ `orbus_audit_snapshot.md` sezione "R16.3 Phase 2 closed" (5 righe) presente.
✅ Nuovo script `app/scripts/reset_test_account_world_state.py` — permanente, gated `APP_ENV != production`. Eseguito con successo: tester ora su `ambash`, `change_count=0`, next_change +30gg (2026-07-31).

## 1. Struttura backend

Due moduli separati (per clarity) sotto `backend/app/`:
- `world_events/__init__.py` (~340 righe) — catalog 12 eventi + instances + admin CRUD
- `site_contracts/__init__.py` (~340 righe) — config + ledger daily + claim CAS + admin

Registrati in `core/app_factory.py` con seed a boot (idempotente) + `ensure_indexes` per `guild_site_income_ledger` unique `(guild_id, day_bucket)`.

## 2. Collections MongoDB

| Nome | Ruolo | Delete? |
|---|---|---|
| `continent_event_catalog` | 12 eventi statici | ❌ solo `is_active=false` (admin) |
| `continent_event_instances` | eventi programmati/attivi/expired | ❌ status flow `scheduled → active → expired` |
| `guild_site_income_config` | singleton config economica | ❌ modificato via PATCH admin |
| `guild_site_income_ledger` | 1 riga giornaliera per gilda | ❌ append + `claimed_at` flip |

## 3. Catalog 12 eventi (idempotente)

| Slug | Categoria | Modificatore |
|---|---|---|
| `clima_mite` | clima | +5% site_income |
| `carestia` | economia | -10% site_income |
| `boom_commerciale` | economia | +15% site_income |
| `instabilita_magica` | magia | +10% mission_risk (esposto, NON applicato Phase 3) |
| `benedizione_divina` | divino | +10% site_income |
| `maledizione` | divino | -15% site_income |
| `invasione_locale` | guerra | flavor puro |
| `stagione_fertile` | natura | +8% site_income |
| `tempesta_elementale` | elementi | flavor puro |
| `frattura_del_vuoto` | vuoto | flavor puro (tag Ergolat/Alveora) |
| `guerra_locale` | guerra | flavor puro |
| `presenza_mostri` | mostri | flavor puro |

Tutti i modificatori entro `[-30, +30]` (verificato T03). 5 eventi con `site_income_pct` attivi. Un solo evento `mission_risk_pct` esposto in preparazione a Phase 4-5 (NON ancora applicato al gameplay).

## 4. Formula entrata giornaliera (trasparente)

```
level      = guild.guild_level or guild.level or 1
base       = config.base_income + config.level_bonus_per_level * (level - 1)
rep_mult   = 1 + min(guild.reputation / 1000, 0.2)   # max +20%, cap 1.2
event_mod  = active_continent_event.modifier_value / 100 se site_income_pct
gross      = (base + reputation_bonus) * (1 + event_mod)
final      = min(gross, config.hard_cap_daily)        # safety cap 500 oro/giorno
```

**Config di default** (seed):
- `base_income = 20`
- `level_bonus_per_level = 5` → level 10 = 65 oro base
- `hard_cap_daily = 500` (protezione anti-inflazione)
- `reputation_multiplier_max = 1.2` (max +20%)

**Sanity check numerico** (verificato T11-T13):
- Guild lv 1, rep 0: 20 oro/g
- Guild lv 10, rep 0: 65 oro/g
- Guild lv 10, rep 500: 65 * 1.2 = ~78 oro/g
- Guild lv 20, rep 5000, evento +30%: `min(round(120 * 1.2 * 1.30), 500) = min(187, 500) = 187`; se scala a lv 30+ → hard cap 500

Il complemento è piccolo vs raid successful (migliaia di oro).

## 5. API pubbliche

| Metodo | Path | Descrizione |
|---|---|---|
| GET | `/api/world-events/continent/{slug}/active` | Evento attivo su un continente (public). On-visit fallback expire scaduti. |
| GET | `/api/world-events/mine` | Evento attivo nel continente della gilda. 403 senza access, 409 senza presence. |
| GET | `/api/site-income/today` | Situazione giornaliera + breakdown. Crea row idempotentemente. |
| POST | `/api/site-income/claim` | CAS `claimed_at:null → now`, `$inc gold`, audit. Retry → `skipped/already_claimed`. |
| GET | `/api/site-income/history?days=7` | Storico ultimi N giorni (cap 30). |

## 6. API admin

| Metodo | Path | Note |
|---|---|---|
| POST | `/api/admin/world-events` | Crea instance (scheduled/active). CAS 409 se altro active su continente. |
| POST | `/api/admin/world-events/{eid}/activate` | scheduled → active. CAS. |
| POST | `/api/admin/world-events/{eid}/expire` | scheduled|active → expired. Soft, no delete. |
| GET | `/api/admin/world-events/all` | Filtri `continent_slug`, `status`, limit ≤ 200. |
| GET | `/api/admin/world-events/catalog` | Lista 12 eventi catalog. |
| GET | `/api/admin/site-income/config` | Leggi config singleton. |
| PATCH | `/api/admin/site-income/config` | Modifica base/bonus/cap/rep_max, audit `SITE_INCOME_CONFIG_UPDATED`. |
| GET | `/api/admin/site-income/stats?window_days=7` | Aggregato oro totale + top 10 gilde per income. |

Tutti gated `is_admin=true` via `get_admin_user`.

## 7. Audit events

Aggiunti a `EVENT_TYPES` (log.py) + `AUDIT_EVENT_WHITELIST` (admin filter):
- `CONTINENT_EVENT_CREATED`
- `CONTINENT_EVENT_ACTIVATED`
- `CONTINENT_EVENT_EXPIRED`
- `SITE_INCOME_CLAIMED`
- `SITE_INCOME_CONFIG_UPDATED`

Test T21 verifica accettazione 200 dell'admin filter per tutti e 5.

## 8. Frontend mobile-first

| File | Ruolo |
|---|---|
| `pages/WorldEvents.jsx` | Evento attivo continente gilda con modifier badge trasparente |
| `pages/SiteContracts.jsx` | Breakdown giornaliero + CTA "Reclama" + storico 7gg |
| `components/SiteIncomeMiniCard.jsx` | Card Dashboard con "X oro pronti da reclamare" |
| `components/ContinentEventBanner.jsx` | Slim banner Dashboard con evento attivo |
| `App.js` | +2 route protette (`/world-events`, `/site-contracts`) |
| `components/navMenu.js` | +1 voce "Eventi" sotto "Mondo" (badge NEW), +1 "Incarichi di Sede" sotto "Gilda" (badge NEW) |
| `pages/Dashboard.jsx` | Banner evento (slim) + grid 2col con SiteIncomeMiniCard + WorldMiniCard |

Mobile: `pb-32 md:pb-8`, CTA `w-full md:w-auto`, tap `min-h-[44px]`, no overflow-x, sezioni impilate. ESLint clean 4/4 file, webpack `Compiled successfully!`.

Modifier badges colorati (green ≥0, red <0, amber neutro) rendono la matematica esplicita.

## 9. On-visit fallback (no scheduler)

- `_get_active_event_for_continent(slug)`: prima di ritornare l'evento, chiama `update_many({continent_slug, status:"active", ends_at ≤ now}, {status:"expired"})` best-effort. Verificato T23.
- `_ensure_today_row(guild)`: la row `guild_site_income_ledger` per il giorno corrente è creata al primo hit di `/today`. Se race lost sul unique key, re-fetch. Nessuno scheduler.

## 10. Recovery script

`app/scripts/expire_stuck_continent_events.py` (permanente, come `expire_stuck_world_boss_events.py` di Phase 1):
- `--dry-run` → lista eventi stuck
- `--apply` → CAS flip + audit emit per ognuno

Verificato T24.

## 11. Test pytest

**File**: `backend/tests/backend_round163_phase3_test.py`
**Risultato locale**: **28/28 PASS** in 6.2s (2 workers xdist)

| # | Test | Focus |
|---|---|---|
| T01 | `catalog_seed_creates_12_events` | seed 12 slug |
| T02 | `catalog_seed_idempotent` | 2° call `inserted=0` |
| T03 | `modifier_ranges_within_bounds` | `[-30, +30]` |
| T04 | `admin_create_event_scheduled` | POST /admin/world-events → 200 scheduled |
| T05 | `admin_activate_event` | POST /activate flip |
| T06 | `admin_activate_conflict_when_another_active` | 409 |
| T07 | `admin_expire_event` | POST /expire flip |
| T08 | `only_one_active_event_per_continent` | Second activate → 409 |
| T09-T10 | `site_income_today_creates_row/breakdown_structure` | ledger creation |
| T11 | `site_income_hard_cap_respected` | 500/g cap safety |
| T12 | `site_income_level_bonus_applied` | lv10 = 65 |
| T13 | `site_income_reputation_multiplier_applied` | +20% cap |
| T14 | `claim_credits_gold_once` | first claim credita gold |
| T15 | `claim_idempotent_retry` | 2nd → `skipped/already_claimed` |
| T16 | `claim_gold_not_double_credited` | 3rd → gold unchanged |
| T17-T18 | `history_returns_recent/capped_at_30_days` | history filter |
| T19 | `audit_site_income_claimed_emitted` | ≥1 riga |
| T20 | `audit_continent_event_created_emitted` | ≥1 riga |
| T21 | `audit_whitelist_accepts_new_events` | admin filter 200 x5 |
| T22 | `admin_config_patch_audits` | PATCH → audit |
| T23 | `on_visit_fallback_expires_stuck_event` | expire scaduti |
| T24 | `recovery_script_expires_stuck_events` | script apply flip |
| T25 | `no_hard_delete_on_expire` | count invariato |
| T26 | `regression_previous_modules_still_importable` | world_boss/world/raids importabili |
| T27 | `openapi_has_phase3_paths` | tutti gli 11 path pubblici + admin |
| T28 | `event_modifier_reflected_in_today` | integration: evento +15% → breakdown |

## 12. Regression completa

```
$ pytest tests/backend_round16{1,A}_phase{1,2,3}_test.py \
         tests/backend_round1611_raid_recovery_test.py \
         tests/backend_round163_phase{1,2,3}_test.py \
         tests/backend_phase14_4_round15_test.py \
         tests/backend_dev_seed_test.py
================= 136 passed, 2 skipped, 0 failed in 13.74s =================
```

**136 PASS / 2 skipped / 0 fail** = 108 pre-esistenti + **28 nuovi Phase 3**. Zero regressioni.

## 13. Vincoli rispettati

| Vincolo | Stato |
|---|---|
| NO deploy | ✅ solo preview |
| NO hard delete | ✅ verificato T25 |
| NO scheduler globale | ✅ solo on-visit + seed a boot |
| NO P2W / premium advantage | ✅ nessun paywall, cap uguale per tutte le gilde |
| NO risorse continentali (Phase 4) | ✅ non implementate |
| NO Forgia Leggendaria (Phase 5) | ✅ non implementata |
| NO patti/PvP/stalla (Phase 6-8) | ✅ non implementati |
| Cap conservativo | ✅ 20 oro/g @ lv 1, 500 oro/g @ max — molto sotto un raid |
| Modificatori trasparenti | ✅ tutti mostrati +/-X% con label esplicita |
| Idempotenza CAS | ✅ create/activate/expire/claim tutti CAS-protected |
| Lingua IT primaria | ✅ label UI, seed dual `_it/_en` |
| UTC ovunque | ✅ `datetime.now(timezone.utc)` |
| Zero regressioni | ✅ 136/138 PASS |

## 14. Files toccati / creati

### Backend
| File | Tipo |
|---|---|
| `app/world_events/__init__.py` | NEW ~340 |
| `app/site_contracts/__init__.py` | NEW ~340 |
| `app/scripts/reset_test_account_world_state.py` | NEW (Phase 2 cleanup dev utility) |
| `app/scripts/expire_stuck_continent_events.py` | NEW (Phase 3 recovery) |
| `app/audit/log.py` | MOD +5 event types |
| `app/admin/audit_routes.py` | MOD +5 whitelist |
| `app/core/app_factory.py` | MOD +2 module import + on_event startup seed |

### Frontend
| File | Tipo |
|---|---|
| `pages/WorldEvents.jsx` | NEW |
| `pages/SiteContracts.jsx` | NEW |
| `components/SiteIncomeMiniCard.jsx` | NEW |
| `components/ContinentEventBanner.jsx` | NEW |
| `App.js` | MOD +2 route + import |
| `components/navMenu.js` | MOD +2 voci (Eventi sotto Mondo, Incarichi di Sede sotto Gilda) |
| `pages/Dashboard.jsx` | MOD +2 import + banner slim + grid 2col |

### Tests
- `tests/backend_round163_phase3_test.py` — NEW, 28 test.

### Memory
- `memory/round163_phase3_final_report.md` — NEW (questo file)
- `memory/round163_phase2_final_report.md` — MOD (header CLOSED ✅ + sezione E2E)
- `memory/orbus_world_roadmap.md` — MOD (Phase 2 CLOSED, Phase 3 READY-TO-VERIFY)
- `memory/orbus_audit_snapshot.md` — MOD (+ sezione Phase 2 closed + Phase 3 ready)
- `memory/PRD.md` — MOD (+ sezione Phase 3 ready)
- `memory/test_credentials.md` — MOD (documentazione utility reset + recovery)

### OpenAPI count
Phase 3: 12 nuovi path (5 public + 7 admin). Totale endpoint R16.3 = 30.

---

## Prossima Phase proposta

**R16.3 Phase 4 — Risorse continentali (8 slug uniche per continente) + Classifiche continentali basiche**. Introduce competizione soft ma resta puramente cosmetica; leggeri drop rate bonus per gilde massimizzate. Stima 3gg dev + 0.5gg test.

**Deliverable summary Phase 3**:
- ✅ 12 nuovi endpoint (5 pubblici + 7 admin)
- ✅ 4 pagine/component React mobile-first
- ✅ 5 nuovi audit event UPPERCASE in whitelist
- ✅ 28 nuovi test PASS
- ✅ Regression 136/138 · 0 fail
- ✅ Zero hard delete · Zero scheduler globale
- ✅ Cap trasparenti: 20-500 oro/g, formula esplicita
- ✅ Modificatori evento trasparenti (badge +/-X% visibile)
- ✅ Dev reset + recovery script permanenti gated `APP_ENV != production`
- 🟡 UI E2E finale: deferita al playtest R16.3 completo.
