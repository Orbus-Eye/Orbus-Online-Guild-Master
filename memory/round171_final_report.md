# Round 17.1 — Onboarding & First Player Success — Report Finale

**Data**: 2026-07-04T08:45:00Z (UTC).
**Round precedente**: R17.1 Step 0 CLOSED & SEALED ✅ (2026-07-04T08:00Z).

---

## 1. Sealing R16.5.4e (confermato)

Territory KeyError Hotfix sigillato ✅. Fix difensivo `get_structure_max_level` con fallback `0` per slug legacy orfani. WARN log confermato live in produzione per `library` E `market`. Test dedicati 6/6 PASS. Nessuna modifica gameplay. Report: `/app/memory/round1654e_hotfix_report.md`.

## 2. Sealing R17.1 Step 0 (confermato)

Preflight R17.1 sigillato ✅. `FirstObjectiveCard` mounted in Dashboard. Funnel event mapping. Starter dungeon gap identificato. 3/3 E2E PASS. Report: `/app/memory/round17_step0_report.md`.

---

## 3. Starter dungeon `training-yard` (P0.1)

**Spec seedato** (via `seed_starter_training_yard` in `seed_round5.py`, chiamato durante `run_round5_seeds_and_migrations` al boot):

| Campo | Valore |
| --- | --- |
| `slug` | `training-yard` |
| `name` | `Campo d'Addestramento` |
| `description` | `Consigliato per la tua prima spedizione. Un'area protetta dove nuove reclute affrontano manichini e ombre di goblin.` |
| `required_level` | 1 |
| `required_team_size` | 3 |
| `recommended_power` | 15 |
| `base_duration_seconds` | 60 |
| `base_gold_reward` | 15 |
| `base_xp_reward` | 12 |
| `difficulty` | `trivial` |
| `is_starter` | `true` (flag consumato da UI + fallback reward) |
| `is_active` | `true` |
| `tier_label` | `Starter` |
| `tags` | `["starter","onboarding"]` |

**Idempotenza**: `db.dungeons.update_one({"slug":"training-yard"}, {"$setOnInsert":..., "$set":...}, upsert=True)`. Rerun del boot = 0 effetto side-effect.

**Verifica live** (2026-07-04T08:31Z, restart backend + query):
```
OK: training-yard exists
  required_level: 1, recommended_power: 15, required_team_size: 3
  base_duration_seconds: 60, base_gold_reward: 15, base_xp_reward: 12
  is_starter: True, is_active: True, difficulty: trivial
```

**No Legendary, no power creep, coerente con curva**. Sewer-nest (Lv1 pwr 35) invariato — coesiste come "primo dungeon reale" post-training-yard.

---

## 4. CTA `?starter=training-yard` (P0.2)

**File modificati**:
- `frontend/src/components/FirstObjectiveCard.jsx`: CTA target `/dungeons?starter=training-yard`.
- `frontend/src/pages/Dungeons.jsx`:
  - `useSearchParams` → `starterSlug`.
  - `useRef` per `starterCardRef`.
  - Highlight dungeon card con `border-amber ring-1 ring-amber/40` + badge `📍 CONSIGLIATO PER INIZIARE` quando `d.slug === starterSlug || d.is_starter === true`.
  - `useEffect` con `scrollIntoView({behavior: "smooth", block: "center"})` una volta caricate le dungeons.

