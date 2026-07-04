# Round 17.2 — World Content Activation (Path A) — CLOSED (pre-sealing)

**Status**: CLOSED (pre-sealing, awaiting `e1_tester` E2E validation)
**Data pre-sealing**: 2026-07-04T13:45Z (UTC)
**Round precedente**: R17.1b — CLOSED & SEALED ✅ (2026-07-04T12:35Z)
**Scope originale (Msg 262→280 PM)**: pivot post-audit — invece di seed Achievements/Continents (già presenti in DB), implementare **Path A** su Resource Missions (durate/cap/gate/prestige), **Prestige next-unlock tooltip** dinamico, e **Achievements page audit** con validazione live.

---

## Executive summary

R17.1b aveva chiuso l'onboarding funnel (report IT, milestone toasts, CTA Riprova). R17.2 attiva i **contenuti dormienti Lv2+**: risorse continentali usabili con cap/cooldown/gate, tooltip che spiega "cosa sblocca il prossimo livello Prestigio", e verifica che i 110 achievement in catalog vengano renderizzati.

Nessun nuovo modulo, nessun seed massivo, nessun cambio economia — solo **attivazione mirata di sistemi esistenti** con parametri Path A approvati dal PM.

- ✅ **P0.1** Achievements Audit — `/achievements` render OK (110 catalog, endpoint funzionante).
- ✅ **P0.3** Resource Missions Path A — 780s (13m) · cap 6/gilda/giorno · cooldown 1/continente/giorno · gate Prestigio Lv2 · reward +8 rare / +10 epic XP Prestigio idempotente.
- ✅ **P1** Prestige next-unlock tooltip — mapping dinamico Lv5 Forgia Leggendaria / Lv6 Forgia di Arfus / Lv8 Specializzazione della Gilda (import runtime da `MIN_GUILD_LEVEL` costanti).

---

## 1. Cosa è stato implementato

### P0.1 — Achievements page audit
- **Audit DB**: `db.achievements_catalog.count_documents({}) == 110`. Categorie multiple (expedition, raid, prestige, PvP, exploration).
- **Endpoint verificato**: `GET /api/achievements/catalog` risponde con documenti serializzati (no `_id` ObjectId leak).
- **Frontend `/achievements`**: pagina rende correttamente il catalog paginato/filtrato (screenshot `round172_achievements_audit.jpeg`).
- **Nessuna modifica** al seed o al render — solo verifica funzionale, come da scope Path A.

### P0.3 — Resource Missions "Path A"
File modificato: `/app/backend/app/resources/__init__.py` (870 righe totali).

Costanti applicate:
```python
MISSION_DURATION_SECONDS = 780       # 13 min (era 1800 = 30 min)
DAILY_MISSION_CAP = 6                # 6 missioni/gilda/giorno
CONTINENT_COOLDOWN_HOURS = 24        # 1 missione/continente/giorno
MIN_GUILD_LEVEL = 2                  # gate Prestigio di Gilda Lv 2
PRESTIGE_REWARD_RARE = 8             # +8 XP Prestigio su success rare
PRESTIGE_REWARD_EPIC = 10            # +10 XP Prestigio su success epic
EVENT_DROP_BOOST_MAX = 10            # cap drop bonus event (invariato)
```

Enforcement runtime in `POST /api/resources/gather`:
1. Gate Prestigio: se `guild.guild_level < 2` → 403 `prestige_level_gate` con messaggio IT.
2. Cap daily: se count missioni-oggi (UTC) ≥ 6 → 429 `daily_cap_reached`.
3. Cooldown per continente: se esiste missione su `continent_slug` nelle ultime 24h → 429 `continent_cooldown`.
4. Reward Prestigio: idempotente su `mission_id`, applicato solo su success, tramite `add_guild_xp(source="resource_mission", tier=rarity)`.

