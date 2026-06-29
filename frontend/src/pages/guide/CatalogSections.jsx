// ROUND 11.4c — Data-driven catalog sections extracted from `Guide.jsx`.
//
// Each section owns its own fetch lifecycle (lazy: only fires when the
// section becomes active for the first time). Keeps the parent `Guide.jsx`
// free of network state.
import { useEffect, useState } from "react";
import { api, formatApiError } from "../../lib/api";
import {
    SectionBlock,
    POLARITY_LABEL,
    RARITY_LABEL,
    formatModifier,
} from "./_shared";

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

// ─── TRAITS CATALOG ──────────────────────────────────────────────────────
export function TraitsCatalogSection({ active }) {
    const [traits, setTraits] = useState({ data: null, loading: false, error: null });
    const [filters, setFilters] = useState({ q: "", polarity: "all", rarity: "all" });

    useEffect(() => {
        if (active !== "traits-catalog") return;
        if (traits.data !== null || traits.loading) return;
        setTraits((s) => ({ ...s, loading: true, error: null }));
        api.get("/traits/catalog")
            .then((r) => setTraits({ data: r.data?.traits || [], loading: false, error: null }))
            .catch((err) => setTraits({ data: [], loading: false, error: formatApiError(err) }));
    }, [active, traits.data, traits.loading]);

    const filtered = (traits.data || []).filter((t) => {
        if (filters.polarity !== "all") {
            if (filters.polarity === "mixed") {
                if (t.polarity !== "mixed" && t.polarity !== "neutral") return false;
            } else if (t.polarity !== filters.polarity) {
                return false;
            }
        }
        if (filters.rarity !== "all" && t.rarity !== filters.rarity) return false;
        if (filters.q) {
            const q = filters.q.toLowerCase();
            const hay = `${t.display_name_it || ""} ${t.description_it || ""} ${t.gameplay_effect_it || ""}`.toLowerCase();
            if (!hay.includes(q)) return false;
        }
        return true;
    });

    return (
        <SectionBlock id="traits-catalog" title="Tratti">
            <p>
                Catalogo completo dei <strong>tratti</strong> che gli avventurieri possono ottenere alla
                generazione. Dati caricati live dal server: nessun tratto interno/di test compare in elenco
                (filtraggio automatico server-side per <code>is_test</code> e <code>is_active</code>).
            </p>
            {!traits.loading && !traits.error && traits.data && (
                <div className="mt-4 flex flex-col sm:flex-row gap-2" data-testid="guide-traits-filters">
                    <input
                        type="text"
                        value={filters.q}
                        onChange={(e) => setFilters({ ...filters, q: e.target.value })}
                        placeholder="Cerca per nome o descrizione…"
                        data-testid="guide-traits-filter-q"
                        className="flex-1 bg-secondary border border-border rounded-sm px-3 py-2 text-xs"
                    />
                    <select
                        value={filters.polarity}
                        onChange={(e) => setFilters({ ...filters, polarity: e.target.value })}
                        data-testid="guide-traits-filter-polarity"
                        className="bg-secondary border border-border rounded-sm px-3 py-2 text-xs"
                    >
                        <option value="all">Polarità: tutte ({traits.data?.length || 0})</option>
                        <option value="positive">Positivi ({(traits.data || []).filter(t=>t.polarity==='positive').length})</option>
                        <option value="negative">Negativi ({(traits.data || []).filter(t=>t.polarity==='negative').length})</option>
                        <option value="mixed">Misti + Neutri ({(traits.data || []).filter(t=>t.polarity==='mixed'||t.polarity==='neutral').length})</option>
                    </select>
                    <select
                        value={filters.rarity}
                        onChange={(e) => setFilters({ ...filters, rarity: e.target.value })}
                        data-testid="guide-traits-filter-rarity"
                        className="bg-secondary border border-border rounded-sm px-3 py-2 text-xs"
                    >
                        <option value="all">Rarità: tutte</option>
                        <option value="common">Comune</option>
                        <option value="uncommon">Non comune</option>
                        <option value="rare">Raro</option>
                        <option value="epic">Epico</option>
                        <option value="legendary">Leggendario</option>
                    </select>
                </div>
            )}

            {traits.loading && (
                <p className="mt-3 text-[12px] text-muted-foreground italic" data-testid="guide-traits-loading">
                    Caricamento del catalogo tratti…
                </p>
            )}
            {traits.error && !traits.loading && (
                <p className="mt-3 text-[12px] text-red-400" data-testid="guide-traits-error">
                    Errore nel caricamento: {traits.error}
                </p>
            )}
            {!traits.loading && !traits.error && traits.data && (
                <>
                    <div className="mt-3 grid gap-2 sm:grid-cols-2" data-testid="guide-traits-grid">
                        {filtered.map((t) => {
                            const pol = POLARITY_LABEL[t.polarity] || POLARITY_LABEL.positive;
                            return (
                                <div
                                    key={t.id}
                                    data-testid={`guide-trait-card-${t.id}`}
                                    className="border border-border rounded-sm p-3 bg-card/60"
                                >
                                    <div className="flex items-center justify-between gap-2">
                                        <strong className="text-sm">{t.display_name_it}</strong>
                                        <span
                                            className={`text-[10px] tracking-widest px-1.5 py-0.5 border rounded-sm ${pol.cls}`}
                                            data-testid={`guide-trait-polarity-${t.id}`}
                                        >
                                            {pol.label}
                                        </span>
                                    </div>
                                    <p className="text-[12px] text-foreground/85 mt-1">{t.description_it}</p>
                                    <p className="text-[11px] text-amber/90 mt-1.5 italic" data-testid={`guide-trait-effect-${t.id}`}>
                                        {t.gameplay_effect_it || "Tratto descrittivo: al momento non modifica direttamente i calcoli principali."}
                                    </p>
                                    <div className="mt-2 flex flex-wrap gap-3 text-[10px] text-muted-foreground">
                                        <span>
                                            Rarità: <strong className="text-foreground/90">{RARITY_LABEL[t.rarity] || t.rarity}</strong>
                                        </span>
                                        {t.affected_stat && (
                                            <span>
                                                Stat: <strong className="text-foreground/90">{t.affected_stat}</strong>{" "}
                                                ({formatModifier(t.modifier_type, t.modifier_value)})
                                            </span>
                                        )}
                                        {t.affects_power && <span className="text-amber">Influenza PWR</span>}
                                        {t.is_situational && <span>Situazionale</span>}
                                        {t.is_capped && <span>Cappato</span>}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                    {filtered.length === 0 && (
                        <p className="mt-3 text-[12px] text-muted-foreground italic" data-testid="guide-traits-empty">
                            Nessun tratto corrisponde ai filtri selezionati.
                        </p>
                    )}
                    <p className="mt-3 text-[10px] text-muted-foreground" data-testid="guide-traits-total">
                        {filtered.length} di {traits.data.length} tratti visibili
                        (fonte: <code>/api/traits/catalog</code>, filtra automaticamente
                        <code> is_test=true</code> e <code>is_active=false</code>)
                    </p>
                </>
            )}
        </SectionBlock>
    );
}
