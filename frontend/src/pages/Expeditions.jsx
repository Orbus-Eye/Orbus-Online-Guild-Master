import { useEffect, useState, useCallback, useRef } from "react";
import { Link } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import { toast } from "sonner";
import AppHeader from "../components/AppHeader";
import OverCapBanner from "../components/OverCapBanner";
import { useT } from "../i18n/I18nContext";
import { Button } from "../components/ui/button";
import { useAuth } from "../context/AuthContext";

const StatusBadge = ({ status, summary }) => {
    if (status === "in_progress") {
        return (
            <span
                data-testid="exp-status-in-progress"
                className="inline-block text-[10px] tracking-widest border border-amber/55 text-amber px-1.5 py-0.5 rounded-sm"
            >
                IN PROGRESS
            </span>
        );
    }
    const _isSuccess = (summary || status) === "Success" || status === "completed";
    if (status === "completed" && summary === "Success") {
        return (
            <span
                data-testid="exp-status-success"
                className="inline-block text-[10px] tracking-widest border border-[#22c55e]/55 text-[#22c55e] px-1.5 py-0.5 rounded-sm"
            >
                SUCCESS
            </span>
        );
    }
    if (status === "completed" && summary === "Failed") {
        return (
            <span
                data-testid="exp-status-failed"
                className="inline-block text-[10px] tracking-widest border border-[#ef4444]/55 text-[#ef4444] px-1.5 py-0.5 rounded-sm"
            >
                FAILED
            </span>
        );
    }
    return (
        <span className="inline-block text-[10px] tracking-widest border border-border text-muted-foreground px-1.5 py-0.5 rounded-sm">
            {status?.toUpperCase()}
        </span>
    );
};

const formatRemaining = (s) => {
    if (s == null) return "—";
    if (s <= 0) return "completing…";
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return m > 0 ? `${m}m ${sec}s` : `${sec}s`;
};

import { formatDateTime as formatDate } from "../utils/dateFormat";
import { translateDungeonName } from "../i18n/contentMap";

