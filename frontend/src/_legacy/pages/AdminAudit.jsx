// ROUND 16.A Phase 3 — Admin Audit Dashboard (read-only).
// Consumes /api/admin/audit/{summary,trigger-emissions,events}.
// Italian UI, dark theme matching existing admin pages.

import { useCallback, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { toast } from "sonner";

import AppHeader from "../components/AppHeader";
import { useAuth } from "../context/AuthContext";
import { api, formatApiError } from "../lib/api";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";

const TABS = [
    { id: "summary", label: "Riepilogo" },
    { id: "triggers", label: "Emissioni Trigger" },
    { id: "events", label: "Timeline Audit" },
];

const TRIGGER_EVENT_OPTIONS = [
    "", "item_crafted", "market_purchase", "auction_sale",
    "auction_purchase", "consortium_joined", "season_league_reached",
    "leaderboard_rank_reached", "item_disenchanted", "material_purchased",
    "pvp_match_completed", "territory_upgraded",
];

const AUDIT_EVENT_OPTIONS = [
    "", "achievement_unlocked", "guild_xp_gained", "onboarding_graduated",
];

function StatCard({ label, value, testid }) {
    return (
        <div className="border border-border bg-card rounded-sm p-3" data-testid={testid}>
            <div className="text-[10px] text-muted-foreground tracking-widest">{label}</div>
            <div className="text-xl font-semibold tracking-tight mt-1">{value}</div>
        </div>
    );
}

function SummaryTab() {
    const [windowHours, setWindowHours] = useState(24);
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const r = await api.get(`/admin/audit/summary?window_hours=${windowHours}`);
            setData(r.data);
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setLoading(false);
        }
    }, [windowHours]);

    useEffect(() => { load(); }, [load]);

    return (
        <section data-testid="audit-summary-tab" className="space-y-4">
            <div className="flex items-end gap-2">
                <div>
                    <Label className="text-[10px] text-muted-foreground tracking-widest">Finestra (ore)</Label>
                    <Input
                        type="number"
                        min={1}
                        max={720}
                        value={windowHours}
                        onChange={(e) => setWindowHours(Math.max(1, Number(e.target.value) || 24))}
                        className="w-32 rounded-sm"
                        data-testid="audit-summary-window-input"
                    />
                </div>
                <Button onClick={load} disabled={loading} className="rounded-sm" data-testid="audit-summary-refresh">
                    {loading ? "..." : "Aggiorna"}
                </Button>
                {data?.window_clamped && (
                    <span className="text-[10px] text-amber italic">
                        (finestra limitata a 720h = 30 giorni)
                    </span>
                )}
            </div>

            {data && (
                <>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <StatCard
                            label="ACHIEVEMENT SBLOCCATI"
                            value={data.achievement_unlocked_count}
                            testid="audit-stat-ach-unlocked"
                        />
                        <StatCard
                            label="XP GILDA EROGATO"
                            value={data.guild_xp_gained_total_amount.toLocaleString("it-IT")}
                            testid="audit-stat-xp-total"
                        />
                        <StatCard
                            label="EVENTI XP"
                            value={data.guild_xp_gained_event_count}
                            testid="audit-stat-xp-events"
                        />
                        <StatCard
                            label="GILDE GRADUATED"
                            value={data.guilds_graduated_count}
                            testid="audit-stat-graduated"
                        />
                    </div>

                    <div className="border border-border bg-card rounded-sm p-3">
                        <div className="text-[10px] text-muted-foreground tracking-widest mb-2">
                            :: TOP EVENTI TRIGGER
                        </div>
                        {data.top_trigger_events.length === 0 ? (
                            <p className="text-xs text-muted-foreground italic">
                                Nessuna emissione trigger nella finestra selezionata.
                            </p>
                        ) : (
                            <ul className="space-y-0.5" data-testid="audit-top-triggers">
                                {data.top_trigger_events.map((t) => (
                                    <li key={t.event_name} className="flex justify-between text-xs border-b border-border/40 py-0.5">
                                        <span className="font-mono">{t.event_name}</span>
                                        <span className="text-amber">{t.count}</span>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                </>
            )}
        </section>
    );
}

function Pager({ offset, limit, total, onChange, testidPrefix }) {
    const page = Math.floor(offset / limit) + 1;
    const totalPages = Math.max(1, Math.ceil(total / limit));
    return (
        <div className="flex items-center justify-between text-xs mt-2">
            <span className="text-muted-foreground">
                Pagina {page} / {totalPages} · {total} totali
            </span>
            <div className="flex gap-1">
                <Button
                    size="sm" variant="outline"
                    disabled={offset === 0}
                    onClick={() => onChange(Math.max(0, offset - limit))}
                    data-testid={`${testidPrefix}-prev`}
                >← Prec.</Button>
                <Button
                    size="sm" variant="outline"
                    disabled={offset + limit >= total}
                    onClick={() => onChange(offset + limit)}
                    data-testid={`${testidPrefix}-next`}
                >Succ. →</Button>
            </div>
        </div>
    );
}

function TriggersTab() {
    const [eventName, setEventName] = useState("");
    const [guildId, setGuildId] = useState("");
    const [offset, setOffset] = useState(0);
    const [data, setData] = useState({ items: [], total: 0 });
    const [loading, setLoading] = useState(false);
    const LIMIT = 50;

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const qs = new URLSearchParams({ limit: String(LIMIT), offset: String(offset) });
            if (eventName) qs.set("event_name", eventName);
            if (guildId) qs.set("guild_id", guildId.trim());
            const r = await api.get(`/admin/audit/trigger-emissions?${qs}`);
            setData(r.data);
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setLoading(false);
        }
    }, [eventName, guildId, offset]);

    useEffect(() => { load(); }, [load]);

    return (
        <section data-testid="audit-triggers-tab" className="space-y-3">
            <div className="flex flex-wrap items-end gap-2">
                <div>
                    <Label className="text-[10px] text-muted-foreground tracking-widest">Evento</Label>
                    <select
                        value={eventName}
                        onChange={(e) => { setEventName(e.target.value); setOffset(0); }}
                        className="w-56 bg-card border border-border rounded-sm px-2 py-1.5 text-sm"
                        data-testid="audit-triggers-event-filter"
                    >
                        {TRIGGER_EVENT_OPTIONS.map((o) => (
                            <option key={o} value={o}>{o || "(tutti)"}</option>
                        ))}
                    </select>
                </div>
                <div>
                    <Label className="text-[10px] text-muted-foreground tracking-widest">Guild ID</Label>
                    <Input
                        value={guildId}
                        onChange={(e) => { setGuildId(e.target.value); setOffset(0); }}
                        placeholder="uuid…"
                        className="w-64 rounded-sm font-mono text-xs"
                        data-testid="audit-triggers-guild-filter"
                    />
                </div>
                <Button onClick={load} disabled={loading} className="rounded-sm" data-testid="audit-triggers-refresh">
                    {loading ? "..." : "Filtra"}
                </Button>
            </div>

            <div className="border border-border bg-card rounded-sm overflow-x-auto">
                <table className="w-full text-xs" data-testid="audit-triggers-table">
                    <thead className="text-[10px] tracking-widest text-muted-foreground border-b border-border">
                        <tr>
                            <th className="text-left p-2">EVENT</th>
                            <th className="text-left p-2">GUILD ID</th>
                            <th className="text-left p-2">IDEMPOTENCY KEY</th>
                            <th className="text-left p-2">CREATED AT</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.items.length === 0 ? (
                            <tr><td colSpan={4} className="text-center text-muted-foreground italic p-4">
                                Nessuna emissione corrispondente ai filtri.
                            </td></tr>
                        ) : data.items.map((row, i) => (
                            <tr key={`${row.idempotency_key}-${i}`} className="border-t border-border/40">
                                <td className="p-2 font-mono">{row.event_name}</td>
                                <td className="p-2 font-mono text-muted-foreground truncate max-w-[200px]">{row.guild_id}</td>
                                <td className="p-2 font-mono text-[10px] text-muted-foreground truncate max-w-[200px]">{row.idempotency_key}</td>
                                <td className="p-2 text-muted-foreground">{(row.created_at || "").replace("T", " ").slice(0, 19)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <Pager offset={offset} limit={LIMIT} total={data.total}
                onChange={setOffset} testidPrefix="audit-triggers-pager" />
        </section>
    );
}

function EventsTab() {
    const [eventType, setEventType] = useState("");
    const [guildId, setGuildId] = useState("");
    const [from, setFrom] = useState("");
    const [to, setTo] = useState("");
    const [offset, setOffset] = useState(0);
    const [data, setData] = useState({ items: [], total: 0 });
    const [loading, setLoading] = useState(false);
    const LIMIT = 50;

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const qs = new URLSearchParams({ limit: String(LIMIT), offset: String(offset) });
            if (eventType) qs.set("event_type", eventType);
            if (guildId) qs.set("guild_id", guildId.trim());
            if (from) qs.set("from", from);
            if (to) qs.set("to", to);
            const r = await api.get(`/admin/audit/events?${qs}`);
            setData(r.data);
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setLoading(false);
        }
    }, [eventType, guildId, from, to, offset]);

    useEffect(() => { load(); }, [load]);

    return (
        <section data-testid="audit-events-tab" className="space-y-3">
            <div className="flex flex-wrap items-end gap-2">
                <div>
                    <Label className="text-[10px] text-muted-foreground tracking-widest">Tipo evento</Label>
                    <select
                        value={eventType}
                        onChange={(e) => { setEventType(e.target.value); setOffset(0); }}
                        className="w-56 bg-card border border-border rounded-sm px-2 py-1.5 text-sm"
                        data-testid="audit-events-type-filter"
                    >
                        {AUDIT_EVENT_OPTIONS.map((o) => (
                            <option key={o} value={o}>{o || "(tutti R16.A)"}</option>
                        ))}
                    </select>
                </div>
                <div>
                    <Label className="text-[10px] text-muted-foreground tracking-widest">Guild ID</Label>
                    <Input
                        value={guildId}
                        onChange={(e) => { setGuildId(e.target.value); setOffset(0); }}
                        placeholder="uuid…"
                        className="w-64 rounded-sm font-mono text-xs"
                        data-testid="audit-events-guild-filter"
                    />
                </div>
                <div>
                    <Label className="text-[10px] text-muted-foreground tracking-widest">Da (ISO)</Label>
                    <Input
                        value={from}
                        onChange={(e) => { setFrom(e.target.value); setOffset(0); }}
                        placeholder="2026-06-01T00:00:00"
                        className="w-48 rounded-sm font-mono text-xs"
                        data-testid="audit-events-from-filter"
                    />
                </div>
                <div>
                    <Label className="text-[10px] text-muted-foreground tracking-widest">A (ISO)</Label>
                    <Input
                        value={to}
                        onChange={(e) => { setTo(e.target.value); setOffset(0); }}
                        placeholder="2026-06-30T23:59:59"
                        className="w-48 rounded-sm font-mono text-xs"
                        data-testid="audit-events-to-filter"
                    />
                </div>
                <Button onClick={load} disabled={loading} className="rounded-sm" data-testid="audit-events-refresh">
                    {loading ? "..." : "Filtra"}
                </Button>
            </div>

            <div className="border border-border bg-card rounded-sm overflow-x-auto">
                <table className="w-full text-xs" data-testid="audit-events-table">
                    <thead className="text-[10px] tracking-widest text-muted-foreground border-b border-border">
                        <tr>
                            <th className="text-left p-2">EVENT TYPE</th>
                            <th className="text-left p-2">GUILD</th>
                            <th className="text-left p-2">SOURCE</th>
                            <th className="text-left p-2">METADATA</th>
                            <th className="text-left p-2">CREATED AT</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.items.length === 0 ? (
                            <tr><td colSpan={5} className="text-center text-muted-foreground italic p-4">
                                Nessun evento audit corrispondente ai filtri.
                            </td></tr>
                        ) : data.items.map((row, i) => (
                            <tr key={`${row.id}-${i}`} className="border-t border-border/40 align-top">
                                <td className="p-2 font-mono text-amber">{row.event_type}</td>
                                <td className="p-2 font-mono text-muted-foreground truncate max-w-[180px]">{row.actor_guild_id}</td>
                                <td className="p-2 text-muted-foreground">{row.source}</td>
                                <td className="p-2 font-mono text-[10px] text-muted-foreground truncate max-w-[280px]">
                                    {JSON.stringify(row.metadata || {})}
                                </td>
                                <td className="p-2 text-muted-foreground whitespace-nowrap">{(row.created_at || "").replace("T", " ").slice(0, 19)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <Pager offset={offset} limit={LIMIT} total={data.total}
                onChange={setOffset} testidPrefix="audit-events-pager" />
        </section>
    );
}

export default function AdminAudit() {
    const { user, loading: authLoading } = useAuth();
    const [tab, setTab] = useState("summary");

    if (authLoading) {
        return (
            <div className="min-h-screen bg-background">
                <AppHeader />
                <main className="max-w-6xl mx-auto p-6 text-xs text-muted-foreground">
                    Caricamento<span className="caret-blink" />
                </main>
            </div>
        );
    }
    if (!user?.is_admin) return <Navigate to="/dashboard" replace />;

    return (
        <div className="min-h-screen bg-background">
            <AppHeader />
            <main className="max-w-6xl mx-auto p-4 sm:p-6">
                <div className="mb-4">
                    <h1 className="text-xl sm:text-2xl font-semibold tracking-tight" data-testid="admin-audit-title">
                        Audit Dashboard
                    </h1>
                    <p className="text-xs text-muted-foreground mt-1">
                        Read-only · Round 16.A · Emissioni trigger + timeline audit + KPI aggregati.
                    </p>
                </div>

                <nav className="flex border-b border-border mb-4">
                    {TABS.map((t) => (
                        <button
                            key={t.id}
                            type="button"
                            data-testid={`audit-tab-${t.id}`}
                            onClick={() => setTab(t.id)}
                            className={`px-4 py-2 text-xs tracking-widest border-b-2 transition-colors ${
                                tab === t.id
                                    ? "border-amber text-amber"
                                    : "border-transparent text-muted-foreground hover:text-foreground"
                            }`}
                        >
                            {t.label.toUpperCase()}
                        </button>
                    ))}
                </nav>

                {tab === "summary" && <SummaryTab />}
                {tab === "triggers" && <TriggersTab />}
                {tab === "events" && <EventsTab />}
            </main>
        </div>
    );
}
