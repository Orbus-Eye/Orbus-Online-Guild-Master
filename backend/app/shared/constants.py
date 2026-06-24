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

# Equipment slots (Phase 6)
EQUIPMENT_SLOTS = ("weapon", "armor", "accessory")
SLOT_TO_ITEM_TYPE = {"weapon": "weapon", "armor": "armor", "accessory": "accessory"}

# Tester / seed gating
TESTER_EMAIL = "tester@orbus.test"
TESTER_USERNAME = "tester"
TESTER_PASSWORD = "password123"
