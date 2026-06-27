# Orbus Online — Refactor Log (ROUND 6B Stabilization)

> Phase-specific quality/security refactor recap. Lives separately from
> `BUILD_RULES.md` to keep the policy ledger free of episode-specific notes.
> Each section is a self-contained record of a phase: scope, files touched,
> verification commands, status.

---

## ROUND 6B — Stabilization (Feb 2026, pre-deploy)

Goal: close all P0/P1 quality + security findings flagged by the user's
external Code Quality Analysis Report before the next production redeploy.
Three phases (A → B → C), gated by user approval between phases.

---

### ✅ FASE A — Backend Security P0 (DONE)

**Scope**: zero-MD5, zero-circular-import, zero-hardcoded-secret in backend.

#### A1 — Circular Import resolved
- `backend/app/adventurers/common.py` *(new)* — pure primitives (`_rng`,
  `_weighted_choice`, `_generate_name`, `_roll_stat`, `_pick_random_traits`,
  `_apply_trait_effects`, `_generate_candidate` with `forced_rarity` kwarg).
- `backend/app/recruitment/services.py` — re-exports primitives from
  `common.py` (legacy `__all__` preserved).
- `backend/app/adventurers/generator.py` — drops the
  `_rec.RARITY_WEIGHTS` monkey-patch trick in favour of the new
  `forced_rarity` kwarg.

Verification:
```bash
python -c "import app.recruitment.services; import app.adventurers.generator"
# Forward + reverse import order both OK; common._generate_candidate IS services._generate_candidate
```

#### A2 — Hardcoded test secrets externalized
- `backend/tests/.env.test` *(new, gitignored)*
- `backend/tests/.env.test.example` *(new, committable template with
  obvious placeholders + header comment).*
- `.gitignore` — allowlist exception for `.env.test.example`.
- `backend/tests/conftest.py` — also loads `.env.test` (override=True).
- `backend/tests/backend_test.py`,
  `backend/tests/backend_phase5_test.py`,
  `backend/tests/backend_phase93_smtp_test.py`,
  `backend/tests/backend_phase14_3_traits_preview_test.py` — all read
  credentials via `os.environ[...]`. No literal fallback (fail-fast).

Tester seed credentials (`tester@orbus.test` / `password123`) intentionally
NOT changed in the DB seed — only how tests read them.

Verification:
```bash
grep -rE "(password|secret|api_key|token).*=.*['\"][a-zA-Z0-9]{8,}" \
  backend/tests/backend_test.py \
  backend/tests/backend_phase5_test.py \
  backend/tests/backend_phase93_smtp_test.py
# → 0 matches
```

#### A3 — Ruff cleanup
20 errors → 0. Files touched: `chronicle/services.py` (dead-code `gold`
variable removed — verified not a behavior change), `core/email_templates.py`
(unused `safe_username_html`), `raids/__init__.py` (E701 one-liners),
`scripts/seed_tester_adventurers.py` (F541 f-string), `seeds/seed_round5.py`
(F841 `res6`), plus 8 unused-import fixes across `admin/`, `consortiums/`,
`expeditions/loot_tables.py`, `shop/routes.py`, `territory/*`,
`shared/constants.py` (E402).

Verification:
```bash
python -m ruff check backend/app/   # → All checks passed!
```

#### Tests after FASE A
6 critical files × 88 tests passed (backend_test, backend_phase5,
backend_phase93_smtp, backend_round6a_generator, backend_round6b1_territory,
backend_round6b2a_guards). Pre-existing `backend_phase14_3_traits_preview_test.py`
errors (7) confirmed unchanged on `main` — not regressions.

---

### ✅ FASE B — Frontend Security P0 (DONE)

**Scope**: XSS audit + React Hook dependency cleanup + R8 gate repair.

#### B1 — XSS audit
`grep -rn "dangerouslySetInnerHTML" frontend/src/` → 1 match, in a docstring
comment at `Chat.jsx:12` ("Hard rule: NEVER render via …"). **Zero actual
usages.** Chat renders messages as React text (`{msg.message_text}`) and
the backend HTML-escapes inbound payloads. Double escape — DOMPurify not
needed. Smoke-tested with browser dialog listener: 3 payloads
(`<img src=x onerror=alert(1)>`, `<script>…</script>`, `<svg/onload=…>`)
posted, **0 dialogs fired**.

#### B2 — React Hook deps
**Critical discovery**: `yarn lint:strict` was silently a no-op. The script
used `eslint src --ext .js,.jsx` which ESLint v9 ignores (the `--ext` flag
is deprecated and matched 0 `.jsx` files). The R8 deploy gate was
effectively disabled.

Fix (in `frontend/package.json`):
```diff
- "lint":        "eslint src --ext .js,.jsx",
- "lint:strict": "eslint src --ext .js,.jsx --max-warnings 0",
- "lint:fix":    "eslint src --ext .js,.jsx --fix"
+ "lint":        "eslint \"src/**/*.{js,jsx}\"",
+ "lint:strict": "eslint \"src/**/*.{js,jsx}\" --max-warnings 0 --report-unused-disable-directives",
+ "lint:fix":    "eslint \"src/**/*.{js,jsx}\" --fix"
```

After the fix, real warnings surfaced. Remediations:
- `frontend/src/pages/Inventory.jsx` — `useCallback`-wrapped `refresh`,
  fixing a latent bug (stale recipe localizations after `lang` change).
