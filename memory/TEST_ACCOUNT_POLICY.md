# TEST ACCOUNT POLICY (PERMANENT) — Orbus Online

**Effective**: 2026-06-26 (Phase 19)
**Scope**: every account / guild created by an agent for QA, debug, E2E, smoke,
or manual validation purposes.

## 1. Naming convention (MANDATORY)

| Resource | Pattern | Example |
|---|---|---|
| Email | `*@orbus.test` (never a real domain) | `e2e-raid-builder@orbus.test` |
| Username | prefix `TEST_`, `E2E_`, `QA_`, `R<N>_`, `SMOKE_`, etc. | `R5_smoke_raider`, `QA_admin_ui` |
| Guild | same prefix as username | `R5_Probe_001`, `E2E_RaidBuilder_001` |

Tester reale `tester@orbus.test` (forced `is_test_user=True` since Round 4) is
the **only** allowed orbus.test account that bypasses the leaderboard filter
(opt-in via `TEST_GUILDS_FORCE` list).

## 2. Tracking in every final report (MANDATORY)

Every agent report MUST include a section **"Account test creati e cleanup"**
listing for each test account created during the session:

- Email test
- Guild created (if any)
- Reason for creation
- Environment (preview / prod)
- Final state: **ELIMINATED** | **FLAGGED `is_test_user=True`** | **STILL NEEDED**
- Backup file path if data was modified (e.g. shadow placeholder users)

If no test accounts were created → report MUST explicitly state:
> "Nessun account test creato in questa sessione."

## 3. Preview / dev environment

- **Preferred**: full cleanup (drop the user + guild + linked adventurers/expeditions/raids/listings) **only if safe** (no foreign-key cascade risk).
- **Fallback**: flag `is_test_user=true` on the user → guild is hidden from
  leaderboard / chronicle / market / consortium / raid leaderboard
  automatically via existing privacy filters.
- **Orphan guilds** (owner deleted): create a "shadow placeholder" user with
  `is_test_user=true` and re-attach the guild; document in
  `/app/memory/db_phase19_raid_lb_cleanup_backup.json` (or analogous file)
  for full reversibility. **NO hard delete of guild data.**

## 4. Production environment

- **Default**: NO test accounts. Use preview for QA.
- **If unavoidable** (e.g. live-fire smoke after a deploy):
  - MUST use the `*@orbus.test` naming convention.
  - MUST set `is_test_user=true` immediately after creation.
  - MUST be excluded from leaderboard / chronicle / market / consortium /
    raid leaderboard via the existing privacy filters.
  - Post-test action: flag retained OR account deletion (only if
    authorized explicitly by the user — NO hard delete without authorization).

## 5. Hard rules

- ❌ NO test account in leaderboard.
- ❌ NO test account in ALLOWLIST.
- ❌ NO test account name confusable with a real guild (Crociata d'Argento,
  Drakarys, Harambes, The Loremaster, Il Regno di Lanafuoco, Sentiero di Efreto).
- ❌ NO hard delete of any data without explicit user authorization.
- ❌ NO PII (real email / username) in test fixtures.

## 6. Real-player allowlist (PERMANENT)

Real-player guilds are protected by name + email in 3 files:
- `/app/backend/tests/conftest.py` (`ALLOWLIST_GUILDS_LOWER`, `ALLOWLIST_EMAILS`)
- `/app/scripts/prod_leaderboard_cleanup.py` (`ALLOWLIST_GUILDS`)
- `/app/backend/app/admin/services.py` (`CLEANUP_ALLOWLIST_GUILDS`, `CLEANUP_ALLOWLIST_EMAILS`)
- Source of truth: `/app/memory/ALLOWLIST.md`

Current entries (2026-06-26): Sentiero di Efreto, Drakarys, Harambes,
The Loremaster, Il Regno di Lanafuoco, **Crociata d'Argento**.

Adding a new real player → update **all 4 files atomically** + audit entry
in `/app/memory/ALLOWLIST.md`.

## 7. Enforcement

Future agents MUST read this file BEFORE creating any test account.
Reference it in every final report (cite this file by path).
