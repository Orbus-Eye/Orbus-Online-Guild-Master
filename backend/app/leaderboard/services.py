"""Leaderboard services (Phase 9.1).

`get_guild_leaderboard(db, limit, offset)` returns a paginated, ranked list
of guilds sorted by `max_team_power_ever` (then level → reputation →
created_at). Privacy-preserving: never exposes `owner_user_id`, `email`,
`is_admin`, `password_hash`, or any other sensitive field — only a fixed
whitelist via `LeaderboardEntryOut`.

Performance: a single aggregation over `expeditions` covers
`total_completed` + `success_dungeon_ids` for the whole page, avoiding the
N+1 query pattern that `compute_dashboard_stats` uses for a single guild.
"""
from typing import Optional

from fastapi import HTTPException


_MAX_LIMIT = 100
_MAX_OFFSET = 1000


async def get_guild_leaderboard(
    db, limit: int = 50, offset: int = 0
) -> dict:
    """Return a paginated leaderboard. Validates inputs (400 on out-of-range)."""
    # Strict validation (HTTPException 400 before any DB I/O)
    if not isinstance(limit, int) or limit < 1 or limit > _MAX_LIMIT:
        raise HTTPException(
            status_code=400,
            detail=f"limit must be an integer in [1, {_MAX_LIMIT}]",
        )
    if not isinstance(offset, int) or offset < 0 or offset > _MAX_OFFSET:
        raise HTTPException(
            status_code=400,
            detail=f"offset must be an integer in [0, {_MAX_OFFSET}]",
        )

    # Phase 14.3 — exclude guilds owned by `is_test_user=True` accounts from
    # the public leaderboard. The flag is additive (absent ≡ False), so this
    # is a no-op when no user has been flagged yet.
    test_owner_ids = await db.users.distinct("id", {"is_test_user": True})
    base_filter: dict = (
        {"owner_user_id": {"$nin": test_owner_ids}} if test_owner_ids else {}
    )

    total = await db.guilds.count_documents(base_filter)

    # Sort: peak power desc → level desc → reputation desc → created_at asc.
    # Tie-break by `created_at` ascending means older guilds appear earlier
    # when all other fields are identical (rewards consistency / longevity).
    guilds = await (
        db.guilds.find(
            base_filter,
            {
                "_id": 0,
                "id": 1,
                "name": 1,
                "level": 1,
                "reputation": 1,
                "max_team_power_ever": 1,
                "created_at": 1,
            },
        )
        .sort(
            [
                ("max_team_power_ever", -1),
                ("level", -1),
                ("reputation", -1),
                ("created_at", 1),
            ]
        )
        .skip(offset)
        .limit(limit)
        .to_list(limit)
    )

    if not guilds:
        return {"total": total, "limit": limit, "offset": offset, "entries": []}

    guild_ids = [g["id"] for g in guilds]

    # Single aggregation: per-guild completed count + set of successful dungeon ids.
    # `$$REMOVE` filters out non-success expeditions from the set without
    # losing the count (handled by separate $sum).
    pipeline = [
        {"$match": {"guild_id": {"$in": guild_ids}, "status": "completed"}},
        {
            "$group": {
                "_id": "$guild_id",
                "total_completed": {"$sum": 1},
                "success_dungeon_ids": {
                    "$addToSet": {
                        "$cond": [
                            {"$eq": ["$result_summary", "Success"]},
                            "$dungeon_id",
                            "$$REMOVE",
                        ]
                    }
                },
            }
        },
    ]
    agg_map: dict[str, dict] = {}
    async for row in db.expeditions.aggregate(pipeline):
        agg_map[row["_id"]] = row

    # Batch-load any dungeon referenced as a success across the visible page.
    all_dungeon_ids: set[str] = set()
    for row in agg_map.values():
        all_dungeon_ids.update(row.get("success_dungeon_ids", []))

    dungeons_by_id: dict[str, dict] = {}
    if all_dungeon_ids:
        async for d in db.dungeons.find(
            {"id": {"$in": list(all_dungeon_ids)}},
            {"_id": 0, "id": 1, "slug": 1, "difficulty": 1},
        ):
            dungeons_by_id[d["id"]] = d

    def _highest_slug(success_ids: list[str]) -> Optional[str]:
        ranked = sorted(
            (
                dungeons_by_id[did]
                for did in success_ids
                if did in dungeons_by_id
            ),
            key=lambda d: d.get("difficulty", 0),
            reverse=True,
        )
        return ranked[0]["slug"] if ranked else None

    entries = []
    for i, g in enumerate(guilds):
        agg_row = agg_map.get(g["id"], {})
        entries.append(
            {
                "rank": offset + i + 1,
                "guild_id": g["id"],
                "guild_name": g["name"],
                "level": int(g.get("level", 1)),
                "reputation": int(g.get("reputation", 0)),
                "max_team_power_ever": int(g.get("max_team_power_ever", 0)),
                "highest_dungeon_slug": _highest_slug(
                    agg_row.get("success_dungeon_ids", [])
                ),
                "total_expeditions_completed": int(
                    agg_row.get("total_completed", 0)
                ),
                "created_at": g["created_at"],
            }
        )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "entries": entries,
    }


