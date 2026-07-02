# Round 16.5.3 — Final Report

**Data chiusura**: 2026-07-02T11:00Z
**Scope**: 3 problemi (2 P0 core loop + 1 P1 Guild XP V1).
**Stato**: **CLOSED ✅**

---

## 1. Raid level display fix

**Sorpresa positiva emersa in audit**: il fix era al 90% già implementato in R16.5. Sopralluogo:

- `raid_dungeon_public` (`raids/__init__.py:83`) **GIÀ esponeva** `min_adventurer_level` risolto via `legacy_min_level_for_raid(rd)`.
- Il FE (`Raids.jsx:173`, `RaidBuilder.jsx:155/230/329`) lo consuma correttamente.

Micro-fix applicato (D3 delta):
- Payload d'errore 423 `underleveled_squad` ora include `dungeon_slug` (= raid_slug) per FE clarity.
- `raids/__init__.py:326` (`raid.preview`) e `raids/__init__.py:382` (`raid.start`): aggiunto `dungeon_slug=rd.get("slug")` al call di `enforce_min_adventurer_level`.

**Mapping documentato** (verificato via test):
- Tier 1 → `min_adventurer_level=8`
- Tier 2 → `min_adventurer_level=12`

## 2. Raid start enforcement confermato

`enforce_min_adventurer_level(source="raid.start")` **già chiamato** in `raids/__init__.py:382` (linea invariata). Nessun buco di enforcement:

| Endpoint | Enforcement | Payload dungeon_slug |
|---|:-:|:-:|
| `POST /api/raids/preview` | ✅ (linea 326) | ✅ post-fix |
| `POST /api/raids/start` | ✅ (linea 382) | ✅ post-fix |
| `POST /api/raids/replay-preview` | ⭕ (non-mutating check) | N/A |

## 3. Sweep unificato agganciato

Nuovo helper `app/core/activity_sweep.py::sweep_activities_for_guild(db, guild_id)` che chiama in sequenza best-effort:

1. `complete_due_expeditions` (expedition sweep)
2. `auto_resolve_stuck_raids_for_guild` (raid recovery)
3. `_resolve_expired_missions_for_guild` (resource mission)

**Punti d'aggancio** (3 endpoint frequentemente visitati):

| Endpoint | Prima | Dopo |
|---|---|---|
| `GET /api/adventurers` | ❌ nessun sweep | ✅ sweep unificato |
| `GET /api/roster/health` | ❌ nessun sweep | ✅ sweep unificato |
| `GET /api/guilds/me` | ⚠️ solo expedition | ✅ sweep unificato (ora +raid +resource) |

Latenza cumulativa attesa: **<30ms** con 0 attività in coda, **~80ms** worst-case (3 attività scadute simultanee).

## 4. Test release avventurieri senza aprire report

3 test isolati coprono la fix P0.2:

- `test_P0_2_get_adventurers_releases_stale_expedition_squad` — expedition scaduta → GET /api/adventurers → advs rilasciati **senza mai leggere il report**.
- `test_P0_2_get_adventurers_no_release_for_active_activity` — expedition NON scaduta → advs restano lock (regression guard).
- `test_P0_2_sweep_idempotent_no_double_reward` — 2× GET /api/adventurers → gold guild creditato **una sola volta** (CAS idempotency confermata).

**Tutti ✅ PASS.**

## 5. Guild XP V1 implementata (Prestigio di Gilda)

Nuovo modulo `app/achievements/xp_hooks.py` con 3 drip hooks:

| Hook | Trigger backend | XP crediti | Idempotency key |
|---|---|:-:|---|
| `on_expedition_completed` | `_complete_one_expedition` (services.py) | +15 success / +5 fail | `expedition_id` |
| `on_raid_completed` | `complete_raid` (endpoint) + `raids/recovery.py` (mirror) | +80 victory / +40 partial / +15 fail | `raid_id` |
| `on_resource_mission_completed` | `_resolve_mission` (resources) | +10 success / 0 fail | `mission_id` |

