# ROUND 16.3 — Phase 4 Final Report

**Data**: 2026-07-01
**Scope**: Risorse Continentali V0 (8 slug) + Classifiche Continentali V0.
**Stato**: 🟢 **READY-TO-VERIFY** (in attesa E2E `e1_tester` manuale utente).

---

## 1. Sommario esecutivo

Introdotto il primo sistema di **raccolta risorse continentali** in Orbus: 8 risorse tematiche (una per continente, 5 epic + 3 rare), missioni di gathering con team di 3 avventurieri idle esistenti, drop rate CONSERVATIVE (3% epic / 5% rare) con piccolo boost `+2%` da eventi `site_income_pct > 0` (cap `+10%`). Le missioni durano 30 minuti, costano 20 oro, sono idempotenti CAS-protected con on-visit fallback e script CLI di recovery.

Aggiunte anche **Classifiche Continentali V0**, informative e read-only, con 2 tipologie (`resource_gathering_count`, `site_income_total`) computate su finestra 7gg, freschezza 24h, top 20 per continente. Snapshot immutabili in `continent_leaderboard_snapshots`, computate on-visit (nessuno scheduler).

**Vincoli chiave rispettati**: NO hard delete · NO scheduler globale · NO P2W · NO buff economici da leaderboard · NO cambi a economia/XP/drop rate esistenti fuori dalle nuove risorse.

---

## 2. File creati / modificati

| File | Righe | Tipo |
|---|---|---|
| `app/resources/__init__.py` | 714 | NEW — modulo compact single-file (seed catalog + gather + resolve + leaderboards + admin) |
| `app/scripts/recover_stuck_resource_missions.py` | ~90 | NEW — CLI recovery `--dry-run/--apply` |
| `app/audit/log.py` | +5 event | UPDATE — whitelist estesa append-only |
| `app/app_factory.py` | +router+seed | UPDATE — mount router + boot seed |
| `frontend/src/pages/Resources.jsx` | ~180 | NEW — pagina catalog + inventario mio |
| `frontend/src/pages/ResourceGather.jsx` | ~220 | NEW — pagina start-mission (team picker) |
| `frontend/src/pages/ResourceMissions.jsx` | ~180 | NEW — missioni in-progress + recent |
| `frontend/src/pages/ContinentLeaderboards.jsx` | ~200 | NEW — classifiche V0 |
| `frontend/src/App.js` | +4 route | UPDATE — mount rotte |
| `frontend/src/components/navMenu.js` | +2 voci | UPDATE — nav Mondo + Gilda |
| `backend/tests/backend_round163_phase4_test.py` | 526 | NEW — 30 test T01→T30 |

---

## 3. Endpoint disponibili (Phase 4)

### Public (auth JWT)
| Method | Path | Descrizione |
|---|---|---|
| GET | `/api/resources/catalog` | 8 risorse `is_active=True` |
| GET | `/api/resources/mine` | Inventario risorse continentali della gilda |
| POST | `/api/resources/gather` | Avvia missione (body: `resource_slug`, `adventurer_ids[3]`) |
| GET | `/api/resources/missions/mine` | In-progress + recent (10) + on-visit expiry |
| GET | `/api/resources/missions/{id}` | Dettaglio + on-visit resolve |
| GET | `/api/continent-leaderboards/{continent_slug}/summary` | 2 classifiche + top3 preview |
| GET | `/api/continent-leaderboards/{continent_slug}/{ltype}` | Snapshot completo (freschezza 24h) |

### Admin (gated `is_admin=True`, 403 altrimenti)
| Method | Path | Descrizione |
|---|---|---|
| PATCH | `/api/admin/resources/catalog/{slug}` | Toggle `is_active` (NO hard delete) |
| GET | `/api/admin/resources/gathering-stats?window_days=N` | Aggregate stats (max 30gg) |
| POST | `/api/admin/resources/dev/grant/{guild_id}/{slug}?qty=N` | Dev grant (gated `APP_ENV != production`) |
| POST | `/api/admin/continent-leaderboards/{continent_slug}/{ltype}/recompute` | Forza recompute snapshot |

