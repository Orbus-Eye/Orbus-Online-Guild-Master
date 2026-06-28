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

---

## ROUND 6B.3 — Wave 2 (Feb 2026) — UX hotfix: Consorzi + Asta/Mercato

### TASK 2 — Consortium description readability
- `pages/Consortiums.jsx`: replaced 80-char slice with 2-line CSS clamp,
  added "Leggi tutto"/"Read more" button when description > 100 chars,
  full-screen modal with name/tag/members/description/Join/Close.
- React auto-escape → confirmed XSS safety (5/5 checks passed).

### TASK 3 — Auction/Mercato text cleanup
- `pages/Auction.jsx`: switched from `market.*` to `auction.*` i18n keys.
  Page header "Mercato" → "Asta", tab labels updated.
- `Market.jsx` (NPC shop) intentionally untouched.
- New i18n keys IT+EN under `auction.*` (15 keys per locale).

### TASK 4 — Auction buy button hardening
- BuyTab now passes `myGuildId` + `myGuildGold` props.
- Buy button disabled with structured tooltip when:
    - listing belongs to own guild
    - status != "active"
    - price > guild gold
- Quantity confirm `[✓ Compra]` also disabled when total > gold.

### Verification
| Check | Result |
|-------|--------|
| Yarn lint:strict | 0 warnings, 0 errors ✅ |
| Pytest (backend_test + round6b3 atomicity + overcap) | 43 passed, 1 skipped |
| XSS smoke (script + img onerror) | 5/5 checks passed — escaped, not executed |
| Asta header smoke | "Auction"/"Asta" header, BUY/SELL/MY LISTINGS tabs |
| Buy button smoke | 50 buttons visible with price label, no disabled-state false-positive on tester |
| Modal smoke | Open/close OK, full description visible, Join button present |
| Mobile (375px) | Renders without layout breakage |

**Wave 2 status: DONE. Ready for Wave 3.**

---

## ROUND 6B.3 — Wave 3 (Feb 2026) — Guida + regression + chiusura hotfix

### TASK 5 — Guida aggiornata
- `pages/Guide.jsx`: rinumerate 17 sezioni (era 14). Aggiunta sezione "4. Capacità roster"
  (Wave 1.5). Aggiornate sezioni Territorio (costi atomici Wave 1), Mercato vs Asta
  (chiarimento NPC vs P2P), Consorzi (modal "Leggi tutto").
- Italian-first hardcoded style (coerente con file esistente).

### TASK 6 — Regression sweep + cleanup r6b3
- 12 endpoint smoke OK (territory/adventurers/expeditions/raids/squads/auction/consortia/
  chat/quests/leaderboard/inventory/forge — tutti 200).
- Leaderboard PII check: ✅ no email/user_id/password_hash exposed.
- DB sanity post-hotfix:
    - migration structures: 2861 (invariato ✅)
    - rolled_back structures: 97 (invariato ✅)
    - audit rollback events: 97 (invariato ✅)
- r6b3 cleanup: 281 guilds + 147 users + 1780 adventurers flagged
  `is_test_artifact=True`. **0 hard delete.**
- `_fresh_user` helper in atomicity test ora tagga automaticamente i nuovi
  test users come `is_test_artifact=True` per evitare nuovi leftover.

### Verification
| Check | Result |
|-------|--------|
| Pytest critical suite (104 tests) | ✅ 104 passed, 1 skipped |
| Ruff app/ | ✅ All checks passed |
| Yarn lint:strict | ✅ 0 warnings, 0 errors |
| OpenAPI path count | 92 (invariato — no path aggiunti/rimossi) |
| Backend regression (12 endpoints) | ✅ 12/12 200 OK |
| DB invariants | ✅ tutti invariati |
| r6b3 cleanup | ✅ flag-based, 0 hard delete |

**Wave 3 status: DONE. ROUND 6B.3 COMPLETE.**


---

## ROUND 6B.3 Wave 3.1 — Post-deploy hotfix (smoke su https://orbusonline.net)

**Data**: 2026-06-28
**Trigger**: Smoke su prod ha rilevato 1 bug P1 (frontend routing) + 1 finding di sicurezza (UUID leak minor).

### BUG P1 (fixato) — `/chronicle` routing broken
**Sintomo**: navigazione diretta a `https://orbusonline.net/chronicle` rimbalzava in landing (catch-all `*` → `/`). Nessun link al menu/nav per arrivare alla Cronaca, che era visibile solo come card embedded nella Dashboard.

