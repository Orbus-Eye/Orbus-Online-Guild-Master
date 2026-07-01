# Round 16.3 — Final Report

## Stato: **OFFICIALLY CLOSED ✅**

**Data chiusura**: 01 Luglio 2026

Round 16.3 è formalmente sigillato. Il ciclo PvP (Phase 7A + Phase 7B) è chiuso end-to-end con test backend 76/76 PASS, frontend 8/8 smoke PASS, disclaimer anti-P2W visibile ×3, e nessuna regression rilevata.

---

## Cosa include Round 16.3

### Recovery (post-incident 2026-07-01)
- Ripristino codice Round 16.x da `/app/backend/_legacy/` + `/app/frontend/src/_legacy/`
- Nuovo DB preview `orbus_r16` (con `test_database` conservato come snapshot naturale della Fase 1 accidentale)
- Ambiente confermato preview/dev isolato (`mongod` bind `127.0.0.1`)
- 233 endpoint OpenAPI restaurati, frontend production build OK

### Seed cataloghi statici (fine Fase 1)
- **11 classi base** (10 core + `alchemist`) + **30 specializzazioni R16** + 3 deprecate soft-flagged
- **50 razze** (30 common + 12 uncommon + 6 rare + 2 epic)
- **1672 class_halls** (11 halls × 152 gilde attive)
- **110 achievement catalog**
- **131 item tags** (100% coverage)
- 22 dungeons, 130 items, 13 enchants, 8 continenti, 12 event catalog, 8 resource catalog, 14 signature templates

### Migrazioni
- 177 avventurieri migrati da classi deprecate (`berserker`/`assassin`/`necromancer`) → `warrior`/`rogue`/`mage` + campo `specialization_slug` popolato

### Fix P0 (post-tester bug report)
- Raid on-visit fallback (già presente in `raids/__init__.py`, confermato non-blocker)
- Forgia 404 (5 route `/api/inventory/{id}/{action}` aggiunte)

### Fix P1 (gap catalogo + config)
- `/api/races` endpoint creato + test 6/6 PASS
- Nav "Achievement/Imprese" confermato presente
- Dungeon 22/22 esposti (feature gate legittima)
- `APP_BASE_URL` preview corretto
- **Fix trasversale badge NEW** nella nav (AppHeader + MobileMenuDrawer) — component `<NavBadge>` esportato + rendered in emerald+mono su desktop dropdown e mobile drawer

### Feature grandi pre-recovery (Phase 1..6, tutte CLOSED)
- Phase 1: **World Boss Alveora V1**
- Phase 2: **Mondo & 8 Mastocontinenti**
- Phase 3: **Eventi Continentali + Site Contracts** (passive income CAP-ped)
- Phase 4: **Continental Resources V0** (8 risorse + classifiche V0)
- Phase 5A: **Legendary Forge** (BOP items, stat cap +50%, pity system)
- Phase 5B: **Arfus Forge** (tech tree passivo, +30% stat cap)
- Phase 6: **Trade Pacts V0** + **Guild Specialization V0**

### Nuove feature Phase 7 (chiuse in questa sessione)

**Phase 7A — PvP Continentale 1v1** (Iter1 Backend + Iter2 Frontend)
- **Backend**: 33/33 pytest PASS
  - Elo K=32 clamp `[800, 2400]`
  - Gate `guild.level ≥ 8`
  - Max 3 sfide attive per gilda, cooldown 12h per coppia (challenger, defender)
  - Bracket ±200 Elo (ampliato a ±3 lvl gilda a lvl >12)
  - Team snapshot 5v5 al momento della challenge
  - Resolution deterministica `random.Random(seed=battle_id + role)`
  - On-visit fallback per timeout defaulted
  - Recovery CLI `recover_stuck_pvp_battles.py`
  - **Arfus applier filtrato PvP**: whitelist 6 categorie combat (`combat_damage`, `combat_healing`, `combat_defense`, `counter_effectiveness`, `iron_will`, `team_morale`), cap totale 50%
  - Blacklist esplicita categorie non-PvP (arcane_knowledge, exploration_luck, tempo_travel, ecc.)
  - 6 audit events UPPERCASE + admin whitelist 41 → 47
- **Frontend**: 4 pagine (`PvpOpponents`, `PvpChallenge`, `PvpBattles`, `PvpBattleReport`) + `PvpMiniCard` + `PvpGuildLevelGate` visivo lvl<8 + battle log narrativo italiano

**Phase 7B — Leaderboard settimanale + Cosmetici** (Iter1 Backend + Iter2 Frontend)
- **Backend**: 31/31 pytest PASS (30 P0 + 1 guard-rail leaderboard endpoint parity)
  - Snapshot settimanale + rollover on-visit (nessuno scheduler globale)
  - CAS lock `active → closing → finalized` idempotente
  - **24 cosmetici** (8 continenti × 3 tipi: `title` rank1, `badge` rank≤3, `frame` rank≤10)
  - Recovery CLI `recover_stuck_pvp_seasons.py`
  - 3 audit events UPPERCASE + admin whitelist 47 → **50**
- **Frontend**: 3 pagine (`PvpSeasonOverview`, `PvpSeasonLeaderboardDetail`, `PvpSeasonCosmetics`) + `PvpSeasonMiniCard` + nav voce "Stagione PvP" con badge NEW + disclaimer anti-P2W ×3

---

## Anti-P2W verifica

