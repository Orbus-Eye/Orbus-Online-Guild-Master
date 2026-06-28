/* ROUND 11.2 TASK 5b — Admin Ops page (route /admin/ops).
 * 3 tabs: Search | Detail | Audit. Modal Grant Gold / Grant Item.
 * Access control: NOT-AUTHORIZED clean page (no silent redirect).
 */
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import GrantGoldModal from "@/components/admin/GrantGoldModal";
import GrantItemModal from "@/components/admin/GrantItemModal";

function NotAuthorized() {
    return (
        <div
            data-testid="admin-not-authorized"
            className="min-h-screen flex items-center justify-center p-6 bg-background text-foreground"
        >
            <div className="max-w-sm text-center space-y-4 border border-border rounded-sm p-8 bg-card">
                <div className="text-4xl">⛔</div>
                <h1 className="text-lg font-bold uppercase tracking-wider">Accesso admin richiesto</h1>
                <p className="text-sm text-muted-foreground">
                    Questa pagina è riservata agli amministratori. Se ritieni si tratti di un errore,
                    contatta il supporto.
                </p>
                <Link
                    to="/dashboard"
                    data-testid="admin-not-authorized-back"
                    className="inline-block bg-secondary border border-border hover:bg-secondary/70 px-4 py-2 rounded-sm text-xs"
                >
                    ← Torna al Dashboard
                </Link>
            </div>
        </div>
    );
}

