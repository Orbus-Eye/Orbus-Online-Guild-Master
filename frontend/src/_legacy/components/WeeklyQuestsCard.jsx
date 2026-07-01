// Phase 14.1 — Weekly Quests Card.
// Optional weekly quests with progress bars + claim, rotating per ISO week.
import { useEffect, useState, useCallback, useImperativeHandle, forwardRef } from "react";
import { api, formatApiError } from "../lib/api";
import { useT } from "../i18n/I18nContext";
import { toast } from "sonner";


function formatResetCountdown(targetIso) {
    const target = new Date(targetIso).getTime();
    const now = Date.now();
    const diff = Math.max(0, target - now);
    const days = Math.floor(diff / 86_400_000);
    const hours = Math.floor((diff % 86_400_000) / 3_600_000);
    return `${days}d ${hours}h`;
}


const WeeklyQuestsCard = forwardRef(function WeeklyQuestsCard(_props, ref) {
    const { t } = useT();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [claiming, setClaiming] = useState(null);

    const load = useCallback(async () => {
        try {
            const { data: res } = await api.get("/quests/weekly");
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

    const onClaim = async (slug) => {
        setClaiming(slug);
        try {
            const { data: res } = await api.post(
                `/quests/weekly/claim/${slug}`
            );
            toast.success(
                t("weekly.claim_success", { gold: res.gold_granted })
            );
            await load();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setClaiming(null);
        }
    };

    if (loading) {
        return (
            <div
                data-testid="weekly-quests-card-loading"
                className="border border-border/60 bg-card/40 rounded-sm p-4 font-mono text-[11px] text-muted-foreground"
            >
                :: {t("weekly.loading")}
            </div>
        );
    }
    if (error || !data) {
        return (
            <div
                data-testid="weekly-quests-card-error"
                className="border border-border/60 bg-card/40 rounded-sm p-4 font-mono text-[11px] text-red-400/80"
            >
                :: {t("weekly.unavailable")}
            </div>
        );
    }

    return (
        <div
            data-testid="weekly-quests-card"
            className="border border-border/60 bg-card/40 rounded-sm p-4 font-mono text-[12px]"
        >
            <div className="flex items-baseline justify-between mb-3 gap-2">
                <div className="text-amber tracking-widest text-[11px]">
                    :: {t("weekly.title")}
                </div>
                <div className="text-muted-foreground text-[10px]">
                    {t("weekly.reset_in", {
                        time: formatResetCountdown(data.next_reset_at),
                    })}
                </div>
            </div>
            <div className="space-y-3">
                {(data.quests || []).map((q) => (
                    <WeeklyRow
                        key={q.slug}
                        quest={q}
                        t={t}
                        claiming={claiming === q.slug}
                        onClaim={() => onClaim(q.slug)}
                    />
                ))}
            </div>
        </div>
    );
});


function WeeklyRow({ quest, t, claiming, onClaim }) {
    const title = t(quest.display_key) || quest.slug;
    const progress = Number(quest.progress ?? 0);
    const target = Number(quest.objective_target ?? 1);
    const pct = Math.min(100, Math.round((progress / Math.max(1, target)) * 100));
    const canClaim = Boolean(quest.can_claim) && !claiming;
    let buttonLabel;
    let buttonState;
    if (quest.claimed) {
        buttonLabel = t("weekly.claimed");
        buttonState = "claimed";
    } else if (canClaim) {
        buttonLabel = t("weekly.claim");
        buttonState = "ready";
    } else {
        buttonLabel = t("weekly.locked");
        buttonState = "locked";
    }
    const mats = (quest.reward_materials || [])
        .map((m) => `${m.qty}×${m.slug}`)
        .join(", ");
    return (
        <div
            data-testid={`weekly-quest-row-${quest.slug}`}
            className="border-l-2 border-border/40 pl-3 flex flex-col gap-1"
        >
            <div className="flex items-center justify-between gap-3">
                <div className="flex-1 min-w-0">
                    <div
                        data-testid={`weekly-quest-title-${quest.slug}`}
                        className="text-foreground/90 truncate"
                    >
                        {title}
                    </div>
                    <div className="text-muted-foreground text-[10px]">
                        {progress}/{target} · +{quest.reward_gold}{" "}
                        {t("weekly.reward_gold")}
                        {mats ? ` · ${mats}` : ""}
                    </div>
                </div>
                <button
                    type="button"
                    disabled={!canClaim}
                    onClick={onClaim}
                    data-testid={`weekly-quest-claim-${quest.slug}`}
                    className={
                        "shrink-0 text-[10px] tracking-widest px-2 py-1 border rounded-sm " +
                        (buttonState === "ready"
                            ? "border-amber text-amber hover:bg-amber/10"
                            : buttonState === "claimed"
                              ? "border-[#22c55e]/40 text-[#22c55e]/70 cursor-default"
                              : "border-border/40 text-muted-foreground cursor-not-allowed")
                    }
                >
                    {buttonLabel}
                </button>
            </div>
            <div
                data-testid={`weekly-quest-progress-${quest.slug}`}
                className="h-1 bg-border/30 rounded-sm overflow-hidden"
            >
                <div
                    className={
                        "h-full transition-all " +
                        (quest.completed ? "bg-amber/80" : "bg-foreground/40")
                    }
                    style={{ width: `${pct}%` }}
                />
            </div>
        </div>
    );
}

export default WeeklyQuestsCard;
