"""Phase 14.7 (ROUND 3.D) — Append-only economic audit log.

Pure helper module. Anyone in the codebase calls `write_audit(db, ...)` to
record an event. Failures are swallowed (logged at WARNING) so the audit
infrastructure never blocks a business operation.

Schema:
    {
        "id": str (uuid4),
        "event_type": str,
        "actor_user_id": str | None,
        "actor_guild_id": str | None,
        "item_slug": str | None,
        "item_template_id": str | None,
        "quantity": int | None,
        "gold_delta": int | None,
        "source": str,
        "related_entity_id": str | None,
        "metadata": dict,
        "created_at": str (ISO UTC),
    }

Privacy rules (enforced by `_sanitize_metadata`):
- No password / token / hash values.
- Email addresses get masked to `f***@domain`.
- Anything else passes through as-is.
"""
from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("orbus.audit")

# Canonical event types — keep this set explicit so misspellings stand out.
EVENT_TYPES = frozenset({
    "loot_awarded",
    "item_crafted",
    "crafting_inputs_consumed",
    "gold_debited",
    "gold_credited",
    "equip_item",
    "unequip_item",
    # Phase 14.8 (ROUND 3.C) — Marketplace events (kept under market_ name
    # for continuity; same events fire from the new /api/auction/* mirror).
    "market_listing_created",
    "market_listing_cancelled",
    "market_purchase_completed",
    # Phase 19.4b — NPC system shop
    "shop_system_purchase",
    "shop_system_sale",
    # ROUND 13b
    "season_stat_incremented",
    # ROUND 13c
    "market_rotation_refreshed",
    # ROUND 14
    "guild_archived_pre_launch",
    "guild_unarchived_pre_launch",
    "shop_system_sale",
    # ROUND 6A.1 — adventurer generation (server-authoritative)
    "adventurer_generated",
    # Phase 14.1 + 15 — Retention layer
    "quest_reward_claimed",
    "weekly_quest_claimed",
    "weekly_rotation_generated",
    "streak_updated",
    "streak_reward_claimed",
    # Phase 16 — Consortiums
    "consortium_created",
    "consortium_joined",
    "consortium_left",
    # ROUND 4 — Forge
    "item_refined",
    "item_refine_failed",
    "item_enchanted",
    "item_disenchanted",
    "item_reroll_affix",
    # ROUND 5 — Phase 17.5 + 18
    "starter_roster_seeded",
    "dungeon_power_bumped",
    "raid_started",
    "raid_completed",
    "raid_recovered",
    "WORLD_BOSS_EVENT_CREATED",
    "WORLD_BOSS_EVENT_STARTED",
    "WORLD_BOSS_JOINED",
    "WORLD_BOSS_CONTRIBUTION_RECORDED",
    "WORLD_BOSS_REWARD_GRANTED",
    "WORLD_BOSS_EVENT_RESOLVED",
    "WORLD_BOSS_TEAM_RELEASED",
    "WORLD_CONTINENT_JOINED",
    "WORLD_CONTINENT_CHANGED",
    "WORLD_ACCESS_GRANTED",
    # ROUND 16.3 Phase 3 — Continent events + site contracts
    "CONTINENT_EVENT_CREATED",
    "CONTINENT_EVENT_ACTIVATED",
    "CONTINENT_EVENT_EXPIRED",
    "SITE_INCOME_CLAIMED",
    "SITE_INCOME_CONFIG_UPDATED",
    # ROUND 16.3 Phase 4 — Continent resources + leaderboards
    "RESOURCE_MISSION_STARTED",
    "RESOURCE_MISSION_COMPLETED",
    "RESOURCE_MISSION_FAILED",
    "RESOURCE_GRANTED",
    "LEADERBOARD_SNAPSHOT_COMPUTED",
    # ROUND 16.3 Phase 5A — Legendary Forge
    "LEGENDARY_CRAFT_STARTED",
    "LEGENDARY_CRAFT_COMPLETED",
    "LEGENDARY_CRAFT_FAILED",
    "LEGENDARY_STAT_CLAMPED",
    "LEGENDARY_RECIPE_TOGGLED",
    # ROUND 16.3 Phase 5A Enhancement — Chronicle public event (lowercase
    # so it flows into the existing chronicle whitelist)
    "legendary_perfezionato",
    # ROUND 16.3 Phase 5B — Arfus Forge (guild passive technologies)
    "ARFUS_RESEARCH_STARTED",
    "ARFUS_RESEARCH_COMPLETED",
    "ARFUS_TECHNOLOGY_UNLOCKED",
    "ARFUS_TECHNOLOGY_ACTIVATED",
    "ARFUS_TECHNOLOGY_DEACTIVATED",
    # ROUND 6A.2a — Squads (custom adventurer groupings)
    "squad_created",
    "squad_updated",
    "squad_archived",
    # ROUND 6A.2b — Trait hygiene
    "trait_quarantined",
    # ROUND 6B.1 — Territory
    "guild_structure_purchased",
    "guild_structure_upgraded",
    "guild_territory_migrated",
    # ROUND 6B.2a — Cap + Retire
    "adventurer_cap_reached",
    "adventurer_retired",
    # ROUND 6B.3 Wave 1 — Territory rollback
    "guild_structure_rollback_free_purchase",
    # ROUND 6B.3 Wave 1.5 — Over-cap roster enforcement
    "roster_over_capacity_blocked",
    # ROUND 6B.4 — Bound items + retire safety + roster health
    "adventurer_retired_bulk",
    "equipment_returned_after_retire",
    "bound_to_adventurer_dev_seed",
    # ROUND 6C — Training Grounds + Specializations
    "specialization_applied",
    "specialization_signature_item_created",
    "specialization_signature_item_discarded_on_retire",
    # ROUND 6E — Respec
    "specialization_respec",
    "specialization_signature_item_discarded_on_respec",
    # ROUND 11.2 TASK 2 — Specialization atomicity (compensating pattern)
    "training_specialization_attempt",       # pending: BEFORE gold debit, records intent
    "training_specialization_committed",     # success: AFTER all writes complete
    "training_specialization_rolled_back",   # failure: gold refunded, no state change
    "training_specialization_refund",        # one-shot CLI refund (P0 historical recovery)
    # ROUND 11.2 TASK 5a — Admin Ops MVP
    "admin_gold_granted",                    # admin granted gold to a guild (with reason)
    "admin_item_granted",                    # admin granted item(s) to a guild (with reason)
    # ROUND 6C — Preview validation seed (dev-only, whitelist-gated)
    "guild_structure_seeded",
    "adventurer_seeded",
    # ROUND 6E — Preview validation seed extension (materials grant)
    "materials_granted_for_round6e_validation",
    # ROUND 6D — Contracts + Milestones
    "contract_claimed",
    "guild_milestone_reached",
    "guild_milestone_claimed",
    # ROUND 11.3 TASK D — Leaderboard cache rebuilt audit event.
    "leaderboard_cache_rebuilt",
    # ROUND 11.3 TASK B — Equipment level requirement
    "equipment_auto_unequipped_level_requirement",
    # ROUND 11.3 TASK C — Recruit Freeze Bench
    "recruit_candidate_frozen",
    "recruit_candidate_unfrozen",
    "recruit_frozen_candidate_hired",
    # ROUND 12 — Seasons / Leagues / PvP Arena
    "season_created",
    "season_activated",
    "season_ended",
    "season_archived",
    "season_scores_recomputed",
    "season_rewards_granted",
    "pvp_defense_team_created",
    "pvp_defense_team_updated",
    "pvp_defense_team_deleted",
    "pvp_match_created",
    "pvp_match_resolved",
    "pvp_rating_updated",
    "pvp_match_invalidated",
    # ROUND 12.D — Preview-only tester roster release
    "tester_roster_released_preview",
    # ROUND 16.0 — Class rework (10 base classes + specializations + Stregone)
    "class_created_round160",
    "class_deprecated_round160",
    "class_marked_base_round160",
    "class_specialization_seeded",
    "class_specialization_unlocked",
    "class_hall_seeded_round160",
    "class_hall_unlocked",
    "adventurer_class_migrated",
    "item_class_tags_extended",
    "achievement_text_updated_round160",
    # ROUND 16.0 Phase 3 — Races + Gender + Auto-Equip
    "race_seeded_round160",
    "adventurer_race_assigned",
    "adventurer_gender_assigned",
    "adventurer_auto_equipped",
    # ROUND 16.0 Phase 4 — Threats & Counters (schema-only Void/Undead) + Mission Traits
    "threat_seeded_round160",
    "counter_tag_seeded_round160",
    "dungeon_threats_assigned_round160",
    "spec_counter_tags_updated_round160",
    "trait_counter_tags_updated_round160",
    "mission_trait_seeded_round160",
    # ROUND 16.0.1 — Alchemist (11th base class) + recruitment cleanup
    "alchemist_class_seeded",
    "alchemist_class_halls_seeded",
    "recruitment_offers_deprecated_round160",
    # ROUND 16.A Phase 2 — Achievement / XP / Onboarding audit bridge
    "achievement_unlocked",   # superseded the legacy `achievement_completed`
    "guild_xp_gained",
    "onboarding_graduated",
})

