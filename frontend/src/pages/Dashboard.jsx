import { Button } from "../components/ui/button";
import { useAuth } from "../context/AuthContext";

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

const QuickAction = ({ label, code, phase }) => (
    <button
        type="button"
        disabled
        className="text-left border border-border bg-card/60 rounded-sm p-4 opacity-60 cursor-not-allowed disabled:cursor-not-allowed"
        data-testid={`quickaction-${code}`}
        title={`Coming in ${phase}`}
        aria-disabled="true"
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
    const { user, guild, logout } = useAuth();
    if (!guild) return null;

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg term-scanline">
            <header className="border-b border-border">
                <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3 text-xs">
                        <span className="text-amber">◆</span>
                        <span className="text-muted-foreground tracking-widest">
                            ORBUS // DASHBOARD
                        </span>
                    </div>
                    <div className="flex items-center gap-4 text-xs">
                        <span
                            data-testid="header-username"
                            className="text-muted-foreground"
                        >
                            @{user?.username}
                        </span>
                        <Button
                            data-testid="logout-btn"
                            onClick={logout}
                            variant="outline"
                            className="h-8 px-3 rounded-sm border-border bg-transparent hover:bg-secondary text-xs"
                        >
                            logout
                        </Button>
                    </div>
                </div>
            </header>

            <main className="max-w-6xl mx-auto px-6 py-10">
                {/* Guild header */}
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

                {/* Stats grid */}
                <section className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-10">
                    <Stat
                        label="LEVEL"
                        value={guild.level}
                        testid="stat-level"
                        accent
                    />
                    <Stat
                        label="REPUTATION"
                        value={guild.reputation}
                        testid="stat-reputation"
                    />
                    <Stat
                        label="GOLD"
                        value={guild.gold}
                        testid="stat-gold"
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

                {/* Quick actions */}
                <section>
                    <div className="text-xs text-muted-foreground tracking-widest mb-3">
                        :: QUICK ACTIONS
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <QuickAction code="01" label="Recruit adventurers" phase="phase 2" />
                        <QuickAction code="02" label="Adventurers" phase="phase 2" />
                        <QuickAction code="03" label="Dungeons" phase="phase 3" />
                        <QuickAction code="04" label="Inventory" phase="phase 3" />
                    </div>
                </section>

                {/* System log */}
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
                            <span className="text-foreground">{guild.name}</span> ready —
                            level {guild.level}, gold {guild.gold}
                        </div>
                        <div>
                            <span className="text-amber">$</span> phase-2 modules pending
                            <span className="caret-blink" />
                        </div>
                    </div>
                </section>
            </main>
        </div>
    );
}
