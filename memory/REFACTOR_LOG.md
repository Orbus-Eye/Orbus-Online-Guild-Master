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


---

## ROUND 6B.3 — Wave 1 Hotfix (Feb 2026)

**Scope**: Fix P0 economy exploit "Territory free purchase" (cost.gold never
debited, materials never debited) + roll back 93 abuser structures.

### Backend changes
- `backend/app/territory/services.py` — atomic `$inc` debit for gold and
  materials, with compensating refund on partial failure (`_atomic_purchase_or_upgrade`).
  Audit log now reflects real delta.
- `backend/app/seeds/seed_territory_materials.py` *(new)* — idempotent seed
  for `lesser_arcane_dust`, `greater_arcane_dust` reagents.
- `backend/app/scripts/rollback_territory_free_purchases.py` *(new)* —
  one-shot CLI rollback. Hard safety: `SAFE_ACQUIRED_VIA = {default, purchase, None}`
  assert, `EXCLUDED_ACQUIRED_VIA = {migration, migration_legacy}` pre-filter,
  `skipped_other_acquired_via` counter for non-safe non-excluded slugs.

### Frontend changes
- `frontend/src/pages/Territory.jsx` — disable/busy state hardening (already
  in earlier 6B.3 wave).

### Tests
- `backend/tests/backend_round6b3_territory_atomicity_test.py` *(new, 12 tests)* —
  validates atomic debit, compensating refund, CAS race, audit accuracy.
- `backend/tests/backend_round6b1_territory_test.py` — 2 pre-existing tests
  updated to seed `iron_shard` (were written against the buggy backend; now
  the atomic debit requires the material to exist).

### Rollback execution (apply)
- 97 actions applied (93 real abusers + 4 r6b3 test artifacts).
- 2861 migration structures skipped (untouched).
- 81 affected guilds.
- 0 hard deletes (all entity counts invariant pre→post).
- 97 audit rows written with `event_type=guild_structure_rollback_free_purchase`.
- 97 structures now marked `acquired_via=rolled_back`.
- Idempotency confirmed: second `--apply` run = 0 actions.
- Backup file: `/app/memory/territory_free_purchase_rollback_backup_20260627T225420Z.json`

### Verification
| Layer | Check | Status |
|-------|-------|--------|
| Backend | Atomicity test suite (12/12) | ✅ |
| Backend | Round 6B.1 territory suite (12/12) | ✅ |
| Backend | Critical suite (90/90) | ✅ |
| DB | Entity counts pre==post | ✅ (zero hard delete) |
| DB | Migration structures (2861) untouched | ✅ |
| DB | `rolled_back` marker count = 97 | ✅ |
| Tester | Tester guild structures NOT rollbacked | ✅ |
| Smoke | Compensating refund on partial fail | ✅ (gold delta = 0) |
| Idempotency | Re-run = 0 actions | ✅ |

**Wave 1 status: DONE. Ready for Wave 1.5 (over-cap roster enforcement).**

---

## ROUND 6B.3 — Wave 1.5 (Feb 2026) — Over-cap roster enforcement

### Scope
Block destructive write flows when active roster exceeds the
`dormitories` cap, instead of silently producing inconsistent state.

### Backend
- New: `app/territory/cap_guard.py` — `assert_not_over_cap` (423
  `roster_over_capacity`), `assert_adventurers_not_retired` (423
  `adventurers.retired_in_set`), `over_cap_dep()` FastAPI dependency.
- Recruit/Expedition/Replay-last/Raid/Squad/Equip now gated.
- `Adventurer.retired_by` field added (enum string, set to "user" on
  POST /retire). Legacy retires default to None (back-compat).
- Audit event `roster_over_capacity_blocked` added to allowlist.

### Frontend
- New: `components/OverCapBanner.jsx` (reusable, used on 5 pages).
- New: `pages/RosterManage.jsx` at route `/roster/manage` with sticky
  cap state, filters (search/role/rarity), 4-criteria sort, multi-select
  bulk retire and explicit confirm modal.
- Axios interceptor `lib/api.js` extended to handle 423 codes
  `roster_over_capacity`, `adventurers.retired_in_set` and
  `equip.target_retired` with toast + CTA.
- i18n IT+EN keys for `overcap.*` and `rosterManage.*`.

### Tests
- New: `tests/backend_round6b3_overcap_enforcement_test.py` (14 passed,
  1 skipped — equip skip on fresh guild without inventory).
- Updated: `backend_round6b2a_guards_test.py` — `recruitment.cap_reached`
  expectation 422 → 423 `roster_over_capacity`.
- Updated: `backend_round6b1_territory_test.py` — 2 tests reseeded with
  `iron_shard` (regression from Wave 1 atomicity fix).

### Verification
| Check | Result |
|-------|--------|
| Pytest (61 over-cap + atomicity + territory + guards) | 60 passed, 1 skipped |
| Pytest full critical suite | 104 passed, 1 skipped |
| Ruff app/ | All checks passed |
| Yarn lint:strict | 0 warnings, 0 errors |
| Smoke: RosterManage live | All 10 data-testid present, mobile responsive, 4/5 over-cap banner verified |
| Smoke: Bulk retire flow | filter→select→confirm→success toast→state refresh OK |

**Wave 1.5 status: DONE. Ready for Wave 2.**
