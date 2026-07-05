# R18.Reset.2 — Final Closure Report (Fresh Start Banner UI/API)

**Round**: `R18.Reset.2` (Fresh Start Banner UI/API)
**Data closure**: 2026-07-05T16:04:00Z UTC (SEAL originale del test suite banner)
**Data compilazione report**: 2026-07-05T16:30:00Z UTC
**Autore**: e1_dev
**Stato**: 🔒 **CLOSED & SEALED**
**Seal authority**: PM Orchestrator
**Round precedente sigillato**: `R18.Reset.1b` + `R18.Reset.1b.hotfix.v1_3`

---

## Report 8 punti (as-per direttiva PM Messaggio 220)

### 1. `R18.Reset.2` — SEAL status

- **SEALED**: SÌ (contract lock documentale)
- **Timestamp UTC**: `2026-07-05T16:04:00Z` (banner header nel file di test)
- **File di test contract-locked**: `/app/backend/tests/backend_r18_reset2_banner_dismiss_test.py`
- **SHA256** (post-header seal): `c1b5bb74e4aeeed8a933df7900ce440cec190125937968567edd8666a52a8d2e`
- **Registry**: `/app/memory/r18_reset1b_hotfix_v1_3_seal_registry.json` sezione `contract_lock_tests.sealed_tests`
- **Modalità di enforcement**: **documentale** (header "CLOSED & SEALED" nel file di test) + **audit trail** (hash nel registry). Il test di integrity pre-esistente (`test_t01_sealed_scripts_untouched` nel file `backend_round1b_hotfix_v1_3_schema_compat_test.py`) **NON è stato modificato** per non alterare uno script già sigillato. Se una futura verifica lock-strict fosse richiesta, potrà essere creata come nuova sibling test-suite (mai in-place).
- **Header contract**:
  - SEAL AUTHORITY: PM Orchestrator
  - SEAL DATE (UTC): 2026-07-05T16:04:00Z
  - STATUS: CLOSED & SEALED (contract test lock)
  - Protegge endpoint contract per `POST /api/guilds/me/r18-reset-banner/dismiss` e `GET /api/guilds/me/r18-reset-banner`
  - Copre tenant isolation, idempotency, no-leak invariants, regression baseline post-hotfix v1_3

### 2. Verifica integrità pre-SEAL (baseline 8 sigilli R18.Reset.1b)

Eseguito prima di ogni modifica documentale:

```
cd /app/backend && python -m pytest tests/backend_round1b_hotfix_v1_3_schema_compat_test.py::test_t01_sealed_scripts_untouched -v
```

**Esito**: `1 passed in 0.41s` → **PASS**. Nessuno degli 8 sigilli R18.Reset.1b è stato alterato.

Registry integrity confermato:
- `round18_reset1b_apply.py` sha=`657d5853…d934` intatto
- `round18_reset1b_apply_v1_1.py` sha=`14d38bf8…1abd` intatto
- `round18_reset1b_apply_v1_2.py` sha=`d754c0dd…3f66` intatto
- `round18_reset1b_apply_v1_3.py` sha=`3737052166b0…4d88` intatto ✓
- `round18_reset1b_staged_backup_materialize.py` sha=`db426655…7dd9` intatto
- `round18_reset1c_field_cleanup.py` sha=`fe2d39bf…e052c` intatto
- `round18_reset1c_restore_from_jsonl_manifest.py` sha=`453b87c8…c3048` intatto
- `app/core/job_freeze.py` sha=`487c9223…11be` intatto

### 3. Endpoint & test coverage

**Endpoint implementati**:
- `POST /api/guilds/me/r18-reset-banner/dismiss` (auth-required, idempotent, tenant-isolated)
- `GET /api/guilds/me/r18-reset-banner` (auth-required, response `{show, dismissed, message_it}` con `message_it` byte-exact IT)
- `GET /api/guilds/me` esteso per esporre `r18_reset1b_banner_dismissed` (bool)

