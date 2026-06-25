# Production restore — Drakarys (gianluca.brandi42@gmail.com)

**Date prepared:** 2026-06-25 21:10 UTC
**Scope:** PRODUCTION ONLY (`orbusonline.net`). The agent that wrote this
file has NO access to the production database. You (the project owner) must
run the steps below from the prod pod console.

## TL;DR — what the agent already verified (preview side)

- `gianluca.brandi42@gmail.com` is **NOT** in the preview MongoDB.
- `Drakarys` is **NOT** in any cleanup backup (`db_pre_cleanup_backup.json`,
  `db_ambiguous_flag_backup.json`).
- The pytest pollution sweep regex does **NOT** match the email
  (`gianluca.brandi42@gmail.com` does not start with any test prefix and is
  on `@gmail.com`) nor the guild name (`Drakarys` does not match any test
  pattern).
- The agent's cleanup scripts (`db_cleanup_phase14_3.py`) ran at
  `2026-06-25T18:58` UTC, hours before the user's reported registration.

**Conclusion:** the user almost certainly registered on
**production** (`orbusonline.net`), not on preview. The preview cleanup
could not have affected them. Step 1 below confirms or denies this.

## Step 0 — Pull the latest preview code into prod

The patches you need in prod for this hotfix are code-only and additive:

| File | What changed |
| --- | --- |
| `/app/backend/tests/conftest.py` | Hardcoded `ALLOWLIST_EMAILS` + `ALLOWLIST_GUILDS_LOWER`; pollution sweep `$nin` filters. **Only affects pytest** — has no effect on a running prod backend. |
| `/app/scripts/db_cleanup_phase14_3.py` | `classify()` returns "allowlist" for any of the new emails. |
| `/app/memory/ALLOWLIST.md` | This document + the master list. |

No OpenAPI change. No env var change. No DB migration in the runtime path.
You can ship this with the next regular redeploy (it does not need its own
release).

## Step 1 — Verify Drakarys exists in production

Run this **read-only** check from the prod pod (or any host with prod
`MONGO_URL` configured):

```python
"""Drakarys prod presence check — READ-ONLY."""
import os, asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import dotenv_values

env = dotenv_values("/app/backend/.env")  # prod .env path

async def main():
    cli = AsyncIOMotorClient(env["MONGO_URL"])
    db = cli[env["DB_NAME"]]
    u = await db.users.find_one(
        {"email": "gianluca.brandi42@gmail.com"},
        {"_id": 0, "id": 1, "email": 1, "username": 1,
         "is_test_user": 1, "created_at": 1},
    )
    print("user:", u)
    if u:
        gs = await db.guilds.find(
            {"owner_user_id": u["id"]},
            {"_id": 0, "id": 1, "name": 1, "level": 1, "gold": 1,
             "max_team_power_ever": 1, "created_at": 1},
        ).to_list(10)
        print("guilds:", gs)
        # quick collateral count
        if gs:
            gid = gs[0]["id"]
            print("adventurers:",     await db.adventurers.count_documents({"guild_id": gid}))
            print("inventory_items:", await db.inventory_items.count_documents({"guild_id": gid}))
            print("equipped_items:",  await db.equipped_items.count_documents({"guild_id": gid}))
            print("expeditions:",     await db.expeditions.count_documents({"guild_id": gid}))
            print("recruitment_offers:", await db.recruitment_offers.count_documents({"guild_id": gid}))
    cli.close()

asyncio.run(main())
```

### Interpretation

| Result | What to do |
| --- | --- |
| User found, guild "Drakarys" found, `is_test_user` absent or False | **No restore needed.** Drakarys is intact in prod. Apply Step 2 (allowlist hardening) and Step 4 (verify leaderboard) only. |
| User found, but `is_test_user=True` flagged | Run Step 3 (un-flag). |
| User found, but no guild | Real user lost their guild somehow (NOT due to our cleanup — backups are clean). Step 5 (restore guild from scratch only after talking to Gianluca). |
| User NOT found at all | Either Gianluca never completed registration (email mistype on his side), or there's a deeper issue. **Stop and contact Emergent Support** with this report — we want their DB ops to check audit logs before any creation from scratch. |

## Step 2 — Apply the allowlist hardening to prod (idempotent)

If your prod conftest is identical to the preview one, the pollution sweep
now refuses to touch the allowlist. If you have prod-specific scripts that
delete users or guilds, audit them and import:

```python
ALLOWLIST_EMAILS = {
    "mr.gualmini@gmail.com",
    "gianluca.brandi42@gmail.com",
    "tester@orbus.test",
}
ALLOWLIST_GUILDS_LOWER = {"sentiero di efreto", "drakarys"}
```

Add `$nin` filters on `email` and `owner_user_id` to every destructive
operation. This is purely defensive — Drakarys was NOT caught by these
filters before, but adding them prevents any future regex widening from
hitting them.

## Step 3 — Un-flag if accidentally marked test

If Step 1 returned `is_test_user=True`:

```python
res = await db.users.update_one(
    {"email": "gianluca.brandi42@gmail.com"},
    {"$unset": {"is_test_user": ""}},
)
print("unflagged:", res.modified_count)
```

Drakarys reappears in the leaderboard at the next page load (filter is
runtime, no cache).

## Step 4 — Verify leaderboard visibility

```bash
curl -s https://orbusonline.net/api/leaderboard/guilds?limit=50 | \
  python3 -c "import sys, json; d=json.load(sys.stdin); \
    print([g['name'] for g in d.get('guilds', d.get('leaderboard', [])) \
           if 'drakarys' in g.get('name','').lower() or 'sentiero' in g.get('name','').lower()])"
```

Expected output: `['Sentiero di Efreto', 'Drakarys']` (in some order
depending on `max_team_power_ever`).

## Step 5 — Recreation from scratch (LAST RESORT, only with user consent)

If Drakarys is truly missing from prod, **do NOT auto-create**. Reach out to
Gianluca directly:

> Ciao Gianluca, abbiamo verificato l'account `gianluca.brandi42@gmail.com`
> e non lo troviamo nel nostro database di produzione. È possibile che la
> registrazione si sia interrotta. Ti vorremmo aiutare a ricreare l'account
> con un piccolo bonus di scuse (oro extra). Puoi confermarmi che vorresti
> rifare la registrazione su https://orbusonline.net e che il nome guild
> "Drakarys" è ancora libero?

When he confirms, just send a password reset link with a fresh registration
flow. Do NOT manually insert a user document — it would skip bcrypt
hashing and break login.

## Step 6 — Sign-off checklist (prod)

- [ ] Step 1 run, output captured
- [ ] Outcome documented in this file (append below)
- [ ] If user found: Step 2 + Step 4 done, leaderboard verified
- [ ] If user not found: contacted Gianluca, awaiting reply
- [ ] No `delete_many` operation executed during this audit

## Append-only log

| Date | Operator | Step | Outcome |
| --- | --- | --- | --- |
| 2026-06-25 21:10 | E1 (agent) | Steps prepared for prod execution | Drakarys NOT in preview DB; preview cleanup not at fault. |
| | | | |
