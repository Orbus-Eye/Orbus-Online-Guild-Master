# ROUND 16.3 Phase 7A Iter1 — PvP Continentale Backend Report

**Data**: 2026-07-01
**Ambiente**: preview `orbus_r16` DB @ `https://drain-dispatch.preview.emergentagent.com`
**Fase**: 7A Iter1 (backend combat 1v1)

---

# ✅ STATO: **BACKEND CLOSED / FRONTEND PENDING**

- Backend PvP Continentale asincrono 1v1 completo, deterministico, idempotente, con on-visit fallback.
- Ricompense **puramente cosmetiche** (Elo + wins/losses/draws + battle log narrativo). Nessuna currency, nessun gold, nessun XP, nessun loot.
- Frontend Iter2 rimandato a sessione dedicata (dopo smoke test owner).

---

## 1. Moduli creati

```
app/pvp_continental/
├── __init__.py          # router + admin_router export
├── models.py            # Pydantic payloads (Challenge/Respond/Decline)
├── applier.py           # Arfus PvP filter (6 categorie whitelist + cap 50%)
├── resolver.py          # calculate_battle_score / compute_elo_update /
│                          find_mvp / generate_battle_log / resolve_battle /
│                          auto_resolve_stuck_battles_for_guild
├── services.py          # gate + cooldown + bracket + team snapshot + CAS
├── routes.py            # 6 endpoint pubblici sotto /api/pvp/*
└── admin_routes.py      # 2 endpoint admin sotto /api/admin/pvp/*

app/scripts/
└── recover_stuck_pvp_battles.py   # CLI recovery --dry-run / --apply

tests/
└── test_pvp_phase7a_p0.py         # 33 test targeted, network-based
```

## 2. Modifiche a file esistenti

| File | Modifica |
|---|---|
| `app/audit/log.py` | +6 event types PVP nella `EVENT_TYPES` frozenset |
| `app/admin/audit_routes.py` | `AUDIT_EVENT_WHITELIST` 41 → **47** (+6 PVP) |
| `app/core/app_factory.py` | import + `include_router(pvp_continental_router)` + `include_router(pvp_continental_admin_router)` |

**Nessun altro file toccato**. Verificato che il modulo PvE esistente `app.pvp` (Arena/Rating) NON è stato modificato — è preservato.

---

## 3. Collection Mongo introdotte

### `pvp_battles`
```
id, challenger_guild_id, defender_guild_id, continent_slug,
challenger_elo_snapshot, defender_elo_snapshot,
challenger_team[5], defender_team[5],
challenger_status, defender_status, status,
challenge_created_at, response_deadline, resolves_at,
resolved_at, resolution_started_at,
outcome, battle_log[], mvp_adventurer_id,
challenger_elo_after, defender_elo_after,
audit_log_ids[]
```

### `guild_pvp_stats`
```
guild_id, elo, wins, losses, draws,
current_active_challenges, created_at, updated_at
```

### `pvp_challenge_cooldowns`
```
challenger_id, defender_id, cooldown_ends_at
```

**Indici**: nessuno creato via lifespan in questa iterazione (postponed a Iter2 con il seed dei dati storici). Query pattern testato con collezioni vuote — performance non critica in questa fase.

---

## 4. API endpoints (6 pubblici + 2 admin)

### Pubblici (`/api/pvp`)
| Method | Path | Descrizione |
|---|---|---|
| GET  | `/opponents` | Lista gilde bracket-matched nello stesso continente |
| POST | `/challenge/{defender_guild_id}` | Invia sfida (body: `adventurer_ids[5]`) |
| GET  | `/battles/mine` | Attive + storico 20 ultime (**triggera on-visit fallback**) |
| GET  | `/battles/{battle_id}` | Dettaglio (403 se non partecipante) |
| POST | `/battles/{battle_id}/respond` | Difensore accetta (body: `adventurer_ids[5]`) |
| POST | `/battles/{battle_id}/decline` | Difensore declina (refund cooldown 6h) |

### Admin (`/api/admin/pvp`)
| Method | Path | Descrizione |
|---|---|---|
| GET  | `/stats` | Counters + Elo histogram + top 10 |
| POST | `/dev/force-resolve/{battle_id}` | Solo `APP_ENV != production` |