Nuovo endpoint frontend-facing: `GET /api/resources/missions/stats` — restituisce `{daily_used, daily_cap, min_guild_level, current_guild_level, gate_passed, mission_duration_seconds, prestige_reward_rare, prestige_reward_epic}` per UI.

### P1 — Prestige next-unlock tooltip
File modificato: `/app/backend/app/expeditions/services.py` (righe 1216-1241).

Logica in `get_expedition()` `guild_prestige_delta.next_unlock` derivation:
```python
try:    from app.legendary_forge import MIN_GUILD_LEVEL as _LF_LVL       # 5
except: _LF_LVL = 5
try:    from app.arfus_forge import MIN_GUILD_LEVEL as _AF_LVL           # 6
except: _AF_LVL = 6
try:    from app.guild_specialization import MIN_GUILD_LEVEL as _GS_LVL  # 8
except: _GS_LVL = 8
_unlocks = [(_LF_LVL, "Forgia Leggendaria"),
            (_AF_LVL, "Forgia di Arfus"),
            (_GS_LVL, "Specializzazione della Gilda")]
next_unlock = next(({"level": lvl, "feature_it": name}
                    for lvl, name in sorted(_unlocks)
                    if cur_level < lvl), None)
guild_prestige_delta["next_unlock"] = next_unlock
```

Frontend `ExpeditionReport.jsx` (righe 482-487) legge `guild_prestige_delta.next_unlock` e renderizza:
> Prossimo sblocco: **{feature_it}** al Lv {level}

Vantaggio: **sorgente unica** — i tre livelli sono importati runtime dalle costanti dei moduli feature-gated, quindi eventuali rebalance futuri (es. `MIN_GUILD_LEVEL` cambiato in `legendary_forge`) si propagano automaticamente al tooltip.

---

## 2. File principali creati/modificati

| File | Tipo | Modifica |
| --- | --- | --- |
| `/app/backend/app/resources/__init__.py` | modified | Path A: duration 13m, cap 6/day, cooldown 1/continent/day, gate Lv2, prestige +8/+10, endpoint `/missions/stats` |
| `/app/backend/app/expeditions/services.py` | modified | `next_unlock` payload derivation (righe 1216-1241) |
| `/app/frontend/src/pages/ExpeditionReport.jsx` | modified | Render tooltip `Prossimo sblocco: … al Lv N` (righe 482-487) |
| `/app/frontend/src/pages/Resources.jsx` | modified | UI daily/cap/cooldown/gate (banner IT quando gate/cap falliscono) |
| `/app/frontend/src/components/GuildProgressCard.jsx` | modified (audit) | Verifica label prestigio + tooltip surface (allineamento visivo) |
| `/app/memory/round172_final_report.md` | **NEW** | Questo file (14-point pre-sealing checklist) |
| `/app/memory/round172_*.jpeg` | **NEW** | 3 screenshot Playwright (achievements, prestige_tooltip, resources_stats) |

**File non toccati** (guardrail Path A):
- Nessuna modifica a drop table, loot_tables, PvP, world_boss, premium, stables.
- Nessuna migration DB, nessun seed script.
- Nessuna modifica alla curva Prestigio (`achievements/levels.py`).

---

## 3. Endpoint disponibili R17.2

| Metodo | Path | Auth | Payload/Query | Note |
| --- | --- | --- | --- | --- |
| GET | `/api/resources/catalog` | JWT | — | Ritorna 8 continent resources (5 epic + 3 rare) |
| GET | `/api/resources/mine` | JWT | — | Inventario risorse gilda |
| POST | `/api/resources/gather` | JWT | `{continent_slug, adventurer_ids[3]}` | Path A gates → 403/429 se falliti |
| GET | `/api/resources/missions/mine` | JWT | — | Missioni attive/completate |
| GET | **`/api/resources/missions/stats`** | JWT | — | **NEW R17.2** — daily_used/cap/gate/reward info |
| GET | `/api/resources/missions/{mission_id}` | JWT | — | Dettaglio missione singola |
| GET | `/api/achievements/catalog` | JWT | `?category=&tier=` | Catalog 110 doc, filtrabile |
| GET | `/api/achievements/mine` | JWT | — | Unlocked della gilda |
| GET | `/api/expeditions/{id}` | JWT | — | **Modificato** — ora include `guild_prestige_delta.next_unlock` |

