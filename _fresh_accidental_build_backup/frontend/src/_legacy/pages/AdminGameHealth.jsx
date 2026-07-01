// ROUND 14.v3 — Admin Game Health UI.
//
// Read-only dashboard that consumes the 6 telemetry endpoints exposed by
// `app/admin/game_health_routes.py`. Plus a single mutating action: the
// "Unarchive guild" form (calls `POST /admin/game-health/guilds/:id/unarchive`).
//
// Visual style: matches the existing Admin console (terminal-ish minimal
// tables/cards, no charts, no extra libraries).
import { useCallback, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { toast } from "sonner";

import AppHeader from "../components/AppHeader";
import { useAuth } from "../context/AuthContext";
import { api, formatApiError } from "../lib/api";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";

const ENDPOINTS = [
    { key: "economy", path: "/admin/game-health/economy?window=24h",
        title: "Economia (24h)",
        subtitle: "Faucet, sink e inflazione netta nelle ultime 24h." },
    { key: "materials", path: "/admin/game-health/materials",
        title: "Materiali in circolazione",
        subtitle: "Top materiali per quantità totale nei vault attivi." },
    { key: "shop", path: "/admin/game-health/shop?window=24h",
        title: "Mercato NPC (24h)",
        subtitle: "Volume acquisti dal Market e revenue verso il banco." },
    { key: "progression", path: "/admin/game-health/progression",
        title: "Progressione",
        subtitle: "Distribuzione livello gilda + roster + avventurieri." },
    { key: "competitive", path: "/admin/game-health/competitive",
        title: "PvP / Arena",
        subtitle: "Stagione attiva, partecipanti, rating medio." },
    { key: "anomalies", path: "/admin/game-health/anomalies",
        title: "Anomalie",
        subtitle: "Warning runtime di alta priorità." },
];

const SEVERITY_STYLES = {
    critical: "text-red-300 border-red-500/60 bg-red-500/10",
    warn: "text-amber border-amber/50 bg-amber/5",
    info: "text-muted-foreground border-border bg-secondary/30",
};

function SeverityBadge({ severity }) {
    const cls = SEVERITY_STYLES[severity] || SEVERITY_STYLES.info;
    return (
        <span
            data-testid={`gh-severity-${severity}`}
            className={`inline-block text-[10px] tracking-widest border px-1.5 py-0.5 rounded-sm ${cls}`}
        >
            {(severity || "info").toUpperCase()}
        </span>
    );
}

function KV({ label, value, testid }) {
    return (
        <div className="flex items-center justify-between text-xs border-b border-border/40 py-1.5 last:border-b-0">
            <span className="text-muted-foreground tracking-wider">{label}</span>
            <span data-testid={testid} className="text-foreground font-mono">
                {value == null ? "—" : value}
            </span>
        </div>
    );
}

function CardShell({ title, subtitle, testid, children, action }) {
    return (
        <section
            data-testid={testid}
            className="border border-border bg-card rounded-sm p-4"
        >
            <div className="flex items-start justify-between gap-3 mb-3">
                <div>
                    <div className="text-[10px] text-amber tracking-widest mb-1">
                        :: {title}
                    </div>
                    <p className="text-[11px] text-muted-foreground">{subtitle}</p>
                </div>
                {action}
            </div>
            {children}
        </section>
    );
}

function EmptyState({ message, testid }) {
    return (
        <div
            data-testid={testid}
            className="text-[11px] text-muted-foreground italic py-3"
        >
            {message}
        </div>
    );
}

function EconomyCard({ data }) {
    if (!data) return <EmptyState testid="gh-economy-empty" message="Nessun dato economia disponibile." />;
    return (
        <dl className="space-y-0">
            <KV label="Gilde idonee" value={data.eligible_guilds} testid="gh-economy-eligible" />
            <KV label="Oro in circolazione" value={data.current_gold_in_circulation} testid="gh-economy-circulation" />
            <KV label="Faucet (oro generato)" value={data.faucets_total_gold} testid="gh-economy-faucets" />
            <KV label="Sink (oro consumato)" value={data.sinks_total_gold} testid="gh-economy-sinks" />
            <KV
                label="Inflazione netta"
                value={
                    <span className={data.net_inflation_gold >= 0 ? "text-amber" : "text-emerald-400"}>
                        {data.net_inflation_gold >= 0 ? "+" : ""}{data.net_inflation_gold}
                    </span>
                }
                testid="gh-economy-net"
            />
            <KV label="Admin grant (separato)" value={data.admin_granted_gold} testid="gh-economy-admin-grant" />
        </dl>
    );
}

function MaterialsCard({ data }) {
    if (!data || !data.materials?.length) {
        return <EmptyState testid="gh-materials-empty" message="Nessun materiale tracciato." />;
    }
    return (
        <div className="overflow-x-auto">
            <table className="w-full text-xs">
                <thead className="text-[10px] text-muted-foreground tracking-widest">
                    <tr>
                        <th className="text-left py-1.5 font-normal">SLUG</th>
                        <th className="text-left py-1.5 font-normal">NOME</th>
                        <th className="text-right py-1.5 font-normal">QTÀ</th>
                    </tr>
                </thead>
                <tbody data-testid="gh-materials-table">
                    {data.materials.slice(0, 10).map((m) => (
                        <tr key={m.slug} className="border-t border-border/40">
                            <td className="font-mono text-muted-foreground py-1">{m.slug}</td>
                            <td className="py-1">{m.name_it}</td>
                            <td className="py-1 text-right font-mono">{m.total_in_circulation}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

function ShopCard({ data }) {
    if (!data) return <EmptyState testid="gh-shop-empty" message="Nessun dato shop." />;
    return (
        <>
            <dl className="space-y-0 mb-3">
                <KV label="Acquisti totali" value={data.total_buys} testid="gh-shop-buys" />
                <KV label="Unità acquistate" value={data.total_units_bought} testid="gh-shop-units" />
                <KV label="Revenue (oro al banco)" value={data.revenue_to_npc_gold} testid="gh-shop-revenue" />
            </dl>
            {data.top_5_materials_bought?.length > 0 ? (
                <div>
                    <div className="text-[10px] text-muted-foreground tracking-widest mb-1.5">
                        TOP 5 MATERIALI
                    </div>
                    <ul className="space-y-1 text-xs font-mono" data-testid="gh-shop-top5">
                        {data.top_5_materials_bought.map((r) => (
                            <li key={r.slug} className="flex justify-between border-b border-border/40 py-1">
                                <span>{r.slug}</span>
                                <span className="text-amber">×{r.units}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            ) : (
                <EmptyState testid="gh-shop-no-purchases" message="Nessun acquisto in finestra." />
            )}
        </>
    );
}

function ProgressionCard({ data }) {
    if (!data) return <EmptyState testid="gh-progression-empty" message="Nessun dato progressione." />;
    const ld = Object.entries(data.guild_level_dist || {}).sort(([a], [b]) => +a - +b);
    return (
        <>
            <dl className="space-y-0 mb-3">
                <KV label="Gilde idonee" value={data.eligible_guilds} testid="gh-progression-eligible" />
                <KV label="Roster size medio" value={data.avg_roster_size} testid="gh-progression-avg" />
            </dl>
            <div className="text-[10px] text-muted-foreground tracking-widest mb-1.5">
                LIVELLO GILDA · DISTRIBUZIONE
            </div>
            <ul className="space-y-1 text-xs font-mono" data-testid="gh-progression-leveldist">
                {ld.length === 0 && <li className="text-muted-foreground italic">—</li>}
                {ld.map(([lvl, count]) => (
                    <li key={lvl} className="flex justify-between border-b border-border/40 py-1">
                        <span>Lv {lvl}</span>
                        <span className="text-amber">{count} gilde</span>
                    </li>
                ))}
            </ul>
        </>
    );
}

function CompetitiveCard({ data }) {
    if (!data || !data.active_season) {
        return <EmptyState testid="gh-competitive-empty" message="Nessuna stagione attiva." />;
    }
    return (
        <>
            <dl className="space-y-0 mb-3">
                <KV label="Stagione" value={data.active_season} testid="gh-competitive-season" />
                <KV label="Partecipanti" value={data.participants} testid="gh-competitive-participants" />
                <KV label="Rating medio" value={data.rating_avg} testid="gh-competitive-rating" />
                <KV label="Attacchi giocati" value={data.attacks_played_total} testid="gh-competitive-attacks" />
                <KV label="Vittorie totali" value={data.wins_total} testid="gh-competitive-wins" />
            </dl>
            <div className="text-[10px] text-muted-foreground tracking-widest mb-1.5">
                LEGHE
            </div>
            <ul className="space-y-1 text-xs font-mono" data-testid="gh-competitive-leagues">
                {Object.entries(data.leagues || {}).map(([lg, n]) => (
                    <li key={lg} className="flex justify-between border-b border-border/40 py-1">
                        <span>{lg}</span>
                        <span className="text-amber">{n}</span>
                    </li>
                ))}
            </ul>
        </>
    );
}

function AnomaliesCard({ data }) {
    if (!data) return <EmptyState testid="gh-anomalies-empty" message="Nessun dato anomalie." />;
    const warnings = data.warnings || [];
    if (warnings.length === 0) {
        return (
            <div data-testid="gh-anomalies-clean" className="text-xs text-emerald-400">
                ✓ Nessuna anomalia rilevata. Sistema sano.
            </div>
        );
    }
    return (
        <ul className="space-y-2" data-testid="gh-anomalies-list">
            {warnings.map((w) => (
                <li
                    key={`${w.code}-${w.severity}`}
                    data-testid={`gh-anomaly-${w.code}`}
                    className="border border-border rounded-sm p-2.5 flex items-start justify-between gap-3"
                >
                    <div className="min-w-0">
                        <div className="font-mono text-xs text-foreground">{w.code}</div>
                        <div className="text-[10px] text-muted-foreground mt-0.5">
                            count: {w.count}
                        </div>
                    </div>
                    <SeverityBadge severity={w.severity} />
                </li>
            ))}
        </ul>
    );
}

function UnarchiveForm() {
    const [guildId, setGuildId] = useState("");
    const [reason, setReason] = useState("");
    const [busy, setBusy] = useState(false);
    const [lastResult, setLastResult] = useState(null);

    const submit = async (e) => {
        e.preventDefault();
        if (reason.trim().length < 3) {
            toast.error("La motivazione deve avere almeno 3 caratteri.");
            return;
        }
        if (!guildId.trim()) {
            toast.error("ID gilda obbligatorio.");
            return;
        }
        setBusy(true);
        setLastResult(null);
        try {
            const { data } = await api.post(
                `/admin/game-health/guilds/${guildId.trim()}/unarchive`,
                { reason: reason.trim() },
            );
            toast.success(`Gilda ${data.guild_id} riattivata.`);
            setLastResult({ ok: true, ...data });
            setGuildId("");
            setReason("");
        } catch (err) {
            setLastResult({ ok: false, error: formatApiError(err) });
            toast.error(formatApiError(err));
        } finally {
            setBusy(false);
        }
    };

    return (
        <CardShell
            testid="gh-unarchive-card"
            title="Riattiva gilda archiviata"
            subtitle="Inverte il soft-flag pre-launch. Audit-logged. Motivazione obbligatoria."
        >
            <form onSubmit={submit} className="space-y-3">
                <div>
                    <Label className="text-[10px] text-muted-foreground tracking-widest">
                        ID PUBBLICO GILDA <span className="text-amber">*</span>
                    </Label>
                    <Input
                        data-testid="gh-unarchive-guild-id"
                        value={guildId}
                        onChange={(e) => setGuildId(e.target.value)}
                        placeholder="uuid…"
                        className="bg-background border-border rounded-sm h-10 font-mono text-sm mt-1.5"
                    />
                </div>
                <div>
                    <Label className="text-[10px] text-muted-foreground tracking-widest">
                        MOTIVAZIONE (min 3 char) <span className="text-amber">*</span>
                    </Label>
                    <Textarea
                        data-testid="gh-unarchive-reason"
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                        placeholder="Es: utente reale segnalato, errore di cleanup, ecc."
                        className="bg-background border-border rounded-sm font-mono text-sm mt-1.5 min-h-[60px]"
                    />
                </div>
                <Button
                    type="submit"
                    disabled={busy}
                    data-testid="gh-unarchive-submit"
                    className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm"
                >
                    {busy ? "…" : "Riattiva gilda"}
                </Button>
                {lastResult && (
                    <div
                        data-testid="gh-unarchive-result"
                        className={`text-xs border rounded-sm px-3 py-2 ${
                            lastResult.ok
                                ? "border-emerald-500/40 text-emerald-300 bg-emerald-500/5"
                                : "border-red-500/40 text-red-300 bg-red-500/5"
                        }`}
                    >
                        {lastResult.ok
                            ? `✓ Riattivata: ${lastResult.guild_id}`
                            : `✗ Errore: ${lastResult.error}`}
                    </div>
                )}
            </form>
        </CardShell>
    );
}

export default function AdminGameHealth() {
    const { user } = useAuth();
    const [results, setResults] = useState({});
    const [errors, setErrors] = useState({});
    const [loading, setLoading] = useState(true);
    const [refreshedAt, setRefreshedAt] = useState(null);

    const fetchAll = useCallback(async () => {
        setLoading(true);
        const allResults = {};
        const allErrors = {};
        await Promise.all(
            ENDPOINTS.map(async (e) => {
                try {
                    const { data } = await api.get(e.path);
                    allResults[e.key] = data;
                } catch (err) {
                    allErrors[e.key] = formatApiError(err);
                }
            }),
        );
        setResults(allResults);
        setErrors(allErrors);
        setRefreshedAt(new Date());
        setLoading(false);
    }, []);

    useEffect(() => {
        if (user?.is_admin) fetchAll();
    }, [user, fetchAll]);

    if (user === undefined) return null;
    if (!user) return <Navigate to="/login" replace />;
    if (user && !user.is_admin) {
        toast.error("Accesso riservato agli amministratori.");
        return <Navigate to="/dashboard" replace />;
    }

    const anomaliesWarnings = results.anomalies?.warnings || [];
    const hasAnomalies = anomaliesWarnings.length > 0;

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg">
            <AppHeader subtitle="GAME HEALTH" />

            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
                <div className="flex items-end justify-between gap-3 mb-6 flex-wrap">
                    <div>
                        <div className="text-xs text-amber tracking-widest mb-2">
                            :: ADMIN · GAME HEALTH
                        </div>
                        <h1 className="text-3xl font-semibold tracking-tight">
                            Game Health
                        </h1>
                        <p className="text-sm text-muted-foreground mt-2 max-w-2xl">
                            Telemetria runtime — economia, mercato, progressione, PvP,
                            anomalie. Solo lettura. Gilde test/demo/archiviate escluse.
                        </p>
                    </div>
                    <div className="flex flex-col items-end gap-1.5">
                        <Button
                            onClick={fetchAll}
                            disabled={loading}
                            data-testid="gh-refresh-btn"
                            className="h-10 rounded-sm bg-primary text-primary-foreground hover:bg-primary/90"
                        >
                            {loading ? "Aggiornamento…" : "↻ Aggiorna"}
                        </Button>
                        <div
                            className="text-[10px] text-muted-foreground tracking-widest"
                            data-testid="gh-refreshed-at"
                        >
                            {refreshedAt
                                ? `ultimo refresh: ${refreshedAt.toLocaleTimeString("it-IT")}`
                                : "nessun refresh"}
                        </div>
                    </div>
                </div>

                {hasAnomalies && (
                    <div
                        data-testid="gh-anomalies-banner"
                        className="border border-red-500/50 bg-red-500/10 rounded-sm p-3 mb-5 flex items-center gap-3"
                    >
                        <span className="text-red-300 text-xs tracking-widest">
                            ⚠ ANOMALIE RILEVATE
                        </span>
                        <span className="text-xs text-muted-foreground">
                            {anomaliesWarnings.length} warning attivi — vedi sezione qui sotto.
                        </span>
                    </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
                    {ENDPOINTS.map((e) => (
                        <CardShell
                            key={e.key}
                            testid={`gh-card-${e.key}`}
                            title={e.title}
                            subtitle={e.subtitle}
                        >
                            {loading && !results[e.key] && (
                                <div className="text-[11px] text-muted-foreground italic py-3">
                                    caricamento<span className="caret-blink" />
                                </div>
                            )}
                            {!loading && errors[e.key] && (
                                <div
                                    data-testid={`gh-error-${e.key}`}
                                    className="text-xs text-red-300 border border-red-500/40 bg-red-500/5 rounded-sm px-3 py-2"
                                >
                                    Errore: {errors[e.key]}
                                </div>
                            )}
                            {!errors[e.key] && (
                                <>
                                    {e.key === "economy" && <EconomyCard data={results.economy} />}
                                    {e.key === "materials" && <MaterialsCard data={results.materials} />}
                                    {e.key === "shop" && <ShopCard data={results.shop} />}
                                    {e.key === "progression" && <ProgressionCard data={results.progression} />}
                                    {e.key === "competitive" && <CompetitiveCard data={results.competitive} />}
                                    {e.key === "anomalies" && <AnomaliesCard data={results.anomalies} />}
                                </>
                            )}
                        </CardShell>
                    ))}
                </div>

                <UnarchiveForm />
            </main>
        </div>
    );
}
