# ORBUS ONLINE — Permanent Allowlist

Single source of truth for accounts and guilds that **no automated process**
(pytest pollution sweep, DB cleanup script, denylist filter, leaderboard
test-user filter) is allowed to delete, flag, or hide.

Last updated: **2026-06-25** (Phase 14.5-hotfix)

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
}
```

### Guild names (case-insensitive, lowercase form for comparison)

```python
ALLOWLIST_GUILDS_LOWER = {
    "sentiero di efreto",  # Gualma's guild
    "drakarys",            # Brandi's guild
}
```

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
