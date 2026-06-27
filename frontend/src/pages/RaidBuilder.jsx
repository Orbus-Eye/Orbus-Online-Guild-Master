// Phase 18.1 — Raid Builder (4 party × 5).
// Phase 19.4a — added roster filter panel (search/role/class/rarity/level/PWR
// /availability/sort). Filters don't break drag/select; assigned advs are
// always excluded from the pool and the disable-once-full guard is preserved.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { toast } from "sonner";

import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";
import { useT } from "../i18n/I18nContext";
import RoleMarker from "../components/RoleMarker";


const PARTY_COUNT = 4;
const PARTY_SIZE = 5;

const EMPTY_FILTERS = {
    q: "",
    roles: [],          // multi-select
    klass: "",
    rarities: [],       // multi-select
    level_min: "",
    level_max: "",
    pwr_min: "",
    pwr_max: "",
    availability: "all", // all | available_only | hide_assigned
    sort: "pwr_desc",   // pwr_desc | level_desc | rarity_desc | name | role
};

const RARITY_ORDER = { Common: 1, Uncommon: 2, Rare: 3, Epic: 4, Legendary: 5 };


export default function RaidBuilder() {
    const { t, lang } = useT();
    const { slug } = useParams();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const squadIdParam = searchParams.get("squad_id") || "";
    const autoLoadedRef = useRef(false);
    const [raidDungeon, setRaidDungeon] = useState(null);
    const [advs, setAdvs] = useState([]);
    const [parties, setParties] = useState(
        () => Array.from({ length: PARTY_COUNT }, () => Array(PARTY_SIZE).fill(null)),
    );
    const [preview, setPreview] = useState(null);
    const [busy, setBusy] = useState(false);
    const [filters, setFilters] = useState(EMPTY_FILTERS);
    const [panelOpen, setPanelOpen] = useState(false);
    // ROUND 6A.2b — saved raid_20 squads
    const [squads, setSquads] = useState([]);

    useEffect(() => {
        api.get("/squads?type=raid_20")
            .then(({ data }) => setSquads(data.squads || []))
            .catch(() => setSquads([]));
    }, []);

    // Apply a saved raid_20 squad to the 4×5 grid. Uses `raid_parties`
    // if present, otherwise distributes adventurer_ids sequentially.
    // Skips ids not in current available roster (toasts a count).
    const loadSquadIntoParties = (squadId) => {
        if (!squadId) return;
        const sq = squads.find((s) => s.squad_id === squadId);
        if (!sq) return;
        const byId = new Map(advs.map((a) => [a.id, a]));
        const next = Array.from({ length: PARTY_COUNT }, () => Array(PARTY_SIZE).fill(null));
        let missing = 0;
        if (sq.raid_parties) {
            const partyKeys = ["party_1", "party_2", "party_3", "party_4"];
            for (let pi = 0; pi < PARTY_COUNT; pi++) {
                const ids = sq.raid_parties[partyKeys[pi]] || [];
                for (let si = 0; si < PARTY_SIZE; si++) {
                    const aid = ids[si];
                    if (aid && byId.has(aid)) next[pi][si] = aid;
                    else if (aid) missing += 1;
                }
            }
        } else {
            // Fallback: flat distribution 5+5+5+5
            const flat = sq.adventurer_ids || [];
            for (let i = 0; i < flat.length && i < 20; i++) {
                const aid = flat[i];
                const pi = Math.floor(i / PARTY_SIZE);
                const si = i % PARTY_SIZE;
                if (byId.has(aid)) next[pi][si] = aid;
                else missing += 1;
            }
        }
        setParties(next);
        if (missing > 0) {
            toast.warning(`${missing} avventuriere/i della squadra non disponibili. Completa manualmente.`);
        } else {
            toast.success(`Squadra "${sq.name}" caricata`);
        }
    };

    // ROUND 6A.2c — auto-load squad from ?squad_id once raid + squads + advs are ready.
    // RATIONALE (ROUND 6B FASE B): `loadSquadIntoParties` is intentionally
    // NOT in the dep list. The `autoLoadedRef` guard makes this effect
    // strictly one-shot per mount; the listed deps are the SEMANTIC
    // readiness signal (raid + squads + advs all hydrated, then fire once).
    useEffect(() => {
        if (!squadIdParam || autoLoadedRef.current) return;
        if (!raidDungeon || squads.length === 0 || advs.length === 0) return;
        const sq = squads.find((s) => s.squad_id === squadIdParam);
        if (!sq) {
            autoLoadedRef.current = true;
            toast.error("Squadra raid non trovata");
            return;
        }
        autoLoadedRef.current = true;
        loadSquadIntoParties(squadIdParam);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [squadIdParam, raidDungeon, squads, advs]);

    // ROUND 6B FASE B — wrapped in useCallback so its identity is stable;
    // the effect below can list `load` directly (no disable directive).
    const load = useCallback(async () => {
        try {
            const [cat, advR] = await Promise.all([
                api.get("/raids/catalog"),
                api.get("/adventurers"),
            ]);
            const rd = cat.data.raid_dungeons.find((r) => r.slug === slug);
            if (!rd) {
                toast.error("Raid non trovato");
                navigate("/raids");
                return;
            }
            setRaidDungeon(rd);
            setAdvs(advR.data.adventurers || []);
        } catch (err) {
            toast.error(formatApiError(err));
        }
    }, [slug, navigate]);
    useEffect(() => { load(); }, [load]);

    const assignedIds = useMemo(() => {
        const s = new Set();
        for (const p of parties) for (const id of p) if (id) s.add(id);
        return s;
    }, [parties]);

    const totalAssigned = assignedIds.size;

    // Distinct class list for filter dropdown (computed once from roster)
    const classOptions = useMemo(() => {
        const set = new Set(advs.map((a) => a.class_name).filter(Boolean));
        return Array.from(set).sort();
    }, [advs]);

    // P19.4a — full filter pipeline.
    // assignedIds: ALWAYS excluded (rule: an adv assigned to a party can't be
    // picked again from the pool).
    const available = useMemo(() => {
        const q = filters.q.trim().toLowerCase();
        const lvlMin = filters.level_min === "" ? null : Number(filters.level_min);
        const lvlMax = filters.level_max === "" ? null : Number(filters.level_max);
        const pwrMin = filters.pwr_min === "" ? null : Number(filters.pwr_min);
        const pwrMax = filters.pwr_max === "" ? null : Number(filters.pwr_max);

        let rows = advs.filter((a) => {
            // Hard rule (kept from previous behaviour): never pick already-assigned
            if (assignedIds.has(a.id)) return false;
            // Availability mode
            if (filters.availability === "available_only" && !a.is_available) return false;
            if (filters.availability === "hide_assigned" && !a.is_available) return false;
            if (filters.availability === "all") {/* keep busy advs visible (disabled) */ }
            // Search
            if (q && !(a.name || "").toLowerCase().includes(q)) return false;
            // Roles
            if (filters.roles.length && !filters.roles.includes(a.class_role)) return false;
            // Class
            if (filters.klass && a.class_name !== filters.klass) return false;
            // Rarities
            if (filters.rarities.length && !filters.rarities.includes(a.rarity)) return false;
            // Level range
            if (lvlMin !== null && (a.level || 0) < lvlMin) return false;
            if (lvlMax !== null && (a.level || 0) > lvlMax) return false;
            // PWR range
            if (pwrMin !== null && (a.total_power || 0) < pwrMin) return false;
            if (pwrMax !== null && (a.total_power || 0) > pwrMax) return false;
            return true;
        });

        const cmp = {
            pwr_desc: (x, y) => (y.total_power || 0) - (x.total_power || 0),
            level_desc: (x, y) => (y.level || 0) - (x.level || 0),
            rarity_desc: (x, y) =>
                (RARITY_ORDER[y.rarity] || 0) - (RARITY_ORDER[x.rarity] || 0),
            name: (x, y) => (x.name || "").localeCompare(y.name || ""),
            role: (x, y) => (x.class_role || "").localeCompare(y.class_role || ""),
        }[filters.sort] || ((x, y) => (y.total_power || 0) - (x.total_power || 0));
        rows = rows.slice().sort(cmp);
        return rows;
    }, [advs, assignedIds, filters]);

    function nextEmptySlot(partyIdx) {
        return parties[partyIdx].findIndex((x) => x === null);
    }

    function assignAdv(advId, targetPartyIdx) {
        if (assignedIds.has(advId)) return;
        // Block assigning a busy adv (is_available=false) — same as before
        const a = advs.find((x) => x.id === advId);
        if (a && a.is_available === false) {
            toast.error("Avventuriero non disponibile");
            return;
        }
        const partyIdx = targetPartyIdx ?? parties.findIndex((p) => p.includes(null));
        if (partyIdx < 0 || partyIdx >= PARTY_COUNT) return;
        const slotIdx = nextEmptySlot(partyIdx);
        if (slotIdx < 0) return;
        const next = parties.map((p) => [...p]);
        next[partyIdx][slotIdx] = advId;
        setParties(next);
        setPreview(null);
    }

    function removeAdv(advId) {
        const next = parties.map((p) => p.map((x) => (x === advId ? null : x)));
        setParties(next);
        setPreview(null);
    }

    function advName(id) {
        const a = advs.find((x) => x.id === id);
        if (!a) return "?";
        return `${a.name} L${a.level} (${a.class_role || "?"})`;
    }

    // Filter helpers
    const setF = (k, v) => setFilters((p) => ({ ...p, [k]: v }));
    const toggleInArr = (k, v) =>
        setFilters((p) => {
            const arr = p[k];
            return { ...p, [k]: arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v] };
        });
    const resetFilters = () => setFilters(EMPTY_FILTERS);
    const activeFilterCount =
        (filters.q ? 1 : 0) +
        (filters.roles.length ? 1 : 0) +
        (filters.klass ? 1 : 0) +
        (filters.rarities.length ? 1 : 0) +
        (filters.level_min !== "" ? 1 : 0) +
        (filters.level_max !== "" ? 1 : 0) +
        (filters.pwr_min !== "" ? 1 : 0) +
        (filters.pwr_max !== "" ? 1 : 0) +
        (filters.availability !== "all" ? 1 : 0) +
        (filters.sort !== "pwr_desc" ? 1 : 0);

    function payload() {
        return {
            raid_slug: slug,
            parties: parties.map((advs5, i) => ({
                party_idx: i + 1,
                adventurer_ids: advs5,
            })),
        };
    }

    async function doPreview() {
        if (totalAssigned < PARTY_COUNT * PARTY_SIZE) {
            toast.error(t("raids.builder.not_enough", { have: totalAssigned }));
            return;
        }
        setBusy(true);
        try {
            const r = await api.post("/raids/preview", payload());
            setPreview(r.data);
            toast.success(t("raids.builder.preview_done"));
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setBusy(false);
        }
    }

    async function doLaunch() {
        if (!preview) return;
        setBusy(true);
        try {
            const r = await api.post("/raids/start", payload());
            toast.success(t("raids.builder.launched"));
            navigate(`/raids/${r.data.raid.id}/report`);
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setBusy(false);
        }
    }

    if (!raidDungeon) {
        return (
            <div className="min-h-screen bg-background text-foreground">
                <AppHeader />
                <main className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
                    <div className="text-xs text-muted-foreground">…</div>
                </main>
            </div>
        );
    }

    const focusHints = raidDungeon.party_focus_hints || [];
    const raidName = lang === "it"
        ? t(`raids.catalog.${slug}.name`)
        : (raidDungeon.name || t(`raids.catalog.${slug}.name`));

    return (
        <div className="min-h-screen bg-background text-foreground">
            <AppHeader />
            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-6" data-testid="raid-builder-page">
                <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
                    <h1 className="text-xs tracking-[0.3em] text-amber">
                        :: {t("raids.builder.title")} — {raidName}
                    </h1>
                    <Link to="/raids" className="text-[11px] text-muted-foreground hover:underline" data-testid="builder-back-link">
                        {t("raids.builder.back_to_raids")}
                    </Link>
                </div>

                {/* ROUND 6A.2b — Carica squadra raid_20 */}
                <div className="mb-4 border border-neutral-800 rounded-sm p-3 bg-secondary/30">
                    <div className="text-[10px] text-muted-foreground tracking-widest mb-2">
                        :: CARICA SQUADRA RAID 20 ({squads.length})
                    </div>
                    {squads.length === 0 ? (
                        <div className="flex items-center justify-between gap-3 flex-wrap">
                            <p className="text-[11px] text-muted-foreground italic">
                                Nessuna squadra raid_20 salvata.
                            </p>
                            <Link
                                to="/squads/new?type=raid_20"
                                data-testid="raid-create-squad-link"
                                className="text-[11px] tracking-widest border border-amber/60 text-amber px-3 py-1 hover:bg-amber hover:text-background transition-colors"
                            >
                                + Crea squadra ora
                            </Link>
                        </div>
                    ) : (
                        <div className="flex items-center gap-2 flex-wrap">
                            <select
                                onChange={(e) => loadSquadIntoParties(e.target.value)}
                                defaultValue=""
                                data-testid="raid-load-squad"
                                className="bg-secondary border border-neutral-700 px-3 py-1.5 text-xs focus:border-amber outline-none flex-1 min-w-[200px]"
                            >
                                <option value="">— Seleziona squadra raid 20 —</option>
                                {squads.map((s) => (
                                    <option key={s.squad_id} value={s.squad_id}>
                                        {s.name} (PWR {s.total_power}{s.missing_adventurer_ids?.length ? ` · ⚠ ${s.missing_adventurer_ids.length} mancanti` : ""})
                                    </option>
                                ))}
                            </select>
                            <Link
                                to="/squads"
                                className="text-[10px] tracking-widest text-muted-foreground hover:text-foreground"
                            >
                                Gestisci →
                            </Link>
                        </div>
                    )}
                </div>

                {/* 4 party columns */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
                    {parties.map((slots, idx) => {
                        const focus = focusHints[idx] || {};
                        const focusLabel = lang === "it" ? focus.label_it : focus.label_en;
                        return (
                            <div
                                key={idx}
                                data-testid={`raid-party-${idx + 1}`}
                                className="border border-border bg-card rounded-sm p-3"
                            >
                                <div className="text-[11px] tracking-widest text-amber mb-1">
                                    {t("raids.builder.party_label", { n: idx + 1 })}
                                </div>
                                {focusLabel && (
                                    <div className="text-[10px] text-muted-foreground italic mb-2">
                                        {focusLabel} {focus.preferred_role ? `(${focus.preferred_role})` : ""}
                                    </div>
                                )}
                                <ul className="space-y-1">
                                    {slots.map((advId, slotIdx) => (
                                        <li
                                            key={slotIdx}
                                            data-testid={`party-${idx + 1}-slot-${slotIdx + 1}`}
                                            className={`text-[11px] border ${advId ? "border-border" : "border-dashed border-border/40"} rounded-sm px-2 py-1.5 flex items-center justify-between gap-1`}
                                        >
                                            <span className="truncate">{advId ? advName(advId) : "—"}</span>
                                            {advId && (
                                                <button
                                                    onClick={() => removeAdv(advId)}
                                                    data-testid={`remove-${advId}`}
                                                    className="text-[10px] text-muted-foreground hover:text-destructive"
                                                >
                                                    ✕
                                                </button>
                                            )}
                                        </li>
                                    ))}
                                </ul>
                                {preview && (
                                    <div className="mt-2 text-[10px] text-muted-foreground" data-testid={`party-${idx + 1}-preview`}>
                                        pwr {preview.party_powers?.[idx] ?? "?"} · {preview.success_chance_per_party?.[idx] ?? "?"}%
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>

                {/* Phase 19.4a — Roster filter panel (collapsible on mobile) */}
                <section
                    data-testid="raid-roster-filters"
                    className="border border-border bg-card rounded-sm mb-3"
                >
                    <button
                        type="button"
                        data-testid="raid-filters-toggle"
                        onClick={() => setPanelOpen((v) => !v)}
                        className="w-full flex items-center justify-between px-4 py-2 text-xs tracking-widest text-amber hover:bg-card/80"
                    >
                        <span>▾ FILTRI ROSTER{activeFilterCount > 0 ? ` · ${activeFilterCount} attivi` : ""}</span>
                        <span className="text-[10px] text-muted-foreground">
                            {panelOpen ? "nascondi" : "mostra"}
                        </span>
                    </button>
                    <div className={(panelOpen ? "block" : "hidden sm:block") + " px-4 pb-3 pt-1"}>
                        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-2 text-xs">
                            <div className="col-span-2 sm:col-span-2">
                                <label className="block text-muted-foreground text-[10px] mb-1 tracking-widest">CERCA NOME</label>
                                <input
                                    type="text"
                                    data-testid="raid-filter-q"
                                    value={filters.q}
                                    onChange={(e) => setF("q", e.target.value)}
                                    placeholder="es. Aria"
                                    className="w-full bg-background border border-border rounded-sm px-2 py-1 text-foreground"
                                />
                            </div>
                            <div>
                                <label className="block text-muted-foreground text-[10px] mb-1 tracking-widest">CLASSE</label>
                                <select
                                    data-testid="raid-filter-class"
                                    value={filters.klass}
                                    onChange={(e) => setF("klass", e.target.value)}
                                    className="w-full bg-background border border-border rounded-sm px-2 py-1 text-foreground"
                                >
                                    <option value="">Tutte</option>
                                    {classOptions.map((c) => (
                                        <option key={c} value={c}>{c}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-muted-foreground text-[10px] mb-1 tracking-widest">DISPONIBILITÀ</label>
                                <select
                                    data-testid="raid-filter-availability"
                                    value={filters.availability}
                                    onChange={(e) => setF("availability", e.target.value)}
                                    className="w-full bg-background border border-border rounded-sm px-2 py-1 text-foreground"
                                >
                                    <option value="all">Tutti</option>
                                    <option value="available_only">Solo disponibili</option>
                                    <option value="hide_assigned">Nascondi occupati</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-muted-foreground text-[10px] mb-1 tracking-widest">ORDINA</label>
                                <select
                                    data-testid="raid-filter-sort"
                                    value={filters.sort}
                                    onChange={(e) => setF("sort", e.target.value)}
                                    className="w-full bg-background border border-border rounded-sm px-2 py-1 text-foreground"
                                >
                                    <option value="pwr_desc">PWR ↓</option>
                                    <option value="level_desc">Livello ↓</option>
                                    <option value="rarity_desc">Rarità ↓</option>
                                    <option value="name">Nome</option>
                                    <option value="role">Ruolo</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-muted-foreground text-[10px] mb-1 tracking-widest">LIV MIN</label>
                                <input
                                    type="number" min="1" max="99"
                                    data-testid="raid-filter-level-min"
                                    value={filters.level_min}
                                    onChange={(e) => setF("level_min", e.target.value)}
                                    placeholder="—"
                                    className="w-full bg-background border border-border rounded-sm px-2 py-1 text-foreground"
                                />
                            </div>
                            <div>
                                <label className="block text-muted-foreground text-[10px] mb-1 tracking-widest">LIV MAX</label>
                                <input
                                    type="number" min="1" max="99"
                                    data-testid="raid-filter-level-max"
                                    value={filters.level_max}
                                    onChange={(e) => setF("level_max", e.target.value)}
                                    placeholder="—"
                                    className="w-full bg-background border border-border rounded-sm px-2 py-1 text-foreground"
                                />
                            </div>
                            <div>
                                <label className="block text-muted-foreground text-[10px] mb-1 tracking-widest">PWR MIN</label>
                                <input
                                    type="number" min="1" max="9999"
                                    data-testid="raid-filter-pwr-min"
                                    value={filters.pwr_min}
                                    onChange={(e) => setF("pwr_min", e.target.value)}
                                    placeholder="—"
                                    className="w-full bg-background border border-border rounded-sm px-2 py-1 text-foreground"
                                />
                            </div>
                            <div>
                                <label className="block text-muted-foreground text-[10px] mb-1 tracking-widest">PWR MAX</label>
                                <input
                                    type="number" min="1" max="9999"
                                    data-testid="raid-filter-pwr-max"
                                    value={filters.pwr_max}
                                    onChange={(e) => setF("pwr_max", e.target.value)}
                                    placeholder="—"
                                    className="w-full bg-background border border-border rounded-sm px-2 py-1 text-foreground"
                                />
                            </div>
                        </div>
                        <div className="mt-3 flex flex-wrap gap-3 items-center">
                            <div className="flex gap-1 flex-wrap">
                                {["Tank", "Healer", "DPS", "Support", "Control", "Stratega"].map((r) => (
                                    <button
                                        type="button"
                                        key={r}
                                        data-testid={`raid-filter-role-${r.toLowerCase()}`}
                                        onClick={() => toggleInArr("roles", r)}
                                        className={
                                            "text-[10px] tracking-widest border px-2 py-0.5 rounded-sm transition-colors " +
                                            (filters.roles.includes(r)
                                                ? "border-amber text-amber bg-amber/10"
                                                : "border-border text-muted-foreground hover:text-foreground")
                                        }
                                    >
                                        {r}
                                    </button>
                                ))}
                            </div>
                            <div className="flex gap-1 flex-wrap">
                                {["Common", "Uncommon", "Rare", "Epic", "Legendary"].map((r) => (
                                    <button
                                        type="button"
                                        key={r}
                                        data-testid={`raid-filter-rarity-${r.toLowerCase()}`}
                                        onClick={() => toggleInArr("rarities", r)}
                                        className={
                                            "text-[10px] tracking-widest border px-2 py-0.5 rounded-sm transition-colors " +
                                            (filters.rarities.includes(r)
                                                ? "border-amber text-amber bg-amber/10"
                                                : "border-border text-muted-foreground hover:text-foreground")
                                        }
                                    >
                                        {r}
                                    </button>
                                ))}
                            </div>
                            <button
                                type="button"
                                data-testid="raid-filter-reset"
                                onClick={resetFilters}
                                className="ml-auto text-[11px] tracking-widest text-muted-foreground hover:text-amber underline-offset-4 hover:underline"
                            >
                                ↺ Reset filtri
                            </button>
                        </div>
                    </div>
                </section>

                {/* Roster pool */}
                <section className="border border-border bg-card rounded-sm mb-4" data-testid="raid-roster-pool">
                    <div className="px-4 py-2 border-b border-border/60 bg-secondary/30 text-xs tracking-widest text-amber flex items-center justify-between flex-wrap">
                        <span data-testid="raid-roster-count">:: {t("raids.builder.available_advs")} ({available.length})</span>
                        <span className="text-[10px] text-muted-foreground">
                            {totalAssigned}/{PARTY_COUNT * PARTY_SIZE}
                        </span>
                    </div>
                    <div className="p-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-1.5">
                        {available.length === 0 && (
                            <div
                                data-testid="raid-roster-empty"
                                className="col-span-full text-[11px] text-muted-foreground italic text-center py-4"
                            >
                                {activeFilterCount > 0 ? (
                                    <>
                                        Nessun avventuriero corrisponde ai filtri.{" "}
                                        <button
                                            type="button"
                                            onClick={resetFilters}
                                            className="text-amber underline-offset-4 hover:underline"
                                        >
                                            Resetta i filtri
                                        </button>
                                    </>
                                ) : (
                                    "—"
                                )}
                            </div>
                        )}
                        {available.map((a) => {
                            const fullPartyIdx = parties.findIndex((p) => p.includes(null));
                            const busyAdv = a.is_available === false;
                            return (
                                <button
                                    key={a.id}
                                    data-testid={`adv-pick-${a.id}`}
                                    onClick={() => assignAdv(a.id)}
                                    disabled={fullPartyIdx < 0 || busyAdv}
                                    title={busyAdv ? "Avventuriero non disponibile (in spedizione/raid)" : ""}
                                    className="text-[11px] border border-border/60 rounded-sm px-2 py-1.5 text-left hover:bg-secondary/30 disabled:opacity-40 disabled:cursor-not-allowed"
                                >
                                    <div className="truncate flex items-center gap-1">
                                        <RoleMarker role={a.class_role} />
                                        <span>{a.name} L{a.level}</span>
                                    </div>
                                    <div className="text-[10px] text-muted-foreground">
                                        {a.class_name || "?"} · {a.rarity || "Common"} · pwr {a.total_power}
                                        {busyAdv ? " · busy" : ""}
                                    </div>
                                </button>
                            );
                        })}
                    </div>
                </section>

                {/* Summary */}
                {preview && (
                    <section className="border border-amber/40 bg-amber/5 rounded-sm p-3 mb-4" data-testid="raid-builder-summary">
                        <div className="text-[11px]"><strong>{t("raids.builder.summary_power")}:</strong> {preview.team_power_combined} / rec {preview.recommended_power_combined}</div>
                        <div className="text-[11px]"><strong>{t("raids.builder.summary_success")}:</strong> {preview.success_chance_combined}%</div>
                        <div className="text-[10px] text-muted-foreground">
                            {t("raids.builder.summary_per_party")}: {(preview.success_chance_per_party || []).map((c) => `${c}%`).join(" · ")}
                        </div>
                    </section>
                )}

                <div className="flex flex-wrap gap-2">
                    <button
                        onClick={doPreview}
                        disabled={busy || totalAssigned < PARTY_COUNT * PARTY_SIZE}
                        data-testid="builder-preview-btn"
                        className="text-xs tracking-widest border border-border bg-secondary/50 hover:bg-secondary px-4 py-2 rounded-sm disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                        ⌖ {t("raids.builder.preview_btn")}
                    </button>
                    <button
                        onClick={doLaunch}
                        disabled={busy || !preview}
                        data-testid="builder-launch-btn"
                        className="text-xs tracking-widest border border-amber/60 text-amber bg-amber/10 hover:bg-amber/20 px-4 py-2 rounded-sm disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                        ▶ {t("raids.builder.launch_btn")}
                    </button>
                    <div className="text-[10px] text-muted-foreground self-center">
                        {totalAssigned < PARTY_COUNT * PARTY_SIZE
                            ? t("raids.builder.not_enough", { have: totalAssigned })
                            : ""}
                    </div>
                </div>
            </main>
        </div>
    );
}
