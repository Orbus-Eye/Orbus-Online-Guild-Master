"""Persistent verification of the 27-class, item-first tester baseline."""

from __future__ import annotations

import asyncio
from collections import Counter

from motor.motor_asyncio import AsyncIOMotorClient

from app.admin.tester_journey import (
    build_tester_smoke_matrix,
    reset_tester_class_hall_journey,
)
from app.adventurers.classless import is_explicit_classless_recruit
from app.class_halls.catalog import CLASS_HALLS
from app.class_halls.collection_book import get_class_hall_collection_book
from app.class_halls.journey import (
    complete_safe_trial,
    confirm_class_hall_assignment,
    start_safe_trial,
)
from app.class_halls.item_track import (
    claim_class_hall_track_item,
    get_class_hall_item_track,
)
from app.core.indexes import create_all_indexes
from app.equipment.services import equip_item_service
from app.expeditions.services import _dispatch_expedition
from app.seeds.seed_class_hall_content import (
    CANONICAL_CLASS_HALL_ITEM_SEED,
    seed_canonical_class_hall_content,
)
from app.stats.runtime.effects.item_catalog import (
    STARTER_ITEM_EFFECT_REGISTRY,
)


MONGO_URI = "mongodb://127.0.0.1:27017"


def _classless_adventurer(index: int) -> dict:
    return {
        "id": f"real-classless-{index:02d}",
        "guild_id": "real-guild-27",
        "name": f"Recluta Persistente {index:02d}",
        "level": 1,
        "rarity": "Common",
        "is_retired": False,
        "adventurer_class_id": None,
        "class_name": None,
        "class_role": None,
        "class_proficiency": None,
        "class_slug": None,
        "canonical_class_slug": None,
        "class_hall_id": None,
        "class_hall_assigned_at": None,
        "hall_master_witness_npc": None,
        "recruit_status": "recruit_unassigned",
        "narrative_intro_shown": False,
    }


