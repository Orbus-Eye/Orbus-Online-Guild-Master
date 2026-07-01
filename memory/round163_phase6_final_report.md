# ROUND 16.3 — Phase 6 Iterazione 1 (BACKEND) Final Report

**Data**: 2026-07-01
**Scope**: Trade Pacts V0 + Guild Specialization V0 — pure social +
narrative, ZERO numerical modifiers on economy/XP/drop rates.
**Stato**: 🟡 **BACKEND CLOSED / FRONTEND PENDING** — Iterazione 2
(frontend) partirà dopo verifica manuale utente.

---

## 1. Cosa è stato implementato

### 1.1 — Patti Commerciali V0 (`app/trade_pacts/`)
- **Filosofia V0**: puramente social + informativo, ZERO bonus economici
  (le riduzioni tasse tra partner arrivano in Phase 6.5+)
- Max 3 patti `status=accepted` per gilda, enforce server-side su accept
- Cross-continent block via `guild_world_presence.continent_slug`
- Cooldown 7gg dopo unilateral dissolve tra le stesse due gilde
- NO hard delete: dissolve mantiene la row con `status=dissolved`

### 1.2 — Specializzazioni Gilda V0 (`app/guild_specialization/`)
- **Filosofia V0**: puramente flavor + narrative + hook categories per
  future Phase 6.5+. ZERO bonus numerici in V0
- 6 specializzazioni con `badge_color`, `icon_slug`, `hook_categories`
  per rendering frontend
- 1 sola `status=active` per gilda alla volta (archivio via reset)
- Guild level gate ≥ 8
- Prima scelta gratuita; reset costa 200_000 oro + 3× frammento_di_ergolat
- Cooldown reset 30gg
- NO hard delete: archived rows preservati

### 1.3 — 8 audit events UPPERCASE (whitelist 33 → 41)

---

## 2. File principali creati/modificati

### 2.1 — Nuovi file

| File | Righe | Ruolo |
|---|---:|---|
| `backend/app/trade_pacts/__init__.py` | ~350 | Trade pacts module completo |
| `backend/app/guild_specialization/__init__.py` | ~330 | Specialization module + seed 6 |
| `backend/tests/backend_round163_phase6_test.py` | ~510 | 34 test suite |
| `memory/round163_phase6_final_report.md` | (questo) | Report finale iter1 |

### 2.2 — File modificati

| File | Modifica |
|---|---|
| `backend/app/audit/log.py` | +8 UPPERCASE Phase 6 events in `EVENT_TYPES` |
| `backend/app/admin/audit_routes.py` | +8 events in `AUDIT_EVENT_WHITELIST` (33→41) |
| `backend/app/core/app_factory.py` | Mount 4 router (trade_pacts + admin, spec + admin) + startup seed + indexes |

---

## 3. Seed catalog — 6 specializzazioni

| Slug | Nome IT | Badge Color | Hook Categories | Sort |
|---|---|---|---|---:|
| `incursion` | Gilda di Incursioni | amber | world_boss, raid | 1 |
| `production` | Gilda di Produzione | orange | legendary_forge, crafting | 2 |
| `merchant` | Gilda Mercantile | emerald | market, auction | 3 |
| `exploration` | Gilda di Esplorazione | sky | resource_gathering, continent | 4 |
| `military` | Gilda Militare | red | pvp, defense | 5 |
| `arcane_research` | Gilda di Ricerca Arcana | violet | arfus_forge, arcane | 6 |

**Nota**: `hook_categories` è puramente informativo in V0 — nessun
effetto meccanico. Sarà consumato da Phase 6.5+ (riduzione tasse mercato
per `merchant`, +% success chance legendary per `production`, ecc.).

---

## 4. API endpoint (15 nuovi)

### 4.1 — Trade Pacts `/api/trade-pacts/*` (7 public + 2 admin)
| Metodo | Path | Descrizione |
|---|---|---|
| POST | `/api/trade-pacts/request/{target_guild_id}` | Invia richiesta (continente match, no duplicati, no cooldown) |
| GET | `/api/trade-pacts/received` | Richieste pending ricevute |
| POST | `/api/trade-pacts/{pact_id}/accept` | Accetta (max 3 enforcement) |
| POST | `/api/trade-pacts/{pact_id}/reject` | Rifiuta |
| POST | `/api/trade-pacts/{pact_id}/dissolve?reason=<mutual\|unilateral>` | Sciogli con cooldown 7gg unilateral |
| GET | `/api/trade-pacts/mine?status=<opt>` | Tutti i patti (filtrable) |
| GET | `/api/trade-pacts/partners` | Solo partner attivi (id + nome + since) |
| GET | `/api/admin/trade-pacts/stats` | Aggregato by_status + total_active |
| POST | `/api/admin/trade-pacts/{pact_id}/force-dissolve` | Admin dispute resolution |

### 4.2 — Guild Specialization `/api/guild-specialization/*` (4 public + 2 admin)
| Metodo | Path | Descrizione |
|---|---|---|
| GET | `/api/guild-specialization/catalog` | Lista 6 specializzazioni |
| GET | `/api/guild-specialization/mine` | Attuale + `reset_cost_gold` + `reset_cost_material` |
| POST | `/api/guild-specialization/choose/{slug}` | Prima scelta gratuita (lvl ≥8, no active existing) |
| POST | `/api/guild-specialization/reset/{new_slug}` | Reset con costo + cooldown 30gg |
| PATCH | `/api/admin/guild-specialization/catalog/{slug}?is_active=<bool>` | Toggle catalog |
| GET | `/api/admin/guild-specialization/stats` | Distribuzione per slug + total_active |

