// Phase 15 — Daily Streak Badge.
// Server-authoritative display. Polls /api/quests/streak on mount + on demand
// via the optional onClaimed callback (parent triggers reload).
import { useEffect, useState, useCallback, useImperativeHandle, forwardRef } from "react";
import { api, formatApiError } from "../lib/api";
import { useT } from "../i18n/I18nContext";
import { toast } from "sonner";


const StreakBadge = forwardRef(function StreakBadge(_props, ref) {
    const { t } = useT();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [claiming, setClaiming] = useState(false);

    const load = useCallback(async () => {
        try {
            const { data: res } = await api.get("/quests/streak");
            setData(res);
            setError(null);
        } catch (err) {
            setError(formatApiError(err));
        } finally {
            setLoading(false);
        }
    }, []);

    useImperativeHandle(ref, () => ({ reload: load }), [load]);

    useEffect(() => {
        load();
    }, [load]);

    const onClaim = async () => {
        if (!data?.current_tier || !data?.can_claim_reward) return;
        setClaiming(true);
        try {
            const { data: res } = await api.post(
                `/quests/streak/claim/${data.current_tier}`
            );
            toast.success(t("streak.claim_success", { gold: res.gold_granted }));
            await load();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setClaiming(false);
        }
    };

    if (loading) {
        return (
            <div
                data-testid="streak-badge-loading"
                className="border border-border/60 bg-card/40 rounded-sm p-3 font-mono text-[11px] text-muted-foreground"
            >
                :: {t("streak.loading")}
            </div>
        );
    }
    if (error || !data) {
        return (
            <div
                data-testid="streak-badge-error"
                className="border border-border/60 bg-card/40 rounded-sm p-3 font-mono text-[11px] text-red-400/80"
            >
                :: {t("streak.unavailable")}
            </div>
        );
    }

    const current = Number(data.current ?? 0);
    const longest = Number(data.longest ?? 0);
    const tier = data.current_tier;
    const reward = data.current_reward;
    const canClaim = Boolean(data.can_claim_reward) && !claiming;
    const todayDone = Boolean(data.today_completed);

    return (
        <div
            data-testid="streak-badge"
            className="border border-border/60 bg-card/40 rounded-sm p-3 font-mono text-[12px] flex flex-col gap-2"
        >
            <div className="flex items-baseline justify-between gap-2">
                <div className="text-amber tracking-widest text-[11px]">
                    :: {t("streak.title")}
                </div>
                <div
                    data-testid="streak-best"
                    className="text-muted-foreground text-[10px]"
                >
                    {t("streak.best", { n: longest })}
                </div>
            </div>
            <div className="flex items-center gap-3">
                <div
                    data-testid="streak-current"
                    className="text-2xl text-foreground font-semibold tracking-tight"
                >
                    {current}
                </div>
                <div className="text-muted-foreground text-[10px] leading-tight">
                    {todayDone
                        ? t("streak.today_done")
                        : t("streak.today_pending")}
                </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
                {[1, 3, 5, 7].map((d) => {
                    const reached = current > 0 &&
                        ((current - 1) % 7) + 1 >= d;
                    return (
                        <div
                            key={d}
                            data-testid={`streak-tier-${d}`}
                            className={
                                "text-[10px] px-2 py-0.5 border rounded-sm tracking-widest " +
                                (reached
                                    ? "border-amber text-amber"
                                    : "border-border/40 text-muted-foreground")
                            }
                        >
                            D{d}
                        </div>
                    );
                })}
            </div>
            {tier ? (
                <div className="flex items-center justify-between gap-2 pt-1 border-t border-border/30">
                    <div className="text-[10px] text-muted-foreground leading-tight">
                        {reward
                            ? t("streak.reward_for_tier", {
                                tier,
                                gold: reward.gold,
                                mats: (reward.materials || [])
                                    .map((m) => `${m.qty}×${m.slug}`)
                                    .join(", ") || t("streak.no_mats"),
                            })
                            : t("streak.no_reward")}
                    </div>
                    <button
                        type="button"
                        disabled={!canClaim}
                        onClick={onClaim}
                        data-testid="streak-claim-button"
                        className={
                            "shrink-0 text-[10px] tracking-widest px-2 py-1 border rounded-sm " +
                            (canClaim
                                ? "border-amber text-amber hover:bg-amber/10"
                                : "border-border/40 text-muted-foreground cursor-not-allowed")
                        }
                    >
                        {claiming
                            ? t("streak.claiming")
                            : canClaim
                              ? t("streak.claim")
                              : t("streak.locked")}
                    </button>
                </div>
            ) : null}
        </div>
    );
});

export default StreakBadge;
