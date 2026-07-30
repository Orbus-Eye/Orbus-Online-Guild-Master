"""MongoDB index creation (Phase 5.5g).

Single entry point `create_all_indexes(db)` invoked by the ASGI lifespan.
All indexes are idempotent (`create_index` is a no-op if the spec matches).
TTL indexes use `expireAfterSeconds` for automatic cleanup.
"""
from pymongo import ASCENDING

from app.shared.constants import LOGIN_ATTEMPTS_TTL_SECONDS


async def create_all_indexes(db) -> None:
    # ─── Auth / Users / Guilds ────────────────────────────────────────────────
    await db.users.create_index([("email", ASCENDING)], unique=True, name="users_email_unique")
    await db.users.create_index([("id", ASCENDING)], unique=True, name="users_id_unique")
    await db.guilds.create_index([("id", ASCENDING)], unique=True, name="guilds_id_unique")
    await db.guilds.create_index(
        [("owner_user_id", ASCENDING)], unique=True, name="guilds_owner_unique"
    )
    await db.guilds.create_index([("name", ASCENDING)], name="guilds_name_idx")
    # Phase 9.1: compound index for public leaderboard sort
    # (max_team_power_ever desc, level desc, reputation desc, created_at asc)
    from pymongo import DESCENDING  # local import to keep top-imports tight

    await db.guilds.create_index(
        [
            ("max_team_power_ever", DESCENDING),
            ("level", DESCENDING),
            ("reputation", DESCENDING),
            ("created_at", ASCENDING),
        ],
        name="guilds_leaderboard_idx",
    )

    # ─── Phase 2: Adventurers / Classes / Traits / Recruitment ────────────────
    await db.adventurer_classes.create_index(
        [("slug", ASCENDING)], unique=True, name="classes_slug_unique"
    )
    await db.adventurer_classes.create_index(
        [("id", ASCENDING)], unique=True, name="classes_id_unique"
    )
    await db.adventurer_traits.create_index(
        [("name", ASCENDING)], unique=True, name="traits_name_unique"
    )
    await db.adventurers.create_index(
        [("id", ASCENDING)], unique=True, name="adventurers_id_unique"
    )
    await db.adventurers.create_index(
        [("guild_id", ASCENDING)], name="adventurers_guild_idx"
    )
    await db.adventurers.create_index(
        [
            ("guild_id", ASCENDING),
            ("recruit_status", ASCENDING),
            ("is_retired", ASCENDING),
        ],
        name="adventurers_guild_recruit_status_idx",
    )
    await db.adventurer_career_events.create_index(
        [("id", ASCENDING)],
        unique=True,
        name="adventurer_career_event_id_unique",
    )
    await db.adventurer_career_events.create_index(
        [("adventurer_id", ASCENDING), ("created_at", ASCENDING)],
        name="adventurer_career_event_history",
    )
    await db.reward_secret_rolls.create_index(
        [("id", ASCENDING)], unique=True, name="reward_secret_rolls_id_unique"
    )
    await db.reward_global_uniques.create_index(
        [("id", ASCENDING)], unique=True, name="reward_global_uniques_id_unique"
    )
    await db.recruitment_offers.create_index(
        [("id", ASCENDING)], unique=True, name="offers_id_unique"
    )
    await db.recruitment_offers.create_index(
        [("guild_id", ASCENDING)], name="offers_guild_idx"
    )

    # ─── Phase 3: Dungeons / Items / Expeditions / Inventory ──────────────────
    await db.dungeons.create_index([("slug", ASCENDING)], unique=True, name="dungeons_slug_unique")
    await db.dungeons.create_index([("id", ASCENDING)], unique=True, name="dungeons_id_unique")
    await db.items.create_index([("slug", ASCENDING)], unique=True, name="items_slug_unique")
    await db.items.create_index([("id", ASCENDING)], unique=True, name="items_id_unique")
    await db.items.create_index(
        [("blueprint_id", ASCENDING)],
        unique=True,
        partialFilterExpression={"blueprint_id": {"$type": "string"}},
        name="items_blueprint_id_unique",
    )
    await db.expeditions.create_index(
        [("id", ASCENDING)], unique=True, name="expeditions_id_unique"
    )
    await db.expeditions.create_index(
        [("guild_id", ASCENDING), ("status", ASCENDING)],
        name="expeditions_guild_status_idx",
    )
    await db.expeditions.create_index(
        [("completes_at", ASCENDING)], name="expeditions_completes_at_idx"
    )
    await db.expedition_members.create_index(
        [("id", ASCENDING)], unique=True, name="members_id_unique"
    )
    await db.expedition_members.create_index(
        [("expedition_id", ASCENDING)], name="members_exp_idx"
    )
    await db.raid_reward_grants.create_index(
        [("raid_id", ASCENDING)],
        unique=True,
        name="raid_reward_grant_raid_unique",
    )
    await db.raid_reward_grants.create_index(
        [("guild_id", ASCENDING), ("created_at", ASCENDING)],
        name="raid_reward_grant_guild_history",
    )
    await db.raid_item_reward_grants.create_index(
        [("raid_id", ASCENDING)],
        unique=True,
        name="raid_item_reward_grant_raid_unique",
    )
    await db.raid_item_reward_grants.create_index(
        [("guild_id", ASCENDING), ("created_at", ASCENDING)],
        name="raid_item_reward_grant_guild_history",
    )
    await db.tester_release_checklists.create_index(
        [("id", ASCENDING)],
        unique=True,
        name="tester_release_checklist_id_unique",
    )
    await db.tester_release_checklists.create_index(
        [("target_user_id", ASCENDING), ("recorded_at", ASCENDING)],
        name="tester_release_checklist_user_history",
    )
    await db.reward_source_grants.create_index(
        [("grant_key", ASCENDING)],
        unique=True,
        name="reward_source_grant_key_unique",
    )
    await db.reward_source_grants.create_index(
        [("guild_id", ASCENDING), ("source_policy_id", ASCENDING)],
        name="reward_source_grant_guild_source",
    )
    await db.inventory_items.create_index(
        [("id", ASCENDING)], unique=True, name="inv_id_unique"
    )
    await db.inventory_items.create_index(
        [("guild_id", ASCENDING), ("item_id", ASCENDING)],
        unique=True,
        name="inv_guild_item_unique",
    )
    await db.inventory_items.create_index(
        [("source_grant_id", ASCENDING)],
        unique=True,
        partialFilterExpression={"source_grant_id": {"$type": "string"}},
        name="inv_source_grant_unique",
    )
    # R18.6 — classless recruit journey and reconcile-forward starter reward.
    await db.class_hall_trial_sessions.create_index(
        [("id", ASCENDING)],
        unique=True,
        name="class_hall_trial_id_unique",
    )
    await db.class_hall_trial_sessions.create_index(
        [
            ("guild_id", ASCENDING),
            ("adventurer_id", ASCENDING),
            ("hall_id", ASCENDING),
            ("status", ASCENDING),
        ],
        name="class_hall_trial_assignment_lookup",
    )
    await db.class_hall_trial_sessions.create_index(
        [("expires_at", ASCENDING)],
        expireAfterSeconds=0,
        name="class_hall_trial_ttl",
    )
    await db.class_hall_reward_grants.create_index(
        [
            ("guild_id", ASCENDING),
            ("adventurer_id", ASCENDING),
            ("hall_id", ASCENDING),
        ],
        unique=True,
        name="class_hall_reward_assignment_unique",
    )
    await db.class_hall_reward_grants.create_index(
        [("status", ASCENDING)],
        name="class_hall_reward_status_idx",
    )
    await db.class_hall_item_grants.create_index(
        [
            ("guild_id", ASCENDING),
            ("adventurer_id", ASCENDING),
            ("item_id", ASCENDING),
        ],
        unique=True,
        name="class_hall_item_grant_unique",
    )
    await db.class_hall_item_grants.create_index(
        [("status", ASCENDING)],
        name="class_hall_item_grant_status_idx",
    )

    # ─── Phase 6: Equipped items ──────────────────────────────────────────────
    await db.equipped_items.create_index(
        [("id", ASCENDING)], unique=True, name="equipped_id_unique"
    )
    await db.equipped_items.create_index(
        [("guild_id", ASCENDING)], name="equipped_guild_idx"
    )
    await db.equipped_items.create_index(
        [("adventurer_id", ASCENDING)], name="equipped_adv_idx"
    )
    await db.equipped_items.create_index(
        [("item_id", ASCENDING)], name="equipped_item_idx"
    )
    await db.equipped_items.create_index(
        [("adventurer_id", ASCENDING), ("slot", ASCENDING)],
        unique=True,
        name="equipped_adv_slot_unique",
    )

    # ─── Phase 5: Security collections (TTL-managed) ──────────────────────────
    await db.login_attempts.create_index(
        [("email", ASCENDING)], unique=True, name="login_attempts_email_unique"
    )
    await db.login_attempts.create_index(
        [("last_attempt_at", ASCENDING)],
        expireAfterSeconds=LOGIN_ATTEMPTS_TTL_SECONDS,
        name="login_attempts_ttl",
    )
    await db.refresh_tokens.create_index(
        [("token_hash", ASCENDING)], unique=True, name="refresh_tokens_hash_unique"
    )
    await db.refresh_tokens.create_index(
        [("user_id", ASCENDING)], name="refresh_tokens_user_idx"
    )
    await db.refresh_tokens.create_index(
        [("expires_at", ASCENDING)],
        expireAfterSeconds=0,
        name="refresh_tokens_ttl",
    )
    await db.password_reset_tokens.create_index(
        [("token_hash", ASCENDING)], unique=True, name="password_reset_hash_unique"
    )
    await db.password_reset_tokens.create_index(
        [("user_id", ASCENDING)], name="password_reset_user_idx"
    )
    await db.password_reset_tokens.create_index(
        [("expires_at", ASCENDING)],
        expireAfterSeconds=0,
        name="password_reset_ttl",
    )

    # ─── ROUND 6A.2a — Squads ────────────────────────────────────────────────
    await db.squads.create_index([("id", ASCENDING)], unique=True, name="squads_id_unique")
    await db.squads.create_index(
        [("guild_id", ASCENDING), ("squad_type", ASCENDING)],
        name="squads_guild_type_idx",
    )
    await db.squads.create_index(
        [("owner_user_id", ASCENDING), ("is_archived", ASCENDING)],
        name="squads_owner_active_idx",
    )
    # Case-insensitive name uniqueness per guild (only enforced on non-archived).
    await db.squads.create_index(
        [("guild_id", ASCENDING), ("name_lower", ASCENDING)],
        unique=True,
        partialFilterExpression={"is_archived": False},
        name="squads_guild_name_unique_active",
    )

    # ROUND 6B.1 — guild_structures (Territory)
    await db.guild_structures.create_index(
        [("guild_id", ASCENDING)],
        unique=True,
        name="guild_structures_guild_unique",
    )
    await db.guild_structures.create_index(
        [("id", ASCENDING)], unique=True, name="guild_structures_id_unique"
    )


__all__ = ["create_all_indexes"]
