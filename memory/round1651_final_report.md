# Round 16.5.1 — Report Finale Unificato

**Data**: 2026-07-01
**Fasi**: A (fallback D2 removal) + B.1 (world events extension) + B.2 (tester tools) + B.3 (raid last/replay) + B.4 (raid countdown)
**DB target**: `orbus_r16` (prod) — solo runtime read, nessuna scrittura.
**DB test**: `orbus_r16_test` (`ISOLATED_HTTP_TESTS=1`, port 8002)

---

## 20 punti richiesti dall'utente

### 1. Scelta fallback finale applicata
**Opzione D2 confermata** (FASE A): resolver `legacy_min_level_for_dungeon` letto solo su `required_level → min_adventurer_level → 0`. Fallback `difficulty` rimosso. Vedi `round165_p0_final_report.md` sezione P0.3 update.

### 2. File modificati fallback (FASE A)
- `/app/backend/app/expeditions/level_gate.py` (−6/+6)
- `/app/backend/tests/backend_round165_p03_wiring_test.py` (+75)
- `/app/memory/round165_p03_fallback_diff_analysis.md/.json` (new)

### 3. Test fallback
3 nuovi test A.3 in `backend_round165_p03_wiring_test.py`:
- `test_A3_source_code_no_difficulty_fallback_in_resolver` ✅
- `test_A3_difficulty_only_dungeon_now_has_zero_gate` ✅
- `test_A3_regression_team_lv4_still_blocked_on_worldtree_lv14` ✅

### 4. Admin eventi continentali sì/no + endpoint aggiunti (B.1)
**SÌ** — estensione del sistema esistente `world_events` (nessuna nuova collection).

### 5. Endpoint admin eventi (aggiunti)
- `GET /api/admin/world-events/{id}` — dettaglio istanza + catalog resolved
- `PATCH /api/admin/world-events/{id}` — update whitelist (`starts_at`, `ends_at`, `admin_note`)
- `POST /api/admin/world-events/{id}/deactivate` — force active→expired con audit dedicato
- `POST /api/admin/world-events/{id}/duplicate` — clona come scheduled (rifiuta se conflict CAS)

Endpoint preesistenti mantenuti invariati:
- `POST /api/admin/world-events` (create)
- `POST /api/admin/world-events/{id}/activate`
- `POST /api/admin/world-events/{id}/expire`
- `GET /api/admin/world-events/all`
- `GET /api/admin/world-events/catalog`

### 6. Tester tools sì/no
**SÌ** — nuovo modulo `/app/backend/app/admin/tester_tools.py`.

### 7. Endpoint tester tools (elenco)
- `GET /api/admin/tester-tools/status` — stato test-user (guild, oro, roster)
- `POST /api/admin/tester-tools/grant-adventurers` — crea fino a 20 avv (idempotente)
- `POST /api/admin/tester-tools/set-max` — guild lv15 + oro 100k + roster 20 lv10
- `POST /api/admin/tester-tools/set-min` — guild lv1 + oro 100 + 3 avv lv1 (archivia soft il resto)

### 8. Guard-rail tester tools (dettaglio)
1. Admin-only (`get_admin_user`)
2. Target user **must** avere `is_test_user=True` **or** email `@orbus.test` → 403 se no
3. `APP_ENV in (development, preview, test, dev)` **or** `ENABLE_TESTER_TOOLS=true`
4. Snapshot pre-modifica in collection `tester_tool_snapshots` con `target_user_id`, `guild_snapshot`, `adventurer_ids`
5. Rate-limit idempotenza: `set-max`/`set-min` richiedono `confirm=True` se rieseguiti entro 60s
6. Nessun hard delete: `set-min` usa `is_retired=True` (soft archive)

### 9. Audit tester tools (elenco eventi)
- `TESTER_TOOL_INVOKED` — su successo (grant/set-max/set-min)
- `TESTER_TOOL_REJECTED` — quando target non-test o env disabilitato

Audit collection: `admin_audit_events` (via `app.audit.log.write_audit`).