- `frontend/src/pages/Crafting.jsx` — same useCallback pattern.
- `frontend/src/pages/RaidBuilder.jsx` — `load` wrapped in useCallback;
  auto-load effect gained a rationale comment for the surviving
  `eslint-disable-next-line` (autoLoadedRef one-shot pattern).
- `frontend/src/pages/RaidReport.jsx` — `load` useCallback.
- `frontend/src/pages/ExpeditionNew.jsx` — rationale comment on the
  auto-load disable directive.

Final state: `yarn lint:strict` exits 0/0 across 105 files. Webpack dev
server: "Compiled successfully".

#### B3 — Smoke check
5 critical pages (`/territory`, `/squads`, `/squad-builder`,
`/recruitment`, `/raids`) plus the new `/raids/builder/<slug>` route
tested with `pageerror` + `console.error` listeners.
**0 JS errors captured.**

---

### ✅ FASE C — Hardening P1 (C1 + C3 DONE, C2 DEFERRED)

#### C1 — MD5 → SHA-256
- `backend/app/expeditions/report_builder.py:488` — single occurrence,
  value was already assigned to `_` (discarded). Swap is a no-op for
  behavior but removes MD5 from the dependency graph.

Verification:
```bash
grep -rnE "hashlib\.md5|\bmd5\(" backend/app/   # → 0 matches
```

#### C3 — Complexity refactor (Radon CC before → after)

| Function | Before | After | Δ | Helpers added |
|---|---|---|---|---|
| `flag_test_users_aggressive` | E (39) | B (9) | −30 | 4 |
| `generate_candidate` | D (21) | B (7) | −14 | 2 |
| `_format_event` | C (19) | B (7) | −12 | 1 (+ dispatch table) |
| `retire_adventurer` | C (16) | A (3) | −13 | 6 |

All public APIs **unchanged** (same signatures, return shapes, status
codes). All 13 new helpers are `_private` (underscore prefix).

Files: `backend/app/admin/services.py`, `backend/app/adventurers/generator.py`,
`backend/app/adventurers/retire.py`, `backend/app/chronicle/services.py`.

#### C2 — DEFERRED to Round 11.1 (post-deploy)

**Decision**: do NOT migrate `localStorage` → `httpOnly` cookies in this
round.

**Rationale (recorded, binding for future agents)**:
1. **httpOnly without CSRF is not a net win.** It trades XSS-token-exfil
   risk for CSRF risk on state-changing endpoints. SameSite=Lax mitigates
   the worst CSRF patterns but does not eliminate them; full CSRF token
   plumbing (~100-200 LOC, double-submit pattern) is a prerequisite.
2. **XSS surface already mitigated in FASE B** (zero
   `dangerouslySetInnerHTML`, double escape server + React, R8 lint gate
   repaired). Marginal gain from httpOnly is currently low.
3. **Cutover risk on preview URL** (cookie domain/path) and mobile client
   compatibility (`/app/mobile`) are not quantifiable under deploy pressure.
4. **Bearer fallback testing surface** (curl, playwright, CI) would have
   to be migrated in lockstep.

**Roadmap for Round 11.1 (post-deploy)**:
1. CSRF token implementation (double-submit cookie + `X-CSRF-Token` header
   + backend middleware). Dedicated round.
2. httpOnly cookies on register/login/refresh/logout responses,
   `get_current_user` extended with cookie fallback. Bearer header kept
   for 1 week grace period.
3. Bearer fallback removal (cleanup round).

`localStorage` audit captured: 11 occurrences — **9 auth** (legitimate
migration target), **2 UI state** (i18n lang preference, stays in
localStorage; not a security risk).

---

## Verification commands (re-runnable)

```bash
# Backend lint
cd /app/backend && python -m ruff check app/

# Backend tests (88 critical-path tests)
cd /app/backend && python -m pytest \
  tests/backend_test.py \
  tests/backend_phase5_test.py \
  tests/backend_phase93_smtp_test.py \
  tests/backend_round6a_generator_test.py \
  tests/backend_round6b1_territory_test.py \
  tests/backend_round6b2a_guards_test.py \
  -n 0 --tb=line -q

# Backend complexity (Radon)
cd /app/backend && radon cc -s app/admin/services.py app/adventurers/generator.py \
  app/adventurers/retire.py app/chronicle/services.py | grep -E "(generate_candidate|retire_adventurer|_format_event|flag_test_users_aggressive)"

# Frontend lint (R8 gate — now functional)
cd /app/frontend && yarn lint:strict

# Live preview smoke
curl -s https://guild-master-5.preview.emergentagent.com/api/health
curl -s -X POST https://guild-master-5.preview.emergentagent.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"tester@orbus.test","password":"password123"}'
```

## Status at end of ROUND 6B Stabilization

| Layer | Gate | Status |
|---|---|---|
| Backend | `ruff check app/` | ✅ 0 issues |
| Backend | pytest critical-path (88) | ✅ all green |
| Backend | Radon CC of refactored fns | ✅ ≤ B (was E/D/C) |
| Backend | MD5 references | ✅ 0 |
| Backend | Circular imports in adventurers/* | ✅ resolved |
| Backend | Test files with hardcoded secrets | ✅ 0 (env-sourced) |
| Frontend | `yarn lint:strict` (R8 gate) | ✅ 0/0 across 105 files |
| Frontend | `dangerouslySetInnerHTML` usage | ✅ 0 |
| Frontend | XSS payload smoke test | ✅ 0 dialogs fired |
| Frontend | Critical pages JS errors | ✅ 0 |
| Frontend | localStorage→httpOnly cookies | 🟡 DEFERRED to Round 11.1 |

**Ready for e1_tester end-to-end validation.**