**Root cause**: la pagina `Chronicle.jsx` non esisteva (esisteva solo il component `ChronicleCard.jsx` usato in `Dashboard.jsx`); nessuna `<Route path="/chronicle">` in `App.js`; nessun `<NavLink to="/chronicle">` in `AppHeader.jsx`.

**Fix** (5 file):
- ✨ Nuovo: `frontend/src/pages/Chronicle.jsx` (35 righe — wrapper standalone su `ChronicleCard limit={50}` con header `:: SERVER CHRONICLE` + intro text)
- `frontend/src/App.js`: import + route protetta `requireGuild`
- `frontend/src/components/AppHeader.jsx`: `<NavLink to="/chronicle" data-testid="nav-chronicle">` inserito tra Consorzi e Chat
- `frontend/src/i18n/lang/it.json`: aggiunto `nav.chronicle="CRONACA"` + `chronicle.page_title` + `chronicle.page_intro`
- `frontend/src/i18n/lang/en.json`: speculari `nav.chronicle="CHRONICLE"` + `chronicle.page_title` + `chronicle.page_intro`

**Bug secondario sgamato durante il fix**: il backend `/api/chronicle` ha `limit ≤ 50` (HTTP 422 oltre). Avevo inizialmente messo `limit=100` nella nuova pagina — ridotto a `50` (massimo consentito).

**Smoke locale (preview)**:
- ✅ `GET /chronicle` (diretto) → carica `data-testid="chronicle-page"`
- ✅ `nav-chronicle` link visibile (text="CHRONICLE", href="/chronicle")
- ✅ Click sul link → naviga a `/chronicle` correttamente
- ✅ Empty state mostrato correttamente (tester preview ha 0 eventi recenti — è normale)
- ✅ `yarn lint:strict` 0/0 su tutti i file modificati
- ✅ JSON i18n entrambi validi (IT+EN)

### Finding minor — `seller.user_id` esposto pubblicamente in `/api/auction/listings`
**Contesto**: introdotto in Wave 3 BUG 1 fix per permettere al FE di calcolare `isOwn` e disabilitare il bottone Buy. Il tester di prod l'ha flaggato come "PII leak minor".

**Decisione product**: **Opzione A — lascia così** (UUID interno non è PII reale: niente email, username o data di nascita). Backlog Round 11.1 per hardening.

**Backlog Round 11.1 hardening** (da affiancare al lavoro su `httpOnly` cookies):
- Espone solo `seller.public_id = sha256(user_id)[:16]` invece dell'UUID raw nelle listing pubbliche
- `/api/auth/me` espone `user.public_id` parallelo
- FE `isOwn` confronta `listing.seller.public_id === currentUser.public_id`
- Backwards-compat: lasciare `user_id` per 1 deploy con deprecation note, poi rimuovere

### Falsi positivi (NON fixati, by-design)
**1. Expedition deadlock 9/5**: 9>5 è vero over-cap → 423 corretto come da decisione semantica Wave 3 (codice in `cap_guard.py` riga 40-53). Tester di prod era già in over-cap state per migrazione/rollback storico. **Nessuna azione.**

**2. State mismatch tester prod (gold=0, roster=9/5)**: stato genuinamente diverso da preview (gold=50K, roster nominale). Non è bug.

### Backlog P3 (deferred) — `seed_prod_tester_state.py`
Script idempotente per portare l'account `tester@orbus.test` di prod in stato demo-ready (gold=50000, Dormitori Lv2, soft-retire degli avventurieri eccedenti con `retired_by="auto_over_cap"`, audit `tester_seed_paid_purchase` su ogni structure purchase — **mai free purchase**). Whitelist hardcoded su `tester@orbus.test`, dry-run by default.

**Status**: deferred. Motivazione: lo script andrebbe testato su prod e non è scope del fix routing. Implementarlo solo quando serve per la prossima sessione di smoke prod. Tracking ID: `seed-prod-tester-state` (cartella consigliata: `backend/app/scripts/`).

### File touched in 3.1
```
 frontend/src/App.js                   |  10 +++++++++  (import + route)
 frontend/src/components/AppHeader.jsx |   1 +          (NavLink)
 frontend/src/i18n/lang/en.json        |   4 +++-       (nav.chronicle + page_title/intro)
 frontend/src/i18n/lang/it.json        |   4 +++-       (nav.chronicle + page_title/intro)
 frontend/src/pages/Chronicle.jsx      |  35 ++++++++   (NEW)
 memory/REFACTOR_LOG.md                |  56 ++++++++   (this entry)
 ----------------------------------------
 6 files changed, ~110 insertions, 0 deletions
```

