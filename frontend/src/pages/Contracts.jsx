// ROUND 6D — Contract Board page: 3 tabs (daily / weekly / milestones).
// Server-authoritative: progress + claim state come from /api/contracts/*.
// Locked-state banner shown when contract_board structure is Lv0.
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";

import AppHeader from "../components/AppHeader";
import { useAuth } from "../context/AuthContext";
import { useT } from "../i18n/I18nContext";
import { api, formatApiError } from "../lib/api";

const TABS = [
    { key: "daily", testid: "contracts-tab-daily" },
    { key: "weekly", testid: "contracts-tab-weekly" },
    { key: "milestones", testid: "contracts-tab-milestones" },
];

function Reward({ gold, materials, reputation, t }) {
    return (
        <div className="text-[10px] text-amber/90 mt-2 flex flex-wrap gap-x-3 gap-y-1">
            {gold > 0 && <span>+{gold} G</span>}
            {(materials || []).map((m) => (
                <span key={m.slug} className="text-foreground/80">
                    +{m.qty} {m.slug}
                </span>
            ))}
            {reputation > 0 && (
                <span className="text-emerald-300">
                    +{reputation} {t("contracts.reputation_short", "Rep")}
                </span>
            )}
        </div>
    );
}

function ContractRow({ contract, onClaim, claiming, scope, t }) {
    const target = contract.objective_target;
    const progress = Math.min(contract.progress, target);
    const pct = target > 0 ? Math.round((progress / target) * 100) : 0;
    const completed = contract.completed;
    const claimed = contract.claimed;
    const canClaim = contract.can_claim;
    return (
        <li
            data-testid={`contract-row-${scope}-${contract.slug}`}
            className="border border-border rounded-sm p-3 bg-card/40"
        >
            <div className="flex items-start justify-between gap-3 flex-wrap">
                <div className="flex-1 min-w-0">
                    <div className="text-sm font-bold text-foreground">
                        {t(contract.display_key, contract.slug)}
                    </div>
                    <div className="text-[10px] text-muted-foreground mt-0.5">
                        {contract.objective_type}
                    </div>
                </div>
                <div className="text-[11px] tabular-nums text-foreground/80">
                    {progress} / {target}
                </div>
            </div>
            {/* Progress bar */}
            <div className="mt-2 h-1 bg-border rounded-sm overflow-hidden">
                <div
                    className={`h-full transition-all ${
                        completed ? "bg-amber" : "bg-foreground/40"
                    }`}
                    style={{ width: `${pct}%` }}
                />
            </div>
            <Reward
                gold={contract.reward_gold}
                materials={contract.reward_materials}
                reputation={contract.reward_reputation}
                t={t}
            />
            <div className="mt-3 flex items-center justify-end gap-2">
                {claimed ? (
                    <span
                        data-testid={`contract-claimed-${scope}-${contract.slug}`}
                        className="text-[10px] text-emerald-400 tracking-widest"
                    >
                        ✓ {t("contracts.claimed", "RECLAMATO")}
                    </span>
                ) : (
                    <button
                        type="button"
                        data-testid={`contract-claim-${scope}-${contract.slug}`}
                        disabled={!canClaim || claiming === contract.slug}
                        onClick={() => onClaim(contract.slug)}
                        className={`text-[11px] tracking-widest font-bold px-3 py-1 rounded-sm transition-colors ${
                            canClaim
                                ? "bg-amber text-background hover:bg-amber/90"
                                : "bg-border text-muted-foreground cursor-not-allowed"
                        }`}
                    >
                        {claiming === contract.slug
                            ? "..."
                            : completed
                              ? t("contracts.claim", "RECLAMA")
                              : t("contracts.in_progress", "IN CORSO")}
                    </button>
                )}
            </div>
        </li>
    );
}

