"""ROUND 16.5.4c REOPEN #3 — Auto-Equip i18n / off-class silent-skip tests.

Verifiche richieste dal PM dopo lo screenshot `e1_tester`:

1. Slot label sempre in italiano nel payload player-facing.
2. Nessuna stringa inglese identificabile in `reason_it` /
   `unchanged_slots_detail[].reason_it`.
3. Messaggio "già il migliore" tradotto per tutti e 3 gli slot.
4. Nessun `HTTPException` mai nel payload.
5. Nessun nome di item off-class citato nel messaggio player-facing
   (`reason_it`) — deve restare filtrato silenziosamente.
6. `off_class_seen` presente nel payload tecnico ma NON come stringa
   inglese o come nome item leaked.

Scope stretto: NON introduce framework i18n globale. Solo verifica del
contract del payload backend (le stringhe IT sono già prodotte da
`app.equipment.auto_equip`).
"""
from __future__ import annotations

import asyncio
import json
import pytest

# Riuso helper del file R16.5.4b/c principale.
from tests.backend_round1654b_test import (  # type: ignore[import-not-found]
    _seed_class, _seed_guild, _seed_adventurer, _seed_item,
    _seed_inventory, _call_auto_equip, _run, cleanup_r1654b,  # noqa
    sync_db,  # noqa
)


# Blacklist di stringhe inglesi che NON devono mai apparire nel payload
# player-facing (`reason_it`, `unchanged_slots_detail[].reason_it`,
# `warnings_it`). Sono le forme che il tester ha visto in produzione.
_ENGLISH_BANNED_SUBSTRINGS = (
    "Weapon:", "Armor:", "Accessory:",  # slot in inglese
    "the currently equipped", "already the best",
    "found but not compatible", "no compatible item",
    "no better item", "equip failed", "unequip failed",
    "HTTPException", "[object Object]",
)


def _collect_it_strings(payload: dict) -> list[str]:
    """Estrai le stringhe IT visibili al player dal payload."""
    out: list[str] = []
    for r in payload.get("reasons") or []:
        if isinstance(r.get("reason_it"), str):
            out.append(r["reason_it"])
    for d in payload.get("unchanged_slots_detail") or []:
        if isinstance(d.get("reason_it"), str):
            out.append(d["reason_it"])
    for w in payload.get("warnings_it") or []:
        if isinstance(w, str):
            out.append(w)
    return out


def test_28_it_slot_labels_present(sync_db, cleanup_r1654b):
    """Warrior class-fit: reason_it deve iniziare con 'Arma equipaggiata:',
    'Armatura equipaggiata:', 'Accessorio equipaggiato:'."""
    _seed_class(sync_db, "test_r1654c_warr28", "strength", ["endurance"],
                name="Guerriero")
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654c_warr28",
                           level=8)
    w = _seed_item(sync_db, item_type="weapon", name_tag="wpn28",
                   strength=5, endurance=2, power=7,
                   class_tags=["test_r1654c_warr28"])
    a = _seed_item(sync_db, item_type="armor", name_tag="arm28",
                   strength=1, endurance=5, power=6,
                   class_tags=["test_r1654c_warr28"])
    acc = _seed_item(sync_db, item_type="accessory", name_tag="acc28",
                     strength=2, endurance=2, power=6,
                     class_tags=["test_r1654c_warr28"])
    for it in (w, a, acc):
        _seed_inventory(sync_db, g["id"], it["id"])
    res = _run(_call_auto_equip(g, adv["id"]))

    reasons_by_slot = {r["slot"]: r["reason_it"] for r in res["reasons"]}
    assert reasons_by_slot["weapon"].startswith("Arma equipaggiata:"), (
        f"weapon reason_it non italiano: {reasons_by_slot['weapon']!r}"
    )
    assert reasons_by_slot["armor"].startswith("Armatura equipaggiata:"), (
        f"armor reason_it non italiano: {reasons_by_slot['armor']!r}"
    )
    assert reasons_by_slot["accessory"].startswith(
        "Accessorio equipaggiato:"), (
        f"accessory reason_it non italiano: "
        f"{reasons_by_slot['accessory']!r}"
    )