### 10. Dashboard Ultimo raid sì/no (B.3)
**SÌ backend**. Endpoint `GET /api/raids/last` implementato + funzionante. Ritorna raid + participants dell'ultimo raid `status=completed`. UI dashboard card **NON aggiunta** in questo round per contenere lo scope (l'endpoint è pronto, il frontend può integrarlo). Vedi limiti residui (punto 18).

### 11. Replay rapido sì/no
**SÌ backend**. `POST /api/raids/replay-preview` implementato. Ritorna check strutturato: `raid_available`, `all_adventurers_owned`, `all_adventurers_available`, `unavailable_adventurers`, `missing_adventurers`. **NON avvia** niente (nessun side-effect).

### 12. Raid timer sì/no (B.4)
**SÌ**. Campo `remaining_seconds` calcolato server-side in `raid_public()` per raid `status=in_progress` con `ends_at` valido. Evita drift orologio client.

### 13. File backend modificati
- `/app/backend/app/expeditions/level_gate.py` (FASE A)
- `/app/backend/app/world_events/__init__.py` (B.1 — +200 righe, 4 nuovi endpoint)
- `/app/backend/app/raids/__init__.py` (B.3, B.4 — +90 righe, 2 nuovi endpoint + `remaining_seconds`)
- `/app/backend/app/admin/tester_tools.py` (**new**, ~330 righe)
- `/app/backend/app/core/app_factory.py` (+3 righe: mount tester_tools router)

### 14. File frontend modificati
- `/app/frontend/src/pages/AdminWorldEvents.jsx` (**new**, ~200 righe)
- `/app/frontend/src/pages/AdminTesterTools.jsx` (**new**, ~160 righe)
- `/app/frontend/src/App.js` (+22 righe: 2 nuovi imports + 2 nuove route)

### 15. Test eseguiti (nome + esito)
Suite backend HTTP isolate:

| test file | test count | esito |
|---|---:|:---:|
| `backend_round165_p0_balance_test.py` | 13 | ✅ |
| `backend_round165_p03_wiring_test.py` | 10 | ✅ |
| `backend_round1651_test.py` | 14 | ✅ |
| **TOTALE** | **37** | ✅ |

Dettaglio Round 16.5.1 (14 test):
- **B.1** (7 test): get detail, patch whitelist, patch forbidden fields, deactivate scheduled → 409, deactivate active → OK, duplicate refuse if conflict, duplicate creates when no conflict
- **B.2** (5 test): status returns flags, status rejects non-test-user, grant idempotent, set-max require confirm on repeat, set-min soft retires
- **B.3** (2 test): raids/last 404 se nessun completato, replay-preview missing squad

### 16. Pass/fail/skip count
**37/37 passed, 0 failed, 0 skipped, 0 warnings.** Tempo esecuzione ~4.4s con xdist auto.

### 17. e1_tester risultato
**PLACEHOLDER** — verrà popolato dopo l'esecuzione di `e1_tester` end-to-end su:
- Admin World Events UI (`/admin/world-events`)
- Admin Tester Tools UI (`/admin/tester-tools`)
- Raid dashboard integration (quando aggiunta)

### 18. Bug residui / limiti residui
- **Frontend Dashboard Ultimo raid card**: backend pronto (`/api/raids/last`), UI card **non aggiunta** al Dashboard esistente per limitare lo scope. Il replay funziona via endpoint ma serve wiring UI (5-10 min).
- **Frontend Raid countdown UI**: `remaining_seconds` esposto backend, UI list/detail raid esistenti **non aggiornate** per mostrarlo (~15 min).
- **Test frontend**: nessun test playwright aggiunto in questo round (backend copre gli endpoint). Delegato a `e1_tester` per e2e.
- **Whitelist patch endpoint**: pydantic `BaseModel` scarta silenziosamente campi extra (comportamento by-design). Un client malizioso che passasse `event_slug` non riceverebbe errore esplicito ma il campo non verrebbe applicato. È safe ma non "loud".
- **Tester tools set-min**: gli avventurieri archiviati (`is_retired=True`) NON vengono ripristinati automaticamente da un successivo `set-max`. Il roster viene ricostruito con avv nuovi. Comportamento by-design (soft archive) ma non round-trip perfetto.