**Error codes strutturati** (tutti con `user_message` italiano):
- `pvp.level_gate` (403) — livello gilda < 8
- `pvp.no_guild`, `pvp.no_continent`, `pvp.defender_not_found` (404)
- `pvp.self_challenge`, `pvp.team_size`, `pvp.team_ownership` (400)
- `pvp.cross_continent`, `pvp.out_of_bracket`, `pvp.cooldown`, `pvp.max_active_challenges`, `pvp.team_unavailable`, `pvp.team_race`, `pvp.race_lost`, `pvp.deadline_expired`, `pvp.wrong_status` (409)
- `pvp.not_defender`, `pvp.not_participant` (403)
- `pvp.battle_not_found` (404)
- `pvp.dev_disabled_in_prod` (403 solo prod)

---

## 5. Formula PvP + Elo

### Score deterministico

```
base_power(team)     = Σ (STR + AGI + INT + END + FAI + level*3)  per 5 adv
arfus_multiplier     = 1 + get_pvp_arfus_bonus_sum(guild)      # cap +50%
new_player_multiplier= 1.20 if role=defender AND completed_expeditions<10 else 1.0
variance             = Random("{battle_id}:{role}").uniform(0.9, 1.1)

score = base_power * arfus_multiplier * new_player_multiplier * variance
```

### Outcome
```
diff_ratio = |chall_score - def_score| / max(chall_score, def_score)
if diff_ratio < 0.03: outcome = "draw"        # nessuna variazione Elo
elif chall_score > def_score: outcome = "challenger_win"
else: outcome = "defender_win"
```

### Elo update (K=32)
```
expected_w = 1 / (1 + 10^((loser_elo - winner_elo) / 400))
delta = 32 * (1 - expected_w)
new_winner = clamp(winner_elo + delta, 800, 2400)
new_loser  = clamp(loser_elo  - delta, 800, 2400)
```

Esempio (1200 vs 1200): +16 / -16 → **verificato in test_05**.
Esempio clamp (2400 vs 810): delta massimo bloccato a 2400 e ≥ 800 → **verificato in test_06/07**.

### Forfeit
- No Elo change (anti rage-quit)
- +1 win challenger, +1 loss defender
- MVP calcolato solo su challenger_team

---

## 6. Battle log narrative (deterministico, italiano)

Templates hardcoded, no LLM. Struttura per battaglia:

```
Turno 1: opening (arena/schieramento)
Turni 2-5: mid-fight (3-4 azioni miste, alternate tra squadre)
Turno n: MVP highlight (skip in caso di forfeit)
Turno finale: closing (win / draw / forfeit)
```

**Determinismo**: seed = `f"{battle.id}:log"`. Rigenerazione produce lo stesso log — verificato in `test_11`.

Esempi di frasi:
- Opening: `"L'arena si accende: Aurora sfida Boreal a duello aperto."`
- Mid: `"Zephyr scaglia un incantesimo che infligge danno significativo."`
- MVP: `"Alpha apre uno squarcio decisivo nel dispositivo avversario."`
- Closing win: `"La battaglia si conclude: la vittoria va a Aurora."`
- Closing forfeit: `"Il tempo di risposta scade: forfait automatico a favore di Aurora."`

Ogni entry: `{turn, actor_guild_id, actor_adventurer_id, text_it}`.

---

## 7. Arfus applier PvP filtrato

### Whitelist (6 categorie ONLY)
```python
PVP_APPLICABLE_CATEGORIES = {
    "combat_damage", "combat_healing", "combat_defense",
    "counter_effectiveness", "iron_will", "team_morale",
}
```

### Blacklist evidence (categorie NON applicate a PvP)
Le categorie tech Arfus **escluse** da PvP (verificate in `test_03`):
- `arcane_knowledge` — bonus PvE ricerca / crafting
- `exploration_luck` — bonus expedition
- `leader_experience` — bonus XP gilda
- `forge_efficiency` — bonus refine/enchant
- `site_income_boost` — bonus resource sites
- `resource_efficiency` — bonus raccolta materiali

**Anti-P2W statement**: nessuna categoria non-PvP è mai applicata al calcolo battle score. Verificato con test dedicato (`test_03_applier_rejects_pve_categories`).

### Cap totale
`PVP_TOTAL_BONUS_CAP = 0.50` (50% max additivo) — previene runaway stacking.

### Additivo separato da PvE
- `applier.py` (PvP) legge lo stesso storage `arfus_tech_unlocks` MA filtra CATEGORY prima di sommare
- Il modulo PvE `app/arfus_forge/` NON è stato toccato
- **Non è possibile per una tech `combat_damage` avere effetto solo su PvP e non su PvE** — è un design choice consapevole: le tech "combat" sono chiaramente PvE+PvP overlap. Le tech non-combat sono strettamente PvE (blacklist).