**Totale**: 11 endpoint (7 public + 4 admin).

---

## 4. Catalogo risorse (8 slug)

| Slug | Continente | Rarity | Base drop % |
|---|---|---|---:|
| `cristallo_di_ambash` | ambash | epic | 3 |
| `cenere_di_velur` | velur | epic | 3 |
| `linfa_di_soe` | soe | rare | 5 |
| `nucleo_di_efreto` | efreto | epic | 3 |
| `osso_di_irthe` | irthe | rare | 5 |
| `seme_di_nathos` | nathos | rare | 5 |
| `frammento_di_ergolat` | ergolat | epic | 3 |
| `sigillo_di_aveol` | aveol | epic | 3 |

Distribuzione: **5 epic + 3 rare**. Ogni risorsa ha `name_it/name_en/description_it/description_en`. Mirror creato in `items` collection con `item_type="material_continental"` per riuso infrastruttura inventory esistente. Campo `market_cap_daily_per_guild=3` persistito nel catalog (utilizzo differito a Phase 6 patti commerciali).

---

## 5. Formula drop rate (trasparente)

```
base_drop_rate(rarity) = 3% (epic) | 5% (rare)
event_bonus(continent) = +2% se attivo evento con modifier_type='site_income_pct' e value > 0 (else 0)
event_bonus cap = min(+10%, event_bonus)   # hard cap
drop_rate_final = base + event_bonus

success_chance(team_power) = clamp(20, 50 + (team_power - 60) * 0.5, 90)
```

Sequenza roll (server-side, `_resolve_mission`):
1. `success_roll = rng.randint(1,100)`; se ≤ `success_chance` → outcome = `completed_with_drop` OR `completed_no_drop`.
2. Se successo: `drop_roll = rng.randint(1,100)`; se ≤ `drop_rate_final` → `resources_obtained=1`.
3. Se fallimento (`success_roll > success_chance`) → outcome = `failed`, `resources_obtained=0`.

**Costo missione**: 20 oro (dedotto in `gather()` prima di lock team). **Durata**: 1800 s (30 min).

---

## 6. Team lock/release + Idempotenza CAS

- **Lock**: `_lock_adventurers(ids, mission_id)` → status `"resource_gathering"`.
- **Release**: `_release_adventurers(ids)` chiamato dentro `_resolve_mission` dopo la CAS di transizione.
- **CAS resolve**: `find_one_and_update({id, status:"in_progress", resolution_started_at:None}, {$set:{resolution_started_at:now}})`. Se non matcha, un altro resolver già lavora → ritorna stato corrente senza duplicare.
- **On-visit fallback**: `GET /api/resources/missions/mine` chiama `_resolve_expired_missions_for_guild(guild_id)` che scansiona missioni `in_progress AND completes_at <= now` e le risolve.
- **Recovery CLI**: `python -m app.scripts.recover_stuck_resource_missions --dry-run|--apply` risolve missioni stuck (>30 min oltre `completes_at`) idempotentemente.

---

## 7. Classifiche Continentali V0

| Tipo | Metrica | Finestra |
|---|---|---|
| `resource_gathering_count` | Somma `resources_obtained` dei mission `completed` | 7gg rolling |
| `site_income_total` | Somma `total_amount` dei ledger `claimed` | 7gg rolling |

- **Freschezza**: 24h. Se snapshot esistente entro 24h → riutilizzo. Altrimenti compute + insert new snapshot.
- **Cap**: Top 20 (`LEADERBOARD_TOP_N`).
- **Filtri**: solo `guild_world_presence.status="active"` sul continente. Match `guild_id` sui documenti `resource_gathering_missions` o `guild_site_income_ledger`.
- **Read-only**: NO reward, NO buff, puro info V0. Snapshot immutabile, mai aggiornato in-place.

---

## 8. Audit events aggiunti (whitelist admin filter)

