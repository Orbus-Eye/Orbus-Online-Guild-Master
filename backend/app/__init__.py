"""Orbus backend — application package.

Phase 5.5 partial modularisation. The route handlers still live in
`backend/server.py` for now; this package isolates the pieces that benefit
the most from being modularised:

- `app.shared.constants`: tunable gameplay/security constants (single source
  of truth, no behaviour change vs Phase 7)
- `app.seeds.seed_data`: declarative seed payloads for classes, traits,
  dungeons and items
- `app.expeditions.formulas`: pure functions (no I/O, no Mongo) used by the
  expedition flow
- `app.expeditions.loot_tables`: per-dungeon loot weights + a single
  weighted sampler used by the resolver

Importing from `server.py` keeps backwards compatibility for the test
suite and supervisor entrypoint (`uvicorn server:app`).
"""