**Test suite backend** (`backend_r18_reset2_banner_dismiss_test.py`): **15/15 PASS**

| # | Test | Focus |
|:---:|:---|:---|
| 1 | `test_1_dismiss_requires_auth` | 401 senza token |
| 2 | `test_2_dismiss_sets_flag_own_guild` | Flag setter + persistenza DB |
| 3 | `test_3_dismiss_idempotent` | 3 chiamate consecutive → 200 stabile |
| 4 | `test_4_dismiss_isolates_tenant` | Isolation A→B (no leak flag) |
| 5 | `test_5_banner_visible_if_not_dismissed` | GET → `show=true, message_it` byte-exact IT |
| 6 | `test_6_banner_hidden_after_dismiss` | GET post-dismiss → `show=false, dismissed=true` |
| 7 | `test_7_dismiss_endpoint_route_active` | Route mounted correttamente |
| 8 | `test_8_refresh_state_persists` | Stato persistente su GET dopo dismiss |
| 9 | `test_9_migration_banner_still_works` | migration-banner NON regredito |
| 10 | `test_10_no_technical_leak_in_guild_me` | 8 field tecnici forbidden non esposti |
| 11 | `test_11_login_regression` | Login core OK |
| 12 | `test_12_recruitment_regression` | Recruitment core OK |
| 13 | `test_13_adventurers_regression` | Adventurers list OK |
| 14 | `test_14_dungeons_and_expedition_regression` | Dungeons + expedition no-500 |
| 15 | `test_15_freeze_off` | Freeze flag GONE, no 503 |

### 4. Sistema live healthy

Verifiche curl post-implementazione:

```
GET  /api/health                                    → 200
GET  /tmp/orbus_maintenance.flag                    → GONE ✓
GET  /tmp/orbus_internal_job_freeze.flag            → GONE ✓
POST /api/auth/login (valid)                        → 200 (JWT emesso)
GET  /api/guilds/me                                 → 200 (con r18_reset1b_banner_dismissed esposto)
GET  /api/guilds/me/r18-reset-banner                → 200 ({show, dismissed, message_it})
POST /api/guilds/me/r18-reset-banner/dismiss        → 200 (idempotente su ripetizioni)
GET  /api/adventurers                               → 200
GET  /api/dungeons                                  → 200
GET  /api/recruitment/candidates                    → 200
POST /api/expeditions (goblin-warrens, adv lv1)     → 423 Locked (functional)
```

Nessuna regressione runtime. Nessun 500. Nessun 503.

### 5. UI Banner — deliverable frontend

**Componente**: `/app/frontend/src/components/R18ResetBanner.jsx`
**Integrazione**: montato nella pagina Dashboard, sopra la card guild-info.
**Trigger visibilità**: `guild.r18_reset1b_banner_dismissed === false` (o `undefined` per gilde legacy).
**Testo banner (byte-exact IT-locale, LOCKED)**:
```
Le gilde sono state riallineate per il nuovo inizio di Orbus. Il nome della tua gilda è stato preservato; progressi, roster e risorse sono ripartiti da zero.
```
**Interazione**:
- CTA "Ho capito" → `POST /api/guilds/me/r18-reset-banner/dismiss`
- On success: banner sparisce con transizione discreta (opacity fade + collapse)
- On error rete: banner resta visibile, toast "Riprova più tardi"

**Design compliance**:
- Palette scura Orbus, nessun gradient viola/violet
- Nessuna emoji (guidelines UI rispettate)
- Componente shadcn/ui-based (`Card`, `Button` secondary variant)
- Responsive mobile testato via viewport stretto

### 6. Regression e1_tester (PM regression pass)

Esito: **4/4 PASS** (delegato dal PM Orchestrator).

| # | Focus | Esito |
|:---:|:---|:---:|
| 1 | Login + Dashboard rendering post-reset | PASS |
| 2 | Banner UI visibile pre-dismiss + testo byte-exact | PASS |
| 3 | Click "Ho capito" + POST 200 + banner scompare + refresh persiste | PASS |
| 4 | migration-banner esistente NON toccato + endpoint core no-500 | PASS |

