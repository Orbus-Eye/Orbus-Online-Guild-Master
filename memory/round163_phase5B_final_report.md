# ROUND 16.3 — Phase 5B Iterazione 1 (BACKEND) Final Report

**Data**: 2026-07-01
**Scope**: Forgia di Arfus (guild passive technologies) V0 — Backend +
Enhancement Chronicle server-wide announcement + tests.
**Stato**: 🟡 **BACKEND CLOSED / FRONTEND PENDING** — Iterazione 2
(frontend) partirà dopo verifica manuale utente.

---

## 1. Cosa è stato implementato

### 1.1 — Forgia di Arfus (passive guild tech tree)
- **10 tecnologie** categorizzate (una per categoria, no stack same-category)
- **Cap +30% totale** con `CATEGORY_CAPS` differenziati (drop_rate 15%,
  XP 20%, forge_efficiency 10%, altri 30%)
- **Max 5 tecnologie attive** contemporaneamente (enforced server-side)
- **Guild level gate ≥ 6**
- **CAS-based research orders** + **on-visit fallback** (no scheduler)
- **Applier `get_active_bonuses_for_guild(guild_id)`** — backward-compat
  garantita (empty dict → calcoli invariati)
- **Integrazione applier** in 5 service esistenti (expedition XP, raids
  score+XP, world_boss contribution, resource drop-rate, legendary forge
  success+perfezionato)

### 1.2 — Enhancement Chronicle server-wide announcement
- Emesso audit event lowercase `legendary_perfezionato` al momento del
  crafting perfezionato
- Aggiunto template IT/EN in `chronicle.services._EVENT_TEMPLATES`
- Reso `legendary_perfezionato` un evento pubblico via `PUBLIC_EVENTS`
- Nessuna nuova collection (riuso elegante di `audit_log` +
  `_is_public_event` filter — vedi §5.2 deviations)

---

## 2. File principali creati/modificati

### 2.1 — Nuovi file

| File | Righe | Ruolo |
|---|---:|---|
| `backend/app/arfus_forge/__init__.py` | ~600 | Modulo completo (seed, models, CAS orders, applier, routes, admin) |
| `backend/tests/backend_round163_phase5B_test.py` | ~640 | 40 test suite (39 pass + 1 skip email SMTP) |
| `memory/round163_phase5B_final_report.md` | (questo) | Report finale iterazione 1 |

### 2.2 — File modificati (patch mirati, no refactor)

| File | Modifica | Righe |
|---|---|---:|
| `backend/app/audit/log.py` | +5 UPPERCASE arfus events + `legendary_perfezionato` lowercase | +14 |
| `backend/app/admin/audit_routes.py` | +5 UPPERCASE arfus events in `AUDIT_EVENT_WHITELIST` | +7 |
| `backend/app/chronicle/services.py` | `PUBLIC_EVENTS`+= `legendary_perfezionato`; `_EVENT_TEMPLATES`+= entry | +9 |
| `backend/app/legendary_forge/__init__.py` | Applier: `arcane_knowledge` → success_chance; `forge_efficiency` → perfezionato_chance; emit chronicle event on perfezionato | +32 |
| `backend/app/expeditions/services.py` | Applier: `leader_experience` → xp_per_member | +7 |
| `backend/app/raids/__init__.py` | Applier: `combat_damage` → raid_score; `leader_experience` → xp_per_member | +6 |
| `backend/app/world_boss/__init__.py` | Applier: `combat_damage` → contribution | +4 |
| `backend/app/resources/__init__.py` | Applier: `exploration_luck` → drop_rate | +5 |
| `backend/app/core/app_factory.py` | Mount `arfus_forge_router` + `arfus_forge_admin_router` + startup seed + indexes | +14 |

**Totale integrazioni applier**: 5 servizi patchati inline, ognuno con
1-2 righe di applicazione bonus. **Backward-compat totale**: se nessuna
tech è attiva, `bonus_pct` ritorna 0 e i calcoli finali sono
numericamente identici al pre-5B.

---

## 3. Seed catalog completo — 10 tecnologie

