# Orbus Online: Guild Master — AUDIT SNAPSHOT (read-only)

> Generato: 2026-06-30 · scope: PREVIEW · modalità: solo lettura.
> **Nessuna modifica al codice/DB.** Tutte le evidenze provengono da
> `git`, `pytest --collect-only`, `mongosh`-equivalente Motor query, e
> grep sul codebase.

---

## 1. Stato generale del progetto

| Voce | Valore |
|---|---|
| Branch | `main` |
| Ultimo commit | `d295ea0 auto-commit for df00afbb-…` (auto-commit pipeline) |
| Stack backend | FastAPI 0.110.1 · Python 3.11 · Motor 3.3.1 · Pydantic 2.x |
| Stack frontend | React 19 · React Router 7.5 · Tailwind 3.4 · Axios 1.8 · Sonner 2.0 |
| Stack DB | MongoDB (preview cluster, 39 collections) |
| Auth | JWT HS256 + httpOnly cookie + CSRF double-submit (R11.1 Slice 2) |
| Servizi supervisor | `backend RUNNING`, `frontend RUNNING`, `mongodb RUNNING`, `mobile RUNNING` |
| Lint frontend | 0 errori, 0 warning su file polish R15 |
| Webpack | `Compiled successfully!` |
| OpenAPI | `/api/openapi.json` esposto → **146 path, 161 operazioni** |
| Deploy | Solo preview (no production) |
| LLM key | `EMERGENT_LLM_KEY` non presente (app non usa LLM) |
| Storage | Tigris keys presenti in `.env` ma **0 riferimenti** nel codice → integrazione dormiente |
| Email | `EMAIL_PROVIDER=smtp` configurato in `.env`; `core/email.py` supporta `smtp` + `resend` |

