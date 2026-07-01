"""ROUND 12 — Season system.

Read-only public endpoints + admin-gated lifecycle endpoints.
Invariants:
  * Only ONE season with `status="active"` exists at any given time
    (enforced both via partial unique index and applicative CAS guard).
  * `season_id` is uuid4 string; `public_id` shorter slug for URLs.
  * All timestamps stored as ISO strings UTC.
"""