function MilestoneRow({ milestone, onClaim, claiming, t }) {
    const target = milestone.objective_target;
    const progress = Math.min(milestone.progress, target);
    const pct = target > 0 ? Math.round((progress / target) * 100) : 0;
    const tierLocked = !milestone.tier_unlocked;
    return (
        <li
            data-testid={`milestone-row-${milestone.slug}`}
            className={`border rounded-sm p-3 ${
                tierLocked
                    ? "border-border/50 bg-card/20 opacity-60"
                    : "border-border bg-card/40"
            }`}
        >
            <div className="flex items-start justify-between gap-3 flex-wrap">
                <div className="flex-1 min-w-0">
                    <div className="text-sm font-bold text-foreground">
                        {t(milestone.display_key, milestone.slug)}
                    </div>
                    <div className="text-[10px] text-muted-foreground mt-0.5">
                        T{milestone.tier} · {milestone.objective_type}
                    </div>
                </div>
                <div className="text-[11px] tabular-nums text-foreground/80">
                    {progress} / {target}
                </div>
            </div>
            <div className="mt-2 h-1 bg-border rounded-sm overflow-hidden">
                <div
                    className={`h-full transition-all ${
                        milestone.completed ? "bg-amber" : "bg-foreground/40"
                    }`}
                    style={{ width: `${pct}%` }}
                />
            </div>
            <Reward
                gold={milestone.reward_gold}
                materials={milestone.reward_materials}
                reputation={milestone.reward_reputation}
                t={t}
            />
            <div className="mt-3 flex items-center justify-end gap-2">
                {milestone.claimed ? (
                    <span
                        data-testid={`milestone-claimed-${milestone.slug}`}
                        className="text-[10px] text-emerald-400 tracking-widest"
                    >
                        ✓ {t("contracts.claimed", "RECLAMATO")}
                    </span>
                ) : tierLocked ? (
                    <span className="text-[10px] text-muted-foreground tracking-widest">
                        🔒 {t("contracts.tier_locked", "TIER BLOCCATO")}
                    </span>
                ) : (
                    <button
                        type="button"
                        data-testid={`milestone-claim-${milestone.slug}`}
                        disabled={!milestone.can_claim || claiming === milestone.slug}
                        onClick={() => onClaim(milestone.slug)}
                        className={`text-[11px] tracking-widest font-bold px-3 py-1 rounded-sm transition-colors ${
                            milestone.can_claim
                                ? "bg-amber text-background hover:bg-amber/90"
                                : "bg-border text-muted-foreground cursor-not-allowed"
                        }`}
                    >
                        {claiming === milestone.slug
                            ? "..."
                            : milestone.completed
                              ? t("contracts.claim", "RECLAMA")
                              : t("contracts.in_progress", "IN CORSO")}
                    </button>
                )}
            </div>
        </li>
    );
}

function fmtResetDate(iso, _t) {
    if (!iso) return "—";
    try {
        const d = new Date(iso);
        return d.toLocaleString(undefined, {
            year: "numeric", month: "2-digit", day: "2-digit",
            hour: "2-digit", minute: "2-digit",
        });
    } catch {
        return iso;
    }
}