### 7. WARN residui → backlog

Durante lo sviluppo e regression sono emersi 2 warning **non-blocking** che sono stati acquisiti come backlog aperto (P3):

**WARN 1 — Migration Banner State Schema Review**
- Il field `r18_reset1b_banner_dismissed` è persistito e restituito da `GET /api/guilds/me/r18-reset-banner`, ma è esposto come chiave "flat" nella response di `GET /api/guilds/me` senza un modello Pydantic dedicato `GuildBannerState`.
- Scope backlog: consolidare uno schema tipizzato riutilizzabile per multi-banner state future.
- Non-blocking (funzionalità coperta, contract già consumato dal frontend).

**WARN 2 — Dungeon Locked Status Code Consistency Review**
- `POST /api/expeditions` in caso di dungeon locked per gate di livello restituisce `403 Forbidden` in alcuni percorsi vs `423 Locked` in altri.
- Scope backlog: convergenza su `423 Locked` per gate funzionali (semantic REST), mantenere `403` solo per ownership violation.
- Non-blocking (i client attuali gestiscono entrambi come "non-permesso").

**Registrati in**: `/app/memory/backlog.md` sotto sezione "Backlog aperti".

### 8. Deferred scope, HOLD, next-in-queue

**Deferred scope R18.Reset.2**: nessuno. Tutte le milestone del round (endpoint + UI + persistence + tests + regression) sono state completate.

**HOLD confermati dopo il SEAL** (invariati):
- `R18.1 drift`
- `R18.3d Stat/Role Mapping Registry` (brief pronto, HOLD implementazione)
- `Traits`
- `Fatigue/Cucina`
- `SMTP R17`
- `orbus.seed_round5.base_strength` warning (P3)

**Next-in-queue consigliato**: `R18.3d — Stat/Role Mapping Registry`
- Brief pronto: `/app/memory/r18_3d_stat_role_mapping_registry_brief.md`
- **Nessuna implementazione** fino a GO PM esplicito.

---

## Timeline sintetica R18.Reset.2

| Timestamp UTC | Evento |
|:---|:---|
| 2026-07-05 15:04 | GO PM per implementazione R18.Reset.2 |
| 2026-07-05 15:15 | Endpoint backend `POST /dismiss` + `GET /r18-reset-banner` + esposizione flag su `GET /api/guilds/me` |
| 2026-07-05 15:30 | Componente `R18ResetBanner.jsx` + integrazione Dashboard |
| 2026-07-05 15:45 | Test suite 15 test scritti e in PASS |
| 2026-07-05 15:50 | Regression e1_tester 4/4 PASS |
| 2026-07-05 16:04 | Header "CLOSED & SEALED" applicato al test file (SEAL contract) |
| 2026-07-05 16:30 | Aggiornamento PRD.md, backlog.md, registry, closure report + brief R18.3d |
| 2026-07-05 16:30 | **R18.Reset.2 = CLOSED & SEALED** |

## Statistiche finali del blocco "Full Guild Fresh Start Reset"

Consolidato R18.Reset.1b + hotfix.v1_3 + R18.Reset.2:

- **672 guild** riallineate (nome preservato, gold=100)
- **3360 adventurers starter** rigenerati (11 classi safe)
- **3415 adventurers storici** archiviati soft
- **2016 minor_healing_potion** distribuite (672 kit × 3)
- **8 sigilli** R18.Reset.1b intatti (verificato)
- **1 contract-lock** documentale per il test file R18.Reset.2
- **15 test dedicati** al banner UI/API (PASS)
- **3 backup persistiti** (retention 90gg)
- **3 backlog aperti** (WARN M3 audit + 2 WARN R18.Reset.2)

---

**R18.Reset.2 = CLOSED & SEALED (2026-07-05T16:04:00Z UTC)**
**Full Guild Fresh Start Reset (blocco intero) = CLOSED & SEALED (2026-07-05T16:30:00Z UTC)**
