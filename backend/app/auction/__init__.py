"""Phase 19.4b — Auction module (player-to-player marketplace).

Public surface (`/api/auction/*`). This module is an URL-prefix mirror of
the original `/api/market/*` routes: same MongoDB collection
(`market_listings`), same handler functions (`app.market.services`), same
audit log events (kept under `market_*` event_type names for continuity).

The old `/api/market/*` routes remain mounted as **deprecated 307 redirects**
to `/api/auction/*` for backward compatibility.
"""
