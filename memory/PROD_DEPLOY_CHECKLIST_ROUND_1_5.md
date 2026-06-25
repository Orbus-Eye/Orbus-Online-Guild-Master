# Production Deploy Checklist — ROUND 1 + ROUND 1.5
### Target: `https://orbusonline.net`
### Date: 2026-06-25

This document supersedes `PROD_DEPLOY_CHECKLIST.md` for the upcoming deploy.
Older deploy notes (SMTP env setup) remain valid and were already applied —
those settings DO NOT need to be re-applied.

---

## 1. What's shipping in this redeploy

### ROUND 1 — anti-leak trait + dungeon preview (already in code)
- Canonical Italian trait catalog (10 entries, upsert by `code`).
- Regex-driven anti-leak that flags any trait whose `display_name`/`name`
  matches `^(Test|TEST_|qa_|dev_|pytest_)|_[a-f0-9]{6,}$|^[a-f0-9-]{16,}$`
  as `is_test=True is_active=False`.
- Recruitment + adventurer projections drop test-flagged traits at read time
  (`trait_public_filtered_list`).
- New endpoint `POST /api/expeditions/preview` returning estimated success
  chance, injury risk and modifiers BEFORE actually dispatching.

### ROUND 1.5 — UX clarity (frontend-only, no new endpoints)
- Reusable `PasswordInput` with show/hide eye toggle (Login, Register,
  PasswordResetConfirm).
- Confirm-password field on Register, client-side validation EN+IT.
- `AdventurerDetailModal` (click roster row → full sheet with XP bar, stats,
  traits, per-slot equipment).
- Inventory: explicit requirements (`Lvl ≥ N`, slot), status badges
  (`Available × N`, `Equipped by …`), contextual equip buttons per eligible
  adventurer.
- `Empty` state of Adventurers no longer crashes on a brand-new roster
  (pre-existing `t()` scope bug fixed in passing).

### Backend invariants kept
- OpenAPI path count: **43** (40 baseline + trait-preview + dungeon preview).
- No schema changes to existing endpoints.
- Seeds are idempotent (`update_one({..}, {"$setOnInsert", "$set"}, upsert=True)`).
- Tester seed gated by `APP_ENV` (`APP_ENV=production` → seed skipped).

---

## 2. Pre-deploy verification (preview, already done)

| Check | Status |
| --- | --- |
| `yarn build` frontend | ✅ Compiled successfully (190 kB gz) |
| ESLint on touched files | ✅ No issues |
| pytest `backend_phase14_4_round15_test.py` | ✅ 5/5 |
| pytest `backend_phase14_3_traits_preview_test.py` (ROUND 1) | ✅ 9/9 |
| pytest `backend_phase9_leaderboard_test.py` (Step A2) | ✅ 5/5 |
| pytest `backend_phase931_security_test.py::TestPhase931OpenAPI` | ✅ 11/11 |
| Preview `/api/health` | ✅ `{"status":"ok","env":"development"}` |
| Preview `/api/openapi.json` path count | ✅ 43 |
| Preview `/api/leaderboard/guilds` | ✅ 0 visible (test users filtered) |
| Seed idempotency (double boot) | ✅ "no legacy test traits to flag" on 2nd run |

---

## 3. Production environment variables

The variables from the previous SMTP rollout (already in prod) MUST stay
in place. ROUND 1 / ROUND 1.5 introduce **no new env vars**.

### Required (must already be set)
```env
APP_BASE_URL="https://orbusonline.net"
APP_ENV="production"

EMAIL_PROVIDER="smtp"
SMTP_HOST="smtp.ionos.it"
SMTP_PORT="587"
SMTP_USE_TLS="true"
SMTP_USERNAME="support@orbusonline.net"
SMTP_PASSWORD="<from IONOS mailbox>"
EMAIL_FROM="Orbus Online <support@orbusonline.net>"
EMAIL_REPLY_TO="support@orbusonline.net"
SEND_WELCOME_EMAIL="true"

MONGO_URL="<production cluster, untouched>"
DB_NAME="<production DB, untouched>"
JWT_SECRET="<production secret, untouched>"
CORS_ORIGINS="<production origins, untouched>"
```

### Verify before deploy
```bash
# From the prod pod console — values must be non-empty
echo $APP_ENV $APP_BASE_URL $EMAIL_PROVIDER $SMTP_USERNAME
```

If any of these is empty → STOP, fix env first.

---

## 4. Deploy procedure (Emergent dashboard)

The agent cannot deploy. You (user) must:

1. **Backup recommended**: trigger a MongoDB snapshot from the Emergent
   dashboard or note the current cluster generation, in case of rollback.
2. Open **Emergent Dashboard → Project Orbus → Deploy → `orbusonline.net`**.
3. Confirm the env vars listed in §3 are all set (no changes needed
   if SMTP rollout already happened).
4. Click **Redeploy** (or "Deploy latest commit") so the prod pod picks up
   the ROUND 1 + ROUND 1.5 code.
5. Wait for the deploy to finish ("healthy").
6. Tell the agent: "**deploy fatto**" and the agent will run §5 smoke.

### Rollback path
If §5 fails: redeploy the previous commit from the Emergent dashboard
(no DB schema changes were introduced, so a code-only rollback is safe).

---

## 5. Post-deploy smoke (executed by agent against prod, read-only)

```bash
# 5.1 health
curl -s https://orbusonline.net/api/health
# expected: {"status":"ok","env":"production"}

# 5.2 OpenAPI path count
curl -s https://orbusonline.net/api/openapi.json | jq '.paths | length'
# expected: 43

# 5.3 leaderboard (no auth, public). Test users must NOT appear.
curl -s https://orbusonline.net/api/leaderboard/guilds?limit=5

# 5.4 landing page sanity
curl -s https://orbusonline.net/ | grep -i "<title>"
# expected: <title>Orbus Online: Guild Master</title>

# 5.5 favicon
curl -s -o /dev/null -w "%{http_code}\n" https://orbusonline.net/favicon.svg
# expected: 200
```

What the agent **cannot** test from curl:
- Frontend UI (password toggle, adventurer modal, inventory equip clarity)
  → requires browser. To be playtested by the user.
- Real SMTP send → user must trigger a password-reset on their own mailbox
  and confirm the email arrives.
- Cross-adventurer equip race → covered by pytest in preview, identical
  code shipped to prod.

---

## 6. Production DB audit (optional, recommended)

ROUND 1 changed how traits are stored. If prod has been running before the
trait migration, you should run the read-only audit described in
`PROD_AUDIT_INSTRUCTIONS.md` (updated for ROUND 1.5) to confirm:

- `traits_canonical_it_present == 10` (all Italian seeds applied),
- `traits_flagged_is_test` and `adventurers_with_test_pattern_trait` show
  the residual surface, if any.

If those numbers look fine (no residual leak), nothing else needs to be
done. If residual test-pattern traits are surfacing on prod, we can mirror
`/app/scripts/db_cleanup_phase14_3.py` in a separate run (NOT bundled with
this deploy).

---

## 7. Sign-off

| Owner | Action | Time |
| --- | --- | --- |
| User | Backup / snapshot prod | __:__ |
| User | Redeploy via Emergent dashboard | __:__ |
| User | Ping agent "deploy fatto" | __:__ |
| Agent | Run §5 smoke checks | __:__ |
| User | Browser playtest (password toggle, modal, equip) | __:__ |
| User | Password-reset email smoke (real inbox) | __:__ |
| User | Run §6 audit (optional) | __:__ |

---

*Document generated 2026-06-25. Replaces the previous SMTP-only checklist
for the scope of this redeploy.*