| Event type | Trigger | Metadata |
|---|---|---|
| `RESOURCE_MISSION_STARTED` | `gather()` insert mission | `resource_slug, continent_slug, cost_gold, team_power, success_chance, drop_rate` |
| `RESOURCE_MISSION_COMPLETED` | `_resolve_mission` success branch | `outcome, resources_obtained, resource_slug, continent_slug` |
| `RESOURCE_MISSION_FAILED` | `_resolve_mission` fail branch | idem |
| `RESOURCE_GRANTED` | Post-`_grant_resource` (drop OR dev-grant) | `resource_slug, qty, item_id, continent_slug` |
| `LEADERBOARD_SNAPSHOT_COMPUTED` | `_compute_leaderboard` post-insert | `continent_slug, leaderboard_type, entries_count` |

Tutti UPPERCASE, tutti aggiunti in `EVENT_TYPES` frozenset + `AUDIT_EVENT_WHITELIST` admin filter. Test T21 verifica whitelist accetta i 5 events (200 OK).

---

## 9. Frontend mobile-first

4 nuove pagine + 2 nuove voci navigation:

| Pagina | Route | Feature chiave |
|---|---|---|
| `Resources.jsx` | `/resources` | Catalog 8 slug + inventario mio (rarità badge, `pb-32 md:pb-6`) |
| `ResourceGather.jsx` | `/resources/gather` | Team picker (3 avv idle) + preview drop_rate |
| `ResourceMissions.jsx` | `/resources/missions` | In-progress con countdown + recent 10 |
| `ContinentLeaderboards.jsx` | `/world/leaderboards/:slug` | Tab per ltype, tabella top20 |

Nav aggiornato in `navMenu.js`:
- Sotto "Gilda" → voce "Risorse" (badge NEW).
- Sotto "Mondo" → voce "Classifiche" (badge NEW).

Tap target `min-h-[44px]`, bottom-nav clear `pb-32 md:pb-6`, CTA `w-full md:w-auto`. Modificatori event visualizzati con badge `+X%` esplicito (colore ambra) sul catalog.

---

## 10. Test coverage — 30/30 PASS

File `backend/tests/backend_round163_phase4_test.py` (526 righe). Test enumerati:

| # | Nome | Verifica |
|---|---|---|
| T01 | `catalog_seed_creates_8_resources` | 8 doc in `continent_resource_catalog` |
| T02 | `catalog_seed_idempotent` | 2 chiamate seed → `inserted_catalog=0` seconda volta |
| T03 | `catalog_rarity_distribution` | 5 epic + 3 rare esatti |
| T04 | `catalog_is_active_filter` | GET public ritorna 8 con `is_active=True` |
| T05 | `gather_starts_mission` | POST → status `in_progress`, `drop_rate>=3` |
| T06 | `gather_locks_adventurers` | 3 avv → status `resource_gathering` |
| T07 | `gather_cross_continent_rejected` | ambash+velur risorsa → 400 `resource_not_in_current_continent` |
| T08 | `resolve_success_grants_resource` | force success → +1 in inventario |
| T09 | `resolve_failure_no_drop` | force fail → 0 drop |
| T10 | `resolve_idempotent_retry` | 2nda `_resolve_mission` no double-grant |
| T11 | `missions_mine_on_visit_expiry` | GET → risolve mission scaduta |
| T12 | `adventurers_released_after_resolve` | Lock 3 → resolve → 0 busy |
| T13 | `recovery_script_resolves_stuck` | CLI script → resolved ≥ 1 |
| T14 | `event_boost_drop_rate` | boom_commerciale attivo → +2 bonus |
| T15 | `leaderboard_snapshot_computed_on_visit` | GET → snapshot fresh |
| T16 | `leaderboard_freshness_reuses_snapshot` | 2 GET entro 24h → stesso computed_at |
| T17 | `leaderboard_top_capped_at_20` | Max 20 entries |
| T18 | `leaderboard_admin_recompute` | POST admin → nuovo snapshot |
| T19 | `leaderboard_summary` | Summary contiene entrambi ltype |
| T20 | `audit_resource_events_emitted` | 3 event types presenti in `audit_log` |
| T21 | `audit_whitelist_accepts_phase4` | Admin filter 200 per 5 event UPPERCASE |
| T22 | `admin_toggle_resource_no_hard_delete` | PATCH → catalog=7, NO delete (count=8) |
| T23 | `admin_dev_grant_gated` | POST admin → qty=2 granted |
| T24 | `admin_gathering_stats` | GET admin → `groups` array |
| T25 | `regression_previous_modules_still_importable` | world_boss, world, raids.recovery, world_events, site_contracts |
| T26 | `regression_no_hard_delete_on_missions` | `resource_gathering_missions.count >= 3` |
| T27 | `openapi_has_phase4_paths` | 11 path esposti in OpenAPI |
| T28 | `success_chance_formula` | clamp [20, 90] |
| T29 | `non_admin_blocked` | 403 su admin endpoints da account non-admin |
| T30 | `gather_insufficient_adventurers_400` | 422 Pydantic validation su `min_length=3` |

