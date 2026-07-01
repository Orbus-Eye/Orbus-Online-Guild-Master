"""ROUND 16.3 Phase 8 V1 — Static catalog for mounts + narrative routes.

ANTI-P2W GUARANTEE (verified by test_stables_phase8_v1.py):
    - Every mount has affects_combat/economy/ranking/travel_time = False
    - Every mount has can_be_sold_for_real_money = False
    - Every narrative route reward is cosmetic (badge/title/lore only)
    - No gold, XP, materials or gameplay stats ever unlocked
"""
from __future__ import annotations


# ── 9 mounts (1 starter + 8 domain, one per continent) ───────────────
MOUNT_CATALOG_V1: list[dict] = [
    # STARTER
    {
        "slug": "ronzino-di-strada",
        "name_it": "Ronzino di Strada",
        "rarity": "common",
        "description_it": "Cavalcatura da viaggio robusta e affidabile.",
        "lore_it": (
            "Un compagno modesto ma leale per ogni gilda ai primi passi. "
            "Non ha forma né gloria, ma resiste ad ogni sentiero."
        ),
        "domain_slug": "starter",
        "source_type": "starter_quest",
    },
    # DOMAIN MOUNTS — 8 continenti canonici
    {
        "slug": "lupo-delle-fronde",
        "name_it": "Lupo delle Fronde",
        "rarity": "uncommon",
        "description_it": "Lupo silenzioso che si muove nell'ombra del sottobosco.",
        "lore_it": "Le sue zampe non lasciano orme, solo silenzio.",
        "domain_slug": "soe",
        "source_type": "world_boss_drop",
    },
    {
        "slug": "grifone-delle-alture",
        "name_it": "Grifone delle Alture",
        "rarity": "rare",
        "description_it": "Grifone dai fianchi ambrati, allevato tra le vette di Aveol.",
        "lore_it": "Il grifone conosce ogni corrente d'aria delle alture.",
        "domain_slug": "aveol",
        "source_type": "achievement",
    },
    {
        "slug": "cervo-lunare",
        "name_it": "Cervo Lunare",
        "rarity": "rare",
        "description_it": "Cervo dal manto argenteo delle pianure notturne di Velur.",
        "lore_it": "Le sue corna riflettono la luce delle stelle.",
        "domain_slug": "velur",
        "source_type": "world_boss_drop",
    },
    {
        "slug": "scarabeo-runico",
        "name_it": "Scarabeo Runico",
        "rarity": "uncommon",
        "description_it": "Scarabeo gigante dal carapace inciso di rune dorate.",
        "lore_it": "Camminatore delle sabbie arcane di Ambash.",
        "domain_slug": "ambash",
        "source_type": "craft",
    },
    {
        "slug": "segugio-cinereo",
        "name_it": "Segugio Cinereo",
        "rarity": "uncommon",
        "description_it": "Segugio dalle brughiere di Irthe, fedele e resistente.",
        "lore_it": "La sua ombra è più veloce del suo passo.",
        "domain_slug": "irthe",
        "source_type": "achievement",
    },
    {
        "slug": "salamandra-di-efreto",
        "name_it": "Salamandra di Efreto",
        "rarity": "rare",
        "description_it": "Grande salamandra vulcanica dei territori di Efreto.",
        "lore_it": "La sua pelle è cenere calda, ma il suo passo è lieve.",
        "domain_slug": "efreto",
        "source_type": "craft",
    },
    {
        "slug": "remora-tempestosa",
        "name_it": "Remora Tempestosa",
        "rarity": "rare",
        "description_it": "Enorme remora addestrata delle acque profonde di Nathos.",
        "lore_it": "Il mare la riconosce come figlia.",
        "domain_slug": "nathos",
        "source_type": "world_boss_drop",
    },
    {
        "slug": "ombra-sellata",
        "name_it": "Ombra Sellata",
        "rarity": "epic",
        "description_it": "Cavalcatura spettrale forgiata nei santuari di Ergolat.",
        "lore_it": "Chi la monta cavalca il silenzio stesso.",
        "domain_slug": "ergolat",
        "source_type": "narrative",
    },
]