**Wave 3.1 status**: ✅ READY for prod re-deploy + re-validation mirata su `/chronicle`.

## 2026-06-28 — Round 6D / 6C — Naming hygiene (P2, DEFERRED to Round 11.1)

**Cosmetic WARN da e1_tester finale (4/4 PASS + 2 WARN cosmetic)**:
- Auction guard sui bound-items risponde `400 "Item is not tradeable"` (catalog flag `is_tradeable=false`) invece di `auction.bound_to_adventurer_not_listable`.
- Shop NPC sell risponde `409 shop.sell.bound` invece di `market.bound_to_adventurer_not_sellable`.

Security: nessun gap — entrambi i path bloccano correttamente la transazione. Solo naming inconsistency.

**Azione**: allineare gli error codes dei bound guards tra auction/market/equipment/shop in Round 11.1 (hardening sprint) per diagnostic consistency. NON fixare prima del prod deploy.

---

## 2026-06-28 — Round 6E UX backlog note

**UX gap (notato da e1_tester durante validazione 6E)**:
- `GET /api/training/catalog` ritorna SOLO le specs sbloccate dal tier corrente (es: 4 starter a TG Lv1). Il pattern attuale è "mostra solo cosa puoi fare ora".
- **Considerazione futura**: esporre tutta la lista 14 spec con flag `is_unlocked: bool` per ogni spec, così il giocatore vede la roadmap completa e ha incentivo a upgradare il Training Grounds.

**Azione**: lasciato così per ora (decision: progressive disclosure è coerente con UX text-based del gioco). Da rivalutare in **Round 11.1 / UX sprint**.

---

## 2026-06-28 — ROUND 11.1 Slice 1 (B1+B3+B4+B5+B6) — COMPLETE

### B1 — Bound guard naming hygiene
- NEW: `app/core/bound_errors.py` — 5 helpers + 5 code constants + 422 status uniform + legacy aliases map.
- Refactored: `market/services.py` (create_listing × 2), `shop/services.py` (sell), `equipment/services.py` (equip), `adventurers/retire.py` (retire).
- Frontend: `Auction.jsx` + `Market.jsx` + `Adventurers.jsx` updated to handle new + legacy codes during rollout.
- Tests updated: `backend_phase17_round4_test.py`, `backend_phase19_4b_shop_test.py`, `backend_round6c_specialization_test.py`.

### B3 — pytest-xdist worker isolation
- Investigation: existing `conftest.py` already has robust pre-suite cleanup (`pre-suite cleanup removed: {'users.email': N}`). Running `pytest -n 4` on Round 6 bundle = **62/62 PASS** (no flakiness reproduced in this run).
- Decision: do NOT introduce per-worker DB at this time. The integration tests speak to a single live backend server, so true per-worker DB isolation would require spinning up parallel backends (out of scope for Slice 1). Documented Pattern 2 in `conftest.py` "FUTURE" comment remains as design proposal.
- Test artifact `is_test_user/is_test_artifact` flags (B6) now ensure any guilds created by tests are visually isolatable from prod queries — a complementary mitigation.

### B4 — Public ID hash
- NEW: `app/core/identifiers.py::to_public_id(internal_uuid, *, salt) -> str` — sha256, 16-hex truncated, salt from env `PUBLIC_ID_SALT` or stable fallback.
- Auction serializer: `seller.user_id` → `seller.public_id` + new server-side `is_own: bool` flag.
- Consortium serializer: `founder_user_id` → `founder_public_id` (in list + detail + create response). `founder_guild_id` retained (not PII).

### B5 — PII sweep
- Audited 12 endpoint families (auction × 2, consortium, leaderboard × 2, chronicle, contracts × 3, training, roster_health, health). 
- Findings: 2 leaks pre-Slice-1 (`seller.user_id` in auction, `founder_user_id` in consortium) → both fixed via B4 helper.
- Other endpoints clean (no email, no raw UUID for user PII, no Mongo ObjectId, no traceback, no `[object Object]`).

### B6 — `is_test_user` / `is_test_artifact` + leaderboard filter
- User model: new field `is_test_user: bool` — set automatically on registration when email ends in `@orbus.test`.
- Guild model: new field `is_test_artifact: bool` — inherited from owner's `is_test_user` at creation.
- Backfill executed in preview: 1206 users + 2666 guilds flagged. All `tester@orbus.test` data flagged correctly.
- Leaderboard filter: now combines `is_test_artifact != True` AND `owner_user_id NOT IN test_owners` (defense in depth). Independent of `APP_ENV`.
- `/api/health` left untouched (env label flip = deploy step, NOT applied to prod in Slice 1).

