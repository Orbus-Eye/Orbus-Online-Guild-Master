# Round 14.v2.1 — Cleanup Diff (close-out)

**Author**: E1 agent
**Date**: 2026-06-29
**Scope**: Final pre-Beta soft-archive sweep + leaderboard sanitisation.

## Cumulative archive counts

| Phase                                | archived_total |
|--------------------------------------|----------------|
| R14.v2 original cleanup              | 10,681         |
| R14.v2.1 patch 1 (G_/G/Test/Demo/…)  | 10,681 (same — already applied) |
| R14.v2.1 patch 2 (Guild_*/Guildhouse)| 12,222         |
| R14.v2.1 patch 3 (P<n>[A-Z]?/Ver/RaidSmoke) | **12,611** |
| **Final active (non-archived)**      | **5**          |

DB total guilds: 12,616. Active = 5 (4 preserved + 1 real player). All other rows
remain queryable in Mongo for forensics (NO hard delete).

## Patterns added in v2.1 (regex extensions)

Original v1 regex caught: `is_test_artifact=True`, `Guild_ob_oor_`, `Guild_dh_sticky_`, `Guild_dh_`.

v2.1 extensions (idempotent, additive):
1. `^(G_|G |Test|Demo|tester|R[0-9]|[0-9]+[A-Z])` — fixture short prefixes.
2. `^P[0-9]+[A-Za-z]*\s+[0-9a-fA-F]` — phase fixtures `P192R`, `P193D`, `P194a`, `P194b`, `P194ba` + space + hex.
3. `^Ver\s+ver_` — verification harness fixture.
4. `^RaidSmoke\s+raidsmoke_` — raid smoke-test fixture.
5. `^Guild(house)?[_\s]` — catches `Guild_ref_*`, `Guild_gw_*`, `Guild_sc_*`, `Guild_unlock_*`, `Guild_gates_*`, `Guild_disp_lock_*`, `Guild <hex>`, `Guildhouse <HEX>`.

Each pattern was validated to NOT match the preserved 4 (`The Iron Lantern`,
`Custodi del Vento`, `Esiliati del Vuoto`, `Compagnia delle Tre Lune`) nor the
single legitimate player `Sentiero di Efreto`.

## Idempotency proof (last run pair)

| Run | archived_in_this_run | total_archived_now | active_after |
|-----|----------------------|---------------------|--------------|
| C (apply final regex) | 389 | 12,611 | 5 |
| D (immediate rerun)   |   **0**   | 12,611 | 5 |

Run D archives 0 → cleanup is idempotent.

## Leaderboard sanitisation (5 categories × 14 test patterns)

All 5 public categories verified via `GET /api/leaderboard?category=<slug>&limit=50`:

| Category          | total_entries | test/demo pattern matches |
|-------------------|---------------|---------------------------|
| `peak_power`      | 1             | 0 / 14                    |
| `dungeon_clears`  | 1             | 0 / 14                    |
| `raid_clears`     | 1             | 0 / 14                    |
| `raid_score`      | 1             | 0 / 14                    |
| `territory_score` | 1             | 0 / 14                    |

Each leaderboard now shows only `Sentiero di Efreto` (the lone real player with
gameplay stats). Tester `The Iron Lantern` is correctly excluded via the
existing `is_test_artifact=True` filter. Demo opponents (`Custodi del Vento`,
`Esiliati del Vuoto`, `Compagnia delle Tre Lune`) are also excluded from public
LB via the existing `is_demo_opponent=True` filter while still preserved for
PvP matchmaking.

Note: requested categories `weekly_gold` and `arena_rating` do not exist in the
current category catalog (`GET /api/leaderboard/categories`). Substituted with
`raid_score` and `territory_score` from the live catalog.

## Preserved 4 (verified post-cleanup)

| Name                      | archived | is_test_artifact | is_demo_opponent |
|---------------------------|----------|------------------|------------------|
| The Iron Lantern          | False    | True             | (n/a)            |
| Custodi del Vento         | False    | False            | True             |
| Esiliati del Vuoto        | False    | False            | True             |
| Compagnia delle Tre Lune  | False    | False            | True             |

## PII / privacy sweep on `/api/leaderboard`

Top-1 entry keys: `['guild_name', 'guild_public_id', 'is_me', 'rank', 'score']`.

No leaks: `email`, `user_id`, `owner_id` (ObjectId), `password_hash`, `_id` raw, IP — all **absent**.

## localStorage sweep on `frontend/src`

`grep -rn` for `localStorage.(get|set|removeItem).*(access_token|jwt|auth_token|authToken|accessToken|jwtToken)` → **0 hits**.

Only references to localStorage in source are explanatory comments in
`context/AuthContext.jsx` and `lib/api.js` noting that the new auth flow
deliberately avoids localStorage (HttpOnly cookie + in-memory CSRF). Auth is
cookie-based, no tokens leaked to JS storage.

## Pytest regression smoke

`pytest tests/backend_round13a_test.py tests/backend_round13b_seasonal_increment_test.py tests/backend_round13c_market_test.py tests/backend_round14_test.py` → **69 passed, 1 skipped, 0 failed**.

## Verdict

**R14.v2.1 — CHIUDIBILE: SÌ.**
