# Round 16.3 — Final Report

## Stato: **OFFICIALLY CLOSED ✅**

**Data chiusura**: 01 Luglio 2026 (aggiornato con Phase 8 V1 il 01/07/2026)

Round 16.3 è formalmente sigillato. Il ciclo PvP (Phase 7A + Phase 7B) è chiuso end-to-end. Phase 8 V1 (Stalla — solo cosmetico) è chiusa in doppio Iter (Backend + Frontend). Totali sessione R16.3: **106/106 pytest PASS**, frontend smoke completi, disclaimer anti-P2W visibile ×5 (3 PvP + 2 Stalla), zero regression rilevata.

---

## Etichette esplicite

```
Round 16.3      — CLOSED ✅
Phase 1-7       — CLOSED ✅
Phase 8 V1      — CLOSED ✅
Phase 8 V2      — FUTURE / DESIGN REVIEW REQUIRED 🔴
```

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

**Phase 8 V1 — Stalla & Cavalcature (puramente cosmetico)** (Iter1 Backend + Iter2 Frontend)
- **Backend Iter1**: 28/28 pytest PASS (`test_stables_phase8_v1.py`)
  - **4 collezioni Mongo**: `mount_catalog`, `narrative_routes`, `guild_mount_ownership`, `narrative_route_completions` (+ ausiliaria `narrative_rewards_unlocked`)
  - Seed idempotenti su lifespan: 9 mount + 5 rotte
  - **9 endpoint** totali: 7 pubblici (`/api/stables/*`) + 2 admin (`/api/admin/stables/*`)
  - **4 audit events** UPPERCASE: `MOUNT_STARTER_CLAIMED`, `MOUNT_ACQUIRED`, `MOUNT_ACTIVE_SET`, `NARRATIVE_ROUTE_TRAVELED` → whitelist 50 → **54**
  - Anti-P2W hard V1: catalog ha `affects_combat/affects_economy/affects_ranking/affects_travel_time/can_be_sold_for_real_money = False` hardcoded + anti-drift override nel seed
  - Reward rotte narrative limitato a `cosmetic_badge | cosmetic_title | lore_entry`
- **Frontend Iter2**: build+lint puliti, mobile 375px 0px horizontal overflow
  - **4 componenti**: `Stables.jsx` (pagina hub 3 tab: Le Mie / Catalogo / Rotte Narrative), `MountCard.jsx`, `NarrativeRouteCard.jsx`, `StablesMiniCard.jsx`
  - Nav voce "Stalla" in sezione Gilda con badge NEW (`menu-stables`)
  - Dashboard mini-card integrata sotto `PvpSeasonMiniCard`
  - Anti-P2W disclaimer ×2 (box emerald full su Stables + micro-disclaimer su mini-card)
- **Catalog 9 mount**: 1 starter (`ronzino-di-strada`, domain `starter`) + 8 domain (uno per continente: `scarabeo-runico`, `cervo-lunare`, `lupo-delle-fronde`, `salamandra-di-efreto`, `segugio-cinereo`, `remora-tempestosa`, `ombra-sellata`, `grifone-delle-alture`)
- **Catalog 5 rotte narrative**: `sentiero-delle-fronde` (soe), `via-delle-alture` (aveol), `traccia-lunare` (velur), `passo-delle-ceneri` (efreto), `cammino-ombra` (ergolat). I 3 domini scoperti (ambash, irthe, nathos) sono riservati a Phase 8 V2.

---

## Anti-P2W verifica

### Backend
- **Whitelist Arfus PvP**: solo `combat_damage`, `combat_healing`, `combat_defense`, `counter_effectiveness`, `iron_will`, `team_morale`, capped al 50% totale
- **Blacklist esplicita**: categorie non-combat (arcane_knowledge, exploration_luck, market_bonus, ecc.) ignorate in resolver PvP
- **Cosmetici** (Phase 7B): tipologie limitate a `title | badge | frame`. Docstring `cosmetics.py` inizia con `ANTI-P2W GUARANTEE`. Descrizioni italiane contengono "puramente decorativi"
- **Test regression** `test_26_no_p2w_stat_impact_after_award`: asserta immutabilità di `guild.gold`, `guild.reputation`, `guild.level`, `guild.name`, `guild_pvp_stats.elo/wins/losses/draws` dopo `award_cosmetic()`