### Bearer fallback cleanup (Slice 2 prep)
- Bearer auth still active. Cookie/CSRF migration scoped to **Slice 2 (dedicated session)**. Documented below in this log for context: do not implement Slice 2 alongside non-auth work.


---

## 2026-06-28 — ROUND 11.1 Slice 2 (B2 — Auth Migration) — COMPLETE

### Auth flow (new)
```
┌─────────────────────────────────────────────────────────────┐
│ 1. POST /api/auth/login {email, password}                   │
│    ⤷ Backend: validates → emits JWT → Response.set_cookie:  │
│      • access_token (HttpOnly, Secure*, SameSite=Lax, 7d)   │
│      • csrf_token   (JS-readable, SameSite=Lax,    7d)      │
│    ⤷ Body also returns `access_token` (14gg Bearer fallback)│
│                                                             │
│ 2. GET  /api/auth/csrf  (idempotent, anonymous OK)          │
│    ⤷ Returns {csrf_token: <64-hex>}, rotates cookie         │
│                                                             │
│ 3. Mutating req (POST/PATCH/PUT/DELETE):                    │
│    Browser auto-sends:    access_token cookie               │
│    Frontend JS adds:      X-CSRF-Token: <csrf_token>        │
│    CSRFMiddleware checks: cookie csrf_token == header       │
│                           → 403 auth.csrf.invalid if mismatch│
│                                                             │
│ 4. POST /api/auth/logout                                    │
│    ⤷ Clears both cookies. CSRF-exempt (idempotent).         │
└─────────────────────────────────────────────────────────────┘
* Secure flag is env-gated: True iff APP_ENV=production.
```

### Decisioni & motivazioni
1. **SameSite=Lax** (non Strict): Strict rompe redirect post-OAuth e
   condivisione link autenticato. Lax + CSRF token = same security.
2. **Double-submit cookie pattern** (non Redis session): stateless,
   scala bene, no DB lookup per validation. Threat model: attacker
   cross-origin non legge il csrf_token cookie né può forgiare il header.
3. **GET /api/auth/csrf endpoint**: idempotente, anonymously fetchable
   (boot-time), rotation gratuita per ogni call (entropy = 32 bytes).
4. **Bearer fallback 14 giorni**: get_current_user prova cookie prima,
   poi Bearer. Emette `auth.legacy_bearer_usage` log con `user_id_hash`
   + path + method ad ogni Bearer usage. Zero rotture per test suite
   esistenti (tutti i test usano `Authorization: Bearer`).
5. **Cookie httpOnly + Secure env-gated**: in dev (APP_ENV=development)
   Secure=False per permettere localhost http. In prod Secure=True.

### Piano deploy prod Round 11.1 (Slice 1 + Slice 2 insieme)
1. **Pre-deploy**:
   - Verifica `APP_ENV=production` su pod prod (variabile supervisor).
   - Verifica `CORS_ORIGINS=https://orbusonline.net` su pod prod
     (l'ingress di prod può potenzialmente accettare o no — same-origin
     in prod rende CORS irrilevante per il flusso normale, ma una lista
     esplicita serve per crawlers/Stripe webhooks).
2. **Deploy code** (git push da preview → prod via Emergent panel).
3. **Post-deploy smoke**:
   - `GET https://orbusonline.net/api/health` → `env=production`
   - Login da browser → verifica cookie `access_token` HttpOnly +
     `csrf_token` non-HttpOnly + `Secure=true`
   - localStorage check: `orbus_token` rimosso dopo primo /me success
   - POST mutating senza header CSRF → 403
   - POST mutating con header CSRF → success
   - `/api/auction/listings` → no `seller.user_id`
   - `/api/consortiums` → no `founder_user_id`
4. **Monitoring**:
   - Grep log per `auth.legacy_bearer_usage` event → count nel tempo.
   - Settimanalmente verificare il count → quando vicino a 0 (no client
     Bearer attivo), procedere al cleanup Bearer (step separato).

### Piano cleanup Bearer fallback (a 14gg post-deploy)
**Pre-requisito**: `auth.legacy_bearer_usage` metric → 0 per 7gg
consecutivi. Verifica via log grep / monitoring stack.

**Cosa rimuovere**:
1. `app/core/security.py::get_current_user`: rimuovi il branch
   `elif creds is not None and creds.credentials` + tutto il logging
   `auth.legacy_bearer_usage`. Tieni solo il cookie path.
