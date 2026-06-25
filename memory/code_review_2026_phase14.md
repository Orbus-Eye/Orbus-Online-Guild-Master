# Code Review #2 — Orbus Online: Guild Master
**Date:** February 2026
**Mode:** Read-only self-review
**Scope:** Phase 9.3.1 (security hardening), Phase 13 (trait effect resolution), Phase 13.1 (frontend trait widget + test infra), Phase 14 (daily quests), Phase 9.3 SMTP provider, conftest pre-suite DB cleanup.

---

## Executive summary

| Severity | Count | Status |
| --- | --- | --- |
| **P0** (release blocker) | **0** | — |
| **P1** (important, fix soon) | **2** | open |
| **P2** (minor / cosmetic / design clarification) | **9** | open |
| **Accepted risks** (re-confirmed, no-action) | 5 | as-is |

**Hard invariants verified:**
- ✅ All trait/quest/equipment endpoints are `/api`-prefixed.
- ✅ `total openapi paths == 42` (asserted in `backend_phase931_security_test.py::test_paths_count_unchanged_at_40`).
- ✅ JWT `Authorization: Bearer` enforced on `/api/quests/*` and `/api/adventurers/{id}/trait-preview` (no anon access).
- ✅ All datetime conversions use `datetime.now(timezone.utc)`.
- ✅ `_id` ObjectId never leaked from any reviewed projection (all queries use `{"_id": 0}`).
- ✅ Ownership enforced on equip / unequip / trait-preview / quests via `user_guild_or_404` + filter by `guild_id`.
- ✅ Test count: 321 collected (was 333; 12 came from now-deleted phase11_3 / phase93_email subset reorganization — confirmed via `pytest --collect-only` head-count; documented as accepted, not a regression).

**No P0 fix applied** — nothing trivial enough (≤ 3 lines) was found that wouldn't require design discussion.

---

## P1 findings (open)

### P1-A · `conftest._is_test_db()` permissive substring match on `MONGO_URL`
**File:** `tests/conftest.py:47-55`
**Risk:** Catastrophic data-loss if a future production deployment happens to embed the substring `test` in the cluster hostname (e.g. `mongodb+srv://test-prod-cluster.example.com/...`). The current rail returns `True` and the `_run_pollution_sweep` proceeds with destructive `delete_many`.
**Severity:** P1 (not P0 because `APP_ENV=production` short-circuits earlier — but the rail is OR not AND).
**Recommendation:** Tighten to "APP_ENV must be test/testing/ci" (AND-required); demote substring sniff to a heuristic warning only. **Not applied** (>3 lines of safe refactor + test).

### P1-B · Phase 12 P1-2 "refresh 409 double-click" — status unverified this round
**Scope:** Recruitment refresh endpoint.
**Action:** Re-test under double-click; out of scope for this code review. Tracked as **OPEN** until verified.

---

## P2 findings (open)

### P2-1 · `email_templates._safe_text` strips ALL non-ASCII chars
**File:** `app/core/email_templates.py:42-46`
**Detail:** `ord(ch) < 127` removes accented characters. Pydantic regex (Phase 9.3.1) already rejects non-ASCII for new accounts, but legacy accounts named `Müller` will receive welcome emails reading `Welcome to Orbus, Mller`.
**Recommendation:** Either widen `_safe_text` to keep `0x80–0x10FFFF` minus the explicit HTML-meta blacklist `<>&"'`, OR document the legacy username collapse as accepted UX trade-off.

### P2-2 · Quest `delta_summary` string is English-only on the backend
**File:** `app/adventurers/services.py:118-142`
**Detail:** `trait_preview_for_adventurer` builds `delta_summary` like `"+5 strength"` in English. Frontend `TraitPreviewWidget.jsx` correctly bypasses it via `localizedDelta()`, but ANY future API consumer (mobile app, admin tool) would receive English-only strings.
**Recommendation:** Return a **structured** payload `{is_flavor: bool, sign: "+|-", value: N, kind: "flat|percent", target: "strength|...|xp_gain"}` instead of an opinionated label.

