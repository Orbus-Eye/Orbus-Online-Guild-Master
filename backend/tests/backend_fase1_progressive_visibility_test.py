"""FASE 1.9 (2026-08-08) — Visibilità progressiva dungeon/raid.

Regola: sbloccati + SOLO il primo bloccato ("prossima sfida"); il resto
è nascosto. Test puri, nessun Mongo richiesto.
"""
from app.shared.progressive_visibility import apply_progressive_visibility


def _mk(slug, unlocked):
    return {"slug": slug, "unlocked": unlocked}


def test_sbloccati_piu_primo_bloccato():
    items = [
        _mk("a", True), _mk("b", True),
        _mk("c", False), _mk("d", False), _mk("e", False),
    ]
    out = apply_progressive_visibility(items)
    assert [i["slug"] for i in out] == ["a", "b", "c"]
    assert out[0]["is_next_challenge"] is False
    assert out[2]["is_next_challenge"] is True
    assert all(i["hidden_upcoming_count"] == 2 for i in out)


def test_tutto_sbloccato_nessun_nascosto():
    items = [_mk("a", True), _mk("b", True)]
    out = apply_progressive_visibility(items)
    assert len(out) == 2
    assert all(i["hidden_upcoming_count"] == 0 for i in out)
    assert not any(i["is_next_challenge"] for i in out)


def test_tutto_bloccato_mostra_solo_il_primo():
    items = [_mk("a", False), _mk("b", False), _mk("c", False)]
    out = apply_progressive_visibility(items)
    assert [i["slug"] for i in out] == ["a"]
    assert out[0]["is_next_challenge"] is True
    assert out[0]["hidden_upcoming_count"] == 2


def test_sbloccato_dopo_il_teaser_resta_visibile():
    """Un contenuto sbloccato che viene DOPO un bloccato (es. gate
    alternativi) non deve mai sparire."""
    items = [_mk("a", True), _mk("b", False), _mk("c", True), _mk("d", False)]
    out = apply_progressive_visibility(items)
    assert [i["slug"] for i in out] == ["a", "b", "c"]
    assert out[1]["is_next_challenge"] is True
    assert all(i["hidden_upcoming_count"] == 1 for i in out)


def test_lista_vuota():
    assert apply_progressive_visibility([]) == []
