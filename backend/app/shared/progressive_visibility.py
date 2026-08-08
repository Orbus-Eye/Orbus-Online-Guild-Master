"""FASE 1.9 (2026-08-08) — Visibilità progressiva dei contenuti.

Regola condivisa da dungeon e raid: il giocatore vede tutti i contenuti
sbloccati PIÙ soltanto il primo bloccato in ordine di progressione (il
teaser "prossima sfida"); tutto ciò che viene dopo resta nascosto finché
la progressione non lo raggiunge.

La regola è indipendente dal TIPO di gate (oggi potere-picco gilda /
livello, domani potere del gruppo — Fase 2), quindi sopravvive ai
rebalance: lavora solo sul flag `unlocked` già calcolato a monte.

Pure function, nessun I/O → unit-testabile senza Mongo.
"""
from __future__ import annotations


def apply_progressive_visibility(items: list[dict]) -> list[dict]:
    """Filtra una lista ORDINATA per progressione di dict con `unlocked`.

    Muta i dict visibili aggiungendo:
      * ``is_next_challenge``: True solo sul primo item bloccato visibile
      * ``hidden_upcoming_count``: quanti item restano nascosti (uguale
        su tutti i visibili, così il FE lo legge dal primo elemento)

    Ritorna la nuova lista visibile (l'input non viene troncato in place).
    """
    visible: list[dict] = []
    teaser_shown = False
    hidden_count = 0
    for item in items:
        if item.get("unlocked"):
            item["is_next_challenge"] = False
            visible.append(item)
        elif not teaser_shown:
            item["is_next_challenge"] = True
            visible.append(item)
            teaser_shown = True
        else:
            hidden_count += 1
    for item in visible:
        item["hidden_upcoming_count"] = hidden_count
    return visible


__all__ = ["apply_progressive_visibility"]