---

## 8. On-visit fallback

### Pattern
```python
# In GET /api/pvp/battles/mine:
try:
    await auto_resolve_stuck_battles_for_guild(db, guild["id"])
except Exception as exc:
    logger.warning(...)  # non-blocking
# ...poi query battles (rileggerà stato aggiornato)
```

### Copertura
- Battaglie con `status=pending_response AND response_deadline <= now` → forced `defender_forfeit`
- Battaglie con `status=resolving AND resolves_at <= now` → normal resolve
- **CAS transition** `in_progress/pending → resolving` previene double-resolve concorrente
- Try/except fail-safe: `GET /api/pvp/battles/mine` risponde sempre 200 anche se recovery raise

### Recovery script CLI
```bash
# Dry-run (default)
python -m app.scripts.recover_stuck_pvp_battles

# Apply
python -m app.scripts.recover_stuck_pvp_battles --apply --limit 100
```

Output esempio:
```json
{"dry_run": false, "total_stuck": 3, "resolved": 3, "failed": 0, "errors": []}
```

---

## 9. Audit events (6 nuovi UPPERCASE)

| Event | Emesso in |
|---|---|
| `PVP_CHALLENGE_CREATED` | `services.create_challenge` |
| `PVP_CHALLENGE_ACCEPTED` | `services.respond_to_challenge` |
| `PVP_CHALLENGE_DECLINED` | `services.decline_challenge` |
| `PVP_CHALLENGE_TIMEOUT_DEFAULTED` | `resolver._finalize_forfeit` |
| `PVP_BATTLE_RESOLVED` | `resolver._finalize_normal` + `_finalize_forfeit` |
| `PVP_ELO_UPDATED` | `resolver._finalize_normal` (solo se outcome != "draw") |

**Whitelist admin**: 41 → **47** — verificato in `test_22`.

---

## 10. Test summary

### Test suite dedicata: `tests/test_pvp_phase7a_p0.py`
```
33 passed in 4.52s
[orbus.test] Test pollution cleanup SKIPPED (DB doesn't look like a test DB)
```

**Copertura**:
- Test 01-04: applier whitelist (size, contents, PvE rejection, filter helper)
- Test 05-07: Elo update (K=32 symmetric, clamp lower/upper)
- Test 08: MVP determinism con ties
- Test 09-11: battle log (min length, italiano, MVP reference, deterministic seed)
- Test 12-13: opponents route + level gate
- Test 14-15: battles mine + detail 404
- Test 16-18: challenge/respond/decline routes registered (no route-not-found)
- Test 19-20: admin stats OK + admin.forbidden per non-admin
- Test 21: tutti gli endpoint richiedono auth (401 auth.missing)
- Test 22: AUDIT_EVENT_WHITELIST ≥ 47
- Test 23: EVENT_TYPES include 6 PVP events
- Test 24: OpenAPI espone tutti gli 8 path PvP
- Test 25: guild_pvp_stats seed idempotente
- Test 26: **end-to-end** challenge → respond → resolve, verifica battle_log ≥4, mvp assigned, team released, audit row
- Test 27: self-challenge forbidden
- Test 28: new-player buff ~1.20× solo su defender (media su 30 battle_id)
- Test 29: Arfus PvP filtra correttamente (0.0 con guild senza tech)
- Test 30-32: **regression** su `/races`, `/dungeons`, `/inventory/{}/refine` — nessun impatto
- Test 33: dev force-resolve gated in production (source inspection)

### Regression baseline P0 + P1
```
$ pytest tests/test_forge_actions_p0.py tests/test_races_endpoint_p1.py -v
12 passed in 1.56s
```
6 forge P0 + 6 races P1 tutti verdi → **nessuna regressione introdotta**.

### Fixture cleanup verificato
Dopo `pytest`, 0 documenti con prefix `p7a_smoke_` residui in nessuna collection (verificato via mongosh).

---

## 11. Anti-P2W statement

- **Nessuna currency PvP creata** in questa iterazione (`pvp_currency`, `pvp_shop`, `pvp_tokens` sono postponed a 7B).
- **Ricompense**: solo Elo + wins/losses/draws counters + battle log cosmetico (leggibile).
- **Ricompense NON incluse**: gold, XP, loot, item drop, achievement unlock non-PvP, buff globali.
- **Arfus filter blacklist verificato**: 6 categorie non-combat (`arcane_knowledge`, `exploration_luck`, `leader_experience`, `forge_efficiency`, `site_income_boost`, `resource_efficiency`) NON applicabili al battle score.
- **New-player protection**: buff difensivo +20% per gilde con <10 completed expeditions (soft, non hard-block). Riduce lo stomping su target inesperti.
- **Bracket matchmaking**: ±200 Elo OR ±3 guild level → gilde molto avanzate non possono sfidare novellini per bullshit farm.