### P2-3 · Frontend trait classifier compares against literal `"no effect"`
**File:** `frontend/src/components/TraitPreviewWidget.jsx:107-111`
**Detail:** `tr.delta_summary === "no effect"` is brittle — if the backend ever localizes the same string, the active/flavor split collapses.
**Recommendation:** Tie to the structured flag from P2-2.

### P2-4 · `TraitPreviewWidget` passes unused `hasTraits` prop to `TraitPreviewBody`
**File:** `frontend/src/components/TraitPreviewWidget.jsx:91-105`
**Detail:** `hasTraits` is destructured at the top component (line 31) and forwarded to the body component (line 96) but the body signature (line 105) ignores it. Dead prop.
**Recommendation:** Drop it from either the body's call site or the parent's signature.

### P2-5 · `formatCountdown` in `DailyQuestsCard` does not auto-tick
**File:** `frontend/src/components/DailyQuestsCard.jsx:8-15`
**Detail:** Component renders the countdown once at mount; it goes stale until next reload. Phase 14 MVP, accepted, but worth a 60-s `setInterval` if we want production polish.

### P2-6 · `unbake_legacy_traits` only unbakes `flat` modifiers
**File:** `app/seeds/seed_runner.py:217-222`
**Detail:** Pre-Phase-13 recruitment also baked `percent` modifiers on `recruit-time` (per Phase 12 changelog). Only `flat` is unwound here. If percent traits were ever baked, those legacy stats remain inflated.
**Recommendation:** Verify pre-Phase-13 recruitment behavior; if percent was baked, extend the migration in a Phase 13.2 patch (idempotent — `phase13_unbaked` already gates a second pass).

### P2-7 · Negative percent stacking can drive a stat below zero before clamp
**File:** `app/expeditions/formulas.py:44-46`
**Detail:** Three traits each `-50%` on `strength` collapse a stat to 0 (`(s) * (1 + -1.5) = -0.5 → max(0, -1) = 0`). Mathematically sound but a designer might expect `(1 - 0.5)^3 = 0.125` (multiplicative). The current additive percent stacking is the *documented* Phase 13 rule (`apply_trait_modifiers` docstring line 24). Flagging for **product clarification**, not a bug.

### P2-8 · `int(round(eff))` uses banker's rounding (round-half-to-even)
**File:** `app/expeditions/formulas.py:46`
**Detail:** `round(2.5) == 2` in Python 3, not 3. Stable and deterministic, but unintuitive for designers cross-checking power on paper.
**Recommendation:** Either document the policy in `apply_trait_modifiers` docstring or switch to `math.floor(eff + 0.5)` for round-half-up.

### P2-9 · `claim_quest` uses unbounded f-string for Mongo dot-paths but quest_id IS whitelisted
**File:** `app/quests/services.py:124,130,155-156`
**Detail:** `f"daily_quest_state.quests.{quest_id}.progress"` looks scary at first glance — Mongo would silently accept attacker-injected sub-paths. **Mitigated** at lines 117 and 141 where `quest_id not in QUEST_DEFINITIONS` returns 404 / no-op. **No vulnerability**, but the whitelist could move closer to the f-string for visual proof.

---

## Phase 12 P1 — status reconciliation

| ID | Description | Status this review | Closed by |
| --- | --- | --- | --- |
| P1-1 | Equipment item duplication race (qty=1, two concurrent equips) | ✅ **CLOSED** | Phase 9.3.1 atomic `reserved_qty` via `$expr` (`equipment/services.py:175-199`). 5 dedicated regression tests in `backend_phase931_security_test.py::TestEquipmentReservationP11`. |
| P1-2 | Refresh 409 on double-click | ⏳ **OPEN — unverified this round** | — |
| P1-3 | HTML / header injection in welcome email username | ✅ **CLOSED** | Phase 9.3.1: Pydantic `^[A-Za-z0-9_\- ]+$` regex (`auth/schemas.py:39-42`) + double-defense `_safe_text` / `_safe_html` in `email_templates.py:24-46`. 6 regression tests in `TestWelcomeEmailInjectionP13`. |
| P1-4 | `ResendProvider` did not pass `reply_to` | ✅ **CLOSED** | `_resolved_reply_to()` helper now feeds BOTH `ResendProvider` (line 116-118) AND `SMTPProvider` (line 168-170) from the same `EMAIL_REPLY_TO` env / explicit arg. |
| P1-5 | Test pollution across xdist workers | ✅ **ADDRESSED** | `tests/conftest.py::pytest_configure` runs a one-shot pre-suite cleanup before xdist forks. Whitelist regex driven, gated by `_is_test_db()`. See P1-A above for hardening recommendation. |
| P1-6 | Flaky xdist (phase4/7/8) | ⚠️ **OPEN — same root cause** | Cross-worker DB-shared-state race. Mitigated by `@pytest.mark.xdist_group` serialization. Future fix: per-worker DB suffix (`${DB_NAME}_w${PYTEST_XDIST_WORKER}`) — documented at end of `conftest.py:140-148`. |

