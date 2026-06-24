import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import { toast } from "sonner";
import AppHeader from "../components/AppHeader";
import { useT } from "../i18n/I18nContext";
import { Button } from "../components/ui/button";

const DifficultyBadge = ({ value }) => {
    const TIER = { 1: "TIER I", 2: "TIER II", 3: "TIER III" };
    const TIER_COLOR = { 1: "amber", 2: "rare", 3: "epic" };
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

export default function Dungeons() {
    const { t } = useT();
    const [dungeons, setDungeons] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        (async () => {
            try {
                const { data } = await api.get("/dungeons");
                setDungeons(data.dungeons);
            } catch (err) {
                toast.error(formatApiError(err));
                setDungeons([]);
            } finally {
                setLoading(false);
            }
        })();
    }, []);

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg">
            <AppHeader subtitleKey="nav.dungeons" />

            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
                <div className="text-xs text-amber tracking-widest mb-2">
                    :: ACTIVE EXPEDITIONS CATALOG
                </div>
                <h1 className="text-3xl font-semibold tracking-tight">{t("dungeons.title")}</h1>
                <p className="text-sm text-muted-foreground mt-2 max-w-2xl mb-8">
                    Choose a dungeon and dispatch a party. Each run takes time and either
                    rewards your guild or sends them back bruised.
                </p>

                {loading && (
                    <div className="text-xs text-muted-foreground">
                        {t("common.loading")}<span className="caret-blink" />
                    </div>
                )}

                {!loading && dungeons && dungeons.length === 0 && (
                    <div className="border border-border bg-card rounded-sm p-8 text-center text-sm text-muted-foreground">
                        No dungeons are currently active.
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
                                        {d.description}
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
                                        <Link to={`/dungeons/${d.slug}/start`}>
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