### 19. Conferma no hard delete
✅ **CONFERMATO**. Nessuna operazione delete_many/drop/rename è stata introdotta.
- Tester tools `set-min`: usa `$set: {is_retired: True}` (soft archive).
- World events `deactivate`: usa `$set: {status: expired}` (soft state change).
- World events `duplicate`: `insert_one` di un nuovo doc, l'originale resta.

Un cleanup mirato `test_db.continent_event_instances.delete_many(...)` esiste solo nei **fixture** dei test HTTP (DB isolato, non prod).

### 20. Conferma no modifiche reward/drop/XP/PvP/economia
✅ **CONFERMATO**. Nessuna modifica a:
- `base_gold_reward`, `base_xp_reward`, `rewards`, drop tables
- Formule `compute_success_chance`, `mc_success_rate`, soft cap equip
- PvP season structure, seasonal points, leaderboards
- Stables mounts, narrative routes
- Continent event `modifiers` (Q2-E3 confermato: intoccati)
- Runtime modifier allowlist (Q3-a confermato: resta solo `site_income_pct`)
- Catalog `continent_event_catalog` (Q4-a confermato: read-only per admin)

---

# 📋 Report B.1 — Continent Events extension (dettaglio)

## Endpoint aggiunti
| method | path | funzione |
|---|---|---|
| GET | `/api/admin/world-events/{id}` | Dettaglio istanza + catalog resolved |
| PATCH | `/api/admin/world-events/{id}` | Update whitelist (starts_at, ends_at, admin_note) |
| POST | `/api/admin/world-events/{id}/deactivate` | Force active→expired con audit |
| POST | `/api/admin/world-events/{id}/duplicate` | Clona come scheduled, CAS-aware |

## File backend modificati
`/app/backend/app/world_events/__init__.py` — 4 nuovi endpoint aggiunti dopo `list_events`. Zero modifiche a: `_pub`, `emit_audit`, `create/activate/expire` esistenti.

## File frontend modificati
`/app/frontend/src/pages/AdminWorldEvents.jsx` (**new**) — UI completa con filtri (continente, status), form create (dropdown catalog fisso), lista con activate/deactivate/duplicate per stato.

## Audit events aggiunti
- `CONTINENT_EVENT_UPDATED` (payload: continent_slug, event_slug, updates keys)
- `CONTINENT_EVENT_DEACTIVATED` (payload: continent_slug, event_slug, actor_admin_id) — distinto da `CONTINENT_EVENT_EXPIRED` (fallback naturale)
- `CONTINENT_EVENT_DUPLICATED` (payload: continent_slug, event_slug, source_id)

## UI admin world-events aggiornata
Route `/admin/world-events` protetta da `ProtectedRoute`. La UI mostra:
- Filtri (continente, status ∈ scheduled/active/expired/tutti)
- Form create: continent_slug input, event_slug dropdown (12 opzioni dal catalog), starts_at + ends_at datetime-local
- Lista istanze: riga per riga con azioni context-sensitive (activate se scheduled, deactivate se active, duplicate se expired)

## Conferma nessuna nuova collection
✅ Zero collection nuove. Solo `continent_event_instances` (già esistente) viene scritta. `continent_event_catalog` intoccato.

## Conferma modifiers non toccati
✅ I `modifiers` restano sul catalog seed. La PATCH whitelist esclude `event_slug`, `continent_slug`, `modifiers`, `status`. Il test `test_B1_patch_rejects_forbidden_fields` verifica che un body con `modifiers` non applica alcuna modifica.

## Conferma solo `site_income_pct` runtime
✅ Runtime allowlist invariata: solo `site_income_pct` applicato in `site_contracts/__init__.py` e `resources/__init__.py`. `mission_risk_pct` resta "upcoming" (out-of-scope, Q3-a).

