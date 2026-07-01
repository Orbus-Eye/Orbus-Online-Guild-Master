"""ROUND 15 — Phase 3 / Task 9 — Seed 100 achievement catalog.

Idempotent upsert on `slug`. Cosmetic rewards only — the seed validates
`reward_type` ∈ {xp_points, xp_points_title, xp_points_badge,
xp_points_frame} and refuses to write any entry whose reward payload
references gameplay-affecting fields (gold/xp_adv/drop_boost/...).

Run:
    cd /app/backend
    python3 -m app.scripts.round15_seed_achievements
    python3 -m app.scripts.round15_seed_achievements --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import os
import uuid
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

from app.achievements.engine import ALLOWED_REWARD_TYPES


CATEGORIES = (
    "primi_passi", "roster", "dungeon", "raid", "equipaggiamento",
    "classi_stats", "territorio", "crafting", "economia",
    "pvp_stagioni", "leaderboard", "consorzi", "lore", "meta_beta",
)

# Forbidden reward payload keys — defence against P2W creep.
FORBIDDEN_PAYLOAD_KEYS = frozenset({
    "gold", "gold_reward", "adventurer_xp", "adv_xp",
    "drop_boost", "xp_boost", "boost_pct",
    "item_slug", "material_slug", "recruit_slot", "expedition_slot",
})


# Helper: build a single catalog entry with sane defaults.
def _ach(
    slug: str, category: str, name_it: str, description_it: str,
    *, trigger: str, target: int = 1, points: int = 5, xp: int = 50,
    reward_type: str = "xp_points", reward_payload: dict | None = None,
    is_hidden: bool = False, display_order: int = 999,
    name_en: str | None = None, description_en: str | None = None,
) -> dict:
    if reward_type not in ALLOWED_REWARD_TYPES:
        raise ValueError(f"reward_type {reward_type!r} not whitelisted")
    payload = reward_payload or {}
    bad = set(payload.keys()) & FORBIDDEN_PAYLOAD_KEYS
    if bad:
        raise ValueError(f"reward_payload contains forbidden keys: {bad}")
    return {
        "slug": slug, "category": category,
        "name_it": name_it, "name_en": name_en,
        "description_it": description_it, "description_en": description_en,
        "points": int(points), "guild_xp_reward": int(xp),
        "reward_type": reward_type, "reward_payload": payload,
        "is_repeatable": False, "repeat_limit": None,
        "is_hidden": is_hidden,
        "spoiler_level": "hidden" if is_hidden else "public",
        "trigger_event": trigger,
        "progress_target": int(target),
        "display_order": int(display_order),
        "is_active": True,
    }


# ─── 100 achievement catalog ────────────────────────────────────────────
def build_catalog() -> list[dict]:
    rows: list[dict] = []
    # ===== Primi Passi (8) =====
    rows += [
        _ach("il-primo-passo", "primi_passi", "Il Primo Passo",
             "Crea la tua prima gilda nelle terre di Orbus.",
             trigger="guild_created", target=1, points=5, xp=100,
             reward_type="xp_points_title",
             reward_payload={"title_it": "Il Primo Passo"}, display_order=1),
        _ach("prima-recluta", "primi_passi", "Prima Recluta",
             "Recluta il tuo primo avventuriero.",
             trigger="adventurer_recruited", target=1, xp=80, display_order=2),
        _ach("primo-dungeon", "primi_passi", "Primo Dungeon",
             "Completa la tua prima spedizione con successo.",
             trigger="dungeon_completed", target=1, xp=120, display_order=3),
        _ach("primo-equip", "primi_passi", "Primo Equipaggiamento",
             "Equipaggia il primo oggetto a un tuo avventuriero.",
             trigger="item_equipped", target=1, xp=50, display_order=4),
        _ach("primo-acquisto-mercato", "primi_passi", "Primo Acquisto",
             "Effettua il primo acquisto al mercato.",
             trigger="market_purchase", target=1, xp=40, display_order=5),
        _ach("primo-craft", "primi_passi", "Primo Crafting",
             "Forgia il tuo primo oggetto.",
             trigger="item_crafted", target=1, xp=60, display_order=6),
        _ach("primo-pvp", "primi_passi", "Primo Duello",
             "Concludi la tua prima partita PvP.",
             trigger="pvp_match_completed", target=1, xp=70, display_order=7),
        _ach("primo-raid", "primi_passi", "Primo Raid",
             "Conduci la tua gilda al primo raid completato.",
             trigger="raid_completed", target=1, xp=150, display_order=8),
    ]

    # ===== Roster (10) =====
    rows += [
        _ach(f"reclute-{n}", "roster", f"{n} Reclute",
             f"Recluta in totale {n} avventurieri.",
             trigger="adventurer_recruited", target=n, xp=int(40 + n * 0.5),
             points=5 + (1 if n >= 50 else 0), display_order=10 + i)
        for i, n in enumerate([5, 10, 20, 35, 50, 75, 100, 150, 200, 300])
    ]

    # ===== Dungeon (12) =====
    dungeon_levels = [5, 10, 25, 50, 100, 150, 200, 300, 500, 750, 1000]
    rows += [
        _ach(f"dungeon-completati-{n}", "dungeon", f"{n} Dungeon completati",
             f"Conduci la gilda alla vittoria in {n} spedizioni.",
             trigger="dungeon_completed", target=n,
             xp=80 + n * 2, points=5,
             display_order=20 + i)
        for i, n in enumerate(dungeon_levels)
    ]
    rows.append(_ach(
        "esploratore-instancabile", "dungeon", "Esploratore Instancabile",
        "Completa 25 spedizioni in totale.",
        trigger="dungeon_completed", target=25, xp=200, points=10,
        reward_type="xp_points_badge",
        reward_payload={"badge_slug": "trailblazer"}, display_order=32))

    # ===== Raid (8) =====
    raid_levels = [1, 3, 5, 10, 15, 25, 50]
    rows += [
        _ach(f"raid-completati-{n}", "raid", f"{n} Raid completati",
             f"Completa {n} raid epici.",
             trigger="raid_completed", target=n,
             xp=200 + n * 20, points=10, display_order=40 + i)
        for i, n in enumerate(raid_levels)
    ]
    rows.append(_ach(
        "veterano-dei-raid", "raid", "Veterano dei Raid",
        "Completa 20 raid in totale (ricompensa cosmetica).",
        trigger="raid_completed", target=20, xp=600, points=20,
        reward_type="xp_points_frame",
        reward_payload={"frame_slug": "raid_veteran"}, display_order=48))

    # ===== Equipaggiamento (10) =====
    equip_levels = [5, 10, 25, 50, 100, 200, 350, 500, 750, 1000]
    rows += [
        _ach(f"equip-{n}", "equipaggiamento",
             f"{n} oggetti equipaggiati",
             f"Equipaggia in totale {n} oggetti ai tuoi avventurieri.",
             trigger="item_equipped", target=n,
             xp=50 + n, points=5, display_order=50 + i)
        for i, n in enumerate(equip_levels)
    ]

    # ===== Classi e Stats (12: 8 classi + 2 milestone + 2 disenchant/material) =====
    class_slugs = [
        ("warrior", "Guerriero"), ("rogue", "Ladro"),
        ("mage", "Mago"), ("priest", "Sacerdote"),
        ("ranger", "Ranger"), ("paladin", "Paladino"),
        ("druid", "Druido"), ("bard", "Bardo"),
    ]
    for i, (slug, name) in enumerate(class_slugs):
        rows.append(_ach(
            f"specialista-{slug}", "classi_stats",
            f"Specialista — {name}",
            f"Equipaggia 25 oggetti su avventurieri di classe {name}.",
            trigger="item_equipped", target=25, xp=120, points=6,
            display_order=60 + i,
        ))
    rows += [
        _ach("team-bilanciato", "classi_stats", "Team Bilanciato",
             "Recluta avventurieri da almeno 6 classi diverse.",
             trigger="adventurer_recruited", target=6, xp=150, points=8,
             reward_type="xp_points_title",
             reward_payload={"title_it": "Stratega del Roster"}, display_order=68),
        _ach("primary-stat-sopra-soglia", "classi_stats",
             "Statistica Primaria",
             "Mantieni la statistica primaria di un avventuriero sopra soglia per 10 spedizioni.",
             trigger="dungeon_completed", target=10, xp=180, points=10,
             display_order=69),
        _ach("disenchant-50", "classi_stats", "Riciclatore",
             "Distruggi 50 oggetti per recuperarne i materiali.",
             trigger="item_disenchanted", target=50, xp=120, points=5, display_order=70),
        _ach("materiali-100", "classi_stats", "Collezionista di Materiali",
             "Acquista 100 materiali dal mercato.",
             trigger="material_purchased", target=100, xp=120, points=5, display_order=71),
    ]

    # ===== Territorio (8) =====
    territory_levels = [1, 3, 5, 8, 12, 20, 30, 50]
    rows += [
        _ach(f"territorio-{n}", "territorio",
             f"{n} edifici potenziati",
             f"Potenzia in totale {n} strutture del tuo territorio.",
             trigger="territory_upgraded", target=n, xp=100 + n * 5,
             display_order=80 + i)
        for i, n in enumerate(territory_levels)
    ]

    # ===== Crafting (8) =====
    craft_levels = [1, 5, 10, 25, 50, 100, 200, 350]
    rows += [
        _ach(f"crafting-{n}", "crafting",
             f"{n} oggetti forgiati",
             f"Forgia un totale di {n} oggetti.",
             trigger="item_crafted", target=n, xp=60 + n * 2,
             display_order=90 + i)
        for i, n in enumerate(craft_levels)
    ]

    # ===== Economia (6) =====
    rows += [
        _ach("acquisto-mercato-10", "economia", "Mercante Esperto",
             "10 acquisti al mercato.", trigger="market_purchase",
             target=10, xp=80, display_order=100),
        _ach("acquisto-mercato-50", "economia", "Mercante Veterano",
             "50 acquisti al mercato.", trigger="market_purchase",
             target=50, xp=200, display_order=101),
        _ach("acquisto-mercato-200", "economia", "Mercante Leggendario",
             "200 acquisti al mercato.", trigger="market_purchase",
             target=200, xp=500, points=10, display_order=102),
        _ach("asta-vendita-1", "economia", "Prima Asta",
             "Vendi un oggetto all'asta.", trigger="auction_sale",
             target=1, xp=60, display_order=103),
        _ach("asta-vendita-25", "economia", "Banditore",
             "25 oggetti venduti all'asta.", trigger="auction_sale",
             target=25, xp=300, points=10, display_order=104),
        _ach("asta-acquisto-25", "economia", "Cacciatore d'aste",
             "25 oggetti acquistati all'asta.", trigger="auction_purchase",
             target=25, xp=300, points=10, display_order=105),
    ]

    # ===== PvP / Stagioni (8) =====
    rows += [
        _ach(f"pvp-{n}-vittorie", "pvp_stagioni", f"{n} duelli PvP",
             f"Completa {n} partite PvP.", trigger="pvp_match_completed",
             target=n, xp=80 + n * 5, points=5, display_order=110 + i)
        for i, n in enumerate([5, 15, 30, 60, 100, 200])
    ]
    rows += [
        _ach("lega-bronzo", "pvp_stagioni", "Lega Bronzo",
             "Raggiungi la lega Bronzo nella stagione corrente.",
             trigger="season_league_reached", target=1, xp=100,
             reward_type="xp_points_badge",
             reward_payload={"badge_slug": "league_bronze"}, display_order=116),
        _ach("lega-argento", "pvp_stagioni", "Lega Argento",
             "Raggiungi la lega Argento.",
             trigger="season_league_reached", target=2, xp=250, points=10,
             reward_type="xp_points_badge",
             reward_payload={"badge_slug": "league_silver"}, display_order=117),
    ]

    # ===== Leaderboard (5) =====
    rows += [
        _ach("lb-top-100", "leaderboard", "Top 100",
             "Entra nei primi 100 di una classifica pubblica.",
             trigger="leaderboard_rank_reached", target=1, xp=120, display_order=120,
             reward_type="xp_points_title",
             reward_payload={"title_it": "Tra i 100"}),
        _ach("lb-top-50", "leaderboard", "Top 50",
             "Entra nei primi 50 di una classifica pubblica.",
             trigger="leaderboard_rank_reached", target=2, xp=200, points=10, display_order=121),
        _ach("lb-top-10", "leaderboard", "Top 10",
             "Entra nei primi 10 di una classifica pubblica.",
             trigger="leaderboard_rank_reached", target=3, xp=400, points=15,
             reward_type="xp_points_frame",
             reward_payload={"frame_slug": "top10_aura"}, display_order=122),
        _ach("lb-top-3", "leaderboard", "Top 3",
             "Entra nei primi 3 di una classifica pubblica.",
             trigger="leaderboard_rank_reached", target=4, xp=800, points=25, display_order=123),
        _ach("lb-first", "leaderboard", "Primo Posto",
             "Raggiungi la vetta di una classifica pubblica.",
             trigger="leaderboard_rank_reached", target=5, xp=1500, points=50,
             reward_type="xp_points_title",
             reward_payload={"title_it": "Vetta di Orbus"}, display_order=124),
    ]

    # ===== Consorzi (3) =====
    rows += [
        _ach("consorzio-membro", "consorzi", "Parte di un Consorzio",
             "Entra a far parte del tuo primo consorzio.",
             trigger="consortium_joined", target=1, xp=120, display_order=130),
        _ach("consorzio-veterano", "consorzi", "Veterano di Consorzio",
             "Permani in un consorzio per 10 spedizioni.",
             trigger="dungeon_completed", target=10, xp=180, display_order=131),
        _ach("consorzio-leader", "consorzi", "Voce del Consorzio",
             "Partecipa attivamente a 50 spedizioni come membro di consorzio.",
             trigger="dungeon_completed", target=50, xp=400, points=15, display_order=132),
    ]

    # ===== Lore / Esplorazione (8) =====
    rows += [
        _ach("custode-del-vuoto", "lore", "Custode del Vuoto",
             "Completa 10 spedizioni nelle terre di Voidspire.",
             trigger="dungeon_completed", target=10, xp=180, display_order=140),
        _ach("cronista-degli-undead", "lore", "Cronista degli Undead",
             "Sconfiggi 5 boss della famiglia Undead.",
             trigger="dungeon_completed", target=5, xp=180, display_order=141),
        _ach("erede-di-irthe", "lore", "Erede di Irthe",
             "Completa la prima spedizione in territorio di Irthe.",
             trigger="dungeon_completed", target=1, xp=150, display_order=142,
             reward_type="xp_points_title",
             reward_payload={"title_it": "Erede di Irthe"}),
        _ach("ombra-di-ergolat", "lore", "Ombra di Ergolat",
             "Completa 15 spedizioni con avventurieri di tipo furtivo.",
             trigger="dungeon_completed", target=15, xp=200, display_order=143),
        _ach("voce-di-alevora", "lore", "Voce di Alevora",
             "Completa 8 raid del ciclo di Alevora.",
             trigger="raid_completed", target=8, xp=300, points=10, display_order=144),
        _ach("cercatore-di-rune", "lore", "Cercatore di Rune",
             "Trova 50 materiali rari (uncommon o superiore).",
             trigger="material_purchased", target=50, xp=180, display_order=145),
        _ach("collezionista-titoli", "lore", "Collezionista di Titoli",
             "Ottieni almeno 5 titoli cosmetici diversi.",
             trigger="dungeon_completed", target=50, xp=300, points=15, display_order=146),
        _ach("studioso-di-orbus", "lore", "Studioso di Orbus",
             "Equipaggia 30 oggetti diversi su 4 classi.",
             trigger="item_equipped", target=30, xp=200, display_order=147),
    ]

    # ===== Meta / Beta (4, HIDDEN) =====
    rows += [
        _ach("beta-tester", "meta_beta", "Beta Tester",
             "Partecipa alla beta del Round 15.",
             trigger="guild_created", target=1, xp=200, points=20,
             is_hidden=True, reward_type="xp_points_badge",
             reward_payload={"badge_slug": "beta_r15"}, display_order=200),
        _ach("primo-debuff", "meta_beta", "Primo Debuff",
             "Sopravvivi a una spedizione con statistica primaria sotto soglia.",
             trigger="dungeon_completed", target=1, xp=100,
             is_hidden=True, display_order=201),
        _ach("100-imprese", "meta_beta", "Centurione delle Imprese",
             "Sblocca 100 imprese in totale (auto-meta).",
             trigger="dungeon_completed", target=100, xp=500, points=25,
             is_hidden=True, display_order=202),
        _ach("cronache-segrete", "meta_beta", "Cronache Segrete",
             "Un'impresa nascosta nel folklore di Orbus...",
             trigger="raid_completed", target=3, xp=200,
             is_hidden=True, display_order=203),
    ]

    return rows


async def main():
    parser = argparse.ArgumentParser(
        description="ROUND 15 — Phase 3: seed 100 achievement catalog (idempotent).",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_dotenv("/app/backend/.env")
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    rows = build_catalog()
    seen_slugs: set[str] = set()
    for r in rows:
        if r["slug"] in seen_slugs:
            raise RuntimeError(f"duplicate slug in seed: {r['slug']}")
        seen_slugs.add(r["slug"])

    print(f"=== Catalog build: {len(rows)} entries ===")
    by_cat: dict[str, int] = {}
    for r in rows:
        by_cat[r["category"]] = by_cat.get(r["category"], 0) + 1
    for cat in sorted(by_cat):
        print(f"  {cat:18s} {by_cat[cat]:3d}")

    if args.dry_run:
        print("  (dry-run: nessuna scrittura)")
        client.close()
        return

    # Ensure indexes once (idempotent).
    await db.achievements_catalog.create_index("slug", unique=True)
    await db.achievements_catalog.create_index("category")
    await db.achievement_progress.create_index(
        [("guild_id", 1), ("achievement_slug", 1)], unique=True,
    )

    now = datetime.now(timezone.utc).isoformat()
    inserted = updated = 0
    for r in rows:
        existing = await db.achievements_catalog.find_one(
            {"slug": r["slug"]}, {"_id": 0, "achievement_id": 1},
        )
        delta = {**r, "updated_at": now}
        if existing:
            await db.achievements_catalog.update_one(
                {"slug": r["slug"]}, {"$set": delta},
            )
            updated += 1
        else:
            delta["achievement_id"] = str(uuid.uuid4())
            delta["created_at"] = now
            await db.achievements_catalog.insert_one(delta)
            inserted += 1

    print(f"\n=== Apply: inserted={inserted}  updated={updated} ===")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
