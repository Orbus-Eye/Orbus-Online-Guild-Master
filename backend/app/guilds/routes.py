"""Guilds routes (Phase 5.5c + 11.3 onboarding).

Mounted under prefix `/api/guilds`.
"""
from fastapi import APIRouter, Depends

from app.core.database import db
from app.core.security import get_current_user
from app.expeditions.services import complete_due_expeditions  # noqa: F401  # still exported for legacy imports
from app.guilds.schemas import GuildCreateIn, OnboardingPatchIn
from app.guilds.services import (
    compute_dashboard_stats,
    compute_onboarding_state,
    create_guild_for_user,
    guild_public,
    patch_onboarding,
    user_guild_or_404,
)
from app.onboarding.services import ensure_starter_roster


router = APIRouter(prefix="/api/guilds", tags=["guilds"])


@router.post("", status_code=201)
async def create_guild(
    payload: GuildCreateIn, current_user: dict = Depends(get_current_user)
):
    guild_doc = await create_guild_for_user(
        db, current_user["id"], payload.name, payload.description
    )
    # ROUND 5 §I.1 — auto-pop 5 starter adventurers (idempotent).
    try:
        await ensure_starter_roster(db, guild_doc["id"], user_id=current_user["id"])
    except Exception:  # noqa: BLE001
        pass
    # ROUND 17.1 P0.3 — funnel event GUILD_CREATED (idempotente per guild).
    try:
        from app.audit.first_events import emit_first_event
        await emit_first_event(
            db, event_type="GUILD_CREATED",
            guild_id=guild_doc["id"], user_id=current_user["id"],
        )
    except Exception:  # noqa: BLE001
        pass
    return {"guild": guild_public(guild_doc)}