def test_seed_indexes_and_all_27_assignments_persist_exactly_once(
    class_hall_real_db,
):
    async def run() -> None:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[class_hall_real_db]
        try:
            await create_all_indexes(db)
            first_seed = await seed_canonical_class_hall_content(db)
            assert first_seed == {"classes": 27, "items": 135}

            class_ids_before = {
                row["slug"]: row["id"]
                for row in await db.adventurer_classes.find(
                    {},
                    {"_id": 0, "slug": 1, "id": 1},
                ).to_list(None)
            }
            item_ids_before = {
                row["slug"]: row["id"]
                for row in await db.items.find(
                    {},
                    {"_id": 0, "slug": 1, "id": 1},
                ).to_list(None)
            }

            await seed_canonical_class_hall_content(db)
            assert await db.adventurer_classes.count_documents({}) == 27
            assert await db.items.count_documents({}) == 135
            assert class_ids_before == {
                row["slug"]: row["id"]
                for row in await db.adventurer_classes.find(
                    {},
                    {"_id": 0, "slug": 1, "id": 1},
                ).to_list(None)
            }
            assert item_ids_before == {
                row["slug"]: row["id"]
                for row in await db.items.find(
                    {},
                    {"_id": 0, "slug": 1, "id": 1},
                ).to_list(None)
            }

            persisted_items = await db.items.find({}, {"_id": 0}).to_list(None)
            assert len(
                {item["blueprint_id"].casefold() for item in persisted_items}
            ) == 135
            assert len({item["slug"].casefold() for item in persisted_items}) == 135
            assert len(
                {item["display_name_it"].casefold() for item in persisted_items}
            ) == 135
            assert all(
                item["lore_reviewed"]
                and item["lore_source"]
                and item["flavor_text_it"]
                for item in persisted_items
            )
            assert all(
                len(item["acquisition_sources"]) == 1
                and item["acquisition_hint_it"]
                for item in persisted_items
            )
            assert sum(bool(item.get("effect_metadata")) for item in persisted_items) == 27
            assert Counter(
                item["recommended_classes"][0] for item in persisted_items
            ) == Counter(
                {
                    profile.canonical_class_slug: 5
                    for profile in CLASS_HALLS.values()
                }
            )

            item_indexes = await db.items.index_information()
            trial_indexes = await db.class_hall_trial_sessions.index_information()
            reward_indexes = await db.class_hall_reward_grants.index_information()
            assert item_indexes["items_blueprint_id_unique"]["unique"] is True
            assert trial_indexes["class_hall_trial_id_unique"]["unique"] is True
            assert trial_indexes["class_hall_trial_ttl"]["expireAfterSeconds"] == 0
            assert reward_indexes["class_hall_reward_assignment_unique"]["unique"] is True

            profiles = sorted(
                CLASS_HALLS.values(),
                key=lambda profile: profile.canonical_class_slug,
            )
            await db.adventurers.insert_many(
                [_classless_adventurer(index) for index in range(len(profiles))]
            )

            for index, profile in enumerate(profiles):
                adventurer_id = f"real-classless-{index:02d}"
                trial = await start_safe_trial(
                    db,
                    guild_id="real-guild-27",
                    adventurer_id=adventurer_id,
                    hall_id=profile.hall_id,
                    actor_user_id="real-tester",
                )
                completed = await complete_safe_trial(
                    db,
                    guild_id="real-guild-27",
                    adventurer_id=adventurer_id,
                    hall_id=profile.hall_id,
                    trial_id=trial["id"],
                    completed_steps=list(profile.trial_steps),
                    actor_user_id="real-tester",
                )
                assert completed["status"] == "completed"
                result = await confirm_class_hall_assignment(
                    db,
                    guild_id="real-guild-27",
                    adventurer_id=adventurer_id,
                    hall_id=profile.hall_id,
                    trial_id=trial["id"],
                    explicit_confirmation=True,
                    actor_user_id="real-tester",
                )
                assert result["reward"]["status"] == "delivered"
                assert result["reward"]["item_slug"] == profile.starter_item_slug

                retry = await confirm_class_hall_assignment(
                    db,
                    guild_id="real-guild-27",
                    adventurer_id=adventurer_id,
                    hall_id=profile.hall_id,
                    trial_id=trial["id"],
                    explicit_confirmation=True,
                    actor_user_id="real-tester",
                )
                assert retry["idempotent"] is True

            assigned = await db.adventurers.find(
                {"guild_id": "real-guild-27"},
                {"_id": 0},
            ).to_list(None)
            assert len(assigned) == 27
            assert {row["canonical_class_slug"] for row in assigned} == {
                profile.canonical_class_slug for profile in profiles
            }
            assert all(
                row["class_assignment_status"] == "COMMITTED"
                and row["starter_item_reward_status"] == "delivered"
                and len(row["class_assignment_history"]) == 1
                for row in assigned
            )

            assert await db.class_hall_trial_sessions.count_documents(
                {"status": "completed"}
            ) == 27
            assert await db.class_hall_reward_grants.count_documents(
                {"status": "delivered"}
            ) == 27
            for event_type in (
                "class_hall_safe_trial_started",
                "class_hall_safe_trial_completed",
                "class_hall_class_committed",
            ):
                assert await db.audit_log.count_documents(
                    {
                        "event_type": event_type,
                        "actor_guild_id": "real-guild-27",
                    }
                ) == 27
            inventory = await db.inventory_items.find(
                {"guild_id": "real-guild-27"},
                {"_id": 0},
            ).to_list(None)
            assert len(inventory) == 27
            assert len({row["item_id"] for row in inventory}) == 27
            assert all(
                row["quantity"] == 1 and len(row["class_hall_grant_ids"]) == 1
                for row in inventory
            )
        finally:
            client.close()

    asyncio.run(run())


