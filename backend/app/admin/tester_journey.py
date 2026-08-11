"""Tester-only support for the class-first Class Hall journey.

FASE 9C — riscritto senza il concetto di build/specializzazione: il
viaggio tester è Hall → item-firma → dungeon con risonanza di CLASSE →
raid → ricompensa. Le vecchie analytics di tuning per-build (T8 wave
coverage, controlled comparisons, balance telemetry) sono state rimosse
insieme alle 81 build.

The reset keeps account and guild history intact: active adventurers are
soft-retired, their equipment is released through the same reservation
invariant used by normal unequip, and six new Common recruits are created
in the explicit ``recruit_unassigned`` state.
"""

from __future__ import annotations

import uuid
from collections import Counter
from datetime import datetime, timezone

from fastapi import HTTPException

from app.adventurers.classless import is_explicit_classless_recruit
from app.adventurers.common import _generate_classless_candidate
from app.class_halls.catalog import CLASS_HALLS
from app.class_halls.mechanics import resolve_class_mechanic
from app.classes import CLASS_REGISTRY, class_role_for


# FASE 9 A4 — allineato ai 6 fondatori gratuiti (STARTER_TARGET).
STARTER_TESTER_ROSTER_SIZE = 6
LONG_TERM_ITEM_TARGET = 1500
VERTICAL_SLICE_STEPS = (
    ("class_hall_chosen", "Class Hall scelta"),
    ("signature_item_equipped", "Item-firma equipaggiato"),
    ("resonant_dungeon_completed",
     "Dungeon completato con risonanza di classe"),
    ("raid_completed", "Raid completato dopo il dungeon"),
    ("raid_reward_tracked", "Ricompensa raid registrata"),
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


def _class_resonance_reachability(hall_items: list[dict]) -> dict:
    """FASE 9C — per ogni classe canonica, il kit della sua Hall deve
    poter attivare la risonanza di classe (nessuna build)."""
    items_by_hall: dict[str, list[dict]] = {}
    for item in hall_items:
        hall_id = str(item.get("source") or "").split(":", 1)[-1]
        items_by_hall.setdefault(hall_id, []).append(item)
    resonant_classes = 0
    missing: list[str] = []
    for profile in CLASS_HALLS.values():
        kit = items_by_hall.get(profile.hall_id, [])
        resolved = resolve_class_mechanic(
            adventurer={
                "canonical_class_slug": profile.canonical_class_slug,
            },
            equipment_items=kit,
        )
        if resolved.get("resonance_active"):
            resonant_classes += 1
        else:
            missing.append(profile.canonical_class_slug)
    return {
        "resonant_class_count": resonant_classes,
        "class_count": len(CLASS_HALLS),
        "all_classes_resonant": not missing,
        "missing_classes": missing,
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
    resonance = _class_resonance_reachability(hall_items)

    # FASE 9B — distribuzione canonica dei ruoli: 13 DPS · 6 TANK · 8 HEALER.
    role_distribution = Counter(
        definition.class_role for definition in CLASS_REGISTRY.values()
    )
    roles_ok = (
        role_distribution.get("DPS") == 13
        and role_distribution.get("TANK") == 6
        and role_distribution.get("HEALER") == 8
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
            "canonical_roles",
            "Ruoli fissi canonici (13 DPS · 6 TANK · 8 HEALER)",
            ok=roles_ok,
            current=(
                f"{role_distribution.get('DPS', 0)} DPS · "
                f"{role_distribution.get('TANK', 0)} TANK · "
                f"{role_distribution.get('HEALER', 0)} HEALER"
            ),
            target="13 · 6 · 8",
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
            "hall_class_resonance",
            "Risonanza di classe attivabile dal kit della Sala",
            ok=resonance["all_classes_resonant"],
            current=(
                f"{resonance['resonant_class_count']}/"
                f"{resonance['class_count']}"
            ),
            target="27/27",
            detail_it=(
                "Ogni classe deve poter attivare la propria risonanza "
                "vestendo gli item della sua Sala (niente build)."
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
            "resonant_hall_classes": resonance["resonant_class_count"],
        },
    }


def _snapshot_resonance_active(snapshot: dict | None) -> bool:
    """True se lo snapshot meccanica indica risonanza attiva.

    Compatibile sia col nuovo formato FASE 9 (`resonance_active` al
    livello radice) sia con gli snapshot storici pre-9C
    (`active_build.resonance_active`)."""
    snap = snapshot or {}
    if snap.get("resonance_active") is True:
        return True
    if int(snap.get("item_resonance_bonus") or 0) > 0:
        return True
    active_build = snap.get("active_build") or {}
    return active_build.get("resonance_active") is True


def _activity_timestamp(row: dict) -> str:
    """Return a UTC timestamp whose lexical order is chronological."""
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
    """Compile the read-only Hall → item → dungeon → raid journey.

    FASE 9C — l'ultimo gradino build-driven ("nuova build attivata") non
    esiste più: il viaggio si chiude con la ricompensa raid registrata.
    Activity snapshots restano la source of truth.
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
                "resonance_active": _snapshot_resonance_active(
                    member.get("class_mechanic_snapshot")
                ),
                "equipment_item_ids": equipment_ids,
                "outcome_known": expedition.get("result_summary") in {
                    "Success",
                    "Failed",
                },
                "success": expedition.get("result_summary") == "Success",
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
                "resonance_active": _snapshot_resonance_active(
                    participant.get("class_mechanic_snapshot")
                ),
                "reward_tracked": raid.get("id") in applied_grant_raid_ids,
                "raid_outcome": raid.get("outcome"),
            }
        )

    journey_rows: list[dict] = []
    telemetry_counts = {key: 0 for key, _label in VERTICAL_SLICE_STEPS}

    for adventurer in adventurers:
        adventurer_id = adventurer.get("id")
        hall_chosen = _assigned_through_canonical_hall(adventurer)
        signature = signature_by_hall.get(adventurer.get("class_hall_id"))
        signature_id = signature.get("id") if signature else None
        activities = sorted(
            activities_by_adventurer.get(adventurer_id, []),
            key=lambda row: (row["timestamp"], row["kind"], row["id"] or ""),
        )
        signature_equipped = bool(
            hall_chosen
            and signature_id
            and (
                signature_id
                in equipped_by_adventurer.get(adventurer_id, set())
                or any(
                    signature_id in activity.get("equipment_item_ids", set())
                    for activity in activities
                    if activity["kind"] == "dungeon"
                )
            )
        )
        resonant_dungeon = next(
            (
                activity for activity in activities
                if activity["kind"] == "dungeon"
                and activity.get("resonance_active")
                and activity.get("success")
            ),
            None,
        ) if signature_equipped else None
        raid_after = None
        if resonant_dungeon:
            raid_after = next(
                (
                    activity for activity in activities
                    if activity["kind"] == "raid"
                    and activity["timestamp"]
                    >= resonant_dungeon["timestamp"]
                ),
                None,
            )
        reward_tracked = bool(raid_after and raid_after.get("reward_tracked"))

        steps = [
            _slice_step("class_hall_chosen", completed=hall_chosen),
            _slice_step(
                "signature_item_equipped",
                completed=signature_equipped,
                evidence={"item_id": signature_id} if signature_id else None,
            ),
            _slice_step(
                "resonant_dungeon_completed",
                completed=resonant_dungeon is not None,
                evidence=(
                    {"expedition_id": resonant_dungeon["id"]}
                    if resonant_dungeon else None
                ),
            ),
            _slice_step(
                "raid_completed",
                completed=raid_after is not None,
                evidence=(
                    {"raid_id": raid_after["id"]} if raid_after else None
                ),
            ),
            _slice_step("raid_reward_tracked", completed=reward_tracked),
        ]
        journey_completed = all(step["completed"] for step in steps)
        for step in steps:
            if step["completed"]:
                telemetry_counts[step["key"]] += 1
        journey_rows.append(
            {
                "adventurer_id": adventurer_id,
                "name": adventurer.get("name"),
                "class_slug": adventurer.get("canonical_class_slug"),
                "class_role": class_role_for(
                    str(adventurer.get("canonical_class_slug") or "")
                ),
                "steps": steps,
                "journey_completed": journey_completed,
            }
        )

    completed_journeys = sum(
        row["journey_completed"] for row in journey_rows
    )
    bottleneck = None
    for key, label_it in VERTICAL_SLICE_STEPS:
        if telemetry_counts[key] == 0:
            bottleneck = {"key": key, "label_it": label_it}
            break

    return {
        "target_user": {
            "id": user.get("id"),
            "email": user.get("email"),
        },
        "guild_id": guild.get("id"),
        "ready_for_playtest": completed_journeys > 0,
        # T5 gate consumato da tester_release: almeno un viaggio completo.
        "t5_completion_ready": completed_journeys > 0,
        "completed_journeys": completed_journeys,
        "bottleneck": bottleneck,
        "telemetry": {
            "active_adventurers": len(adventurers),
            "completed_journeys": completed_journeys,
            **telemetry_counts,
        },
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
        },
    ).to_list(5000)
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
    """Soft-retire the current roster and create six classless starters."""
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
