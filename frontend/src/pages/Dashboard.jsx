import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import AppHeader from "../components/AppHeader";

const formatDate = (iso) => {
    if (!iso) return "—";
    try {
        const d = new Date(iso);
        return d.toISOString().replace("T", " ").slice(0, 19) + " UTC";
    } catch {
        return iso;
    }
};

const Stat = ({ label, value, testid, accent = false }) => (
    <div className="border border-border bg-card rounded-sm p-4">
        <div className="text-[10px] text-muted-foreground tracking-widest mb-2">
            {label}
        </div>
        <div
            data-testid={testid}
            className={`text-2xl font-semibold ${accent ? "text-amber" : "text-foreground"}`}
        >
            {value}
        </div>
    </div>
);

const ActiveAction = ({ to, label, code, testid }) => (
    <Link
        to={to}
        data-testid={testid}
        className="block border border-border bg-card rounded-sm p-4 hover:bg-secondary/40 transition-colors group"
    >
        <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] text-amber tracking-widest">::{code}</span>
            <span className="text-[10px] text-amber group-hover:translate-x-0.5 transition-transform">
                →
            </span>
        </div>
        <div className="text-sm">{label}</div>
        <div className="text-[10px] text-muted-foreground mt-2">— ready —</div>
    </Link>
);

const LockedAction = ({ label, code, phase }) => (
    <button
        type="button"
        disabled
        aria-disabled="true"
        title={`Coming in ${phase}`}
        data-testid={`quickaction-${code}`}
        className="text-left border border-border bg-card/60 rounded-sm p-4 opacity-60 cursor-not-allowed disabled:cursor-not-allowed w-full"
    >
        <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] text-muted-foreground tracking-widest">
                ::{code}
            </span>
            <span className="text-[10px] text-muted-foreground border border-border rounded-sm px-1.5 py-0.5">
                {phase}
            </span>
        </div>
        <div className="text-sm">{label}</div>
        <div className="text-[10px] text-muted-foreground mt-2">— locked —</div>
    </button>
);

export default function Dashboard() {
    const { user, guild } = useAuth();
    if (!guild) return null;
    const advCount = guild.adventurer_count ?? 0;

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg term-scanline">
            <AppHeader subtitle="DASHBOARD" />

            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
                <section className="mb-8">
                    <div className="text-xs text-amber tracking-widest mb-2">
                        :: GUILD OVERVIEW
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
                        <div>
                            <h1
                                data-testid="guild-name"
                                className="text-3xl sm:text-4xl font-semibold tracking-tight"
                            >
                                {guild.name}
                            </h1>
                            {guild.description ? (
                                <p
                                    data-testid="guild-description"
                                    className="text-sm text-muted-foreground mt-2 max-w-2xl"
                                >
                                    {guild.description}
                                </p>
                            ) : (
                                <p className="text-sm text-muted-foreground/60 italic mt-2">
                                    no description set
                                </p>
                            )}
                        </div>
                        <div className="text-xs text-muted-foreground">
                            founded:{" "}
                            <span
                                data-testid="guild-created-at"
                                className="text-foreground"
                            >
                                {formatDate(guild.created_at)}
                            </span>
                        </div>
                    </div>
                </section>

                <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-10">
                    <Stat label="LEVEL" value={guild.level} testid="stat-level" accent />
                    <Stat
                        label="REPUTATION"
                        value={guild.reputation}
                        testid="stat-reputation"
                    />
                    <Stat label="GOLD" value={guild.gold} testid="stat-gold" accent />
                    <Stat
                        label="ADVENTURERS"
                        value={advCount}
                        testid="stat-adventurer-count"
                    />
                    <Stat
                        label="ACTIVE EXP"
                        value={guild.active_expedition_count ?? 0}
                        testid="stat-active-expeditions"
                        accent
                    />
                    <Stat
                        label="GUILD ID"
                        value={
                            <span className="text-xs font-mono break-all">
                                {guild.id.slice(0, 8)}…
                            </span>
                        }
                        testid="stat-guild-id"
                    />
                </section>

                {guild.last_expedition_id && (
                    <section className="mb-8">
                        <Link
                            to={`/expeditions/${guild.last_expedition_id}`}
                            data-testid="last-expedition-link"
                            className="inline-flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground border border-border bg-card rounded-sm px-3 py-2"
                        >
                            <span className="text-amber">::</span>
                            <span>
                                last expedition:{" "}
                                <span
                                    className={
                                        guild.last_expedition_summary === "Success"
                                            ? "text-[#22c55e]"
                                            : guild.last_expedition_summary === "Failed"
                                              ? "text-[#ef4444]"
                                              : "text-amber"
                                    }
                                >
                                    {guild.last_expedition_summary || "in progress"}
                                </span>
                            </span>
                            <span className="text-amber">→</span>
                        </Link>
                    </section>
                )}

                <section>
                    <div className="text-xs text-muted-foreground tracking-widest mb-3">
                        :: QUICK ACTIONS
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <ActiveAction
                            to="/recruitment"
                            label="Recruit adventurers"
                            code="01"
                            testid="quickaction-01"
                        />
                        <ActiveAction
                            to="/adventurers"
                            label="View adventurers"
                            code="02"
                            testid="quickaction-02"
                        />
                        <ActiveAction
                            to="/dungeons"
                            label="Dungeons"
                            code="03"
                            testid="quickaction-03"
                        />
                        <ActiveAction
                            to="/inventory"
                            label="Inventory"
                            code="04"
                            testid="quickaction-04"
                        />
                    </div>
                </section>

                <section className="mt-10">
                    <div className="text-xs text-muted-foreground tracking-widest mb-3">
                        :: SYSTEM LOG
                    </div>
                    <div className="border border-border bg-card rounded-sm p-4 text-xs text-muted-foreground font-mono space-y-1">
                        <div>
                            <span className="text-amber">$</span> session opened for{" "}
                            <span className="text-foreground">@{user?.username}</span>
                        </div>
                        <div>
                            <span className="text-amber">$</span> guild{" "}
                            <span className="text-foreground">{guild.name}</span> — level{" "}
                            {guild.level}, gold {guild.gold}, adventurers {advCount}
                        </div>
                        <div>
                            <span className="text-amber">$</span> phase-3 modules pending
                            <span className="caret-blink" />
                        </div>
                    </div>
                </section>
            </main>
        </div>
    );
}
