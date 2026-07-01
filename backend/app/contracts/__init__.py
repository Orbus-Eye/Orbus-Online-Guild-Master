"""ROUND 6D — Contract Board (daily + weekly contracts + guild milestones).

Server-authoritative retention loop layered on top of the existing audit /
quest event sources. Design constraints (binding):

  • NO P2W (gold/material/reputation reward only; NO power gear, NO premium).
  • NO XP gilda (deferred to a future round).
  • Server-authoritative progress (increment-only via hook, claim is atomic CAS).
  • Lazy reset (UTC midnight for daily, ISO Monday for weekly; pattern reused
    from app.quests.services).
  • Idempotent — claiming a contract twice or the same milestone twice is a
    no-op (atomic filter on `claimed: False`).
  • Reputation reward source: NEW. Active on weekly + milestones (anti-inflation
    on daily). See `catalog.py` reward tables.
"""