# Indexes asserted at module import via `ensure_audit_indexes`.
_REQUIRED_INDEXES = (
    [("actor_user_id", 1), ("created_at", -1)],
    [("event_type", 1), ("created_at", -1)],
    [("actor_guild_id", 1), ("created_at", -1)],
)


_BLOCKED_KEYS = frozenset({
    "password", "passwd", "password_hash", "hash",
    "token", "access_token", "refresh_token", "jwt",
    "smtp_password", "secret",
})

_EMAIL_RE = re.compile(r"([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*(@[A-Za-z0-9.-]+\.[A-Za-z]{2,})")


def _mask_email(s: str) -> str:
    return _EMAIL_RE.sub(r"\1***\2", s)


def _sanitize_metadata(md: Optional[dict]) -> dict:
    """Drop sensitive keys, mask email-shaped values. Defensive but minimal."""
    if not md:
        return {}
    out: dict = {}
    for k, v in md.items():
        if not isinstance(k, str):
            continue
        if k.lower() in _BLOCKED_KEYS:
            continue
        if isinstance(v, str) and "@" in v:
            out[k] = _mask_email(v)
        elif isinstance(v, dict):
            out[k] = _sanitize_metadata(v)
        elif isinstance(v, (str, int, float, bool, list, type(None))):
            out[k] = v
        # everything else (e.g. ObjectId) is dropped on purpose
    return out