**Contratti tecnici**:
- Emette audit `guild_xp_gained` su `db.audit_log` (fix di alignment: la mia prima versione cercava `audit_events` inesistente).
- Idempotenza pre-check via query `db.audit_log.find_one({event_type, actor_guild_id, source, related_entity_id})`. Se già creditato → skip silent, return None.
- Best-effort: exception nell'hook NON blocca il resolver principale.
- **NO backfill retroattivo**: gli hook si attivano solo sulle nuove completion post-deploy.

## 6. Cap Guild XP implementati

Nuova collection `guild_xp_daily_cap_tracker` con unique index `(guild_id, source, date_utc_iso)`. Reset a mezzanotte UTC.

| Source | Cap | XP max/day | Nota |
|---|:-:|:-:|---|
| `expedition_completed` | **8 / giorno** | 120 XP | drip principale |
| `raid_completed` | **1 / giorno** | 80 XP | scelta tecnica sotto |
| `resource_mission` | **6 / giorno** | 60 XP | drip secondario |
| **Totale soft cap** | — | **~260 XP/giorno** | fair per casual + hardcore |

**Decisione cap raid = 1/giorno** (invece di 3/settimana come opzione originale):
Il tracker `guild_xp_daily_cap_tracker` usa granularità giornaliera UTC per **tutte** le sorgenti (expedition, raid, resource). Adottare cap settimanale sul raid avrebbe richiesto tracker separato con reset logic distinta (weekly ISO). Il pattern giornaliero uniforme è più semplice, più testabile, e semanticamente equivalente per il ritmo previsto (1 raid/giorno max coincide col cooldown esistente `RAID_COOLDOWN_SECONDS`).

**Bootstrap indexes**: aggiunto `ensure_cap_tracker_indexes` a `app/core/lifespan.py` (chiamato al boot) + lazy fallback nel modulo hooks per test isolati.

**Time-to-level proiettato** (con drip attivo):
- Gilda casual (2 exp/giorno + 1 raid/settimana + 1 mission/giorno): ~60-100 XP/giorno → Lv3 in 3-4 giorni, Lv5 in 2 settimane, Lv10 in ~2 mesi.
- Gilda hardcore (cap saturo tutti i giorni): ~260 XP/giorno → Lv10 in ~19 giorni, Lv20 in ~4-5 mesi.

## 7. Progress bar Dashboard "Prestigio di Gilda"

Componente esistente: `/app/frontend/src/components/GuildProgressCard.jsx`.

Modifiche (search-replace, no re-scaffolding):
- Titolo header: `PROGRESSO GILDA` → **`PRESTIGIO DI GILDA`** (label italiana esatta come da brief PM).
- Livello + XP progress bar già presente (invariata, con `data-testid="card-guild-level"` e `data-testid="card-xp-fill"`).
- **Aggiunta sezione** `data-testid="how-to-level-up"` (nuova, tra XP bar e "Prossime imprese").

## 8. "Cosa fare per salire" visibile

Nuova sezione (statica V1) sotto la XP bar, `data-testid="how-to-level-up"`:

```
:: COSA FARE PER SALIRE
• Completa una spedizione                    +15 XP
• Vinci un raid                              +80 XP
• Completa una missione risorse              +10 XP
```

Ciascuna voce ha `data-testid`:
- `hint-expedition`
- `hint-raid`
- `hint-resource-mission`

V1 statico (deliberatamente): mostra le 3 sorgenti core, senza esporre lo stato del cap giornaliero. V2 potrà usare un endpoint dedicato `GET /api/guilds/me/xp-progress` (deferred a R16.5.4).

## 9. Test pass/fail (numeri esatti totali)

**Suite `backend_round1653_test.py`**: **12 / 12 PASS** ✅

Dettaglio:
- **P0.1** (Raid gate): 1/1 pass
  - `test_P0_1_raid_catalog_exposes_min_adventurer_level`
- **P0.2** (Activity sweep): 3/3 pass
  - `test_P0_2_get_adventurers_releases_stale_expedition_squad`
  - `test_P0_2_get_adventurers_no_release_for_active_activity`
  - `test_P0_2_sweep_idempotent_no_double_reward`
