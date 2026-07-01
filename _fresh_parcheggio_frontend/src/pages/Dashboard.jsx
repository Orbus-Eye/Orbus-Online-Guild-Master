import AppShell from "@/components/AppShell";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";

function StatCard({ label, value, testId }) {
    return (
        <Card
            data-testid={testId}
            className="border-border/70 bg-card px-4 py-4 sm:px-5 sm:py-5"
        >
            <p className="text-[10px] uppercase tracking-widest text-muted-foreground">
                {label}
            </p>
            <p className="mt-2 font-mono text-2xl text-foreground sm:text-3xl">
                {value}
            </p>
        </Card>
    );
}

function QuickAction({ label, testId }) {
    return (
        <Button
            variant="outline"
            disabled
            title="In arrivo prossimamente"
            data-testid={testId}
            className="justify-start border-border/70 bg-card/40 text-left text-xs opacity-60 sm:text-sm"
        >
            <span className="truncate">{label}</span>
            <span className="ml-auto text-[9px] uppercase tracking-widest text-muted-foreground">
                soon
            </span>
        </Button>
    );
}

function formatDate(iso) {
    if (!iso) return "—";
    try {
        return new Date(iso).toLocaleString("it-IT", {
            day: "2-digit", month: "short", year: "numeric",
            hour: "2-digit", minute: "2-digit",
        });
    } catch {
        return iso;
    }
}

export default function Dashboard() {
    const { user, guild } = useAuth();

    return (
        <AppShell>
            {/* Header gilda */}
            <section className="mb-8">
                <p className="text-[10px] uppercase tracking-widest text-muted-foreground">
                    &gt; gilda attiva
                </p>
                <h1
                    data-testid="dashboard-guild-name"
                    className="mt-2 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl"
                >
                    {guild?.name}
                </h1>
                {guild?.description && (
                    <p
                        data-testid="dashboard-guild-description"
                        className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground"
                    >
                        {guild.description}
                    </p>
                )}
                <p className="mt-3 text-[11px] text-muted-foreground/80">
                    Fondata il {formatDate(guild?.created_at)} · Owner: {user?.email}
                </p>
            </section>

            {/* Stats */}
            <section className="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-4 sm:gap-4">
                <StatCard label="Livello" value={guild?.level ?? 1} testId="dashboard-stat-level" />
                <StatCard label="Reputazione" value={guild?.reputation ?? 0} testId="dashboard-stat-reputation" />
                <StatCard label="Oro" value={guild?.gold ?? 0} testId="dashboard-stat-gold" />
                <StatCard label="Avventurieri" value={0} testId="dashboard-stat-adventurers" />
            </section>

            {/* Spedizioni + Report */}
            <section className="mb-8 grid gap-4 lg:grid-cols-2">
                <Card
                    data-testid="dashboard-active-expeditions"
                    className="border-border/70 bg-card p-5"
                >
                    <div className="mb-3 flex items-center justify-between">
                        <h2 className="text-xs uppercase tracking-widest text-muted-foreground">
                            Spedizioni attive
                        </h2>
                    </div>
                    <p className="py-6 text-center text-sm text-muted-foreground">
                        Nessuna spedizione attiva.
                    </p>
                </Card>

                <Card
                    data-testid="dashboard-recent-reports"
                    className="border-border/70 bg-card p-5"
                >
                    <div className="mb-3 flex items-center justify-between">
                        <h2 className="text-xs uppercase tracking-widest text-muted-foreground">
                            Ultimi report
                        </h2>
                    </div>
                    <p className="py-6 text-center text-sm text-muted-foreground">
                        Nessun report disponibile.
                    </p>
                </Card>
            </section>

            {/* Quick actions */}
            <section>
                <h2 className="mb-3 text-xs uppercase tracking-widest text-muted-foreground">
                    Azioni rapide
                </h2>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4" data-testid="dashboard-quick-actions">
                    <QuickAction label="Recluta avventurieri" testId="quick-action-recruit" />
                    <QuickAction label="Vedi roster" testId="quick-action-roster" />
                    <QuickAction label="Dungeon" testId="quick-action-dungeons" />
                    <QuickAction label="Inventario" testId="quick-action-inventory" />
                </div>
            </section>
        </AppShell>
    );
}
