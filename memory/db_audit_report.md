# DB Audit Report — Orbus Online
**Date:** 2026-06-25
**Mode:** READ-ONLY (no DELETE performed)
**Scope:** Identify smoke/test users and orphan records polluting prod data.

---

## 1. Totals (before any cleanup)

| Collection | Count |
| --- | --- |
| users | 227 |
| guilds | 3803 |

## 2. Anomaly explained: why 3803 guilds for 227 users?

Quick analysis of `guilds.owner_user_id` against the live `users.id` set:

| Bucket | Count |
| --- | --- |
| guilds with a valid (still-existing) owner | **221** |
| **orphan guilds** (owner_user_id no longer in `users`) | **3582** |
| distinct living owners | 221 |
| living owners with more than 1 guild | 0 |

The unique index `guilds_owner_unique` is intact (verified): no living user
owns more than one guild. The 1:1 invariant is respected for the active
population.

**Root cause of the 3582 orphans:** Historical pytest / load-test runs
created users + guilds, then `users.delete_many(...)` was called WITHOUT
cascading on `guilds` (no FK in Mongo, no transactional cleanup). The
guilds remained, pointing at user ids that no longer exist. A sample:

```
{ name: "Guild_ref_poor_a3c5cdd3",
  owner_user_id: "00002a46-545c-48f2-b69d-c536f085f768",   ← gone
  created_at: "2026-06-24T23:02:44.902705+00:00" }
```

The naming pattern `Guild_ref_poor_*`, `Guild_<scenario>_<hex>` is the
pytest fixture signature in `/app/backend/tests/`. So 100% of orphans are
test residue, never used by a real player.

**Index health:** `_id_`, `guilds_id_unique`, `guilds_owner_unique`,
`guilds_name_idx`, `guilds_leaderboard_idx` — all present, consistent
with `server.py` startup. No corruption.

## 3. User-side breakdown of the 221 living owners

| Category | Count | Notes |
| --- | --- | --- |
| Allowlist (real beta tester) | 1 | `Gualma` / `mr.gualmini@gmail.com` |
| Denylist (smoke / `@orbus.test`) | 210 | safe to remove |
| Ambiguous (`@test.com`, `@x.test`) | 16 | needs human review |

Cross-checked against `owners_with_email_breakdown`:
real=1 · `@orbus.test`=207 · other-test=13. The 207 + 13 + 1 = 221 ≈
distinct living owners. Delta vs. denylist (210 vs. 207) explained by 3
extra users matching denylist by username pattern but with non-`.test`
email (already classified in `denylist` above).

## 4. Collateral records owned by denylist users

| Collection | Records owned by denylist | Notes |
| --- | --- | --- |
| guilds | 207 | (subset of the 221 living-owner guilds) |
| guilds (extra by name pattern, owner already gone) | 3 | edge cases |
| adventurers | 229 | inside deny-owned guilds |
| inventory_items | 0 | none yet |
| expeditions | 44 | mostly Goblin Warrens smoke runs |

Plus the **3582 orphan guilds** (owners already deleted) — separate
bucket, deletable independently.

## 5. Allowlist (KEEP — real beta tester)

- `m*********i@gmail.com` · username=`Gualma`

## 6. Denylist samples (CANDIDATES for cleanup, 210 users total)

- `t****r@orbus.test` (tester admin — KEEP if used by QA, otherwise delete)
- `l*******_@orbus.test`
- `d********0@orbus.test`
- `o*************f@orbus.test`
- `o**************e@orbus.test`
- `o***************b@orbus.test`
- `o*****************5@orbus.test`
- … plus 203 more `@orbus.test` accounts (auto-generated)

## 7. Ambiguous (LEAVE ALONE — needs human review, 16 users)

- `c*********7@x.test`
- `u***********q@test.com`
- `u**********v@test.com`
- `a********o@test.com`
- `b********3@test.com`
- `p******************5@test.com`
- `u*********6@x.test` × 10 more variants

---

## 8. Proposed cleanup (NOT EXECUTED — review required)

### 8.a Step 1 — additive, reversible: flag denylist users

```python
# Run inside a mongo shell or a backend script.
deny_uids = [<resolved at audit time>]   # 210 ids
db.users.update_many(
    {"id": {"$in": deny_uids}},
    {"$set": {"is_test_user": True}},
)
```