__all__ = ["get_guild_leaderboard", "get_raids_leaderboard"]


async def get_raids_leaderboard(
    db, limit: int = 20, offset: int = 0
) -> dict:
    """Phase 19 — Public raid leaderboard ranked by `max_raid_score`.

    Privacy-preserving: filters out `is_test_user=True` owners (same gate as
    `get_guild_leaderboard`). Returns one row per (guild, raid_dungeon_slug)
    showing the best raid score for that raid attempt.

    Sort: max_raid_score desc → completed_at asc (older wins on tie).
    """
    # Strict validation
    if not isinstance(limit, int) or limit < 1 or limit > _MAX_LIMIT:
        raise HTTPException(
            status_code=400,
            detail=f"limit must be an integer in [1, {_MAX_LIMIT}]",
        )
    if not isinstance(offset, int) or offset < 0 or offset > _MAX_OFFSET:
        raise HTTPException(
            status_code=400,
            detail=f"offset must be an integer in [0, {_MAX_OFFSET}]",
        )

    # Privacy filter: exclude raids whose guild is owned by a test user.
    test_owner_ids = await db.users.distinct("id", {"is_test_user": True})
    test_guild_ids: list[str] = []
    if test_owner_ids:
        test_guild_ids = await db.guilds.distinct(
            "id", {"owner_user_id": {"$in": test_owner_ids}}
        )

    match: dict = {"status": "completed", "raid_score": {"$gt": 0}}
    if test_guild_ids:
        match["guild_id"] = {"$nin": test_guild_ids}

    # Per (guild, raid_dungeon_slug) best raid_score.
    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": {"guild_id": "$guild_id", "raid_dungeon_slug": "$raid_dungeon_slug"},
                "max_raid_score": {"$max": "$raid_score"},
                "best_outcome": {"$first": "$outcome"},
                "completed_at": {"$max": "$completed_at"},
            }
        },
        {"$sort": {"max_raid_score": -1, "completed_at": 1}},
    ]

    # Count total distinct (guild, slug) keys
    all_rows = await db.raids.aggregate(pipeline).to_list(length=None)
    total = len(all_rows)

    page = all_rows[offset: offset + limit]

    # Resolve guild names in a single query
    guild_ids = list({r["_id"]["guild_id"] for r in page})
    name_map: dict[str, str] = {}
    if guild_ids:
        async for g in db.guilds.find(
            {"id": {"$in": guild_ids}},
            {"_id": 0, "id": 1, "name": 1},
        ):
            name_map[g["id"]] = g["name"]

    entries = []
    for i, r in enumerate(page):
        gid = r["_id"]["guild_id"]
        entries.append({
            "rank": offset + i + 1,
            "guild_id": gid,
            "guild_name": name_map.get(gid, "Unknown"),
            "raid_dungeon_slug": r["_id"]["raid_dungeon_slug"],
            "max_raid_score": int(r["max_raid_score"]),
            "outcome": r.get("best_outcome"),
            "completed_at": r.get("completed_at"),
        })

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "entries": entries,
    }
