# ORBUS ONLINE — Permanent Allowlist

Single source of truth for accounts and guilds that **no automated process**
(pytest pollution sweep, DB cleanup script, denylist filter, leaderboard
test-user filter) is allowed to delete, flag, or hide.

Last updated: **2026-06-26** (Round 3 post-deploy — Harambes added)

## Why this exists

On 2026-06-25 ~21:00 UTC, a real user (`gianluca.brandi42@gmail.com`,
guild **Drakarys**) reported their account missing. Audit established:

1. The user is **NOT** in any of our cleanup backups (`db_pre_cleanup_backup.json`
   created 2026-06-25T18:58, `db_ambiguous_flag_backup.json`).
2. The user is **NOT** in the current preview MongoDB.
3. The pytest pollution sweep regex patterns **DO NOT match** their email or
   guild name (verified — see "Audit conftest" below).
4. The cleanup scripts (`db_cleanup_phase14_3.py`) ran hours BEFORE the user's
   reported registration time.

Most likely explanation: the user registered on **production**
(`orbusonline.net`), not on preview. Preview and production use separate
MongoDB clusters (`PROD_AUDIT_INSTRUCTIONS.md` riga 5-7). The preview agent
(me) has no access to the production cluster and could not have deleted
anything there.

Regardless: as a defensive measure, the allowlist below is now **hardcoded**
in every cleanup surface so that no future operation can touch these accounts.

## Allowlist (canonical sets)

### Emails (case-insensitive, must be lowercased before comparison)

```python
ALLOWLIST_EMAILS = {
    "mr.gualmini@gmail.com",          # Gualma — primary author/admin
    "gianluca.brandi42@gmail.com",    # Drakarys owner (real player)
    "tester@orbus.test",              # sandbox admin (dev-only seed)
    # PENDING: Harambes owner email — guild "harambes" is a real prod player
    # but the email was not provided yet. Until the user provides it,
    # protection relies on the name-based check below.
}
```

### Guild names (case-insensitive, lowercase form for comparison)

```python
ALLOWLIST_GUILDS_LOWER = {
    "sentiero di efreto",       # Gualma's guild
    "drakarys",                 # Brandi's guild
    "harambes",                 # real prod player (owner email pending)
    "the loremaster",           # CONFIRMED real player (mr.gualmini@gmail.com) — 2026-06-26
    "il regno di lanafuoco",    # CONFIRMED real player 2026-06-26 (owner email TBD)
}
```

### TODO — email pendenti da richiedere all'utente

- Owner email di `harambes` — protezione attualmente solo name-based
- Owner email di `il regno di lanafuoco` — protezione attualmente solo name-based
  Una volta nota, va aggiunta a `ALLOWLIST_EMAILS` in tutti e 3 i file.

## Enforcement points

All of these files import / replicate the allowlist. Any new cleanup or
flagging code MUST honour both sets.

| File | What it enforces |
| --- | --- |
| `/app/backend/tests/conftest.py` | Pytest pre-suite pollution sweep — `$nin ALLOWLIST_EMAILS` on every `users.delete_many`; `$nin` lowered name + `$nin` owner_user_id on every `guilds.delete_many`. |
| `/app/scripts/db_cleanup_phase14_3.py` | `classify()` returns "allowlist" for any email in `ALLOWLIST_EMAILS`. Allowlist guilds never enter `guilds_owned_by_denylist` or `orphan_guilds`. |
| `/app/backend/app/leaderboard/services.py` | (existing) Filters `is_test_user=True`. Allowlist users must NEVER have this flag set. |
| `/app/memory/PROD_AUDIT_INSTRUCTIONS.md` | Read-only audit script counts how many of the allowlist accounts are present in production. |

## Operational rules

1. **Adding an account to the allowlist** requires explicit user confirmation
   (mention email + guild name) and an entry in this document with date +
   reason.
2. **Removing an account** from the allowlist is forbidden without explicit
   user authorization — it's a permanent guarantee.
3. **Any new cleanup script** added under `/app/scripts/` MUST import
   `ALLOWLIST_EMAILS` from `tests/conftest.py` (or replicate it verbatim) and
   exclude both sets from any destructive operation.
4. **Leaderboard filter**: the allowlist users must never receive
   `is_test_user=True`. The audit script reports if they do.

## Audit log

| Date | Event | Result |
| --- | --- | --- |
| 2026-06-25 18:58 | Phase 14.3 cleanup (3582 orphan guilds, 210 denylist flagged) | Allowlist at that time: 1 entry (mr.gualmini@gmail.com). Drakarys NOT in DB. |
| 2026-06-25 19:06 | 16 ambiguous users flagged `is_test_user=True` | None of them was gianluca.brandi42 or Drakarys (full dump available). |
| 2026-06-25 21:06 | Allowlist hardened (this commit) | +gianluca.brandi42@gmail.com, +tester@orbus.test, +Drakarys (guild). Pytest conftest sweep now filters all of them. |
| 2026-06-26 (Round 3 post-deploy) | +Harambes (guild only, email pending) | Real prod player confirmed by user. Owner email still to be provided; name-based protection active. |
| 2026-06-26 08:35 (post unified deploy) | +The Loremaster (allowlist) +Il Regno di Lanafuoco (allowlist) +The Iron Lantern (TEST_GUILDS_FORCE) | User classified the 3 previously-ambiguous prod guilds. Loremaster confirmed = mr.gualmini@gmail.com (already in email allowlist). Lanafuoco = nuovo giocatore reale (email TBD). Iron Lantern = test → forced flag via TEST_GUILDS_FORCE set in prod_leaderboard_cleanup.py. |
| 2026-06-26 (Round 3 post-deploy) | Preview leaderboard residual cleanup | 13 leaderboard-visible test users flagged `is_test_user=True`; 53 orphan-owner guilds got a shadow placeholder user (`is_test_user=True`) so the leaderboard filter applies. Reversible via the backup in `db_leaderboard_residual_flag_backup.json`. No hard delete. |
