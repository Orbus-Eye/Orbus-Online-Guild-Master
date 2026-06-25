# Production Leaderboard Cleanup — Manual Runbook

**File**: `/app/scripts/prod_leaderboard_cleanup.py`
**Purpose**: Apply on production the same cleanup already applied to preview on
2026-06-26 (Round 3 post-deploy). Soft-flag every leaderboard-leaking test
residual + create shadow placeholder users for orphan guilds. **NO hard
delete. Fully reversible.**

The agent (E1) running in preview cannot reach production MongoDB. You,
the user, must execute the script on the prod pod console.

---

## 1. Why this is needed

Smoke test on 2026-06-26 22:18 UTC showed `GET /api/leaderboard/guilds`
returning **47 entries** in production, of which only 4 plausibly belong
to real players (`Drakarys`, `Harambes`, `The Loremaster`, `The Iron
Lantern`). The remaining 43 entries are visible test pollution
(`TEST_*`, `E2E_*`, `UI Test*`, `TEST_P2_*`, etc.) that the
`is_test_user=True` filter cannot catch because their owner accounts
were never flagged.

`Sentiero di Efreto` is not in the top 20 of prod yet (peak likely 0 or
the guild was created on prod but never ran an expedition). Still
protected by allowlist regardless.

`The Loremaster` and `The Iron Lantern` are unknown. The script will
**NOT** touch them — they are explicitly in `PENDING_AMBIGUOUS`.

---

## 2. Copy the script to the prod pod

From the prod pod console (Emergent Dashboard → Orbus → Production → Console):

```bash
# Option A — paste content directly (file is ~360 lines, fits one paste)
cat > /tmp/prod_leaderboard_cleanup.py <<'PYEOF'
<paste the full contents of /app/scripts/prod_leaderboard_cleanup.py>
PYEOF

# Option B — if your prod pod has git access to your repo, pull and run from there
# (we don't enable this by default; ignore if you aren't sure)
```

Verify the script doesn't load unwanted modules:
```bash
python3 -c "import ast; ast.parse(open('/tmp/prod_leaderboard_cleanup.py').read()); print('parse ok')"
```

---

## 3. Dry-run (READ-ONLY, always do this first)

```bash
cd /app/backend  # ensures .env is picked up by python-dotenv
python3 /tmp/prod_leaderboard_cleanup.py
```

Expected output template:
```
── LEADERBOARD AUDIT (read-only) ──
total visible (pre-flag): 47
           allowlist: 2-3      ← Drakarys, Harambes, (maybe Sentiero di Efreto)
   pending_ambiguous: 2        ← The Loremaster, The Iron Lantern
      test_residual: <N>       ← TEST_/E2E_/etc. with a live owner doc
              orphan: <M>      ← TEST_/E2E_/etc. whose owner was deleted
        unknown_real: 0        ← MUST be 0 to safely --apply
⚠  PENDING_AMBIGUOUS — explicitly held for user review:
  • The Loremaster ...
  • The Iron Lantern ...
✅ ALLOWLIST (will stay visible):
  • Drakarys ...
  • Harambes ...
(dry-run — pass --apply to write. NO writes performed.)
```

**If `unknown_real > 0`**: STOP. Send the list to the agent. The script
refuses to flag anything it can't classify with high confidence — those
guilds need explicit user decision.

---

## 4. Apply

Only after the dry-run looks right:

```bash
python3 /tmp/prod_leaderboard_cleanup.py --apply
```

The script will:
1. Drop a backup JSON to `/tmp/prod_leaderboard_residual_flag_backup_<UTC>.json`
   BEFORE any write. **Save this file somewhere durable** (download it from
   the pod) — it's your rollback fuel.
2. `update_many` with `$set: {is_test_user: True}` on every user in
   `test_residual`. Allowlist intersection is double-checked first; the
   script aborts with exit-code 3 if any leak is detected.
3. `insert_one` a shadow placeholder for each unique orphan
   `owner_user_id`. The shadow has the same `id`, `is_test_user=True`,
   and `password_hash="$ORPHAN_PLACEHOLDER$"`. The leaderboard service
   then automatically excludes these via its existing
   `$nin test_owner_ids` filter — **no code change required**.
4. Re-runs the leaderboard count: should equal
   `len(allowlist) + len(pending_ambiguous) + len(unknown_real)`.

Re-running `--apply` is idempotent. It will skip users already flagged
and shadow ids already present.

---

## 5. Verify post-apply

```bash
# from the prod pod
curl -s https://orbusonline.net/api/leaderboard/guilds?limit=20 | jq '.entries[] | {name: .guild_name, peak: .max_team_power_ever}'
```

Expected: only Drakarys, Harambes, The Loremaster, The Iron Lantern,
plus Sentiero di Efreto if mr.gualmini has a guild on prod with peak>0.

---

## 6. Rollback

If anything looks wrong (e.g. a guild you expected to stay disappears):

```bash
python3 /tmp/prod_leaderboard_cleanup.py --rollback /tmp/prod_leaderboard_residual_flag_backup_<UTC>.json
```

This:
- `$unset is_test_user` on each user originally listed in `users_flagged`,
- `delete_many({password_hash: "$ORPHAN_PLACEHOLDER$", id ∈ orphan_ids})`
  for the shadow placeholders.

The rollback NEVER touches users not in the backup file, so allowlist /
real-player accounts are always safe. Sentinel check: rollback aborts
if the backup's `shadow_pw_sentinel` doesn't match (exit 4).

---

## 7. Allowlist scope (hardcoded in the script)

```python
ALLOWLIST_EMAILS = {
    "mr.gualmini@gmail.com",
    "gianluca.brandi42@gmail.com",
    # PENDING: Harambes owner email
    "tester@orbus.test",
}
ALLOWLIST_GUILDS = {
    "sentiero di efreto",
    "drakarys",
    "harambes",          # name-based protection while email pending
}
PENDING_AMBIGUOUS = {
    "the loremaster",
    "the iron lantern",
}
```

When the user provides the Harambes owner email, update this list in
the script AND in `/app/backend/tests/conftest.py`,
`/app/scripts/db_cleanup_phase14_3.py`, `/app/memory/ALLOWLIST.md`.

---

## 8. Hard guards in the script

- Refuses to run when `MONGO_URL` points to `localhost`, `127.0.0.1`, or
  contains `/test_database` (preview heuristic). Override only with
  `--allow-preview` on a deliberate preview re-run.
- Refuses to flag any user whose email is in `ALLOWLIST_EMAILS` (post-
  classification leak check before the bulk update).
- Refuses to rollback a backup whose `shadow_pw_sentinel` doesn't
  match. Sentinel is a constant string the script is the only writer of.
- Default is dry-run. `--apply` is required to write.

---

## 9. Sign-off checklist

| Step | Done | Time |
| --- | --- | --- |
| Copied script to /tmp on prod pod | | |
| `python3 -c "ast.parse..."` smoke | | |
| Dry-run output looks correct | | |
| `unknown_real == 0` | | |
| `--apply` executed | | |
| Backup downloaded to local machine | | |
| `/api/leaderboard/guilds` shows only real players | | |
| (optional) Harambes email provided + allowlist updated | | |

---

*Generated 2026-06-26 (Round 3 post-deploy assist).*