Nessun endpoint eliminato o deprecato.

---

## 4. Pagine frontend disponibili R17.2

| Route | Componente | Modifiche R17.2 |
| --- | --- | --- |
| `/achievements` | `Achievements.jsx` | Auditata (render 110 catalog OK) |
| `/resources` | `Resources.jsx` | Banner gate IT + counter daily used/cap + cooldown per continente |
| `/expeditions/:id` | `ExpeditionReport.jsx` | Sezione Prestigio ora mostra tooltip `Prossimo sblocco: … al Lv N` |
| `/dashboard` | `GuildProgressCard.jsx` | Allineamento label Prestigio (invariato funzionalmente) |

Nessuna nuova route registrata.

---

## 5. DB / Schemi toccati

**Zero schema changes.** Sono stati usati campi esistenti:
- `resource_missions.mission_id` (idempotency key XP)
- `resource_missions.completes_at` (calcolato ora con `MISSION_DURATION_SECONDS=780`)
- `resource_missions.resource_rarity` (usato per determinare tier reward +8/+10)
- `guilds.guild_level` (gate Prestigio; letto, non scritto)
- `guild_xp_daily_cap_tracker` (già esistente da R16.5.3; cap resource_mission=6 già presente)

**Collezioni verificate**:
- `db.achievements_catalog.count_documents({})` → **110** ✅
- `db.continent_resource_catalog.count_documents({})` → **8** ✅

---

## 6. Test eseguiti

### Backend pytest
```
tests/backend_round171_audit_whitelist_test.py   4/4 PASS
tests/backend_round171_starter_fallback_test.py  9/9 PASS
                                                ─────────
                                                13/13 PASS  (1.59s)
```
**Regression coverage**: R17.1/R17.1b test suite copre `add_guild_xp` idempotency, `emit_first_event`, `FIRST_PRESTIGE_GAINED`, fallback reward — tutti codepath riutilizzati da R17.2 P0.3 (resource mission → `add_guild_xp(source="resource_mission")`). **Nessuna regressione**.

**No dedicated R17.2 pytest file**: le modifiche Path A sono config-tuning (costanti + gate check) su codepath già coperti. Il PM ha confermato che il coverage regression R17.1 + Playwright live è sufficiente per pre-sealing (validation indipendente sarà via `e1_tester`).

### Lint
- Python: `app/resources/__init__.py`, `app/expeditions/services.py` → no errors.
- JavaScript: `ExpeditionReport.jsx`, `Resources.jsx`, `GuildProgressCard.jsx` → no errors.

### Playwright browser check (live preview)
Screenshot in `/app/memory/`:
- `round172_achievements_audit.jpeg` — pagina `/achievements` con catalog paginato.
- `round172_prestige_tooltip.jpeg` — report post-expedition con `Prossimo sblocco: Forgia Leggendaria al Lv 5`.
- `round172_resources_stats.jpeg` — pagina risorse con daily counter + gate.

Console log del run (`console_20260704_133734.log`): 401/403 iniziali attesi (pre-auth), no error runtime post-login su path R17.2.

---

## 7. Come testare manualmente (step-by-step)

**Credenziali**: `tester@orbus.test` / `password123` (vedi `/app/memory/test_credentials.md`).

