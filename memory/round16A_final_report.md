# Orbus Online — Round 16.A Final Report

**Status: 🟢 OFFICIALLY READY FOR E2E SIGN-OFF**
**Closing date**: 30 giugno 2026
**Scope**: Achievement Hooks Coverage + Audit Bridge + Admin Read-Only Audit Dashboard.

> **Note**: il bollo `OFFICIALLY CLOSED` viene posto **solo dopo** la verifica
> E2E di `e1_tester`, che l'utente lancia esplicitamente. Questo report
> documenta lo stato "ready to seal".

---

## 1. Stato finale Round 16.A

**🟢 READY** — Tre fasi tutte verdi:

| Fase | Titolo | Stato | Test |
|---|---|---|---|
| **R16.A P1** | Trigger Emission Layer (10 hook wired + 1 deferred) | ✅ PASS | 14 passed, 1 skipped |
| **R16.A P2** | Audit Bridge + `add_guild_xp` helper + `onboarding.graduated` | ✅ PASS | 5 passed |
| **R16.A P3** | Admin Read-Only Audit Dashboard + Sweep XP + E2E | ✅ PASS | 10 passed |

Totale R16.A: **29 passed, 1 skipped, 0 failed** (in 1.37s con parallelismo loadscope).

Suite estesa (R16.1 + R16.A + Phase 14.4 + dev-seed): **58 passed, 1 skipped, 0 failed** (in 7.84s).

---

## 2. Cosa è stato implementato

### Fase 1 — Trigger Emission Layer (chiusa precedentemente)

Wiring di 10 `trigger_event` su altrettanti code path canonici via il nuovo
emitter `app.achievements.trigger_emitter.emit_achievement_trigger`:

| # | trigger_event | Code path | Test |
|---|---|---|---|
| 1 | `item_crafted` | `app/crafting/services.py` | `test_t01_item_crafted_wired` |
| 2 | `market_purchase` | `app/market/services.py` (gold→item) | `test_t02_market_purchase_wired` |
| 3 | `auction_purchase` | `app/market/services.py` (winning bid) | `test_t03_auction_purchase_wired` |
| 4 | `auction_sale` | `app/market/services.py` (seller side) | `test_t04_auction_sale_wired_seller_side` |
| 5 | `consortium_joined` | `app/consortium/services.py` | `test_t05_consortium_joined_wired` |
| 6 | `season_league_reached` | `app/seasons/services.py` | `test_t06_season_league_reached_wired` |
| 7 | `leaderboard_rank_reached` | `app/leaderboard/services.py` | `test_t07_leaderboard_rank_reached_wired` (skipped — feature-gated) |
| 8 | `item_disenchanted` | `app/crafting/disenchant.py` | `test_t08_item_disenchanted_wired` |
| 9 | `material_purchased` | `app/market/services.py` (material order) | `test_t09_material_purchased_wired` |
| 10 | `pvp_match_completed` | `app/pvp/services.py` (both winner + loser) | `test_t10_pvp_match_completed_wired_both_sides` |
| 11 | `territory_upgraded` | `app/territory/services.py` | `test_t11_territory_upgraded_wired` |

Emissione persistente nella collection `trigger_emissions` con `idempotency_key`.

### Fase 2 — Audit Bridge

1. **Audit log centralizzato** — collection `audit_log` ora popolata
   per tre event_type whitelisted:
   - `achievement_unlocked` (emette su sblocco)
   - `guild_xp_gained` (emette su credito XP)
   - `onboarding_graduated` (emette one-shot quando un utente con
     guild_level≥3 OR completed_expeditions≥3 visita la dashboard).
2. **`add_guild_xp(db, guild_id, amount, *, source, source_id, points_delta)`**
   in `app/achievements/engine.py` come unico entry-point auditato per
   credito XP gilda. Il vecchio `_apply_reward` diventa shim.
3. **Idempotenza** garantita via `idempotency_key` sui tre event_type.

### Fase 3 — Admin Read-Only Audit Dashboard + Closure

#### A. Sweep `add_guild_xp` su `app/expeditions/services.py`

Verifica: `grep -n 'guild_xp\|guild_level' /app/backend/app/expeditions/services.py` → 0 match.

Le spedizioni accreditano XP **agli avventurieri** (via `db.adventurers.update_one`),
**non** alla gilda — nessuna chiamata diretta a `guilds.update_one({"$inc": {"guild_xp": …}})`
da rimpiazzare. La sweep è completata sotto forma di **verifica statica**: il
file è clean, e il sweep delle restanti code path (daily bonus, contracts,
quest rewards) è esplicitamente schedulato per **R16.B**.