async def ensure_audit_indexes(db) -> None:
    """Create indexes idempotently. Called from app startup."""
    try:
        for idx in _REQUIRED_INDEXES:
            await db.audit_log.create_index(idx)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ensure_audit_indexes failed: %s", exc)


async def write_audit(
    db,
    *,
    event_type: str,
    actor_user_id: Optional[str] = None,
    actor_guild_id: Optional[str] = None,
    item_slug: Optional[str] = None,
    item_template_id: Optional[str] = None,
    quantity: Optional[int] = None,
    gold_delta: Optional[int] = None,
    source: str = "unknown",
    related_entity_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Optional[str]:
    """Write a single audit log row. Never raises — failures only log.

    Returns the audit event `id` (uuid4 str) on success, `None` if the
    write failed or the event_type was rejected. ROUND 11.2 TASK 5b —
    surfaced for admin grant endpoints to return `audit_event_id` to the
    client. All other call sites ignore the return value (safe additive).
    """
    if event_type not in EVENT_TYPES:
        logger.warning("audit: unknown event_type=%s — dropped", event_type)
        return None
    doc = {
        "id": str(uuid.uuid4()),
        "event_type": event_type,
        "actor_user_id": actor_user_id,
        "actor_guild_id": actor_guild_id,
        "item_slug": item_slug,
        "item_template_id": item_template_id,
        "quantity": int(quantity) if quantity is not None else None,
        "gold_delta": int(gold_delta) if gold_delta is not None else None,
        "source": source,
        "related_entity_id": related_entity_id,
        "metadata": _sanitize_metadata(metadata),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        await db.audit_log.insert_one(doc)
        return doc["id"]
    except Exception as exc:  # noqa: BLE001
        # Never block business flow on audit write failure.
        logger.warning("audit write failed (%s): %s", event_type, exc)
        return None


__all__ = ["write_audit", "ensure_audit_indexes", "EVENT_TYPES"]
