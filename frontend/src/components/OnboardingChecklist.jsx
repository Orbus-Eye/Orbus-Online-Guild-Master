import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { api, formatApiError } from "../lib/api";
import { useAuth } from "../context/AuthContext";

const STEPS = [
    {
        n: 1,
        label: "Welcome to your guild",
        body: "You are the Guild Master. Recruit adventurers and dispatch them on expeditions.",
        cta: "Go to Recruitment",
        to: "/recruitment",
    },
    {
        n: 2,
        label: "Recruit 3 adventurers",
        body: "You need at least 3 adventurers to form an expedition team. 3 free refreshes per day, then 10/20/30 gold.",
        cta: "Open Recruitment",
        to: "/recruitment",
    },
    {
        n: 3,
        label: "Start your first expedition",
        body: "Goblin Warrens is your starting dungeon. Recommended power 45, 60s duration.",
        cta: "Browse Dungeons",
        to: "/dungeons",
    },
    {
        n: 4,
        label: "Read the expedition report",
        body: "Your first run completed. Check the report for XP, gold and loot.",
        cta: "View Expeditions",
        to: "/expeditions",
    },
    {
        n: 5,
        label: "Equip items or replay",
        body: "Equip loot to boost team power, or use Replay Last Run to grind the same dungeon.",
        cta: "Open Inventory",
        to: "/inventory",
    },
];

export default function OnboardingChecklist() {
    const { guild, refreshGuild } = useAuth();
    const navigate = useNavigate();
    const [busy, setBusy] = useState(false);

    if (!guild) return null;
    if (guild.onboarding_completed || guild.onboarding_dismissed) return null;

    const stored = guild.onboarding_step || 1;
    const suggested = guild.onboarding_suggested_step || stored;
    const activeStep = Math.max(stored, suggested);
    const current = STEPS.find((s) => s.n === activeStep) || STEPS[0];

    const patch = async (body) => {
        if (busy) return null;
        setBusy(true);
        try {
            const { data } = await api.patch("/guilds/onboarding", body);
            await refreshGuild();
            return data;
        } catch (err) {
            toast.error(formatApiError(err));
            return null;
        } finally {
            setBusy(false);
        }
    };

    const handleCta = async () => {
        // Advance stored step to the active one and navigate
        if (activeStep > stored) {
            await patch({ step: activeStep });
        }
        navigate(current.to);
    };

    const handleSkip = async () => {
        await patch({ dismissed: true });
        toast.success("Onboarding hidden. You can re-enable it from your profile (Phase later).");
    };

    const handleComplete = async () => {
        await patch({ completed: true });
        toast.success("Onboarding completed. Good luck, Guild Master.");
    };

    const isFinalStep = activeStep >= 5;

    return (
        <section
            className="mb-8 border border-amber/40 bg-card rounded-sm p-4 sm:p-5"
            data-testid="onboarding-checklist"
        >
            <div className="flex items-start justify-between gap-3 flex-wrap mb-3">
                <div>
                    <div className="text-[10px] text-amber tracking-widest mb-1">
                        :: ONBOARDING · STEP {activeStep} OF 5
                    </div>
                    <div
                        className="text-sm sm:text-base font-semibold"
                        data-testid="onboarding-step-label"
                    >
                        {current.label}
                    </div>
                </div>
                <button
                    type="button"
                    onClick={handleSkip}
                    disabled={busy}
                    data-testid="onboarding-skip-btn"
                    className="text-[10px] text-muted-foreground tracking-widest hover:text-foreground transition-colors disabled:opacity-40"
                >
                    SKIP TUTORIAL
                </button>
            </div>

            <p
                className="text-xs sm:text-sm text-muted-foreground mb-4"
                data-testid="onboarding-step-body"
            >
                {current.body}
            </p>

            {/* Progress dots */}
            <div className="flex items-center gap-1.5 mb-4" data-testid="onboarding-progress">
                {STEPS.map((s) => (
                    <span
                        key={s.n}
                        className={`h-1.5 flex-1 rounded-sm ${
                            s.n < activeStep
                                ? "bg-amber"
                                : s.n === activeStep
                                ? "bg-amber/60"
                                : "bg-border"
                        }`}
                        data-testid={`onboarding-dot-${s.n}`}
                    />
                ))}
            </div>

            <div className="flex items-center justify-between gap-3 flex-wrap">
                <button
                    type="button"
                    onClick={handleCta}
                    disabled={busy}
                    data-testid="onboarding-cta-btn"
                    className="inline-flex items-center gap-2 px-3 py-2 rounded-sm bg-amber text-amber-foreground hover:bg-amber/90 text-xs sm:text-sm font-semibold tracking-wide transition-colors disabled:opacity-50"
                >
                    {current.cta} →
                </button>
                {isFinalStep && (
                    <button
                        type="button"
                        onClick={handleComplete}
                        disabled={busy}
                        data-testid="onboarding-complete-btn"
                        className="text-xs text-muted-foreground hover:text-foreground transition-colors underline-offset-4 hover:underline disabled:opacity-40"
                    >
                        finish tutorial
                    </button>
                )}
            </div>
        </section>
    );
}
