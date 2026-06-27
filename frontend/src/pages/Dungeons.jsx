import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import { toast } from "sonner";
import AppHeader from "../components/AppHeader";
import { useT } from "../i18n/I18nContext";
import { Button } from "../components/ui/button";

const DifficultyBadge = ({ value }) => {
    const TIER = { 1: "TIER I", 2: "TIER II", 3: "TIER III", 4: "TIER IV" };
    const TIER_COLOR = { 1: "amber", 2: "rare", 3: "epic", 4: "epic" };
    const tone = TIER_COLOR[value] || "amber";
    const color = tone === "rare" ? "#3b82f6" : tone === "epic" ? "#a855f7" : "#f59e0b";
    return (
        <span
            className="inline-block text-[10px] tracking-widest border px-1.5 py-0.5 rounded-sm"
            style={{ color, borderColor: color + "55" }}
        >
            {TIER[value] || `DIFF ${value}`}
        </span>
    );
};

const LockedBadge = () => (
    <span
        className="inline-block text-[10px] tracking-widest border border-destructive/60 text-destructive px-1.5 py-0.5 rounded-sm"
        data-testid="locked-badge"
    >
        LOCKED
    </span>
);

const Stat = ({ label, value }) => (
    <div className="flex justify-between text-xs py-1 border-b border-border/40 last:border-b-0">
        <span className="text-muted-foreground">{label}</span>
        <span className="text-foreground font-medium">{value}</span>
    </div>
);

const EMPTY_FILTERS = {
    team_size: "",
    pwr_min: "",
    pwr_max: "",
    difficulty: "",
    status: "",
};

const buildQuery = (f) => {
    const params = new URLSearchParams();
    Object.entries(f).forEach(([k, v]) => {
        if (v !== "" && v !== null && v !== undefined) params.set(k, v);
    });
    const s = params.toString();
    return s ? `?${s}` : "";
};