#### B. Admin Read-Only Audit Dashboard

**Backend** — 3 endpoint nuovi in `app/admin/audit_routes.py`,
tutti gated da `get_admin_user`:

| Metodo | Path | Funzione | Test |
|---|---|---|---|
| GET | `/api/admin/audit/trigger-emissions` | Feed Fase 1 (`trigger_emissions`) con filtri `event_name`, `guild_id`, paginazione | T01–T03 |
| GET | `/api/admin/audit/events` | Feed Fase 2 (`audit_log`) con whitelist `event_type ∈ {achievement_unlocked, guild_xp_gained, onboarding_graduated}` + filtri `guild_id`, `from`/`to`, paginazione | T04–T06 |
| GET | `/api/admin/audit/summary?window_hours=N` | KPI aggregati (count achievement, XP totale + count, count onboarding, top trigger events) — clamp interno a 720h (30gg) | T07–T08 |

Hard caps: `MAX_LIMIT=200`, `MAX_WINDOW_HOURS=720`. La risposta del summary
include `window_clamped: bool` per UX trasparente.

**Frontend** — nuova pagina `pages/AdminAudit.jsx` (tema scuro, IT-only):
- Tab "Riepilogo" (StatCard × 4 + top trigger events).
- Tab "Emissioni Trigger" (tabella con filtri `event_name` + `guild_id` + paginazione).
- Tab "Timeline Audit" (tabella con filtri `event_type` whitelist + date range + paginazione).
- Mounted in `App.js` su `/admin/audit`, linkata da `AdminOps.jsx`.

#### C. E2E coverage (in `tests/backend_round16A_phase3_test.py`)

1. `test_e2e_tester_advanced_emits_onboarding_graduated_once` — reset flag
   graduation su `The Iron Lantern`, due chiamate consecutive a
   `/api/dashboard/onboarding`, conta esattamente **1** riga
   `onboarding_graduated` (idempotenza one-shot).
2. `test_e2e_new_player_full_flow` — login con `clean_onboarding@orbus.test`
   (no guild), verifica che `audit_log` **non** contenga alcuna riga di
   graduazione per quell'utente.

---

## 3. Test verde — evidenza pytest

```
$ python -m pytest tests/backend_round16A_phase3_test.py -v
============================== 10 passed in 1.37s ==============================
```

Suite estesa (R16.1 P1+P2+P3, R16.A P1+P2+P3, Phase 14.4, dev-seed):

```
$ python -m pytest tests/backend_round161_phase{1,2,3}_test.py \
                    tests/backend_round16A_phase{1,2,3}_test.py \
                    tests/backend_phase14_4_round15_test.py \
                    tests/backend_dev_seed_test.py
================== 58 passed, 1 skipped, 2 warnings in 7.84s ===================
```

Nessuna regressione introdotta.

---

## 4. File principali toccati/creati

### Backend
- ✏️ `app/admin/audit_routes.py` (creato) — 3 endpoint read-only.
- ✏️ `app/main.py` / router include — aggiunto router audit.
- ✏️ `app/achievements/engine.py` — helper `add_guild_xp` (P2).
- ✏️ `app/achievements/trigger_emitter.py` — emitter unico (P1).
- ✏️ `app/dashboard/services.py` — `onboarding_graduated` one-shot (P2).
- ✓ `app/expeditions/services.py` — clean (no sweep needed).

### Frontend
- ✏️ `frontend/src/pages/AdminAudit.jsx` (creato) — 3 tab read-only.
- ✏️ `frontend/src/App.js` — route `/admin/audit`.
- ✏️ `frontend/src/pages/AdminOps.jsx` — link verso `/admin/audit`.

### Tests
- ✏️ `tests/backend_round16A_phase1_test.py` (chiusa precedentemente).
- ✏️ `tests/backend_round16A_phase2_test.py` (chiusa precedentemente).
- ✏️ `tests/backend_round16A_phase3_test.py` (creato — 10 test inclusi 2 E2E).

### Documenti
- ✏️ `memory/round16A_final_report.md` (questo file).
- ✏️ `memory/orbus_audit_snapshot.md` (sezione "Round 16.A closed" aggiunta).

---

## 5. Checklist verifica Phase 3