def test_concurrent_same_hall_confirmation_never_duplicates_reward(
    class_hall_real_db,
):
    async def run() -> None:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[class_hall_real_db]
        try:
            await create_all_indexes(db)
            await seed_canonical_class_hall_content(db)
            profile = CLASS_HALLS["hall_guerriero"]
            adventurer = _classless_adventurer(99)
            adventurer["guild_id"] = "real-guild-race"
            await db.adventurers.insert_one(adventurer)

            trial = await start_safe_trial(
                db,
                guild_id="real-guild-race",
                adventurer_id=adventurer["id"],
                hall_id=profile.hall_id,
                actor_user_id="race-tester",
            )
            await complete_safe_trial(
                db,
                guild_id="real-guild-race",
                adventurer_id=adventurer["id"],
                hall_id=profile.hall_id,
                trial_id=trial["id"],
                completed_steps=list(profile.trial_steps),
                actor_user_id="race-tester",
            )

            async def confirm() -> dict:
                return await confirm_class_hall_assignment(
                    db,
                    guild_id="real-guild-race",
                    adventurer_id=adventurer["id"],
                    hall_id=profile.hall_id,
                    trial_id=trial["id"],
                    explicit_confirmation=True,
                    actor_user_id="race-tester",
                )

            results = await asyncio.gather(confirm(), confirm())
            assert all(result["reward"]["status"] == "delivered" for result in results)
            stored = await db.adventurers.find_one(
                {"id": adventurer["id"]},
                {"_id": 0},
            )
            assert stored["canonical_class_slug"] == "guerriero"
            assert len(stored["class_assignment_history"]) == 1

            inventory = await db.inventory_items.find(
                {"guild_id": "real-guild-race"},
                {"_id": 0},
            ).to_list(None)
            assert len(inventory) == 1
            assert inventory[0]["quantity"] == 1
            assert len(inventory[0]["class_hall_grant_ids"]) == 1
            assert await db.class_hall_reward_grants.count_documents({}) == 1
        finally:
            client.close()

    asyncio.run(run())


def test_static_seed_count_matches_persisted_contract():
    assert len(CANONICAL_CLASS_HALL_ITEM_SEED) == 135