2. `app/auth/routes.py`: rimuovi `access_token` field da login/register
   response body (rimane solo nel cookie).
3. `frontend/src/lib/api.js`: rimuovi `localStorage.getItem(TOKEN_KEY)`
   + il blocco `if (token) config.headers.Authorization`. Tieni solo
   `withCredentials: true` + CSRF interceptor.
4. `frontend/src/context/AuthContext.jsx`: rimuovi il branch
   "401 → try Bearer fallback" (linee 56-72 circa).
5. Rimuovi `localStorage.removeItem(TOKEN_KEY)` opportunistico
   (non più necessario).
6. **Test suite**: aggiornare tutti i test esistenti (`headers={"Authorization":...}`) per usare `requests.Session()` con login cookie-based, OPPURE rinominare i test in "legacy_bearer_compat" e marcarli skip.

**Verifica post-cleanup**:
- Run full test suite → tutti i test che usavano Bearer falliscono con 401 se non aggiornati → conferma che fallback è veramente off.
- Smoke prod → flow auth ancora funzionante via cookie.

### Blocker scoperti durante Slice 2 (risolti)
- **CORS `Allow-Origin: *` + `Allow-Credentials: true` incompatible**: 
  risolto sostituendo `allow_origins=["*"]` con `allow_origin_regex=".*"` 
  in dev/preview. In prod `CORS_ORIGINS` deve essere lista esplicita.
- **Browser localhost → preview cross-origin**: l'ingress preview ritorna
  ancora `Allow-Origin: *` (config infra Emergent). **In preview** il
  tester accede via `https://guild-master-5.preview.emergentagent.com/`
  (same-origin) → no CORS triggered → flow auth funziona. **In prod**
  stesso pattern same-origin (`orbusonline.net`).
- Local dev (localhost:3000 → preview backend) richiede `CORS_ORIGINS=http://localhost:3000` per dev experience pura. Non blocking per deploy.


## ROUND 11.2 FASE B (TASK 1+2+3+4) — 2026-06-28

### TASK 2 — Specialization P0 atomicity
- `app/training/services.py::apply_specialization` rifattorizzato con compensating pattern (audit triplo stato `pending/committed/rolled_back`). Error codes 4xx strutturati: `training.specialization.{insufficient_gold,invalid_spec,requirements_not_met,adventurer_retired,internal_error}`. Nessun 500 raggiungibile da happy/known-error path. Solo `internal_error` (500) con gold refundato.
- Nuovi audit event_types in `app/audit/log.py`: `training_specialization_attempt`, `training_specialization_committed`, `training_specialization_rolled_back`, `training_specialization_refund`.
- Script CLI `app/scripts/refund_failed_specializations.py` con `--dry-run` (default) e `--apply`. Idempotente. Mode A (orphan signature pointer storico) + Mode B (pending audit senza committed).
- 10 test in `tests/backend_round112_specialize_atomicity_test.py` (incluso compensating con monkeypatch + idempotency CLI).

### TASK 1 — Recruitment refresh ≠ recruit
- Backend `app/recruitment/services.py::recruit_from_offer`: aggiunto post-insert verify atomico (insert-first → count → se cap superato, delete + refund + restore offer + 423). Risolve race condition concurrent recruit.
- FE `Recruitment.jsx` `CandidateCard`: prop `overCap` → bottone disabled+tooltip "Capienza avventurieri raggiunta. Potenzia Dormitori o congeda."
- 7 test in `tests/backend_round112_t1_t4_test.py` (refresh/recruit at-cap/over-cap/under-cap + concurrent exploit + cooldown non regredito).

### TASK 4 — Cap roster Lv11=100
- `app/territory/structures.py`: `dormitories.max_level: 6 → 11`, rimosso `max_legacy_level`. `DORMITORY_CAP_BY_LEVEL` esteso (Lv7=40, Lv8=50, Lv9=65, Lv10=80, Lv11=100).
- `app/territory/costs.py`: Lv7-Lv11 costi progressivi (8500g → 50000g + iron_shard/greater_arcane_dust/lesser_arcane_dust). Rimosso `_LEGACY_ONLY` sentinel.
- FE constants allineate in 3 file: `Recruitment.jsx`, `OverCapBanner.jsx`, `utils/structures.js`.
- 8 test in `tests/backend_round112_t1_t4_test.py` (catalog max_level, cap curve, Lv6→Lv7 purchasable, cap server-authoritative Lv11=100, no upgrade beyond Lv11, monotonic cost curve, FE↔BE constants alignment).

