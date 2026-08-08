// Saved formations for every canonical dungeon and raid size.
import { useEffect, useState, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import AppHeader from "@/components/AppHeader";
import OverCapBanner from "@/components/OverCapBanner";
import { useT } from "@/i18n/I18nContext";
import { api } from "@/lib/api";

const TYPE_META = {
    dungeon_3: { titleIt: "Squadre Dungeon 3", titleEn: "Dungeon 3 Squads", size: 3 },
    dungeon_5: { titleIt: "Squadre Dungeon 5", titleEn: "Dungeon 5 Squads", size: 5 },
    dungeon_7: { titleIt: "Squadre Dungeon 7", titleEn: "Dungeon 7 Squads", size: 7 },
    raid_10: { titleIt: "Squadre Raid 10", titleEn: "Raid 10 Squads", size: 10 },
    raid_15: { titleIt: "Squadre Raid 15", titleEn: "Raid 15 Squads", size: 15 },
    raid_20: { titleIt: "Squadre Raid 20", titleEn: "Raid 20 Squads", size: 20 },
    raid_40: { titleIt: "Squadre Raid 40", titleEn: "Raid 40 Squads", size: 40 },
};
const TYPE_ORDER = Object.keys(TYPE_META);

function SquadCard({ squad, lang, onArchive }) {
    const missing = (squad.missing_adventurer_ids || []).length;
    // ROUND 6B.4 Q5 — Distinguish retired (recoverable history) from
    // deleted (data corruption edge). Backend now splits the two arrays;
    // legacy responses fall back to the union `missing_adventurer_ids`.
    const retiredCount = (squad.retired_adventurer_ids || []).length;
    const deletedCount = (squad.deleted_adventurer_ids || []).length;
    const isRaid = squad.squad_type.startsWith("raid_");
    // Round 6A.2c — raid deploy guard: disable if any required adventurer is missing.
    const deployDisabled = isRaid && missing > 0;
    const deployHref = isRaid
        ? `/raids?squad_id=${squad.squad_id}`
        : `/dungeons?squad_id=${squad.squad_id}`;
    const deployLabel = isRaid
        ? lang === "it" ? "▶ Lancia Raid" : "▶ Launch Raid"
        : lang === "it" ? "▶ Invia in Spedizione" : "▶ Send Expedition";
    const deployTooltip = deployDisabled
        ? lang === "it"
            ? `${missing} avventurieri mancanti, modifica la squadra`
            : `${missing} adventurers missing, edit the squad`
        : "";
    return (
        <div
            data-testid={`squad-card-${squad.squad_id}`}
            className="border border-neutral-800 rounded-sm p-4 bg-secondary/30 hover:bg-secondary/50 transition-colors"
        >
            <div className="flex items-start justify-between gap-3 mb-2">
                <h3 className="text-foreground font-bold text-sm tracking-wide" data-testid={`squad-name-${squad.squad_id}`}>
                    {squad.name}
                </h3>
                <span className="text-xs text-amber font-bold tracking-widest" data-testid={`squad-power-${squad.squad_id}`}>
                    PWR {squad.total_power}
                </span>
            </div>
            <div className="text-[11px] text-muted-foreground tracking-wider mb-3">
                {squad.member_count}/{squad.adventurer_ids.length} {lang === "it" ? "membri attivi" : "active members"}
                {retiredCount > 0 && (
                    <span
                        className="ml-2 text-red-400"
                        data-testid={`squad-retired-${squad.squad_id}`}
                        title={lang === "it"
                            ? "Membri congedati. Riaggiungi avventurieri attivi alla squadra."
                            : "Retired members. Re-roster the squad with active adventurers."}
                    >
                        ⚠ {retiredCount} {lang === "it" ? "congedato/i" : "retired"}
                    </span>
                )}
                {deletedCount > 0 && (
                    <span
                        className="ml-2 text-orange-300/80"
                        data-testid={`squad-deleted-${squad.squad_id}`}
                        title={lang === "it"
                            ? "Membri non trovati nel DB (caso edge storico)."
                            : "Members not found in DB (legacy edge case)."}
                    >
                        ⚠ {deletedCount} {lang === "it" ? "non trovati" : "not found"}
                    </span>
                )}
                {/* Fallback: legacy missing count if neither split array is present */}
                {retiredCount === 0 && deletedCount === 0 && missing > 0 && (
                    <span className="ml-2 text-red-400" data-testid={`squad-missing-${squad.squad_id}`}>
                        ⚠ {missing} {lang === "it" ? "non disponibili" : "unavailable"}
                    </span>
                )}
            </div>
            {/* Round 6A.2c — Deploy CTA */}
            {deployDisabled ? (
                <button
                    type="button"
                    disabled
                    title={deployTooltip}
                    data-testid={`squad-deploy-btn-${squad.squad_id}`}
                    className="w-full mb-2 px-3 py-1.5 text-[11px] tracking-widest font-bold bg-amber/30 text-background/60 rounded-sm cursor-not-allowed opacity-60"
                >
                    {deployLabel}
                </button>
            ) : (
                <Link
                    to={deployHref}
                    data-testid={`squad-deploy-btn-${squad.squad_id}`}
                    title={deployTooltip}
                    className="block w-full mb-2 px-3 py-1.5 text-[11px] tracking-widest font-bold bg-amber text-background hover:opacity-90 transition-opacity rounded-sm text-center"
                >
                    {deployLabel}
                </Link>
            )}
            <div className="flex gap-2">
                <Link
                    to={`/squads/${squad.squad_id}/edit`}
                    data-testid={`squad-edit-btn-${squad.squad_id}`}
                    className="px-3 py-1 text-[11px] tracking-widest border border-amber/60 text-amber hover:bg-amber hover:text-background transition-colors"
                >
                    {lang === "it" ? "Modifica" : "Edit"}
                </Link>
                <button
                    onClick={() => onArchive(squad.squad_id, squad.name)}
                    data-testid={`squad-archive-btn-${squad.squad_id}`}
                    className="px-3 py-1 text-[11px] tracking-widest border border-neutral-700 text-muted-foreground hover:text-foreground hover:border-neutral-500 transition-colors"
                >
                    {lang === "it" ? "Archivia" : "Archive"}
                </button>
            </div>
        </div>
    );
}

function SquadSection({ type, squads, lang, onArchive }) {
    const meta = TYPE_META[type];
    return (
        <section className="mb-10" data-testid={`squad-section-${type}`}>
            <div className="flex items-center justify-between mb-4 border-b border-neutral-800 pb-2">
                <h2 className="text-amber font-bold text-sm tracking-widest">
                    :: {lang === "it" ? meta.titleIt : meta.titleEn} ({meta.size}p)
                </h2>
                <Link
                    to={`/squads/new?type=${type}`}
                    data-testid={`squad-new-btn-${type}`}
                    className="px-3 py-1.5 text-xs tracking-widest font-bold bg-amber text-background hover:opacity-90 transition-opacity rounded-sm"
                >
                    + {lang === "it" ? "Nuova" : "New"}
                </Link>
            </div>
            {squads.length === 0 ? (
                <p className="text-muted-foreground text-xs italic" data-testid={`squad-empty-${type}`}>
                    {lang === "it"
                        ? "Nessuna squadra salvata. Crea la prima per riusarla in spedizioni/raid."
                        : "No saved squads yet. Create one to reuse it in expeditions/raids."}
                </p>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {squads.map((s) => (
                        <SquadCard key={s.squad_id} squad={s} lang={lang} onArchive={onArchive} />
                    ))}
                </div>
            )}
        </section>
    );
}

export default function Squads() {
    const { lang } = useT();
    const [squads, setSquads] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    const load = useCallback(async () => {
        setLoading(true);
        try {
            // ROUND 11.1 Slice 2 — switched to `api` wrapper for cookie auth + CSRF.
            const { data } = await api.get("/squads");
            setSquads(data.squads || []);
        } catch (e) {
            if (e?.response?.status === 401) { navigate("/login"); return; }
            toast.error(lang === "it" ? "Errore caricamento squadre" : "Failed to load squads");
        } finally {
            setLoading(false);
        }
    }, [lang, navigate]);

    useEffect(() => {
        load();
    }, [load]);

    const handleArchive = async (id, name) => {
        const confirmMsg =
            lang === "it"
                ? `Archiviare "${name}"? Potrai sempre crearne una nuova.`
                : `Archive "${name}"? You can always create a new one.`;
        if (!window.confirm(confirmMsg)) return;
        try {
            // ROUND 11.1 Slice 2 — `api.delete` adds CSRF header automatically.
            await api.delete(`/squads/${id}`);
            toast.success(lang === "it" ? "Squadra archiviata" : "Squad archived");
            load();
        } catch (e) {
            toast.error(lang === "it" ? "Errore archiviazione" : "Archive failed");
        }
    };

    const grouped = Object.fromEntries(
        TYPE_ORDER.map((type) => [type, squads.filter((s) => s.squad_type === type)]),
    );

    return (
        <div className="min-h-screen bg-background text-foreground">
            <AppHeader />
            <main className="max-w-6xl mx-auto px-4 py-8" data-testid="squads-page">
                <OverCapBanner source="squads" />
                <div className="mb-8">
                    <h1 className="text-amber text-2xl font-bold tracking-wider mb-2">
                        {lang === "it" ? "SQUADRE PERSONALIZZATE" : "CUSTOM SQUADS"}
                    </h1>
                    <p className="text-muted-foreground text-xs tracking-wide">
                        {lang === "it"
                            ? "Salva combinazioni di avventurieri per riusarle istantaneamente in spedizioni e raid. Nessun bonus al power: pura comodità."
                            : "Save adventurer combinations to reuse them instantly in expeditions and raids. No power bonus: pure convenience."}
                    </p>
                </div>
                {loading ? (
                    <p className="text-muted-foreground text-xs" data-testid="squads-loading">
                        {lang === "it" ? "Caricamento..." : "Loading..."}
                    </p>
                ) : (
                    <>
                        {TYPE_ORDER.map((type) => (
                            <SquadSection
                                key={type}
                                type={type}
                                squads={grouped[type]}
                                lang={lang}
                                onArchive={handleArchive}
                            />
                        ))}
                    </>
                )}
            </main>
        </div>
    );
}
