// ROUND 6B.3 Wave 1.5 — Pagina /roster/manage.
// Bulk retire UI con filtri (search/role/rarity/level), sort multi-criterio,
// multi-select e modal di conferma. Solo avventurieri non-retired.
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import AppHeader from "../components/AppHeader";
import { Button } from "../components/ui/button";
import { useT } from "../i18n/I18nContext";
import { api, formatApiError } from "../lib/api";
import { DORM_CAP_BY_LEVEL } from "../utils/structures";

const RARITY_ORDER = ["Common", "Uncommon", "Rare", "Epic", "Legendary"];

function powerOf(a) {
    return Number(a.base_power || a.power || 0);
}

export default function RosterManage() {
    const { t } = useT();
    const navigate = useNavigate();
    const [advs, setAdvs] = useState([]);
    const [cap, setCap] = useState(0);
    const [dormLevel, setDormLevel] = useState(0);
    const [loading, setLoading] = useState(true);
    const [selected, setSelected] = useState(new Set());
    const [search, setSearch] = useState("");
    const [filterRole, setFilterRole] = useState("");
    const [filterRarity, setFilterRarity] = useState("");
    const [sortBy, setSortBy] = useState("power");
    const [sortDir, setSortDir] = useState("desc");
    const [confirmOpen, setConfirmOpen] = useState(false);
    const [retiring, setRetiring] = useState(false);

    async function refresh() {
        setLoading(true);
        try {
            const [advR, terrR] = await Promise.all([
                api.get("/adventurers"),
                api.get("/territory"),
            ]);
            const list = (advR.data?.adventurers || []).filter((a) => !a.is_retired);
            const lvl = Number(terrR.data?.territory?.structures?.dormitories?.level || 0);
            setAdvs(list);
            setDormLevel(lvl);
            setCap(DORM_CAP_BY_LEVEL[lvl] || 0);
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => { refresh(); }, []);

    const filtered = useMemo(() => {
        let out = advs;
        const q = search.trim().toLowerCase();
        if (q) out = out.filter((a) => (a.name || "").toLowerCase().includes(q));
        if (filterRole) out = out.filter((a) => (a.class_role || "") === filterRole);
        if (filterRarity) out = out.filter((a) => (a.rarity || "") === filterRarity);

        const cmp = (a, b) => {
            let va, vb;
            switch (sortBy) {
                case "name": va = a.name || ""; vb = b.name || ""; break;
                case "level": va = Number(a.level || 0); vb = Number(b.level || 0); break;
                case "rarity":
                    va = RARITY_ORDER.indexOf(a.rarity || "Common");
                    vb = RARITY_ORDER.indexOf(b.rarity || "Common");
                    break;
                case "power":
                default: va = powerOf(a); vb = powerOf(b);
            }
            if (va < vb) return sortDir === "asc" ? -1 : 1;
            if (va > vb) return sortDir === "asc" ? 1 : -1;
            return 0;
        };
        return [...out].sort(cmp);
    }, [advs, search, filterRole, filterRarity, sortBy, sortDir]);

    const roles = useMemo(
        () => Array.from(new Set(advs.map((a) => a.class_role).filter(Boolean))).sort(),
        [advs],
    );

    const overCapBy = Math.max(0, advs.length - cap);
    const allSelectedIds = filtered.map((a) => a.id);
    const allChecked = allSelectedIds.length > 0
        && allSelectedIds.every((id) => selected.has(id));

    function toggleAll() {
        const next = new Set(selected);
        if (allChecked) allSelectedIds.forEach((id) => next.delete(id));
        else allSelectedIds.forEach((id) => next.add(id));
        setSelected(next);
    }

    function toggleOne(id) {
        const next = new Set(selected);
        if (next.has(id)) next.delete(id);
        else next.add(id);
        setSelected(next);
    }

    async function doRetire() {
        setRetiring(true);
        const ids = Array.from(selected);
        let success = 0;
        let failed = 0;
        for (const id of ids) {
            try {
                await api.post(`/adventurers/${id}/retire`, {
                    reason: "Over-cap manual cleanup",
                });
                success++;
            } catch (_e) {
                failed++;
            }
        }
        setRetiring(false);
        setConfirmOpen(false);
        setSelected(new Set());
        if (success > 0) {
            toast.success(t("rosterManage.retire_success", { n: success }));
        }
        if (failed > 0) {
            toast.error(t("rosterManage.retire_partial_fail", { n: failed }));
        }
        await refresh();
    }

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg">
            <AppHeader subtitle="ROSTER MANAGE" />
            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8" data-testid="roster-manage-page">

                <div className="sticky top-0 z-10 bg-background border-b border-border pb-4 mb-6">
                    <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
                        <div>
                            <div className="text-xs text-amber tracking-widest mb-2">
                                :: ROSTER MANAGEMENT
                            </div>
                            <h1 className="text-3xl font-semibold tracking-tight">
                                {t("rosterManage.title")}
                            </h1>
                            <p className="text-sm text-muted-foreground mt-2 max-w-2xl">
                                {t("rosterManage.subtitle")}
                            </p>
                        </div>
                        <Link
                            to="/territory"
                            data-testid="roster-manage-territory-link"
                            className="text-amber font-bold tracking-widest text-xs hover:underline self-start"
                        >
                            {t("rosterManage.upgrade_cta")} →
                        </Link>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 mt-4">
                        <Stat label={t("rosterManage.stat_current")}
                              testid="roster-manage-stat-current" value={advs.length} />
                        <Stat label={t("rosterManage.stat_cap")}
                              testid="roster-manage-stat-cap" value={cap} />
                        <Stat label={t("rosterManage.stat_dormitories")}
                              testid="roster-manage-stat-dorm" value={`Lv${dormLevel}`} />
                        <Stat label={t("rosterManage.stat_must_retire")}
                              testid="roster-manage-stat-must-retire" value={overCapBy}
                              accent={overCapBy > 0} />
                    </div>
                </div>

                {/* Filters */}
                <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 mb-4 text-xs">
                    <input
                        data-testid="roster-manage-filter-search"
                        type="text"
                        placeholder={t("rosterManage.filter_search")}
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="bg-card border border-border rounded-sm px-3 py-2 text-foreground"
                    />
                    <select
                        data-testid="roster-manage-filter-role"
                        value={filterRole}
                        onChange={(e) => setFilterRole(e.target.value)}
                        className="bg-card border border-border rounded-sm px-3 py-2 text-foreground"
                    >
                        <option value="">{t("rosterManage.filter_all_roles")}</option>
                        {roles.map((r) => <option key={r} value={r}>{r}</option>)}
                    </select>
                    <select
                        data-testid="roster-manage-filter-rarity"
                        value={filterRarity}
                        onChange={(e) => setFilterRarity(e.target.value)}
                        className="bg-card border border-border rounded-sm px-3 py-2 text-foreground"
                    >
                        <option value="">{t("rosterManage.filter_all_rarities")}</option>
                        {RARITY_ORDER.map((r) => <option key={r} value={r}>{r}</option>)}
                    </select>
                    <select
                        data-testid="roster-manage-sort-by"
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                        className="bg-card border border-border rounded-sm px-3 py-2 text-foreground"
                    >
                        <option value="power">{t("rosterManage.sort_power")}</option>
                        <option value="rarity">{t("rosterManage.sort_rarity")}</option>
                        <option value="level">{t("rosterManage.sort_level")}</option>
                        <option value="name">{t("rosterManage.sort_name")}</option>
                    </select>
                    <select
                        data-testid="roster-manage-sort-dir"
                        value={sortDir}
                        onChange={(e) => setSortDir(e.target.value)}
                        className="bg-card border border-border rounded-sm px-3 py-2 text-foreground"
                    >
                        <option value="desc">{t("rosterManage.sort_desc")}</option>
                        <option value="asc">{t("rosterManage.sort_asc")}</option>
                    </select>
                </div>

                {/* Bulk action bar */}
                <div className="flex items-center justify-between mb-3 text-xs text-muted-foreground">
                    <span data-testid="roster-manage-count-selected">
                        {t("rosterManage.selected_count", { n: selected.size })}
                    </span>
                    <Button
                        data-testid="roster-manage-bulk-retire-btn"
                        variant="destructive"
                        disabled={selected.size === 0 || retiring}
                        onClick={() => setConfirmOpen(true)}
                    >
                        {t("rosterManage.bulk_retire_btn", { n: selected.size })}
                    </Button>
                </div>

                {/* Table */}
                {loading ? (
                    <div className="text-muted-foreground text-sm">{t("common.loading")}</div>
                ) : filtered.length === 0 ? (
                    <div data-testid="roster-manage-empty" className="text-muted-foreground text-sm border border-border rounded-sm p-6 text-center">
                        {t("rosterManage.empty")}
                    </div>
                ) : (
                    <div className="overflow-x-auto border border-border rounded-sm">
                        <table className="w-full text-xs">
                            <thead className="bg-card text-amber tracking-widest">
                                <tr>
                                    <th className="px-2 py-2 text-left">
                                        <input
                                            data-testid="roster-manage-select-all"
                                            type="checkbox"
                                            checked={allChecked}
                                            onChange={toggleAll}
                                        />
                                    </th>
                                    <th className="px-2 py-2 text-left">{t("rosterManage.col_name")}</th>
                                    <th className="px-2 py-2 text-left">{t("rosterManage.col_class")}</th>
                                    <th className="px-2 py-2 text-left">{t("rosterManage.col_role")}</th>
                                    <th className="px-2 py-2 text-left">{t("rosterManage.col_rarity")}</th>
                                    <th className="px-2 py-2 text-right">{t("rosterManage.col_level")}</th>
                                    <th className="px-2 py-2 text-right">{t("rosterManage.col_power")}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filtered.map((a) => (
                                    <tr
                                        key={a.id}
                                        data-testid={`roster-manage-row-${a.id}`}
                                        className="border-t border-border hover:bg-card/40"
                                    >
                                        <td className="px-2 py-2">
                                            <input
                                                data-testid={`roster-manage-select-${a.id}`}
                                                type="checkbox"
                                                checked={selected.has(a.id)}
                                                onChange={() => toggleOne(a.id)}
                                            />
                                        </td>
                                        <td className="px-2 py-2 font-bold text-foreground">{a.name}</td>
                                        <td className="px-2 py-2">{a.class_name || "—"}</td>
                                        <td className="px-2 py-2">{a.class_role || "—"}</td>
                                        <td className="px-2 py-2">{a.rarity || "Common"}</td>
                                        <td className="px-2 py-2 text-right">{a.level || 1}</td>
                                        <td className="px-2 py-2 text-right">{powerOf(a)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Confirm modal */}
                {confirmOpen && (
                    <div
                        data-testid="roster-manage-confirm-modal"
                        className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
                    >
                        <div className="bg-card border border-border rounded-sm p-6 max-w-lg w-full mx-4">
                            <h2 className="text-amber tracking-widest text-xs mb-3">
                                :: {t("rosterManage.confirm_title")}
                            </h2>
                            <p className="text-sm mb-3">
                                {t("rosterManage.confirm_body", { n: selected.size })}
                            </p>
                            <ul className="text-xs text-muted-foreground max-h-40 overflow-y-auto mb-4 border border-border rounded-sm p-2">
                                {Array.from(selected).map((id) => {
                                    const a = advs.find((x) => x.id === id);
                                    return a ? (
                                        <li key={id} className="py-0.5">
                                            • {a.name} (Lv{a.level || 1}, {a.rarity || "Common"})
                                        </li>
                                    ) : null;
                                })}
                            </ul>
                            <p className="text-xs text-red-400 mb-4">
                                {t("rosterManage.confirm_disclaimer")}
                            </p>
                            <div className="flex justify-end gap-2">
                                <Button
                                    data-testid="roster-manage-confirm-cancel"
                                    variant="secondary"
                                    disabled={retiring}
                                    onClick={() => setConfirmOpen(false)}
                                >
                                    {t("common.cancel")}
                                </Button>
                                <Button
                                    data-testid="roster-manage-confirm-submit"
                                    variant="destructive"
                                    disabled={retiring}
                                    onClick={doRetire}
                                >
                                    {retiring ? t("common.loading") : t("rosterManage.confirm_submit")}
                                </Button>
                            </div>
                        </div>
                    </div>
                )}

                <div className="mt-6 text-xs text-muted-foreground">
                    <button
                        data-testid="roster-manage-back-link"
                        type="button"
                        onClick={() => navigate(-1)}
                        className="hover:underline"
                    >
                        ← {t("common.back")}
                    </button>
                </div>
            </main>
        </div>
    );
}

function Stat({ label, value, testid, accent = false }) {
    return (
        <div className="border border-border bg-card rounded-sm p-3">
            <div className="text-[10px] text-muted-foreground tracking-widest mb-1">{label}</div>
            <div
                data-testid={testid}
                className={`text-xl font-bold ${accent ? "text-red-400" : "text-foreground"}`}
            >
                {value}
            </div>
        </div>
    );
}
