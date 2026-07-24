"""RT2-B-2B-1 · Test suite (37 items · PM Message 151 §15-16 verbatim).

Coverage:
- Mark: apply/duplicate-pair/cap/refresh/expired-refresh/lazy-expiration/cleanup/multi-CdV
- Fragment: gain-trusted/gain-untrusted/cap/overflow/spend/insufficient/invalid-amount
- Resource segment: phase-reset/expedition-reset/open/partial-preserves/zero-closes/explicit-close/focus-cap
- Ordering/dedup: total-ordering/replay/payload-mismatch
- Receipts: ordinary-cap/reserved-cap/no-eviction/size-stress
- Lease/CAS: acquire/stale-fencing/CAS-conflict/retry-ceiling
- Gating: flag-off/non-test-user/mongo-allowlist
- Legacy invariance: response+reward
"""
