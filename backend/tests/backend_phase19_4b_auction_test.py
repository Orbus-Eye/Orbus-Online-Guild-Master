"""Phase 19.4b — Auction (renamed market) tests + legacy /api/market 307 redirect."""
import os
import uuid
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BASE_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or os.environ.get("BACKEND_URL", "http://localhost:8001")
).rstrip("/")


def _user(hint="p194ba"):
    tag = f"{hint}_{uuid.uuid4().hex[:6]}"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": f"{tag}@orbus.test", "username": tag, "password": "Test12345!",
    }, timeout=15)
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": f"{tag}@orbus.test", "password": "Test12345!",
    }, timeout=15)
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    requests.post(f"{BASE_URL}/api/guilds", json={"name": f"P194ba {tag[-5:]}"}, headers=h, timeout=15)
    return {"headers": h, "tag": tag}


class TestAuctionMigration:
    def test_A1_new_auction_endpoint_works(self):
        ctx = _user("a1")
        r = requests.get(f"{BASE_URL}/api/auction/listings", headers=ctx["headers"], timeout=15)
        assert r.status_code == 200, r.text
        assert "listings" in r.json()

    def test_A2_no_pii_in_listing_response(self):
        ctx = _user("a2")
        r = requests.get(f"{BASE_URL}/api/auction/listings?limit=20", headers=ctx["headers"], timeout=15)
        assert r.status_code == 200
        for L in r.json()["listings"]:
            for forbidden in ("seller_user_id", "seller_email", "email", "_id"):
                assert forbidden not in L, f"PII leak: {forbidden} in payload"
            # Sanity: public name allowed
            if "seller_public_name" in L or "seller_guild_name" in L:
                pass

    def test_A3_legacy_market_listings_307_redirect_get(self):
        ctx = _user("a3")
        # Do NOT auto-follow redirects
        r = requests.get(
            f"{BASE_URL}/api/market/listings",
            headers=ctx["headers"], timeout=15, allow_redirects=False,
        )
        assert r.status_code == 307, f"expected 307, got {r.status_code}"
        loc = r.headers.get("Location", "")
        assert "/api/auction/listings" in loc, f"redirect to {loc}"

    def test_A4_legacy_market_listings_307_preserves_query(self):
        ctx = _user("a4")
        r = requests.get(
            f"{BASE_URL}/api/market/listings?rarity=Common&limit=10",
            headers=ctx["headers"], timeout=15, allow_redirects=False,
        )
        assert r.status_code == 307
        loc = r.headers.get("Location", "")
        assert "rarity=Common" in loc and "limit=10" in loc, f"query lost: {loc}"

    def test_A5_legacy_market_buy_307(self):
        ctx = _user("a5")
        bogus = str(uuid.uuid4())
        r = requests.post(
            f"{BASE_URL}/api/market/listings/{bogus}/buy",
            headers=ctx["headers"], json={}, timeout=15, allow_redirects=False,
        )
        assert r.status_code == 307
        assert f"/api/auction/listings/{bogus}/buy" in r.headers.get("Location", "")

    def test_A6_legacy_market_delete_307(self):
        ctx = _user("a6")
        bogus = str(uuid.uuid4())
        r = requests.delete(
            f"{BASE_URL}/api/market/listings/{bogus}",
            headers=ctx["headers"], timeout=15, allow_redirects=False,
        )
        assert r.status_code == 307

    def test_A7_legacy_endpoints_marked_deprecated_in_openapi(self):
        r = requests.get(f"{BASE_URL}/api/openapi.json", timeout=15)
        paths = r.json()["paths"]
        for legacy in ("/api/market/listings", "/api/market/listings/{listing_id}/buy"):
            assert legacy in paths, f"missing alias path: {legacy}"
            methods = paths[legacy]
            for m, spec in methods.items():
                if m in ("get", "post", "delete"):
                    assert spec.get("deprecated") is True, f"{m} {legacy} should be deprecated"
