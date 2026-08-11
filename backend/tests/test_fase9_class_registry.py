"""FASE 9B/9C — contratto del registry canonico delle classi.

CLASSE → RUOLO FISSO: 27 classi, 13 DPS · 6 TANK · 8 HEALER, zero
specializzazioni selezionabili, zero build.
"""
from app.class_halls.catalog import CLASS_HALLS
from app.class_halls.mechanics import (
    CLASS_MECHANICS,
    class_equipment_tags,
    resolve_class_mechanic,
)
from app.classes import (
    CANONICAL_ROLES,
    CLASS_REGISTRY,
    class_role_for,
    member_role,
    role_counts,
    role_focus_stats,
)

EXPECTED_ROLES = {
    # DPS (13)
    "guerriero": "DPS", "ladro": "DPS", "mago": "DPS", "monaco": "DPS",
    "negromante": "DPS", "cacciatore_del_vuoto": "DPS",
    "artificiere": "DPS", "cartografo": "DPS", "runista": "DPS",
    "burattinaio": "DPS", "giocatore_d_azzardo": "DPS", "pittore": "DPS",
    "cacciatore_del_sangue": "DPS",
    # TANK (6)
    "paladino": "TANK", "cacciatore_di_mostri": "TANK",
    "fabbro_arcano": "TANK", "parassita": "TANK",
    "cavaliere_della_morte": "TANK", "cavaliere_di_draghi": "TANK",
    # HEALER (8)
    "alchimista": "HEALER", "bardo": "HEALER", "druido": "HEALER",
    "sciamano": "HEALER", "cronista": "HEALER", "mercante": "HEALER",
    "astrologo": "HEALER", "sognatore": "HEALER",
}


def test_registry_ha_27_classi_con_ruolo_canonico():
    assert len(CLASS_REGISTRY) == 27
    assert set(CLASS_REGISTRY) == set(EXPECTED_ROLES)
    for slug, expected_role in EXPECTED_ROLES.items():
        assert class_role_for(slug) == expected_role, slug


def test_distribuzione_ruoli_13_6_8():
    counts = role_counts()
    assert counts == {"DPS": 13, "TANK": 6, "HEALER": 8}
    assert sum(counts.values()) == 27


def test_ogni_classe_ha_identita_completa():
    for definition in CLASS_REGISTRY.values():
        assert definition.class_role in CANONICAL_ROLES
        assert definition.class_name
        assert definition.class_identity
        assert definition.class_mechanics
        assert definition.emblem
        assert definition.emblem_symbol
        assert len(definition.palette) == 2
        assert definition.armor_tags and definition.weapon_tags
        # FUTURO slot di classe: riservato ma MAI attivo in questa tranche.
        assert definition.hybrid_slot is None


def test_emblemi_unici_per_le_27_classi():
    emblems = [d.emblem for d in CLASS_REGISTRY.values()]
    symbols = [d.emblem_symbol for d in CLASS_REGISTRY.values()]
    assert len(set(emblems)) == 27
    assert len(set(symbols)) == 27


def test_registry_allineato_al_catalogo_hall():
    hall_slugs = {p.canonical_class_slug for p in CLASS_HALLS.values()}
    assert hall_slugs == set(CLASS_REGISTRY)


def test_slug_legacy_risolti():
    assert class_role_for("warrior") == "DPS"
    assert class_role_for("paladin") == "TANK"
    assert class_role_for("priest") == "TANK"     # → paladino
    assert class_role_for("ranger") == "TANK"     # → cacciatore_di_mostri
    assert class_role_for("bard") == "HEALER"
    assert class_role_for("classe_inventata") is None


def test_member_role_preferisce_la_classe_al_campo_storico():
    # Doc storico con ruolo vecchio: vince la CLASSE.
    assert member_role({"class_slug": "guerriero", "class_role": "Tank"}) == "DPS"
    # Snapshot senza slug: fallback sul valore normalizzabile.
    assert member_role({"role_snapshot": "Healer"}) == "HEALER"
    # Support/Hybrid/Utility senza slug: non mappabile.
    assert member_role({"class_role": "Support"}) is None


def test_role_focus_stats_su_stat_reali():
    valid = {"strength", "agility", "intellect", "endurance", "faith"}
    for slug in CLASS_REGISTRY:
        first, second = role_focus_stats(slug)
        assert first in valid and second in valid
        assert first != second
    assert role_focus_stats("paladino")[0] == "endurance"   # TANK
    assert role_focus_stats("bardo")[0] == "faith"          # HEALER
    assert role_focus_stats("mago")[0] == "intellect"       # DPS primaria


def test_meccaniche_senza_build():
    assert len(CLASS_MECHANICS) == 27
    for slug, mechanic in CLASS_MECHANICS.items():
        assert not hasattr(mechanic, "builds")
        assert mechanic.counter_tags
        assert class_equipment_tags(slug)
    resolved = resolve_class_mechanic(
        adventurer={"canonical_class_slug": "paladino"},
        equipment_items=[{"tags": ["shield"]}],
    )
    assert resolved["resonance_active"] is True
    assert resolved["power_bonus"] == 3  # 1 base + 2 risonanza (invariati)
    assert "active_build" not in resolved
    assert "build_options" not in resolved
