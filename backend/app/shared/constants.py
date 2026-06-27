"""Single source of truth for tunable gameplay & security constants.

Behavioural contract: values here must match Phase 5/6/7 spec exactly.
Re-exported by `server.py` for backward compatibility with the test suite.
"""

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

# Success-chance formula clamps
SUCCESS_CHANCE_MIN = 10
SUCCESS_CHANCE_MAX = 95

# Loot
LOOT_DROP_CHANCE_LEGACY = 0.50      # Goblin Warrens default if loot table missing
LOOT_RARITIES_LEGACY = ["Common", "Uncommon"]

# Adventurer progression
XP_THRESHOLD_PER_LEVEL = 100

# Recruitment generation (Phase 2)
RECRUITMENT_CANDIDATES_PER_OFFER = 4
OFFER_TTL_MINUTES = 30
# Phase 6A.1 — rarity distribution with Legendary as ultra-rare surprise.
# Numeric weights MUST sum to ~1000 for fine-grained Legendary tail (0.1%).
# Target distribution: Common 68% / Uncommon 24% / Rare 7% / Epic 0.9% / Legendary 0.1%
RARITY_WEIGHTS = [
    ("Common", 680),
    ("Uncommon", 240),
    ("Rare", 70),
    ("Epic", 9),
    ("Legendary", 1),
]
RARITY_BONUS = {"Common": 0, "Uncommon": 0, "Rare": 1, "Epic": 2, "Legendary": 3}
# Stat max threshold used by the Legendary post-roll guard. A Legendary
# adventurer MUST have at least 1 core stat at or above this floor.
RARITY_STAT_MAX_FLOOR = {"Legendary": 15, "Epic": 12}
# Soft minimum positive-trait count required for high-rarity guard. Falls
# back gracefully when the trait pool is empty (no `Test*` traits ever).
RARITY_POSITIVE_TRAIT_MIN = {"Legendary": 3, "Epic": 2}
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

# Equipment slots (Phase 6)
EQUIPMENT_SLOTS = ("weapon", "armor", "accessory")
SLOT_TO_ITEM_TYPE = {"weapon": "weapon", "armor": "armor", "accessory": "accessory"}

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
import os as _os

TESTER_EMAIL = "tester@orbus.test"
TESTER_USERNAME = "tester"
TESTER_PASSWORD = _os.environ.get("TESTER_PASSWORD", "password123")  # noqa: S105 — dev/CI fallback only; prod skips seeding