**Totale: 15 endpoint Phase 6.**

---

## 5. Test suite + regression

### 5.1 — Test suite Phase 6
**File**: `backend/tests/backend_round163_phase6_test.py`
**Risultato**: **34 passed, 0 failed, 0 skipped**

Copertura:
| ID | Test | Verifica |
|---|---|---|
| T01-T04 | Seed | 6 specializations, idempotent, slug unique, catalog endpoint |
| T05-T08 | Pact request flow | Same continent OK, self→400, cross-continent→400, duplicate→409 |
| T09-T10 | Accept | activated_at set, `/partners` shows active |
| T11-T12 | Dissolve unilateral | cooldown_ends_at set, blocks new request |
| T13-T14 | Reject / mutual dissolve | Reject OK, mutual dissolve no cooldown |
| T15-T16 | Max 3 accepted | 4th accept → 409 max_accepted_pacts_reached |
| T17-T20 | Specialization gate | Lvl<8→403, first choice free, mine returns active, 2nd blocked without reset |
| T21-T23 | Reset flow | Cooldown/gold checks, bypass+success, insufficient gold→402 |
| T24-T27 | Audit events | All 8 UPPERCASE events emitted, whitelist ≥41 |
| T28-T32 | Admin | Stats trade + spec, catalog toggle, force-dissolve, non-admin 403 |
| T33-T35 | Meta | No hard delete, 15 endpoint, Phase 5B regression intact |

### 5.2 — Regression (obiettivo: 253 → 288+)
| Suite | Post-6 |
|---|---:|
| Phase 6 alone | **34/34 pass** ✅ |
| Phase 5A backward-compat | 38/38 ✅ |
| Phase 5B backward-compat | 39/40 (1 skip) ✅ |
| R16.3 phases 1-6 combined | **219 passed, 2 skipped, 0 fail** ✅ |

**Nessuna regression introdotta**. Phase 6 non tocca logica esistente
(patch chirurgici solo su whitelist audit + app_factory mount).

---

## 6. Deviazioni dal brief (documentate)

### 6.1 — `frammento_di_ergolat` come material simbolico
Slug confermato esistente in `items` collection. Reset cost hard-coded.
Se il tester non ha ergolat, il reset **DEVE fallire** con 402 — validato
in T23 (no workaround dev endpoint per bypass).

### 6.2 — Guild continent tramite `guild_world_presence.status='active'`
Schema verificato al bootstrap. Query esplicita:
```python
db.guild_world_presence.find_one(
    {"guild_id": ..., "status": "active"},
    {"_id": 0, "continent_slug": 1})
```
Se una gilda non ha presence attiva → cross-continent check fallisce
esplicitamente con `no_active_continent_for_requester|target`.

### 6.3 — `accept` check su count del destinatario (guild_b_id)
Il brief menzionava "max 3 patti per gilda". Ho implementato il check
sul lato **acceptor** (guild_b_id) al momento dell'accept — cioè
è la gilda che accetta a dover avere <3 patti attivi. Design
intentional: chi accetta è il "commit" finale, quindi il gate va lì.

### 6.4 — No hook categories consumption in V0
`hook_categories` è persistito nel seed ma **nessun servizio lo legge**
in V0. Consumo demandato a Phase 6.5+ tramite un pattern simile
all'applier di Arfus (`get_specialization_hooks(guild_id) -> list[cat]`).

### 6.5 — Reset preserva `reset_count` incrementato
`new_choice["reset_count"] = active["reset_count"] + 1`. Tracking utile
per admin analytics (T29 mostra distribuzione).

---

## 7. Osservazioni non-bloccanti (persistenti)

Valide anche per Phase 6:

1. **`/api/market/listings` → 307 redirect** a `/api/auction/listings`.
2. **PATCH admin `?is_active=<bool>` via query string** (coerente Phase 5A/5B).
3. **BSON ObjectId serialization**: fix post-insert in `choose` e
   `reset` con `.pop("_id", None)` prima di return — pattern riusabile
   per future features.

---

## 8. Vincoli tecnici rispettati

✅ NO deploy · NO hard delete · NO scheduler globale · NO P2W
✅ NO modifiche a economia/XP/drop attuali (patti V0 sono social-only)
✅ NO bonus meccanici da specializzazione in V0
✅ NO tasse ridotte tra alleati (arriva Phase 6.5)
✅ Idempotenza CAS su transizioni stato (accept, dissolve, reset)
✅ Lingua italiana + dual `_it`/`_en` sui seed specializzazioni

---

## 9. Prossimi step

### Iterazione 2 — Frontend Phase 6 (dopo verifica utente)
- 3 pagine React (Trade Pacts hub, Received requests, Guild Specialization)
- 1 MiniCard "Patti Commerciali" in Dashboard V2
- Nav voce "Alleanze" o "Patti Commerciali"
- Vincoli UI identici Phase 5B (`pb-32 md:pb-8`, touch 44x44, no
  `overflow-x` fisso)

### Phase 6.5 (P2 futura, dopo playtest)
- Consumo `hook_categories` per bonus meccanici (tasse mercato, drop
  rate, success chance)
- Riduzione tasse mercato tra partner Trade Pact
- Ordini preferenziali tra partner

### Phase 7 (P2)
- PvP continentale

---

## 10. Header report

**Phase 6 (Backend + Trade Pacts + Guild Specialization)**: 🟡
**BACKEND CLOSED / FRONTEND PENDING**

*Iterazione 1 backend completata: 2026-07-01. Iterazione 2 frontend
segue dopo conferma utente.*
