# Mobile Testing Policy — Orbus Online

**Adopted**: 2026-07-01 (Round 16.3 P3.6)

## Context

`browser-use` headless (default automation) does NOT resize viewport reliably in the pod container — resize events fire but `window.innerWidth` remains at the desktop default. This makes it unreliable for asserting mobile-first responsive behavior (touch targets ≥44px, no horizontal overflow, etc.).

## Policy

For mobile-touching changes (any change to a page/component/nav that has a mobile layout branch), run the Playwright mobile smoke script **manually** before merging:

```bash
python /app/scripts/mobile_smoke.py
```

The script:
- Opens each critical page at **390×844** viewport (iPhone 12 baseline)
- Logs in as `tester@orbus.test` once and reuses the session
- Screenshots every page under `/app/_mobile_smoke_screenshots/<page>_mobile_390x844.png`
- Asserts `documentElement.scrollWidth === documentElement.clientWidth` on each page (no horizontal overflow)
- Returns exit code:
  - **0** — all pages OK
  - **1** — ≥1 page has horizontal overflow (blocker)
  - **2** — Playwright infra failure

## Covered pages (as of 2026-07-01)

- `/dashboard`
- `/stables` (Phase 8 V1)
- `/pvp`, `/pvp-season` (Phase 7A/7B)
- `/world`, `/forge`, `/achievements`, `/class-halls`

New pages MUST be added to the `PAGES` list in `mobile_smoke.py` when they become part of the app.

## Why manual, not automated in CI

- Playwright browser startup is expensive (~5s cold start)
- Screenshots need visual review — infra can flag overflow but not "the layout is broken but non-overflowing"
- CI already runs pytest + `yarn build` + `yarn lint` — mobile smoke is a release checkpoint, not a per-commit gate

## Reference

- Script: `/app/scripts/mobile_smoke.py`
- Screenshots: `/app/_mobile_smoke_screenshots/`
- Related: `/app/memory/pytest_db_isolation_policy.md`