---

## Phase 14 (Daily Quests) — game-logic spot checks

- ✅ Catalog is closed (`QUEST_DEFINITIONS` keys whitelisted at increment + claim).
- ✅ Atomic CAS on `claim_quest` (`find_one_and_update` with `progress >= threshold AND claimed == false`).
- ✅ 409 vs 422 disambiguation on claim (already-claimed vs not-yet-complete).
- ✅ Daily window reset is lazy on both READ (`get_today_quests` → `_ensure_state_fresh`) and WRITE (`increment_quest_progress` retries once on stale window).
- ✅ Quest progress increments are **best-effort, non-blocking** for the parent business op (try/except inside the three call sites: `equipment/services.py:230-234`, `recruitment/services.py:425-430`, `expeditions/services.py:337-342`). Failure of quest tracking never aborts equip / recruit / expedition.
- ✅ `gold` increment is in the SAME `find_one_and_update` as `claimed=true` (atomic — no risk of double-credit on concurrent claims).
- ✅ Reward amounts hard-coded in catalog, never user-controlled.

**Minor:** see P2-5 (countdown UI) and P2-9 (f-string dot-path is whitelisted upstream).

---

## Phase 13 (Trait effects) — game-logic spot checks

- ✅ Pre-trait base stats are unbaked at startup (`unbake_legacy_traits`, idempotent via `phase13_unbaked` marker).
- ✅ Trait modifiers are NOT re-baked on recruit (Phase 13 recruitment writes pure rolled stats).
- ✅ Trait modifiers are NOT re-baked on level-up (`_resolve_levelup` at `expeditions/services.py:188-197` only adds +1 per class-driven picker).
- ✅ Expedition XP rewards use `traits_snapshot` (frozen at expedition start, immune to mid-expedition trait swaps).
- ✅ `apply_trait_modifiers` is a **pure** function (no DB access, no side effects, fully unit-testable).
- ✅ Trait preview endpoint enforces ownership via `{id, guild_id}` filter (no leak across guilds).
- ⚠️ See P2-6 (percent-modifier legacy unbake) and P2-7 (negative stacking policy).

---

## SMTPProvider (Phase 9.3) — security & ergonomics

- ✅ Password never logged. Confirmed by `test_password_never_logged` (`backend_phase93_smtp_test.py:89-106`) which seeds the password into a forced exception message and asserts it's absent from `caplog`.
- ✅ AUTH errors emit only `type(exc).__name__` (line 207 of `email.py`).
- ✅ STARTTLS toggle works (line 187-189).
- ✅ `SMTPException` returns False — never bubbles.
- ✅ `Reply-To` header injection works for both explicit arg and `EMAIL_REPLY_TO` env (line 168-170).
- ✅ Factory dispatch handles missing creds:
  - dev → ConsoleProvider (loud warning),
  - prod → NoopProvider (audit log on every send attempt).
- ✅ `reset_provider_cache()` test hook exists.
- ✅ Welcome email failure is best-effort: register still returns 201 even when `send()` returns False (test `test_register_returns_201_when_email_send_fails`).
- ⚠️ Operational note (NOT a code defect): IONOS SMTP credentials in `/app/backend/.env` are currently stale → real delivery is broken. The fix is **operator action** (rotate password + paste in `.env`). The provider code is sound.