### Backend
- **Whitelist Arfus PvP**: solo `combat_damage`, `combat_healing`, `combat_defense`, `counter_effectiveness`, `iron_will`, `team_morale`, capped al 50% totale
- **Blacklist esplicita**: categorie non-combat (arcane_knowledge, exploration_luck, market_bonus, ecc.) ignorate in resolver PvP
- **Cosmetici** (Phase 7B): tipologie limitate a `title | badge | frame`. Docstring `cosmetics.py` inizia con `ANTI-P2W GUARANTEE`. Descrizioni italiane contengono "puramente decorativi"
- **Test regression** `test_26_no_p2w_stat_impact_after_award`: asserta immutabilità di `guild.gold`, `guild.reputation`, `guild.level`, `guild.name`, `guild_pvp_stats.elo/wins/losses/draws` dopo `award_cosmetic()`

### Frontend
- **Disclaimer anti-P2W visibile ×3**:
  1. `PvpSeasonOverview.jsx` footer full disclosure (data-testid `pvp-season-antip2w-disclaimer`)
  2. `PvpSeasonCosmetics.jsx` top notice emerald-bordered
  3. `PvpSeasonLeaderboardDetail.jsx` compact footer italic

---

## Smoke test finali

### Backend
| Suite | Result | Note |
|---|---|---|
| `test_pvp_phase7a_p0.py` | 33/33 PASS | Phase 7A backend |
| `test_pvp_season_phase7b_p0.py` | 31/31 PASS | Phase 7B backend + guard-rail |
| `test_forge_actions_p0.py` | 6/6 PASS | Regression baseline |
| `test_races_endpoint_p1.py` | 6/6 PASS | Regression baseline |
| **Totale sessione R16.3 Phase 7** | **76/76 PASS** | Zero regressione |

### Frontend
- Smoke targeted: 8/8 PASS (Phase 7A + 7B + fix badge NEW)
- `yarn build` pulito (11.56s, ~+13 kB gzip JS totali)
- `yarn lint` pulito su tutti i file nuovi
- Screenshot desktop 1280×800 + mobile 390×844 verificati

---

## Cosa NON è stato implementato in Round 16.3

- **Phase 8** (Stalla e cavalcature) — richiede design review conservativo anti-P2W dedicato prima dell'implementazione
- **Notifications post-battle** (deferred a round successivo)
- **Storico stagioni completo su Leaderboard** — endpoint backend `GET /api/pvp-season/history/{n}` esiste, UI rimandata a P2
- **Phase 6.5**: consumo `hook_categories` da Guild Specialization
- **Refinement Ritual**, **Leaderboard Specialization enhancement**

---

## Debito tecnico residuo P2

1. **Pytest DB isolation** (bug design in `/app/memory/bug_pytest_db_isolation.md`) — in lavorazione Iter B
2. **30 specializzazioni R16**: verifica collection reale (`adventurer_classes` ne mostra 14) — investigation Iter B
3. **`/api/forge/enchant-options` 404**: gap Forge P5A — verifica Iter B
4. **Ordering validazione POST PvP** (422 vs 403/404): refactor handler Iter B
5. **Warning ESLint** `ClassHalls.jsx:244` (react-hooks/exhaustive-deps): fix Iter B
6. **Startup handler** `_seed_r163_phase3_startup` che si ferma dopo Phase 4: investigation Iter B

---

## Raccomandazione prossima fase

1. **Chiudere debito tecnico P2** (Iter B — brief attivo)
2. **Design review anti-P2W** per Phase 8 (Stalla e cavalcature) con vincoli espliciti:
   - Cavalcature devono restare narrative/utility o gate free-to-earn
   - Nessun premium purchase, nessun cavallo con stat gameplay-impattanti
   - Se serve, restringere a soft-drop da World Boss / craft con costi non-premium
3. **Solo dopo review approvata**: implementare Phase 8

---

## File di riferimento

### Report Round 16.3
- `/app/memory/incident_recovery_report.md` — recovery post-incident
- `/app/memory/orbus_r16_seed_apply_report.md` — apply seed cataloghi
- `/app/memory/bug_p0_fixes_report.md` — fix P0
- `/app/memory/orbus_p1_gap_fixes_report.md` — fix P1
- `/app/memory/round163_badge_new_fix_report.md` — fix trasversale badge NEW
- `/app/memory/round163_phase7a_iter1_backend_report.md` — Phase 7A backend
- `/app/memory/round163_phase7a_iter2_frontend_report.md` — Phase 7A frontend
- `/app/memory/round163_phase7b_iter1_backend_report.md` — Phase 7B backend (+ sezione 15 micro-fix leaderboard endpoint parity)
- `/app/memory/round163_phase7b_iter2_frontend_report.md` — Phase 7B frontend

### Report fasi 1-6 (pre-esistenti)
- `/app/memory/round163_phase1_final_report.md`
- `/app/memory/round163_phase2_final_report.md`
- `/app/memory/round163_phase3_final_report.md`
- `/app/memory/round163_phase4_final_report.md`
- `/app/memory/round163_phase5A_final_report.md`
- `/app/memory/round163_phase5B_final_report.md`
- `/app/memory/round163_phase6_final_report.md`

### Docs di governance
- `/app/memory/orbus_world_roadmap.md` — roadmap fasi (aggiornata a Phase 7 CLOSED)
- `/app/memory/PRD.md` — Product Requirements Document (aggiornata a Round 16.3 CLOSED)
- `/app/memory/BUILD_RULES.md`, `PROD_DEPLOY_CHECKLIST_*.md`, `REFACTOR_LOG.md`
- `/app/memory/test_credentials.md` — credenziali test