### TASK 3 — Auction CTA "Conferma acquisto" / "Annulla"
- FE `Auction.jsx::BuyTab`: inline confirm trasformato in mini-dialog con `role="dialog" aria-modal="true"`. Bottoni "Conferma acquisto" (primary) + "Annulla" (secondary, full-width) + X close dedicato. Layout responsive (flex-col su mobile, flex-row su >=sm).
- i18n: aggiunte keys `auction.buy_confirm_btn` + `auction.buy_cancel_btn` in `lang/it.json` ("Conferma acquisto" / "Annulla") + `lang/en.json` ("Confirm purchase" / "Cancel").
- 8 test in `tests/backend_round112_t3_auction_test.py` (`is_own` server-authoritative, no PII leak `seller.user_id`, gold/sold/own purchase blocks 4xx, happy path atomic, concurrent double-buy serialized, i18n keys present).

### Guida player-facing
- `pages/Guide.jsx`: sezione Dormitori aggiornata con scala progressiva Lv1-Lv11 (5→100). Nota "Lv7-Lv11" rebrand da "Lv7 LEGACY" a "Lv7-Lv11 ROUND 11.2" con costi gold+materiali progressivi. Sezioni `recruitment_refresh_over_cap` e `roster_cap_progression` aggiornate (refresh sempre OK over-cap, recruit blocca con tooltip).

### Note
- Test t1_07 inizialmente fallibile → riscritto recruit con compensating "insert-then-verify" (3/3 PASS deterministico).
- Test t3 (auction): 1 skip su test_t3_06 happy path purchase per bug preesistente del seed (gestito con `pytest.skip` documentato; non in scope Round 11.2).
- Tutti i nuovi error_code mantengono retrocompat: legacy codes `training.spec_unknown`, `training.insufficient_gold`, etc. sostituiti dai nuovi prefissi `training.specialization.*`.

### TASK 1bis — Adventurer name uniqueness EXCLUDE retired (2026-06-28)

**Bug**: Rename a nome di un avventuriero `is_retired=True` veniva bloccato con 409, sbagliato.

**Fix**: `app/adventurers/services.py::rename_adventurer` — aggiunto `"is_retired": {"$ne": True}` alla query di collision check. Error message convertito a dict strutturato:
```json
{"code": "adventurer.name.duplicate_active",
 "user_message": "Esiste già un avventuriero attivo con questo nome nella tua gilda."}
```

**FE**: nessun cambio logico. `formatApiError` legge già `detail.user_message` correttamente. Messaggio toast renderizza leggibile, no `[object Object]`.

**6 test** in `tests/backend_round112_adventurer_name_uniqueness_test.py` (rename→retired name OK, →active 409, case-insensitive 409, retired keeps name in expedition_members snapshot).

**Storia preservata**: retired adv mantengono il loro `name` field + tutti gli `adventurer_name_snapshot` in `expedition_members` invariati. Nessuna migrazione, nessun hard delete.

### FASE B sanity UI P1 — /territory Dormitori legacy gating fix (2026-06-28)

**Bug regressione UI**: Dopo TASK 4 backend (Lv11 cap 100), il file `frontend/src/utils/structures.js` aveva ancora gating legacy che bloccava l'upgrade su `acquired_via=migration_legacy`:
- `MAX_LEVEL=6` hardcoded → tutti i dormitori >Lv6 considerati maxed
- `if (isLegacy) return { isMaxed: true }` → blocco incondizionato
- `desc_it/en` mostravano vecchia scala `(5/10/15/20/25/30)` (6 livelli)
- `UPGRADE_COSTS.dormitories` aveva `null` per Lv7+ (migration-only)

**Fix** in 3 punti (`utils/structures.js`):
1. `desc_it/en` aggiornati: "scala 1-11, cap massimo 100" + sequenza completa visibile.
2. `UPGRADE_COSTS.dormitories` esteso a 11 entries (Lv7=8500g+materials → Lv11=50000g+materials), allineato esattamente con `app/territory/costs.py` BE.
3. Aggiunto `STRUCTURE_MAX_LEVEL = { dormitories: 11 }` + helper `getStructureMaxLevel(slug)`. `resolveCardState` usa `maxLevel` per-struttura (fallback `MAX_LEVEL=6` per altre).
4. `legacy && isMaxed` → ritorna kind=`legacy` (info display). `legacy && !isMaxed` → flusso normale `upgradable/buyable/insufficient_gold` + flag `isLegacy=true` come info badge (NON blocca).