export default function Dungeons() {
    const { t, tContent } = useT();
    const [searchParams, setSearchParams] = useSearchParams();
    const squadIdParam = searchParams.get("squad_id") || "";
    const [activeSquad, setActiveSquad] = useState(null);
    const [squadLoading, setSquadLoading] = useState(false);
    const [dungeons, setDungeons] = useState(null);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState(EMPTY_FILTERS);
    const [panelOpen, setPanelOpen] = useState(false);

    // ROUND 6A.2c — fetch the saved squad referenced by ?squad_id and lock team_size filter.
    useEffect(() => {
        if (!squadIdParam) {
            setActiveSquad(null);
            return;
        }
        let cancelled = false;
        setSquadLoading(true);
        api.get("/squads")
            .then(({ data }) => {
                if (cancelled) return;
                const found = (data.squads || []).find((s) => s.squad_id === squadIdParam);
                if (!found) {
                    toast.error("Squadra non trovata o archiviata");
                    setActiveSquad(null);
                    setSearchParams({}, { replace: true });
                    return;
                }
                if (found.squad_type === "raid_20") {
                    toast.error("Questa squadra è per raid (20), usa /raids");
                    setActiveSquad(null);
                    setSearchParams({}, { replace: true });
                    return;
                }
                setActiveSquad(found);
                const size = found.squad_type === "dungeon_3" ? "3" : "5";
                setFilters((f) => ({ ...f, team_size: size }));
            })
            .catch(() => {
                if (!cancelled) toast.error("Errore caricamento squadra");
            })
            .finally(() => { if (!cancelled) setSquadLoading(false); });
        return () => { cancelled = true; };
    }, [squadIdParam, setSearchParams]);

    const clearSquadFilter = useCallback(() => {
        setActiveSquad(null);
        setFilters((f) => ({ ...f, team_size: "" }));
        const next = new URLSearchParams(searchParams);
        next.delete("squad_id");
        setSearchParams(next, { replace: true });
    }, [searchParams, setSearchParams]);

    const fetchDungeons = useCallback(async (f) => {
        setLoading(true);
        try {
            const { data } = await api.get(`/dungeons${buildQuery(f)}`);
            setDungeons(data.dungeons);
        } catch (err) {
            const detail = err?.response?.data?.detail;
            if (detail && typeof detail === "string" && detail.startsWith("dungeons.")) {
                toast.error(`Filtri non validi: ${detail.replace("dungeons.", "")}`);
            } else {
                toast.error(formatApiError(err));
            }
            setDungeons([]);
        } finally {
            setLoading(false);
        }
    }, []);

    // Debounced refetch on filter change (250ms)
    useEffect(() => {
        const id = setTimeout(() => fetchDungeons(filters), 250);
        return () => clearTimeout(id);
    }, [filters, fetchDungeons]);

    const reset = () => setFilters(EMPTY_FILTERS);
    const setF = (k, v) => setFilters((p) => ({ ...p, [k]: v }));
    const activeCount = Object.values(filters).filter((v) => v !== "").length;
    const squadStartQuery = useMemo(
        () => (activeSquad ? `?squad_id=${activeSquad.squad_id}` : ""),
        [activeSquad],
    );

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg">
            <AppHeader subtitleKey="nav.dungeons" />

            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
                <div className="text-xs text-amber tracking-widest mb-2">
                    :: ACTIVE EXPEDITIONS CATALOG
                </div>
                <h1 className="text-3xl font-semibold tracking-tight">{t("dungeons.title")}</h1>
                <p className="text-sm text-muted-foreground mt-2 max-w-2xl mb-6">
                    Choose a dungeon and dispatch a party. Each run takes time and either
                    rewards your guild or sends them back bruised.
                </p>

                {/* ROUND 6A.2c — Squad context banner */}
                {activeSquad && (
                    <div
                        data-testid="dungeons-squad-banner"
                        className="border border-amber/40 bg-amber/10 rounded-sm px-4 py-3 mb-5 flex items-center justify-between gap-3 flex-wrap"
                    >
                        <div className="text-xs text-amber">
                            <span className="tracking-widest">▶ Stai usando la squadra:</span>{" "}
                            <strong data-testid="dungeons-squad-banner-name">{activeSquad.name}</strong>{" "}
                            <span className="text-muted-foreground">
                                (richiede team da {activeSquad.squad_type === "dungeon_3" ? 3 : 5} avventurieri)
                            </span>
                        </div>
                        <button
                            type="button"
                            data-testid="dungeons-squad-clear"
                            onClick={clearSquadFilter}
                            className="text-[11px] tracking-widest border border-amber/60 text-amber px-3 py-1 rounded-sm hover:bg-amber hover:text-background transition-colors"
                        >
                            ✕ Annulla filtro
                        </button>
                    </div>
                )}
                {squadLoading && (
                    <div className="text-[11px] text-muted-foreground mb-3" data-testid="dungeons-squad-loading">
                        Caricamento squadra...
                    </div>
                )}

                {/* Phase 19.3 — Filter panel (collapsible on mobile) */}
                <div
                    data-testid="dungeon-filters-panel"
                    className="border border-border bg-card rounded-sm mb-5"
                >
                    <button
                        type="button"
                        data-testid="dungeon-filters-toggle"
                        onClick={() => setPanelOpen((v) => !v)}
                        className="w-full flex items-center justify-between px-4 py-3 text-xs tracking-widest text-amber hover:bg-card/80"
                    >
                        <span>
                            ▾ FILTRI{activeCount > 0 ? ` · ${activeCount} attivi` : ""}
                        </span>
                        <span className="text-muted-foreground text-[10px]">
                            {panelOpen ? "nascondi" : "mostra"}
                        </span>
                    </button>
                    <div className={(panelOpen ? "block" : "hidden sm:block") + " px-4 pb-4"}>
                        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs">
                            <div>
                                <label className="block text-muted-foreground text-[10px] mb-1 tracking-widest">SQUADRA</label>
                                <select
                                    data-testid="filter-team-size"
                                    value={filters.team_size}
                                    onChange={(e) => setF("team_size", e.target.value)}
                                    className="w-full bg-background border border-border rounded-sm px-2 py-1 text-foreground"
                                >
                                    <option value="">Tutte</option>
                                    <option value="3">3 eroi</option>
                                    <option value="5">5 eroi</option>
                                    <option value="7">7 eroi</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-muted-foreground text-[10px] mb-1 tracking-widest">PWR MIN</label>
                                <input
                                    type="number"
                                    data-testid="filter-pwr-min"
                                    min="1" max="9999"
                                    value={filters.pwr_min}
                                    onChange={(e) => setF("pwr_min", e.target.value)}
                                    placeholder="—"
                                    className="w-full bg-background border border-border rounded-sm px-2 py-1 text-foreground"
                                />
                            </div>
                            <div>
                                <label className="block text-muted-foreground text-[10px] mb-1 tracking-widest">PWR MAX</label>
                                <input
                                    type="number"
                                    data-testid="filter-pwr-max"
                                    min="1" max="9999"
                                    value={filters.pwr_max}
                                    onChange={(e) => setF("pwr_max", e.target.value)}
                                    placeholder="—"
                                    className="w-full bg-background border border-border rounded-sm px-2 py-1 text-foreground"
                                />
                            </div>
                            <div>
                                <label className="block text-muted-foreground text-[10px] mb-1 tracking-widest">DIFFICOLTÀ</label>
                                <select
                                    data-testid="filter-difficulty"
                                    value={filters.difficulty}
                                    onChange={(e) => setF("difficulty", e.target.value)}
                                    className="w-full bg-background border border-border rounded-sm px-2 py-1 text-foreground"
                                >
                                    <option value="">Tutte</option>
                                    <option value="facile">Facile</option>
                                    <option value="medio">Medio</option>
                                    <option value="difficile">Difficile</option>
                                    <option value="elite">Elite</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-muted-foreground text-[10px] mb-1 tracking-widest">STATO</label>
                                <select
                                    data-testid="filter-status"
                                    value={filters.status}
                                    onChange={(e) => setF("status", e.target.value)}
                                    className="w-full bg-background border border-border rounded-sm px-2 py-1 text-foreground"
                                >
                                    <option value="">Tutti</option>
                                    <option value="available">Disponibili</option>
                                    <option value="locked">Bloccati</option>
                                </select>
                            </div>
                        </div>
                        <div className="mt-3 flex justify-end">
                            <button
                                type="button"
                                data-testid="filter-reset"
                                onClick={reset}
                                className="text-[11px] tracking-widest text-muted-foreground hover:text-amber underline-offset-4 hover:underline"
                            >
                                ↺ Reset filtri
                            </button>
                        </div>
                    </div>
                </div>

                {loading && (
                    <div className="text-xs text-muted-foreground" data-testid="dungeons-loading">
                        {t("common.loading")}<span className="caret-blink" />
                    </div>
                )}

                {!loading && dungeons && dungeons.length === 0 && (
                    <div
                        data-testid="dungeons-empty-state"
                        className="border border-border bg-card rounded-sm p-8 text-center text-sm text-muted-foreground"
                    >
                        {activeSquad ? (
                            <>
                                Nessun dungeon compatibile con la squadra{" "}
                                <strong className="text-foreground">{activeSquad.name}</strong>{" "}
                                (richiede team da {activeSquad.squad_type === "dungeon_3" ? 3 : 5} avventurieri).{" "}
                                <button
                                    type="button"
                                    onClick={clearSquadFilter}
                                    data-testid="dungeons-empty-clear-squad"
                                    className="text-amber underline-offset-4 hover:underline"
                                >
                                    Annulla filtro
                                </button>
                                {" "}per vedere tutti i dungeon.
                            </>
                        ) : activeCount > 0 ? (
                            <>
                                Nessun dungeon corrisponde ai filtri.{" "}
                                <button
                                    type="button"
                                    onClick={reset}
                                    className="text-amber underline-offset-4 hover:underline"
                                >
                                    Resetta i filtri
                                </button>
                                {" "}per vedere tutti.
                            </>
                        ) : (
                            "No dungeons are currently active."
                        )}
                    </div>
                )}

                {!loading && dungeons && dungeons.length > 0 && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                        {dungeons.map((d) => {
                            const locked = d.unlocked === false;
                            return (
                                <div
                                    key={d.id}
                                    data-testid={`dungeon-card-${d.slug}`}
                                    className={
                                        "border bg-card rounded-sm p-5 flex flex-col " +
                                        (locked
                                            ? "border-border/40 opacity-60"
                                            : "border-border")
                                    }
                                >
                                    <div className="flex items-start justify-between gap-2 mb-2">
                                        <div className="text-base font-medium">{d.name}</div>
                                        <div className="flex flex-col items-end gap-1">
                                            <DifficultyBadge value={d.difficulty} />
                                            {locked && <LockedBadge />}
                                        </div>
                                    </div>
                                    <p className="text-xs text-muted-foreground mb-4 flex-1">
                                        {tContent("dungeon", d.slug, "description", d.description)}
                                    </p>
                                    <div className="mb-4">
                                        <Stat label="Required team" value={`${d.required_team_size} heroes`} />
                                        <Stat label="Duration" value={`${d.base_duration_seconds}s`} />
                                        <Stat label="Recommended power" value={d.recommended_power} />
                                        <Stat label="Base reward" value={`${d.base_gold_reward}g`} />
                                        <Stat label="XP per hero" value={d.base_xp_reward} />
                                    </div>
                                    {locked ? (
                                        <div
                                            data-testid={`dungeon-locked-reason-${d.slug}`}
                                            className="text-[11px] text-muted-foreground border border-border/40 bg-secondary/20 px-3 py-2 rounded-sm"
                                            title={d.unlock_reason || ""}
                                        >
                                            🔒 {d.unlock_reason || "Locked"}
                                        </div>
                                    ) : (
                                        <Link to={`/dungeons/${d.slug}/start${squadStartQuery}`}>
                                            <Button
                                                data-testid={`start-dungeon-${d.slug}`}
                                                className="w-full h-10 rounded-sm bg-primary text-primary-foreground hover:bg-primary/90"
                                            >
                                                Start Expedition →
                                            </Button>
                                        </Link>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
            </main>
        </div>
    );
}