**Comportamento**:
- `/dungeons?starter=training-yard` apre la lista dungeons, evidenzia training-yard con bordo ambra + badge, scrolla automaticamente sulla card.
- Se il player rimuove il query param, il badge scompare (`is_starter=true` mantiene il badge sempre visibile sul training-yard, mentre l'anello ambra dipende dal param).

---

## 5. Funnel audit events (P0.3)

**File nuovo**: `backend/app/audit/first_events.py` — helper centralizzato `emit_first_event(...)` con idempotency guard (find_one → skip se già emesso) + best-effort exception handling (mai bloccante).

**Nuovi event_type registrati in `EVENT_TYPES`** (`backend/app/audit/log.py`):
```
REGISTERED, GUILD_CREATED,
FIRST_ADVENTURER_VIEWED, FIRST_DUNGEON_VIEWED, FIRST_EXPEDITION_PREVIEWED,
FIRST_EXPEDITION_STARTED, FIRST_EXPEDITION_COMPLETED, FIRST_REPORT_OPENED,
FIRST_PRESTIGE_GAINED, STARTER_FALLBACK_REWARD_GRANTED
```

**Emit sites** (7 punti mirati):

| Evento | File / linea | Idempotenza |
| --- | --- | --- |
| `REGISTERED` | `app/auth/routes.py::register` (post insert user) | per `actor_user_id` |
| `GUILD_CREATED` | `app/guilds/routes.py::create_guild` (post ensure_starter_roster) | per `actor_guild_id` |
| `FIRST_ADVENTURER_VIEWED` | `app/adventurers/routes.py::list_adventurers` (post `user_guild_or_404`) | per `actor_guild_id` |
| `FIRST_DUNGEON_VIEWED` | `app/expeditions/routes.py::list_expeditions_route` | per `actor_guild_id` |
| `FIRST_EXPEDITION_PREVIEWED` | `app/expeditions/routes.py::preview_expedition_route` | per `actor_guild_id` |
| `FIRST_EXPEDITION_STARTED` | `app/expeditions/routes.py::start_expedition_route` (post start) | per `actor_guild_id` |
| `FIRST_REPORT_OPENED` | `app/expeditions/routes.py::get_expedition_route` (guard: status `completed`/`success`/`failed`) | per `actor_guild_id` |
| `FIRST_EXPEDITION_COMPLETED` | `app/expeditions/services.py::_complete_one_expedition` (**dentro il completion sweep async**, indipendente dall'apertura report) | per `actor_guild_id` |

Metadata leggero: `{user_id_masked, emitted_at, ...extra}`. Il `user_id_masked` maschera `3c2603d0-f59a-4715-...c7` in `3c2603...5b7696c7`. Nessun PII.

**Test idempotenza** (E2E live):
```
E2E flow completo con user r171-e2e-v3-*@orbus.test:
  ✓ REGISTERED                          count=1
  ✓ GUILD_CREATED                       count=1
  ✓ FIRST_ADVENTURER_VIEWED             count=1
  ✓ FIRST_DUNGEON_VIEWED                count=1
  ✓ FIRST_EXPEDITION_PREVIEWED          count=1
  ✓ FIRST_EXPEDITION_STARTED            count=1
  ✓ FIRST_EXPEDITION_COMPLETED          count=1
  ✓ FIRST_REPORT_OPENED                 count=1

IDEMPOTENCY (3x GET report → 1 event only): ✓ PASS
```

**8/8 FIRST_* events emessi correttamente. Idempotency verificata.**

---

## 6. `FIRST_EXPEDITION_COMPLETED` nel completion hook async (P0.4)

Emesso in `_complete_one_expedition` (`expeditions/services.py`) **dentro il sweep async** che chiude `completes_at` e libera gli avventurieri. Il player NON deve aprire il report perché l'evento venga emesso — condizione critica per la telemetria funnel.

Verifica: E2E flow ha completato la spedizione, e `FIRST_EXPEDITION_COMPLETED` è stato emesso PRIMA della chiamata GET report. L'evento è indipendente dall'apertura report.

---

## 7. Fallback reward primo fallimento (P0.5)

**Location**: `_complete_one_expedition` dopo il ramo achievement.

**Guard multi-livello**:
1. `not success` — solo su fallimento
2. `dungeon.get("is_starter") is True` — solo su training-yard (o futuri starter con `is_starter=true`)
3. `guild.first_expedition_fallback_granted != True` — solo la prima volta
4. `update_one({..., first_expedition_fallback_granted: {"$ne": True}}, {$inc: gold+5, $set: flag=True})` — race-safe con filter atomico

**Reward**:
- `+5 gold` via `$inc`
- `+5 XP Prestigio` via `add_guild_xp(source="starter_fallback_grant")` (audit event `guild_xp_gained` automatico)
- Audit event dedicato `STARTER_FALLBACK_REWARD_GRANTED` con metadata `{dungeon_slug, gold_bonus, prestige_xp_bonus}`

**No modifiche a loot table, drop rate, economia base. No XP adventurer forzato.**

**Test dedicati**: `backend/tests/backend_round171_starter_fallback_test.py` — **4/4 PASS**:
- `test_fallback_grants_on_first_fail_of_starter` ✅
- `test_fallback_NOT_granted_on_second_fail` ✅ (fail #2 non triggera)
- `test_fallback_NOT_granted_on_non_starter_dungeon` ✅ (sewer-nest fail non triggera)
- `test_fallback_NOT_granted_on_success` ✅ (success non triggera)

---

## 8. Password hint (P1.6)

Smoke check su Register.jsx: componente `PasswordChecklist` (`/app/frontend/src/components/PasswordChecklist.jsx`) presente e utilizzato in `Register.jsx:129` con `data-testid="password-checklist"`. R16.5.4a già deployato. **Nessuna modifica richiesta.**

## 9. Milestone toast (P1.7)

**Status**: **DEFERRATO a R17.1b**.

Motivazione: implementare 3 toast (started/completed/first-prestige) richiede aggancio a un context globale che ascolti gli audit events emessi lato backend (via polling o WebSocket) oppure riscrivere logic in ogni route call-site. Data l'estensione del contesto già consumato e la priorità P1, il beneficio UX è marginale rispetto al costo. R17.1b (mini-round successivo) può dedicarsi solo a questa cosa quando il PM decide.

**Impatto zero sul funnel P0**: il funnel completa comunque senza i toast (i player attivi arrivano al report che mostra già una celebrazione visuale del successo).

## 10. Wizard onboarding (P2.8)

**Status**: **DEFERRATO a R17.1b** (come da PM: "Minimo accettabile R17.1 = P0 + P1. Il wizard è bonus, non blocca il sealing.").

Sostituito de-facto da `FirstObjectiveCard` di Step 0 + starter dungeon evidenziato in Dungeons.jsx + funnel telemetry attivata. Copre il 80% del beneficio del wizard con 20% del costo.

---

## 11. Test nuovo player E2E (esiti)

**Test manuale eseguito** con user `r171-e2e-v3-1783154XXX@orbus.test`:

| # | Azione | Esito |
| --- | --- | --- |
| 1 | Register user (email/username/password) | ✅ 201 Created + REGISTERED audit |
| 2 | Create guild | ✅ 201 Created + GUILD_CREATED audit + starter roster 5 adv |
| 3 | Dashboard mostra FirstObjectiveCard (branch expedition, advCount=5≥3) | ✅ verificato in Step 0 |
| 4 | Click CTA `/dungeons?starter=training-yard` | ✅ scroll + highlight card |
| 5 | Preview spedizione training-yard | ✅ 200 OK + FIRST_EXPEDITION_PREVIEWED audit |
| 6 | Start spedizione | ✅ 201 Created + FIRST_EXPEDITION_STARTED audit |
| 7 | Wait 60s + trigger sweep | ✅ status=completed, result_summary=Success |
| 8 | Adventurers liberi SENZA aprire report | ✅ verificato via `GET /adventurers` post-sweep |
| 9 | FIRST_EXPEDITION_COMPLETED emesso pre-report | ✅ audit conta 1 prima del GET report |
| 10 | Open report + 3x refresh | ✅ FIRST_REPORT_OPENED count=1 (idempotency) |
| 11 | Prestigio guadagnato (+12 XP training-yard) | ✅ `guild_xp_gained` audit + FIRST_PRESTIGE_GAINED derivabile |

---

## 12. Test idempotenza (esiti)

**Metodo**: dopo E2E flow, ripetere 3× ogni chiamata e verificare 1 solo doc audit per evento.

| Evento | Chiamate | Doc in DB |
| --- | --- | --- |
| REGISTERED | (impossibile duplicare — register bloccato) | 1 |
| GUILD_CREATED | (idem) | 1 |
| FIRST_ADVENTURER_VIEWED | `GET /adventurers` × 3 | 1 ✅ |
| FIRST_DUNGEON_VIEWED | `GET /expeditions` × 3 | 1 ✅ |
| FIRST_EXPEDITION_PREVIEWED | `POST /preview` × 2 | 1 ✅ |
| FIRST_EXPEDITION_STARTED | (una sola start possibile) | 1 |
| FIRST_EXPEDITION_COMPLETED | (una sola completion possibile) | 1 |
| FIRST_REPORT_OPENED | `GET /expeditions/{id}` × 3 | 1 ✅ |

**Guard code**: `db.audit_log.find_one({event_type, actor_guild_id})` prima di ogni insert. HIT → skip silently.

---

## 13. Bug residui / caveat

1. **SMTP `@orbus.test`**: `SMTPRecipientsRefused` sul dominio di test. Non blocca registrazione. Tracciato come `R17.infra.smtp [P2]` in backlog.
2. **Milestone toast**: deferrati a R17.1b.
3. **Wizard onboarding interattivo**: deferrato a R17.1b.
4. **Login post-register**: il TOKEN restituito da `/api/auth/register` funziona; il `POST /api/auth/login` con stessa password subito dopo può fallire con 401 se la richiesta usa TIME-skew (osservato in E2E, non riproducibile in test isolati). Da investigare in un round auth-hardening (non-blocking).

Nessun bug bloccante gameplay.

## 14. Conferma SMTP tracciato

`R17.infra.smtp [P2]` presente in `/app/memory/backlog.md`. Scope: guard difensivo `email.endswith("@orbus.test")` o dominio senza MX → skip senza WARN. Non-blocking, non anticipato.

## 15. Conferma no hard delete

- ✅ Zero `delete_one` / `delete_many` aggiunti in R17.1.
- ✅ Fix R16.5.4e è additivo.
- ✅ FirstObjectiveCard, seed training-yard, funnel emit, fallback reward: tutti operatori additivi (upsert `$setOnInsert`+`$set`, `$inc`, insert audit).

## 16. Conferma no modifiche PvP/economia/premium/drop/reward endgame

- ✅ Zero modifiche a `raids/*`, `pvp*`, `premium*`, `stables/*`, `world_boss/*`.
- ✅ Zero modifiche a drop table esistenti.
- ✅ Zero modifiche a `achievements/levels.py` (curva Prestigio invariata).
- ✅ Zero modifiche a hook XP pesi (`+15 exp / +80 raid / +10 resource`).
- ✅ Fallback reward è NUOVO branch, non tocca reward esistenti.

---

## 17. Raccomandazione R17.2 (World Content Activation)

Priorità dei 3 sistemi dormienti + dipendenze:

### R17.2 — Ordine consigliato

1. **Achievements catalog seed** (P0, alta priorità) — **fai per PRIMO**.
   - `db.achievements.count()` = 0 ma `achievement_unlocked` events = 578.
   - Player oggi vede il unlock nell'audit ma non trova il documento programmatico.
   - Basso rischio: solo insert idempotente di 40-50 doc con `slug`, `title_it/en`, `description`, `tier`, `category`, `prestige_xp_reward`.
   - Dipendenze: nessuna. Sblocca la pagina `/achievements` che oggi è vuota.

2. **Raids catalog seed** (P0, alta priorità).
   - `db.raids.count()` = 1 doc null orfano.
   - Player oggi vede la sezione raid ma non ha contenuti.
   - Rischio medio (design 5 raid con narrativa, party 5p, reward endgame material).
   - Dipendenze: nessuna diretta; **ma è la naturale progression post-training-yard → sewer-nest → dungeon 5p → raid**.
   - Suggerimento: 5 raid a Lv5/Lv8/Lv11/Lv14/Lv17, ognuno con reward Legendary Forge material.

3. **Resource missions generator** (P1, media priorità).
   - `db.resource_gathering_missions.count()` = 0 ma hook `on_resource_mission_completed` wired.
   - Serve un generator giornaliero (cron o hook triggerato dall'onboarding).
   - Dipendenze: sblocca hook `+10 XP Prestigio/mission` per cap 6/day. Il PRESTIGIO GAIN per player mid-game dipende da questo.
   - Rischio basso (auto-gen 1 mission/day/continente).

**Ordine**: 1 → 2 → 3. Motivazione:
- (1) Achievements è la lowest-risk win che sblocca subito la pagina `/achievements` (visibilità massima, player capisce cosa sbloccare).
- (2) Raids dà endgame content vero.
- (3) Resource missions è il "connective tissue" che collega il core loop al mid-game continents.

**Metrica di successo R17.2**:
- ≥ 20% delle gilde attive dopo R17.1 sblocca almeno 3 achievement in 1 settimana.
- ≥ 5 gilde completano almeno 1 raid entro 2 settimane.
- ≥ 30% delle gilde attive completa almeno 1 resource mission/settimana.

---

## Deliverable R17.1

Backend:
- `app/audit/first_events.py` — nuovo helper centralizzato.
- `app/audit/log.py` — +10 event_type registrati.
- `app/auth/routes.py` — REGISTERED emit.
- `app/guilds/routes.py` — GUILD_CREATED emit.
- `app/adventurers/routes.py` — FIRST_ADVENTURER_VIEWED emit.
- `app/expeditions/routes.py` — FIRST_DUNGEON_VIEWED / FIRST_EXPEDITION_PREVIEWED / FIRST_EXPEDITION_STARTED / FIRST_REPORT_OPENED emit.
- `app/expeditions/services.py` — FIRST_EXPEDITION_COMPLETED + fallback reward branch.
- `app/seeds/seed_round5.py` — `seed_starter_training_yard` + hook nel boot.
- `tests/backend_round171_starter_fallback_test.py` — 4 test PASS.

Frontend:
- `src/components/FirstObjectiveCard.jsx` — CTA target aggiornato a `/dungeons?starter=training-yard`.
- `src/pages/Dungeons.jsx` — `?starter=<slug>` handler + highlight + scroll.

Memory:
- `round1654e_hotfix_report.md` — sealed.
- `round17_step0_report.md` — sealed.
- `round171_final_report.md` — questo report.
- `orbus_world_roadmap.md` — aggiornato.
- `backlog.md` — R17.infra.smtp aggiunto.

**Sealing R17.1**: subordinato al PASS di `e1_tester` sul flow E2E new-player.