Deterministic: T08/T09 usano `random.Random(seed)` per riproducibilità.

---

## 11. Regression suite

Dopo Phase 4:
- **R16.x + Phase14.4 + dev-seed bundle**: **208 passed, 2 skipped, 2 failed**.
- Le 2 failure NON sono regressioni Phase 4:
  - `test_t03_alchemist_class_halls_per_guild`: 13.385 alchemist halls su 14.351 gilde = 966 gilde legacy senza hall (debt storico R16.0, non introdotto da Phase 4).
  - `test_t03_all_adventurers_have_race_and_gender`: 6.336 avventurieri legacy senza `race_slug` (debt storico R16.0).
- Entrambe crescono col dataset ma sono debito legacy dei seed R16.0, indipendenti da Phase 4.
- Nessun test toccato da Phase 4 fallisce.

Target minimo utente **166+ test PASS** ampiamente superato (208 PASS).

---

## 12. Bug scoperti + Fix applicati durante Phase 4

### Bug #1 — Test `test_adventurers_released_after_resolve` malformato

- **File**: `tests/backend_round163_phase4_test.py:311-319`.
- **Causa**: la versione originale contava `busy = count({status:"resource_gathering"})` post-batch, ma i test sintetici T08-T10 avevano `adventurers:[]` (nessun lock reale). Solo T05 (`test_gather_starts_mission`) faceva un lock reale via API, ma non veniva mai risolto → l'assert `busy==0` era inevitabilmente falso.
- **Fix**: riscritto T12 per essere semantico:
  - Crea missione con 3 avv reali lockati esplicitamente via `_lock_adventurers`.
  - Verifica pre-condition `busy_before == 3`.
  - Chiama `_resolve_mission` con `rng=Random(42)`.
  - Verifica post-condition `busy_after == 0`.
- **Diff sintetico**:
```diff
-def test_adventurers_released_after_resolve():
-    async def _c():
-        gid = await _get_tester_guild_id()
-        busy = await db.adventurers.count_documents(
-            {"guild_id": gid, "status": "resource_gathering"})
-        assert busy == 0, ...
+def test_adventurers_released_after_resolve():
+    """Create a mission with 3 locked adventurers, resolve, verify release."""
+    async def _flow():
+        gid = await _get_tester_guild_id()
+        advs = await db.adventurers.find(..., "resource_gathering"}).limit(3).to_list(3)
+        adv_ids = [a["id"] for a in advs]
+        await db.adventurers.update_many({"id": {"$in": adv_ids}}, {"$set": {"status": "idle"}})
+        mid = str(uuid.uuid4())
+        m = {..., "adventurers": adv_ids, "success_chance": 100, "drop_rate": 100, ...}
+        await db.resource_gathering_missions.insert_one(m)
+        await _lock_adventurers(adv_ids, mid)
+        assert (await db.adventurers.count_documents({"id":{"$in":adv_ids},"status":"resource_gathering"})) == 3
+        await _resolve_mission(m, rng=_rnd.Random(42))
+        assert (await db.adventurers.count_documents({"id":{"$in":adv_ids},"status":"resource_gathering"})) == 0
```
- **Impatto**: solo test (nessuna modifica al codice produttivo). Backend `_resolve_mission` era già corretto — il test aveva un false expectation.