export default function AdminOps() {
    const { user } = useAuth();
    const [tab, setTab] = useState("search");
    const [q, setQ] = useState("");
    const [searchData, setSearchData] = useState({ guilds: [], total: 0, limit: 20, offset: 0 });
    const [selected, setSelected] = useState(null);
    const [detail, setDetail] = useState(null);
    const [auditFilter, setAuditFilter] = useState({ guild: "", action: "", since: "" });
    const [auditData, setAuditData] = useState({ events: [], total: 0 });
    const [loading, setLoading] = useState(false);
    const [modal, setModal] = useState(null);  // 'gold' | 'item' | null
    const [offset, setOffset] = useState(0);

    const isAdmin = user?.is_admin === true;

    const runSearch = async (qVal, off = 0) => {
        setLoading(true);
        try {
            const { data } = await api.get(`/admin/guilds/search`, {
                params: { q: qVal || "", limit: 20, offset: off },
            });
            setSearchData(data);
            setOffset(off);
        } catch (err) {
            toast.error(formatApiError(err));
        } finally { setLoading(false); }
    };

    const loadDetail = async (gid) => {
        setLoading(true);
        try {
            const { data } = await api.get(`/admin/guilds/${gid}`);
            setDetail(data);
            setSelected(gid);
            setTab("detail");
        } catch (err) {
            toast.error(formatApiError(err));
        } finally { setLoading(false); }
    };

    const refreshDetail = async () => {
        if (selected) await loadDetail(selected);
    };

    const runAudit = async () => {
        setLoading(true);
        try {
            const params = { limit: 50 };
            if (auditFilter.guild) params.guild = auditFilter.guild;
            if (auditFilter.action) params.action = auditFilter.action;
            if (auditFilter.since) params.since = auditFilter.since;
            const { data } = await api.get(`/admin/audit`, { params });
            setAuditData(data);
        } catch (err) {
            toast.error(formatApiError(err));
        } finally { setLoading(false); }
    };

    useEffect(() => { if (isAdmin && tab === "search") runSearch("", 0); }, [isAdmin]); // eslint-disable-line
    useEffect(() => { if (isAdmin && tab === "audit") runAudit(); }, [isAdmin, tab]); // eslint-disable-line

    if (user === undefined || user === null) return null;
    if (!isAdmin) return <NotAuthorized />;

    const totalPages = Math.max(1, Math.ceil((searchData.total || 0) / 20));
    const currentPage = Math.floor(offset / 20) + 1;

    return (
        <div className="min-h-screen bg-background text-foreground" data-testid="admin-ops-page">
            <header className="border-b border-border px-4 sm:px-6 py-4">
                <div className="flex items-center justify-between gap-3 max-w-6xl mx-auto">
                    <h1 className="text-base sm:text-lg font-bold uppercase tracking-wider">Admin Ops</h1>
                    <Link to="/dashboard" className="text-xs text-muted-foreground hover:text-foreground">
                        ← Dashboard
                    </Link>
                </div>
            </header>

            {/* Tab nav */}
            <div className="border-b border-border px-4 sm:px-6 max-w-6xl mx-auto">
                <div className="flex gap-1 overflow-x-auto">
                    {[
                        { key: "search", label: "🔍 Search" },
                        { key: "detail", label: "📋 Detail", disabled: !detail },
                        { key: "audit", label: "📜 Audit" },
                    ].map((t) => (
                        <button
                            key={t.key}
                            data-testid={`admin-ops-tab-${t.key}`}
                            onClick={() => !t.disabled && setTab(t.key)}
                            disabled={t.disabled}
                            className={`px-4 py-2 text-xs font-semibold border-b-2 ${
                                tab === t.key
                                    ? "border-amber text-amber"
                                    : "border-transparent text-muted-foreground hover:text-foreground"
                            } disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap`}
                        >
                            {t.label}
                        </button>
                    ))}
                </div>
            </div>

            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-4 space-y-4">
                {/* SEARCH TAB */}
                {tab === "search" && (
                    <div className="space-y-3" data-testid="admin-ops-search-panel">
                        <div className="flex gap-2">
                            <input
                                type="text"
                                value={q}
                                onChange={(e) => setQ(e.target.value)}
                                onKeyDown={(e) => e.key === "Enter" && runSearch(q, 0)}
                                placeholder="Nome gilda o public_id"
                                data-testid="admin-ops-search-input"
                                className="flex-1 bg-secondary border border-border rounded-sm px-3 py-2 text-sm"
                            />
                            <button
                                data-testid="admin-ops-search-submit"
                                onClick={() => runSearch(q, 0)}
                                disabled={loading}
                                className="bg-amber/90 text-background px-4 py-2 rounded-sm text-xs font-bold disabled:opacity-50"
                            >
                                Cerca
                            </button>
                        </div>

                        {searchData.guilds.length === 0 && !loading && (
                            <p className="text-sm text-muted-foreground text-center py-8"
                               data-testid="admin-ops-search-empty">
                                Nessuna gilda trovata.
                            </p>
                        )}

                        {searchData.guilds.length > 0 && (
                            <>
                                <div className="overflow-x-auto">
                                    <table className="w-full text-xs min-w-[600px]" data-testid="admin-ops-search-table">
                                        <thead className="border-b border-border">
                                            <tr className="text-left text-muted-foreground">
                                                <th className="py-2 px-2">Name</th>
                                                <th className="py-2 px-2">Owner</th>
                                                <th className="py-2 px-2">Gold</th>
                                                <th className="py-2 px-2">Roster</th>
                                                <th className="py-2 px-2">Dorm</th>
                                                <th className="py-2 px-2">Flags</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {searchData.guilds.map((g) => (
                                                <tr
                                                    key={g.public_id}
                                                    onClick={() => loadDetail(g.public_id)}
                                                    data-testid={`admin-ops-row-${g.public_id}`}
                                                    className="border-b border-border/40 hover:bg-secondary/30 cursor-pointer"
                                                >
                                                    <td className="py-2 px-2 font-mono">{g.name}</td>
                                                    <td className="py-2 px-2">{g.owner_email_masked}</td>
                                                    <td className="py-2 px-2 text-amber">{g.gold}</td>
                                                    <td className="py-2 px-2">{g.roster_count}/{g.roster_cap}</td>
                                                    <td className="py-2 px-2">Lv{g.dormitory_level}</td>
                                                    <td className="py-2 px-2">
                                                        {g.is_test_artifact && (
                                                            <span className="text-[10px] bg-muted px-1.5 rounded">TEST</span>
                                                        )}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                                <div className="flex items-center justify-between text-xs text-muted-foreground"
                                     data-testid="admin-ops-pagination">
                                    <button
                                        onClick={() => runSearch(q, Math.max(0, offset - 20))}
                                        disabled={offset === 0 || loading}
                                        className="px-2 py-1 hover:text-foreground disabled:opacity-30"
                                    >← Precedente</button>
                                    <span>Pag {currentPage} di {totalPages} ({searchData.total} totali)</span>
                                    <button
                                        onClick={() => runSearch(q, offset + 20)}
                                        disabled={offset + 20 >= searchData.total || loading}
                                        className="px-2 py-1 hover:text-foreground disabled:opacity-30"
                                    >Successivo →</button>
                                </div>
                            </>
                        )}
                    </div>
                )}

                {/* DETAIL TAB */}
                {tab === "detail" && detail && (
                    <div className="space-y-4" data-testid="admin-ops-detail-panel">
                        <div className="border border-border rounded-sm p-4 bg-card">
                            <div className="flex items-start justify-between gap-3 flex-wrap">
                                <div>
                                    <h2 className="text-base font-bold">{detail.name}</h2>
                                    <p className="text-xs font-mono text-muted-foreground">
                                        public_id: {detail.public_id}
                                    </p>
                                </div>
                                {detail.flags?.is_test_artifact && (
                                    <span className="text-[10px] bg-muted px-2 py-1 rounded">TEST ARTIFACT</span>
                                )}
                            </div>
                            <div className="grid grid-cols-2 gap-3 mt-4 text-xs">
                                <div><span className="text-muted-foreground">Owner:</span> {detail.owner_email_masked}</div>
                                <div><span className="text-muted-foreground">Gold:</span> <span className="text-amber">{detail.gold}</span></div>
                                <div><span className="text-muted-foreground">Roster:</span> {detail.roster?.current}/{detail.roster?.cap}</div>
                                <div><span className="text-muted-foreground">Dorm Lv:</span> {detail.territory?.dormitories_level}</div>
                                <div><span className="text-muted-foreground">Created:</span> {detail.created_at?.slice(0, 10)}</div>
                                <div><span className="text-muted-foreground">Updated:</span> {detail.updated_at?.slice(0, 10)}</div>
                            </div>
                        </div>
                        <div className="flex flex-col sm:flex-row gap-2">
                            <button
                                data-testid="admin-ops-grant-gold-open"
                                onClick={() => setModal("gold")}
                                className="bg-amber/90 text-background px-4 py-2 rounded-sm text-xs font-bold flex-1"
                            >💰 Grant Gold</button>
                            <button
                                data-testid="admin-ops-grant-item-open"
                                onClick={() => setModal("item")}
                                className="bg-amber/90 text-background px-4 py-2 rounded-sm text-xs font-bold flex-1"
                            >🎁 Grant Item</button>
                        </div>
                    </div>
                )}

                {/* AUDIT TAB */}
                {tab === "audit" && (
                    <div className="space-y-3" data-testid="admin-ops-audit-panel">
                        <div className="flex flex-col sm:flex-row gap-2">
                            <input
                                type="text" placeholder="Guild public_id (opzionale)"
                                value={auditFilter.guild}
                                onChange={(e) => setAuditFilter({ ...auditFilter, guild: e.target.value })}
                                data-testid="admin-ops-audit-guild"
                                className="flex-1 bg-secondary border border-border rounded-sm px-3 py-2 text-xs"
                            />
                            <select
                                value={auditFilter.action}
                                onChange={(e) => setAuditFilter({ ...auditFilter, action: e.target.value })}
                                data-testid="admin-ops-audit-action"
                                className="bg-secondary border border-border rounded-sm px-3 py-2 text-xs"
                            >
                                <option value="">All actions</option>
                                <option value="admin_gold_granted">admin_gold_granted</option>
                                <option value="admin_item_granted">admin_item_granted</option>
                            </select>
                            <button onClick={runAudit} disabled={loading}
                                    data-testid="admin-ops-audit-refresh"
                                    className="bg-amber/90 text-background px-4 py-2 rounded-sm text-xs font-bold disabled:opacity-50">
                                Aggiorna
                            </button>
                        </div>
                        {auditData.events.length === 0 ? (
                            <p className="text-sm text-muted-foreground text-center py-8">Nessun audit event.</p>
                        ) : (
                            <div className="space-y-2">
                                {auditData.events.map((ev, i) => (
                                    <div key={i} data-testid={`admin-ops-audit-row-${i}`}
                                         className="border border-border rounded-sm p-3 bg-card text-xs">
                                        <div className="flex items-center justify-between gap-2 flex-wrap">
                                            <span className="font-mono text-amber">{ev.event_type}</span>
                                            <span className="text-muted-foreground">{ev.ts?.slice(0, 19)}</span>
                                        </div>
                                        <p className="mt-1">
                                            <span className="text-muted-foreground">By:</span> {ev.actor_email_masked}
                                        </p>
                                        <p>
                                            <span className="text-muted-foreground">Target:</span>{" "}
                                            {ev.target_guild_name} <span className="font-mono text-[10px]">({ev.target_guild_public_id})</span>
                                        </p>
                                        {ev.event_type === "admin_gold_granted" && (
                                            <p>
                                                amount: <strong className="text-amber">{ev.metadata?.amount}</strong>{" "}
                                                — reason: {ev.metadata?.reason}
                                            </p>
                                        )}
                                        {ev.event_type === "admin_item_granted" && (
                                            <p>
                                                {ev.metadata?.quantity} × <strong>{ev.metadata?.item_slug}</strong>{" "}
                                                — reason: {ev.metadata?.reason}
                                            </p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </main>

            {modal === "gold" && detail && (
                <GrantGoldModal
                    guild={detail}
                    onClose={() => setModal(null)}
                    onGranted={refreshDetail}
                />
            )}
            {modal === "item" && detail && (
                <GrantItemModal
                    guild={detail}
                    onClose={() => setModal(null)}
                    onGranted={refreshDetail}
                />
            )}
        </div>
    );
}
