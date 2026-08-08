"""Seed runner (Phase 5.5g + Phase 14.3-c).

Three idempotent seeds + orchestrator. The tester seed is gated by APP_ENV
so it never writes to a production DB. Content seeds (classes/traits,
dungeons/items) run in all environments to keep the catalog in sync.
"""
import os
import logging
import re
import uuid
from datetime import datetime, timezone

from app.admin.services import validate_item_monetization
from app.core.security import hash_password
from app.seeds.seed_data import (
    CLASS_SEED,
    TRAIT_SEED,
    DUNGEON_SEED,
    ITEM_SEED,
)
from app.seeds.seed_traits_it import ITALIAN_TRAIT_SEED
from app.shared.constants import (
    TESTER_EMAIL,
    TESTER_USERNAME,
    TESTER_PASSWORD,
)


logger = logging.getLogger("orbus")


# Phase 14.3-c — patterns identifying internal/test traits that must never
# surface to players (anti-leak). Anything matching is flagged
# is_test=True / is_active=False (additive, reversible).
_TEST_TRAIT_NAME_RE = re.compile(
    r"^(Test|TEST_|qa_|dev_|pytest_)|_[a-f0-9]{6,}$|^[a-f0-9-]{16,}$",
    re.IGNORECASE,
)


def _is_test_trait_name(name: str) -> bool:
    return bool(name and _TEST_TRAIT_NAME_RE.search(name))


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def seed_italian_traits(db) -> None:
    """Phase 14.3-c — canonical Italian trait catalog (idempotent by `code`).

    Adds the new fields `code`, `display_name`, `display_name_en`,
    `description_en`, `rarity`, `polarity` and stamps
    `is_test=False is_active=True` so these traits are always eligible
    for recruitment + leaderboard preview.
    """
    now = _utc_now_iso()
    for t in ITALIAN_TRAIT_SEED:
        await db.adventurer_traits.update_one(
            {"code": t["code"]},
            {
                "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now},
                "$set": {
                    "code": t["code"],
                    # legacy `name` is set to `code` (snake_case) so it
                    # never collides with the case-sensitive unique index
                    # holding the old English seed names ("Brave",
                    # "Lucky", …). Display always goes through `display_name`.
                    "name": t["code"],
                    "display_name": t["display_name"],
                    "display_name_en": t["display_name_en"],
                    "description": t["description"],
                    "description_en": t["description_en"],
                    "rarity": t["rarity"],
                    "polarity": t["polarity"],
                    "modifier_type": t["modifier_type"],
                    "affected_stat": t["affected_stat"],
                    "modifier_value": t["modifier_value"],
                    "is_positive": t["is_positive"],
                    "is_active": True,
                    "is_test": False,
                    "updated_at": now,
                },
            },
            upsert=True,
        )
    logger.info("Seeded %d Italian traits (Phase 14.3-c)", len(ITALIAN_TRAIT_SEED))


async def flag_legacy_test_traits(db) -> None:
    """Phase 14.3-c — defensively flag any historical Test* / suffix-random
    trait as `is_test=True, is_active=False` so they never reach the player.

    Idempotent: running a second time matches zero new docs.
    """
    cursor = db.adventurer_traits.find(
        {"$or": [{"is_test": {"$ne": True}}, {"is_active": {"$ne": False}}]},
        {"_id": 0, "id": 1, "name": 1, "code": 1},
    )
    candidates_ids = []
    async for t in cursor:
        if t.get("code"):
            continue  # canonical traits keep their code; skip them entirely
        if _is_test_trait_name(t.get("name", "")):
            candidates_ids.append(t["id"])
    if not candidates_ids:
        logger.info("Phase 14.3-c: no legacy test traits to flag")
        return
    r = await db.adventurer_traits.update_many(
        {"id": {"$in": candidates_ids}},
        {"$set": {"is_test": True, "is_active": False,
                  "updated_at": _utc_now_iso()}},
    )
    logger.info(
        "Phase 14.3-c: flagged %d legacy traits as is_test=True/is_active=False",
        r.modified_count,
    )