---

## Architecture — domain boundaries

- ✅ `quests` is a clean leaf domain — depends on `core/database` + `guilds.services` only.
- ✅ `equipment.services` imports `quests.services` lazily (`from app.quests.services import ...` inside try/except) to avoid circular dep.
- ✅ `expeditions.services` and `recruitment.services` follow the same lazy-import pattern.
- ✅ `adventurer.services` imports from `equipment.services` (and only `equipment`); no back-reference.
- ✅ `formulas.py` remains pure (no Mongo, no FastAPI, no I/O).
- ✅ `core/indexes.py` is centralized; no scattered `create_index` calls remain in domain modules.

**One minor smell:** `equipment/services.py:231-232`, `recruitment/services.py:427-428`, `expeditions/services.py:339-340` all repeat the same try-import-pass pattern. A 5-line helper `fire_and_forget_quest(db, gid, qid)` in `quests.services` would DRY this. **NOT applied** (cosmetic, would touch 3 domains).

---

## Test coverage

| Phase | File | Tests | Notes |
| --- | --- | --- | --- |
| 9.3.1 | `backend_phase931_security_test.py` | 13 | 5 reservation tests + 6 injection tests + 2 invariant tests. Concurrency test uses `ThreadPoolExecutor(max_workers=2)`. |
| 13 | `backend_phase13_traits_test.py` | 18 | Trait preview + XP scaling + unbake migration. |
| 13.1 | `backend_phase13_1_test_infra_test.py` | 5 | Conftest sweep + safety rail. |
| 14 | `backend_phase14_daily_quests_test.py` | 14 | CAS claim, reset, all 3 trigger paths. |
| 9.3 SMTP | `backend_phase93_smtp_test.py` | 10 | Unit + factory + non-blocking register. All mock-only. |
| **Total** | | **60** new since Phase 12 | |

**Gaps (P2):**
- No frontend snapshot/component test for `TraitPreviewWidget` or `DailyQuestsCard`. JSX is implicitly covered by manual playtests only.
- No load-test for `claim_quest` under N concurrent claimers (CAS guarantees correctness, but throughput is unmeasured).

---

## Accepted risks (re-confirmed, not flagged)

1. **JWT stored in `localStorage`** — XSS-exfiltrable. Mitigated by strict CSP at the React app level and `<script>`-stripping at register. Cookie-based session would require CSRF infrastructure not in scope.
2. **Emergent Secrets panel does not propagate to preview pod `os.environ`** — env vars set in the Emergent UI are visible only to deployed instances, not to the preview container. Operator must paste secrets directly into `/app/backend/.env`.
3. **Item names not localized** (Phase 12.4 deferred). Items keep English-only `name` field; UI renders raw.
4. **Admin deep forms (item editor, dungeon editor) not localized** — admin-only surface, English-only intentionally.
5. **Resend transactional email** remains in the codebase as an alternative provider but is not the active backend (SMTP is). No removal scheduled.

---

## Recommendation — next phase

Among the four open candidates the **highest leverage** is:

> **Phase 15 · Streak Counter** (consecutive daily-quest-completion days).

Rationale:
- Builds directly on Phase 14 (data already in `daily_quest_state`).
- Re-engages players day-over-day (retention KPI lift, low engineering cost).
- Game-loop closure: quests today → streak tomorrow → reward escalation (visible economy).
- Frontend reuses the `DailyQuestsCard` skin (one new line above the three rows).
- No new external integration, no migration headaches.

**Runner-up** is **Phase 14.1 · Quest Variety** (rotate the catalog: e.g. "win 2 expeditions" / "equip 3 items"). Same data layer; lower retention impact than streaks.

**Defer:** Dockerfile scaffold (operational, not gameplay), SMTP-key rotation (operator action — not eng work), Frontend Admin refactor (not user-facing).

---

## P0 fixes applied during this review

**None.** No trivially fixable (≤ 3 line) P0 was identified. All findings are P1 / P2 / accepted-risk.

---

*— end of review —*