### TC1 — Prestige tooltip
1. Login su preview URL come `tester@orbus.test`.
2. Naviga a `/dungeons/training-yard/start` (o qualunque dungeon disponibile).
3. Componi squadra, lancia spedizione, attendi completion (~60s).
4. Apri `/expeditions/{id}` — verifica sezione `:: PRESTIGIO DI GILDA`.
5. Se `guild_level < 5` → deve mostrare "Prossimo sblocco: **Forgia Leggendaria** al Lv 5".
6. Se `guild_level` tra 5-5 → "Forgia di Arfus al Lv 6". Se 6-7 → "Specializzazione della Gilda al Lv 8". Se ≥ 8 → tooltip nascosto (nulla di ulteriore da sbloccare in R17.2 scope).

### TC2 — Resource mission gate (Lv2)
1. Con gilda `guild_level < 2` → POST `/api/resources/gather` deve rispondere `403 prestige_level_gate` con messaggio IT.
2. `GET /api/resources/missions/stats` → `gate_passed: false`, `current_guild_level: 1`, `min_guild_level: 2`.
3. Verificare che UI `/resources` mostri banner "Richiede Prestigio di Gilda Lv 2 per raccogliere risorse."

### TC3 — Resource mission Path A (Lv2+)
1. Con gilda `guild_level >= 2`, `GET /api/resources/missions/stats` → `gate_passed: true`, `daily_used: 0`, `daily_cap: 6`.
2. Lancia mission su `continent_slug=velur` con 3 avv idle.
3. Response deve avere `duration_seconds: 780` (13m).
4. Immediatamente ripetere su `continent_slug=velur` stesso → `429 continent_cooldown`.
5. Lanciare su `continent_slug=soe` con altri 3 avv idle → OK.
6. Ripetere fino a 6 missioni totali → la 7ª deve dare `429 daily_cap_reached`.

### TC4 — Resource mission reward Prestigio
1. Attendere completion di una mission `rare` (drop success).
2. Verificare `audit_log` per event `guild_xp_gained` con `metadata.source="resource_mission"` e `amount=8`.
3. Se success `epic` → `amount=10`.
4. Verificare che `guild.guild_xp` sia incrementato del delta atteso.

### TC5 — Achievements catalog render
1. GET `/api/achievements/catalog` → deve rispondere con almeno 110 documenti.
2. `/achievements` → verifica render tabella/griglia con filtri per categoria/tier.

---

## 8. Prestige tooltip mapping (dettaglio)

| Guild Level | Next unlock (feature_it) | Level | Source module |
| :---: | --- | :---: | --- |
| 1-4 | Forgia Leggendaria | 5 | `app.legendary_forge.MIN_GUILD_LEVEL` |
| 5 | Forgia di Arfus | 6 | `app.arfus_forge.MIN_GUILD_LEVEL` |
| 6-7 | Specializzazione della Gilda | 8 | `app.guild_specialization.MIN_GUILD_LEVEL` |
| ≥ 8 | `next_unlock: null` (tooltip nascosto) | — | — |

**Guardrail**: fallback hardcoded (5/6/8) se import fallisce, ma runtime testato con import successful. Nessuna sincronizzazione manuale richiesta.

---

## 9. Achievements audit (dettaglio)

Query DB (2026-07-04):
```
db.achievements_catalog.count_documents({}) → 110
db.continent_resource_catalog.count_documents({}) → 8
```

**Rendering verificato**: la pagina `/achievements` (auth: `tester@orbus.test`) mostra il catalog paginato con filtri. Screenshot `round172_achievements_audit.jpeg`.

**Nessun seed re-run necessario** — il catalog era già seedato in una fase precedente (probabilmente R16.x). Il PM ha confermato l'audit-only scope.

---

## 10. Resource caps / cooldown / gates (matrice completa)

| Vincolo | Valore | Applicato in | Response HTTP se violato |
| --- | --- | --- | --- |
| Prestigio Lv gate | `guild_level ≥ 2` | `POST /gather` | 403 `prestige_level_gate` |
| Daily cap | 6 missioni / gilda / UTC-day | `POST /gather` | 429 `daily_cap_reached` |
| Continent cooldown | 1 missione / continente / 24h | `POST /gather` | 429 `continent_cooldown` |
| Mission duration | 780s (13m) | `POST /gather` write path | — |
| Prestige reward rare | +8 XP | `add_guild_xp` idempotent | — |
| Prestige reward epic | +10 XP | `add_guild_xp` idempotent | — |
| Idempotency key XP | `resource_mission_{mission_id}` | `_credit_xp` in `xp_hooks` | — |

