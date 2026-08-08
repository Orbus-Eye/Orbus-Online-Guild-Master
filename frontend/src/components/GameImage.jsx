// FASE 4 (2026-08-08) — Immagine di gioco con catena di fallback.
//
// <GameImage sources={[a, b, c]} .../> prova `a`; se il file manca o è
// rotto passa a `b`, poi `c`. Se TUTTA la catena fallisce non renderizza
// nulla (mai icone rotte in pagina). Le catene arrivano da
// utils/gameAssets.js — così l'art definitiva sostituisce i file senza
// toccare il codice.
import { useEffect, useState } from "react";

export default function GameImage({ sources, alt = "", className = "", ...rest }) {
    const [idx, setIdx] = useState(0);
    const chain = Array.isArray(sources) ? sources : [sources];

    // Nuova catena (es. cambio dungeon selezionato) → riparti dal primo.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    useEffect(() => { setIdx(0); }, [chain.join("|")]);

    if (idx >= chain.length) return null;
    return (
        <img
            src={chain[idx]}
            alt={alt}
            loading="lazy"
            draggable={false}
            className={className}
            onError={() => setIdx((i) => i + 1)}
            {...rest}
        />
    );
}