export default function Expeditions() {
    const { t, tContent, lang } = useT();
    const [exps, setExps] = useState(null);
    const [loading, setLoading] = useState(true);
    const { refreshGuild } = useAuth();
    const tickRef = useRef(null);
    const pollRef = useRef(null);

    const fetchAll = useCallback(async () => {
        try {
            const { data } = await api.get("/expeditions");
            setExps(data.expeditions);
        } catch (err) {
            toast.error(formatApiError(err));
            setExps([]);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchAll();
    }, [fetchAll]);

    // Local countdown ticker (decrements seconds_remaining each second client-side)
    useEffect(() => {
        if (tickRef.current) clearInterval(tickRef.current);
        tickRef.current = setInterval(() => {
            setExps((prev) => {
                if (!prev) return prev;
                return prev.map((e) =>
                    e.status === "in_progress" && typeof e.seconds_remaining === "number"
                        ? { ...e, seconds_remaining: Math.max(0, e.seconds_remaining - 1) }
                        : e,
                );
            });
        }, 1000);
        return () => clearInterval(tickRef.current);
    }, []);

    // Poll backend every 10s while there are active expeditions (triggers lazy completion)
    useEffect(() => {
        if (pollRef.current) clearInterval(pollRef.current);
        const hasActive = exps?.some((e) => e.status === "in_progress");
        if (!hasActive) return;
        pollRef.current = setInterval(async () => {
            await fetchAll();
            await refreshGuild();
        }, 10000);
        return () => clearInterval(pollRef.current);
    }, [exps, fetchAll, refreshGuild]);

    const active = exps?.filter((e) => e.status === "in_progress") ?? [];
    const completed = exps?.filter((e) => e.status !== "in_progress") ?? [];

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg">
            <AppHeader subtitleKey="nav.expeditions" />

            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
                <OverCapBanner source="expeditions" />
                <div className="flex items-end justify-between gap-3 mb-6 flex-wrap">
                    <div>
                        <div className="text-xs text-amber tracking-widest mb-2">
                            :: EXPEDITION LOG
                        </div>
                        <h1 className="text-3xl font-semibold tracking-tight">{t("expeditions.title")}</h1>
                        <p className="text-sm text-muted-foreground mt-2 max-w-2xl">
                            Active runs and historical reports.
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Link to="/dungeons">
                            <Button
                                variant="outline"
                                className="h-10 rounded-sm bg-transparent border-border hover:bg-secondary text-xs"
                                data-testid="goto-dungeons-btn"
                            >
                                + New Expedition
                            </Button>
                        </Link>
                        <Button
                            data-testid="btn-refresh-expeditions"
                            onClick={async () => {
                                await fetchAll();
                                await refreshGuild();
                            }}
                            variant="outline"
                            className="h-10 rounded-sm bg-transparent border-border hover:bg-secondary text-xs"
                        >
                            ↻ Refresh
                        </Button>
                    </div>
                </div>

                {loading && (
                    <div className="text-xs text-muted-foreground">loading<span className="caret-blink" /></div>
                )}

                {!loading && exps && exps.length === 0 && (
                    <div className="border border-border bg-card rounded-sm p-8 text-center" data-testid="expeditions-empty">
                        <div className="text-amber text-xs tracking-widest mb-2">
                            :: NO EXPEDITIONS YET
                        </div>
                        <p className="text-sm text-muted-foreground mb-4">
                            Visit the Dungeons board and dispatch your first party.
                        </p>
                        <Link to="/dungeons">
                            <Button className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm">
                                Go to Dungeons →
                            </Button>
                        </Link>
                    </div>
                )}

                {!loading && active.length > 0 && (
                    <section className="mb-8">
                        <div className="text-[10px] text-muted-foreground tracking-widest mb-3">
                            :: ACTIVE ({active.length})
                        </div>
                        <div className="space-y-2">
                            {active.map((e) => (
                                <Link
                                    to={`/expeditions/${e.id}`}
                                    key={e.id}
                                    data-testid={`expedition-row-${e.id}`}
                                    className="block border border-border bg-card rounded-sm p-4 hover:bg-secondary/30"
                                >
                                    <div className="flex items-center justify-between gap-3 flex-wrap">
                                        <div className="min-w-0">
                                            <div className="font-medium">{translateDungeonName(tContent, e.dungeon_name, lang)}</div>
                                            <div className="text-[11px] text-muted-foreground mt-0.5">
                                                {t("expeditions.started_at", { at: formatDate(e.started_at, lang) })}
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-3">
                                            <StatusBadge status={e.status} />
                                            <span
                                                data-testid={`countdown-${e.id}`}
                                                className="text-sm text-amber font-medium font-mono"
                                            >
                                                {formatRemaining(e.seconds_remaining)}
                                            </span>
                                        </div>
                                    </div>
                                </Link>
                            ))}
                        </div>
                    </section>
                )}

                {!loading && completed.length > 0 && (
                    <section>
                        <div className="text-[10px] text-muted-foreground tracking-widest mb-3">
                            :: COMPLETED ({completed.length})
                        </div>
                        <div className="border border-border rounded-sm overflow-x-auto">
                            <table data-testid="completed-table" className="w-full text-sm min-w-[600px]">
                                <thead className="bg-secondary/40 text-[10px] text-muted-foreground tracking-widest">
                                    <tr>
                                        <th className="text-left px-3 py-2 font-normal border-b border-border">DUNGEON</th>
                                        <th className="text-left px-3 py-2 font-normal border-b border-border">RESULT</th>
                                        <th className="text-left px-3 py-2 font-normal border-b border-border">GOLD</th>
                                        <th className="text-left px-3 py-2 font-normal border-b border-border">COMPLETED</th>
                                        <th className="text-right px-3 py-2 font-normal border-b border-border" />
                                    </tr>
                                </thead>
                                <tbody>
                                    {completed.map((e) => (
                                        <tr
                                            key={e.id}
                                            data-testid={`expedition-row-${e.id}`}
                                            className="border-b border-border/60 hover:bg-secondary/20"
                                        >
                                            <td className="px-3 py-2 font-medium whitespace-nowrap">
                                                {translateDungeonName(tContent, e.dungeon_name, lang)}
                                            </td>
                                            <td className="px-3 py-2 whitespace-nowrap">
                                                <StatusBadge status={e.status} summary={e.result_summary} />
                                            </td>
                                            <td className="px-3 py-2 text-amber whitespace-nowrap">
                                                {e.gold_reward}g
                                            </td>
                                            <td className="px-3 py-2 text-muted-foreground whitespace-nowrap">
                                                {formatDate(e.completed_at, lang)}
                                            </td>
                                            <td className="px-3 py-2 text-right whitespace-nowrap">
                                                <Link
                                                    to={`/expeditions/${e.id}`}
                                                    className="text-amber hover:underline text-xs"
                                                    data-testid={`view-report-${e.id}`}
                                                >
                                                    view report →
                                                </Link>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </section>
                )}
            </main>
        </div>
    );
}