def test_all_five_warrior_items_have_reachable_exactly_once_track(
    class_hall_real_db,
):
    async def run() -> None:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[class_hall_real_db]
        try:
            await create_all_indexes(db)
            await seed_canonical_class_hall_content(db)
            profile = CLASS_HALLS["hall_guerriero"]
            adventurer = _classless_adventurer(77)
            adventurer["guild_id"] = "real-guild-track"
            await db.adventurers.insert_one(adventurer)

            trial = await start_safe_trial(
                db,
                guild_id=adventurer["guild_id"],
                adventurer_id=adventurer["id"],
                hall_id=profile.hall_id,
                actor_user_id="track-tester",
            )
            await complete_safe_trial(
                db,
                guild_id=adventurer["guild_id"],
                adventurer_id=adventurer["id"],
                hall_id=profile.hall_id,
                trial_id=trial["id"],
                completed_steps=list(profile.trial_steps),
                actor_user_id="track-tester",
            )
            await confirm_class_hall_assignment(
                db,
                guild_id=adventurer["guild_id"],
                adventurer_id=adventurer["id"],
                hall_id=profile.hall_id,
                trial_id=trial["id"],
                explicit_confirmation=True,
                actor_user_id="track-tester",
            )

            track = await get_class_hall_item_track(
                db,
                guild_id=adventurer["guild_id"],
                adventurer_id=adventurer["id"],
                hall_id=profile.hall_id,
            )
            assert [row["order"] for row in track["items"]] == [0, 1, 2, 3, 4]
            assert [row["status"] for row in track["items"]] == [
                "claimed",
                "locked",
                "locked",
                "locked",
                "locked",
            ]

            signature_id = track["items"][0]["item"]["id"]
            await db.equipped_items.insert_one(
                {
                    "id": "track-equipped-signature",
                    "guild_id": adventurer["guild_id"],
                    "adventurer_id": adventurer["id"],
                    "item_id": signature_id,
                    "slot": "weapon",
                }
            )
            track = await get_class_hall_item_track(
                db,
                guild_id=adventurer["guild_id"],
                adventurer_id=adventurer["id"],
                hall_id=profile.hall_id,
            )
            first_extra_slug = track["items"][1]["item"]["slug"]
            assert track["items"][1]["status"] == "claimable"

            async def claim_first_extra() -> dict:
                return await claim_class_hall_track_item(
                    db,
                    guild_id=adventurer["guild_id"],
                    adventurer_id=adventurer["id"],
                    hall_id=profile.hall_id,
                    item_slug=first_extra_slug,
                    actor_user_id="track-tester",
                )

            concurrent = await asyncio.gather(
                claim_first_extra(),
                claim_first_extra(),
            )
            assert sorted(
                result["reward"]["idempotent"] for result in concurrent
            ) == [False, True]

            await db.adventurers.update_one(
                {"id": adventurer["id"]},
                {"$set": {"level": 2}},
            )
            await db.expeditions.insert_many(
                [
                    {
                        "id": f"track-exp-{index}",
                        "guild_id": adventurer["guild_id"],
                        "status": "completed",
                    }
                    for index in range(3)
                ]
            )
            await db.expedition_members.insert_many(
                [
                    {
                        "id": f"track-member-{index}",
                        "expedition_id": f"track-exp-{index}",
                        "adventurer_id": adventurer["id"],
                    }
                    for index in range(3)
                ]
            )
            track = await get_class_hall_item_track(
                db,
                guild_id=adventurer["guild_id"],
                adventurer_id=adventurer["id"],
                hall_id=profile.hall_id,
            )
            assert [row["status"] for row in track["items"]] == [
                "claimed",
                "claimed",
                "claimable",
                "claimable",
                "claimable",
            ]
            for entry in track["items"][2:]:
                result = await claim_class_hall_track_item(
                    db,
                    guild_id=adventurer["guild_id"],
                    adventurer_id=adventurer["id"],
                    hall_id=profile.hall_id,
                    item_slug=entry["item"]["slug"],
                    actor_user_id="track-tester",
                )
                assert result["reward"]["status"] == "delivered"

            final_track = await get_class_hall_item_track(
                db,
                guild_id=adventurer["guild_id"],
                adventurer_id=adventurer["id"],
                hall_id=profile.hall_id,
            )
            assert final_track["claimed_count"] == 5
            assert all(row["status"] == "claimed" for row in final_track["items"])
            inventory = await db.inventory_items.find(
                {"guild_id": adventurer["guild_id"]},
                {"_id": 0},
            ).to_list(None)
            assert len(inventory) == 5
            assert len({row["item_id"] for row in inventory}) == 5
            assert all(row["quantity"] == 1 for row in inventory)
            assert await db.class_hall_item_grants.count_documents(
                {"status": "delivered"}
            ) == 4
        finally:
            client.close()

    asyncio.run(run())


