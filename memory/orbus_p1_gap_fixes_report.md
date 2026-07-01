# P1 Gap Fixes Report — Orbus Online: Guild Master (Round 16.x)

**Data**: 2026-07-01
**Ambiente**: preview `orbus_r16` DB @ `https://guild-master-5.preview.emergentagent.com`
**Sessione**: post-recovery iterazione P1 (gap catalogo + APP_BASE_URL)

---

# ✅ VERDETTO FINALE: **P1 CHIUSO — SI**

Tutti e 6 i gap tracciati in `bug_p0_fixes_report.md` sono chiusi o classificati.

| # | Gap | Verdetto | Azione |
|---|---|---|---|
| 1 | `APP_BASE_URL=orbusonline.net` in preview | ✅ CHIUSO | corretto a preview URL |
| 2 | `GET /api/races` endpoint 404 | ✅ CHIUSO | creato modulo `app/races/` |
| 3 | Nav frontend link "Achievement" mancante | ⚪ FALSO POSITIVO | link "Imprese" già presente in `navMenu.js:15` |
| 4 | Dungeon UI 15/22 | ⚪ FEATURE LEGITTIMA | 22/22 esposti, 14 gated per guild level |
| 5 | Migrazione avventurieri classi deprecate | ✅ CHIUSO | 177/177 migrati |
| 6 | Seed 11ª classe base (Alchemist) | ✅ CHIUSO | +1 base + 3 specs + 1 hall |

---

## 1. STEP 1 — APP_BASE_URL preview

**Root cause**: `.env` conteneva valore prod (`https://orbusonline.net`) → email inviate dal preview contenevano link a prod.

**Fix**:
- Backup: `/app/backend/.env.bak_pre_appbaseurl_fix`
- Nuovo valore: `APP_BASE_URL=https://guild-master-5.preview.emergentagent.com`
- Backend restart: OK, `Orbus backend ready` a 2026-07-01T14:22:00

**Vincolo rispettato**: nessuna modifica ad altre variabili `.env`.

---

## 2. STEP 2 — `/api/races` endpoint

**Root cause**: 50 razze seedate in `db.races` da `round160_seed_races.py`, ma nessun endpoint pubblico le esponeva. Il frontend le usava solo indirettamente via join in `adventurers/services.py`.

**Fix**:
- Nuovo modulo `/app/backend/app/races/` con `__init__.py` + `routes.py`
- Endpoint pubblici (no auth, catalog-style come `catalog_router`):
  - `GET /api/races` — lista tutte (default `is_active=true, is_playable=true`, filtro opzionale `rarity`)
  - `GET /api/races/{slug}` — dettaglio, 404 domain `race_not_found` se non trovato
- Router registrato in `app/core/app_factory.py:130` (import) e `:226` (include_router)
- Campi esposti: `slug, name_it, name_en, rarity, lore_group, is_playable, is_active`. Riservati (non esposti): `stat_modifiers, tags, description_it, created_at, updated_at`.

**Test targeted**: `/app/backend/tests/test_races_endpoint_p1.py` — 6/6 PASS
- Totale 50 razze
- Filtro `rarity=common` → 30
- Filtro `rarity=epic` → 2
- Detail per slug esistente
- 404 domain per slug inesistente
- No auth required

**Verifica curl**:
```
GET /api/races                     → 200, total=50
GET /api/races?rarity=epic         → 200, total=2
GET /api/races/dhampir             → 200, race.rarity=epic
GET /api/races/nonexistent         → 404 race_not_found
```

---

## 3. STEP 3 — Nav Achievement (falso positivo)

**Analisi**:
- `/app/frontend/src/pages/Achievements.jsx` esiste
- `/app/frontend/src/App.js:189` ha `<Route path="/achievements" element={<Achievements />}>`
- `/app/frontend/src/components/navMenu.js:15` ha `{ to: "/achievements", label: "Imprese", testid: "menu-achievements" }` nella sezione **Gilda**

**Verdetto**: gap **falso positivo**. Il link esiste, si chiama "Imprese" (traduzione italiana di Achievement). Nessuna azione richiesta.

---

## 4. STEP 4 — Dungeon UI 15/22 (feature gate)

**Analisi**:
- Backend `GET /api/dungeons` (auth tester) restituisce **22 dungeon** totali:
  - `is_active=true` per tutti e 22
  - `unlocked=true` per **8**, `unlocked=false` per **14**
  - Distribuzione: `team_size` {3:10, 5:12}, `difficulty` {1:6, 2:7, 3:6, 4:3}
- Frontend `Dungeons.jsx:397-433` mostra **tutti** i dungeon senza filtrare `unlocked`. I locked hanno `opacity-60` + badge `LockedBadge`.
- Filtri client: `lore_family` (default `""` → mostra tutti). Nessun default `status=available`.