def test_29_no_english_leakage_in_player_strings(sync_db, cleanup_r1654b):
    """Nessuna stringa inglese identificabile nelle stringhe IT
    player-facing del payload."""
    _seed_class(sync_db, "test_r1654c_al29", "intellect",
                ["agility", "endurance"], name="Alchimista")
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654c_al29", level=8)
    w = _seed_item(sync_db, item_type="weapon", name_tag="w_al29",
                   intellect=4, agility=2, power=6,
                   class_tags=["test_r1654c_al29"])
    _seed_inventory(sync_db, g["id"], w["id"])
    res = _run(_call_auto_equip(g, adv["id"]))

    it_strings = _collect_it_strings(res)
    assert it_strings, "il payload deve produrre almeno una stringa IT"
    for s in it_strings:
        for banned in _ENGLISH_BANNED_SUBSTRINGS:
            assert banned not in s, (
                f"stringa vietata {banned!r} nel messaggio IT: {s!r}"
            )


def test_30_already_the_best_it_all_three_slots(sync_db, cleanup_r1654b):
    """Warrior con equipment ottimale già equipaggiato → seconda auto-equip
    produce `reason_it` "Arma/Armatura/Accessorio: l'oggetto attualmente
    equipaggiato è già il migliore." su tutti e 3 gli slot."""
    _seed_class(sync_db, "test_r1654c_warr30", "strength", ["endurance"],
                name="Guerriero")
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654c_warr30",
                           level=8)
    for slot, name in (("weapon", "w30"), ("armor", "a30"),
                       ("accessory", "acc30")):
        it_doc = _seed_item(
            sync_db, item_type=slot, name_tag=name,
            strength=4, endurance=2, power=6,
            class_tags=["test_r1654c_warr30"],
        )
        _seed_inventory(sync_db, g["id"], it_doc["id"])

    _run(_call_auto_equip(g, adv["id"]))
    # Seconda chiamata: tutti "già il migliore".
    res = _run(_call_auto_equip(g, adv["id"]))
    assert res["swaps_count"] == 0
    it_by_slot = {d["slot"]: d["reason_it"]
                  for d in res["unchanged_slots_detail"]}
    assert (
        it_by_slot["weapon"]
        == "Arma: l'oggetto attualmente equipaggiato è già il migliore."
    ), f"weapon: {it_by_slot['weapon']!r}"
    assert (
        it_by_slot["armor"]
        == "Armatura: l'oggetto attualmente equipaggiato è già il migliore."
    ), f"armor: {it_by_slot['armor']!r}"
    assert (
        it_by_slot["accessory"]
        == "Accessorio: l'oggetto attualmente equipaggiato è già il migliore."
    ), f"accessory: {it_by_slot['accessory']!r}"


def test_31_no_httpexception_ever_in_payload(sync_db, cleanup_r1654b):
    """Payload player-facing non deve mai contenere 'HTTPException'
    in nessun campo, anche in caso di inventario incompleto."""
    _seed_class(sync_db, "test_r1654c_wlk31", "intellect",
                ["faith", "agility"], name="Occultista")
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654c_wlk31",
                           level=5)
    # Nessun item in inventario → 3 empty state, potenziale ramo except.
    res = _run(_call_auto_equip(g, adv["id"]))
    dump = json.dumps(res, ensure_ascii=False)
    assert "HTTPException" not in dump, (
        f"REGRESSIONE R16.5.4c ADJ-3.c: 'HTTPException' nel payload"
    )
    assert "[object Object]" not in dump