**3 test FE** aggiunti in `backend_round112_t1_t4_test.py`:
- `test_t4_p1_01`: Lv7 legacy → `isMaxed=false`, `targetLevel=8`, `kind=upgradable`, `isLegacy=true`.
- `test_t4_p1_02`: Lv11 → `isMaxed=true`.
- `test_t4_p1_03`: desc contiene "100" e "11"/"1-11", NON contiene "max 6" né "(5/10/15/20/25/30)".

Test eseguiti via Node subprocess che carica `structures.js` (ESM→CJS shim minimale).

**Verifica visiva**: `/territory` con tester guild (Dormitories Lv7 migration_legacy) mostra:
- Card senza badge "LEGACY"
- Bottone "▶ Upgrade to Lv 8 (14000g)" ATTIVO (costo Lv8 da BE)
- Descrizione nuova scala 1-11
- Capacity: 40 adventurers (corretto Lv7=40)
- Altre strutture invariate.

**Backend**: invariato (nessuna change).

### P2 — Preview auction seed corruption (NON fixato, prod intatto)

`GET /api/auction/listings` ritorna HTTP 500 in PREVIEW DB per bug seed legacy `item_template_id` mancante. UI modal Conferma/Annulla è "code-ready" + ARIA OK + handler safe (verificato static), ma non runtime-tested per assenza listing. **Prod**: TC2 smoke PASS, GET regolarmente `{total:0, listings:[]}`. Issue ESCLUSIVAMENTE preview. Out-of-scope Round 11.2. Da riesercitare quando ci sarà la prima asta reale in prod.

## ROUND 11.2 FASE C — TASK 5a Admin Ops BACKEND ONLY (2026-06-28)

### Endpoint admin (5 nuovi, già montati su `/api/admin` router esistente)
- `GET  /api/admin/guilds/search?q=&limit=&offset=` — paginato (default 20, max 50), match name (case-insensitive partial) o public_id (8-hex exact). Response: `{total, limit, offset, guilds:[{public_id, name, owner_email_masked, gold, roster_count, roster_cap, dormitory_level, is_test_artifact, owner_is_test_user, created_at, updated_at}]}`.
- `GET  /api/admin/guilds/{id_or_public}` — accetta sia internal uuid sia public_id 8-hex. Response: detail completo con `roster:{current,cap,dormitory_level}`, `territory:{dormitories_level,max_buildings_level}`, `flags:{is_test_artifact,owner_is_test_user}`.
- `POST /api/admin/guilds/{id}/grant-gold` — body `{amount>0, reason min_length=3}`, max `ADMIN_MAX_GRANT_GOLD` (env, default 100000). Atomic `$inc gold`, audit `admin_gold_granted` con `{gold_before, gold_after, reason, admin_actor_email_masked}`.
- `POST /api/admin/guilds/{id}/grant-item` — body `{item_slug, quantity>0, reason min_length=3}`, max `ADMIN_MAX_GRANT_ITEM_QTY` (env, default 1000). Validazione: slug deve esistere; refuse `is_bound=true`; refuse P2W (`can_be_sold_for_real_money + affects_combat + !is_cosmetic`). Stackable → upsert qty; non-stackable → N entries. Audit `admin_item_granted`.
- `GET  /api/admin/audit?guild=&action=&since=&limit=&offset=` — paginato (default 50, max 200). PII mask su tutti i campi (`admin_actor_email_masked` only).

### Middleware `require_admin` (estende `get_admin_user` esistente)
File: `app/core/security.py::get_admin_user`. Logic: primary `user.is_admin == True` (DB flag); fallback `ADMIN_EMAILS` env allowlist (comma-separated, lowercase). Non-admin → 403 con `{code: "admin.forbidden", user_message: "Accesso admin richiesto."}`.

### Side-task: `is_admin` esposto in `/api/auth/me`
Già esposto via `public_user()` projection in `auth/services.py` (preesistente). Verificato che il payload `me` include `is_admin: true/false`.

### Audit events nuovi (in `app/audit/log.py` allowlist)
- `admin_gold_granted`
- `admin_item_granted`

### Sicurezza
- Tutti i 5 endpoint protetti da `Depends(get_admin_user)`.
- NO hard delete. NO modifica email/password/token.
- Grant: reason obbligatoria (min_length 3), max amount/qty env-configurable.
- Email mascherata `t***@orbus.test` in tutti i payload (search/detail/audit metadata).
- No `seller.user_id`, no raw email, no `$oid` ObjectId in nessuna risposta.

