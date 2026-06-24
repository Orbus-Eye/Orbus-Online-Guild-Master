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
    await db.inventory_items.create_index(
        [("id", ASCENDING)], unique=True, name="inv_id_unique"
    )
    await db.inventory_items.create_index(
        [("guild_id", ASCENDING), ("item_id", ASCENDING)],
        unique=True,
        name="inv_guild_item_unique",
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


__all__ = ["create_all_indexes"]