async def scrub_test_traits_from_adventurers(db) -> None:
    """Phase 14.3-c — remove any test-trait reference still embedded in
    `adventurers.traits[]` (legacy data baked them in by name).

    Idempotent.
    """
    # Build the set of "bad" trait names from the flagged trait collection.
    bad_names = set()
    async for t in db.adventurer_traits.find(
        {"is_test": True}, {"_id": 0, "name": 1, "code": 1}
    ):
        if t.get("name"):
            bad_names.add(t["name"])
    if not bad_names:
        return

    affected = 0
    async for a in db.adventurers.find(
        {"traits.name": {"$in": list(bad_names)}}, {"_id": 0, "id": 1, "traits": 1}
    ):
        clean = [t for t in (a.get("traits") or []) if t.get("name") not in bad_names]
        if len(clean) != len(a.get("traits") or []):
            await db.adventurers.update_one(
                {"id": a["id"]},
                {"$set": {"traits": clean, "updated_at": _utc_now_iso()}},
            )
            affected += 1
    if affected:
        logger.info(
            "Phase 14.3-c: scrubbed test traits from %d adventurers", affected
        )


async def seed_classes_and_traits(db) -> None:
    """Idempotent content seed (runs in all envs, including production).

    ROUND 16.0 (2026-06): the deprecated classes (berserker, assassin,
    necromancer) keep `is_active=False` + `deprecated_at` set by
    `round160_seed_classes_v2.py`. The bootstrap MUST NOT reactivate
    them on every startup, so we skip any class document that already
    carries `deprecated_at`.
    """
    now = _utc_now_iso()
    for c in CLASS_SEED:
        existing = await db.adventurer_classes.find_one(
            {"slug": c["slug"]},
            {"_id": 0, "deprecated_at": 1},
        )
        if existing and existing.get("deprecated_at"):
            # Leave deprecated rows untouched; soft-deprecation is the
            # only signal recruitment / generator pools look at.
            continue
        await db.adventurer_classes.update_one(
            {"slug": c["slug"]},
            {
                "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now},
                "$set": {
                    "name": c["name"],
                    "slug": c["slug"],
                    "role": c["role"],
                    "description": c["description"],
                    "base_strength": c["base_strength"],
                    "base_agility": c["base_agility"],
                    "base_intellect": c["base_intellect"],
                    "base_endurance": c["base_endurance"],
                    "base_faith": c["base_faith"],
                    "is_active": True,
                    "updated_at": now,
                },
            },
            upsert=True,
        )

    for t in TRAIT_SEED:
        await db.adventurer_traits.update_one(
            {"name": t["name"]},
            {
                "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now},
                "$set": {
                    "name": t["name"],
                    "description": t["description"],
                    "modifier_type": t["modifier_type"],
                    "affected_stat": t["affected_stat"],
                    "modifier_value": t["modifier_value"],
                    "is_positive": t["is_positive"],
                    "is_active": True,
                    "updated_at": now,
                },
            },
            upsert=True,
        )
    logger.info("Seeded %d classes and %d traits", len(CLASS_SEED), len(TRAIT_SEED))


async def seed_dungeons_and_items(db) -> None:
    """Idempotent Phase-3 content seed."""
    from app.shared.content_curve import DUNGEON_CURVE
    now = _utc_now_iso()
    for d in DUNGEON_SEED:
        curve = DUNGEON_CURVE.get(d["slug"])
        await db.dungeons.update_one(
            {"slug": d["slug"]},
            {
                "$setOnInsert": {
                    "id": str(uuid.uuid4()),
                    "created_at": now,
                },
                "$set": {
                    "slug": d["slug"],
                    "name": d["name"],
                    "description": d["description"],
                    "difficulty": d["difficulty"],
                    "required_team_size": d["required_team_size"],
                    "base_duration_seconds": d["base_duration_seconds"],
                    "recommended_power": (
                        curve.recommended_power if curve else d["recommended_power"]
                    ),
                    "base_gold_reward": d["base_gold_reward"],
                    "base_xp_reward": (
                        curve.xp_reward if curve else d["base_xp_reward"]
                    ),
                    **({
                        "required_level": curve.required_level,
                        "bucket": curve.bucket,
                        # Prevent the obsolete Round-5 +25% migration from
                        # modifying the authoritative level-80 power value.
                        "power_bumped": True,
                    } if curve else {}),
                    # Phase 11.2: data-driven gate dict (optional)
                    "gate": d.get("gate") or {},
                    "is_active": True,
                    "updated_at": now,
                },
            },
            upsert=True,
        )

    for it in ITEM_SEED:
        full = {
            "level_required": 1,
            "is_tradeable": True,
            "is_cosmetic": False,
            "affects_economy": False,
            "affects_ranking": False,
            "can_be_sold_for_gold": True,
            "can_be_sold_for_real_money": False,
            **it,
        }
        validate_item_monetization(full)
        await db.items.update_one(
            {"slug": full["slug"]},
            {
                "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now},
                "$set": {
                    "slug": full["slug"],
                    "name": full["name"],
                    "description": full["description"],
                    "item_type": full["item_type"],
                    "rarity": full["rarity"],
                    "level_required": full["level_required"],
                    "power_score": full["power_score"],
                    "strength_bonus": full["strength_bonus"],
                    "agility_bonus": full["agility_bonus"],
                    "intellect_bonus": full["intellect_bonus"],
                    "endurance_bonus": full["endurance_bonus"],
                    "faith_bonus": full["faith_bonus"],
                    "is_tradeable": full["is_tradeable"],
                    "is_cosmetic": full["is_cosmetic"],
                    "affects_combat": full["affects_combat"],
                    "affects_economy": full["affects_economy"],
                    "affects_ranking": full["affects_ranking"],
                    "can_be_sold_for_gold": full["can_be_sold_for_gold"],
                    "can_be_sold_for_real_money": full["can_be_sold_for_real_money"],
                    "is_active": True,
                    "updated_at": now,
                },
            },
            upsert=True,
        )
    logger.info("Seeded %d dungeons and %d items", len(DUNGEON_SEED), len(ITEM_SEED))