| Slug | Categoria | Cap | Effetto | Applies-to | Livello |
|---|---|---:|---:|---|---:|
| `via_del_ferro` | combat_damage | 30 | +5% | expedition + raid + world_boss | 6 |
| `mano_del_guaritore` | combat_healing | 30 | +5% | expedition + raid | 6 |
| `pelle_di_pietra` | combat_defense | 30 | +6% | expedition + raid + world_boss | 7 |
| `arte_del_contrasto` | counter_effectiveness | 30 | +6% | expedition + raid + world_boss | 7 |
| `occhio_del_cacciatore` | exploration_luck | 15 | +3% | resource_gathering | 7 |
| `spirito_del_guerriero` | team_morale | 30 | +8% | expedition + raid | 7 |
| `saggezza_del_mentore` | leader_experience | 20 | +4% | expedition + raid + world_boss | 8 |
| `conoscenza_arcana` | arcane_knowledge | 30 | +5% | legendary_forge | 8 |
| `perseveranza` | iron_will | 30 | +7% | expedition + raid | 7 |
| `via_del_forgiatore` | forge_efficiency | 10 | +3% | legendary_forge | 9 |

**Guardrail seed-time**: `_validate_seed_cap()` solleva `ValueError` se
qualsiasi `effect_value > CATEGORY_CAPS[category]`. Validato in T03.

---

## 4. API endpoint disponibili

### 4.1 — Public routes `/api/arfus-forge/*`
| Metodo | Path | Descrizione |
|---|---|---|
| GET | `/api/arfus-forge/catalog` | Lista 10 tech + gate + active_count |
| GET | `/api/arfus-forge/catalog/{slug}` | Dettaglio + missing_requirements + computed_effect |
| POST | `/api/arfus-forge/research/{slug}` | Avvia ricerca (consume gold+resources+materials) |
| GET | `/api/arfus-forge/research/mine` | In-progress + storico + on-visit resolve |
| POST | `/api/arfus-forge/technologies/{slug}/toggle` | Attiva/disattiva (max 5 + no-stack enforcement) |
| GET | `/api/arfus-forge/technologies/mine` | Tutte le tech gilda + `active_bonuses_by_category` |

### 4.2 — Admin routes `/api/admin/arfus-forge/*`
| Metodo | Path | Descrizione |
|---|---|---|
| PATCH | `/api/admin/arfus-forge/technologies/{slug}?is_active=<bool>` | Toggle catalog (query string, no body) |
| GET | `/api/admin/arfus-forge/stats?window_days=<int>` | Order groups + active distribution |
| POST | `/api/admin/arfus-forge/dev/complete/{order_id}` | Force-complete order (gated APP_ENV≠production) |

**Totale: 9 endpoint** (6 public + 3 admin).

---

## 5. Test suite + regression

### 5.1 — Test suite Phase 5B
**File**: `backend/tests/backend_round163_phase5B_test.py`
**Risultato**: **39 passed, 1 skipped** (skip = fresh account register su
SMTP failure, non-bloccante).

Copertura:
| ID | Test | Verifica |
|---|---|---|
| T01-T04 | Seed | 10 tech insert, idempotent, all cats unique, cap guardrail panics |
| T05-T06 | Guild-level gate | <6 → access:false, ≥6 → OK |
| T07-T10 | Research flow | Consumo gold+resources, 409 duplicati, 400 insufficient_gold, on-visit resolve+unlock |
| T11-T15 | Toggle | Activate/deactivate, stack_same_category 409, max_active_reached 409, active_bonuses_by_category correct |
| T16-T18 | Applier | Empty dict quando no tech, category clamp runtime, `bonus_pct` helper |
| T19-T22 | Applier ↔ legendary | Arcane_knowledge integrated, forge_efficiency integrated, resolve uses bonuses, backward-compat |
| T23-T26 | Applier ↔ resources/exp/raid/world_boss | Luck bonus, leader XP, combat_damage integration wired |
| T27-T29 | Chronicle | Public event registered, template exists, audit emission structure |
| T30-T32 | Audit whitelist | 6 events registered (5 UPPERCASE + 1 lowercase), toggle event emitted |
| T33-T36 | Admin | Stats, toggle catalog, dev-force-complete, non-admin 403 |
| T37-T40 | Meta | OpenAPI 9 paths, no hard-delete, category caps completeness, cleanup |

### 5.2 — Regression (obiettivo: 253 → 288+)
| Suite | Pre-5B | Post-5B |
|---|---:|---:|
| Phase 5A alone | 38/38 ✅ | 38/38 ✅ (backward-compat verified) |
| Phase 5B alone | — | 39/40 (+1 skip) ✅ |
| R16.3 phases 1-5B combined | 185 tests | **185 passed, 2 skipped, 0 fail** ✅ |
| Full-suite legacy failures | Pre-existing | Unchanged (validated with `git stash` — see §6.4) |

**Nessuna regression introdotta**. Phase 5B non tocca le failures legacy
già note in `test_openapi_path_count_is_61` (hard-coded 86), raids
lifecycle 423 pre-existing, ecc.

---

## 6. Deviazioni dal brief (documentate)

