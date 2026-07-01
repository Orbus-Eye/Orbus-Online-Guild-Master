"""ROUND 6B.1 — Declarative unlock requirements.

Maps abstract action codes to the (structure, min_level) gate. Data only:
no enforcement happens here. ROUND 6B.2 wires `require_unlocked(action)`
into the auction/forge/raid/chat/consortium/shop routes.

Naming conventions:
- `shop.system.*`     → NPC system shop (`/api/shop/*`, Phase 19.4b)
- `auction.*`         → player-to-player marketplace (`/api/auction/*`)
- `forge.*`           → upgrade ops (refine/enchant/disenchant/reroll)
- `workshop.craft.*`  → crafting recipes
- `raid.start.tN`     → raid difficulty tiers
- `dungeon.tier.N`    → dungeon tier gates
- `consortium.*`      → consortium ops
- `chat.*`            → chat channels

NB: the 5 legacy `/api/market/*` endpoints stay deprecated and ungated;
they will be removed in a later round, hence no `market.*` keys here.
"""
from __future__ import annotations

from typing import Optional

UNLOCK_REQUIREMENTS: dict[str, dict] = {
    # NPC system shop (Phase 19.4b)
    "shop.system.buy":      {"structure": "market_stall",       "min_level": 1},
    "shop.system.sell":     {"structure": "market_stall",       "min_level": 2},
    # Player-to-player auction
    "auction.buy":          {"structure": "auction_house",      "min_level": 1},
    "auction.list":         {"structure": "auction_house",      "min_level": 2},
    # Forge (upgrade)
    "forge.disenchant":     {"structure": "forge",              "min_level": 1},
    "forge.refine":         {"structure": "forge",              "min_level": 2},
    "forge.enchant":        {"structure": "forge",              "min_level": 3},
    "forge.reroll":         {"structure": "forge",              "min_level": 4},
    # Workshop (crafting)
    "workshop.craft.basic":    {"structure": "workshop", "min_level": 1},
    "workshop.craft.uncommon": {"structure": "workshop", "min_level": 2},
    "workshop.craft.rare":     {"structure": "workshop", "min_level": 3},
    # Raids
    "raid.start.t1":        {"structure": "war_room",           "min_level": 2},
    "raid.start.t2":        {"structure": "war_room",           "min_level": 3},
    # Dungeons (additive to existing per-dungeon gates in dungeons/gates.py)
    "dungeon.tier.1":       {"structure": "expedition_board",   "min_level": 2},
    "dungeon.tier.2":       {"structure": "expedition_board",   "min_level": 3},
    "dungeon.tier.3":       {"structure": "expedition_board",   "min_level": 4},
    # Consortium
    "consortium.join":      {"structure": "consortium_hall",    "min_level": 1},
    "consortium.create":    {"structure": "consortium_hall",    "min_level": 2},
    # Chat
    "chat.global":          {"structure": "communication_hall", "min_level": 1},
    "chat.consortium":      {"structure": "communication_hall", "min_level": 2},
}


def lookup(action: str) -> Optional[dict]:
    """Return the requirement dict for `action`, or None if no gate."""
    return UNLOCK_REQUIREMENTS.get(action)


def is_unlocked(structures: dict, action: str) -> bool:
    """Pure helper: given a `structures` dict (from `guild_structures.structures`)
    and an action code, return True iff the gate is satisfied.

    If the action has no requirement entry → always unlocked (default-open).
    """
    req = UNLOCK_REQUIREMENTS.get(action)
    if not req:
        return True
    cur = structures.get(req["structure"]) or {}
    return bool(cur.get("is_unlocked")) and int(cur.get("level", 0)) >= int(req["min_level"])


__all__ = ["UNLOCK_REQUIREMENTS", "lookup", "is_unlocked"]
