// ROUND 11.4c — Data-driven catalog sections extracted from `Guide.jsx`.
//
// Each section owns its own fetch lifecycle (lazy: only fires when the
// section becomes active for the first time). Keeps the parent `Guide.jsx`
// free of network state.
import { useEffect, useState } from "react";
import { api, formatApiError } from "../../lib/api";
import { SectionBlock } from "./_shared";

// ─── STATS CATALOG ───────────────────────────────────────────────────────
export function StatsCatalogSection({ active }) {
    const [stats, setStats] = useState({ data: null, loading: false, error: null });

    useEffect(() => {
        if (active !== "stats-catalog") return;
        if (stats.data !== null || stats.loading) return;
        setStats((s) => ({ ...s, loading: true, error: null }));
        api.get("/stats/catalog")
            .then((r) => setStats({ data: r.data?.stats || [], loading: false, error: null }))
            .catch((err) => setStats({ data: [], loading: false, error: formatApiError(err) }));
    }, [active, stats.data, stats.loading]);

    return (
        <SectionBlock id="stats-catalog" title="Statistiche">
            <p>
                Catalogo completo delle <strong>statistiche</strong> che governano avventurieri, spedizioni e ranking.
                Dati caricati live dal server: se il team aggiunge una nuova stat, compare qui senza un nuovo deploy
                della Guida. La colonna <em>PWR</em> indica se la stat concorre al calcolo del Power Score totale.
            </p>
            {stats.loading && (
                <p className="mt-3 text-[12px] text-muted-foreground italic" data-testid="guide-stats-loading">
                    Caricamento del catalogo stat…
                </p>
            )}
            {stats.error && !stats.loading && (
                <p className="mt-3 text-[12px] text-red-400" data-testid="guide-stats-error">
                    Errore nel caricamento: {stats.error}
                </p>
            )}
            {!stats.loading && !stats.error && stats.data && (
                <div className="mt-3 overflow-x-auto" data-testid="guide-stats-table-wrap">
                    <table className="w-full text-[12px] min-w-[560px]" data-testid="guide-stats-table">
                        <thead className="border-b border-border">
                            <tr className="text-left text-muted-foreground">
                                <th className="py-2 px-2">Stat</th>
                                <th className="py-2 px-2">Descrizione</th>
                                <th className="py-2 px-2 text-center">PWR</th>
                                <th className="py-2 px-2">Note</th>
                            </tr>
                        </thead>
                        <tbody>
                            {stats.data.map((s) => (
                                <tr
                                    key={s.key}
                                    data-testid={`guide-stat-row-${s.key}`}
                                    className="border-b border-border/40 align-top"
                                >
                                    <td className="py-2 px-2 font-mono whitespace-nowrap">
                                        <strong>{s.display_name_it}</strong>
                                        <div className="text-[10px] text-muted-foreground">{s.key}</div>
                                    </td>
                                    <td className="py-2 px-2 text-foreground/90">{s.description_it}</td>
                                    <td className="py-2 px-2 text-center">
                                        {s.affects_pwr ? (
                                            <span className="text-amber">✓</span>
                                        ) : (
                                            <span className="text-muted-foreground">—</span>
                                        )}
                                    </td>
                                    <td className="py-2 px-2 text-[11px] text-muted-foreground">
                                        {s.implemented === false
                                            ? "documentazione, non ancora applicata nei calcoli"
                                            : (s.ui_locations || []).join(" · ")}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    <p className="mt-2 text-[10px] text-muted-foreground" data-testid="guide-stats-total">
                        {stats.data.length} stat documentate (fonte: <code>/api/stats/catalog</code>)
                    </p>
                </div>
            )}
        </SectionBlock>
    );
}

// FASE 9H — TraitsCatalogSection rimossa: i Tratti non sono più
// player-facing (il runtime resta attivo, vedi report).
