"""ROUND 16.5.4c ADJ-1 — Rarity canonicalizer unit tests.

Verifica che `canonicalize_rarity` produca sempre la forma Capitalized
indipendentemente da case/spazi, e ritorni None (senza sollevare) per
input non riconoscibili.
"""
from __future__ import annotations

import pytest

from app.shared.rarity import canonicalize_rarity, CANONICAL_RARITIES


class TestCanonicalizeRarity:
    @pytest.mark.parametrize("raw", ["Common", "common", "COMMON",
                                    "  common  ", "Common "])
    def test_common_variants(self, raw):
        assert canonicalize_rarity(raw) == "Common"

    @pytest.mark.parametrize("raw", ["Uncommon", "uncommon", "UNCOMMON",
                                    "unCommon"])
    def test_uncommon_variants(self, raw):
        assert canonicalize_rarity(raw) == "Uncommon"

    @pytest.mark.parametrize("raw", ["Rare", "rare", "RARE", "  Rare"])
    def test_rare_variants(self, raw):
        assert canonicalize_rarity(raw) == "Rare"

    @pytest.mark.parametrize("raw", ["Epic", "epic", "EPIC", "ePiC"])
    def test_epic_variants(self, raw):
        assert canonicalize_rarity(raw) == "Epic"

    @pytest.mark.parametrize("raw", ["Legendary", "legendary",
                                    "LEGENDARY", "LEGENDARY  "])
    def test_legendary_variants(self, raw):
        assert canonicalize_rarity(raw) == "Legendary"

    def test_none_input(self):
        assert canonicalize_rarity(None) is None

    def test_empty_string(self):
        assert canonicalize_rarity("") is None
        assert canonicalize_rarity("   ") is None

    def test_unrecognized_returns_none(self):
        assert canonicalize_rarity("mythic") is None
        assert canonicalize_rarity("junk") is None
        assert canonicalize_rarity("weird") is None

    def test_non_string_returns_none(self):
        assert canonicalize_rarity(42) is None
        assert canonicalize_rarity(True) is None
        assert canonicalize_rarity(["Epic"]) is None
        assert canonicalize_rarity({"rarity": "Epic"}) is None

    def test_canonical_constants(self):
        assert CANONICAL_RARITIES == (
            "Common", "Uncommon", "Rare", "Epic", "Legendary",
        )
        # Every canonical form must round-trip.
        for r in CANONICAL_RARITIES:
            assert canonicalize_rarity(r) == r
            assert canonicalize_rarity(r.lower()) == r
            assert canonicalize_rarity(r.upper()) == r

    def test_never_raises(self):
        # Even weird inputs must never raise.
        for weird in [object(), 3.14, b"epic"]:
            try:
                canonicalize_rarity(weird)
            except Exception as exc:  # noqa: BLE001
                pytest.fail(
                    f"canonicalize_rarity({weird!r}) sollevata {exc!r}, "
                    f"deve invece ritornare None."
                )
