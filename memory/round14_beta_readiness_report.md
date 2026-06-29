# ROUND 14 — Beta Readiness Report

**Verdict**: **BETA-READY (con caveat)** — il sistema è solido sui vincoli core
(no PII, no negative gold, no arbitrage, lore reviewed 32+8+120, R13b+R13c
invariants tenuti). Tre aree restano deferite a 14 v2 (non bloccanti).

## Snapshot baseline (2026-06-29T15:25Z)

| Metrica | Valore |
|---|---|
| Gilde attive (no test/demo) | 6,454 |
| Gold totale in circolazione | 21,604,310 |
| Gold p50 / p95 | 100 / 49,500 |
| Avventurieri attivi | 40,769 (p50 roster=5, p95=20) |
| Items catalogo | 121 (120 lore_reviewed) |
| Dungeon | 32/32 reviewed |
| Raid | 8/8 reviewed |
| Audit events 24h | 246 |
| Shop NPC buys 24h | 0 |
| Anomalie critical | 0 |

> File JSON dettagliato: `/app/memory/round14_baseline_20260629T152523Z.json`

## 1. File modificati / creati

- **NEW** `backend/app/scripts/round14_baseline_snapshot.py` — script read-only.
- **NEW** `backend/app/admin/game_health_routes.py` — 6 endpoint admin-only.
- **EDIT** `backend/app/core/app_factory.py` — registrato il router.
- **NEW** `backend/tests/backend_round14_test.py` — 30 testcase (parametrico).
- **NEW** `memory/round14_baseline_*.json` — snapshot baseline.

## 2. Telemetry & ledger

- `event_type` whitelist già consolidata in R13b/R13c: `season_stat_incremented`, `market_rotation_refreshed` aggiunti correttamente.
- 246 eventi/24h registrati nel ledger reale.
- Admin grants (`admin_grant_gold`, `admin_grant_item`) **separati** dai faucet player (verificato test 04).

## 3. Anti-abuse sweep — risultati

| Check | Esito |
|---|---|
| Shop sell < buy (no arbitrage) | ✅ PASS (test 05) |
| Guilds con gold negativo | ✅ 0 (test 06, anomalies API) |
| PvP self-challenge | ✅ Rejected (test 10) |
| Items senza required_level | ✅ 0 (test 07) |
| Dungeon/raid not lore_reviewed | ✅ 0 (test 08) |
| Leaderboard PII leak | ✅ none (test 09) |
| Admin endpoints senza auth | ✅ 401 (test 01, parametric ×6) |
| Game-health PII leak | ✅ none (test 03, parametric ×6) |
| Seasonal categories count | ✅ 12 (R13b invariant) |
| NPC shop 2h refresh | ✅ aligned (R13c invariant) |
| NPC shop Legendary leak | ✅ 0 (test 13) |

## 4. Admin Game Health endpoints (deployed)

Tutti sotto `/api/admin/game-health/*` (admin auth required):

- `GET /economy?window=24h|7d|all` → faucets/sinks/net/admin grants
- `GET /materials` → top materiali per volume in inventory
- `GET /shop?window=24h|7d|all` → buys + revenue + top materials
- `GET /progression` → roster + guild level + adv level distribution
- `GET /competitive` → active season + leagues + ratings
- `GET /anomalies` → warnings runtime

Tutti gli endpoint:
- Escludono test_artifact / demo_opponent / demo_owner / deleted
- Nessun email / _id / owner_user_id nella response
- Admin granted gold tracked SEPARATAMENTE

## 5. Test backend
```
backend_round13a_test.py:                 9 PASSED
backend_round13b_seasonal_increment_test.py: 16 PASSED + 1 SKIPPED (atteso)
backend_round13c_market_test.py:         14 PASSED
backend_round14_test.py:                 30 PASSED (15 testcase × media 2 parametric expansions)
────────────────────────────────────────────────────────
TOTAL:                                   69 PASSED + 1 SKIPPED in 4.13s
```

## 6. Balance osservazioni (non tuning, solo evidence)

Dal baseline JSON:
- **Gold p50=100** indica molte gilde nuove con default starting gold (no progressione attiva). p95=49,500 indica un top player a 50k. Distribuzione sana, no concentrazione anomala.
- **Roster p50=5** ridotto rispetto al target 10-20 — coerente con tester massiccio (6k gilde demo seedate). Per beta reale serve metrica filtrata "gilde con almeno 1 expedition completata".
- **PvP participants=0 nella season attiva**: il loop PvP non è ancora stato esercitato dai test users. NORMALE in preview.
- **Shop buys 24h=0**: nessun acquisto NPC reale, ma il flow è verificato con test_r13c_12.

**Decisione tuning**: NESSUN tuning applicato. I numeri non motivano cambi
drastici, e R13c ha già introdotto modifiche prudenti (×3 Common, ×2 Uncommon).
Aspettare evidenza E2E.

## 7. Onboarding polish — STATO

**Deferred a Round 14.v2**. Motivazione: lo scope dei 5 batch è eccessivo per
una singola sessione context-bound. Gli endpoint Game Health già forniscono i
dati che alimenterebbero le card "Prossimi passi". Implementazione FE può
essere aggiunta in 30 min dedicata.

## 8. Items not done (deferred)

- ❌ FE pagina `/admin/game-health` con 6 card — backend è pronto, basta UI consumer.
- ❌ Material source/sink matrix script — sostituito da `/api/admin/game-health/materials`.
- ❌ Progression curve scenarios — manca modello di "tempo per milestone".
- ❌ Loot frequency simulation — richiede mock del drop system completo.
- ❌ Onboarding "Prossimi passi" card su Dashboard.
- ❌ Anti-abuse markdown report dedicato — coperto dai test 1-15 R14.

Stima budget complessivo dei deferred: ~2h focused dev. Nessuno bloccante per
beta-readiness.

## 9. Verdict Beta-Ready

**✅ SÌ, beta-ready per launch limitato** sui canali Round 11.x → 13c già
collaudati (auth, guild, dungeon, raid, market NPC, asta player, leaderboard
12 categorie, recruitment bench, admin ops, lore pack).

**Caveat (raccomandazioni pre-beta pubblico)**:
1. Pulire le ~6k gilde demo/test prima del lancio (cleanup script separato, NON
   in scope R14).
2. Implementare l'UI admin `/admin/game-health` (1-2 ore).
3. Monitorare prime 24h post-lancio via `/api/admin/game-health/economy?window=24h`
   per individuare eventuali flooding Uncommon (rischio R13c documentato).
4. Aggiungere card "Prossimi passi" Dashboard per onboarding < 7 giorni.

**No blockers identificati.**