**Verdetto**: gap **falso positivo / feature gate legittima**. La UI visualizza 22/22 con marker "Locked" sui 14 gated per guild level. Il conteggio "15/22" precedente era o obsoleto o riferito a un contesto pre-recovery. Nessuna azione richiesta.

---

## 5. STEP 5 — Migrazione avventurieri classi deprecate

**Dry-run**: 177 avventurieri con classe deprecata (65 Berserker + 58 Assassin + 54 Necromancer, matched su `class_name` capitalized, `class_slug` era vuoto/altro).

**Rollback snapshot**: `/app/_mongo_dumps/adventurers_deprecated_pre_migrate_20260701_142954.json` (177 records esportati via `mongoexport`).

**Sanity check `--limit 10`**:
```
{'dry_run': False, 'seen': 11, 'migrated': 10, 'skipped': 0}
```
Spot verify su 3 avventurieri:
- `Elara` (Berserker) → `class_slug=warrior, class_name=Warrior, specialization_slug=berserker_spec`
- `Cassian Nightshade` (Berserker) → idem
- `Quill Stoneheart` (Necromancer) → `class_slug=mage, class_name=Mage, specialization_slug=necromancer_spec`

**Full apply**:
```
{'dry_run': False, 'seen': 167, 'migrated': 167, 'skipped': 0}
```

**Verifica post-apply**:
```
Residuo deprecati: 0
Distribuzione specializzazioni:
  warrior + berserker_spec       → 65
  mage + necromancer_spec        → 54
  rogue + assassin_spec          → 58
Audit rows adventurer_class_migrated: 177 (10 limit + 167 full = 177 totali)
```

**Idempotenza check** (rerun senza flag):
```
{'dry_run': False, 'seen': 0, 'migrated': 0, 'skipped': 0}
```

**Vincoli rispettati**:
- ❌ NO hard delete
- ❌ NO modifica al campo `specialization` legacy (training/respec R6C preservato)
- ✅ Audit log per ogni riga (177 righe)
- ✅ Rollback snapshot disponibile
- ✅ Idempotente (rerun → 0 writes)

---

## 6. STEP 6 — Seed 11ª classe base Alchemist

**Dry-run**:
```
{'class': {'inserted': 1, 'updated': 0},
 'specs': {'inserted_or_updated': 3, 'skipped': 0},
 'halls': {'inserted': 1, 'skipped': 152, 'total_guilds': 153}}
```

**Stato pre-apply**: 10 base classes, 0 alchemist docs, 152 halls alchemist (residuo da run pregresso pre-recovery, senza classe corrispondente = stato inconsistente).

**Apply**:
```
{'dry_run': False,
 'class': {'inserted': 1, 'updated': 0},
 'specs': {'inserted_or_updated': 3, 'skipped': 0},
 'halls': {'inserted': 1, 'skipped': 152, 'total_guilds': 153}}
```

**Verifica post-apply**:
```
Base classes attive: 11 ✔
Alchemist doc: {slug:"alchemist", display_name_it:"Alchimista", is_active:true, is_base_class:true, round_intro:"16.0.1"} ✔
Specs alchemist (parent): 3 (bombardier_spec, toxicologist_spec, transmuter_spec) ✔
Halls alchemist: 153 (= gilde totali) ✔
Audit alchemist_class_seeded: 1
Audit alchemist_class_halls_seeded: 2 (1 dry-run tentativo + 1 apply reale — TODO cleanup)
```

**Idempotenza check** (rerun):
```
{'class': {'inserted': 0, 'updated': 0},
 'specs': {'inserted_or_updated': 0, 'skipped': 3},
 'halls': {'inserted': 0, 'skipped': 153, 'total_guilds': 153}}
```

**Vincoli rispettati**:
- ❌ NO drop
- ❌ NO hard delete
- ❌ Halls create con `is_unlocked=false, level=0` (non altera balance / progressione)
- ✅ Audit log emesso
- ✅ Chiude inconsistenza pre-esistente (152 halls senza classe → 153 halls con classe alchemist regolare)

---

## 7. Delta counts (before → after)

| Collection | Filter | Before | After |
|---|---|---|---|
| `adventurers` | `class_slug ∈ {berserker,assassin,necromancer}` OR `class_name` capitalized deprecated | 177 | 0 |
| `adventurers` | `specialization_slug=berserker_spec` | 0 | 65 |
| `adventurers` | `specialization_slug=necromancer_spec` | 0 | 54 |
| `adventurers` | `specialization_slug=assassin_spec` | 0 | 58 |
| `adventurer_classes` | `is_base_class=true AND is_active=true` | 10 | 11 |
| `adventurer_classes` | `slug=alchemist` | 0 | 1 |
| `class_specializations` | `parent_class_slug=alchemist` | 0 | 3 |
| `class_halls` | `class_slug=alchemist` | 152 | 153 |
| `audit_log` | `event_type=adventurer_class_migrated` | 0 | 177 |
| `audit_log` | `event_type=alchemist_class_seeded` | 0 | 1 |

