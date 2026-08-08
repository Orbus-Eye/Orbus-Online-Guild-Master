"""Tester-only support for the item-first Class Hall journey.

The reset keeps account and guild history intact: active adventurers are
soft-retired, their equipment is released through the same reservation
invariant used by normal unequip, and five new Common recruits are created in
the explicit ``recruit_unassigned`` state.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections import Counter
from datetime import datetime, timezone

from fastapi import HTTPException

from app.adventurers.classless import is_explicit_classless_recruit
from app.adventurers.common import _generate_classless_candidate
from app.class_halls.catalog import CLASS_HALLS
from app.class_halls.build_reachability import (
    audit_class_hall_build_reachability,
)
from app.class_halls.mechanics import CLASS_MECHANICS


STARTER_TESTER_ROSTER_SIZE = 5
LONG_TERM_ITEM_TARGET = 1500
MIN_TUNING_SAMPLES_PER_BUILD = 5
MIN_REPLICATED_COHORTS_PER_BUILD = 2
# Seven-member endgame teams span 27 intentionally distinct class stat
# identities. A ±20% window is the calibrated comparison band for T8: narrow
# enough to reject stale content curves, broad enough to retain every class.
COMPARABLE_POWER_RATIO_MIN = 0.80
COMPARABLE_POWER_RATIO_MAX = 1.20
VERTICAL_SLICE_STEPS = (
    ("class_hall_chosen", "Class Hall scelta"),
    ("signature_item_equipped", "Item-firma equipaggiato"),
    ("resonant_dungeon_completed", "Dungeon completato con build risonante"),
    ("raid_completed", "Raid completato dopo il dungeon"),
    ("raid_reward_tracked", "Ricompensa raid registrata"),
    ("new_build_activated", "Nuova build item-driven attivata"),
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_classless_tester_adventurer(
    guild_id: str,
    *,
    traits_pool: list[dict],
    level: int = 1,
    is_starter: bool = False,
    extra: dict | None = None,
) -> dict:
    """Build a persisted test recruit without assigning a hidden class."""
    created_at = datetime.now(timezone.utc)
    adventurer = _generate_classless_candidate(
        guild_id,
        created_at,
        traits_pool=traits_pool,
        forced_rarity="Common",
    )
    adventurer.pop("expires_at", None)
    adventurer.update(
        {
            "level": level,
            "is_available": True,
            "is_retired": False,
            "retired": False,
            "archived": False,
            "frozen": False,
            "is_starter": is_starter,
            "is_test_artifact": True,
            "updated_at": created_at.isoformat(),
        }
    )
    if extra:
        adventurer.update(extra)
    return adventurer


def _active_roster_query(guild_id: str) -> dict:
    return {
        "guild_id": guild_id,
        "is_retired": {"$ne": True},
        "retired": {"$ne": True},
        "archived": {"$ne": True},
    }


def _assigned_through_canonical_hall(adventurer: dict) -> bool:
    hall_id = adventurer.get("class_hall_id")
    profile = CLASS_HALLS.get(hall_id)
    if not profile:
        return False
    return (
        adventurer.get("recruit_status") == "class_assigned"
        and adventurer.get("canonical_class_slug")
        == profile.canonical_class_slug
        and adventurer.get("class_slug") == profile.canonical_class_slug
        and bool(adventurer.get("adventurer_class_id"))
    )


def _check(
    key: str,
    label_it: str,
    *,
    ok: bool,
    current,
    target,
    blocking: bool = True,
    detail_it: str | None = None,
) -> dict:
    return {
        "key": key,
        "label_it": label_it,
        "ok": bool(ok),
        "current": current,
        "target": target,
        "blocking": blocking,
        "detail_it": detail_it,
    }


async def build_tester_smoke_matrix(db, *, user: dict, guild: dict | None) -> dict:
    """Return a read-only, player-facing readiness matrix."""
    profiles = list(CLASS_HALLS.values())
    canonical_slugs = [profile.canonical_class_slug for profile in profiles]
    class_docs = await db.adventurer_classes.find(
        {
            "slug": {"$in": canonical_slugs},
            "is_active": {"$ne": False},
            "is_playable": {"$ne": False},
        },
        {"_id": 0, "slug": 1},
    ).to_list(100)
    persisted_class_slugs = {row.get("slug") for row in class_docs}

    active_items = await db.items.find(
        {"is_active": {"$ne": False}, "is_test": {"$ne": True}},
        {
            "_id": 0,
            "id": 1,
            "slug": 1,
            "name": 1,
            "display_name_it": 1,
            "lore_reviewed": 1,
            "lore_source": 1,
            "flavor_text_it": 1,
            "source": 1,
            "acquisition_sources": 1,
            "acquisition_hint_it": 1,
            "acquisition_track_order": 1,
            "effect_metadata": 1,
            "item_type": 1,
            "slot_type": 1,
            "tags": 1,
            "weapon_tags": 1,
            "armor_tags": 1,
            "item_subtype": 1,
            "weapon_type": 1,
            "armor_type": 1,
            "build_path_id": 1,
        },
    ).to_list(5000)
    hall_items = [
        item
        for item in active_items
        if (item.get("source") or "").startswith("class_hall:")
    ]
    items_by_hall: dict[str, list[dict]] = {}
    for item in hall_items:
        hall_id = item["source"].split(":", 1)[1]
        items_by_hall.setdefault(hall_id, []).append(item)

    complete_tracks = 0
    for profile in profiles:
        track = items_by_hall.get(profile.hall_id, [])
        orders = sorted(item.get("acquisition_track_order") for item in track)
        if (
            len(track) == 5
            and orders == [0, 1, 2, 3, 4]
            and all(
                len(item.get("acquisition_sources") or []) == 1
                and bool(item.get("acquisition_hint_it"))
                for item in track
            )
        ):
            complete_tracks += 1

    normalized_ids = {
        str(item.get("id") or "").strip().casefold() for item in active_items
    }
    normalized_slugs = {
        str(item.get("slug") or "").strip().casefold() for item in active_items
    }
    normalized_names = {
        str(item.get("display_name_it") or item.get("name") or "")
        .strip()
        .casefold()
        for item in active_items
    }
    unique_items = (
        len(active_items)
        == len(normalized_ids)
        == len(normalized_slugs)
        == len(normalized_names)
        and "" not in normalized_ids
        and "" not in normalized_slugs
        and "" not in normalized_names
    )
    lore_complete = sum(
        bool(item.get("lore_reviewed") and item.get("lore_source"))
        for item in active_items
    )
    flavor_complete = sum(bool(item.get("flavor_text_it")) for item in active_items)
    effect_items = sum(
        bool(
            isinstance(item.get("effect_metadata"), dict)
            and item["effect_metadata"].get("enabled", True) is True
        )
        for item in hall_items
    )
    build_reachability = audit_class_hall_build_reachability(
        hall_items
    )

    active_roster: list[dict] = []
    if guild:
        active_roster = await db.adventurers.find(
            _active_roster_query(guild["id"]),
            {"_id": 0},
        ).to_list(500)
    classless_count = sum(
        is_explicit_classless_recruit(adventurer)
        for adventurer in active_roster
    )
    assigned_count = sum(
        _assigned_through_canonical_hall(adventurer)
        for adventurer in active_roster
    )
    invalid_count = len(active_roster) - classless_count - assigned_count
    available_count = sum(
        adventurer.get("is_available", True) is True
        for adventurer in active_roster
    )

    checks = [
        _check(
            "canonical_halls",
            "Class Hall canoniche",
            ok=len(profiles) == 27,
            current=len(profiles),
            target=27,
        ),
        _check(
            "playable_classes",
            "Classi giocabili persistite",
            ok=len(persisted_class_slugs) == 27,
            current=len(persisted_class_slugs),
            target=27,
        ),
        _check(
            "hall_item_tracks",
            "Sentieri oggetti completi (5 per classe)",
            ok=complete_tracks == 27 and len(hall_items) == 135,
            current=f"{complete_tracks}/27 · {len(hall_items)} oggetti",
            target="27/27 · 135 oggetti",
        ),
        _check(
            "hall_signature_effects",
            "Item-firma con effetto runtime",
            ok=effect_items == 27,
            current=effect_items,
            target=27,
        ),
        _check(
            "hall_build_reachability",
            "Build attivabili dagli item delle Class Hall",
            ok=build_reachability["all_builds_reachable"],
            current=(
                f"{build_reachability['reachable_build_count']}/81 "
                "raggiungibili · "
                f"{build_reachability['exact_declared_build_count']}/81 "
                "dichiarate"
            ),
            target="81/81 raggiungibili e dichiarate",
            detail_it=(
                "Ogni build deve avere esattamente un item Hall che la "
                "attiva realmente."
            ),
        ),
        _check(
            "singular_active_items",
            "Oggetti attivi singolari",
            ok=unique_items,
            current=len(active_items),
            target="nessun ID, slug o nome duplicato",
        ),
        _check(
            "lore_reviewed",
            "Oggetti con lore revisionata e fonte",
            ok=lore_complete == len(active_items) and bool(active_items),
            current=f"{lore_complete}/{len(active_items)}",
            target="100%",
        ),
        _check(
            "flavor_coverage",
            "Copertura testo narrativo",
            ok=(
                bool(active_items)
                and flavor_complete / len(active_items) >= 0.80
            ),
            current=f"{flavor_complete}/{len(active_items)}",
            target="almeno 80%",
        ),
        _check(
            "tester_guild",
            "Gilda tester disponibile",
            ok=guild is not None,
            current=guild.get("name") if guild else "assente",
            target="presente",
        ),
        _check(
            "tester_roster",
            "Roster attivo sufficiente",
            ok=len(active_roster) >= STARTER_TESTER_ROSTER_SIZE,
            current=len(active_roster),
            target=f">={STARTER_TESTER_ROSTER_SIZE}",
        ),
        _check(
            "roster_class_state",
            "Roster senza classi implicite o legacy",
            ok=invalid_count == 0,
            current=(
                f"{classless_count} senza classe · "
                f"{assigned_count} assegnati · {invalid_count} invalidi"
            ),
            target="0 stati invalidi",
        ),
        _check(
            "roster_available",
            "Avventurieri liberi per la prova",
            ok=available_count >= min(
                STARTER_TESTER_ROSTER_SIZE,
                len(active_roster),
            ),
            current=available_count,
            target=f">={STARTER_TESTER_ROSTER_SIZE}",
        ),
        _check(
            "long_term_item_catalog",
            "Obiettivo catalogo globale",
            ok=len(active_items) >= LONG_TERM_ITEM_TARGET,
            current=len(active_items),
            target=LONG_TERM_ITEM_TARGET,
            blocking=False,
            detail_it=(
                "Obiettivo di crescita della roadmap: non blocca la slice "
                "giocabile per i tester."
            ),
        ),
    ]
    blocking_checks = [check for check in checks if check["blocking"]]
    return {
        "target_user": {
            "id": user.get("id"),
            "email": user.get("email"),
        },
        "guild_id": guild.get("id") if guild else None,
        "ready_for_tester_slice": all(check["ok"] for check in blocking_checks),
        "blocking_failures": [
            check["key"] for check in blocking_checks if not check["ok"]
        ],
        "checks": checks,
        "summary": {
            "active_items": len(active_items),
            "lore_complete": lore_complete,
            "flavor_complete": flavor_complete,
            "classless_adventurers": classless_count,
            "assigned_adventurers": assigned_count,
            "invalid_class_states": invalid_count,
            "reachable_hall_builds": build_reachability[
                "reachable_build_count"
            ],
        },
    }


def _resonant_build_id(snapshot: dict | None) -> str | None:
    active_build = (snapshot or {}).get("active_build") or {}
    if active_build.get("resonance_active") is not True:
        return None
    build_id = str(active_build.get("build_id") or "").strip()
    return build_id or None


def _activity_timestamp(row: dict) -> str:
    """Return a UTC timestamp whose lexical order is chronological.

    Mongo fixtures and legacy rows may mix ``Z``, explicit offsets and native
    datetimes. Comparing those raw strings can credit a post-raid build that
    actually happened before the raid.
    """
    for field in ("completed_at", "started_at", "created_at"):
        raw = row.get(field)
        if not raw:
            continue
        try:
            if isinstance(raw, datetime):
                parsed = raw
            else:
                parsed = datetime.fromisoformat(
                    str(raw).strip().replace("Z", "+00:00")
                )
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).isoformat(
                timespec="microseconds"
            )
        except (TypeError, ValueError):
            continue
    return ""


def _slice_step(
    key: str,
    *,
    completed: bool,
    evidence: dict | None = None,
) -> dict:
    label_it = dict(VERTICAL_SLICE_STEPS)[key]
    return {
        "key": key,
        "label_it": label_it,
        "completed": bool(completed),
        "evidence": evidence,
    }


def _compile_wave_coverage(
    *,
    adventurers: list[dict],
    journey_rows: list[dict],
    activities_by_adventurer: dict[str, list[dict]],
) -> dict:
    profiles_by_slug = {
        profile.canonical_class_slug: profile
        for profile in CLASS_HALLS.values()
    }
    journey_by_adventurer = {
        row["adventurer_id"]: row for row in journey_rows
    }
    adventurers_by_class: dict[str, list[dict]] = {}
    for adventurer in adventurers:
        class_slug = adventurer.get("canonical_class_slug")
        if class_slug in CLASS_MECHANICS:
            adventurers_by_class.setdefault(class_slug, []).append(adventurer)

    classes: list[dict] = []
    for class_slug, mechanic in CLASS_MECHANICS.items():
        class_adventurers = adventurers_by_class.get(class_slug, [])
        observed_build_ids = {
            activity["build_id"]
            for adventurer in class_adventurers
            for activity in activities_by_adventurer.get(
                adventurer.get("id"), []
            )
            if activity.get("build_id")
        }
        completed_journeys = sum(
            bool(
                journey_by_adventurer.get(
                    adventurer.get("id"), {}
                ).get("journey_completed")
            )
            for adventurer in class_adventurers
        )
        expected_build_ids = {
            build.build_id for build in mechanic.builds
        }
        observed_expected = observed_build_ids.intersection(
            expected_build_ids
        )
        profile = profiles_by_slug.get(class_slug)
        classes.append(
            {
                "class_slug": class_slug,
                "class_name_it": (
                    profile.class_name_it if profile else class_slug
                ),
                "wave": mechanic.wave,
                "active_adventurers": len(class_adventurers),
                "completed_journeys": completed_journeys,
                "observed_build_count": len(observed_expected),
                "expected_build_count": len(mechanic.builds),
                "builds": [
                    {
                        "build_id": build.build_id,
                        "name_it": build.name_it,
                        "observed": build.build_id in observed_build_ids,
                    }
                    for build in mechanic.builds
                ],
                "ready_for_tuning": (
                    completed_journeys > 0
                    and observed_expected == expected_build_ids
                ),
            }
        )

    waves = []
    for wave in ("A", "B", "C", "D", "E"):
        wave_classes = [
            row for row in classes if row["wave"] == wave
        ]
        expected_builds = sum(
            row["expected_build_count"] for row in wave_classes
        )
        observed_builds = sum(
            row["observed_build_count"] for row in wave_classes
        )
        journey_classes = sum(
            row["completed_journeys"] > 0 for row in wave_classes
        )
        tuning_ready_classes = sum(
            row["ready_for_tuning"] for row in wave_classes
        )
        waves.append(
            {
                "wave": wave,
                "class_count": len(wave_classes),
                "journey_class_count": journey_classes,
                "observed_build_count": observed_builds,
                "expected_build_count": expected_builds,
                "tuning_ready_class_count": tuning_ready_classes,
                "minimum_slice_ready": journey_classes > 0,
                "full_coverage_ready": (
                    tuning_ready_classes == len(wave_classes)
                    and bool(wave_classes)
                ),
            }
        )

    classes.sort(
        key=lambda row: (
            row["ready_for_tuning"],
            row["completed_journeys"] > 0,
            row["observed_build_count"],
            row["wave"],
            row["class_name_it"],
        )
    )
    total_observed_builds = sum(
        row["observed_build_count"] for row in classes
    )
    tuning_ready_classes = sum(
        row["ready_for_tuning"] for row in classes
    )
    return {
        "minimum_wave_slice_ready": all(
            row["minimum_slice_ready"] for row in waves
        ),
        "full_class_build_coverage_ready": (
            tuning_ready_classes == len(CLASS_MECHANICS)
            and total_observed_builds == sum(
                len(mechanic.builds)
                for mechanic in CLASS_MECHANICS.values()
            )
        ),
        "class_count": len(CLASS_MECHANICS),
        "expected_build_count": sum(
            len(mechanic.builds)
            for mechanic in CLASS_MECHANICS.values()
        ),
        "observed_build_count": total_observed_builds,
        "tuning_ready_class_count": tuning_ready_classes,
        "waves": waves,
        "classes": classes,
        "priority_queue": [
            {
                "class_slug": row["class_slug"],
                "class_name_it": row["class_name_it"],
                "wave": row["wave"],
                "completed_journeys": row["completed_journeys"],
                "observed_build_count": row["observed_build_count"],
                "expected_build_count": row["expected_build_count"],
                "missing_build_ids": [
                    build["build_id"]
                    for build in row["builds"]
                    if not build["observed"]
                ],
            }
            for row in classes
            if not row["ready_for_tuning"]
        ],
    }


def _average(total: int, count: int) -> float | None:
    return round(total / count, 2) if count else None


def _rate(successes: int, known_outcomes: int) -> float | None:
    return round(successes / known_outcomes, 3) if known_outcomes else None


def _power_context(team_power, recommended_power) -> dict:
    team = int(team_power or 0)
    recommended = int(recommended_power or 0)
    if team <= 0 or recommended <= 0:
        return {"bucket": "unknown", "ratio": None}
    ratio = round(team / recommended, 3)
    if ratio < COMPARABLE_POWER_RATIO_MIN:
        bucket = "underpowered"
    elif ratio > COMPARABLE_POWER_RATIO_MAX:
        bucket = "overpowered"
    else:
        bucket = "matched"
    return {"bucket": bucket, "ratio": ratio}


def _team_fingerprint(adventurer_ids: list[str]) -> str:
    stable_ids = sorted(
        {str(value) for value in adventurer_ids if value}
    )
    payload = "|".join(stable_ids).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def _comparison_cohort(
    *,
    kind: str,
    encounter_key: str,
    adventurer_ids: list[str],
) -> dict:
    team_ids = sorted(
        {str(value) for value in adventurer_ids if value}
    )
    fingerprint = _team_fingerprint(team_ids)
    return {
        "key": f"{kind}:{encounter_key}:{fingerprint}",
        "kind": kind,
        "encounter_key": encounter_key,
        "team_size": len(team_ids),
        "team_fingerprint": fingerprint,
    }


def _component_delta(value: float | None, baseline: float | None) -> dict:
    if value is None or baseline in (None, 0):
        return {"value": None, "percent": None}
    delta = round(value - baseline, 2)
    return {
        "value": delta,
        "percent": round(delta / baseline, 3),
    }


def _spread(values: list[float | None], baseline: float | None) -> dict:
    if not values or baseline in (None, 0) or any(
        value is None for value in values
    ):
        return {"absolute": None, "ratio": None}
    absolute = round(max(values) - min(values), 3)
    return {
        "absolute": absolute,
        "ratio": round(absolute / baseline, 3),
    }


def _component_extremes(rows: list[dict], key: str) -> dict | None:
    candidates = [
        (
            row["controlled_comparison"]["power"].get(key),
            row["build_id"],
            row["build_name_it"],
        )
        for row in rows
        if row["controlled_comparison"]["power"].get(key) is not None
    ]
    if not candidates:
        return None
    lowest = min(candidates, key=lambda value: value[0])
    highest = max(candidates, key=lambda value: value[0])
    return {
        "lowest": {
            "build_id": lowest[1],
            "build_name_it": lowest[2],
            "value": lowest[0],
        },
        "highest": {
            "build_id": highest[1],
            "build_name_it": highest[2],
            "value": highest[0],
        },
    }


def _manual_review_decision(
    *,
    spreads: dict,
    reasons: list[str],
    replicated: bool,
) -> dict:
    equipment_flag = (
        spreads["equipment"]["ratio"] is not None
        and spreads["equipment"]["ratio"] >= 0.05
    )
    item_flag = (
        spreads["item_effect"]["ratio"] is not None
        and spreads["item_effect"]["ratio"] >= 0.05
    )
    resonance_flag = (
        spreads["class_resonance"]["ratio"] is not None
        and spreads["class_resonance"]["ratio"] >= 0.05
    )
    outcome_flag = (
        spreads["dungeon_outcome"]["absolute"] is not None
        and spreads["dungeon_outcome"]["absolute"] >= 0.20
    )
    item_owned = equipment_flag or item_flag
    replication_note = (
        " Il segnale è confermato da due coorti indipendenti."
        if replicated
        else " Richiedi una seconda coorte prima di modificare valori."
    )
    if item_owned and not resonance_flag:
        scope = "item"
        action_it = (
            "Confronta statistiche base ed effetto dei tre item; prepara "
            "soltanto una variazione manuale dell'item responsabile."
            f"{replication_note}"
        )
    elif resonance_flag and not item_owned:
        scope = "class_resonance"
        action_it = (
            "Ispeziona il moltiplicatore di risonanza della build; preserva "
            f"l'identità dell'item.{replication_note}"
        )
    elif outcome_flag and not item_owned and not resonance_flag:
        scope = "encounter"
        action_it = (
            "Rivedi minacce e probabilità base dell'incontro prima di "
            f"toccare item o classe.{replication_note}"
        )
    else:
        scope = "mixed"
        action_it = (
            "Separa con una seconda coorte item, risonanza e incontro; "
            "non applicare correzioni finché il responsabile non è isolato."
            f"{replication_note}"
        )

    score = min(
        100,
        round(
            float(spreads["total"]["ratio"] or 0) * 200
            + float(spreads["equipment"]["ratio"] or 0) * 150
            + float(spreads["item_effect"]["ratio"] or 0) * 200
            + float(spreads["class_resonance"]["ratio"] or 0) * 200
            + float(spreads["dungeon_outcome"]["absolute"] or 0) * 50
        ),
    )
    if score >= 70:
        severity = "critical"
    elif score >= 50:
        severity = "high"
    elif score >= 30:
        severity = "medium"
    else:
        severity = "low"
    return {
        "severity_score": score,
        "severity": severity,
        "recommended_scope": scope,
        "manual_action_it": action_it,
        "automatic_change_allowed": False,
        "evidence_count": len(reasons),
    }


def _compile_controlled_comparisons(
    *,
    builds: list[dict],
    cohort_metrics_by_build: dict[tuple[str, str], dict],
) -> dict:
    """Compare the three builds only inside shared encounter/team cohorts."""
    class_rows: list[dict] = []
    review_queue: list[dict] = []
    preliminary_review_queue: list[dict] = []
    controlled_ready_build_count = 0
    replicated_ready_build_count = 0

    for class_slug, mechanic in CLASS_MECHANICS.items():
        rows = [
            row for row in builds if row["class_slug"] == class_slug
        ]
        cohort_maps = [
            cohort_metrics_by_build.get(
                (class_slug, build.build_id), {}
            )
            for build in mechanic.builds
        ]
        shared_keys = set(cohort_maps[0]) if cohort_maps else set()
        for cohort_map in cohort_maps[1:]:
            shared_keys.intersection_update(cohort_map)
        controlled_keys = {
            key
            for key in shared_keys
            if all(
                int(cohort_map[key]["samples"])
                >= MIN_TUNING_SAMPLES_PER_BUILD
                for cohort_map in cohort_maps
            )
        }
        independent_team_fingerprints = sorted(
            {
                str(cohort_maps[0][key].get("team_fingerprint"))
                for key in controlled_keys
                if cohort_maps
                and cohort_maps[0][key].get("team_fingerprint")
            }
        )

        controlled_by_build: dict[str, dict] = {}
        for row in rows:
            cohorts = cohort_metrics_by_build.get(
                (class_slug, row["build_id"]), {}
            )
            selected = [
                cohorts[key] for key in controlled_keys
                if key in cohorts
            ]
            samples = sum(int(value["samples"]) for value in selected)
            power_samples = sum(
                int(value["power_sample_count"]) for value in selected
            )
            dungeon_known = sum(
                int(value["dungeon_known_outcomes"]) for value in selected
            )
            dungeon_successes = sum(
                int(value["dungeon_successes"]) for value in selected
            )
            raid_known = sum(
                int(value["raid_known_outcomes"]) for value in selected
            )
            raid_survivals = sum(
                int(value["raid_survivals"]) for value in selected
            )
            comparison = {
                "ready": (
                    samples >= MIN_TUNING_SAMPLES_PER_BUILD
                    and bool(controlled_keys)
                ),
                "replicated_ready": (
                    samples
                    >= (
                        MIN_TUNING_SAMPLES_PER_BUILD
                        * MIN_REPLICATED_COHORTS_PER_BUILD
                    )
                    and len(independent_team_fingerprints)
                    >= MIN_REPLICATED_COHORTS_PER_BUILD
                ),
                "samples": samples,
                "cohort_count": len(controlled_keys),
                "independent_team_count": len(
                    independent_team_fingerprints
                ),
                "encounters": sorted(
                    {
                        value["encounter_key"]
                        for value in selected
                    }
                ),
                "team_sizes": sorted(
                    {int(value["team_size"]) for value in selected}
                ),
                "average_team_power_ratio": _average(
                    sum(
                        int(round(value["power_ratio_total"] * 1000))
                        for value in selected
                    ),
                    samples,
                ),
                "dungeon_success_rate": _rate(
                    dungeon_successes, dungeon_known
                ),
                "raid_survival_rate": _rate(
                    raid_survivals, raid_known
                ),
                "power": {
                    "average_total": _average(
                        sum(value["total_power"] for value in selected),
                        power_samples,
                    ),
                    "average_equipment": _average(
                        sum(
                            value["equipment_power"]
                            for value in selected
                        ),
                        power_samples,
                    ),
                    "average_item_effect": _average(
                        sum(
                            value["item_effect_power"]
                            for value in selected
                        ),
                        power_samples,
                    ),
                    "average_class_resonance": _average(
                        sum(
                            value["class_resonance_power"]
                            for value in selected
                        ),
                        power_samples,
                    ),
                },
            }
            if comparison["average_team_power_ratio"] is not None:
                comparison["average_team_power_ratio"] = round(
                    comparison["average_team_power_ratio"] / 1000,
                    3,
                )
            row["controlled_comparison"] = comparison
            controlled_by_build[row["build_id"]] = comparison
            controlled_ready_build_count += int(comparison["ready"])
            replicated_ready_build_count += int(
                comparison["replicated_ready"]
            )

        component_keys = (
            "average_total",
            "average_equipment",
            "average_item_effect",
            "average_class_resonance",
        )
        baselines = {}
        for key in component_keys:
            values = [
                comparison["power"][key]
                for comparison in controlled_by_build.values()
                if comparison["power"][key] is not None
            ]
            baselines[key] = (
                round(sum(values) / len(values), 2) if values else None
            )
        for row in rows:
            comparison = row["controlled_comparison"]
            comparison["delta_from_class_average"] = {
                key: _component_delta(
                    comparison["power"][key],
                    baselines[key],
                )
                for key in component_keys
            }

        ready = (
            len(rows) == len(mechanic.builds)
            and all(
                row["controlled_comparison"]["ready"] for row in rows
            )
        )
        replicated_ready = (
            ready
            and all(
                row["controlled_comparison"]["replicated_ready"]
                for row in rows
            )
        )
        total_values = [
            row["controlled_comparison"]["power"]["average_total"]
            for row in rows
        ]
        item_values = [
            row["controlled_comparison"]["power"]["average_item_effect"]
            for row in rows
        ]
        resonance_values = [
            row["controlled_comparison"]["power"][
                "average_class_resonance"
            ]
            for row in rows
        ]
        dungeon_rates = [
            row["controlled_comparison"]["dungeon_success_rate"]
            for row in rows
        ]
        reasons = []
        total_baseline = baselines["average_total"]
        equipment_values = [
            row["controlled_comparison"]["power"]["average_equipment"]
            for row in rows
        ]
        spreads = {
            "total": _spread(total_values, total_baseline),
            "equipment": _spread(
                equipment_values,
                baselines["average_equipment"],
            ),
            "item_effect": _spread(
                item_values,
                baselines["average_item_effect"],
            ),
            "class_resonance": _spread(
                resonance_values,
                baselines["average_class_resonance"],
            ),
            "dungeon_outcome": {
                "absolute": (
                    round(max(dungeon_rates) - min(dungeon_rates), 3)
                    if dungeon_rates
                    and all(value is not None for value in dungeon_rates)
                    else None
                ),
                "ratio": None,
            },
        }
        if (
            ready
            and spreads["total"]["ratio"] is not None
            and spreads["total"]["ratio"] >= 0.10
        ):
            reasons.append("controlled_total_power_spread")
        if (
            ready
            and spreads["equipment"]["ratio"] is not None
            and spreads["equipment"]["ratio"] >= 0.05
        ):
            reasons.append("controlled_equipment_spread")
        if (
            ready
            and spreads["item_effect"]["ratio"] is not None
            and spreads["item_effect"]["ratio"] >= 0.05
        ):
            reasons.append("controlled_item_effect_spread")
        if (
            ready
            and spreads["class_resonance"]["ratio"] is not None
            and spreads["class_resonance"]["ratio"] >= 0.05
        ):
            reasons.append("controlled_class_resonance_spread")
        if (
            ready
            and spreads["dungeon_outcome"]["absolute"] is not None
            and spreads["dungeon_outcome"]["absolute"] >= 0.20
        ):
            reasons.append("controlled_dungeon_outcome_spread")

        class_name_it = rows[0]["class_name_it"] if rows else class_slug
        review_decision = (
            _manual_review_decision(
                spreads=spreads,
                reasons=reasons,
                replicated=replicated_ready,
            )
            if reasons
            else {
                "severity_score": 0,
                "severity": "none",
                "recommended_scope": "none",
                "manual_action_it": (
                    (
                        "Mantieni i valori: due coorti indipendenti non "
                        "mostrano un divario che richieda intervento."
                    )
                    if replicated_ready
                    else (
                        "Mantieni i valori e raccogli una seconda coorte "
                        "prima di qualsiasi modifica."
                    )
                ),
                "automatic_change_allowed": False,
                "evidence_count": 0,
            }
        )
        confirmed_reasons = reasons if replicated_ready else []
        preliminary_reasons = reasons if not replicated_ready else []
        summary = {
            "class_slug": class_slug,
            "class_name_it": class_name_it,
            "wave": mechanic.wave,
            "ready": ready,
            "replicated_ready": replicated_ready,
            "controlled_cohort_count": len(controlled_keys),
            "controlled_independent_team_count": len(
                independent_team_fingerprints
            ),
            "controlled_samples": sum(
                row["controlled_comparison"]["samples"] for row in rows
            ),
            "class_power_baseline": baselines,
            "review_required": bool(confirmed_reasons),
            "review_reasons": confirmed_reasons,
            "preliminary_review_detected": bool(preliminary_reasons),
            "preliminary_review_reasons": preliminary_reasons,
            "controlled_spreads": spreads,
            "component_extremes": {
                key: _component_extremes(rows, key)
                for key in component_keys
            },
            **review_decision,
            "decision": (
                "inspect_components"
                if confirmed_reasons
                else (
                    "collect_replication"
                    if preliminary_reasons
                    else (
                        "hold_no_change"
                        if replicated_ready
                        else "collect_controlled_data"
                    )
                )
            ),
        }
        class_rows.append(summary)
        if confirmed_reasons:
            review_queue.append(summary)
        elif preliminary_reasons:
            preliminary_review_queue.append(summary)

    review_queue.sort(
        key=lambda row: (
            -row["severity_score"],
            row["wave"],
            row["class_name_it"],
        )
    )
    export_payload = {
        "schema_version": "t5.manual-tuning.v1",
        "gate": {
            "minimum_samples_per_build_per_cohort": (
                MIN_TUNING_SAMPLES_PER_BUILD
            ),
            "minimum_replicated_cohorts": (
                MIN_REPLICATED_COHORTS_PER_BUILD
            ),
            "ready_class_count": sum(
                row["replicated_ready"] for row in class_rows
            ),
            "expected_class_count": len(CLASS_MECHANICS),
            "ready_build_count": replicated_ready_build_count,
            "expected_build_count": sum(
                len(mechanic.builds)
                for mechanic in CLASS_MECHANICS.values()
            ),
        },
        "proposals": [
            {
                "class_slug": row["class_slug"],
                "class_name_it": row["class_name_it"],
                "wave": row["wave"],
                "severity_score": row["severity_score"],
                "severity": row["severity"],
                "recommended_scope": row["recommended_scope"],
                "manual_action_it": row["manual_action_it"],
                "review_reasons": row["review_reasons"],
                "controlled_spreads": row["controlled_spreads"],
                "component_extremes": row["component_extremes"],
                "automatic_change_allowed": False,
            }
            for row in review_queue
        ],
        "holds": [
            {
                "class_slug": row["class_slug"],
                "class_name_it": row["class_name_it"],
                "wave": row["wave"],
                "decision": row["decision"],
                "manual_action_it": row["manual_action_it"],
                "preliminary_review_reasons": (
                    row["preliminary_review_reasons"]
                ),
                "automatic_change_allowed": False,
            }
            for row in class_rows
            if not row["review_required"]
        ],
    }
    serialized_export = json.dumps(
        export_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "methodology_it": (
            "Confronta le tre build di una classe soltanto nello stesso "
            "incontro e con la stessa squadra; la conferma richiede due "
            "squadre indipendenti. I delta separano potenza totale, "
            "equipaggiamento, effetto item e risonanza rispetto alla media "
            "della classe. Nessun valore viene modificato automaticamente."
        ),
        "ready_class_count": sum(row["ready"] for row in class_rows),
        "expected_class_count": len(CLASS_MECHANICS),
        "ready_build_count": controlled_ready_build_count,
        "minimum_replicated_cohorts": MIN_REPLICATED_COHORTS_PER_BUILD,
        "replicated_ready_class_count": sum(
            row["replicated_ready"] for row in class_rows
        ),
        "replicated_ready_build_count": replicated_ready_build_count,
        "expected_build_count": sum(
            len(mechanic.builds)
            for mechanic in CLASS_MECHANICS.values()
        ),
        "comparison_ready": (
            controlled_ready_build_count
            == sum(
                len(mechanic.builds)
                for mechanic in CLASS_MECHANICS.values()
            )
        ),
        "replication_ready": (
            replicated_ready_build_count
            == sum(
                len(mechanic.builds)
                for mechanic in CLASS_MECHANICS.values()
            )
        ),
        "review_class_count": len(review_queue),
        "preliminary_review_class_count": len(preliminary_review_queue),
        "classes": class_rows,
        "review_queue": review_queue,
        "preliminary_review_queue": preliminary_review_queue,
        "export_bundle": {
            "schema_version": export_payload["schema_version"],
            "sha256": hashlib.sha256(serialized_export).hexdigest(),
            "canonical_json": serialized_export.decode("utf-8"),
            "payload": export_payload,
        },
    }


def _compile_balance_telemetry(
    *,
    adventurers: list[dict],
    activities_by_adventurer: dict[str, list[dict]],
) -> dict:
    accumulators: dict[tuple[str, str], dict] = {}
    for class_slug, mechanic in CLASS_MECHANICS.items():
        for build in mechanic.builds:
            accumulators[(class_slug, build.build_id)] = {
                "samples": 0,
                "comparable_samples": 0,
                "underpowered_samples": 0,
                "matched_samples": 0,
                "overpowered_samples": 0,
                "unknown_context_samples": 0,
                "dungeon_samples": 0,
                "dungeon_known_outcomes": 0,
                "dungeon_successes": 0,
                "raid_samples": 0,
                "raid_known_outcomes": 0,
                "raid_survivals": 0,
                "power_sample_count": 0,
                "total_power": 0,
                "equipment_power": 0,
                "item_effect_power": 0,
                "class_resonance_power": 0,
                "cohorts": {},
            }

    for adventurer in adventurers:
        class_slug = adventurer.get("canonical_class_slug")
        mechanic = CLASS_MECHANICS.get(class_slug)
        if not mechanic:
            continue
        canonical_build_ids = {
            build.build_id for build in mechanic.builds
        }
        for activity in activities_by_adventurer.get(
            adventurer.get("id"), []
        ):
            build_id = activity.get("build_id")
            if build_id not in canonical_build_ids:
                continue
            metrics = accumulators[(class_slug, build_id)]
            metrics["samples"] += 1
            power_bucket = activity.get("power_context", {}).get(
                "bucket", "unknown"
            )
            context_key = {
                "underpowered": "underpowered_samples",
                "matched": "matched_samples",
                "overpowered": "overpowered_samples",
            }.get(power_bucket, "unknown_context_samples")
            metrics[context_key] += 1
            comparable = power_bucket == "matched"
            metrics["comparable_samples"] += int(comparable)
            cohort = activity.get("comparison_cohort") or {}
            cohort_key = cohort.get("key")
            if comparable and cohort_key:
                cohort_metrics = metrics["cohorts"].setdefault(
                    cohort_key,
                    {
                        **cohort,
                        "samples": 0,
                        "power_ratio_total": 0.0,
                        "dungeon_known_outcomes": 0,
                        "dungeon_successes": 0,
                        "raid_known_outcomes": 0,
                        "raid_survivals": 0,
                        "power_sample_count": 0,
                        "total_power": 0,
                        "equipment_power": 0,
                        "item_effect_power": 0,
                        "class_resonance_power": 0,
                    },
                )
                cohort_metrics["samples"] += 1
                cohort_metrics["power_ratio_total"] += float(
                    activity.get("power_context", {}).get("ratio") or 0
                )
            if activity["kind"] == "dungeon":
                metrics["dungeon_samples"] += 1
                if comparable and activity.get("outcome_known"):
                    metrics["dungeon_known_outcomes"] += 1
                    metrics["dungeon_successes"] += int(
                        activity.get("success") is True
                    )
                    if cohort_key:
                        cohort_metrics["dungeon_known_outcomes"] += 1
                        cohort_metrics["dungeon_successes"] += int(
                            activity.get("success") is True
                        )
            else:
                metrics["raid_samples"] += 1
                if comparable and activity.get("participant_outcome") in {
                    "survived",
                    "fainted",
                }:
                    metrics["raid_known_outcomes"] += 1
                    metrics["raid_survivals"] += int(
                        activity.get("participant_outcome") == "survived"
                    )
                    if cohort_key:
                        cohort_metrics["raid_known_outcomes"] += 1
                        cohort_metrics["raid_survivals"] += int(
                            activity.get("participant_outcome") == "survived"
                        )
            total_power = int(activity.get("total_power_snapshot") or 0)
            if total_power > 0:
                metrics["power_sample_count"] += 1
                metrics["total_power"] += total_power
                metrics["equipment_power"] += int(
                    activity.get("equipment_power_snapshot") or 0
                )
                metrics["item_effect_power"] += int(
                    activity.get("item_effect_power_bonus") or 0
                )
                metrics["class_resonance_power"] += int(
                    activity.get("class_item_resonance_bonus") or 0
                )
                if comparable and cohort_key:
                    cohort_metrics["power_sample_count"] += 1
                    cohort_metrics["total_power"] += total_power
                    cohort_metrics["equipment_power"] += int(
                        activity.get("equipment_power_snapshot") or 0
                    )
                    cohort_metrics["item_effect_power"] += int(
                        activity.get("item_effect_power_bonus") or 0
                    )
                    cohort_metrics["class_resonance_power"] += int(
                        activity.get("class_item_resonance_bonus") or 0
                    )

    profiles_by_slug = {
        profile.canonical_class_slug: profile
        for profile in CLASS_HALLS.values()
    }
    builds: list[dict] = []
    for class_slug, mechanic in CLASS_MECHANICS.items():
        profile = profiles_by_slug.get(class_slug)
        for build in mechanic.builds:
            raw = accumulators[(class_slug, build.build_id)]
            dungeon_rate = _rate(
                raw["dungeon_successes"],
                raw["dungeon_known_outcomes"],
            )
            raid_rate = _rate(
                raw["raid_survivals"],
                raw["raid_known_outcomes"],
            )
            sample_ready = (
                raw["comparable_samples"]
                >= MIN_TUNING_SAMPLES_PER_BUILD
            )
            review_signals = []
            if sample_ready and dungeon_rate is not None:
                if dungeon_rate <= 0.35:
                    review_signals.append("low_dungeon_success")
                elif dungeon_rate >= 0.85:
                    review_signals.append("high_dungeon_success")
            if sample_ready and raid_rate is not None:
                if raid_rate <= 0.35:
                    review_signals.append("low_raid_survival")
                elif raid_rate >= 0.85:
                    review_signals.append("high_raid_survival")
            if raw["samples"] == 0:
                status = "untested"
            elif not sample_ready:
                status = "insufficient_sample"
            elif review_signals:
                status = "review_signal"
            else:
                status = "sample_ready"
            builds.append(
                {
                    "class_slug": class_slug,
                    "class_name_it": (
                        profile.class_name_it if profile else class_slug
                    ),
                    "wave": mechanic.wave,
                    "build_id": build.build_id,
                    "build_name_it": build.name_it,
                    "status": status,
                    "sample_ready": sample_ready,
                    "samples": raw["samples"],
                    "comparable_samples": raw["comparable_samples"],
                    "samples_needed": max(
                        0,
                        MIN_TUNING_SAMPLES_PER_BUILD
                        - raw["comparable_samples"],
                    ),
                    "power_context": {
                        "underpowered": raw["underpowered_samples"],
                        "matched": raw["matched_samples"],
                        "overpowered": raw["overpowered_samples"],
                        "unknown": raw["unknown_context_samples"],
                    },
                    "dungeon": {
                        "samples": raw["dungeon_samples"],
                        "known_outcomes": raw["dungeon_known_outcomes"],
                        "successes": raw["dungeon_successes"],
                        "success_rate": dungeon_rate,
                    },
                    "raid": {
                        "samples": raw["raid_samples"],
                        "known_outcomes": raw["raid_known_outcomes"],
                        "survivals": raw["raid_survivals"],
                        "survival_rate": raid_rate,
                    },
                    "power": {
                        "sample_count": raw["power_sample_count"],
                        "average_total": _average(
                            raw["total_power"],
                            raw["power_sample_count"],
                        ),
                        "average_equipment": _average(
                            raw["equipment_power"],
                            raw["power_sample_count"],
                        ),
                        "average_item_effect": _average(
                            raw["item_effect_power"],
                            raw["power_sample_count"],
                        ),
                        "average_class_resonance": _average(
                            raw["class_resonance_power"],
                            raw["power_sample_count"],
                        ),
                    },
                    "review_signals": review_signals,
                }
            )

    builds.sort(
        key=lambda row: (
            row["sample_ready"],
            row["comparable_samples"],
            row["wave"],
            row["class_name_it"],
            row["build_name_it"],
        )
    )
    sample_ready_count = sum(row["sample_ready"] for row in builds)
    review_signal_count = sum(
        bool(row["review_signals"]) for row in builds
    )
    cohort_metrics_by_build = {
        key: value["cohorts"]
        for key, value in accumulators.items()
    }
    controlled = _compile_controlled_comparisons(
        builds=builds,
        cohort_metrics_by_build=cohort_metrics_by_build,
    )
    return {
        "minimum_samples_per_build": MIN_TUNING_SAMPLES_PER_BUILD,
        "comparison_ready": sample_ready_count == len(builds),
        "sample_ready_build_count": sample_ready_count,
        "expected_build_count": len(builds),
        "review_signal_count": review_signal_count,
        "total_activity_samples": sum(row["samples"] for row in builds),
        "total_comparable_samples": sum(
            row["comparable_samples"] for row in builds
        ),
        "comparable_power_ratio": {
            "minimum": COMPARABLE_POWER_RATIO_MIN,
            "maximum": COMPARABLE_POWER_RATIO_MAX,
        },
        "methodology_it": (
            "Readiness e segnali usano soltanto attività con potenza squadra "
            "tra l'80% e il 120% di quella consigliata. Gli altri campioni "
            "restano visibili ma non producono modifiche automatiche."
        ),
        "controlled": controlled,
        "builds": builds,
        "sample_priority_queue": [
            {
                "class_slug": row["class_slug"],
                "class_name_it": row["class_name_it"],
                "wave": row["wave"],
                "build_id": row["build_id"],
                "build_name_it": row["build_name_it"],
                "samples": row["samples"],
                "comparable_samples": row["comparable_samples"],
                "samples_needed": row["samples_needed"],
            }
            for row in builds
            if not row["sample_ready"]
        ],
        "review_queue": [
            {
                "class_slug": row["class_slug"],
                "class_name_it": row["class_name_it"],
                "wave": row["wave"],
                "build_id": row["build_id"],
                "build_name_it": row["build_name_it"],
                "review_signals": row["review_signals"],
                "dungeon_success_rate": row["dungeon"]["success_rate"],
                "raid_survival_rate": row["raid"]["survival_rate"],
            }
            for row in builds
            if row["review_signals"]
        ],
    }


def compile_tester_vertical_slice(
    *,
    user: dict,
    guild: dict | None,
    adventurers: list[dict],
    signature_items: list[dict],
    equipped_items: list[dict],
    expeditions: list[dict],
    expedition_members: list[dict],
    raids: list[dict],
    raid_participants: list[dict],
    raid_reward_grants: list[dict],
) -> dict:
    """Compile the read-only Hall → item → dungeon → raid → build journey.

    Activity snapshots are the source of truth.  The last milestone requires
    a resonant build different from the dungeon build in an activity completed
    after the rewarded raid, so a tester cannot satisfy the journey with a
    static loadout or with administrative state alone.
    """
    if not guild:
        return {
            "target_user": {
                "id": user.get("id"),
                "email": user.get("email"),
            },
            "guild_id": None,
            "ready_for_playtest": False,
            "t5_completion_ready": False,
            "t5_gate": {
                "journeys_ready": False,
                "class_build_coverage_ready": False,
                "sample_coverage_ready": False,
                "controlled_replication_ready": False,
            },
            "completed_journeys": 0,
            "bottleneck": {
                "key": "tester_guild",
                "label_it": "Crea una Gilda tester",
            },
            "telemetry": {
                "active_adventurers": 0,
                "completed_journeys": 0,
            },
            "adventurers": [],
        }

    signature_by_hall = {
        item.get("source", "").split(":", 1)[1]: item
        for item in signature_items
        if str(item.get("source") or "").startswith("class_hall:")
        and int(item.get("acquisition_track_order") or 0) == 0
    }
    equipped_by_adventurer: dict[str, set[str]] = {}
    for row in equipped_items:
        equipped_by_adventurer.setdefault(
            row.get("adventurer_id"), set()
        ).add(row.get("item_id"))

    expedition_by_id = {row.get("id"): row for row in expeditions}
    raid_by_id = {row.get("id"): row for row in raids}
    expedition_team_ids: dict[str, list[str]] = {}
    for member in expedition_members:
        expedition_team_ids.setdefault(
            member.get("expedition_id"), []
        ).append(member.get("adventurer_id"))
    raid_team_ids: dict[str, list[str]] = {}
    for participant in raid_participants:
        raid_team_ids.setdefault(
            participant.get("raid_id"), []
        ).append(participant.get("adventurer_id"))
    applied_grant_raid_ids = {
        row.get("raid_id")
        for row in raid_reward_grants
        if row.get("status") == "applied" and row.get("raid_id")
    }
    activities_by_adventurer: dict[str, list[dict]] = {}

    for member in expedition_members:
        expedition = expedition_by_id.get(member.get("expedition_id"))
        if not expedition:
            continue
        equipment_ids = {
            row.get("item_id")
            for row in member.get("equipment_snapshot") or []
            if row.get("item_id")
        }
        activities_by_adventurer.setdefault(
            member.get("adventurer_id"), []
        ).append(
            {
                "kind": "dungeon",
                "id": expedition.get("id"),
                "timestamp": _activity_timestamp(expedition),
                "build_id": _resonant_build_id(
                    member.get("class_mechanic_snapshot")
                ),
                "equipment_item_ids": equipment_ids,
                "outcome_known": expedition.get("result_summary") in {
                    "Success",
                    "Failed",
                },
                "success": expedition.get("result_summary") == "Success",
                "total_power_snapshot": member.get(
                    "total_power_snapshot"
                ),
                "equipment_power_snapshot": member.get(
                    "equipment_power_snapshot"
                ),
                "item_effect_power_bonus": member.get(
                    "item_effect_power_bonus"
                ),
                "class_item_resonance_bonus": member.get(
                    "class_item_resonance_bonus"
                ),
                "power_context": _power_context(
                    expedition.get("final_team_power")
                    or expedition.get("team_power"),
                    expedition.get("_tuning_recommended_power")
                    or expedition.get("recommended_power"),
                ),
                "comparison_cohort": _comparison_cohort(
                    kind="dungeon",
                    encounter_key=str(
                        expedition.get("_tuning_content_slug")
                        or expedition.get("dungeon_id")
                        or expedition.get("id")
                    ),
                    adventurer_ids=expedition_team_ids.get(
                        expedition.get("id"), []
                    ),
                ),
            }
        )

    for participant in raid_participants:
        raid = raid_by_id.get(participant.get("raid_id"))
        if not raid:
            continue
        activities_by_adventurer.setdefault(
            participant.get("adventurer_id"), []
        ).append(
            {
                "kind": "raid",
                "id": raid.get("id"),
                "timestamp": _activity_timestamp(raid),
                "build_id": _resonant_build_id(
                    participant.get("class_mechanic_snapshot")
                ),
                "reward_tracked": raid.get("id") in applied_grant_raid_ids,
                "raid_outcome": raid.get("outcome"),
                "participant_outcome": participant.get("outcome"),
                "total_power_snapshot": participant.get(
                    "total_power_snapshot"
                ),
                "equipment_power_snapshot": participant.get(
                    "equipment_power_snapshot"
                ),
                "item_effect_power_bonus": 0,
                "class_item_resonance_bonus": (
                    participant.get("class_mechanic_snapshot") or {}
                ).get("item_resonance_bonus"),
                "power_context": _power_context(
                    raid.get("team_power_combined"),
                    raid.get("recommended_power_combined"),
                ),
                "comparison_cohort": _comparison_cohort(
                    kind="raid",
                    encounter_key=str(
                        raid.get("raid_dungeon_slug")
                        or raid.get("id")
                    ),
                    adventurer_ids=raid_team_ids.get(
                        raid.get("id"), []
                    ),
                ),
            }
        )

    journey_rows: list[dict] = []
    telemetry_counts = {key: 0 for key, _label in VERTICAL_SLICE_STEPS}
    distinct_resonant_builds: set[tuple[str | None, str]] = set()

    for adventurer in adventurers:
        adventurer_id = adventurer.get("id")
        hall_chosen = _assigned_through_canonical_hall(adventurer)
        mechanic = CLASS_MECHANICS.get(
            adventurer.get("canonical_class_slug")
        )
        canonical_build_ids = {
            build.build_id for build in mechanic.builds
        } if mechanic else set()
        signature = signature_by_hall.get(adventurer.get("class_hall_id"))
        signature_id = signature.get("id") if signature else None
        activities = sorted(
            activities_by_adventurer.get(adventurer_id, []),
            key=lambda row: (row["timestamp"], row["kind"], row["id"] or ""),
        )
        signature_seen = bool(
            hall_chosen
            and signature_id
            and (
                signature_id in equipped_by_adventurer.get(adventurer_id, set())
                or any(
                    signature_id in row.get("equipment_item_ids", set())
                    for row in activities
                    if row["kind"] == "dungeon"
                )
            )
        )
        first_dungeon = next(
            (
                row
                for row in activities
                if row["kind"] == "dungeon"
                and row.get("build_id") in canonical_build_ids
            ),
            None,
        )
        resonant_dungeon = bool(signature_seen and first_dungeon)
        first_raid = next(
            (
                row
                for row in activities
                if resonant_dungeon
                and row["kind"] == "raid"
                and row["timestamp"] >= first_dungeon["timestamp"]
            ),
            None,
        )
        raid_completed = bool(resonant_dungeon and first_raid)
        reward_tracked = bool(
            raid_completed and first_raid.get("reward_tracked")
        )
        new_build_activity = next(
            (
                row
                for row in activities
                if reward_tracked
                and row["timestamp"] > first_raid["timestamp"]
                and row.get("build_id") in canonical_build_ids
                and row["build_id"] != first_dungeon["build_id"]
            ),
            None,
        )
        new_build_activated = bool(reward_tracked and new_build_activity)

        for row in activities:
            if row.get("build_id") in canonical_build_ids:
                distinct_resonant_builds.add(
                    (
                        adventurer.get("canonical_class_slug"),
                        row["build_id"],
                    )
                )

        steps = [
            _slice_step(
                "class_hall_chosen",
                completed=hall_chosen,
                evidence=(
                    {
                        "hall_id": adventurer.get("class_hall_id"),
                        "class_slug": adventurer.get("canonical_class_slug"),
                    }
                    if hall_chosen
                    else None
                ),
            ),
            _slice_step(
                "signature_item_equipped",
                completed=signature_seen,
                evidence=(
                    {
                        "item_id": signature_id,
                        "item_name_it": (
                            signature.get("display_name_it")
                            or signature.get("name")
                        ),
                    }
                    if signature_seen
                    else None
                ),
            ),
            _slice_step(
                "resonant_dungeon_completed",
                completed=resonant_dungeon,
                evidence=(
                    {
                        "expedition_id": first_dungeon["id"],
                        "completed_at": first_dungeon["timestamp"],
                        "build_id": first_dungeon["build_id"],
                    }
                    if resonant_dungeon
                    else None
                ),
            ),
            _slice_step(
                "raid_completed",
                completed=raid_completed,
                evidence=(
                    {
                        "raid_id": first_raid["id"],
                        "completed_at": first_raid["timestamp"],
                    }
                    if raid_completed
                    else None
                ),
            ),
            _slice_step(
                "raid_reward_tracked",
                completed=reward_tracked,
                evidence=(
                    {"raid_id": first_raid["id"], "status": "applied"}
                    if reward_tracked
                    else None
                ),
            ),
            _slice_step(
                "new_build_activated",
                completed=new_build_activated,
                evidence=(
                    {
                        "activity_type": new_build_activity["kind"],
                        "activity_id": new_build_activity["id"],
                        "completed_at": new_build_activity["timestamp"],
                        "previous_build_id": first_dungeon["build_id"],
                        "new_build_id": new_build_activity["build_id"],
                    }
                    if new_build_activated
                    else None
                ),
            ),
        ]
        for step in steps:
            if step["completed"]:
                telemetry_counts[step["key"]] += 1
        completed_steps = sum(step["completed"] for step in steps)
        next_step = next(
            (step for step in steps if not step["completed"]),
            None,
        )
        journey_rows.append(
            {
                "adventurer_id": adventurer_id,
                "name": adventurer.get("name"),
                "level": int(adventurer.get("level") or 1),
                "class_slug": adventurer.get("canonical_class_slug"),
                "completed_steps": completed_steps,
                "total_steps": len(VERTICAL_SLICE_STEPS),
                "journey_completed": completed_steps == len(VERTICAL_SLICE_STEPS),
                "next_step": (
                    {
                        "key": next_step["key"],
                        "label_it": next_step["label_it"],
                    }
                    if next_step
                    else None
                ),
                "steps": steps,
            }
        )

    journey_rows.sort(
        key=lambda row: (-row["completed_steps"], row.get("name") or "")
    )
    completed_journeys = sum(
        row["journey_completed"] for row in journey_rows
    )
    coverage = _compile_wave_coverage(
        adventurers=adventurers,
        journey_rows=journey_rows,
        activities_by_adventurer=activities_by_adventurer,
    )
    balance = _compile_balance_telemetry(
        adventurers=adventurers,
        activities_by_adventurer=activities_by_adventurer,
    )
    lead = journey_rows[0] if journey_rows else None
    bottleneck = (
        lead.get("next_step")
        if lead and lead.get("next_step")
        else (
            None
            if completed_journeys
            else {
                "key": "active_roster",
                "label_it": "Crea avventurieri attivi",
            }
        )
    )
    t5_gate = {
        "journeys_ready": completed_journeys >= len(CLASS_MECHANICS),
        "class_build_coverage_ready": bool(
            coverage["full_class_build_coverage_ready"]
        ),
        "sample_coverage_ready": bool(balance["comparison_ready"]),
        "controlled_replication_ready": bool(
            balance["controlled"]["replication_ready"]
        ),
    }
    t5_completion_ready = all(t5_gate.values())
    if not t5_gate["journeys_ready"]:
        t5_bottleneck = {
            "key": "all_class_journeys",
            "label_it": (
                "Completa i viaggi item-first di tutte le classi "
                f"({completed_journeys}/{len(CLASS_MECHANICS)})"
            ),
        }
    elif not t5_gate["class_build_coverage_ready"]:
        t5_bottleneck = {
            "key": "all_class_builds",
            "label_it": (
                "Osserva tutte le tre build canoniche di ogni classe"
            ),
        }
    elif not t5_gate["sample_coverage_ready"]:
        t5_bottleneck = {
            "key": "comparable_samples",
            "label_it": (
                "Raccogli almeno cinque campioni comparabili per build"
            ),
        }
    elif not t5_gate["controlled_replication_ready"]:
        t5_bottleneck = {
            "key": "independent_replication",
            "label_it": (
                "Replica ogni confronto con due squadre indipendenti"
            ),
        }
    else:
        t5_bottleneck = None
    return {
        "target_user": {
            "id": user.get("id"),
            "email": user.get("email"),
        },
        "guild_id": guild.get("id"),
        "ready_for_playtest": completed_journeys > 0,
        "t5_completion_ready": t5_completion_ready,
        "t5_gate": t5_gate,
        "t5_bottleneck": t5_bottleneck,
        "completed_journeys": completed_journeys,
        "bottleneck": bottleneck,
        "telemetry": {
            "active_adventurers": len(adventurers),
            **telemetry_counts,
            "completed_journeys": completed_journeys,
            "distinct_resonant_builds_observed": len(
                distinct_resonant_builds
            ),
            "completed_dungeons": len(expeditions),
            "completed_raids": len(raids),
            "applied_raid_reward_grants": len(applied_grant_raid_ids),
        },
        "coverage": coverage,
        "balance": balance,
        "adventurers": journey_rows,
    }


async def build_tester_vertical_slice(
    db,
    *,
    user: dict,
    guild: dict | None,
) -> dict:
    """Load and compile the server-owned vertical-slice telemetry."""
    if not guild:
        return compile_tester_vertical_slice(
            user=user,
            guild=None,
            adventurers=[],
            signature_items=[],
            equipped_items=[],
            expeditions=[],
            expedition_members=[],
            raids=[],
            raid_participants=[],
            raid_reward_grants=[],
        )

    guild_id = guild["id"]
    adventurers = await db.adventurers.find(
        _active_roster_query(guild_id),
        {"_id": 0},
    ).to_list(500)
    adventurer_ids = [
        row.get("id") for row in adventurers if row.get("id")
    ]
    hall_sources = [
        f"class_hall:{row.get('class_hall_id')}"
        for row in adventurers
        if row.get("class_hall_id")
    ]
    signature_items = await db.items.find(
        {
            "source": {"$in": hall_sources},
            "acquisition_track_order": 0,
            "is_active": {"$ne": False},
        },
        {
            "_id": 0,
            "id": 1,
            "name": 1,
            "display_name_it": 1,
            "source": 1,
            "acquisition_track_order": 1,
        },
    ).to_list(100)
    equipped_items = await db.equipped_items.find(
        {
            "guild_id": guild_id,
            "adventurer_id": {"$in": adventurer_ids},
        },
        {"_id": 0, "adventurer_id": 1, "item_id": 1},
    ).to_list(5000)
    expeditions = await db.expeditions.find(
        {
            "guild_id": guild_id,
            "status": {"$in": ["completed", "success", "failed"]},
        },
        {
            "_id": 0,
            "id": 1,
            "status": 1,
            "completed_at": 1,
            "started_at": 1,
            "created_at": 1,
            "result_summary": 1,
            "dungeon_id": 1,
            "final_team_power": 1,
            "team_power": 1,
            "recommended_power": 1,
        },
    ).to_list(5000)
    dungeon_ids = list(
        {
            row.get("dungeon_id")
            for row in expeditions
            if row.get("dungeon_id")
        }
    )
    dungeon_docs = await db.dungeons.find(
        {"id": {"$in": dungeon_ids}},
        {
            "_id": 0,
            "id": 1,
            "recommended_power": 1,
            "required_level": 1,
            "slug": 1,
        },
    ).to_list(100)
    dungeon_by_id = {
        row.get("id"): row for row in dungeon_docs
    }
    for expedition in expeditions:
        dungeon = dungeon_by_id.get(expedition.get("dungeon_id"), {})
        expedition["_tuning_recommended_power"] = dungeon.get(
            "recommended_power"
        )
        expedition["_tuning_required_level"] = dungeon.get(
            "required_level"
        )
        expedition["_tuning_content_slug"] = dungeon.get("slug")
    expedition_ids = [
        row.get("id") for row in expeditions if row.get("id")
    ]
    expedition_members = await db.expedition_members.find(
        {
            "expedition_id": {"$in": expedition_ids},
        },
        {
            "_id": 0,
            "expedition_id": 1,
            "adventurer_id": 1,
            "equipment_snapshot": 1,
            "class_mechanic_snapshot": 1,
            "total_power_snapshot": 1,
            "equipment_power_snapshot": 1,
            "item_effect_power_bonus": 1,
            "class_item_resonance_bonus": 1,
        },
    ).to_list(25000)
    raids = await db.raids.find(
        {"guild_id": guild_id, "status": "completed"},
        {
            "_id": 0,
            "id": 1,
            "status": 1,
            "completed_at": 1,
            "started_at": 1,
            "created_at": 1,
            "outcome": 1,
            "raid_dungeon_slug": 1,
            "team_power_combined": 1,
            "recommended_power_combined": 1,
        },
    ).to_list(1000)
    raid_ids = [row.get("id") for row in raids if row.get("id")]
    raid_participants = await db.raid_participants.find(
        {
            "raid_id": {"$in": raid_ids},
        },
        {
            "_id": 0,
            "raid_id": 1,
            "adventurer_id": 1,
            "class_mechanic_snapshot": 1,
            "outcome": 1,
            "total_power_snapshot": 1,
            "equipment_power_snapshot": 1,
            "level_snapshot": 1,
        },
    ).to_list(25000)
    raid_reward_grants = await db.raid_reward_grants.find(
        {"guild_id": guild_id, "raid_id": {"$in": raid_ids}},
        {"_id": 0, "raid_id": 1, "status": 1},
    ).to_list(1000)
    return compile_tester_vertical_slice(
        user=user,
        guild=guild,
        adventurers=adventurers,
        signature_items=signature_items,
        equipped_items=equipped_items,
        expeditions=expeditions,
        expedition_members=expedition_members,
        raids=raids,
        raid_participants=raid_participants,
        raid_reward_grants=raid_reward_grants,
    )


async def release_tester_equipment(
    db,
    *,
    guild_id: str,
    adventurer_ids: list[str],
) -> int:
    if not adventurer_ids:
        return 0
    equipped = await db.equipped_items.find(
        {
            "guild_id": guild_id,
            "adventurer_id": {"$in": adventurer_ids},
        },
        {"_id": 0, "item_id": 1},
    ).to_list(5000)
    counts = Counter(
        row.get("item_id") for row in equipped if row.get("item_id")
    )
    deleted = await db.equipped_items.delete_many(
        {
            "guild_id": guild_id,
            "adventurer_id": {"$in": adventurer_ids},
        }
    )
    for item_id, count in counts.items():
        inventory = await db.inventory_items.find_one(
            {"guild_id": guild_id, "item_id": item_id},
            {"_id": 0, "reserved_qty": 1},
        )
        if inventory is None:
            continue
        reserved = max(0, int(inventory.get("reserved_qty") or 0) - count)
        await db.inventory_items.update_one(
            {"guild_id": guild_id, "item_id": item_id},
            {"$set": {"reserved_qty": reserved, "updated_at": _now_iso()}},
        )
    return int(getattr(deleted, "deleted_count", 0))


async def reset_tester_class_hall_journey(
    db,
    *,
    user: dict,
    guild: dict,
    snapshot_id: str,
) -> dict:
    """Soft-retire the current roster and create five classless starters."""
    guild_id = guild["id"]
    active = await db.adventurers.find(
        _active_roster_query(guild_id),
        {"_id": 0},
    ).to_list(500)
    busy = [
        adventurer["id"]
        for adventurer in active
        if adventurer.get("is_available", True) is not True
    ]
    if busy:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "tester_journey.active_activity",
                "user_message": (
                    "Termina o annulla le attività degli avventurieri prima "
                    "di creare un nuovo viaggio tester."
                ),
                "busy_adventurer_ids": busy,
            },
        )

    reset_id = str(uuid.uuid4())
    now = _now_iso()
    active_ids = [adventurer["id"] for adventurer in active]
    equipment_released = await release_tester_equipment(
        db,
        guild_id=guild_id,
        adventurer_ids=active_ids,
    )
    archived = 0
    if active_ids:
        result = await db.adventurers.update_many(
            {"guild_id": guild_id, "id": {"$in": active_ids}},
            {
                "$set": {
                    "is_retired": True,
                    "retired": True,
                    "archived": True,
                    "is_available": False,
                    "archived_by_tester_journey_reset": True,
                    "tester_journey_reset_id": reset_id,
                    "updated_at": now,
                }
            },
        )
        archived = int(getattr(result, "modified_count", 0))

    traits_pool = await db.adventurer_traits.find(
        {"is_active": True, "is_test": {"$ne": True}},
        {"_id": 0},
    ).to_list(500)
    if not traits_pool:
        traits_pool = await db.traits.find(
            {"is_active": True, "is_test": {"$ne": True}},
            {"_id": 0},
        ).to_list(500)

    starters = []
    for _ in range(STARTER_TESTER_ROSTER_SIZE):
        adventurer = build_classless_tester_adventurer(
            guild_id,
            traits_pool=traits_pool,
            is_starter=True,
            extra={
                "tester_journey_generation_id": reset_id,
                "tester_journey_snapshot_id": snapshot_id,
                "updated_at": now,
            },
        )
        starters.append(adventurer)
    await db.adventurers.insert_many(starters)

    await db.guilds.update_one(
        {"id": guild_id},
        {
            "$set": {
                "tester_journey_generation_id": reset_id,
                "tester_journey_started_at": now,
                "updated_at": now,
            }
        },
    )
    return {
        "reset_id": reset_id,
        "snapshot_id": snapshot_id,
        "guild_id": guild_id,
        "archived_adventurers": archived,
        "equipment_released": equipment_released,
        "created_classless_adventurers": len(starters),
        "adventurer_ids": [adventurer["id"] for adventurer in starters],
        "class_selection_required": True,
        "history_preserved": True,
    }


__all__ = [
    "LONG_TERM_ITEM_TARGET",
    "STARTER_TESTER_ROSTER_SIZE",
    "VERTICAL_SLICE_STEPS",
    "build_classless_tester_adventurer",
    "build_tester_smoke_matrix",
    "build_tester_vertical_slice",
    "compile_tester_vertical_slice",
    "release_tester_equipment",
    "reset_tester_class_hall_journey",
]
