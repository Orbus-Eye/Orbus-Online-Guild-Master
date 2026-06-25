# Production DB Audit — Manual Instructions

**Why this file exists:** the agent (E1) running in the preview pod only
has access to the **preview MongoDB** (`mongodb://localhost:27017/test_database`).
The production `orbusonline.net` deployment uses a different MongoDB
cluster whose connection string is set via the Emergent production
dashboard and is NOT visible from this environment.

The cleanup performed in this session (flag 210 denylist + 16 ambiguous,
delete 3582 orphan guilds) was applied to the **preview DB only**. To
mirror it on production you must either:

1. **Run the same scripts on the prod pod**, or
2. **Audit prod first** and only then decide what to do.

This document is option (2): a read-only audit you can run yourself.

---

## Prerequisites

You need:
- access to the production pod shell (Emergent dashboard → Production → Logs/Console), OR
- the production `MONGO_URL` value (visible in the prod env panel) plus a host
  where you can run Python with `motor`+`dotenv` installed.

**DO NOT** copy the production `MONGO_URL` into the preview pod's
`/app/backend/.env`. That would re-route the preview backend to write to
production. Use the prod pod or a dedicated workstation.

## Audit script (copy-paste, read-only)

Save as `prod_audit.py` next to the prod env file and run with
`python3 prod_audit.py`. It performs ZERO writes.

**ROUND 1.5 update (2026-06-25)**: the script now also reports
- count of canonical Italian traits present (expected: 10),
- count of legacy/test trait docs (`is_test=True` or `is_active=False`),
- count of adventurer documents that still embed a test-pattern trait name.

These three counters are what we need to decide whether to run
`db_cleanup_phase14_3.py` on prod or skip it.

