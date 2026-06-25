# DB Audit Report — Orbus Online
**Date:** 2026-06-25
**Mode:** READ-ONLY (no DELETE performed)
**Scope:** Identify smoke/test users polluting the leaderboard.

## Totals (before any cleanup)
- Users: 227
- Guilds: 3803

## Breakdown
| Category | Count |
| --- | --- |
| Allowlist (real testers) | 1 |
| Denylist match (smoke/test) | 210 |
| Ambiguous (needs human review) | 16 |

## Collateral records owned by denylist users
- Guilds (owner is denylist user): 207
- Extra guilds matching guild-name pattern (not yet linked): 3
- Adventurers in deny guilds: 229
- Inventory items in deny guilds: 0
- Expeditions in deny guilds: 44

## Allowlist (KEEP — real testers)
- m*********i@gmail.com · username=Gualma

## Denylist samples (CANDIDATES for cleanup)
- t****r@orbus.test
- l*******_@orbus.test
- d********0@orbus.test
- o*************f@orbus.test
- o**************e@orbus.test
- o***************b@orbus.test
- o*****************5@orbus.test
- o***************f@orbus.test
- o******************2@orbus.test
- o***************0@orbus.test
- o*************f@orbus.test
- o*****************3@orbus.test
- o*************2@orbus.test
- o**************1@orbus.test
- o***************7@orbus.test
- o*****************4@orbus.test
- o***************b@orbus.test
- o******************c@orbus.test
- o***************a@orbus.test
- o*************b@orbus.test
… and 190 more

## Ambiguous (LEAVE ALONE — needs human review)
- c*********7@x.test
- u***********q@test.com
- u*********p@test.com
- u**********v@test.com
- a********o@test.com
- b********3@test.com
- p******************5@test.com
- u*********6@x.test
- u*********4@x.test
- u*********4@x.test
- u*********c@x.test
- u*********e@x.test
- u*********c@x.test
- u*********4@x.test
- u*********6@x.test
- u*********0@x.test

## Proposed cleanup (NOT EXECUTED — review required)

```python
# Step 1: mark denylist users with is_test_user=True (additive, reversible)
deny_uids = ['d280a1e6-d4f5-4826-9aa7-8537290e8cb4', '0b62e67b-447d-479e-b522-69ce478378ba', '3abe1f5e-05b0-4b88-ab8b-bbea74506be0', 'da09fd60-8304-4e8b-baf7-35f7a8a1e85f', '28616195-b615-4ce5-a61f-a06f8c73c21b'] ...
db.users.update_many({'id': {'$in': deny_uids}}, {'$set': {'is_test_user': True}})

# Step 2 (later, after observing leaderboard with filter active): hard delete
deny_gids = [g['id'] for g in db.guilds.find({'owner_user_id': {'$in': deny_uids}}, {'id': 1})]
db.adventurers.delete_many({'guild_id': {'$in': deny_gids}})
db.inventory_items.delete_many({'guild_id': {'$in': deny_gids}})
db.expeditions.delete_many({'guild_id': {'$in': deny_gids}})
db.expedition_members.delete_many({})  # cascade left
db.recruitment_offers.delete_many({'guild_id': {'$in': deny_gids}})
db.password_reset_tokens.delete_many({'user_id': {'$in': deny_uids}})
db.refresh_tokens.delete_many({'user_id': {'$in': deny_uids}})
db.login_attempts.delete_many({'email': {'$regex': r'@orbus\.test$'}})
db.guilds.delete_many({'owner_user_id': {'$in': deny_uids}})
db.users.delete_many({'id': {'$in': deny_uids}})
```

## Schema design: `is_test_user`
Add an OPTIONAL field on the `users` collection:
- Field: `is_test_user: bool` (absent = False)
- Set automatically on register if `EMAIL_PROVIDER == 'console'` OR if email matches `@orbus.test$`.
- Leaderboard query already excludes users via guild owner; the recommended pre-filter is added on the GUILDS side: `guilds.is_test_guild` (derived).
- Real beta testers receive normal emails → never get the flag → never excluded.

## Leaderboard preventive filter (proposed, NOT applied)
Modify `/api/leaderboard/guilds` query to exclude guilds where the owner user has `is_test_user == True`. Safe no-op today (no user has the flag).

---

*End of audit report. NO destructive operation executed. Awaiting explicit user confirmation before proceeding to cleanup.*