# ── 5 narrative routes (one-shot, cosmetic reward only) ─────────────
NARRATIVE_ROUTES_V1: list[dict] = [
    {
        "slug": "sentiero-delle-fronde",
        "name_it": "Il Sentiero delle Fronde",
        "description_it": (
            "Un percorso serpeggiante nel cuore della foresta di Soe. "
            "Richiede una cavalcatura del dominio naturale."
        ),
        "lore_it": (
            "Solo chi cavalca creature legate alla natura può attraversare i "
            "boschi silenziosi. Al termine del sentiero, un radura antica accoglie "
            "il viaggiatore con un simbolo inciso nella corteccia."
        ),
        "required_mount_domains": ["soe"],
        "reward_type": "cosmetic_badge",
        "reward_slug": "traveler_of_fronde",
        "reward_name_it": "Viaggiatore delle Fronde",
        "reward_description_it": (
            "Badge assegnato a chi percorre il Sentiero delle Fronde di Soe."
        ),
        "is_repeatable": False,
    },
    {
        "slug": "via-delle-alture",
        "name_it": "La Via delle Alture",
        "description_it": (
            "Rotta d'alta quota che attraversa le cime di Aveol. "
            "Solo un grifone o una cavalcatura d'altura può portarti là."
        ),
        "lore_it": (
            "Quando il vento tace, la Via delle Alture rivela un santuario "
            "dimenticato, dove il cielo tocca la pietra."
        ),
        "required_mount_domains": ["aveol"],
        "reward_type": "cosmetic_title",
        "reward_slug": "titolo_scalatore_delle_alture",
        "reward_name_it": "Scalatore delle Alture",
        "reward_description_it": (
            "Titolo onorifico per chi ha percorso la Via delle Alture."
        ),
        "is_repeatable": False,
    },
    {
        "slug": "traccia-lunare",
        "name_it": "La Traccia Lunare",
        "description_it": (
            "Percorso notturno delle pianure di Velur. "
            "Richiede una cavalcatura affine al chiaro di luna."
        ),
        "lore_it": (
            "Sotto il primo quarto di luna, la Traccia Lunare si illumina di "
            "polvere argentea. Ogni impronta lasciata resta impressa fino all'alba."
        ),
        "required_mount_domains": ["velur"],
        "reward_type": "lore_entry",
        "reward_slug": "codex_traccia_lunare",
        "reward_name_it": "Codex: Traccia Lunare",
        "reward_description_it": (
            "Voce di codex sbloccata dopo aver percorso la Traccia Lunare."
        ),
        "is_repeatable": False,
    },
    {
        "slug": "passo-delle-ceneri",
        "name_it": "Il Passo delle Ceneri",
        "description_it": (
            "Attraversamento vulcanico di Efreto. "
            "Solo una cavalcatura resistente al calore può percorrerlo."
        ),
        "lore_it": (
            "Il Passo delle Ceneri è un sentiero di lava raffreddata dove ogni "
            "passo rimbomba come un tamburo. In fondo, una porta di pietra nera."
        ),
        "required_mount_domains": ["efreto"],
        "reward_type": "cosmetic_badge",
        "reward_slug": "badge_passo_ceneri",
        "reward_name_it": "Superstite del Passo delle Ceneri",
        "reward_description_it": (
            "Badge assegnato a chi ha attraversato il Passo delle Ceneri di Efreto."
        ),
        "is_repeatable": False,
    },
    {
        "slug": "cammino-ombra",
        "name_it": "Il Cammino d'Ombra",
        "description_it": (
            "Rotta segreta che si intreccia con i santuari di Ergolat. "
            "Richiede una cavalcatura d'ombra o spettrale."
        ),
        "lore_it": (
            "Il Cammino d'Ombra non appare sulle mappe. Chi lo percorre torna "
            "portando con sé una piccola traccia di silenzio incorporeo."
        ),
        "required_mount_domains": ["ergolat"],
        "reward_type": "cosmetic_title",
        "reward_slug": "titolo_pellegrino_ombra",
        "reward_name_it": "Pellegrino d'Ombra",
        "reward_description_it": (
            "Titolo onorifico per chi ha percorso il Cammino d'Ombra."
        ),
        "is_repeatable": False,
    },
]


# ── Anti-P2W safety fields (applied uniformly by seed) ───────────────
# Every mount inserted via `ensure_mount_catalog` gets these flags set
# to `False`. Never set to `True` without a design review sign-off.
ANTI_P2W_FLAGS: dict = {
    "affects_combat": False,
    "affects_economy": False,
    "affects_ranking": False,
    "affects_travel_time": False,
    "can_be_sold_for_real_money": False,
    "is_active": True,
}


def mount_domains_by_slug() -> dict[str, str]:
    return {m["slug"]: m["domain_slug"] for m in MOUNT_CATALOG_V1}


__all__ = [
    "MOUNT_CATALOG_V1", "NARRATIVE_ROUTES_V1", "ANTI_P2W_FLAGS",
    "mount_domains_by_slug",
]