async def seed_tester(db) -> None:
    """Idempotent dev/preview tester account. Gated by APP_ENV (never runs in prod)."""
    app_env = os.environ.get("APP_ENV", "development")
    if app_env == "production":
        logger.info("APP_ENV=production → skipping tester seed")
        return
    # Phase 5.6b: hard-fail in non-prod if the tester password is somehow blank.
    if not TESTER_PASSWORD:
        raise RuntimeError(
            "TESTER_PASSWORD is empty; set it in the environment or restore the "
            "default in app/shared/constants.py before running in non-prod."
        )
    now = _utc_now_iso()
    existing = await db.users.find_one({"email": TESTER_EMAIL})
    if existing:
        if not existing.get("is_admin"):
            await db.users.update_one(
                {"email": TESTER_EMAIL},
                {"$set": {"is_admin": True, "updated_at": now}},
            )
            logger.info("Promoted existing tester to is_admin=True")
        else:
            logger.info("Tester account already exists with is_admin=True")
        return
    await db.users.insert_one(
        {
            "id": str(uuid.uuid4()),
            "email": TESTER_EMAIL,
            "username": TESTER_USERNAME,
            "password_hash": hash_password(TESTER_PASSWORD),
            "is_admin": True,
            "created_at": now,
            "updated_at": now,
        }
    )
    logger.info("Seeded tester account: %s (is_admin=True)", TESTER_EMAIL)


async def seed_dev_clean_onboarding_account(db) -> None:
    """ROUND 16.1 Phase 4 — idempotent seed of the `clean_onboarding`
    test account used by e1_tester to validate the new-player onboarding
    flow on a guild that genuinely has no progress yet.

    Hard rules:
      * Gated by APP_ENV (never runs in production).
      * Only creates the USER row. NO guild, NO adventurers, NO inventory —
        the whole point is a pristine onboarding state.
      * Idempotent: if the user already exists we do nothing (we do NOT
        overwrite — the human tester may have logged in and seeded data
        meanwhile, and that's their state to keep).
    """
    app_env = os.environ.get("APP_ENV", "development")
    if app_env == "production":
        logger.info("APP_ENV=production → skipping clean_onboarding seed")
        return
    if not TESTER_PASSWORD:
        # We reuse the same default-password convention as the admin tester.
        # The constant is enforced non-empty by seed_tester() running above.
        raise RuntimeError(
            "TESTER_PASSWORD empty — cannot seed clean_onboarding account.")
    email = "clean_onboarding@orbus.test"
    username = "clean_onboarding"
    existing = await db.users.find_one({"email": email})
    if existing:
        logger.info("clean_onboarding account already exists (id=%s)",
                    existing.get("id"))
        return
    now = _utc_now_iso()
    await db.users.insert_one(
        {
            "id": str(uuid.uuid4()),
            "email": email,
            "username": username,
            "password_hash": hash_password(TESTER_PASSWORD),
            "is_admin": False,
            "created_at": now,
            "updated_at": now,
        }
    )
    logger.info("Seeded clean_onboarding account: %s (no guild, no roster)",
                email)


