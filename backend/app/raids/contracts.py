"""Canonical 10/15/20/40-adventurer raid contracts."""
from __future__ import annotations

from app.shared.content_curve import RAID_CURVE


RAID_CONTRACTS = {
    "moonfall-vigil": {
        "contract_version": "career-revamp-r1",
        "required_party_count": 2,
        "party_responsibilities": [
            {"party_idx": 1, "name_it": "Custodi del Frammento",
             "threat_tags": ["spell", "magic_barrier"]},
            {"party_idx": 2, "name_it": "Cacciatori dell'Eclissi",
             "threat_tags": ["ambush", "boss"]},
        ],
        "phases": [
            {"phase_id": "frattura", "name_it": "La Frattura nel Cielo",
             "required_parties": [1]},
            {"phase_id": "eclissi", "name_it": "La Cosa dietro la Luna",
             "required_parties": [1, 2]},
        ],
        "reward_profile": {
            "profile_id": "raid.level40.vigil",
            "source_policy_id": "raid_level40",
            "categories": ["rare_equipment", "raid_token", "lore_fragment"],
            "allowed_rarities": ["Uncommon", "Rare"],
            "legendary_allowed": False,
            "unique_allowed": False,
        },
    },
    "broken-bastion-siege": {
        "contract_version": "career-revamp-r1",
        "required_party_count": 3,
        "party_responsibilities": [
            {"party_idx": 1, "name_it": "Avanguardia",
             "threat_tags": ["siege", "elite"]},
            {"party_idx": 2, "name_it": "Custodi delle mura",
             "threat_tags": ["minion", "ambush"]},
            {"party_idx": 3, "name_it": "Sabotatori", "threat_tags": ["trap", "magic_barrier"]},
        ],
        "phases": [
            {"phase_id": "mura", "name_it": "Tenuta delle mura", "required_parties": [1, 2]},
            {"phase_id": "macchine", "name_it": "Caduta delle macchine",
             "required_parties": [3]},
            {"phase_id": "comandante", "name_it": "Comandante del Bastione",
             "required_parties": [1, 2, 3]},
        ],
        "reward_profile": {
            "profile_id": "raid.level60.fragments",
            "source_policy_id": "raid_level60",
            "categories": ["epic_equipment", "raid_token", "lore_fragment"],
            "allowed_rarities": ["Rare", "Epic"],
            "legendary_allowed": False,
            "unique_allowed": False,
        },
    },
    "necropolis-bells": {
        "contract_version": "career-revamp-r1",
        "required_party_count": 4,
        "party_responsibilities": [
            {"party_idx": 1, "name_it": "Guardia del rintocco",
             "threat_tags": ["undead", "curse"]},
            {"party_idx": 2, "name_it": "Esorcisti", "threat_tags": ["spell", "magic_barrier"]},
            {"party_idx": 3, "name_it": "Spezzacampane", "threat_tags": ["siege", "elite"]},
            {"party_idx": 4, "name_it": "Cacciatori del Campanaro",
             "threat_tags": ["boss", "stealth"]},
        ],
        "phases": [
            {"phase_id": "processione", "name_it": "Processione dei morti",
             "required_parties": [1, 2]},
            {"phase_id": "campane", "name_it": "Mille campane", "required_parties": [2, 3]},
            {"phase_id": "campanaro", "name_it": "Campanaro Senza Volto",
             "required_parties": [1, 2, 3, 4]},
        ],
        "reward_profile": {
            "profile_id": "raid.level70.legendary_fragments",
            "source_policy_id": "raid_level70",
            "categories": ["epic_equipment", "legendary_fragment", "raid_token"],
            "allowed_rarities": ["Rare", "Epic"],
            "legendary_allowed": False,
            "unique_allowed": False,
        },
    },
    "dragon-vault": {
        "contract_version": "career-revamp-r1",
        "required_party_count": 8,
        "party_responsibilities": [
            {"party_idx": 1, "name_it": "Scudo delle scaglie",
             "threat_tags": ["boss", "elemental"]},
            {"party_idx": 2, "name_it": "Cacciatori del cuore", "threat_tags": ["beast", "elite"]},
            {"party_idx": 3, "name_it": "Custodi del sigillo",
             "threat_tags": ["spell", "magic_barrier"]},
            {"party_idx": 4, "name_it": "Predatori del tesoro", "threat_tags": ["trap", "ambush"]},
            {"party_idx": 5, "name_it": "Araldi della Cenere",
             "threat_tags": ["elemental", "spell"]},
            {"party_idx": 6, "name_it": "Custodi delle Catene",
             "threat_tags": ["siege", "elite"]},
            {"party_idx": 7, "name_it": "Occhi del Vuoto",
             "threat_tags": ["void", "curse"]},
            {"party_idx": 8, "name_it": "Ultima Riserva",
             "threat_tags": ["boss", "beast"]},
        ],
        "phases": [
            {"phase_id": "sigillo", "name_it": "Apertura della Volta",
             "required_parties": [3, 4]},
            {"phase_id": "risveglio", "name_it": "Risveglio del Drago",
             "required_parties": [1, 2]},
            {"phase_id": "cuore", "name_it": "Cuore della Volta",
             "required_parties": [1, 2, 3, 4, 5, 6, 7, 8]},
        ],
        "reward_profile": {
            "profile_id": "raid.level80.endgame",
            "source_policy_id": "raid_level80_victory",
            "categories": ["epic_equipment", "legendary_blueprint", "raid_token"],
            "allowed_rarities": ["Epic", "Legendary"],
            "legendary_allowed": True,
            "legendary_requires_victory": True,
            "unique_allowed": False,
            "unique_ring_allowed": False,
        },
    },
}


def apply_raid_contract(raid_dungeon: dict | None) -> dict | None:
    if raid_dungeon is None:
        return None
    slug = str(raid_dungeon.get("slug") or "")
    contract = RAID_CONTRACTS.get(slug)
    curve = RAID_CURVE.get(slug)
    if contract is None or curve is None:
        return dict(raid_dungeon)
    return {
        **raid_dungeon,
        **contract,
        "required_level": curve.required_level,
        "min_adventurer_level": curve.required_level,
        "recommended_power_combined": curve.recommended_power,
        "base_xp_per_member": curve.xp_reward,
        "required_party_count": int(contract["required_party_count"]),
        "required_party_size": 5,
        "min_roster_size": int(contract["required_party_count"]) * 5,
        "gate": {
            **(raid_dungeon.get("gate") or {}),
            "min_roster_size": int(contract["required_party_count"]) * 5,
        },
    }


def raid_progression_rewards(slug: str, outcome: str) -> dict:
    """Return deterministic non-item grants shared by complete/recovery."""
    tier = {
        "moonfall-vigil": 1,
        "broken-bastion-siege": 2,
        "necropolis-bells": 3,
        "dragon-vault": 4,
    }.get(slug, 0)
    tokens = {
        "wipe": tier,
        "partial": tier * 2,
        "victory": tier * 4,
    }.get(outcome, 0)
    fragments = 0
    if tier >= 2 and outcome == "partial":
        fragments = tier - 1
    elif tier >= 2 and outcome == "victory":
        fragments = tier
    return {
        "raid_tokens": tokens,
        "legendary_fragments": fragments,
        "legendary_blueprint_eligible": (
            slug == "dragon-vault" and outcome == "victory"
        ),
        "unique_eligible": False,
        "unique_ring_eligible": False,
    }


__all__ = [
    "RAID_CONTRACTS",
    "apply_raid_contract",
    "raid_progression_rewards",
]
