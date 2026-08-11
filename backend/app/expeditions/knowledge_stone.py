"""FASE 9J — Pietra della Conoscenza: policy di drop UNICA e condivisa.

Audit del mandato (identificatore, effetto, compatibilità, drop, copertura):
  * item: `pietra_della_conoscenza` ("Pietra della Conoscenza", Rare,
    consumabile NON craftabile — seed FASE 3.4);
  * effetto reale: `consumable_effect = {type: "xp_boost",
    magnitude: 0.5, charges: 5}` → +50% XP per le prossime 5 spedizioni
    dell'avventuriero che la porta nello scomparto Consumabile;
  * drop CANONICO: 20% flat, SOLO su dungeon conclusi con successo,
    tiro indipendente aggiunto DOPO l'Overpower (mai moltiplicato);
  * copertura: TUTTI i dungeon attivi — ogni completamento passa da
    `apply`-path legacy (`services._complete_one_expedition`) o dal
    finalize a stanze (`rooms_engine`), ed entrambi usano QUESTO helper.

Prima della FASE 9J la stessa logica era duplicata inline nei due
moduli (allineata, ma non blindata): ora un solo punto di verità.
"""
from __future__ import annotations

KNOWLEDGE_STONE_SLUG = "pietra_della_conoscenza"
KNOWLEDGE_STONE_DROP_RATE = 0.20


async def maybe_roll_knowledge_stone(db, *, success: bool, rng) -> str | None:
    """Ritorna l'item id della Pietra se il tiro (20%) riesce, altrimenti None.

    Regole: mai su fallimento; mai moltiplicata dall'Overpower (il
    chiamante la aggiunge DOPO quel blocco); nessun crash se il seed
    FASE 3 non è ancora stato applicato all'ambiente.
    """
    if not success:
        return None
    try:
        if rng.random() >= KNOWLEDGE_STONE_DROP_RATE:
            return None
        stone = await db.items.find_one(
            {"slug": KNOWLEDGE_STONE_SLUG, "is_active": True},
            {"_id": 0, "id": 1},
        )
        return stone["id"] if stone else None
    except Exception:  # noqa: BLE001
        return None  # seed fase 3 assente: niente pietra, nessun crash


__all__ = [
    "KNOWLEDGE_STONE_DROP_RATE",
    "KNOWLEDGE_STONE_SLUG",
    "maybe_roll_knowledge_stone",
]