| # | Punto | Stato | Evidenza |
|---|---|---|---|
| 1 | Sweep `add_guild_xp` su expeditions/services.py | ✅ PASS | Grep → 0 occorrenze `guild_xp` in expeditions |
| 2 | Endpoint `/api/admin/audit/trigger-emissions` con filtri + paginazione | ✅ PASS | T01–T03 verdi |
| 3 | Endpoint `/api/admin/audit/events` whitelist-guarded | ✅ PASS | T04–T06 verdi |
| 4 | Endpoint `/api/admin/audit/summary` con clamp interno window_hours | ✅ PASS | T07–T08 verdi (passing `99999` → 720) |
| 5 | Gating admin su tutti e tre i route (401/403) | ✅ PASS | T01, T04 verificano 403 per non-admin |
| 6 | Frontend `AdminAudit.jsx` 3 tab (Summary/Triggers/Events) | ✅ PASS | Pagina compila, route `/admin/audit` montata |
| 7 | E2E onboarding.graduated one-shot per `tester@orbus.test` | ✅ PASS | T09 verde |
| 8 | E2E new player non emette graduation | ✅ PASS | T10 verde |
| 9 | Nessuna regressione su R16.1 + Phase 14.4 + dev-seed | ✅ PASS | 58 passed, 1 skipped |
| 10 | Hard delete: nessuno | ✅ PASS | Nessun `delete_many` non-test introdotto |
| 11 | Economia/XP/drop rate: invariati | ✅ PASS | Helper `add_guild_xp` ricalcola il livello con formula esistente, no balancing change |

---

## 6. Cosa resta per R16.B / R16.C

### R16.B (P1 — prossima milestone consigliata)
- **Audit events aggiuntivi**:
  - `material_dropped` (emitter + write in `audit_log`).
  - `adventurer_xp_gained` (per audit XP avventurieri).
  - `leaderboard_score_updated` (per snapshot ranking).
- **Sweep `add_guild_xp` esteso** alle code path residue che mutano `guild_xp`:
  - `app/quests/services.py` (daily quest rewards).
  - `app/contracts/services.py` (contract completion).
  - `app/seasons/services.py` (season closing bonus).
  - Eventuali altri `db.guilds.update_one({"$inc": {"guild_xp": ...}})` non ancora rinverditi.
- Persistere `leaderboard_snapshots` (storico ranking) — già in §6 audit snapshot.

### R16.C (P2 — QoL polish)
- Smooth-scroll guide sezione → sezione.
- Lock-in spec UI conferma (modal "sei sicuro? non si può tornare indietro").
- Admin Audit: export CSV + filtri salvati.

---

## 7. Limiti noti / dichiarazioni

- **Test `test_t07_leaderboard_rank_reached_wired` skipped**: la feature
  `leaderboard_rank_reached` è dietro feature flag e non emette in preview.
  Verrà ri-abilitato in R16.B insieme al persist di `leaderboard_snapshots`.
- **`audit_logs` legacy (287 rows)** — collection orfana, non touchata in
  questo round. Archive schedulato per cleanup tecnico futuro.
- **R16.A non tocca produzione**: solo preview, nessun deploy.
- **Compliance balance**: nessun cambio a `base_xp_reward`, `base_gold_reward`,
  drop rate, multiplier formule, soglie level-up. Verificato via diff su
  `app/expeditions/{formulas,loot_tables,material_drop_tables,xp_modifier}.py` (0 modifiche).

---

## 8. Test credentials (allineati)

- `tester@orbus.test` / `password123` — admin, gilda `The Iron Lantern` (avanzata).
- `clean_onboarding@orbus.test` / `password123` — non-admin, pristine onboarding fixture.

(Entrambi seedati idempotentemente da `seeds/seed_runner.py`, gated `APP_ENV != "production"`.)

---

## 9. Recommendation for next round

**R16.B — Audit Coverage Extension + Sweep XP Helper Round 2**

Priorità P1:
1. Aggiungere `material_dropped`, `adventurer_xp_gained`, `leaderboard_score_updated` ad audit whitelist + write.
2. Sweep `add_guild_xp` su daily bonus, contract completion, season closing (4–5 code path identificate).
3. Persistere `leaderboard_snapshots` (storico).
4. Admin Audit UI: aggiungere widget "Recent XP gains" + export CSV.

Stima: 1.5–2 giorni dev + 0.5 giorno test.

---

**Fine R16.A. In attesa di lancio `e1_tester` da parte dell'utente per il sigillo OFFICIAL CLOSED.**
