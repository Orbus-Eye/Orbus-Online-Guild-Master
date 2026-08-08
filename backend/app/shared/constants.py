"""Single source of truth for tunable gameplay & security constants.

Behavioural contract: values here must match Phase 5/6/7 spec exactly.
Re-exported by `server.py` for backward compatibility with the test suite.
"""
import os as _os

# ─── Auth / security (Phase 5) ────────────────────────────────────────────────
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7
# TODO Phase 8: reduce access TTL to ~1h once frontend actively uses refresh.

REFRESH_TOKEN_TTL_DAYS = 30
PASSWORD_RESET_TTL_MINUTES = 60
LOGIN_LOCK_MAX_ATTEMPTS = 5
LOGIN_LOCK_DURATION_MINUTES = 15
LOGIN_ATTEMPTS_TTL_SECONDS = 86400  # 24h cleanup of stale attempt rows

# ─── Gameplay (Phase 2/3/6/7) ─────────────────────────────────────────────────
RECRUITMENT_COST_GOLD = 20

# Success-chance formula clamps.
# FASE 2 (2026-08-08) — il vecchio cap 95 è stato rimosso: la curva
# logistica di `compute_success_chance` arriva al 100% reale quando il
# Rating di Potenza raggiunge GUARANTEED_SUCCESS_RATING. Vedi
# memory/fase2_design_bilanciamento.md per formula e razionale.
SUCCESS_CHANCE_MIN = 5
SUCCESS_CHANCE_MAX = 100

# FASE 2 — Rating di Potenza & Overpower.
# rating = round(100 * team_power / recommended_power); l'eccedenza oltre
# 100 diventa bonus sui drop a gradini di OVERPOWER_STEP_PCT.
SUCCESS_CURVE_K = 4.4                  # pendenza della logistica
GUARANTEED_SUCCESS_RATING = 200        # potenza doppia → vittoria garantita
OVERPOWER_STEP_PCT = 25                # ogni +25 rating oltre 100...
OVERPOWER_BONUS_PER_STEP = 0.5         # ...+50% drop
OVERPOWER_LOOT_MULTIPLIER_CAP = 3.0    # tetto economico (rating ≥ 200)
# Gate d'ingresso dungeon: potere squadra ≥ 60% del consigliato
# (equivale a ~14% di probabilità: run azzardata permessa, assurda no).
POWER_GATE_RATIO = 0.60

# Loot
LOOT_DROP_CHANCE_LEGACY = 0.50      # Goblin Warrens default if loot table missing
LOOT_RARITIES_LEGACY = ["Common", "Uncommon"]

# Adventurer progression. The old linear ``level * 100`` curve reached level
# 80 too quickly. The career curve now totals roughly 2.8M XP from 1 to 80.
XP_THRESHOLD_PER_LEVEL = 125  # legacy name; now used as curve multiplier
ADVENTURER_XP_CURVE_EXPONENT = 1.5
# T0 item-first contract — authoritative adventurer cap. Endgame equipment
# imports this value instead of repeating historical literals.
ADVENTURER_MAX_LEVEL = 80

# Recruitment generation (Phase 2)
RECRUITMENT_CANDIDATES_PER_OFFER = 4
OFFER_TTL_MINUTES = 30
# Deprecated compatibility constant. Player-facing generation never rolls
# rarity: every adventurer starts Common and earns career rarity by use.
RARITY_WEIGHTS = [
    ("Common", 1),
]
RARITY_BONUS = {"Common": 0}
# Stat max threshold used by the Legendary post-roll guard. A Legendary
# adventurer MUST have at least 1 core stat at or above this floor.
RARITY_STAT_MAX_FLOOR = {}
# Soft minimum positive-trait count required for high-rarity guard. Falls
# back gracefully when the trait pool is empty (no `Test*` traits ever).
RARITY_POSITIVE_TRAIT_MIN = {}
FIRST_NAMES = [
    "Aldric", "Brenna", "Cassian", "Dorin", "Elara", "Faelan", "Gwyn",
    "Hadrian", "Iona", "Joren", "Kael", "Lyra", "Mira", "Nyx", "Oren",
    "Perrin", "Quill", "Rhea", "Soren", "Talia", "Ulric", "Vera", "Wren",
    "Yara", "Zane",
]
LAST_NAMES = [
    "the Bold", "Stoneheart", "Ashwood", "Stormwind", "Ironfoot",
    "Nightshade", "Brightblade",
]

# Equipment slots — ten physical positions. Paired rings and trinkets are
# distinct slots but share the same item type.
EQUIPMENT_SLOTS = (
    "weapon",
    "chest",
    "legs",
    "head",
    "accessory",
    "back",
    "ring_1",
    "ring_2",
    "trinket_1",
    "trinket_2",
)
SLOT_TO_ITEM_TYPE = {
    "weapon": "weapon",
    "chest": "armor",
    "legs": "legs",
    "head": "helmet",
    "accessory": "accessory",
    "back": "back",
    "ring_1": "ring",
    "ring_2": "ring",
    "trinket_1": "trinket",
    "trinket_2": "trinket",
}
EQUIPMENT_SLOT_LABELS_IT = {
    "weapon": "Arma",
    "chest": "Corazza",
    "legs": "Gambe",
    "head": "Elmo",
    "accessory": "Accessorio",
    "back": "Schiena",
    "ring_1": "Anello I",
    "ring_2": "Anello II",
    "trinket_1": "Monile I",
    "trinket_2": "Monile II",
}

# Tester / seed gating
# Test-fixture credentials (NOT real secrets). Used by the idempotent
# `seed_tester()` helper which is itself gated by `APP_ENV != "production"`,
# so these values are never written to a production DB.
#
# `TESTER_PASSWORD` is loaded from the env var of the same name; the
# `"password123"` literal is only used as a dev/CI fallback. In production
# the seed is skipped entirely (see `seed_tester()` in `server.py`), so the
# fallback is never persisted. If you need a non-default tester credential
# for staging/preview, set `TESTER_PASSWORD` in your environment.

TESTER_EMAIL = "tester@orbus.test"
TESTER_USERNAME = "tester"
TESTER_PASSWORD = _os.environ.get("TESTER_PASSWORD", "password123")  # noqa: S105 — dev/CI fallback only; prod skips seeding