def test_tester_reset_preserves_history_and_creates_five_classless_starters(
    class_hall_real_db,
):
    async def run() -> None:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[class_hall_real_db]
        try:
            await create_all_indexes(db)
            await seed_canonical_class_hall_content(db)
            user = {"id": "reset-user", "email": "reset@orbus.test"}
            guild = {
                "id": "reset-guild",
                "owner_user_id": user["id"],
                "name": "Gilda Nuovo Viaggio",
            }
            await db.users.insert_one(dict(user))
            await db.guilds.insert_one(dict(guild))

            classless = _classless_adventurer(90)
            classless.update(
                {
                    "id": "reset-classless",
                    "guild_id": guild["id"],
                    "is_available": True,
                }
            )
            assigned = _classless_adventurer(91)
            assigned.update(
                {
                    "id": "reset-assigned",
                    "guild_id": guild["id"],
                    "is_available": True,
                    "adventurer_class_id": "class-guerriero",
                    "class_name": "Guerriero",
                    "class_role": "Tank",
                    "class_proficiency": "Warrior",
                    "class_slug": "guerriero",
                    "canonical_class_slug": "guerriero",
                    "class_hall_id": "hall_guerriero",
                    "recruit_status": "class_assigned",
                }
            )
            await db.adventurers.insert_many([classless, assigned])

            signature = await db.items.find_one(
                {"slug": "iron_sword"},
                {"_id": 0, "id": 1},
            )
            await db.inventory_items.insert_one(
                {
                    "id": "reset-inventory",
                    "guild_id": guild["id"],
                    "item_id": signature["id"],
                    "quantity": 1,
                    "reserved_qty": 1,
                }
            )
            await db.equipped_items.insert_one(
                {
                    "id": "reset-equipped",
                    "guild_id": guild["id"],
                    "adventurer_id": assigned["id"],
                    "item_id": signature["id"],
                    "slot": "weapon",
                }
            )

            result = await reset_tester_class_hall_journey(
                db,
                user=user,
                guild=guild,
                snapshot_id="reset-snapshot",
            )
            assert result["archived_adventurers"] == 2
            assert result["equipment_released"] == 1
            assert result["created_classless_adventurers"] == 5
            assert result["history_preserved"] is True

            old = await db.adventurers.find(
                {"id": {"$in": ["reset-classless", "reset-assigned"]}},
                {"_id": 0},
            ).to_list(None)
            assert len(old) == 2
            assert all(
                row["is_retired"] is True and row["archived"] is True
                for row in old
            )
            active = await db.adventurers.find(
                {
                    "guild_id": guild["id"],
                    "is_retired": {"$ne": True},
                    "retired": {"$ne": True},
                    "archived": {"$ne": True},
                },
                {"_id": 0},
            ).to_list(None)
            assert len(active) == 5
            assert all(is_explicit_classless_recruit(row) for row in active)
            assert all(row["is_starter"] is True for row in active)
            assert await db.equipped_items.count_documents(
                {"guild_id": guild["id"]}
            ) == 0
            inventory = await db.inventory_items.find_one(
                {"id": "reset-inventory"},
                {"_id": 0},
            )
            assert inventory["quantity"] == 1
            assert inventory["reserved_qty"] == 0

            matrix = await build_tester_smoke_matrix(
                db,
                user=user,
                guild=guild,
            )
            assert matrix["ready_for_tester_slice"] is True
            assert matrix["summary"]["classless_adventurers"] == 5
            assert matrix["summary"]["invalid_class_states"] == 0
            long_term = next(
                check
                for check in matrix["checks"]
                if check["key"] == "long_term_item_catalog"
            )
            assert long_term["ok"] is False
            assert long_term["blocking"] is False
        finally:
            client.close()

    asyncio.run(run())