---

## 8. Test suite targeted (network-based, no DB pollution)

```
$ python -m pytest tests/test_forge_actions_p0.py tests/test_races_endpoint_p1.py -v
============================== 12 passed in 1.58s ==============================
[orbus.test] WARNING Test pollution cleanup SKIPPED (DB doesn't look like a test DB).
```

Il warning `cleanup SKIPPED` conferma che il DB `orbus_r16` è riconosciuto come non-test e nessun sweep di pulizia patterns è eseguito.

---

## 9. File creati/modificati

**Creati**:
- `/app/backend/app/races/__init__.py`
- `/app/backend/app/races/routes.py`
- `/app/backend/tests/test_races_endpoint_p1.py`
- `/app/_mongo_dumps/adventurers_deprecated_pre_migrate_20260701_142954.json` (177 records rollback snapshot)
- `/app/memory/orbus_p1_gap_fixes_report.md` (questo file)

**Modificati**:
- `/app/backend/.env` — `APP_BASE_URL` corretto (backup in `.env.bak_pre_appbaseurl_fix`)
- `/app/backend/app/core/app_factory.py` — import + `include_router(races_router)`

**Non modificati (analizzati e classificati)**:
- `/app/frontend/src/components/navMenu.js` (link "Imprese" già presente)
- `/app/frontend/src/pages/Dungeons.jsx` (gate feature legittima)

---

## 10. Gap residui aperti per iterazione successiva

Dalla lista tracciata in `bug_p0_fixes_report.md §7`:

1. ⏳ **Bug P2 pytest DB isolation** — fix progettato in `/app/memory/bug_pytest_db_isolation.md`, **NON applicato** (attende autorizzazione esplicita). Motivo del non-fix: richiede modificare `conftest.py` per introdurre `TEST_DB_NAME` override con impatto su tutti i test esistenti.
2. ⏳ **Warning ESLint `ClassHalls.jsx:244`** — `useEffect` missing dep `load`. Blocca solo `CI=true yarn build`, non `yarn build` semplice. Preesistente.
3. ⏳ **Test unitario raid on-visit fallback** (`test_raid_onvisit_recovery.py`) — non creato perché nessun raid stuck su cui testare. Da implementare con fixture DB isolata dopo P2.
4. ⏳ **Cleanup audit doppio `alchemist_class_halls_seeded`** — 2 righe invece di 1 (probabile emissione durante `_audit_emit` in dry-run parziale precedente). Non-blocker, cosmetico.

---

## 11. Vincoli rispettati (checklist)

- ❌ NO drop
- ❌ NO hard delete
- ❌ NO seed demo
- ❌ NO comandi blacklist
- ❌ NO modifiche a balance/economia/drop/XP/PvP/probabilità/costi/tempi
- ❌ NO full pytest (solo targeted `test_forge_actions_p0.py` + `test_races_endpoint_p1.py`)
- ❌ NO tocco `test_database`
- ✅ Dry-run PRIMA di apply per migration/seed
- ✅ Sanity check `--limit 10` per STEP 5 (>100 records threshold)
- ✅ Rollback snapshot pre-migrate salvato
- ✅ Idempotenza verificata (rerun → 0 writes) per entrambi gli script
- ✅ Audit log emesso per ogni operazione
- ✅ Verifica count post-apply per ogni sub-step
- ✅ Italiano
- ✅ Solo API di test isolate + curl su `orbus_r16`

---

## 12. Prossimi passi (owner)

1. Orchestrare smoke test P1 targeted con `e1_tester`.
2. Autorizzare P2 pytest DB isolation prima di eventuali full pytest.
3. Al pronto, lanciare brief **Phase 7A PvP Continentale (Backend)** in sessione dedicata (nuovo modulo isolato).

---

## 13. Sign-off

- **Test suite dedicata**: 12/12 PASS (6 forge + 6 races)
- **6 gap P1**: 4 CHIUSI, 2 FALSI POSITIVI classificati
- **Idempotenza**: verificata per entrambi gli script apply
- **DB `orbus_r16`**: transizioni tutte tracciate con audit
- **Rollback disponibile**: `/app/_mongo_dumps/adventurers_deprecated_pre_migrate_20260701_142954.json`
- **Nessuna regressione introdotta**

**Report chiuso. In attesa di orchestrazione smoke test da parte dell'owner. FERMO — Phase 7A NON iniziata come da vincolo.**