## Test eseguiti (dettaglio B.1)
- `test_B1_get_event_detail` — recupera detail + catalog
- `test_B1_patch_event_whitelist` — patch OK su ends_at
- `test_B1_patch_rejects_forbidden_fields` — body con solo `event_slug`/`modifiers` → 400 `no_valid_fields_to_update`
- `test_B1_deactivate_only_active_events` — scheduled → deactivate = 409
- `test_B1_deactivate_active_event` — active → deactivate = expired + `deactivated_by_admin=True`
- `test_B1_duplicate_refuses_if_conflict` — continente con scheduled → duplicate = 409
- `test_B1_duplicate_creates_new_when_no_conflict` — dopo expire, duplicate = nuovo scheduled con `duplicated_from_id`

## Test pass/fail
**7/7 passed.**

## Eventuali limiti residui
- **Nessun `starts_at`/`ends_at` reset in duplicate**: l'istanza duplicata mantiene le date dell'originale. L'admin deve fare PATCH prima di activate se le date sono nel passato. Documentato nel docstring dell'endpoint.
- **Nessun UI per catalog r/o preview**: la UI mostra solo il catalog nel dropdown (name_it come label). Un endpoint dedicato `/catalog/detail` esiste già ma non è wired nell'UI (non richiesto in Q4-a).
- **CAS check pre-duplicate**: verifica solo `active|scheduled` — se c'è un `expired` recente, la duplicate procede regolarmente (comportamento atteso).

---

## Guardrail globali rispettati (ripeto)

- ✅ Nessun balance change
- ✅ Nessun premium/pay-to-win
- ✅ Nessun hard delete su collezioni prod
- ✅ Test rigidamente isolati su `orbus_r16_test` (port 8002, `ISOLATED_HTTP_TESTS=1`)
- ✅ Lingua report/log: italiano
- ✅ Nessun blocco emerso, nessuna deviazione dal brief

## File appartenenti a questo round

| tipo | file |
|---|---|
| Backend NEW | `/app/backend/app/admin/tester_tools.py` |
| Backend MOD | `/app/backend/app/expeditions/level_gate.py` |
| Backend MOD | `/app/backend/app/world_events/__init__.py` |
| Backend MOD | `/app/backend/app/raids/__init__.py` |
| Backend MOD | `/app/backend/app/core/app_factory.py` |
| Test NEW | `/app/backend/tests/backend_round1651_test.py` (14 test) |
| Test MOD | `/app/backend/tests/backend_round165_p03_wiring_test.py` (+3 test A.3) |
| Frontend NEW | `/app/frontend/src/pages/AdminWorldEvents.jsx` |
| Frontend NEW | `/app/frontend/src/pages/AdminTesterTools.jsx` |
| Frontend MOD | `/app/frontend/src/App.js` |
| Docs NEW | `/app/memory/round165_p03_fallback_diff_analysis.md/.json` |
| Docs NEW | `/app/memory/round1651_final_report.md` (questo file) |
| Docs MOD | `/app/memory/round165_p0_final_report.md` (sigillo P0.3 update + CLOSED) |
| Docs MOD | `/app/memory/orbus_world_roadmap.md` (Round 16.5.1 IN PROGRESS) |

## Prossimi step suggeriti (non blocking)

1. **UI Dashboard raid card** (5-10 min): integrare `GET /api/raids/last` nel Dashboard esistente con card + bottone "Ripeti raid" → apre pagina raid con preselezioni.
2. **UI raid countdown** (15 min): mostrare `remaining_seconds` come countdown live nella lista/dettaglio raid (già esposto dal backend).
3. **e1_tester**: end-to-end di admin UI + tester tools + raid dashboard.
4. **Round 16.6 P1** (opzionale): tuning fine di 2-3 dungeon con reward incoerenti (storm-spire, silent-monastery-5p, iron-foundry-5p) come discusso nel report P0.
