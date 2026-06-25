# Production Deploy Troubleshooting — Round 3 (orbusonline.net)

## TL;DR

The post-deploy smoke run on **2026-06-26 22:18 UTC** showed that the
production environment is **NOT running the Round 3.A+B+D build**:

| Check | Got | Expected |
| --- | --- | --- |
| `GET /api/health` `.env` | `"development"` | `"production"` |
| `GET /api/openapi.json paths.length` | **43** | **45** |
| `/api/recipes` present in paths | ❌ no | ✅ yes |
| `/api/recipes/{recipe_slug}/craft` present | ❌ no | ✅ yes |
| `GET /` `<title>` | `"Orbus Online: Guild Master"` | ✅ same |
| `/api/leaderboard/guilds` total | `47` (43+ test residuals) | will be ~4 after cleanup |

Conclusion: either the Round 3 redeploy on Emergent was **not actually
triggered**, or it ran against an old commit, or it failed silently.

The agent (E1) has **no autonomous deploy capability**: no
`emergent`/`emergentctl` CLI on the pod, no git remote, no CI/CD config,
no Dockerfile/compose. The only deploy lever is your Emergent dashboard.

---

## Symptoms in detail

### S1 — `env=development` on prod
```
$ curl -s https://orbusonline.net/api/health
{"status":"ok","env":"development"}
```
Means: the prod backend container does **not** see `APP_ENV=production`.

Either:
- the env var is missing from the prod env panel, or
- the deploy hasn't picked up a `.env` change, or
- the var was overridden by a default elsewhere.

This alone is not catastrophic (no business logic branches on it today,
only the health string), but it strongly suggests the env panel and the
running container are out of sync.

### S2 — OpenAPI path count stuck at 43
Pre-Round-3 baseline: **43** paths.
Post-Round-3 baseline: **45** paths (adds `/api/recipes` and
`/api/recipes/{recipe_slug}/craft`).

The script that asserts this in preview:
```python
# /app/backend/tests/backend_phase14_6_round3ab_test.py:304
assert len(paths) == 45, f"expected 45, got {len(paths)}"
```
runs green on preview, fails on prod (because prod returns 43).

### S3 — No `recipes` paths
```
$ curl -s https://orbusonline.net/api/openapi.json | jq '.paths | keys[]' | grep -E 'recipes|craft'
(no output)
```
Hard confirmation: the Round 3 code is not loaded in the running prod
container.

---

## Debug checklist (operate from your Emergent dashboard)

### Step 1 — Verify last deploy timestamp
1. Open **Emergent Dashboard → Orbus → Deploy → `orbusonline.net`**.
2. Note the **"Last Deploy"** timestamp.
3. If it is **earlier than 2026-06-25 21:00 UTC** (when ROUND 3 was
   committed to preview), the redeploy never happened.
4. If it is **after** that timestamp but `/api/openapi.json` still
   returns 43, the build picked up the wrong commit OR failed to restart
   the backend container.

### Step 2 — Read build logs
1. From the same Deploy panel, open the most recent build's logs.
2. Look for the line that comes from `server.py` on startup:
   ```
   Phase 14.6: seeded 17 IT items + 5 recipes (idempotent)
   ```
   If this line is **NOT present**, the prod container is running an
   older commit that doesn't have `seed_runner.py:Phase 14.6`.
3. Look for any failure such as `pip install` errors,
   `motor`/`pymongo` mismatches, missing env vars, or a crash loop.

### Step 3 — Verify env panel
Open **Emergent Dashboard → Orbus → Environment**. Confirm these are set
on the production environment (not preview!):

