"""ROUND 11.1 B1 — Centralized bound-item guards.

Single source of truth for the 5 user-facing error codes used when a
bound (refinement/enchant) or adventurer-bound inventory item blocks a
business operation. All raise `HTTPException(status_code=422)` with a
structured detail dict so the frontend can i18n-resolve the code and
display contextual messaging without parsing free-form strings.

Codes (final, ROUND 11.1):
  • `auction.bound_to_adventurer_not_listable`   — list to auction
  • `auction.bound_to_adventurer_not_buyable`    — purchase from auction
  • `market.bound_to_adventurer_not_sellable`    — NPC shop sell
  • `equipment.bound_to_adventurer_not_transferable` — equip on another adv
  • `retire.bound_item_blocks_retirement`        — adventurer retire

All codes carry the optional `bound_to_adventurer_id` for diagnostic
context. None of the codes ever leak email, internal Mongo `_id`, raw
exceptions or PII.
"""
from __future__ import annotations

from fastapi import HTTPException

# ─── Code constants ──────────────────────────────────────────────────────
CODE_AUCTION_NOT_LISTABLE = "auction.bound_to_adventurer_not_listable"
CODE_AUCTION_NOT_BUYABLE = "auction.bound_to_adventurer_not_buyable"
CODE_MARKET_NOT_SELLABLE = "market.bound_to_adventurer_not_sellable"
CODE_EQUIPMENT_NOT_TRANSFERABLE = "equipment.bound_to_adventurer_not_transferable"
CODE_RETIRE_BLOCKED = "retire.bound_item_blocks_retirement"

# Backward-compat aliases so legacy clients reading the old code strings
# can still display SOMETHING during the rollout window. The interceptor
# in `frontend/src/lib/api.js` maps the new codes to localized strings.
LEGACY_ALIASES: dict[str, str] = {
    "auction.bound_item_not_sellable": CODE_MARKET_NOT_SELLABLE,
    "market.bound_item_not_sellable": CODE_MARKET_NOT_SELLABLE,
    "shop.sell.bound": CODE_MARKET_NOT_SELLABLE,
    "equipment.bound_to_other_adventurer": CODE_EQUIPMENT_NOT_TRANSFERABLE,
    "adventurer.has_bound_items": CODE_RETIRE_BLOCKED,
    "Item is not tradeable": CODE_MARKET_NOT_SELLABLE,
}


def _raise(code: str, *, source: str, user_message: str,
           bound_to_adventurer_id: str | None = None,
           **extra) -> None:
    """Single `raise HTTPException` factory.

    All bound guards use status 422 (business-rule violation, request was
    valid syntactically). The frontend interceptor in `api.js` reads
    `detail.code` and replaces `user_message` with the localized string.
    """
    detail: dict = {
        "code": code,
        "source": source,
        "user_message": user_message,
    }
    if bound_to_adventurer_id is not None:
        detail["bound_to_adventurer_id"] = bound_to_adventurer_id
    detail.update(extra)
    raise HTTPException(status_code=422, detail=detail)


# ─── Public API ──────────────────────────────────────────────────────────
def raise_auction_not_listable(*, source: str,
                                bound_to_adventurer_id: str | None = None) -> None:
    _raise(
        CODE_AUCTION_NOT_LISTABLE,
        source=source,
        bound_to_adventurer_id=bound_to_adventurer_id,
        user_message=(
            "Questo oggetto è legato a un avventuriero e non può "
            "essere messo all'asta."
        ),
    )


def raise_auction_not_buyable(*, source: str,
                               bound_to_adventurer_id: str | None = None) -> None:
    _raise(
        CODE_AUCTION_NOT_BUYABLE,
        source=source,
        bound_to_adventurer_id=bound_to_adventurer_id,
        user_message=(
            "Questo oggetto è legato a un avventuriero specifico e "
            "non può essere acquistato da te."
        ),
    )


def raise_market_not_sellable(*, source: str,
                               bound_to_adventurer_id: str | None = None) -> None:
    _raise(
        CODE_MARKET_NOT_SELLABLE,
        source=source,
        bound_to_adventurer_id=bound_to_adventurer_id,
        user_message=(
            "Questo oggetto è legato a un avventuriero e non può essere venduto."
        ),
    )


def raise_equipment_not_transferable(*, source: str,
                                      bound_to_adventurer_id: str | None = None,
                                      target_adventurer_id: str | None = None) -> None:
    _raise(
        CODE_EQUIPMENT_NOT_TRANSFERABLE,
        source=source,
        bound_to_adventurer_id=bound_to_adventurer_id,
        target_adventurer_id=target_adventurer_id,
        user_message=(
            "Questo oggetto è legato a un altro avventuriero. "
            "Solo l'avventuriero a cui è legato può equipaggiarlo."
        ),
    )


def raise_retire_blocked(*, source: str, adventurer_id: str,
                          bound_count: int, bound_items: list[str]) -> None:
    _raise(
        CODE_RETIRE_BLOCKED,
        source=source,
        adventurer_id=adventurer_id,
        bound_count=bound_count,
        bound_items=bound_items[:10],
        user_message=(
            f"Avventuriero ha {bound_count} oggetto/i legato/i. "
            f"Trasferisci o sblocca i seguenti item prima di congedarlo: "
            f"{', '.join(bound_items[:10])}."
        ),
    )


__all__ = [
    "CODE_AUCTION_NOT_BUYABLE",
    "CODE_AUCTION_NOT_LISTABLE",
    "CODE_EQUIPMENT_NOT_TRANSFERABLE",
    "CODE_MARKET_NOT_SELLABLE",
    "CODE_RETIRE_BLOCKED",
    "LEGACY_ALIASES",
    "raise_auction_not_buyable",
    "raise_auction_not_listable",
    "raise_equipment_not_transferable",
    "raise_market_not_sellable",
    "raise_retire_blocked",
]
