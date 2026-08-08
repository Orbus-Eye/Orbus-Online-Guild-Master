"""Offline, read-only audit for an Orbus item-catalog snapshot.

Accepted inputs: JSON array, JSONL, BSON and their gzip-compressed variants.
The command never connects to Mongo and never mutates its input.

Usage:
    python -m app.scripts.t0_item_catalog_audit path/to/items.jsonl
"""
from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path
from typing import Iterable, Mapping

from app.items.catalog_contract import (
    ENDGAME_RARITIES,
    ITEM_CATALOG_TARGET_TOTAL,
    RARITY_CATALOG_TARGETS,
    audit_catalog_items,
    ordinary_random_drop_allowed,
)
from app.shared.constants import ADVENTURER_MAX_LEVEL
from app.shared.rarity import canonicalize_rarity


def _read_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    return gzip.decompress(data) if path.suffix.casefold() == ".gz" else data


def load_snapshot(path: Path) -> list[dict]:
    """Load a supported local snapshot without side effects."""
    data = _read_bytes(path)
    logical_suffixes = [
        suffix.casefold()
        for suffix in path.suffixes
        if suffix.casefold() != ".gz"
    ]
    suffix = logical_suffixes[-1] if logical_suffixes else ""
    if suffix == ".bson":
        from bson import decode_all

        return list(decode_all(data))
    text = data.decode("utf-8-sig")
    if suffix == ".jsonl":
        return [
            json.loads(line)
            for line in text.splitlines()
            if line.strip()
        ]
    payload = json.loads(text)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("items", "rows", "documents"):
            if isinstance(payload.get(key), list):
                return payload[key]
    raise ValueError("snapshot JSON must contain an array or items/rows/documents")


def _duplicates(values: Iterable[tuple[str, str]]) -> list[dict]:
    grouped: dict[str, list[str]] = {}
    for normalized, slug in values:
        if normalized:
            grouped.setdefault(normalized, []).append(slug)
    return [
        {"value": value, "slugs": sorted(slugs)}
        for value, slugs in sorted(grouped.items())
        if len(slugs) > 1
    ]


def build_dry_run_report(items: Iterable[Mapping[str, object]]) -> dict:
    """Return actionable findings while preserving every input row."""
    rows = [
        dict(item)
        for item in items
        if item.get("is_active", True) is not False
        and item.get("is_test") is not True
    ]
    quota_audit = audit_catalog_items(rows)
    duplicate_slugs = _duplicates(
        (
            str(row.get("slug") or "").strip().casefold(),
            str(row.get("slug") or ""),
        )
        for row in rows
    )
    duplicate_names = _duplicates(
        (
            str(
                row.get("display_name_it")
                or row.get("name")
                or ""
            ).strip().casefold(),
            str(row.get("slug") or ""),
        )
        for row in rows
    )

    endgame_below_cap = []
    forbidden_ordinary_drop = []
    missing_source = []
    by_class: Counter[str] = Counter()
    universal = 0
    unclassified_binding = 0

    for row in rows:
        slug = str(row.get("slug") or "")
        rarity = canonicalize_rarity(row.get("rarity"))
        declared_level = row.get(
            "required_adventurer_level",
            row.get("level_required"),
        )
        if (
            rarity in ENDGAME_RARITIES
            and declared_level != ADVENTURER_MAX_LEVEL
        ):
            endgame_below_cap.append(
                {
                    "slug": slug,
                    "rarity": rarity,
                    "declared_level": declared_level,
                    "required_level": ADVENTURER_MAX_LEVEL,
                }
            )

        acquisition_mode = str(
            row.get("acquisition_mode") or ""
        ).strip().casefold()
        if (
            acquisition_mode in {"ordinary_random_drop", "random_drop"}
            and not ordinary_random_drop_allowed(rarity)
        ):
            forbidden_ordinary_drop.append(
                {"slug": slug, "rarity": rarity}
            )

        sources = row.get("acquisition_sources") or []
        if not (
            row.get("source")
            or row.get("lore_source")
            or sources
        ):
            missing_source.append(slug)

        classes = row.get("recommended_classes") or row.get("class_tags") or []
        direct_class = (
            row.get("canonical_class_slug")
            or row.get("class_slug")
            or row.get("required_class_optional")
        )
        if direct_class:
            classes = [direct_class, *classes]
        unique_classes = {
            str(value).strip().casefold()
            for value in classes
            if str(value).strip()
        }
        if unique_classes:
            for class_slug in unique_classes:
                by_class[class_slug] += 1
        elif row.get("item_binding_policy") == "universal":
            universal += 1
        else:
            unclassified_binding += 1

    return {
        "mode": "dry_run_read_only",
        "mutations": 0,
        "quota_audit": quota_audit,
        "findings": {
            "duplicate_slugs": duplicate_slugs,
            "duplicate_names_casefold": duplicate_names,
            "endgame_below_max_level": endgame_below_cap,
            "forbidden_ordinary_endgame_drops": forbidden_ordinary_drop,
            "missing_source_slugs": sorted(missing_source),
            "class_item_counts": dict(sorted(by_class.items())),
            "universal_count": universal,
            "unclassified_binding_count": unclassified_binding,
        },
        "ready_for_1500_import": (
            quota_audit["current_total"] <= ITEM_CATALOG_TARGET_TOTAL
            and not quota_audit["has_quota_overflow"]
            and quota_audit["invalid_rarity_count"] == 0
            and not duplicate_slugs
            and not duplicate_names
            and not endgame_below_cap
            and not forbidden_ordinary_drop
        ),
        "targets": RARITY_CATALOG_TARGETS,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit offline read-only del catalogo item Orbus",
    )
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    report = build_dry_run_report(load_snapshot(args.snapshot))
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