def test_all_27_classes_equip_their_signature_and_enter_expeditions(
    class_hall_real_db,
):
    async def run() -> None:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[class_hall_real_db]
        try:
            await create_all_indexes(db)
            await seed_canonical_class_hall_content(db)
            guild = {
                "id": "all-classes-expedition-guild",
                "owner_user_id": "all-classes-tester",
                "name": "Gilda delle Ventisette Vie",
                "level": 1,
                "gold": 100,
                "max_team_power_ever": 0,
            }
            await db.guilds.insert_one(dict(guild))
            await db.users.insert_one(
                {
                    "id": guild["owner_user_id"],
                    "email": "all-classes@orbus.test",
                    "is_test_user": True,
                }
            )
            await db.dungeons.insert_one(
                {
                    "id": "real-goblin-warrens",
                    "slug": "goblin-warrens",
                    "name": "Cunicoli del Primo Collaudo",
                    "description": "Fixture locale per le ventisette vie.",
                    "is_active": True,
                    "required_team_size": 3,
                    "required_level": 1,
                    "recommended_power": 1,
                    "base_duration_seconds": 60,
                    "difficulty": 1,
                }
            )

            profiles = sorted(
                CLASS_HALLS.values(),
                key=lambda profile: profile.canonical_class_slug,
            )
            recruits = []
            for index in range(len(profiles)):
                recruit = _classless_adventurer(200 + index)
                recruit.update(
                    {
                        "id": f"all-classes-{index:02d}",
                        "guild_id": guild["id"],
                        "level": 5,
                        "is_available": True,
                        "strength": 5,
                        "agility": 5,
                        "intellect": 5,
                        "endurance": 5,
                        "faith": 5,
                        "stamina": 100,
                        "morale": 100,
                        "traits": [],
                    }
                )
                recruits.append(recruit)
            await db.adventurers.insert_many(recruits)

            assigned_ids: list[str] = []
            signature_names: set[str] = set()
            for index, profile in enumerate(profiles):
                adventurer_id = recruits[index]["id"]
                trial = await start_safe_trial(
                    db,
                    guild_id=guild["id"],
                    adventurer_id=adventurer_id,
                    hall_id=profile.hall_id,
                    actor_user_id=guild["owner_user_id"],
                )
                await complete_safe_trial(
                    db,
                    guild_id=guild["id"],
                    adventurer_id=adventurer_id,
                    hall_id=profile.hall_id,
                    trial_id=trial["id"],
                    completed_steps=list(profile.trial_steps),
                    actor_user_id=guild["owner_user_id"],
                )
                assignment = await confirm_class_hall_assignment(
                    db,
                    guild_id=guild["id"],
                    adventurer_id=adventurer_id,
                    hall_id=profile.hall_id,
                    trial_id=trial["id"],
                    explicit_confirmation=True,
                    actor_user_id=guild["owner_user_id"],
                )
                item = await db.items.find_one(
                    {"id": assignment["reward"]["item_id"]},
                    {"_id": 0},
                )
                slot = item.get("slot_type") or item.get("item_type")
                equipped = await equip_item_service(
                    db,
                    guild,
                    adventurer_id,
                    item["id"],
                    slot,
                )
                assert equipped["slots"][slot]["item"]["id"] == item["id"]
                assert equipped["equipment_power"] > 0
                assigned_ids.append(adventurer_id)
                signature_names.add(
                    item.get("display_name_it") or item["name"]
                )

            assert len(assigned_ids) == 27
            assert len(signature_names) == 27
            collection = await get_class_hall_collection_book(
                db,
                guild_id=guild["id"],
            )
            assert collection["owned_count"] == 27
            assert collection["total_count"] == 135
            assert collection["completed_halls"] == 0
            assert len(collection["halls"]) == 27
            assert all(hall["owned_count"] == 1 for hall in collection["halls"])
            assert all(
                hall["equipped_count"] == 1
                for hall in collection["halls"]
            )
            expedition_ids = []
            for offset in range(0, len(assigned_ids), 3):
                result = await _dispatch_expedition(
                    db,
                    guild=guild,
                    dungeon_id="real-goblin-warrens",
                    adventurer_ids=assigned_ids[offset:offset + 3],
                )
                assert result["expedition"]["status"] == "in_progress"
                assert len(result["members"]) == 3
                assert all(
                    len(member["equipment_snapshot"]) == 1
                    for member in result["members"]
                )
                assert result["expedition"]["item_effect_power_bonus"] == 6
                for member in result["members"]:
                    assert member["item_effect_power_bonus"] == 2
                    assert len(member["item_effects_snapshot"]) == 1
                    profile_index = int(
                        member["adventurer_id"].rsplit("-", 1)[1]
                    )
                    profile = profiles[profile_index]
                    definition = STARTER_ITEM_EFFECT_REGISTRY.get(
                        profile.starter_effect_id,
                        1,
                    )
                    assert definition is not None
                    effect = member["item_effects_snapshot"][0]
                    assert effect["effect_id"] == profile.starter_effect_id
                    assert effect["target_stat"] == definition.target_key
                    assert effect["magnitude"] == definition.magnitude
                    assert effect["summary_it"]
                    assert effect["lore_source"]
                expedition_ids.append(result["expedition"]["id"])

            assert len(expedition_ids) == 9
            assert len(set(expedition_ids)) == 9
            assert await db.expedition_members.count_documents(
                {"expedition_id": {"$in": expedition_ids}}
            ) == 27
            assert await db.adventurers.count_documents(
                {
                    "id": {"$in": assigned_ids},
                    "is_available": False,
                }
            ) == 27
        finally:
            client.close()

    asyncio.run(run())