@router.get("/me")
async def get_my_guild(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    # ROUND 16.5.3 P0.2 — lazy sweep unificato (sostituisce il vecchio
    # complete_due_expeditions puntuale; ora include anche raid + resource).
    from app.core.activity_sweep import sweep_activities_for_guild
    await sweep_activities_for_guild(db, guild["id"])
    # Re-fetch guild after sweep (gold/level/onboarding may have changed)
    guild = await user_guild_or_404(db, current_user["id"])

    payload = guild_public(guild)
    stats = await compute_dashboard_stats(db, guild)
    payload.update(stats)
    # Phase 11.3: derive onboarding suggested step from real state + lazy migration
    onboarding = await compute_onboarding_state(db, guild, stats)
    payload.update(onboarding)
    return {"guild": payload}


@router.patch("/onboarding")
async def update_onboarding(
    payload: OnboardingPatchIn,
    current_user: dict = Depends(get_current_user),
):
    """Phase 11.3 — Update onboarding fields (step / dismissed / completed)."""
    guild = await user_guild_or_404(db, current_user["id"])
    updated_guild = await patch_onboarding(
        db,
        guild,
        step=payload.step,
        dismissed=payload.dismissed,
        completed=payload.completed,
    )
    stats = await compute_dashboard_stats(db, updated_guild)
    onboarding = await compute_onboarding_state(db, updated_guild, stats)
    return {
        "guild": guild_public(updated_guild),
        **onboarding,
    }


# ─────────────────────────────────────────────────────────────────────
# ROUND 18.3c — Migration Banner IT (player-facing informativo).
# Zero leak metadata tecnici (migration_round, previous_class_slug,
# career_history, migration_reason, migration_timestamp, role, stat).
# ─────────────────────────────────────────────────────────────────────

_R18_3C_MAPPING_IT: list[dict] = [
    {"from_it": "Ranger", "to_it": "Cacciatore di Mostri"},
    {"from_it": "Warlock", "to_it": "Cacciatore del Vuoto"},
    {"from_it": "Priest", "to_it": "Paladino"},
    {"from_it": "Berserker", "to_it": "Guerriero"},
    {"from_it": "Assassin", "to_it": "Ladro"},
]

# BYTE-EXACT PM-approved message. Do NOT modify wording.
_R18_3C_BANNER_MESSAGE_IT: str = (
    "Alcuni tuoi avventurieri sono stati riallineati alle classi "
    "canoniche di Orbus. Nessun livello, oggetto o progresso è "
    "stato perso."
)


@router.get("/me/migration-banner")
async def get_migration_banner(
    current_user: dict = Depends(get_current_user),
):
    """ROUND 18.3c — Player-facing migration banner IT.

    Returns `show=true` solo se la guild ha almeno 1 adventurer con
    `migration_round="R18.3c"` E il flag di dismiss non è impostato.
    Zero leak di field tecnici sull'adventurer o sulla migration.
    """
    guild = await user_guild_or_404(db, current_user["id"])
    guild_id = guild["id"]

    dismissed = bool(guild.get("migration_banner_r18_3c_dismissed", False))

    migrated_count = await db.adventurers.count_documents({
        "guild_id": guild_id,
        "migration_round": "R18.3c",
    })

    applicable_mappings: list[dict] = []
    if migrated_count > 0:
        source_slugs_present = await db.adventurers.distinct(
            "previous_class_slug",
            {"guild_id": guild_id, "migration_round": "R18.3c"},
        )
        source_set = set(source_slugs_present)
        _SOURCE_TO_IT = {
            "ranger": "Ranger",
            "warlock": "Warlock",
            "priest": "Priest",
            "berserker": "Berserker",
            "assassin": "Assassin",
        }
        for m in _R18_3C_MAPPING_IT:
            source_it = m["from_it"]
            source_slug = next(
                (s for s, i in _SOURCE_TO_IT.items() if i == source_it), None
            )
            if source_slug and source_slug in source_set:
                applicable_mappings.append(
                    {"from_it": m["from_it"], "to_it": m["to_it"]}
                )

    show = (migrated_count > 0) and (not dismissed)
    return {
        "show": show,
        "dismissed": dismissed,
        "migrated_count": migrated_count,
        "message_it": _R18_3C_BANNER_MESSAGE_IT,
        "mappings": applicable_mappings,
    }


@router.post("/me/migration-banner/dismiss")
async def dismiss_migration_banner(
    current_user: dict = Depends(get_current_user),
):
    """ROUND 18.3c — Persist banner dismiss server-side (guild-level)."""
    guild = await user_guild_or_404(db, current_user["id"])
    await db.guilds.update_one(
        {"id": guild["id"]},
        {"$set": {"migration_banner_r18_3c_dismissed": True}},
    )
    return {"ok": True, "dismissed": True}


# ────────────────────────────────────────────────────────────────────
# R18.Reset.2 — Fresh Start Banner UI/API
# ────────────────────────────────────────────────────────────────────

_R18_RESET1B_BANNER_MESSAGE_IT = (
    "Le gilde sono state riallineate per il nuovo inizio di Orbus. "
    "Il nome della tua gilda è stato preservato; progressi, roster e "
    "risorse sono ripartiti da zero."
)


@router.get("/me/r18-reset-banner")
async def get_r18_reset_banner(
    current_user: dict = Depends(get_current_user),
):
    """R18.Reset.2 — Player-facing fresh-start banner IT.

    Returns `show=true` solo se la guild NON ha ancora fatto dismiss del
    banner reset R18.Reset.1b. Nessun leak di metadata tecnici
    (backup path, apply_id, archive count, ecc.).
    """
    guild = await user_guild_or_404(db, current_user["id"])
    dismissed = bool(guild.get("r18_reset1b_banner_dismissed", False))
    return {
        "show": not dismissed,
        "dismissed": dismissed,
        "message_it": _R18_RESET1B_BANNER_MESSAGE_IT,
    }


@router.post("/me/r18-reset-banner/dismiss")
async def dismiss_r18_reset_banner(
    current_user: dict = Depends(get_current_user),
):
    """R18.Reset.2 — Persist fresh-start banner dismiss server-side.

    Idempotent: se il flag è già `true`, l'endpoint ritorna comunque 200
    con `dismissed=true` (nessun side-effect aggiuntivo). Modifica solo
    la guild del `current_user` via filtro `owner_user_id`.
    """
    guild = await user_guild_or_404(db, current_user["id"])
    await db.guilds.update_one(
        {"id": guild["id"], "owner_user_id": current_user["id"]},
        {"$set": {"r18_reset1b_banner_dismissed": True}},
    )
    return {"ok": True, "r18_reset1b_banner_dismissed": True}



__all__ = ["router"]