```python
"""Read-only production DB audit — Orbus Online (ROUND 1.5)."""
import asyncio, json, re
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import dotenv_values

# Adjust path to wherever the prod .env lives on the pod
env = dotenv_values("/app/backend/.env")
ALLOW = "mr.gualmini@gmail.com"

_DENY_CONTAINS = (
    "@orbus.test", "tester@", "+smoke", "+smoketest", "+welcometest",
    "+secrettest", "+pwd", "+e2e",
    "@example.com", "@example.org", "@test.local",
)
_DENY_STARTS = ("smoke", "smoketest", "welcometest", "secrettest",
                "pytest", "qa-", "dev-")
_AMBIG_DOMAINS = ("@x.test", "@test.com", "@test.org")

# Phase 14.3-c — same regex used by seed_runner to detect test trait names.
_TEST_TRAIT_NAME_RE = re.compile(
    r"^(Test|TEST_|qa_|dev_|pytest_)|_[a-f0-9]{6,}$|^[a-f0-9-]{16,}$",
    re.IGNORECASE,
)
CANONICAL_IT_CODES = {
    "lucky", "brave", "disciplined", "sharp_eye", "reckless",
    "fragile", "greedy", "loyal", "clumsy", "inspired",
}


def classify(email: str) -> str:
    e = (email or "").strip().lower()
    if e == ALLOW.lower():
        return "allowlist"
    if any(s in e for s in _DENY_CONTAINS):
        return "denylist"
    local = e.split("@", 1)[0]
    if any(local.startswith(s) for s in _DENY_STARTS):
        return "denylist"
    if any(d in e for d in _AMBIG_DOMAINS):
        return "ambiguous"
    return "real"


def mask(email):
    if not email or "@" not in email:
        return "***"
    local, _, dom = email.partition("@")
    return (local[0] + "*" * max(1, len(local) - 2) + (local[-1] if len(local) > 1 else "")) + "@" + dom


async def main():
    cli = AsyncIOMotorClient(env["MONGO_URL"])
    db = cli[env["DB_NAME"]]

    users = await db.users.find({}, {"id": 1, "email": 1, "is_test_user": 1}).to_list(None)
    living_ids = {u["id"] for u in users}

    buckets = {"allowlist": 0, "denylist": 0, "ambiguous": 0, "real": 0}
    for u in users:
        buckets[classify(u.get("email", ""))] += 1

    total_guilds = await db.guilds.count_documents({})
    orphan_guilds = await db.guilds.count_documents(
        {"owner_user_id": {"$nin": list(living_ids)}}
    )

    flagged = await db.users.count_documents({"is_test_user": True})

    allow = await db.users.find_one({"email": ALLOW}, {"id": 1, "is_test_user": 1})
    sentiero = await db.guilds.find_one(
        {"name": "Sentiero di Efreto"},
        {"id": 1, "owner_user_id": 1, "max_team_power_ever": 1},
    )

    # Top-10 leaderboard sample (matches the public API behaviour)
    top10 = await (
        db.guilds.find(
            {}, {"_id": 0, "name": 1, "owner_user_id": 1,
                 "max_team_power_ever": 1, "level": 1}
        )
        .sort([("max_team_power_ever", -1), ("level", -1)])
        .limit(10)
        .to_list(10)
    )
    by_uid = {u["id"]: u for u in users}
    top10_view = []
    for g in top10:
        owner = by_uid.get(g.get("owner_user_id"))
        top10_view.append({
            "guild": g["name"],
            "peak": g.get("max_team_power_ever", 0),
            "owner_email_masked": mask(owner["email"]) if owner else "(orphan)",
            "owner_class": classify(owner["email"]) if owner else "orphan",
            "owner_is_test_user": (owner or {}).get("is_test_user", False),
        })

    # ── ROUND 1.5 — trait inventory ────────────────────────────────────
    traits_all = await db.adventurer_traits.find({}, {"_id": 0}).to_list(None)
    canonical_it_present = sorted({
        t.get("code") for t in traits_all
        if t.get("code") in CANONICAL_IT_CODES
    })
    test_flagged = sum(1 for t in traits_all if t.get("is_test"))
    inactive_flagged = sum(1 for t in traits_all if t.get("is_active") is False)
    name_matches_test_pattern = sum(
        1 for t in traits_all
        if _TEST_TRAIT_NAME_RE.search(t.get("display_name") or t.get("name") or "")
    )

    # Adventurers that still embed a trait whose display_name/name matches
    # the test pattern (anti-leak guard from ROUND 1).
    adv_with_test_traits = 0
    async for adv in db.adventurers.find(
        {"traits": {"$exists": True, "$ne": []}},
        {"id": 1, "traits": 1},
    ):
        for tr in adv.get("traits", []):
            label = (tr.get("display_name") or tr.get("name") or "") if isinstance(tr, dict) else str(tr)
            if _TEST_TRAIT_NAME_RE.search(label):
                adv_with_test_traits += 1
                break

    report = {
        # users & guilds (existing checks)
        "users_total": len(users),
        "users_classified": buckets,
        "users_flagged_is_test_user": flagged,
        "guilds_total": total_guilds,
        "guilds_orphan": orphan_guilds,
        "allowlist_present": bool(allow),
        "allowlist_is_test_user": (allow or {}).get("is_test_user", False),
        "sentiero_present": bool(sentiero),
        "sentiero_peak": (sentiero or {}).get("max_team_power_ever", "?"),
        "leaderboard_top10_with_owner_classification": top10_view,
        # ROUND 1.5 — trait audit
        "traits_total": len(traits_all),
        "traits_canonical_it_present": canonical_it_present,
        "traits_canonical_it_missing": sorted(
            CANONICAL_IT_CODES - set(canonical_it_present)
        ),
        "traits_flagged_is_test": test_flagged,
        "traits_flagged_inactive": inactive_flagged,
        "traits_name_matches_test_pattern": name_matches_test_pattern,
        "adventurers_with_test_pattern_trait": adv_with_test_traits,
    }
    print(json.dumps(report, indent=2, default=str))
    cli.close()


asyncio.run(main())
```

## What to send back

Run the script, redact any complete email or hash, and send me back the
JSON output. From there I can decide whether to:

- apply the same cleanup on prod (mirror script `/app/scripts/db_cleanup_phase14_3.py`),
- adapt the denylist if prod has different test patterns,
- or hold off if prod is already clean.

## Safety reminders

- The script above is **read-only** (only `find` / `count_documents`).
- Do NOT run `db_cleanup_phase14_3.py` on prod until after this audit.
- Do NOT print full emails, password hashes, or tokens in any output
  you share back. Masked output is fine.
- The leaderboard patch in `app/leaderboard/services.py` (filter on
  `is_test_user`) is already in the codebase — it will start filtering
  as soon as the prod redeploy happens AND prod users get flagged.
  Without the flag, the filter is a no-op (safe).

---

*Generated 2026-06-25. Re-run the audit whenever you want — it never writes.*
