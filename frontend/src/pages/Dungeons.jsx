import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import { toast } from "sonner";
import AppHeader from "../components/AppHeader";
import { Button } from "../components/ui/button";

const DifficultyBadge = ({ value }) => (
    <span className="inline-block text-[10px] tracking-widest border border-amber/40 text-amber px-1.5 py-0.5 rounded-sm">
        DIFF {value}
    </span>
);

const Stat = ({ label, value }) => (
    <div className="flex justify-between text-xs py-1 border-b border-border/40 last:border-b-0">
        <span className="text-muted-foreground">{label}</span>
        <span className="text-foreground font-medium">{value}</span>
    </div>
);

export default function Dungeons() {
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
            <AppHeader subtitle="DUNGEONS" />

            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
                <div className="text-xs text-amber tracking-widest mb-2">
                    :: ACTIVE EXPEDITIONS CATALOG
                </div>
                <h1 className="text-3xl font-semibold tracking-tight">Dungeons</h1>
                <p className="text-sm text-muted-foreground mt-2 max-w-2xl mb-8">
                    Choose a dungeon and dispatch a party. Each run takes time and either
                    rewards your guild or sends them back bruised.
                </p>

                {loading && (
                    <div className="text-xs text-muted-foreground">
                        loading dungeons<span className="caret-blink" />
                    </div>
                )}

                {!loading && dungeons && dungeons.length === 0 && (
                    <div className="border border-border bg-card rounded-sm p-8 text-center text-sm text-muted-foreground">
                        No dungeons are currently active.
                    </div>
                )}

                {!loading && dungeons && dungeons.length > 0 && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                        {dungeons.map((d) => (
                            <div
                                key={d.id}
                                data-testid={`dungeon-card-${d.slug}`}
                                className="border border-border bg-card rounded-sm p-5 flex flex-col"
                            >
                                <div className="flex items-start justify-between mb-2">
                                    <div className="text-base font-medium">{d.name}</div>
                                    <DifficultyBadge value={d.difficulty} />
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
                                <Link to={`/dungeons/${d.slug}/start`}>
                                    <Button
                                        data-testid={`start-dungeon-${d.slug}`}
                                        className="w-full h-10 rounded-sm bg-primary text-primary-foreground hover:bg-primary/90"
                                    >
                                        Start Expedition →
                                    </Button>
                                </Link>
                            </div>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}