### Frontend
- **Disclaimer anti-P2W visibile ×5** (3 PvP + 2 Stables):
  1. `PvpSeasonOverview.jsx` footer full disclosure (data-testid `pvp-season-antip2w-disclaimer`)
  2. `PvpSeasonCosmetics.jsx` top notice emerald-bordered
  3. `PvpSeasonLeaderboardDetail.jsx` compact footer italic
  4. `Stables.jsx` footer full disclosure (data-testid `stables-antip2w-disclaimer`)
  5. `StablesMiniCard.jsx` micro-disclaimer italic (data-testid `stables-mini-antip2w`)

### Stables Anti-P2W hard (Phase 8 V1)
- Ogni mount ha esplicitamente `affects_combat=false`, `affects_economy=false`, `affects_ranking=false`, `affects_travel_time=false`, `can_be_sold_for_real_money=false` — verificato runtime da 2 test unit (`test_06_anti_p2w_flags_shape`, `test_09_get_catalog_returns_9_with_anti_p2w_flags`)
- Reward rotte narrative: solo `cosmetic_badge | cosmetic_title | lore_entry` — verificato runtime da 2 test (`test_05_narrative_routes_reward_is_cosmetic_only`, `test_22_reward_reference_is_cosmetic_only_in_db`)
- **Regression test esplicito** `test_20_no_p2w_stat_impact_after_claim` + `test_21_no_p2w_stat_impact_after_narrative_travel`: snapshot BEFORE/AFTER assertano immutabilità di `guild.gold`, `guild.reputation`, `guild.level`, `guild.name`, `guild_pvp_stats.elo/wins/losses/draws` dopo claim e dopo travel

---

## Smoke test finali

### Backend
| Suite | Result | Note |
|---|---|---|
| `test_pvp_phase7a_p0.py` | 33/33 PASS | Phase 7A backend |
| `test_pvp_season_phase7b_p0.py` | 31/31 PASS | Phase 7B backend + guard-rail |
| `test_forge_actions_p0.py` | 6/6 PASS | Regression baseline |
| `test_races_endpoint_p1.py` | 6/6 PASS | Regression baseline |
| `test_stables_phase8_v1.py` | 28/28 PASS | Phase 8 V1 backend (unit + HTTP + anti-P2W regression + admin) |
| **Totale sessione R16.3 Phase 7+8** | **106/106 PASS** | Zero regressione |

### Frontend
- Smoke targeted: 15/15 PASS (Phase 7A + 7B + fix badge NEW + Phase 8 V1 Stables)
- `yarn build` pulito (11.86s, ~+3.61 kB gzip JS aggiuntivi per Phase 8 V1)
- `yarn lint` pulito su tutti i file nuovi (4 file Phase 8: Stables/MountCard/NarrativeRouteCard/StablesMiniCard)
- Screenshot desktop 1920×800 + mobile 375×800 verificati (0px horizontal overflow)

---

## Cosa NON è stato implementato in Round 16.3

- **Phase 8 V2** (rotte narrative sui 3 domini restanti ambash/irthe/nathos + variante esplorativa con `-5% travel time` opzionale) — **DESIGN REVIEW REQUIRED**: il bonus travel time deve applicarsi SOLO a rotte narrative dedicate mai a farm loop
- **Notifications post-battle** (deferred a round successivo)
- **Storico stagioni completo su Leaderboard** — endpoint backend `GET /api/pvp-season/history/{n}` esiste, UI rimandata a P2
- **Phase 6.5**: consumo `hook_categories` da Guild Specialization
- **Refinement Ritual**, **Leaderboard Specialization enhancement**

---

## Debito tecnico residuo P3

1. **P3.1 Pytest HTTP admin bypass DB isolation** — HTTP admin tests colpiscono backend running su `orbus_r16` invece che `orbus_r16_test` (workaround idempotency-tolerant applicato in `test_stables_phase8_v1.py test_26`)
2. **P3.2 Startup handler cleanup** — `_seed_r163_phase3_startup` si ferma dopo Phase 4 (dead code o incomplete)
3. **P3.3 Schema drift Alchemist** — 3 doc `class_specializations` con `parent_class_slug` vs 30 con `class_slug` (naming inconsistente)
4. **P3.4 ESLint warning** `ClassHalls.jsx:244` (react-hooks/exhaustive-deps)
5. **P3.5 Guard-rail self-test mancante** — nessun test verifica che il guard-rail rifiuti DB name non-`_test`
6. **P3.6 Mobile viewport verification** — `browser-use` headless non ridimensiona viewport nel pod, serve workaround Playwright dedicato

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
- `/app/memory/round163_phase8_v1_iter1_backend_report.md` — **Phase 8 V1 backend (28/28 pytest)**
- `/app/memory/round163_phase8_v1_iter2_frontend_report.md` — **Phase 8 V1 frontend (4 componenti + anti-P2W ×2)**

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