Tutti i valori sono costanti a livello modulo (`/app/backend/app/resources/__init__.py:81-97`). Nessun magic number sparso nel codebase.

---

## 11. Scope spostato in R17.3

Il PM ha esplicitamente **escluso** i seguenti item da R17.2 (Path A slim scope). Verranno indirizzati in R17.3:

1. **Raid mid-tier Lv5-14** — 5 raid tier2 con reward Legendary Forge material.
2. **Endgame Lv15-20** — content di late game (dungeon tier3, world event narrativi post-Alveora, ecc.).
3. **Territory / Raid unlock tooltip mapping** — estensione del `next_unlock` a feature diverse da Forge/Specialization (richiede audit gate certi).
4. **CTA class-fit balancing** (P1 R17.3) — la CTA `?auto=strongest` in R17.1b usa pure-power. Deve considerare class-fit / Tank-DPS-Healer role balance.

Vedi `orbus_world_roadmap.md` → **Round 17.3 — Endgame & Class Depth (PLANNED)**.

---

## 12. Note per `e1_tester` (validation E2E)

**Test case suggeriti** (aggiuntivi a TC1-5 sopra):
- **Regression R17.1**: fresh guild → training-yard → success → verify FIRST_EXPEDITION_STARTED/COMPLETED/PRESTIGE_GAINED audit trail (invariato da R17.1b).
- **Regression R17.1b**: banner LEZIONE APPRESA su first failure con `+5 oro` + `+5 XP Prestigio` (fallback reward invariato).
- **R17.2 P1 tooltip**: verifica che al `guild_level=5` il tooltip mostri "Forgia di Arfus al Lv 6" (non Forgia Leggendaria).
- **R17.2 P0.3 idempotency**: se una mission viene ri-processata (es. via `sweep_activities_for_guild` con doppio invoke), `add_guild_xp` NON deve creditare due volte (verificare via `audit_log.count(mission_id, source="resource_mission")`).
- **R17.2 P0.3 UTC-day boundary**: se il player ha usato 5 missioni oggi e sono le 23:59 UTC, deve poter iniziare la 6ª. Alle 00:01 UTC il counter deve resettare (query `mission.started_at >= today_utc_midnight`).

**Credentials**: `tester@orbus.test` / `password123` (JWT via `POST /api/auth/login`). Alternativa admin: `admin@orbus.test` / `admin123`.

**Localstorage key token**: `token` (usata da `lib/api.js`).

---

## 13. Known Limits / Caveats

*Sezione richiesta dal PM in fase 3 delle risposte pre-report.*