export default function Contracts() {
    const { t } = useT();
    const { refreshGuild } = useAuth();
    const [tab, setTab] = useState("daily");
    const [daily, setDaily] = useState(null);
    const [weekly, setWeekly] = useState(null);
    const [milestones, setMilestones] = useState(null);
    const [loading, setLoading] = useState(true);
    const [claiming, setClaiming] = useState(null);

    const refresh = useCallback(async () => {
        setLoading(true);
        try {
            const [d, w, m] = await Promise.all([
                api.get("/contracts/daily"),
                api.get("/contracts/weekly"),
                api.get("/contracts/milestones"),
            ]);
            setDaily(d.data);
            setWeekly(w.data);
            setMilestones(m.data);
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        refresh();
    }, [refresh]);

    const locked = daily?.locked === true;

    async function doClaim(scope, slug) {
        setClaiming(slug);
        try {
            const r = await api.post(`/contracts/${scope}/${slug}/claim`);
            const reward = r.data?.reward || {};
            toast.success(
                `${t("contracts.claim_success", "Reclamato")}: +${reward.gold || 0}G` +
                    (reward.reputation
                        ? ` · +${reward.reputation} ${t("contracts.reputation_short", "Rep")}`
                        : ""),
            );
            await Promise.all([refresh(), refreshGuild()]);
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setClaiming(null);
        }
    }

    const dailyContracts = daily?.contracts || [];
    const weeklyContracts = weekly?.contracts || [];
    const milestoneList = milestones?.milestones || [];

    return (
        <div className="min-h-screen bg-background text-foreground">
            <AppHeader />
            <main className="max-w-6xl mx-auto px-4 py-8 space-y-6">
                <header className="space-y-2">
                    <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
                        {t("contracts.page_title", "Bacheca Contratti")}
                    </h1>
                    <p className="text-sm text-muted-foreground max-w-3xl leading-relaxed">
                        {t(
                            "contracts.page_intro",
                            "Completa contratti giornalieri e settimanali per oro, materiali e reputazione. I milestone permanenti danno ricompense più rare a chi gioca con costanza.",
                        )}
                    </p>
                </header>

                {locked ? (
                    <div
                        data-testid="contracts-locked-banner"
                        className="border border-amber/40 bg-amber/5 rounded-sm p-6"
                    >
                        <div className="text-amber tracking-widest text-xs mb-2">
                            🔒 {t("contracts.locked_title", "BACHECA CONTRATTI NON SBLOCCATA")}
                        </div>
                        <p className="text-sm mb-4">
                            {t(
                                "contracts.locked_desc",
                                "Sblocca la Bacheca Contratti dal Territorio (richiede Guild Hall Lv2 + Bacheca Spedizioni Lv1).",
                            )}
                        </p>
                        <Link
                            to="/territory"
                            data-testid="contracts-locked-go-territory"
                            className="inline-block bg-amber text-background text-xs tracking-widest font-bold px-3 py-2 rounded-sm hover:bg-amber/90"
                        >
                            {t("contracts.go_territory", "VAI AL TERRITORIO")}
                        </Link>
                    </div>
                ) : (
                    <>
                        {/* Tabs */}
                        <nav className="flex gap-1 border-b border-border">
                            {TABS.map((tDef) => (
                                <button
                                    key={tDef.key}
                                    type="button"
                                    data-testid={tDef.testid}
                                    onClick={() => setTab(tDef.key)}
                                    className={`px-4 py-2 text-xs tracking-widest transition-colors ${
                                        tab === tDef.key
                                            ? "border-b-2 border-amber text-amber font-bold"
                                            : "text-muted-foreground hover:text-foreground"
                                    }`}
                                >
                                    {t(`contracts.tab.${tDef.key}`, tDef.key.toUpperCase())}
                                </button>
                            ))}
                        </nav>

                        {/* Tab content */}
                        {loading ? (
                            <div className="text-xs text-muted-foreground">
                                {t("common.loading", "Caricamento…")}
                            </div>
                        ) : tab === "daily" ? (
                            <section>
                                <div className="text-[10px] text-muted-foreground mb-2 tracking-widest">
                                    {t("contracts.next_daily_reset", "Reset")}: {fmtResetDate(daily?.next_reset_at, t)}
                                </div>
                                {dailyContracts.length === 0 ? (
                                    <div className="text-xs text-muted-foreground">
                                        {t("contracts.no_daily", "Nessun contratto giornaliero attivo.")}
                                    </div>
                                ) : (
                                    <ul className="space-y-3" data-testid="contracts-daily-list">
                                        {dailyContracts.map((c) => (
                                            <ContractRow
                                                key={c.slug} contract={c} scope="daily"
                                                onClaim={(s) => doClaim("daily", s)}
                                                claiming={claiming} t={t}
                                            />
                                        ))}
                                    </ul>
                                )}
                            </section>
                        ) : tab === "weekly" ? (
                            <section>
                                <div className="text-[10px] text-muted-foreground mb-2 tracking-widest">
                                    {t("contracts.next_weekly_reset", "Reset")}: {fmtResetDate(weekly?.next_reset_at, t)}
                                </div>
                                {weeklyContracts.length === 0 ? (
                                    <div className="text-xs text-muted-foreground">
                                        {t("contracts.no_weekly", "Nessun contratto settimanale attivo.")}
                                    </div>
                                ) : (
                                    <ul className="space-y-3" data-testid="contracts-weekly-list">
                                        {weeklyContracts.map((c) => (
                                            <ContractRow
                                                key={c.slug} contract={c} scope="weekly"
                                                onClaim={(s) => doClaim("weekly", s)}
                                                claiming={claiming} t={t}
                                            />
                                        ))}
                                    </ul>
                                )}
                            </section>
                        ) : (
                            <section>
                                <div className="text-[10px] text-muted-foreground mb-2 tracking-widest">
                                    {t("contracts.milestones_intro",
                                        "I milestone sono permanenti — completali per sbloccare il tier successivo.")}
                                </div>
                                {milestoneList.length === 0 ? (
                                    <div className="text-xs text-muted-foreground">
                                        {t("contracts.no_milestones", "Nessuna milestone disponibile.")}
                                    </div>
                                ) : (
                                    <ul className="space-y-3" data-testid="contracts-milestones-list">
                                        {milestoneList.map((m) => (
                                            <MilestoneRow
                                                key={m.slug} milestone={m}
                                                onClaim={(s) => doClaim("milestones", s)}
                                                claiming={claiming} t={t}
                                            />
                                        ))}
                                    </ul>
                                )}
                            </section>
                        )}
                    </>
                )}
            </main>
        </div>
    );
}