This is **reversible**: a single `$unset` undoes it. Use this first and
observe the leaderboard with the preventive filter (§10) for 24h before
moving on.

### 8.b Step 2 — hard delete of orphan guilds (high impact, low risk)

Orphan guilds have no living owner → no user can possibly miss them.

```python
living_user_ids = [u["id"] for u in db.users.find({}, {"id": 1})]
orphan_guild_ids = [
    g["id"] for g in db.guilds.find(
        {"owner_user_id": {"$nin": living_user_ids}},
        {"id": 1},
    )
]   # ≈ 3582 ids

db.adventurers.delete_many({"guild_id": {"$in": orphan_guild_ids}})
db.inventory_items.delete_many({"guild_id": {"$in": orphan_guild_ids}})
db.expeditions.delete_many({"guild_id": {"$in": orphan_guild_ids}})
db.expedition_members.delete_many({"guild_id": {"$in": orphan_guild_ids}})
db.recruitment_offers.delete_many({"guild_id": {"$in": orphan_guild_ids}})
db.guilds.delete_many({"id": {"$in": orphan_guild_ids}})
```

Expected drop: `guilds` 3803 → ~221.

### 8.c Step 3 — hard delete denylist users + their guilds (only after §8.a observation period)

```python
deny_uids = [<same list as 8.a>]
deny_gids = [
    g["id"]
    for g in db.guilds.find({"owner_user_id": {"$in": deny_uids}}, {"id": 1})
]

db.adventurers.delete_many({"guild_id": {"$in": deny_gids}})
db.inventory_items.delete_many({"guild_id": {"$in": deny_gids}})
db.expeditions.delete_many({"guild_id": {"$in": deny_gids}})
db.expedition_members.delete_many({"guild_id": {"$in": deny_gids}})
db.recruitment_offers.delete_many({"guild_id": {"$in": deny_gids}})
db.password_reset_tokens.delete_many({"user_id": {"$in": deny_uids}})
db.refresh_tokens.delete_many({"user_id": {"$in": deny_uids}})
db.login_attempts.delete_many({"email": {"$regex": r"@orbus\.test$"}})
db.guilds.delete_many({"owner_user_id": {"$in": deny_uids}})
db.users.delete_many({"id": {"$in": deny_uids}})
```

Expected drop: `users` 227 → ~17 (allowlist + ambiguous).

> **None of the snippets above were executed.** They are documented for
> the operator (you) to run after explicit approval.

---

## 9. Schema design: `is_test_user`

Add an OPTIONAL field on the `users` collection:

- Field: `is_test_user: bool` (absent ≡ False — additive, no migration)
- Set automatically on register when EITHER:
  - `EMAIL_PROVIDER == "console"` (no real email backend available), or
  - the email matches `r"@orbus\.test$"` (canonical test domain).
- Real beta testers receive real emails through the SMTP path → flag
  remains absent → never excluded.
- The flag can be set retroactively (Step 8.a) without touching guilds:
  the preventive leaderboard filter operates on the guild-owner join.

## 10. Leaderboard preventive filter (PROPOSED, NOT applied)

Goal: keep flagged users out of the public ranking without deleting
their data.

Modify the leaderboard query in `app/leaderboard/router.py` (or
equivalent) so that the guild list is left-joined to the owner and
filtered:

```python
pipeline = [
    {"$lookup": {
        "from": "users",
        "localField": "owner_user_id",
        "foreignField": "id",
        "as": "owner",
    }},
    {"$match": {
        "owner.is_test_user": {"$ne": True},
    }},
    # ... existing sort / limit / project ...
]
```

Safe no-op today: no user has the flag set, so the result set is
unchanged. Once `is_test_user=True` is applied (Step 8.a), the
leaderboard immediately stops showing those guilds, even before the
hard delete in Step 8.b/c.

**Decision recommended:** apply this filter as a one-line preventive
guard in a future patch (Phase 14.3), in parallel with the additive
flag — it costs nothing today and makes the cleanup zero-downtime.

---

*End of audit report. NO destructive operation executed. Awaiting
explicit user confirmation before proceeding to cleanup steps 8.a / 8.b
/ 8.c.*