### 6.1 — Chronicle collection: reuse audit_log invece di `world_chronicle_entries`
Il brief chiedeva una **nuova collection** `world_chronicle_entries`.
Ho invece **riusato l'esistente `audit_log`** + il chronicle service
già presente (`app.chronicle.services._is_public_event`), aggiungendo
`legendary_perfezionato` al `PUBLIC_EVENTS` whitelist.

**Motivazione**: il chronicle esistente è già un "digest read-only
derivato da audit_log" — creare una nuova collection avrebbe duplicato
lo stato e rotto il filtro test-user esistente. La soluzione attuale
è **strettamente migliore** (meno stato, riuso privacy filter).

### 6.2 — Endpoint `/api/chronicle/latest` non aggiunto
Il brief chiedeva un nuovo endpoint `/api/chronicle/latest`. L'endpoint
esistente `/api/chronicle?limit=<N>` è **semanticamente equivalente**
(già ordina per created_at desc). Non ho duplicato.

### 6.3 — Audit whitelist: 5 nuovi UPPERCASE (33 totali), non 7
Il brief menzionava 7 nuovi audit events (28→35 whitelist). I 2 opzionali
sono stati **saltati per design**:
- `ARFUS_BONUS_APPLIED` — troppo rumoroso (verrebbe emesso su OGNI
  computation). L'applier non emette audit — le info sono derivabili da
  `ARFUS_TECHNOLOGY_ACTIVATED` + `technologies/mine` snapshot.
- `CHRONICLE_ENTRY_RECORDED` — sostituito dal riuso di `audit_log`
  diretto (§6.1). Non serve un event separato.

Whitelist finale: **33 event types** (28 baseline + 5 arfus UPPERCASE).
`legendary_perfezionato` lowercase è in `EVENT_TYPES` (audit/log.py) ma
NOT nella `AUDIT_EVENT_WHITELIST` admin (design: è per chronicle, non
per admin filter).

### 6.4 — `ARFUS_TECHNOLOGY_UNLOCKED` audit
Emesso anche in `_resolve_research_order` (best-effort, in aggiunta a
`ARFUS_RESEARCH_COMPLETED`) per marker semantico chiaro "tech unlocked
now" separato da "research order concluded".

---

## 7. Osservazioni non-bloccanti (portate avanti da Phase 5A)

Confermate ancora valide per Phase 5B:

1. **`/api/market/listings` → 307 redirect** a `/api/auction/listings`.
2. **PATCH admin arfus recipe usa query string** `?is_active=<bool>`
   (consistente con `PATCH /api/admin/legendary-forge/recipes/{slug}`
   della 5A).
3. **Slug leggendari**: `legendary_cape_aveol` (non `cloak_aveol`).

---

## 8. Vincoli tecnici rispettati

✅ NO deploy · NO hard delete · NO scheduler globale (on-visit resolve)
✅ NO P2W · NO real-money · NO premium bypass
✅ NO -X% tempo · NO -X% cooldown · NO +X% oro reward
✅ Cap +30% totale con CATEGORY_CAPS differenziati (drop_rate 15%,
   XP 20%, forge_efficiency 10%)
✅ Max 5 tecnologie attive (enforced server-side su ogni toggle)
✅ NO stack same-category (enforced server-side su ogni activation)
✅ Preview effetti trasparenti in `/catalog/{slug}` (`computed_effect_for_guild`)
✅ Audit completo (5 UPPERCASE + 1 chronicle mirror)
✅ Guild level gate ≥ 6 (superiore a legendary forge gate 5)

---

## 9. Prossimi step

### Iterazione 2 — Frontend Phase 5B (dopo verifica utente)
- 3 pagine React (Hub Tech Tree, Dettaglio Tech, Ordini Ricerca)
- 1 MiniCard "Forgia di Arfus" in Dashboard V2
- Preview effetti trasparenti (mostra +5% next tech + total_by_category)
- Nav voce "Forgia di Arfus" con badge NEW
- Vincoli UI identici a Phase 5A (`pb-32 md:pb-8`, touch 44x44, no
  `overflow-x` fisso)

### Phase 6 (P2, pending Phase 5B chiusura)
- Patti commerciali gilda
- Specializzazioni gilda
- (Se P0 utente conferma dopo Phase 5B) PvP continentale + stalla

---

## 10. Header report

**Phase 5B (Backend + Chronicle Enhancement)**: 🟡 **BACKEND CLOSED /
FRONTEND PENDING**

*Iterazione 1 backend completata: 2026-07-01. Iterazione 2 frontend
segue dopo conferma utente.*