| Var | Required value |
| --- | --- |
| `APP_ENV` | `production` |
| `APP_BASE_URL` | `https://orbusonline.net` |
| `MONGO_URL` | (prod cluster URI) |
| `DB_NAME` | (prod DB name) |
| `JWT_SECRET` | (prod secret — never log) |
| `EMAIL_PROVIDER` | `smtp` |
| `SMTP_HOST` | `smtp.ionos.it` |
| `SMTP_USERNAME` | `support@orbusonline.net` |
| `SMTP_PASSWORD` | (IONOS mailbox password — never log) |
| `EMAIL_FROM` | `Orbus Online <support@orbusonline.net>` |
| `EMAIL_REPLY_TO` | `support@orbusonline.net` |
| `SEND_WELCOME_EMAIL` | `true` |
| `CORS_ORIGINS` | (prod origins) |

The visible "env=development" in `/api/health` is hard evidence that
`APP_ENV` is NOT set on prod. Add it explicitly.

### Step 4 — Force a fresh redeploy
1. Make sure your dashboard is pointing at the commit you intend to
   deploy (the one with `app/crafting/`, `app/audit/`,
   `app/seeds/seed_items_it.py`, `app/seeds/seed_recipes_it.py`).
2. Click **Redeploy**. Watch the logs live until you see
   `Orbus backend ready (env=production)`.
3. As soon as the deploy reports healthy, ping the agent with
   "deploy fatto, ricontrolla". The agent will re-run the 5 smoke curls.

### Step 5 — If the build keeps failing
Copy-paste the failing logs into chat. Common Round 3 failure modes the
agent has playbooks for:
- `motor`/`pymongo` ABI mismatch on Python 3.11+
- Stripe key missing (not used by Round 3, can be ignored)
- `seed_runner.py` raising on an index conflict (means a prior partial
  deploy created some indexes — easy fix).

---

## What changes once the deploy is live

| Endpoint | Pre-Round-3 | Post-Round-3 |
| --- | --- | --- |
| `GET /api/openapi.json` paths.length | 43 | **45** |
| `GET /api/recipes` | 404 | **401 without auth, 200 with auth** |
| `POST /api/recipes/{slug}/craft` | 404 | **401 without auth, 200/4xx with auth** |
| `GET /api/inventory` | 200 (legacy items) | 200 (legacy + IT items + Material badge data) |
| `audit_log` collection | absent | auto-created on first economy event |
| `items.count(slug ∈ italian_slugs)` | 0 | **17** |
| `recipes.count(is_active=True, is_test ≠ True)` | 0 | **5** |
| `/api/health` `.env` | unchanged from current | `production` ONLY if env var is set |

The `audit_log` collection is created lazily by the first
`loot_awarded` / `item_crafted` / `gold_*` event, not on startup, so an
empty collection right after deploy is **expected** and not a problem.
`prod_audit.py` has a counter (`audit_log_exists`) that flips to `True`
the moment the collection appears.

---

## Sign-off checklist (post-fix)

| Owner | Action | Status |
| --- | --- | --- |
| User | DB snapshot taken | □ |
| User | env panel confirmed (`APP_ENV=production`) | □ |
| User | Redeploy triggered | □ |
| User | Build logs show `Phase 14.6: seeded 17 IT items + 5 recipes` | □ |
| User | `/api/health` returns `env=production` | □ |
| User | Ping agent "deploy fatto" | □ |
| Agent | 5 smoke curls pass | □ |
| User | Run `prod_leaderboard_cleanup.py` dry-run | □ |
| User | Apply + backup the leaderboard cleanup | □ |

---

## Related files

- `/app/scripts/prod_leaderboard_cleanup.py` — twin of the preview op
- `/app/memory/PROD_LEADERBOARD_CLEANUP_INSTRUCTIONS.md` — runbook
- `/app/memory/PROD_DEPLOY_CHECKLIST_ROUND_3.md` — deploy checklist
- `/app/memory/PROD_AUDIT_INSTRUCTIONS.md` — read-only prod DB audit script
- `/app/memory/ALLOWLIST.md` — permanent allowlist (incl. Harambes pending)

---

*Generated 2026-06-26 (Round 3 post-deploy assist).*