### 11 test PASS
`tests/backend_round112_admin_ops_test.py`:
1. non_admin → 403 ✅
2. admin → 200 + lista ✅
3. paginazione limit/offset ✅
4. detail con masked email + roster/cap/flags ✅
5. grant-gold incrementa + audit `admin_gold_granted` ✅
6. reason min_length=3 → 422 ✅
7. amount<=0 / >max → 422 ✅
8. grant-item crea inventory entries + audit `admin_item_granted` ✅
9. unknown slug → 422 `admin.item.unknown_slug` ✅
10. /api/admin/audit filtrato per guild+action ✅
11. no PII leak (email/user_id raw, $oid) ✅

### OpenAPI count: 103 → 108 (+5 esatti).

### TASK 5b — Admin Ops FRONTEND (2026-06-28)

**File creati**:
- `frontend/src/pages/AdminOps.jsx` (route `/admin/ops`)
- `frontend/src/components/admin/GrantGoldModal.jsx` (doppia conferma)
- `frontend/src/components/admin/GrantItemModal.jsx` (doppia conferma + 422 mapping)
- `backend/tests/frontend_round112_admin_ops_test.py` (8 test)

**File modificati**:
- `frontend/src/App.js` — route `/admin/ops` aggiunta
- `frontend/src/components/AppHeader.jsx` — nav link "ADMIN OPS" condizionale `user?.is_admin`
- `backend/app/audit/log.py::write_audit` — ora ritorna `Optional[str]` (l'id del doc) invece di `None` (side-fix audit_event_id)
- `backend/app/admin/routes.py::grant_gold` e `grant_item` — propagano `event_id` dal `write_audit`

**Access control**: route `/admin/ops` mostra component `<NotAuthorized />` (pulito, con icona ⛔ + link "Torna al Dashboard") se `user?.is_admin !== true`. NO `<Navigate>` silenzioso.

**Side-fix audit_event_id**: completato. `write_audit` ora ritorna `doc["id"]` su success o `None` su failure. Effetto runtime: `POST grant-gold` ritorna `audit_event_id: "a0fc8b65-..."` invece di `null`. Tutti gli altri call site di `write_audit` (~50+) ignorano il return → no breakage.

**Test FE 8/8 PASS**: source-static checks (testid, ARIA, validation hooks, conditional nav) + live backend contract verification (search endpoint, masked email, 422 unknown_slug).

**Screenshot verificato**: `/admin/ops` con tester@orbus.test → Search tab carica 10527 guild paginati, click row → Detail panel con masked email + flags + bottoni Grant Gold/Item visibili.

**Sweep finale FASE C 5a+5b**: 75 PASS + 1 SKIP (Round 11.2 + 11.1 stack completo).

### TASK 5b P1 — Double-submit useRef sync guard (2026-06-28)

**Bug**: Doppio click rapido (3.5ms apart) su "Conferma" in GrantGoldModal/GrantItemModal emetteva 2 POST consecutivi. `disabled={busy}` insufficiente: React batching commit `setBusy(true)` DOPO che il secondo handler già giravato. Race tra setState async e handler sync.

**Impatto pre-fix**: ogni grant accidentalmente raddoppiabile (gold scalato 2x, audit doppio). Verificato via TC2c tester E2E.

**Fix** (defense-in-depth, entrambi i modal):
```jsx
const submittingRef = useRef(false);
async function onSubmit() {
  if (submittingRef.current) return;  // SYNC guard
  submittingRef.current = true;
  setBusy(true);
  try { await api.post(...); }
  finally {
    setBusy(false);
    submittingRef.current = false;
  }
}
```
`disabled={busy}` mantenuto per la UX visiva (loading state); il `ref` è l'unica protezione reale.

**Backend invariato**: il bug era esclusivamente FE handler.

**3 nuovi test** in `frontend_round112_admin_ops_test.py`:
- `test_t5b_p1_01_grant_gold_double_click_emits_only_one_post`: simulazione Node di 2 invocazioni sync della funzione `submit` → verifica callCount === 1.
- `test_t5b_p1_02_grant_item_double_click_emits_only_one_post`: stesso pattern.
- `test_t5b_p1_03_after_error_submit_re_enabled`: dopo error 422, ref MUST reset a false (verifica `finally`), retry attesa funziona.

**Sweep finale**: 78 PASS + 1 SKIP su 7 suite Round 11.2+11.1 (era 75/76 pre-fix).

**Audit doppi storici**: gli audit `admin_gold_granted` con timestamp `17:58:39.155-159 reason="double submit test"` (TC2c tester E2E) restano in DB come effetti collaterali del test P1. NO hard delete (vincolo brief).