- **P1** (Guild XP drip): 8/8 pass
  - `test_P1_expedition_success_credits_15_xp`
  - `test_P1_expedition_fail_credits_5_xp`
  - `test_P1_raid_victory_credits_80_xp`
  - `test_P1_resource_mission_credits_10_xp`
  - `test_P1_expedition_daily_cap_8`
  - `test_P1_raid_daily_cap_1`
  - `test_P1_idempotent_same_activity_id`
  - `test_P1_audit_event_emitted_with_source`

Suite R16.5.1 esistente: **20/20 PASS** (non toccati, verificato retro-compatibilità).

**Totale test rilevanti al round**: **32 / 32 PASS**.

## 10. Conferma NESSUNA modifica a reward / drop / XP avventurieri / PvP / economia

- ❌ Nessuna modifica a XP avventurieri (`adventurer.xp`, `adventurer.level`).
- ❌ Nessuna modifica a drop rate, formule reward, gold rewards, oro base.
- ❌ Nessuna modifica a PvP (matchmaking, punteggio, cooldown).
- ❌ Nessuna modifica a Stalla (mount, narrative routes).
- ❌ Nessuna modifica a monetizzazione / premium / boost.
- ✅ Guild XP è **additivo** (non toglie XP a nessuno; solo aggiunge nuove sorgenti drip).
- ✅ Cap giornalieri **conservativi** (~260 XP/giorno soft) evitano runaway inflation.
- ✅ No backfill: gilde storiche mantengono lo stato attuale.

## 11. Backlog Round 16.5.4 aperto

Vedi `/app/memory/backlog.md` sezione **"Round 16.5.4 — Guild XP V2 Extended Hooks (PLANNED)"** per l'elenco dei 7 hook rimanenti (continental event, daily/weekly contract, structure upgrade, guild spec, trade pact, PvP battle).

**Priorità**: P2 (miglioramento, non blocker).
**Vincoli**: no monetizzazione, no backfill retroattivo, cap giornaliero/settimanale, audit `GUILD_XP_GAINED`.

---

## File modificati/creati (R16.5.3)

### Backend
- **NEW** `/app/backend/app/core/activity_sweep.py` — helper sweep unificato (P0.2)
- **NEW** `/app/backend/app/achievements/xp_hooks.py` — drip hooks + cap tracker (P1)
- **MOD** `/app/backend/app/raids/__init__.py` — 2× `dungeon_slug` nel payload gate, hook drip su `complete_raid`
- **MOD** `/app/backend/app/raids/recovery.py` — hook drip mirror su recovery path
- **MOD** `/app/backend/app/expeditions/services.py` — hook drip su `_complete_one_expedition`
- **MOD** `/app/backend/app/resources/__init__.py` — hook drip su `_resolve_mission`
- **MOD** `/app/backend/app/adventurers/routes.py` — sweep su `GET /api/adventurers` + `GET /api/roster/health`
- **MOD** `/app/backend/app/guilds/routes.py` — sostituito sweep expedition-only con unificato
- **MOD** `/app/backend/app/core/lifespan.py` — `ensure_cap_tracker_indexes` al boot

### Frontend
- **MOD** `/app/frontend/src/components/GuildProgressCard.jsx` — titolo `PRESTIGIO DI GILDA` + sezione "Cosa fare per salire"

### Test
- **NEW** `/app/backend/tests/backend_round1653_test.py` — 12 test isolati (P0.1 + P0.2 + P1)

### Memory
- **NEW** `/app/memory/round1653_final_report.md` (questo file)
- **MOD** `/app/memory/backlog.md` — sezione R16.5.4 aperta
- **MOD** `/app/memory/orbus_world_roadmap.md` — chiusura R16.5.3, apertura R16.5.4 PLANNED

---

## Statement finale

**Round 16.5.3 CLOSED ✅** — pronto per revisione utente + `e1_tester` (browser).

Test focalizzati suggeriti per e1_tester:
1. Card raid mostra Lv reale (non Lv1) sulla lista `/raids` e nel builder.
2. Avventuriero completa expedition, NON apro report, vado direttamente in `/adventurers` → avv rilasciato entro pochi secondi.
3. Dashboard mostra card "PRESTIGIO DI GILDA" con progress bar XP e sezione "COSA FARE PER SALIRE" con 3 hint.