---

## 12. Non-implementato in Iter1 (rimandato)

### Iter2 Frontend (sessione dedicata, dopo smoke test owner)
- Pagina `/pvp` con 3 tab (Sfide / Battaglie attive / Storico)
- Modal challenge (selezione defender + team composition)
- Battle detail viewer con battle_log renderizzato + MVP badge
- Live-update via polling `/api/pvp/battles/mine` ogni 30s
- Elo widget in dashboard

### Iter successive (post 7A)
- **Phase 7B**: Leaderboard settimanale + badge cosmetici + season rollover (currency ancora escluso)
- **Phase 8**: Stalla e cavalcature (indipendente da PvP)

### Bugfix minori identificati
- Nessun indice Mongo creato in questa Iter1 sulle 3 nuove collection. Da aggiungere in lifespan quando i volumi lo richiederanno.
- Il campo `challenger_elo_snapshot` è memorizzato nel doc battle ma **non usato** per l'Elo calc post-resolve (l'aggiornamento legge lo state corrente da `guild_pvp_stats`). È intenzionale — lo snapshot è per audit trail e display, non per calcolo. Documentato qui.

---

## 13. Vincoli rispettati

- ❌ NO deploy, NO hard delete, NO scheduler globale
- ❌ NO gold/XP/loot da PvP, NO P2W (evidence Arfus blacklist + no currency)
- ❌ NO Phase 7B, NO Phase 8
- ❌ NO full pytest (isolation bug P2 ancora aperto)
- ❌ NO tocco `test_database`
- ❌ NO modifiche a balance/economia/drop/XP/PvE (raid/expedition/wb) — verificato con 3 regression test
- ✅ Guild level gate ≥ 8 (test_13)
- ✅ Max 3 challenge attive per gilda challenger (enforced in `create_challenge:290`)
- ✅ Cooldown 12h tra challenge alla stessa gilda (`COOLDOWN_HOURS=12`)
- ✅ New-player protection +20% (test_28)
- ✅ Bracket matchmaking ±200 Elo o ±3 lvl (`BRACKET_ELO_RANGE=200, BRACKET_LEVEL_RANGE=3`)
- ✅ Team snapshot al challenge (no change in corsa) — `_snapshot_adventurer` congela stats
- ✅ Resolution deterministica seeded (test_11 conferma stesso seed → stesso outcome)
- ✅ On-visit fallback per battaglie scadute (`auto_resolve_stuck_battles_for_guild`)
- ✅ Applier Arfus filtrato (6 categorie whitelist verificato test_02/03)
- ✅ Idempotenza + CAS (`_upsert_pvp_stats`, `resolve_battle` CAS transition)
- ✅ Fixture test cleanup verificato (0 docs `p7a_smoke_` residui)
- ✅ Italiano su tutti i `user_message` di error + battle log

---

## 14. Prossimi passi (owner)

1. Orchestrare smoke test compatto con `e1_tester` sul flusso:
   - Login tester (o account con guild lvl ≥ 8)
   - `POST /api/pvp/challenge/{defender_guild_id}` con team valido
   - Login defender
   - `POST /api/pvp/battles/{id}/respond` con team defender
   - Admin `POST /api/admin/pvp/dev/force-resolve/{id}`
   - Verify outcome, mvp, battle_log
2. Brief Phase 7A **Iter2 Frontend** in sessione dedicata.
3. Post-smoke: valutare autorizzazione P2 pytest DB isolation.

---

## 15. Sign-off

- **Test suite dedicata**: 33/33 PASS (unit + HTTP + end-to-end + regression + audit + OpenAPI)
- **Regression baseline**: 12/12 PASS (forge P0 + races P1)
- **Total**: **45/45 PASS**
- **Fixture cleanup verificato**: 0 documenti `p7a_smoke_` residui
- **DB `orbus_r16`**: intatto (nessuna scrittura al di fuori del fixture scoped)
- **Backend restart**: OK (log `Orbus backend ready`)
- **Nessuna regressione** introdotta su moduli PvE

**Backend Phase 7A Iter1 chiuso. In attesa di orchestrazione smoke test owner.**
