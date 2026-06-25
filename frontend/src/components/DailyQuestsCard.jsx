// Phase 14 — Daily Quests card. Terminal-style, polled on mount.
import { useEffect, useState, useCallback } from "react";
import { api, formatApiError } from "../lib/api";
import { useT } from "../i18n/I18nContext";
import { toast } from "sonner";


function formatCountdown(targetIso) {
    const target = new Date(targetIso).getTime();
    const now = Date.now();
    const diff = Math.max(0, target - now);
    const h = Math.floor(diff / 3_600_000);
    const m = Math.floor((diff % 3_600_000) / 60_000);
    return `${h}h ${m}m`;
}


export default function DailyQuestsCard() {
    const { t } = useT();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [claiming, setClaiming] = useState(null);

    const load = useCallback(async () => {
        try {
            const { data: res } = await api.get("/quests/today");
            setData(res);
            setError(null);
        } catch (err) {
            setError(formatApiError(err));
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        load();
    }, [load]);

    const onClaim = async (qid) => {
        setClaiming(qid);
        try {
            const { data: res } = await api.post(`/quests/claim/${qid}`);
            toast.success(t("quests.claim_success", { gold: res.reward_gold_granted }));
            await load();
        } catch (err) {
            const msg = formatApiError(err);
            toast.error(msg);
        } finally {
            setClaiming(null);
        }
    };

    if (loading) {
        return (
            <div
                data-testid="daily-quests-card-loading"
                className="border border-border/60 bg-card/40 rounded-sm p-4 font-mono text-[11px] text-muted-foreground"
            >
                :: {t("quests.loading")}
            </div>
        );
    }

    if (error || !data) {
        return (
            <div
                data-testid="daily-quests-card-error"
                className="border border-border/60 bg-card/40 rounded-sm p-4 font-mono text-[11px] text-red-400/80"
            >
                :: {t("quests.unavailable")}
            </div>
        );
    }

    return (
        <div
            data-testid="daily-quests-card"
            className="border border-border/60 bg-card/40 rounded-sm p-4 font-mono text-[12px]"
        >
            <div className="flex items-baseline justify-between mb-3 gap-2">
                <div className="text-amber tracking-widest text-[11px]">
                    :: {t("quests.title")}
                </div>
                <div className="text-muted-foreground text-[10px]">
                    {t("quests.reset_in", { time: formatCountdown(data.next_reset_at) })}
                </div>
            </div>
            <div className="space-y-2">
                {data.quests.map((q) => (
                    <QuestRow
                        key={q.id}
                        quest={q}
                        t={t}
                        claiming={claiming === q.id}
                        onClaim={() => onClaim(q.id)}
                    />
                ))}
            </div>
        </div>
    );
}


function QuestRow({ quest, t, claiming, onClaim }) {
    const title = t(`quests.${quest.id}.title`);
    const progressLine = `${quest.progress}/${quest.threshold}`;
    const canClaim = quest.can_claim && !claiming;
    let buttonLabel;
    let buttonState;
    if (quest.claimed) {
        buttonLabel = t("quests.claimed");
        buttonState = "claimed";
    } else if (canClaim) {
        buttonLabel = t("quests.claim");
        buttonState = "ready";
    } else {
        buttonLabel = t("quests.locked");
        buttonState = "locked";
    }
    return (
        <div
            data-testid={`daily-quest-row-${quest.id}`}
            className="flex items-center justify-between gap-3 border-l-2 border-border/40 pl-3"
        >
            <div className="flex-1 min-w-0">
                <div className="text-foreground/90 truncate">{title}</div>
                <div className="text-muted-foreground text-[10px]">
                    {progressLine} · +{quest.reward_gold} {t("quests.reward_gold")}
                </div>
            </div>
            <button
                type="button"
                disabled={!canClaim}
                onClick={onClaim}
                data-testid={`daily-quest-claim-${quest.id}`}
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
    );
}