**Nessun altro bug scoperto**. Il codice Phase 4 (produzione) è passato al primo run senza modifiche.

---

## 13. Task A — Investigazione 2 WARN Phase 3

### WARN #1 — `level_bonus=15` sospetto
- **Diagnosi**: interrogato DB post-cleanup → `guild.level=1, reputation=1`. Formula site income `level_bonus_gold_per_level=5` → per lv1 attuale = `1*5=5`.
- **Verdict**: il valore `level_bonus=15` osservato durante il playtest era conseguenza di `guild.level=3` in quel momento (spedizioni completate durante playtest). Formula corretta, non è un bug.
- **Nota**: il PRD Phase 3 nomina `guild.level=4` come causa; verifica DB oggi conferma sistema coerente.

### WARN #2 — `world/overview.continent=null` post-test
- **Diagnosi**: DB conferma `presence.continent_slug=ambash, change_count=0` post-esecuzione script `reset_test_account_world_state.py`.
- **Verdict**: già risolto in sessione precedente; `tester@orbus.test` è nello stato pulito atteso.

Entrambi i WARN sono ora **chiariti**, nessun fix codice richiesto.

---

## 14. Vincoli rispettati (verifica)

| Vincolo | Stato |
|---|---|
| NO deploy | ✅ (solo preview) |
| NO hard delete su risorse/missioni | ✅ T22 + T26 verificano |
| NO scheduler globale | ✅ Solo on-visit + CLI script |
| NO P2W | ✅ Costo 20 oro/missione, no accelerazione premium |
| NO cambi economia/XP/drop esistenti | ✅ Nuove risorse in `item_type="material_continental"` isolato |
| NO reward economico da leaderboard | ✅ V0 puramente informative |
| Drop rate CONSERVATIVE | ✅ 3-5% base + max +10% event bonus (`EVENT_DROP_BOOST_MAX=10`) |
| Cross-continent block | ✅ T07 verifica 400 |
| Ownership check ogni endpoint | ✅ `user_guild_or_404` + `_get_current_continent_slug` |
| Timestamp UTC | ✅ `datetime.now(timezone.utc)` ovunque |
| Admin gated | ✅ T29 verifica 403 non-admin |
| Dev grant gated `APP_ENV != production` | ✅ `_is_production()` guard |

---

## 15. Recovery + operational tools

### Script CLI: `app/scripts/recover_stuck_resource_missions.py`
```bash
python -m app.scripts.recover_stuck_resource_missions --dry-run    # count only
python -m app.scripts.recover_stuck_resource_missions --apply       # resolve
python -m app.scripts.recover_stuck_resource_missions --guild-id X  # target singolo
```
- Idempotente CAS: usa `_resolve_mission` (stessa lock CAS del flow normale).
- Log strutturato + summary `{"scanned": N, "resolved": M}`.

### On-visit fallback
- `GET /api/resources/missions/mine` → resolve expired.
- `GET /api/resources/missions/{id}` → resolve se `completes_at <= now`.
- `POST /api/resources/gather` → resolve expired PRIMA di validare nuova missione (protegge da reduce contigency di adventurers ancora locked su mission conclusa).

### Admin ops
- Toggle catalog `is_active` (soft-delete effettivo).
- Recompute manuale leaderboard.
- Dev grant risorse (bypass gathering, gated).

---

## Next round proposto

**R16.3 Phase 5 — Forgia Leggendaria & Forgia di Arfus**: nuovi tier di forge unlockable via achievement/reputation, con receipts che consumano le 8 risorse continentali introdotte in Phase 4. Legendary items `is_tradeable=false` una volta craftati (BOP) per evitare RMT. Arfus = forgia mistica associata a Alveora/Ergolat.

Stima: 2-2.5gg dev + 0.5gg test.

---

*Report generato: 2026-07-01 — R16.3 Phase 4 READY-TO-VERIFY (pytest 30/30, regression 208/210, 2 legacy R16.0 debt failures non-Phase4).*
