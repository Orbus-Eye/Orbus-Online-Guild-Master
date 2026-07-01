"""Phase 14.8 → 19.4b — Marketplace routes (DEPRECATED ALIAS).

Phase 19.4b renamed the player-to-player marketplace to "Auction" (mounted
at `/api/auction/*`). These legacy `/api/market/listings*` paths remain as
**deprecated 307 redirects** so existing API consumers (older mobile builds,
external scripts, in-flight requests during deploy) don't break.

Behavior:
  • Every legacy URL returns HTTP 307 with `Location` pointing at the
    new `/api/auction/*` equivalent and query string preserved.
  • OpenAPI marks each route as `deprecated=True` with a description
    pointing at the new path.
  • To be removed in a future release. New clients MUST use `/api/auction/*`.
"""
from urllib.parse import urlencode

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse


router = APIRouter(prefix="/api/market", tags=["market (deprecated)"])

_DEPRECATION_NOTE = (
    "DEPRECATED — use `/api/auction/...` instead. This endpoint returns a "
    "307 redirect. Will be removed in a future release."
)


def _redirect(request: Request, new_path: str) -> RedirectResponse:
    qs = urlencode(list(request.query_params.multi_items()))
    target = f"{new_path}?{qs}" if qs else new_path
    return RedirectResponse(url=target, status_code=307)


@router.get("/listings", deprecated=True, description=_DEPRECATION_NOTE)
async def deprecated_get_listings(request: Request):
    return _redirect(request, "/api/auction/listings")


@router.get("/listings/mine", deprecated=True, description=_DEPRECATION_NOTE)
async def deprecated_get_my_listings(request: Request):
    return _redirect(request, "/api/auction/listings/mine")


@router.post("/listings", deprecated=True, description=_DEPRECATION_NOTE)
async def deprecated_post_create_listing(request: Request):
    return _redirect(request, "/api/auction/listings")


@router.delete("/listings/{listing_id}", deprecated=True, description=_DEPRECATION_NOTE)
async def deprecated_delete_listing(listing_id: str, request: Request):
    return _redirect(request, f"/api/auction/listings/{listing_id}")


@router.post("/listings/{listing_id}/buy", deprecated=True, description=_DEPRECATION_NOTE)
async def deprecated_post_buy_listing(listing_id: str, request: Request):
    return _redirect(request, f"/api/auction/listings/{listing_id}/buy")


__all__ = ["router"]