async def unbake_legacy_traits(db) -> None:
    """Phase 13: one-time migration that strips flat trait baking from
    legacy adventurers and persists a `phase13_unbaked` marker.

    Pre-Phase 13, recruitment baked flat trait modifiers directly into
    the adventurer's stat fields. From Phase 13 traits are resolved
    dynamically, so the stored stats must represent the pre-trait
    rolled values. Existing adventurers are unbaked exactly once:
    for each flat trait targeting str/agi/int/end/fai we subtract
    `modifier_value` from the stored stat, clamp to ≥ 1 (matches the
    pre-Phase-13 invariant), and set `phase13_unbaked=true`.

    Idempotent via the marker flag; safe to call on every startup.
    """
    cursor = db.adventurers.find(
        {"phase13_unbaked": {"$ne": True}}, {"_id": 0}
    )
    affected = ("strength", "agility", "intellect", "endurance", "faith")
    n_updated = 0
    async for adv in cursor:
        traits = adv.get("traits") or []
        if not traits:
            await db.adventurers.update_one(
                {"id": adv["id"]}, {"$set": {"phase13_unbaked": True}}
            )
            continue
        deltas = {s: 0 for s in affected}
        for t in traits:
            if t.get("modifier_type") == "flat" and t.get("affected_stat") in affected:
                deltas[t["affected_stat"]] += int(t.get("modifier_value", 0) or 0)
        new_stats = {}
        for s in affected:
            new_stats[s] = max(1, int(adv.get(s, 0)) - deltas[s])
        await db.adventurers.update_one(
            {"id": adv["id"]},
            {"$set": {**new_stats, "phase13_unbaked": True}},
        )
        n_updated += 1
    if n_updated:
        logger.info("Phase 13: unbaked legacy traits on %d adventurers", n_updated)


async def run_all_seeds(db) -> None:
    """Orchestrator: run all seeds in order."""
    await seed_classes_and_traits(db)
    await seed_dungeons_and_items(db)
    await seed_italian_traits(db)
    await flag_legacy_test_traits(db)
    await scrub_test_traits_from_adventurers(db)
    await seed_tester(db)
    # ROUND 16.1 Phase 4 — pristine onboarding fixture account.
    await seed_dev_clean_onboarding_account(db)
    await unbake_legacy_traits(db)
    # Phase 14.6 ROUND 3.A+3.B — Italian item catalog + crafting recipes.
    from app.seeds.seed_items_it import seed_italian_items
    from app.seeds.seed_recipes_it import seed_italian_recipes
    n_items = await seed_italian_items(db)
    n_recipes = await seed_italian_recipes(db)
    if n_items or n_recipes:
        logger.info(
            "Phase 14.6: seeded %d IT items + %d recipes (idempotent)",
            n_items, n_recipes,
        )
    # R18.6 runtime — 27 canonical classes, five singular lore items per Hall.
    # Runs after the legacy Italian seed so canonical identity and item-first
    # metadata win deterministically without replacing stable database IDs.
    from app.seeds.seed_class_hall_content import (
        seed_canonical_class_hall_content,
    )

    canonical = await seed_canonical_class_hall_content(db)
    if canonical["classes"] or canonical["items"]:
        logger.info(
            "R18.6 runtime: seeded/updated %d canonical classes + %d Hall items",
            canonical["classes"],
            canonical["items"],
        )
    # T8 tester readiness — deterministic recruitment needs playable races
    # after every isolated database reset, not only after a manual script.
    from app.scripts.round160_seed_races import seed_races

    races = await seed_races(db)
    if races["inserted"]:
        logger.info(
            "T8 runtime: seeded %d playable races (%d already present)",
            races["inserted"],
            races["skipped"],
        )
    # T6 — complete singular catalog. Legacy item rows stay available during
    # tester migration, while reward pools prefer this catalog version.
    from app.seeds.seed_t6_final_catalog import seed_t6_final_catalog

    t6_catalog = await seed_t6_final_catalog(db)
    if t6_catalog["inserted"] or t6_catalog["modified"]:
        logger.info(
            "T6 runtime: activated %d item blueprints (%d inserted, %d updated)",
            t6_catalog["total"],
            t6_catalog["inserted"],
            t6_catalog["modified"],
        )
    # Phase 14.7 ROUND 3.D — audit log indexes (no data seed).
    from app.audit.log import ensure_audit_indexes
    await ensure_audit_indexes(db)


__all__ = [
    "seed_classes_and_traits",
    "seed_dungeons_and_items",
    "seed_italian_traits",
    "flag_legacy_test_traits",
    "scrub_test_traits_from_adventurers",
    "seed_tester",
    "seed_dev_clean_onboarding_account",
    "unbake_legacy_traits",
    "run_all_seeds",
]