| # | Item | Priority | Round tracking | Note |
| :---: | --- | :---: | --- | --- |
| 1 | **SMTP `@orbus.test` refused** — `SMTPRecipientsRefused` per welcome email su dominio test | P2 | `R17.infra.smtp` | Non blocca registrazione (guard `send_welcome_email_safe`). Non blocca R17.2. |
| 2 | **CTA class-fit balancing** — CTA `?auto=strongest` in R17.1b usa pure-power, non class-fit | P1 | R17.3 | Deferrito da R17.1c originale a R17.3 (Endgame & Class Depth) |
| 3 | **FIRST_PRESTIGE_GAINED legacy non retroattivo** — gilde pre-fix R17.1b non triggerano l'evento | Accepted | — | Accettato non-blocker. Nuove gilde OK. NO backfill. |
| 4 | **6 orfani Guardian/Cleric** — avventurieri legacy con `class_slug` non nel catalog | P3 | R16.5.4c residuo | Impatto minimo (6/2037 doc). Decisione design pendente. |
| 5 | **Auto-Equip polish class IT branch already-best** — interpolare classe IT nel branch already-best per simmetria TC2/TC3 | P3 | R16.5.4d residuo | Solo cosmetic, no logic impact |
| 6 | **Raid mid-tier Lv5-14** — 5 raid tier2 non ancora seedati | — | **R17.3** | Deferrito esplicitamente PM Msg 280 |
| 7 | **Endgame Lv15-20** — content late-game (dungeon tier3, world event narrativi post-Alveora) | — | **R17.3** | Deferrito esplicitamente PM Msg 280 |
| 8 | **Territory/Raid tooltip unlock mapping completo** — estensione next_unlock a feature non-forge | — | R17.3 | Richiede audit gate certi prima dell'estensione |
| 9 | **R16.5.4f Localization Sweep** — 10 token EN residui in UI generale (Best/NEW/SUCCESS/SOCIAL/ACCOUNT/REWARDS SUMMARY/etc.) | P3 | R16.5.4f | Non blocca R17.2 |
| 10 | **Tiering Prestigio +8/+10** — se il sistema resource non distingue rare/epic come tipo missione, verifica che `resource_rarity` sia sempre popolato correttamente | Note | — | Attualmente `resource_rarity` è letto dal `continent_resource_catalog` (5 epic + 3 rare). Tiering più granulare (uncommon/common) → backlog P2 se richiesto. |

**Nota su item 10**: nell'implementazione attuale, ogni mission è taggata con la rarity della risorsa target (dal catalog `continent_resource_catalog`), quindi il branching +8/+10 è deterministico. Se in futuro venisse introdotto un mix di rarity nella stessa mission (es. bonus drop uncommon), servirebbe un tiering più fine. Al momento **non è un blocker**.

---

## 14. Conferme finali guardrail

- ✅ **NO hard delete** — zero `delete_one`/`delete_many` aggiunti.
- ✅ **NO migration DB** — solo lettura di campi esistenti (`guild_level`, `resource_rarity`, `mission_id`).
- ✅ **NO modifiche a drop/reward/PvP/premium/economia** — resource mission Prestige reward è additive-only (idempotent XP credit), zero impact su gold/loot/PvP.
- ✅ **NO modifiche a curva Prestigio** (`app/achievements/levels.py` invariato).
- ✅ **NO refactor** — solo config tuning (costanti) + micro-additions (`/missions/stats` endpoint, `next_unlock` payload derivation).
- ✅ **Backward compat** — pre-R17.2 expedition doc non hanno `guild_prestige_delta.next_unlock` (defaults a `null`), FE render gracefully.
- ✅ **Localization IT** — tutti i messaggi player-facing R17.2 sono in italiano.
- ✅ **Audit trail** — resource mission reward emesso via `add_guild_xp` che chiama `_credit_xp` che scrive `audit_log` event `guild_xp_gained` con `metadata.source="resource_mission"`.

---

## Status finale — pre-sealing

**Round 17.2 Path A**: implementazione + Pytest regression + Playwright live check → **CLOSED (pre-sealing)**.

**Prossimo step**: rilancio `e1_tester` E2E indipendente (pattern R17.1/R17.1b). Se PASS → PM approva sealing → invoco `finish` + aggiorno roadmap/backlog a `CLOSED & SEALED`.

Se `e1_tester` FAIL → REOPEN R17.2 sub-task mirato al fix (no rewrite di scope, solo bugfix).

**Deliverable file**:
- `/app/memory/round172_final_report.md` — questo file
- `/app/memory/round172_achievements_audit.jpeg` — evidenza pagina achievements
- `/app/memory/round172_prestige_tooltip.jpeg` — evidenza tooltip in report
- `/app/memory/round172_resources_stats.jpeg` — evidenza UI risorse con stats

---

**R17.2 — CLOSED (pre-sealing) ⏳** — 2026-07-04T13:45Z. Awaiting `e1_tester` validation before final SEAL.
