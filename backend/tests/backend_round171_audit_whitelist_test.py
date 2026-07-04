"""ROUND 17.1 pre-sealing — verify AUDIT_EVENT_WHITELIST includes the new
funnel event types + starter fallback event, and backward compat with
pre-R17.1 events still visible.
"""
from __future__ import annotations

from app.admin.audit_routes import AUDIT_EVENT_WHITELIST


R17_FUNNEL_EVENTS = (
    "REGISTERED",
    "GUILD_CREATED",
    "FIRST_ADVENTURER_VIEWED",
    "FIRST_DUNGEON_VIEWED",
    "FIRST_EXPEDITION_PREVIEWED",
    "FIRST_EXPEDITION_STARTED",
    "FIRST_EXPEDITION_COMPLETED",
    "FIRST_REPORT_OPENED",
    "FIRST_PRESTIGE_GAINED",
    "STARTER_FALLBACK_REWARD_GRANTED",
)

PRE_R17_EVENTS_SAMPLE = (
    "achievement_unlocked",
    "guild_xp_gained",
    "onboarding_graduated",
    "WORLD_BOSS_EVENT_CREATED",
    "PVP_BATTLE_RESOLVED",
    "LEGENDARY_CRAFT_COMPLETED",
    "MOUNT_ACQUIRED",
)


def test_all_r17_funnel_event_types_are_whitelisted():
    """PM msg R17.1 mini-fix: 10 event types R17.1 devono essere nella
    whitelist admin per essere visibili via `GET /api/admin/audit/events`."""
    missing = [e for e in R17_FUNNEL_EVENTS if e not in AUDIT_EVENT_WHITELIST]
    assert not missing, f"whitelist missing R17 funnel events: {missing}"


def test_pre_r17_event_types_still_whitelisted_backward_compat():
    """Nessuna regressione: gli event types pre-R17.1 restano nella
    whitelist."""
    missing = [e for e in PRE_R17_EVENTS_SAMPLE if e not in AUDIT_EVENT_WHITELIST]
    assert not missing, f"pre-R17 events lost from whitelist: {missing}"


def test_whitelist_has_no_duplicates():
    """Frozenset garantisce set-semantics; verifica accessoria via
    parse del sorgente per identificare eventuali duplicate literal
    (guard contro edit sloppy futuri)."""
    import inspect
    from app.admin import audit_routes
    src = inspect.getsource(audit_routes)
    # Estrae solo il blocco AUDIT_EVENT_WHITELIST
    start = src.index("AUDIT_EVENT_WHITELIST = frozenset({")
    end = src.index("})", start)
    block = src[start:end]
    literals = [
        line.strip().strip(",").strip('"').strip("'")
        for line in block.splitlines()
        if line.strip().startswith(('"', "'")) and "#" not in line
    ]
    duplicates = [x for x in set(literals) if literals.count(x) > 1]
    assert not duplicates, f"whitelist has literal duplicates: {duplicates}"


def test_all_r17_events_are_uppercase_or_snake_case_consistent():
    """Sanity: gli event types R17.1 seguono la convenzione UPPERCASE
    (allineati con R16.3 phase 1+)."""
    for et in R17_FUNNEL_EVENTS:
        assert et == et.upper(), (
            f"R17 event type deve essere UPPERCASE, got {et!r}"
        )