def test_32_mage_off_class_names_not_leaked(sync_db, cleanup_r1654b):
    """Mage (int primary) con inventario di SOLI item warrior-only
    (Iron Sword-like) → empty state IT, nessun nome item off-class nel
    reason_it / unchanged_slots_detail[].reason_it / warnings_it."""
    _seed_class(sync_db, "test_r1654c_mage32", "intellect", ["faith"],
                name="Mago")
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654c_mage32",
                           level=8)
    iron_sword = _seed_item(
        sync_db, item_type="weapon", name_tag="Iron_Sword_offclass",
        rarity="Rare", strength=4, power=5,
        class_tags=["warrior", "paladin"],
    )
    steel_plate = _seed_item(
        sync_db, item_type="armor", name_tag="Steel_Half_Plate_offclass",
        rarity="Rare", strength=1, endurance=4, power=5,
        class_tags=["warrior", "paladin"],
    )
    _seed_inventory(sync_db, g["id"], iron_sword["id"])
    _seed_inventory(sync_db, g["id"], steel_plate["id"])

    res = _run(_call_auto_equip(g, adv["id"]))

    # I nomi degli item off-class NON devono comparire nei messaggi IT.
    it_strings = _collect_it_strings(res)
    for s in it_strings:
        assert iron_sword["slug"] not in s, (
            f"item off-class {iron_sword['slug']} leaked in: {s!r}"
        )
        assert steel_plate["slug"] not in s
        # Anche il name-tag "Iron_Sword_offclass" non deve mai comparire.
        assert "Iron_Sword_offclass" not in s
        assert "Steel_Half_Plate_offclass" not in s
    # Empty state IT presente per weapon e armor (off_class_seen>0 branch).
    unchanged_slots = set(res.get("unchanged_slots", []))
    assert "weapon" in unchanged_slots and "armor" in unchanged_slots
    for d in res["unchanged_slots_detail"]:
        if d["slot"] in ("weapon", "armor"):
            # Deve citare la classe italiana "Mago", non "warrior".
            assert "Mago" in d["reason_it"], (
                f"empty state IT deve citare 'Mago' come classe: "
                f"{d['reason_it']!r}"
            )


def test_33_off_class_seen_tech_metric_accessible(sync_db, cleanup_r1654b):
    """`off_class_seen` deve essere presente nel payload tecnico per
    dashboard/audit ma NON come stringa player-facing."""
    _seed_class(sync_db, "test_r1654c_mage33", "intellect", ["faith"],
                name="Mago")
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654c_mage33",
                           level=8)
    warrior_wpn = _seed_item(
        sync_db, item_type="weapon", name_tag="warr33",
        strength=4, power=5, class_tags=["warrior"],
    )
    _seed_inventory(sync_db, g["id"], warrior_wpn["id"])
    res = _run(_call_auto_equip(g, adv["id"]))

    wpn_detail = next(
        (d for d in res["unchanged_slots_detail"] if d["slot"] == "weapon"),
        None,
    )
    assert wpn_detail is not None
    assert wpn_detail.get("off_class_seen") == 1, (
        f"off_class_seen tecnico deve essere 1, got: "
        f"{wpn_detail.get('off_class_seen')!r}"
    )
    # Nessuna stringa "off_class_seen" o "off-class" nel reason_it player.
    assert "off_class_seen" not in wpn_detail["reason_it"]
    assert "off-class" not in wpn_detail["reason_it"]
    # E il nome tecnico dell'item warrior non deve leakare.
    assert warrior_wpn["slug"] not in wpn_detail["reason_it"]
    assert "warr33" not in wpn_detail["reason_it"]


def test_34_warlock_class_label_is_occultista(sync_db, cleanup_r1654b):
    """PM decision R16.5.4c REOPEN #3: warlock → 'Occultista' (non
    'Stregone' come nella versione precedente)."""
    _seed_class(sync_db, "test_r1654c_wlk34", "intellect",
                ["faith", "agility"], name="Occultista")
    g = _seed_guild(sync_db)
    adv = _seed_adventurer(sync_db, g["id"], "test_r1654c_wlk34",
                           level=5)
    # Un weapon class-fit per generare reason_it che citi la classe.
    wpn = _seed_item(
        sync_db, item_type="weapon", name_tag="wlk34",
        intellect=4, faith=2, power=6,
        class_tags=["test_r1654c_wlk34"],
    )
    _seed_inventory(sync_db, g["id"], wpn["id"])
    res = _run(_call_auto_equip(g, adv["id"]))
    reason = next(
        r["reason_it"] for r in res["reasons"] if r["slot"] == "weapon"
    )
    # Il reason deve citare "Occultista" (dal class_name IT).
    assert "Occultista" in reason, (
        f"reason_it deve citare la classe italiana 'Occultista', "
        f"got: {reason!r}"
    )
    # Non deve MAI usare "Stregone" (label vecchia).
    assert "Stregone" not in reason