### Segreti in `.env` (solo nomi chiave, no valori)
`MONGO_URL`, `DB_NAME`, `CORS_ORIGINS`, `TIGRIS_ENDPOINT`, `TIGRIS_ACCESS_KEY_ID`,
`TIGRIS_SECRET_ACCESS_KEY`, `TIGRIS_BUCKET`, `JWT_SECRET`, `EMAIL_PROVIDER`,
`EMAIL_FROM`, `EMAIL_REPLY_TO`, `RESEND_API_KEY`, `SMTP_HOST`, `SMTP_PORT`,
`SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, `APP_BASE_URL`,
`SEND_WELCOME_EMAIL`, `APP_ENV`.

### Conteggio collection DB chiave
| Collection | Docs |
|---|---:|
| users | 3.434 |
| guilds | 12.617 |
| adventurers | 90.611 |
| adventurer_classes | 111 (12 attive) |
| items | 122 |
| inventory_items | 5.323 |
| equipped_items | 425 |
| dungeons | 32 |
| raids | 365 |
| expeditions | 3.843 |
| achievements_catalog | **110** |
| achievement_progress | 34 |
| audit_log | 169.169 |
| pvp_matches | 3 |
| pvp_defense_teams | 4 |
| seasons | 1 (`arena-preseason-2026` ATTIVA) |
| market_listings | 741 |
| guild_structures | 11.216 |
| recruitment_offers | 10.416 |
| consortiums | 234 |

---

## 2. Funzionalità implementate

| Area | Stato | File principali | API | Modelli | Problemi noti |
|---|---|---|---|---|---|
| Auth (register/login/logout) | ✅ | `auth/routes.py`, `auth/services.py`, `core/security.py`, `core/csrf.py` | `/api/auth/*` (login, register, csrf, logout, refresh, password-reset/{request,confirm}, me) | `users`, `refresh_tokens` (32.4K), `login_attempts`, `password_reset_tokens` | Doppio binario cookie+Bearer in transizione (Bearer fallback 14gg) |
| Creazione gilda | ✅ | `guilds/routes.py`, `guilds/services.py` | `/api/guilds` POST/GET, `/api/guilds/me` | `guilds` | — |
| Dashboard | ✅ | `pages/Dashboard.jsx`, `components/GuildProgressCard.jsx` | aggrega guild/me + achievements/summary | — | — |
| Avventurieri | ✅ | `adventurers/routes.py`, `pages/Adventurers.jsx` | `/api/adventurers` (6 endpoint) | `adventurers`, `adventurer_traits` | Roster oltre cap (vedi `roster_over_capacity_blocked` 53K log) gestito |
| Classi (catalog R15) | ✅ | `scripts/round15_seed_class_identity.py`, `pages/guide/ClassesAndStatsSection.jsx` | catalog endpoint | `adventurer_classes` (12 attive, **tutte con `primary_stat`**) | — |
| Statistiche | ✅ | `stats/`, `pages/StatsPublic.jsx`, `pages/guide/R15GuideSections.jsx` | `/api/stats/*` | doc inline classi | — |
| Tratti | ✅ | `pages/Adventurers.jsx` (preview), `components/TraitBadge.jsx`, `lib/api.getTraitPreview` | `/api/adventurers/{id}/trait-preview` | `adventurer_traits` | — |
| Reclutamento + Freeze Bench | ✅ | `recruitment/routes.py`, `pages/Recruitment.jsx` | `/api/recruitment/*` (7 endpoint) | `recruitment_offers` | — |
| Dungeon / spedizioni | ✅ | `dungeons/`, `expeditions/`, `pages/Dungeons.jsx`, `pages/ExpeditionNew.jsx` | `/api/dungeons`, `/api/expeditions/*` | `dungeons`, `expeditions`, `expedition_members` (10K) | — |
| Report spedizione (R15 separato) | ✅ | `expeditions/report_builder.py`, `pages/ExpeditionReport.jsx` | `/api/expeditions/{id}` | `expeditions.report` (loot + materials separati) | — |
| XP avventurieri | ✅ | `expeditions/services.py` (apply rewards) | inline | `adventurers.xp` | — |
| XP gilda (achievement-driven) | ✅ | `achievements/engine.py` `+ guilds.guild_xp` | `/api/achievements/summary` | `guilds.guild_xp, guild_level, achievement_points` | Solo trigger achievement (no fonte diretta gameplay) |
| Livello gilda (curva R15 Fase 3) | ✅ | `achievements/levels.py` (Lv1=0…Lv50=300K) | espone via summary | `guilds.guild_level` | — |
| Oro | ✅ | `guilds/services.py`, `audit/log.py` (`gold_credited` 2.9K · `gold_debited` 198) | inline su ogni transazione | `guilds.gold` | — |
| Inventario | ✅ | `inventory/`, `pages/Inventory.jsx` | `/api/inventory` | `inventory_items` | — |
| Oggetti + compat validator (R15) | ✅ | `equipment/compatibility.py` (153 LOC), `equipment/services.py` | `/api/adventurers/{id}/equip` | `items.class_tags/recommended_classes` (110/122 popolati) | — |
| Materiali + roll separato R15 | ✅ | `expeditions/material_drop_tables.py` (169 LOC) | inline a completion | `materials` (granted in `expedition.report.materials_found`) | — |
| Drop table oggetti | ✅ | `expeditions/loot_tables.py` | inline | inline su item | — |
| Achievement (110 catalog R15) | ✅ | `achievements/engine.py` (225 LOC, CAS), `routes.py`, `pages/Achievements.jsx` | `/api/achievements/{catalog,progress,summary}` | `achievements_catalog` (110), `achievement_progress` | **10 trigger_event seed ma hook gameplay parziale** (vedi §7) |
| Leaderboard / ranking | ✅ | `leaderboard/{services,routes,seasonal,multi_category}.py` | `/api/leaderboard/*` (4 endpoint) | aggregata; **`leaderboard_snapshots` collection MISSING** | Score>0 filter già attivo (`seasonal.py:255`); test_user esclusi |
| Admin / Game Health (R14) | ✅ | `admin/routes.py`, `admin/game_health_routes.py`, `admin/ops_routes.py`, `pages/Admin*.jsx` | `/api/admin/*` (23 endpoint) | usa flag su users/guilds | — |
| Audit log | ✅ | `audit/log.py` (whitelist 60+ event types) | nessuno (helper interno) | `audit_log` (169K rows) | **Manca: `ACHIEVEMENT_UNLOCKED`, `ITEM_DROPPED`, `MATERIAL_DROPPED`, `GUILD_XP_GAINED`, `ADVENTURER_XP_GAINED`, `LEADERBOARD_SCORE_UPDATED`** (vedi §7) |
| Test users / privacy LB | ✅ | `leaderboard/services.py:42`, `seasonal.py:47`, `multi_category.py:55` | filtri pre-aggregate | `users.is_test_user` | — |
| Email (SMTP/Resend) | 🟡 | `core/email.py` (2 provider supportati) | trigger su register / password-reset | nessuno | `SEND_WELCOME_EMAIL` flag in `.env` |
| Object storage (Tigris S3) | ❌ | `.env` configurato | nessuna | nessuno | Integrazione preparata ma 0 codice consumer |
| Forge / crafting | ✅ | `forge/`, `crafting/` | `/api/forge/*` (8), `/api/crafting/*` (2) | `recipes`, `enchants`, `item_sets` | Bound items + retire safety attivi |
| Mercato P2P | ✅ | `market/routes.py`, `auction/routes.py` | `/api/market/*` (5), `/api/auction/*` (5) | `market_listings` (741) | — |
| Shop NPC | ✅ | `shop/routes.py` | `/api/shop/*` (3) | `shop_daily_offers` (72) | — |
| PvP Arena | ✅ | `pvp/routes.py`, `pages/Arena.jsx` | `/api/pvp/*` (7) | `pvp_defense_teams`, `pvp_matches`, `season_participations` | Fix CSRF appena applicato (Arena.jsx → api instance) |
| Stagioni | ✅ | `seasons/routes.py` | `/api/seasons/*` (4) | `seasons`, `season_participations`, `season_rewards` | 1 stagione attiva |
| Consorzi | ✅ | `consortiums/routes.py` | `/api/consortiums/*` (7) | `consortiums` (234), `consortium_members` (234) | — |
| Squad / RaidBuilder | ✅ | `squads/routes.py`, `pages/SquadBuilder.jsx`, `pages/RaidBuilder.jsx` | `/api/squads/*` (5), `/api/raids/*` | `squads`, `raid_participants` (7.2K), `raid_dungeons` (8) | — |
| Chronicle / Chat | ✅ | `chronicle/`, `chat/` | `/api/chronicle/*`, `/api/chat/*` (4) | `chat_messages` (200) | — |
| Territory | ✅ | `territory/routes.py` | `/api/territory/*` (3) | `guild_structures` (11.2K) | — |
| Contracts / Quests | ✅ | `contracts/routes.py`, `quests/routes.py` | `/api/contracts/*` (6), `/api/quests/*` (6) | `contract_*`, `quest_*` | — |
| Specializzazione + Respec | ✅ | `training/routes.py` | `/api/training/*` (3) | inline su adventurer | Compensating pattern atomico R11.2 |
| Onboarding | ✅ | `onboarding/`, `components/OnboardingChecklist.jsx` | inline | — | — |
| Guide / Lore (R15 Fase 4) | ✅ | `pages/Guide.jsx`, `pages/guide/R15GuideSections.jsx` (7 sezioni) | nessuno (statico) | — | — |

---

## 3. Roadmap reality check

### Fase 1 — MVP (Auth + Guild + Dashboard)
**✅ COMPLETA — 100%**
- Auth JWT+cookie+CSRF · creazione gilda · dashboard · logout · password reset · welcome email.

### Fase 2 — Alpha (Avventurieri, Spedizioni, Inventario, Equip)
**✅ COMPLETA — 100%**
- 12 classi (con primary_stat, role_tags) · 30 tratti · roster cap + retire · 32 dungeon + 8 raid · expedition flow completo · drop separato (R15) · equip validator (R15) · XP debuff (R15).

### Fase 3 — Economia (Crafting, Forge, Mercato, Shop, Stagioni)
**🟡 IN CORSO — 85%**
- Fatto: forge (refine/enchant/reroll affix), crafting (recipes), market P2P, auction mirror, shop NPC daily offers, contracts, quests, streak.
- Mancante / parziale: market UX polish, balance audit lungo periodo, integrazione achievement `item_crafted`/`market_purchase` non sempre triggerata da hook.
- **Bloccante**: nessuno.

### Fase 4 — Ranking & Competizione (PvP, Leaderboard, Consorzi, Stagioni)
**🟡 IN CORSO — 80%**
- Fatto: pvp asincrono ranked (defense team + challenge + history), 1 stagione attiva, leaderboard multi-categoria + seasonal + privacy filter, consortiums, season rewards, league badges.
- Mancante: `leaderboard_snapshots` collection (storico non persistito) · achievement `leaderboard_rank_reached` ha seed ma no audit event collegato · ranking notification feed.
- **Bloccante**: nessuno (LB snapshot è P1, non blocca gameplay).

### Fase 5 — Community / Achievement / Guide (R15)
**✅ COMPLETA — 100%**
- 110 achievement seedati su 14 categorie · curva XP gilda Lv1-50 · pagina `/achievements` + dashboard card · Guide 7 sezioni · balance audit + final report.

### Fase 6 — Orbus Perfetto (Polish finale, copertura achievement, telemetria)
**🟡 IN CORSO — 30%**
- Fatto: i18n EN→IT polish (R15 Fase 4), display labels rarità/tag, CSRF fix Arena, lint clean, pytest 127/0.
- Mancante: ~10 achievement con `trigger_event` non ancora agganciato a hook gameplay (auction_purchase/sale, consortium_joined, item_disenchanted, leaderboard_rank_reached, season_league_reached, territory_upgraded, material_purchased, item_crafted parziale) · audit bridge per eventi player-facing (vedi §7) · telemetria balance live.
- **Bloccante**: nessuno.

---

## 4. Stato specifico classi/stat/equip

| Domanda | Risposta | Evidenza |
|---|---|---|
| Quali classi esistono? | 12 attive: `warrior, rogue, mage, priest, ranger, paladin, berserker, druid, necromancer, monk, bard, assassin` | `db.adventurer_classes.count({is_active:true})=12` |
| Ogni classe ha `primary_stat`? | **12/12 ✅** (strength/agility/intellect/faith) | query mongo conferma 4 distinti `primary_stat` mappati |
| Distribuzione ruoli | DPS=7, Tank=2, Healer=2, Support=1 | aggregate `$group role` |
| Stat spiegate in UI? | ✅ `pages/guide/ClassesAndStatsSection.jsx`, `R15GuideSections.jsx` (7 sezioni) | importato in `Guide.jsx:14, 1107` |
| Items con `class_tags`? | **110/122** (90%) | `count({class_tags:{$ne:[]}})=110` |
| Items con `recommended_classes`? | **110/122** | idem |
| `weapon_tags` popolati | 45/122 | armi |
| `armor_tags` popolati | 30/122 | armature |
| Items `universal:true` | **0** | nessun item universale (tutti vincolati) |
| Equip validator attivo? | ✅ `equipment/compatibility.py` (153 LOC) con livelli `block/warning/ok` + blacklist hard (no_heavy_armor, no_arcane_weapon) | importato in `equipment/services.py:316` |
| Debuff XP attivo? | ✅ `expeditions/xp_modifier.py` (169 LOC), `compute_xp_multiplier` hookato in `expeditions/services.py` | — |
| File chiave per estensioni future | `adventurer_classes` (seed), `equipment/compatibility.py` (regole), `expeditions/xp_modifier.py` (soglie), `scripts/round15_seed_class_identity.py` (re-seed) | — |

---

## 5. Stato drop materiali / oggetti

| Voce | Dettaglio |
|---|---|
| Roll oggetti | `expeditions/loot_tables.py` → `roll_loot_for_dungeon(dungeon, success)` |
| Roll materiali | `expeditions/material_drop_tables.py` → `roll_materials_for_dungeon` |
| Indipendenza | ✅ R15 Fase 2: **due roll indipendenti** (no slot sharing), entrambi con `secrets.SystemRandom` |
| Boost rates | +70% rispetto baseline, clipped a `RARITY_CAP` |
| Cap per rarità | common ≤ 85% · uncommon ≤ 55% · rare ≤ 25% · epic ≤ 15% · legendary ≤ 10% |
| Floor early-game | iron_shard, raw_leather, healing_herb floor 17% |
| Tier table | T1 (common only) · T2 (+uncommon) · T3 (+rare) · T4 5p elite (+epic dragon_essence) |
| Idempotenza | CAS via `expedition.status: in_progress → completing` (no double-roll) |
| Documentazione | `/app/memory/round15_material_drop_diff.md` + `round15_balance_audit.md` |
| API frontend | `pages/ExpeditionReport.jsx` mostra `OGGETTI TROVATI` + `MATERIALI TROVATI` separati |

---

## 6. Stato livello gilda e achievement

### Livello gilda (curva R15 Fase 3)
| Lv | Cumulativo XP |
|---:|---:|
| 1 | 0 |
| 2 | 100 |
| 5 | 900 |
| 10 | 5.000 |
| 20 | ~25.000 |
| 30 | ~75.000 |
| 50 | ~300.000 |

Source: `app/achievements/levels.py:26-53` (early hand-tuned + polinomio `5000 + (lvl-10)^1.93 * 230`).

### Achievement (110 totali)
| Categoria | Count |
|---|---:|
| classi_stats | 12 |
| consorzi | 3 |
| crafting | 8 |
| dungeon | 12 |
| economia | 6 |
| equipaggiamento | 10 |
| leaderboard | 5 |
| lore | 8 |
| meta_beta | 4 |
| primi_passi | 8 |
| pvp_stagioni | 8 |
| raid | 8 |
| roster | 10 |
| territorio | 8 |
| **TOTALE** | **110** |

### Schema
```
achievements_catalog: { slug, category, name_it, description_it,
  trigger_event, target, points, guild_xp_reward, is_active }
achievement_progress: { _id: "guild_id::slug", guild_id, slug,
  progress_current, completed_at, awarded_xp, ... }
```

### UI
- `/achievements` (`pages/Achievements.jsx`) ✅
- Dashboard card `components/GuildProgressCard.jsx` ✅ (montato in `Dashboard.jsx:189`)

### Trigger event distribution (catalog)
`dungeon_completed=23 · item_equipped=20 · adventurer_recruited=12 · raid_completed=11 · item_crafted=9 · territory_upgraded=8 · pvp_match_completed=7 · leaderboard_rank_reached=5 · market_purchase=4 · auction_purchase=1 · auction_sale=2 · season_league_reached=2 · guild_created=2 · material_purchased=2 · consortium_joined=1 · item_disenchanted=1`

### Trigger event con hook collegato (`evaluate_achievements` invocazioni)
✅ Hookati: `equipment/services.py:317` (item_equipped) · `guilds/services.py:108` (guild_created) · `recruitment/routes.py:70` (adventurer_recruited) · `raids/__init__.py:585` (raid_completed) · `expeditions/services.py:463` (dungeon_completed).
❌ **NON hookati** (seed presente, no codice gameplay): `item_crafted`, `auction_purchase/sale`, `consortium_joined`, `item_disenchanted`, `leaderboard_rank_reached`, `market_purchase`, `material_purchased`, `pvp_match_completed`, `season_league_reached`, `territory_upgraded`.

### Estensioni consigliate (top 8)
1. Hook `evaluate_achievements("item_crafted", …)` in `forge/services.py::craft_item`.
2. Hook `pvp_match_completed` in `pvp/services.py::challenge` resolver.
3. Hook `territory_upgraded` in `territory/services.py::upgrade_structure`.
4. Hook `market_purchase` + `auction_purchase/sale` in `market/services.py` e `auction/services.py`.
5. Hook `consortium_joined` in `consortiums/services.py::join`.
6. Hook `season_league_reached` su transizione liga in `seasons/services.py`.
7. Hook `leaderboard_rank_reached` post snapshot LB (Top 10/100/1000).
8. Hook `item_disenchanted` in `forge/services.py::disenchant_item`.

---

## 7. Stato audit log / audit bridge

| Voce | Dettaglio |
|---|---|
| File | `app/audit/log.py` (254 LOC) — helper `write_audit(db, ...)` |
| Whitelist | `EVENT_TYPES` frozenset (60+ event types canonici) |
| Privacy | `_sanitize_metadata()` redige password/token/email |
| Append-only | ✅ insert-only, mai update/delete |
| Idempotency key | ❌ NON enforce a livello audit (delegato alla CAS del caller) |
| Failure mode | "Swallow + log WARNING" (non blocca business flow) |
| Volume reale | 169.169 rows · 60+ event types attivi · top: `starter_roster_seeded`(71K), `roster_over_capacity_blocked`(53K), `adventurer_generated`(19K), `gold_credited`(2.9K), `equip_item`(675), `unequip_item`(153), `loot_awarded`(873) |

### Verifica eventi richiesti dall'utente

| Event richiesto | Presente? | Note / dove agganciare |
|---|---|---|
| `GUILD_XP_GAINED` | ❌ NO | Aggiungere `guild_xp_gained` allo whitelist + write in `achievements/engine.py` quando incrementa `guild_xp` |
| `ACHIEVEMENT_UNLOCKED` | ❌ NO | Aggiungere `achievement_unlocked` + write in `achievements/engine.py::_complete_achievement` (CAS branch) |
| `ITEM_DROPPED` | 🟡 PARZIALE | Esiste `loot_awarded`(873 rows) ma è generico squad-level. Per granularità per-item aggiungere `item_dropped` in `expeditions/services.py` dopo `roll_loot_for_dungeon` |
| `MATERIAL_DROPPED` | ❌ NO | Aggiungere `material_dropped` in `expeditions/services.py` dopo `roll_materials_for_dungeon` |
| `ITEM_EQUIPPED` | ✅ SÌ | `equip_item` (675 rows) in `equipment/services.py` |
| `ITEM_UNEQUIPPED` | ✅ SÌ | `unequip_item` (153 rows) idem |
| `ADVENTURER_XP_GAINED` | ❌ NO | Aggiungere `adventurer_xp_gained` in `expeditions/services.py::_apply_rewards` |
| `GOLD_CHANGED` | ✅ SÌ | `gold_credited` + `gold_debited` già canonici |
| `LEADERBOARD_SCORE_UPDATED` | 🟡 PARZIALE | `leaderboard_cache_rebuilt` (204) c'è ma per rebuild bulk; per-guild update mancante. Aggiungere `leaderboard_score_updated` in `leaderboard/services.py` |

### Gap principali audit (priorità)
1. **achievement_unlocked + guild_xp_gained** (P0) — necessari per ranking trasparenza.
2. **material_dropped + adventurer_xp_gained** (P1) — per analitica drop/progression.
3. **leaderboard_score_updated** (P2) — telemetria competitiva.

---

## 8. Test e qualità

| Voce | Valore |
|---|---|
| Test files | 78 |
| Test collected | **966** (`pytest --collect-only -q` → "966 tests collected in 0.58s") |
| Suite R12+R13+R14+R15 stabili | **127 passed, 1 skipped, 0 failed** in 4.78s |
| Suite full run (xdist) | Mostra failures intermittenti (`backend_phase17_round4_test::test_04_openapi_path_count` ASSERTION 161 vs expected → drift OpenAPI atteso). Confermati flaky già documentati in `FLAKY_TESTS_AUDIT.md` |
| Lint Python | ✅ pulito (R15 polish) |
| Lint JS | ✅ 0 warning/error |
| Webpack | ✅ Compiled successfully |

### Failure principale isolato
- `test_04_openapi_path_count`: hardcoded soglia path-count, dataset cresciuto a 146 path/161 op. **Aggiornare assert.**

### Aree con copertura adeguata
✅ R12 PvP seasons · R13a dungeon/raid lore · R13b seasonal increment · R13c market · R14 (beta readiness) · R15 phase 2 (equip+drop) · R15 phase 3 (achievement engine, levels).

### Aree con copertura debole
- Leaderboard multi-category (manca test su `leaderboard_snapshots` perché collection inesistente).
- Test users privacy (parziale: `chronicle/services.py` + `leaderboard/services.py` filtrano, no test e2e che valida che un test user NON appaia ai non-test).
- OpenAPI path count (1 test fragile da ribase).
- SMTP / email (manca smoke test invio Resend o SMTP — `core/email.py` non testato).
- Drop materiali Monte Carlo (esiste `scripts/round15_phase2_evidence_monte_carlo.py` ma non in pytest suite).
- Equip block hard (esiste `scripts/round15_phase2_evidence_hardblock_equip.py` ma non in pytest).
- Classi/statistiche (manca verifica 12/12 con primary_stat in pytest, solo verificato via DB).

### Test consigliati da aggiungere
1. `tests/backend_audit_bridge_test.py` — verifica scrittura `achievement_unlocked`, `guild_xp_gained`, `material_dropped`, `adventurer_xp_gained` quando attiveremo i hook (§7).
2. `tests/backend_classes_invariants_test.py` — invariant: ogni classe attiva ha `primary_stat`, `role`, `role_tags`.
3. `tests/backend_email_provider_test.py` — smoke test render template + provider switch (no invio reale).
4. `tests/backend_test_user_privacy_e2e_test.py` — un test user non appare in `/api/leaderboard/*` né in `/api/chronicle`.
5. `tests/backend_openapi_drift_test.py` — sostituisce il 17.4 fragile; verifica `len(paths) >= 140` invece di hardcoded.

---

## 9. Problemi, bug e debito tecnico

### Bug noti / TODO/FIXME in codice
- `grep -E 'TODO|FIXME|XXX'` su `/app/backend/app` → **1 occorrenza** sola (codebase molto pulito).
- Bug recente CSRF Arena ✅ FIXATO oggi (Arena.jsx ora usa istanza `api`).

### Sistemi incompleti
- **Achievement hook gaps**: 10 trigger_event seedati ma senza chiamata `evaluate_achievements` corrispondente nei domini target (vedi §6).
- **Audit bridge gaps**: 5 eventi player-facing (achievement_unlocked, guild_xp_gained, material_dropped, adventurer_xp_gained, leaderboard_score_updated) (vedi §7).
- **leaderboard_snapshots** collection non esistente → storico ranking non persistito.
- **Object storage Tigris** configurato ma 0 codice consumer.
- **`audit_logs` vs `audit_log`**: 2 collection coesistono (287 vs 169K rows). `audit_logs` è legacy/orfana → da archiviare.

### Duplicazioni / naming confusi
- `audit_log` (R3.D canonica) vs `audit_logs` (legacy, 287 rows).
- `inventory_items` (R6 canonica) vs `equipped_items` (R6.D snapshot equip).
- `market_listings` ed `auction` mirror — stesso store, 2 namespace API (per UX A/B). Documentato in `audit/log.py:48`.
- File `Arena.jsx` mescolava `axios` bare con `api` instance (risolto oggi).

### Codice fragile
- Test `test_04_openapi_path_count` (hardcoded count).
- Tigris ENV in `.env` senza fallback / feature flag → init fail silente se chiavi mancano.

### Rischi bilanciamento (sample numerici R15)
- Drop materiali +70% potrebbe inflazionare market a lungo termine (no sink crafting bilanciato).
- Guild XP curva: salto Lv9→Lv10 (1000 XP) vs Lv10→Lv20 (20.000) può scoraggiare mid-game.
- Achievement points + guild XP rewards: 110 achievement × ~50 points medi = ~5.500 punti totali; verificare con simulazione completion rate.

### Rischi sicurezza
- ✅ CSRF double-submit attivo (R11.1 Slice 2).
- ✅ httpOnly cookie auth (no localStorage token).
- ⚠️ Bearer fallback ancora attivo per 14gg (compatibilità tester) — log `auth.legacy_bearer_usage` 18+ rows visibili.
- ✅ Password bcrypt, mai loggate (`_sanitize_metadata` in audit).
- ⚠️ 32.428 `refresh_tokens` in DB — verificare TTL e revoke su logout.

### Rischi economia futura
- 0 sink "consumable" per oro (solo shop NPC + market P2P + forge cost).
- Auction mirror può creare deadlock liste se UX non chiarisce origine.
- `material_purchased` achievement seedato ma nessun NPC vende materiali → dead trigger.

### Rischi ranking/competizione
- `leaderboard_snapshots` mancante → impossibile dimostrare ranking storico ai giocatori.
- `pvp_matches=3` su preview → dataset reale troppo piccolo per validare bilanciamento.

---

## 10. Prossimi step consigliati (round di sviluppo)

### Round 16.A — Achievement hooks completion (P0)
- **Obiettivo**: chiudere i 10 trigger_event scoperti, raggiungere 100% hook coverage achievement engine.
- **Perché**: senza hook, le achievement seedate non si sbloccano mai → frustrazione e perdita di valore UX.
- **File**: `forge/services.py`, `market/services.py`, `auction/services.py`, `pvp/services.py`, `territory/services.py`, `consortiums/services.py`, `seasons/services.py`, `leaderboard/services.py`.
- **DB**: nessun nuovo modello (riusa `achievement_progress`).
- **API**: nessuna nuova (effetto su `/api/achievements/progress`).
- **Test**: `backend_round16a_achievement_hooks_test.py` (uno test per ogni trigger_event mancante).
- **Rischio**: BASSO (hook idempotente già esistente).

### Round 16.B — Audit bridge completion (P0)
- **Obiettivo**: aggiungere whitelist + scrittura di `achievement_unlocked`, `guild_xp_gained`, `material_dropped`, `adventurer_xp_gained`, `leaderboard_score_updated`.
- **Perché**: trasparenza economia + base per dashboard analitica admin.
- **File**: `audit/log.py` (whitelist), `achievements/engine.py`, `expeditions/services.py`, `leaderboard/services.py`.
- **DB**: nuovi event_type in `audit_log`.
- **Test**: `backend_audit_bridge_test.py`.
- **Rischio**: BASSO.

### Round 16.C — Leaderboard snapshots (P1)
- **Obiettivo**: persistere snapshot LB orario/giornaliero + esporre `/api/leaderboard/history`.
- **File**: nuovo `leaderboard/snapshots.py` + scheduler in `core/lifespan.py`.
- **DB**: nuova collection `leaderboard_snapshots`.
- **API**: `GET /api/leaderboard/history?category=…&since=…`.
- **Test**: `backend_leaderboard_snapshots_test.py`.
- **Rischio**: MEDIO (scheduler).

### Round 16.D — Test consolidation + flaky cleanup (P1)
- **Obiettivo**: fixare `test_04_openapi_path_count`, ribase `FLAKY_TESTS_AUDIT.md`, full suite 0 fail.
- **File**: `tests/backend_phase17_round4_test.py`, vari.
- **Rischio**: BASSO.

### Round 17 — Economia balance pass (P1)
- **Obiettivo**: gold sink consumable (potion shop, fast-travel, structure repair), market tax progressivo, recipe tier rebalance.
- **File**: `shop/services.py`, `market/services.py`, `forge/recipes.*`.
- **Test**: simulazione 30gg in pytest.
- **Rischio**: MEDIO (impatta player economy).

### Round 18 — Object storage Tigris (P2)
- **Obiettivo**: agganciare Tigris S3 per assets utente (avatar gilda, screenshot raid).
- **File**: nuovo `core/storage.py` + `guilds/avatars_routes.py`.
- **Rischio**: BASSO.

### Round 19 — Telemetria balance live (P2)
- **Obiettivo**: dashboard admin `/admin/balance` con metriche live (drop rate medio, gold flow, achievement completion %).
- **Rischio**: BASSO.

### Verifica priorità utente
| # | Voce | Stato |
|---|---|---|
| 1 | Guida classi/stat | ✅ R15 Fase 1 |
| 2 | Stat principali per classe | ✅ R15 Fase 1 |
| 3 | Equip vincolato | ✅ R15 Fase 2 |
| 4 | Debuff XP | ✅ R15 Fase 2 |
| 5 | Roll separato | ✅ R15 Fase 2 |
| 6 | Drop +70% | ✅ R15 Fase 2 |
| 7 | Achievement estesi | ✅ R15 Fase 3 (seed 110) |
| 8 | XP gilda da achievement | ✅ R15 Fase 3 |
| 9 | Audit bridge | 🟡 Parziale — 5 gap critici (§7) → Round 16.B |
| 10 | Economia/crafting/mercato | ✅ Funzionante, polish in Round 17 |

---

## 11. Output finale sintetico

| Fase | % Completamento |
|---|---:|
| Fase 1 — MVP | **100%** |
| Fase 2 — Alpha | **100%** |
| Fase 3 — Economia | **85%** |
| Fase 4 — Ranking | **80%** |
| Fase 5 — Achievement/Guide (R15) | **100%** |
| Fase 6 — Orbus Perfetto | **30%** |

**Fase reale corrente**: chiusura Round 15, ingresso Round 16 (Achievement hooks + Audit bridge).

**Prossima milestone consigliata**: Round 16.A + 16.B in parallelo → coverage hook 100% + audit bridge completo. Stima 2-3 giorni dev + 1 giorno test.

### Top 10 task tecnici prioritari (ora)
1. **[P0]** Hook `evaluate_achievements` su 10 trigger_event non agganciati (§6).
2. **[P0]** Aggiungere `achievement_unlocked` + `guild_xp_gained` ad audit whitelist + write (§7).
3. **[P0]** Aggiungere `material_dropped` + `adventurer_xp_gained` ad audit (§7).
4. **[P1]** Persistere `leaderboard_snapshots` (storico ranking).
5. **[P1]** Fixare `test_04_openapi_path_count` (drift soglia).
6. **[P1]** Archiviare collection orfana `audit_logs` (287 rows legacy).
7. **[P1]** Aggiungere test invariant `classi 12/12 con primary_stat`.
8. **[P2]** Verificare TTL/revoke su `refresh_tokens` (32K rows).
9. **[P2]** Smoke test SMTP/Resend in `core/email.py`.
10. **[P2]** Agganciare Tigris S3 (env già pronti, 0 codice consumer).

---

**Audit read-only completato. Nessuna modifica al codice o al DB.**

---

## Round 16.1 closed — 2026-06-30

**Game Clarity Pass — delivered**

1. **Dashboard V2** — `/api/dashboard/{suggestions,onboarding,daily-loop}` with bilingual data-driven cards (NextActions, OnboardingChecklistV2, DailyLoopCard) + graduation rule (`dismissed_implicit` when `guild_level≥3` OR `completed_expeditions≥3`).
2. **Class Halls UI** — full rewrite of `/class-halls` (11 halls incl. Alchemist, KPI top-right, Top Members, specs grid, bonus placeholder for R16.A) backed by enriched `GET /api/class-halls` via `enrich_halls_for_ui`.
3. **Auto-Equip improvements** — bilingual structured `reasons[]` + `unchanged_slots_detail[]` + `score_delta` + `primary_stat`; inline `AutoEquipReport` panel in `AdventurerDetailModal` (`equipped_items` collection is source-of-truth).
4. **Mobile Nav** — 5-slot bottom nav + 8-section drawer (Gilda, Avventurieri, Missioni, Economia, Competizione, Social, Guida, Account), no horizontal scroll, active state highlighted (verified DevTools 390×844 by user).
5. **Guide expansion** — 3 new sections (Daily Loop, Team Composition, Roster Filters); plus FE features `RosterFilterBar`, `DungeonPreviewModal`, Expedition Report `WhyNarrativeSection` (bilingual `narrative_it/_en`).

**Verification**: 27/27 pytest (R16.1 P1=7, P2=7, P3=6, Phase14.4=5, dev-seed=2) · E2E 4/4 by `e1_tester` + DevTools mobile audit by user · 0 economy/PvP/balance changes · 0 hard deletes.

**Auto-seed (preview/dev only)**: `tester@orbus.test` (admin) + `clean_onboarding@orbus.test` (pristine onboarding fixture). Idempotent, gated on `APP_ENV != "production"`. Implemented in `seeds/seed_runner.py::seed_dev_clean_onboarding_account`.

**OpenAPI baseline**: replaced fragile hard-coded count test with `tests/baselines/openapi_paths_round161.txt` snapshot (155 paths) + drift-resistant superset assertion.

**Recommendation for next round**: R16.A — Achievement Hooks (close the 10 trigger_event gaps noted in §6/§7 above, with side-task `onboarding.graduated` audit event).


---

## Round 16.A closed — 2026-06-30

**🟢 OFFICIALLY CLOSED ✅** — Sigillata post verifica E2E `e1_tester` 3/3 PASS.

**Achievement Hooks Coverage + Audit Bridge + Admin Read-Only Audit Dashboard — delivered**

### Riassunto 5 punti

1. **Phase 1 — Trigger Emission Layer**: **10 trigger_event WIRED** (`item_crafted`, `market_purchase`, `auction_purchase`, `auction_sale`, `consortium_joined`, `season_league_reached`, `item_disenchanted`, `material_purchased`, `pvp_match_completed`, `territory_upgraded`) + **1 DEFERRED** (`leaderboard_rank_reached`, feature-gated, schedulato R16.B). Persistenza idempotente in `trigger_emissions`.
2. **Phase 2 — Audit Bridge**: 3 audit event idempotenti (`achievement_unlocked`, `guild_xp_gained`, `onboarding_graduated`) scritti in `audit_log` + nuovo helper `add_guild_xp(db, guild_id, amount, *, source, source_id, points_delta)` in `app/achievements/engine.py` come unico entry-point auditato per credito XP gilda.
3. **Phase 3 — Admin Read-Only Audit Dashboard**: 3 nuovi endpoint sotto `/api/admin/audit/*` (trigger-emissions, events whitelist-guarded, summary con clamp 720h) + nuova pagina `pages/AdminAudit.jsx` (3 tab IT) su `/admin/audit`. Sweep `add_guild_xp` su `app/expeditions/services.py`: verificato statico (0 occorrenze `guild_xp`, no-op richiesto).
4. **Total: 60 test PASS** = 58 backend pytest (R16.A P1+P2+P3 = 29 + 1 skipped, R16.1 P1+P2+P3 = 20, Phase 14.4 = 5, dev-seed = 2, + skipped feature-gated) **+ 3 E2E browser** verificati da `e1_tester` (admin gate 403/200, idempotenza onboarding_graduated one-shot, whitelist filter 400 con `allowed[]` nella response).
5. **0 regressioni R16.1** · 0 hard delete · 0 economy/PvP/balance change · solo preview (no deploy).

### Evidenze E2E browser (e1_tester)
- Test 1: 403 per non-admin su 3/3 endpoint; UI 3 tab IT con counter `36 achievement_unlocked` + `4880 XP totale guild_xp_gained`.
- Test 2: 1 sola riga `onboarding_graduated` post re-visit dashboard (idempotenza one-shot confermata).
- Test 3: filtro whitelist `event_type=hacker_event` → 400 con `allowed: [achievement_unlocked, guild_xp_gained, onboarding_graduated]`.

### Hard caps audit dashboard
`MAX_LIMIT=200`, `MAX_WINDOW_HOURS=720` (30 giorni), whitelist hard-coded sui 3 event_type R16.A.

**Recommendation for next round**: **R16.B — Audit Coverage Extension + Sweep XP Round 2**. Aggiungere `material_dropped`, `adventurer_xp_gained`, `leaderboard_score_updated` ad audit whitelist; sweep `add_guild_xp` su quests/contracts/seasons (4-5 code path identificate); persistere `leaderboard_snapshots` (storico ranking). Stima 1.5-2gg dev + 0.5gg test. R16.C (QoL polish — smooth-scroll guide, lock-in spec UI, CSV export admin audit) resta P2.

---

## Hotfix R16.1.1 closed — 2026-06-30

**🟢 OFFICIALLY CLOSED ✅** — Post-verifica utente DevTools iPhone 14 (Forge mobile) + `e1_tester` 6/6 sub-check PASS (Desktop menu).

1. **Raid recovery**: 28/28 raid stuck `broken-bastion-siege` risolti idempotentemente (script CLI `recover_stuck_raids.py --apply`), 580 avventurieri liberati, 29 audit `raid_recovered` (28 + 1 on-visit fallback). On-visit fallback integrato in `GET /api/raids` e `GET /api/raids/{id}`.
2. **Forge mobile visibility**: `Forge.jsx` riscritto — `pb-32 md:pb-6` per bottom-nav clear, `min-h-[44px]` tap target Apple HIG, auto-scroll operation panel su selezione, confirm button `w-full md:w-auto` full-prominence. PASS confermato in verifica utente DevTools iPhone 14 (viewport 390×844).
3. **Desktop menu click-only**: `AppHeader.jsx` refactor — lifted `openId` state, marker `data-dropdown-region`, listener `click` post-bubble, rimosso `onMouseEnter` auto-switch hover (root cause del conflitto atomic switch). Pattern GitHub/Linear/GitLab-style. 6/6 sub-check E2E `e1_tester` PASS.
4. **Test coverage**: 65/65 pytest PASS (R16.1 + R16.A + R16.1.1 raid recovery [7 tests] + Phase 14.4 + dev-seed, 1 skipped feature-gated). 0 regressioni.
5. **Vincoli rispettati**: NO deploy, NO hard delete, NO cambi a economia/XP/drop rate/balancing/PvP. Recovery riusa logica `complete_raid` deterministic (rng seeded by raid_id). Solo preview.

**Prossimo round schedulato**: R16.3 Phase 1 — World Boss V1 Alveora (in esecuzione).

---

## R16.3 Phase 1 ready-to-verify — 2026-06-30

**🟡 READY FOR E2E VERIFICATION** — In attesa `e1_tester` per verifica browser finale. Backend + frontend + test tutti verdi.

**World Boss V1 Alveora — delivered**:

1. **Backend module** `app/world_boss/__init__.py` (~450 righe) — compact single-file con seed idempotente Alveora catalog + `counter_mind_control` counter (append-only), `THREAT_COUNTER_MAP` locale (no modifica seed R16.0), `resolve_stuck_world_boss_event()` CAS-protected, on-visit fallback, 10 endpoint (`/api/world-boss/*` 6 public + `/api/admin/world-boss/*` 4 admin).
2. **Idempotenza CAS-first** (lezione R16.1.1): CAS lock su status transition (`active → resolving`) + CAS su reward grant (`reward_granted={"$ne": True}`). Retry non duplica mai reward/audit/release. Recovery script CLI `recover_stuck_world_boss_events.py` con `--dry-run/--apply/--event-id`.
3. **Formula contributo**: `int(base_power * (1 + matched_counters * 0.15) * (1 + (phase-1) * 0.2))`. Solo lettura di `power` avv esistenti, nessuna modifica a economia/drop/XP. Reward = 3 event currency (`filo_lunare_spezzato`, `frammento_obelisco_vuoto`, `eco_della_luna_morta`) + oro pool; tutte `is_tradeable=true, can_be_sold_for_real_money=false`. Nessun leggendario diretto, zero P2W.
4. **Frontend** 3 pagine mobile-first: `WorldBoss.jsx` (lista), `WorldBossEvent.jsx` (dettaglio + send-team + ranking), `WorldBossReport.jsx` (report finale). Nav integrata sotto Missioni con badge "NEW". `pb-32 md:pb-8`, `min-h-[44px]` tap target, `w-full md:w-auto` CTA. ESLint clean, webpack `Compiled successfully`.
5. **Test coverage**: 17 pytest PASS + 1 skipped by design (T12 tester exclusion, deferred) in `backend_round163_phase1_test.py`. Regression suite completa **82 passed, 2 skipped, 0 failed** (R16.1 P1+P2+P3 + R16.A P1+P2+P3 + R16.1.1 + R16.3 P1 + Phase 14.4 + dev-seed). Zero regressioni. Target minimo utente 65+ ampiamente superato.

**Roadmap doc creato**: `/app/memory/orbus_world_roadmap.md` con Phase 1 (in esecuzione) + Phase 2-8 (future: Mondo/continenti, gilde vicine, risorse, Forgia Leggendaria, patti, PvP continentale, cavalcature). Nessuna Phase 2+ implementata.

**Audit events aggiunti**: `WORLD_BOSS_EVENT_CREATED/STARTED/RESOLVED/TEAM_RELEASED`, `WORLD_BOSS_JOINED`, `WORLD_BOSS_CONTRIBUTION_RECORDED`, `WORLD_BOSS_REWARD_GRANTED`. Whitelist estesa in `audit/log.py`.

**Next round proposto**: **R16.4 Phase 2 — Mondo & 8 mastocontinenti** (catalog, guilds.continent_slug, scelta post-first-raid, storico trasferimenti, UI Mondo). Stima 2-2.5gg dev + 0.5gg test.

---

## R16.3 Phase 1 closed — 2026-07-01

**🟢 OFFICIALLY CLOSED ✅** — World Boss V1 Alveora delivered.

1. **10 endpoint** (`/api/world-boss/*` 6 public + `/api/admin/world-boss/*` 4 admin) idempotenti CAS-protected + on-visit fallback + script CLI recovery.
2. **Whitelist audit R16.A** estesa append-only con 7 event UPPERCASE `WORLD_BOSS_*`; 400 filter test PASS.
3. **Branch reward `completed`** verificato end-to-end: currency `+3/+2/+1`, oro +100k, squadra rilasciata, idempotency confermata su retry.
4. **86 test pytest PASS + 2 skipped** (R16.3 P1: 21 test compresi 4 T25-T28 branch completed, R16.A P1-P3, R16.1 P1-P3, R16.1.1, Phase 14.4, dev-seed). Static mobile CSS check PASS (pb-32, min-h-44, w-full md:w-auto, no scroll-x forzato).
5. **HUMAN QA UI mobile viewport 390x844 deferred** al playtest finale al termine di R16.3 (Mondo completo). **Next**: R16.3 Phase 2 — Mondo & 8 mastocontinenti V1 (in esecuzione).

---

## R16.3 Phase 2 ready-to-verify — 2026-07-01

**🟡 READY-TO-VERIFY** — Mondo & 8 Mastocontinenti V1 delivered.

1. **Backend `app/world/__init__.py`** (~460 righe) single-file: seed idempotente 8 continenti (ambash/velur/soe/efreto/irthe/nathos/ergolat/aveol), access gate primo raid completed, cooldown 30gg UTC su change, CAS flip active→archived, history append-only. **NO hard delete** verificato T21.
2. **9 endpoint** (`/api/world/*` 6 pubblici: overview/continents/get/join/change/neighbors + `/api/admin/world/*` 3 admin: stats/dev-grant-first-raid/toggle). Dev grant gated `APP_ENV != production`.
3. **3 nuovi audit event UPPERCASE** (`WORLD_CONTINENT_JOINED`, `WORLD_CONTINENT_CHANGED`, `WORLD_ACCESS_GRANTED`) in `EVENT_TYPES` + `AUDIT_EVENT_WHITELIST` admin filter.
4. **Frontend mobile-first**: `pages/World.jsx` (blocked/no-continent/with-continent), `pages/WorldContinent.jsx`, `pages/WorldNeighbors.jsx`, `components/WorldMiniCard.jsx` in Dashboard V2, nav "Mondo" sezione con badge NEW, modal cooldown 30gg. ESLint clean, webpack `Compiled successfully!`.
5. **Test**: **22/22 PASS** in `backend_round163_phase2_test.py`. Regression totale **108 passed / 2 skipped / 0 failed**. Zero cambi economia/XP/drop/PvP/premium. Puro flavor + social.

**Next round proposto**: R16.3 Phase 3 — Eventi continentali admin + Incarichi di Sede (entrate passive con cap).

---

## R16.3 Phase 2 sealed & Phase 3 ready-to-verify — 2026-07-01

**Phase 2 (Mondo & 8 Mastocontinenti)** — 🟢 **OFFICIALLY CLOSED ✅** dopo verifica `e1_tester` 4/4 PASS (access gate, join, change 30gg, neighbors + audit whitelist). WARN filtro `is_active` sui continenti pubblici confermato come design. Tester account riportato a `ambash` pulito via nuovo `app/scripts/reset_test_account_world_state.py` (permanente, gated `APP_ENV != production`).

**Phase 3 (Eventi Continentali + Incarichi di Sede V1)** — 🟡 **READY-TO-VERIFY**:

1. **Backend 2 moduli**: `app/world_events/__init__.py` (~340 righe: seed 12 eventi, instances CAS, on-visit fallback expire) + `app/site_contracts/__init__.py` (~340 righe: config singleton, ledger daily unique_key, formula trasparente, claim CAS). Registrati in `app_factory.py` con seed a boot.
2. **12 endpoint**: `/api/world-events/{continent/{slug}/active,mine}` + `/api/site-income/{today,claim,history}` (5 public); `/api/admin/world-events/{create,catalog,activate,expire,all}` + `/api/admin/site-income/{config,stats}` (7 admin, 403 non-admin, dev routes gated `APP_ENV != production`).
3. **5 nuovi audit event UPPERCASE**: `CONTINENT_EVENT_CREATED/ACTIVATED/EXPIRED`, `SITE_INCOME_CLAIMED`, `SITE_INCOME_CONFIG_UPDATED` — presenti in `EVENT_TYPES` + `AUDIT_EVENT_WHITELIST` admin filter.
4. **Frontend mobile-first**: `pages/WorldEvents.jsx` (evento attivo con modifier badge trasparente), `pages/SiteContracts.jsx` (breakdown giornaliero + claim CTA + storico 7gg), `components/SiteIncomeMiniCard.jsx` in Dashboard, `components/ContinentEventBanner.jsx` slim banner. Nav +2 voci (Eventi sotto Mondo, Incarichi di Sede sotto Gilda). Modificatori mostrati +/-X% esplicito (green/red/amber).
5. **Test**: **28/28 PASS** in `backend_round163_phase3_test.py`. Regression totale **136 passed / 2 skipped / 0 failed** (108 pre-esistenti + 28 Phase 3). Cap conservativi verificati: 20 oro/g @ lv 1, 65 @ lv 10, 500 hard cap. Zero regressioni. Nuovo recovery script `app/scripts/expire_stuck_continent_events.py` con `--dry-run/--apply`.

**Vincoli rispettati**: NO deploy · NO hard delete (T25) · NO scheduler globale · NO P2W (cap uguale per tutte) · NO cambi economia/XP/drop/PvP fuori site income (che è comunque piccolo vs raid). Modificatori esposti trasparentemente.

**Report finale**: `/app/memory/round163_phase3_final_report.md` (14 sezioni).

**Next round proposto**: R16.3 Phase 4 — Risorse continentali (8 slug) + classifiche continentali basiche.

---

## R16.3 Phase 3 closed — 2026-07-01

**🟢 OFFICIALLY CLOSED ✅** — Eventi Continentali V1 + Incarichi di Sede delivered.

1. **12 endpoint** (5 pubblici + 7 admin), 2 moduli separati, seed 12 eventi + config idempotenti. Formula site income trasparente (base 20 oro/g @ lv1 → hard cap 500 oro/g).
2. **5 nuovi audit event UPPERCASE** in whitelist admin filter (`CONTINENT_EVENT_CREATED/ACTIVATED/EXPIRED`, `SITE_INCOME_CLAIMED`, `SITE_INCOME_CONFIG_UPDATED`).
3. **Frontend mobile-first** 4 file + nav +2 voci. Modificatori esposti con badge trasparente `+/-X%`.
4. **28 pytest PASS**. Regression 136 PASS · 2 skipped · 0 fail. Recovery script `expire_stuck_continent_events.py`. Cleanup dev script `reset_test_account_world_state.py`.
5. **E2E `e1_tester` 4/4 PASS**. 2 WARN chiariti: (a) `level_bonus=15` è formula corretta con `guild_level=4` (non il campo legacy `level`); (b) presence null post-pytest → riesecuzione script reset → tester@ambash `change_count=0`, `next_change=2026-07-31`. **Next**: R16.3 Phase 4 — Risorse continentali (8 slug) + classifiche continentali V0.

---

## R16.3 Phase 4 ready-to-verify — 2026-07-01

**🟡 READY-TO-VERIFY** — Risorse Continentali V0 (8 slug) + Classifiche Continentali V0 delivered.

1. **Backend `app/resources/__init__.py`** (~714 righe compact single-file): seed idempotente 8 risorse (5 epic + 3 rare, una per continente), missioni 30 min / 20 oro / team 3 avv idle, CAS `_resolve_mission` idempotente, on-visit expiry + CLI recovery, item mirror in `items` collection con `item_type="material_continental"` per riuso inventory infrastructure. Formula drop CONSERVATIVE: base 3% epic / 5% rare + max +10% event bonus (solo eventi `site_income_pct > 0`).
2. **Leaderboards V0**: 2 tipologie (`resource_gathering_count`, `site_income_total`), 7gg rolling window, freschezza 24h, top 20 per continente. Snapshot immutabili in `continent_leaderboard_snapshots`, on-visit compute (no scheduler). Read-only, ZERO reward economico.
3. **11 endpoint** (7 pubblici sotto `/api/resources/*` e `/api/continent-leaderboards/*` + 4 admin sotto `/api/admin/resources/*` e `/api/admin/continent-leaderboards/*`). Admin 403 non-admin. Dev grant gated `APP_ENV != production`. Recovery script `recover_stuck_resource_missions.py` con `--dry-run/--apply`.
4. **5 nuovi audit event UPPERCASE**: `RESOURCE_MISSION_STARTED/COMPLETED/FAILED`, `RESOURCE_GRANTED`, `LEADERBOARD_SNAPSHOT_COMPUTED` — presenti in `EVENT_TYPES` + `AUDIT_EVENT_WHITELIST` admin filter.
5. **Frontend mobile-first**: `pages/{Resources,ResourceGather,ResourceMissions,ContinentLeaderboards}.jsx` + nav +2 voci (Risorse sotto Gilda, Classifiche sotto Mondo). `pb-32 md:pb-6`, `min-h-[44px]`, `w-full md:w-auto`, badge event modifier trasparente. ESLint clean, webpack `Compiled successfully!`.

**Test**: **30/30 PASS** in `backend_round163_phase4_test.py`. Regression bundle R16.x + Phase14.4 + dev-seed: **208 passed / 2 skipped / 2 failed**. Le 2 failure sono debito legacy R16.0 (966 gilde legacy senza alchemist hall, 6336 avventurieri legacy senza `race_slug` — pre-esistenti al mio Phase 4, indipendenti dai test aggiunti). Zero regressioni Phase 4.

**1 bug scoperto e risolto durante Phase 4** (solo in test, no produzione):
- `test_adventurers_released_after_resolve` (T12) originario contava `busy` su tutti gli avventurieri della gilda dopo test sintetici con `adventurers:[]` che non lockavano nulla → assert impossibile causa mission reale da T05. Riscritto in modo semantico: crea missione con lock esplicito → resolve → verifica release. Zero modifiche al codice produttivo `_resolve_mission` (già corretto).

**Task A investigato**: 2 WARN Phase 3 chiariti (level_bonus formula corretta, presence continent pulito).

**Vincoli rispettati**: NO deploy · NO hard delete (T22 + T26 verificano) · NO scheduler globale · NO P2W · NO buff economici da leaderboard · NO cambi economia/XP/drop esistenti (nuove risorse in `item_type` isolato). Drop rate CONSERVATIVE cap `+10%` event bonus. `market_cap_daily_per_guild=3` persistito nel catalog per Phase 6.

**Report finale**: `/app/memory/round163_phase4_final_report.md` (15 sezioni).

**Next round proposto**: R16.3 Phase 5 — Forgia Leggendaria & Forgia di Arfus (receipts che consumano risorse continentali, legendary BOP `is_tradeable=false`).


---

## R16.3 Phase 4 closed (post-verify) — 2026-07-01

**🟢 OFFICIALLY CLOSED ✅** — E2E `e1_tester` 3/3 PASS post-verify. Bug UX su `/api/adventurers` fixato (ora riflette `is_available=False` + `status="resource_gathering"` + double-book server-side protection). Utility QA `POST /api/admin/resources/dev/complete/{mission_id}` gated APP_ENV. **37/37 pytest** post-verify (30+7 T31-T37). Regression 215/217 (2 legacy R16.0 debt). **Next**: Phase 5A.

---

## R16.3 Phase 5A backend closed — 2026-07-01

**🟡 BACKEND CLOSED / FRONTEND PENDING** — Forgia Leggendaria V0 backend (iterazione 1/2 dello split concordato).

1. **`app/legendary_forge/__init__.py`** (~665 righe compact): seed idempotente 6 ricette (spada_di_alveora, armatura_ambash, anello_di_velur, bastone_di_efreto, amuleto_di_nathos, mantello_di_aveol) + 6 legendary items. Deterministic RNG `_rng_for(guild_id, order_id)` → idempotency on-visit + CLI. Guild-level gate lvl 5. Durata craft 180s V1.
2. **BOP totale**: instances in collection dedicata `legendary_item_instances` (evita clash unique index `inventory_items`). Flag NO_TRADE completi + `bound_to_guild_id`.
3. **Stat cap hard +50% vs epic baseline snapshot 2026-Q2**: `EPIC_STAT_BASELINE` grep-friendly + `LEGENDARY_CAP` runtime clamp + `_validate_base_stats_within_cap()` seed-time guardrail. Clamp trigger → audit `LEGENDARY_STAT_CLAMPED`.
4. **Pity system**: 5 streak senza perfezionato → 6° imperfetto forzato a normale + `pity_applied=true`. Reset su perfezionato reale. Trasparente in `catalog/{slug}.pity_status`.
5. **Materiali rimappati**: 8 slug originali del brief non esistevano nel DB. Rimappato su `iron_shard, raw_leather, arcane_dust, greater_arcane_dust, dragon_essence` con approvazione utente (doc esplicita nel report sez.4).
6. **8 endpoint** (5 public + 3 admin), **5 audit UPPERCASE** in `EVENT_TYPES` + `AUDIT_EVENT_WHITELIST` (23→28). Admin gated 403 non-admin, dev-force-complete gated APP_ENV.
7. **Recovery**: `app/scripts/recover_stuck_legendary_orders.py` (dry-run/apply/guild-id).

**Test**: 33/33 PASS. Regression full **248 passed / 2 skipped / 2 failed** (2 legacy R16.0 debt). Zero regressioni Phase 5A.

**3 bug scoperti+fixati**: signature `user_guild_or_404(db, user_id)`, DuplicateKey `inventory_items` → collection dedicata `legendary_item_instances`, test IDs deterministici → uuid prefix.

**Vincoli**: NO deploy · NO hard delete (T25+T33) · NO scheduler · NO P2W · NO RMT · BOP totale · clamp hard · preview trasparente · pity trasparente · guild lvl 5 gate.

**Report**: `/app/memory/round163_phase5A_final_report.md` (15 sezioni).

**Next**: attesa `e1_tester` E2E backend → iterazione 2 Frontend (LegendaryForge.jsx + LegendaryForgeRecipe.jsx + LegendaryForgeOrders.jsx + MiniCard + nav) → sigillo OFFICIALLY CLOSED.


---

## R16.3 Phase 5A OFFICIALLY CLOSED — 2026-07-01 (Iterazione 3 Frontend)

**🟢 OFFICIALLY CLOSED ✅** — Forgia Leggendaria V0 completa (Backend + Frontend + Docs).

1. **Frontend web** (3 pagine + 1 mini-card):
   - `frontend/src/pages/LegendaryForge.jsx` — hub ricette (gate lvl 5, grid catalog, link ordini).
   - `frontend/src/pages/LegendaryForgeRecipe.jsx` — dettaglio (probabilità trasparenti, pity status, checklist requisiti, **warning BOP evidenziato** con checkbox awareness obbligatoria pre-craft).
   - `frontend/src/pages/LegendaryForgeOrders.jsx` — ordini attivi + storico + auto-refresh 30s.
   - `frontend/src/components/LegendaryForgeMiniCard.jsx` — mini-card in Dashboard V2 sotto SiteIncome/World.

2. **Wiring**:
   - `frontend/src/App.js`: +3 route `ProtectedRoute requireGuild` (`/legendary-forge`, `/legendary-forge/recipe/:slug`, `/legendary-forge/orders`).
   - `frontend/src/components/navMenu.js`: voce "Forgia Leggendaria" badge NEW (testid `menu-legendary-forge`).
   - `frontend/src/pages/Dashboard.jsx`: import + `<LegendaryForgeMiniCard />` mount.

3. **Vincoli UI rispettati**:
   - ✅ Mobile-first, nessun `overflow-x` fisso.
   - ✅ `pb-32 md:pb-8` sui container root delle 3 pagine.
   - ✅ Touch target ≥ 44x44 (min-h-11 sui CTA principali).
   - ✅ Warning BOP evidenziato con checkbox obbligatoria pre-craft.
   - ✅ Probabilità trasparenti (perfezionato/normale/imperfetto + pity bonus).
   - ✅ `data-testid` naming coerente (`legendary-forge-*`, `recipe-card-*`, `forge-craft-cta`, `forge-orders-active`).
   - ✅ Tema dark coerente (bg-slate-900, accenti amber-500/40).

4. **Osservazioni non-bloccanti** (post-testing manuale utente):
   - `/api/market/listings` → 307 redirect a `/api/auction/listings` (consolidamento intenzionale).
   - PATCH admin `is_active` via **query string** (non body): `axios.patch(url, null, { params: { is_active } })`.
   - Slug leggendari confermati: **`legendary_cape_aveol`** (non `cloak_aveol`).

5. **Validazione statica finale**:
   - `pytest tests/backend_round163_phase5A_test.py -q` → **38/38 PASS**.
   - `yarn build` → compilato con 1 warning legacy non-Phase-5A (`ClassHalls.jsx`).
   - Bundle: 348.29 kB gzip (-9 B).

**Report completo**: `/app/memory/round163_phase5A_final_report.md` sez. 17 (Iterazione 3).

**Next**: attesa conferma utente per **Phase 5B — Forgia di Arfus (P1)** — bilanciamento tecnologie passive gilda con cap +30% totale.

---

## R16.3 Phase 5B — Backend + Chronicle Enhancement (2026-07-01)

**🟡 BACKEND CLOSED / FRONTEND PENDING** — Forgia di Arfus V0 (guild
passive technologies) + Enhancement Chronicle server-wide announcement.

1. **Backend module** (`app/arfus_forge/__init__.py`, ~600 righe):
   - 10 tecnologie categorizzate (1 per categoria, no stack same-cat)
   - Cap +30% totale con `CATEGORY_CAPS` differenziati (drop 15%, XP 20%,
     forge 10%, altri 30%)
   - Max 5 tech attive (server-side)
   - Guild level gate ≥ 6
   - Applier `get_active_bonuses_for_guild(guild_id)` backward-compat
   - CAS orders + on-visit fallback (no scheduler)
   - 9 endpoint (6 public + 3 admin)

2. **Applier integrato in 5 servizi** (patch mirati, no refactor):
   - `expeditions/services.py::_complete_one_expedition` — leader_experience → xp
   - `raids/__init__.py::complete_raid` — combat_damage → raid_score, leader_experience → xp
   - `world_boss/__init__.py::send_team` — combat_damage → contribution
   - `resources/__init__.py::_resolve_mission` — exploration_luck → drop_rate
   - `legendary_forge/__init__.py::_resolve_order` — arcane_knowledge → success_chance, forge_efficiency → perfezionato_chance

3. **Chronicle Enhancement server-wide announcement**:
   - Nuovo lowercase audit event `legendary_perfezionato` emesso su
     crafting perfezionato
   - Whitelist `PUBLIC_EVENTS` + template IT/EN in `_EVENT_TEMPLATES`
   - **Reuse elegante di `audit_log`** (no nuova collection — vedi §6.1
     del report per rationale)

4. **Audit whitelist**: 28 → 33 (5 UPPERCASE arfus events).
   `legendary_perfezionato` in `EVENT_TYPES` per chronicle, NOT nella
   admin whitelist (design intentional).

5. **Test suite**:
   - Phase 5B: **39 passed, 1 skipped** (40 test totali)
   - Phase 1-5B combined R16.3: **185 passed, 2 skipped, 0 fail**
   - Backward-compat Phase 5A: **38/38 pass** (nessuna regression numerica)

6. **Deviazioni dal brief** (documentate nel report finale sez. §6):
   - Chronicle NON usa `world_chronicle_entries` — riuso `audit_log`
     esistente (soluzione strictly better)
   - Endpoint `/api/chronicle/latest` NON aggiunto — l'esistente
     `/api/chronicle?limit=N` è semanticamente equivalente
   - Whitelist +5 (non +7): `ARFUS_BONUS_APPLIED` skipped (noisy),
     `CHRONICLE_ENTRY_RECORDED` non serve (reuse audit_log)

**Report completo**: `/app/memory/round163_phase5B_final_report.md`

**Next**: Iterazione 2 (Frontend Phase 5B) dopo verifica manuale utente.


---

## R16.3 Phase 5B OFFICIALLY CLOSED — 2026-07-01 (Iterazione 2 Frontend)

**🟢 OFFICIALLY CLOSED ✅** — Forgia di Arfus V0 completa (Backend +
Frontend + Docs).

1. **Frontend web** (4 pagine + 1 mini-card):
   - `pages/ArfusForge.jsx` — hub Tech Tree (gate lvl<6 + 3 gruppi categoria + slot counter)
   - `pages/ArfusTechDetail.jsx` — dettaglio + modal warning slot ≥4 + CTA "Avvia Ricerca"
   - `pages/ArfusResearch.jsx` — countdown timer + auto-refresh 30s + storico
   - `pages/ArfusActive.jsx` — toggle attiva/disattiva + riassunto bonus con CATEGORY_CAPS
   - `components/ArfusMiniCard.jsx` — Dashboard V2 mini-card

2. **Chronicle enhancement (nessun nuovo componente)**:
   - `ChronicleCard.jsx` esistente rende automaticamente
     `legendary_perfezionato` (backend whitelisted).

3. **Wiring**:
   - `App.js`: +4 route `requireGuild`
   - `navMenu.js`: voce "Forgia di Arfus" badge NEW
   - `Dashboard.jsx`: mount `<ArfusMiniCard />`

4. **Vincoli UI (checklist static CSS rispettata)**:
   - ✅ Mobile-first, no `overflow-x` fisso
   - ✅ `pb-32 md:pb-8` sui container root
   - ✅ Touch target ≥44x44 (`min-h-[44px]`)
   - ✅ CTA `w-full md:w-auto`
   - ✅ Warning slot ≥4 con checkbox conferma prima di sblocco
   - ✅ Bonus attivi combinati mostrati per categoria con caps

5. **Validazione finale**:
   - `yarn build` → 1 warning legacy (ClassHalls.jsx non-5B)
   - `yarn lint` sui file Arfus → solo warning cosmetici
   - `pytest -k round163_phase5B` → 39 passed, 1 skipped
   - `pytest -k round163_phase5A` → 38/38 (backward-compat)

6. **E2E Results (Iter1 backend, `e1_tester`)**: 10/13 PASS + 2 HUMAN_REQUIRED
   + 1 DESIGN_ONLY (i 3 non-PASS sono limiti test infra, non bug —
   verificati via code inspection utente).

7. **Osservazioni non-bloccanti** (persistenti):
   - `/api/market/listings` → 307 redirect
   - PATCH admin usa **query string** `?is_active=<bool>`
   - Slug leggendari: `legendary_cape_aveol`
   - Sub-check 2.7 no-stack: logica presente ma unreachable con V1 seed

**Report completo**: `/app/memory/round163_phase5B_final_report.md` sez. 11-14.

**Next**: **Phase 6 — Patti commerciali gilda + Specializzazioni gilda (P2)**.


---

## R16.3 Phase 6 — Backend Trade Pacts + Guild Specialization (2026-07-01)

**🟡 BACKEND CLOSED / FRONTEND PENDING** — Trade Pacts V0 + Guild
Specialization V0 (pure social + narrative, ZERO numerical modifiers).

1. **Trade Pacts V0** (`app/trade_pacts/`, ~350 righe):
   - Max 3 patti accepted per gilda, cross-continent block via
     `guild_world_presence.status='active'`, cooldown 7gg unilateral
   - 7 public endpoint + 2 admin
   - No hard delete: dissolve preserva la row con `status=dissolved`

2. **Guild Specialization V0** (`app/guild_specialization/`, ~330 righe):
   - 6 archetipi (incursion/production/merchant/exploration/military/
     arcane_research) con `hook_categories` per Phase 6.5+
   - Guild lvl ≥ 8, prima scelta gratuita, reset 200k oro + 3×
     frammento_di_ergolat + cooldown 30gg
   - 4 public endpoint + 2 admin
   - Zero bonus meccanici in V0

3. **Whitelist audit**: 33 → 41 (8 nuovi UPPERCASE events).

4. **Test suite**:
   - Phase 6: **34 passed** (0 fail, 0 skip)
   - R16.3 phases 1-6 combined: **219 passed, 2 skipped, 0 fail**
   - Backward-compat Phase 5A/5B: intatto (38/38 + 39/40)

5. **Deviazioni dal brief** (rationale nel report §6):
   - Max 3 check applicato sull'acceptor (guild_b_id) per design intentional
   - `hook_categories` persistito ma non consumato in V0 (demandato a 6.5+)
   - BSON ObjectId serialization fix: `.pop("_id", None)` pattern

6. **Osservazioni non-bloccanti** (persistenti):
   - `/api/market/listings` → 307 redirect
   - PATCH admin usa **query string** `?is_active=<bool>`

**Report completo**: `/app/memory/round163_phase6_final_report.md`

**Next**: Iterazione 2 (Frontend Phase 6) dopo verifica manuale utente.


---

## R16.3 Phase 6 OFFICIALLY CLOSED — 2026-07-01 (Iter2 Frontend + QA cleanup)

**🟢 OFFICIALLY CLOSED ✅** — Trade Pacts V0 + Guild Specialization V0
completi (Backend + Frontend + Docs).

1. **Frontend web** (4 pagine + 2 mini-card):
   - `pages/TradePacts.jsx` — hub attivi + ricevute + inviate + modal dissolve
   - `pages/TradePactRequest.jsx` — search neighbors + invita
   - `pages/GuildSpecialization.jsx` — choose free-first + modal reset
   - `pages/GuildSpecializationCatalog.jsx` — read-only 6 archetipi
   - `components/TradePactsMiniCard.jsx` — Dashboard N/3 attivi + M ricevute
   - `components/SpecializationMiniCard.jsx` — branch active/choose/locked

2. **QA Cleanup**:
   - Script `scripts/reset_test_account_phase6_state.py` (idempotente, gated)
   - Concatenato a `reset_test_account_world_state.py` (`--skip-phase6-cleanup` opt-out)
   - Eseguito: **6 pacts archiviati + 1 spec (incursion) archiviata**

3. **Wiring**:
   - `App.js`: +4 route `requireGuild`
   - `navMenu.js`: +2 voci "Specializzazione" + "Patti Commerciali" badge NEW
   - `Dashboard.jsx`: +2 mini-card in grid 2-col

4. **Vincoli UI (checklist rispettata)**:
   - ✅ Mobile-first, no `overflow-x` fisso
   - ✅ `pb-32 md:pb-8` sui container
   - ✅ Touch target ≥44x44
   - ✅ CTA `w-full md:w-auto`
   - ✅ Warning modals (dissolve unilateral 7gg, reset 200k+3× ergolat+30gg)

5. **E2E Results** (`e1_tester`):
   - Test 1 (pact flow): **PASS completo**
   - Test 2 (spec reset): **PARTIAL** (cost debit coperto da pytest T22)
   - Test 3 (audit+admin gates): **NOT_EXECUTED per timeout** (coperto
     pytest T24-T27). Tester rilancerà out-of-band post-sigillo.

6. **Validazione finale**:
   - `yarn build` → OK (1 warning legacy non-Phase-6)
   - `pytest -k round163_phase6` → 34/34 pass
   - R16.3 combined 1-6: 219 passed, 2 skipped, 0 fail

7. **Osservazioni non-bloccanti** (persistenti):
   - `/api/market/listings` → 307 redirect
   - PATCH admin usa **query string** `?is_active=<bool>`
   - BSON ObjectId serialization: pattern `.pop("_id", None)`

**Report completo**: `/app/memory/round163_phase6_final_report.md` sez. 11-15.

**Next**: **STOP per conferma utente Phase 7 — PvP continentale (P2)**.


---

## R16.3 Phase 7 — Ciclo PvP completo *(CLOSED ✅ 2026-07-01)*

### Phase 7A — PvP Continentale 1v1 (Iter1 Backend + Iter2 Frontend)
- **Backend**: 33/33 pytest PASS
- Elo K=32 clamp `[800, 2400]`, gate `guild.level ≥ 8`, max 3 sfide attive, cooldown 12h coppia
- Bracket ±200 Elo, team snapshot 5v5, resolution deterministica `random.Random(battle_id+role)`
- On-visit fallback per timeout defaulted + recovery CLI `recover_stuck_pvp_battles.py`
- Arfus applier filtrato PvP: whitelist 6 categorie combat (`combat_damage`, `combat_healing`, `combat_defense`, `counter_effectiveness`, `iron_will`, `team_morale`), cap totale 50%
- 6 audit events UPPERCASE + admin whitelist 41 → 47
- **Frontend**: 4 pagine (`PvpOpponents`, `PvpChallenge`, `PvpBattles`, `PvpBattleReport`) + `PvpMiniCard` + `PvpGuildLevelGate` + battle log narrativo italiano
- **Fix trasversale badge NEW**: nav Component `<NavBadge>` esportato + rendering in AppHeader + MobileMenuDrawer

### Phase 7B — Leaderboard settimanale + Cosmetici (Iter1 Backend + Iter2 Frontend)
- **Backend**: 31/31 pytest PASS (30 P0 + 1 guard-rail leaderboard endpoint parity)
- Snapshot settimanale + rollover on-visit (nessuno scheduler globale), CAS lock idempotente `active→closing→finalized`
- 24 cosmetici (8 continenti × 3 tipi: `title` rank1, `badge` rank≤3, `frame` rank≤10)
- Recovery CLI `recover_stuck_pvp_seasons.py`
- 3 audit events UPPERCASE + admin whitelist 47 → **50**
- **Frontend**: 3 pagine (`PvpSeasonOverview`, `PvpSeasonLeaderboardDetail`, `PvpSeasonCosmetics`) + `PvpSeasonMiniCard` + nav voce "Stagione PvP" badge NEW + disclaimer anti-P2W ×3

### Anti-P2W GUARANTEE (verificato)
- Whitelist Arfus PvP taglia effetti non-combat (arcane_knowledge, exploration_luck, market_bonus, ecc.)
- Cosmetici puramente decorativi (title/badge/frame — zero gameplay impact)
- Test regression `test_26_no_p2w_stat_impact_after_award` asserta immutabilità di `guild.gold`, `guild.reputation`, `guild.level`, `guild.name`, `guild_pvp_stats.elo/wins/losses/draws` dopo `award_cosmetic()`
- Disclaimer utente frontend visibile ×3 (Overview footer + Cosmetics top + Detail footer)

### Risultato test suite Round 16.3 Phase 7
| Suite | Result |
|---|---|
| `test_pvp_phase7a_p0.py` | 33/33 PASS |
| `test_pvp_season_phase7b_p0.py` | 31/31 PASS |
| `test_forge_actions_p0.py` (regression) | 6/6 PASS |
| `test_races_endpoint_p1.py` (regression) | 6/6 PASS |
| **Totale sessione Phase 7** | **76/76 PASS** |

**Report completo**: `/app/memory/round163_final_report.md` (sigillo consolidato Round 16.3).

**Round 16.3 OFFICIALLY CLOSED ✅** con inclusione Phase 8 V1.

---

## ROUND 16.3 Phase 8 V1 — Stalla & Cavalcature (cosmetic-only) ✅ CLOSED 2026-07-01

### Backend Iter1

**Modulo**: `/app/backend/app/stables/` (7 file: `__init__`, `models`, `catalog`, `seed`, `services`, `routes`, `admin_routes`).

**Collezioni Mongo** (4 principali + 1 ausiliaria):
- `mount_catalog` — 9 mount seeded (unique(slug))
- `narrative_routes` — 5 rotte seeded (unique(slug))
- `guild_mount_ownership` — ownership per guild (unique(guild_id, mount_slug), aux (guild_id, is_active))
- `narrative_route_completions` — one-shot completions (unique(guild_id, route_slug))
- `narrative_rewards_unlocked` — badge/title/lore assegnati (unique(guild_id, reward_slug))

**9 Mount seedati**:
| Slug | Dominio | Rarità | Fonte |
|---|---|---|---|
| ronzino-di-strada | starter | common | starter_quest |
| scarabeo-runico | ambash | uncommon | craft |
| cervo-lunare | velur | rare | world_boss_drop |
| lupo-delle-fronde | soe | uncommon | world_boss_drop |
| salamandra-di-efreto | efreto | rare | craft |
| segugio-cinereo | irthe | uncommon | achievement |
| remora-tempestosa | nathos | rare | world_boss_drop |
| ombra-sellata | ergolat | epic | narrative |
| grifone-delle-alture | aveol | rare | achievement |

**5 Rotte narrative seedate**:
| Slug | Dominio richiesto | Reward type | Reward slug |
|---|---|---|---|
| sentiero-delle-fronde | soe | cosmetic_badge | traveler_of_fronde |
| via-delle-alture | aveol | cosmetic_title | titolo_scalatore_delle_alture |
| traccia-lunare | velur | lore_entry | codex_traccia_lunare |
| passo-delle-ceneri | efreto | cosmetic_badge | badge_passo_ceneri |
| cammino-ombra | ergolat | cosmetic_title | titolo_pellegrino_ombra |

I 3 domini scoperti (ambash, irthe, nathos) sono riservati a Phase 8 V2.

**Endpoint** (9 = 7 pubblici + 2 admin dev-gated):
- `GET /api/stables/catalog`
- `GET /api/stables/mine`
- `POST /api/stables/set-active` (accetta `mount_slug: null` per deselect)
- `POST /api/stables/quest/starter/claim` (idempotente, first-time only, auto-attiva)
- `GET /api/stables/narrative-routes`
- `POST /api/stables/narrative-routes/{slug}/travel` (one-shot per rotta+guild)
- `GET /api/stables/narrative-rewards/mine`
- `GET /api/admin/stables/catalog`
- `POST /api/admin/stables/dev/grant-mount`

**Audit events UPPERCASE** (+4):
- `MOUNT_STARTER_CLAIMED`
- `MOUNT_ACQUIRED`
- `MOUNT_ACTIVE_SET`
- `NARRATIVE_ROUTE_TRAVELED`

Whitelist admin: **50 → 54** (verificato runtime da `test_24_audit_whitelist_has_54_entries`).

### Anti-P2W hard verification (Phase 8 V1)

**Catalog invariants** (hardcoded + anti-drift override nel seed):
- `affects_combat=false`
- `affects_economy=false`
- `affects_ranking=false`
- `affects_travel_time=false`
- `can_be_sold_for_real_money=false`

**Reward invariants**: `reward_type ∈ {cosmetic_badge, cosmetic_title, lore_entry}` — mai `gold/xp/reputation/materials`.

**Regression test esplicito** con snapshot BEFORE/AFTER:
- `test_20_no_p2w_stat_impact_after_claim`: `guild.gold`, `guild.reputation`, `guild.level`, `guild.name` invariati dopo claim starter
- `test_21_no_p2w_stat_impact_after_narrative_travel`: `guild.gold/reputation/level` invariati dopo travel narrative

**Zero scritture runtime** a `guilds.gold`, `guilds.reputation`, `guilds.level`, `guild_pvp_stats.*`, `adventurers.stats`, `inventory`, `item_instances`.

### Frontend Iter2

**File creati** (4):
- `/app/frontend/src/pages/Stables.jsx` — hub pagina con 3 tab (Le Mie Cavalcature / Catalogo Completo / Rotte Narrative), CTA "Rivendica il Ronzino", loading/empty state, toast IT
- `/app/frontend/src/components/MountCard.jsx` — card riutilizzabile con emoji, rarity badge, dominio, activate/deactivate CTA
- `/app/frontend/src/components/NarrativeRouteCard.jsx` — card rotta con status pill (Percorribile/Completata/Cavalcatura mancante) + CTA travel
- `/app/frontend/src/components/StablesMiniCard.jsx` — mini-card dashboard con mount attivo + count + micro-disclaimer

**File modificati** (3):
- `App.js` — route `/stables` con `requireGuild`
- `Dashboard.jsx` — inclusione `<StablesMiniCard />` sotto `PvpSeasonMiniCard`
- `navMenu.js` — voce "Stalla" in sezione Gilda (badge NEW, `menu-stables`)

**Anti-P2W disclaimer visibile ×2**:
1. `Stables.jsx` footer full box emerald (`stables-antip2w-disclaimer`)
2. `StablesMiniCard.jsx` micro-disclaimer 1 riga (`stables-mini-antip2w`)

### Test suite Phase 8 V1

- `test_stables_phase8_v1.py`: **28/28 PASS** — Unit catalog invariants (6), seed idempotency (2), HTTP endpoints (8), direct-DB flows (3), anti-P2W regression (3), audit registration (2), admin HTTP (2), regression baseline (2)

### Totale sessione R16.3 Phase 7 + 8

| Suite | Result |
|---|---|
| `test_pvp_phase7a_p0.py` | 33/33 PASS |
| `test_pvp_season_phase7b_p0.py` | 31/31 PASS |
| `test_stables_phase8_v1.py` | 28/28 PASS |
| `test_forge_actions_p0.py` (regression) | 6/6 PASS |
| `test_races_endpoint_p1.py` (regression) | 6/6 PASS |
| **Totale sessione Phase 7+8 V1** | **106/106 PASS** |

**Report Phase 8 V1**: `/app/memory/round163_phase8_v1_iter1_backend_report.md` + `/app/memory/round163_phase8_v1_iter2_frontend_report.md`.

---

**Next**: **P3 Debt cleanup (Iter C)** — pytest HTTP admin bypass DB isolation, startup handler cleanup, schema drift Alchemist, ESLint warning ClassHalls, guard-rail self-test, mobile viewport workaround.

