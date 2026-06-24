import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { api, formatApiError } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { useT } from "../i18n/I18nContext";

// 5 steps — content (label/body/cta) comes from i18n via `onboarding.stepN.*`.
const STEP_ROUTES = {
    1: "/recruitment",
    2: "/recruitment",
    3: "/dungeons",
    4: "/expeditions",
    5: "/inventory",
};

export default function OnboardingChecklist() {
    const { guild, refreshGuild } = useAuth();
    const { t } = useT();
    const navigate = useNavigate();
    const [busy, setBusy] = useState(false);

    if (!guild) return null;
    if (guild.onboarding_completed || guild.onboarding_dismissed) return null;

    const stored = guild.onboarding_step || 1;
    const suggested = guild.onboarding_suggested_step || stored;
    const activeStep = Math.max(stored, suggested);
    const route = STEP_ROUTES[activeStep] || "/recruitment";

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
        if (activeStep > stored) {
            await patch({ step: activeStep });
        }
        navigate(route);
    };

    const handleSkip = async () => {
        await patch({ dismissed: true });
        toast.success(t("onboarding.toast_skipped"));
    };

    const handleComplete = async () => {
        await patch({ completed: true });
        toast.success(t("onboarding.toast_completed"));
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
                        {t("onboarding.header", { step: activeStep })}
                    </div>
                    <div
                        className="text-sm sm:text-base font-semibold"
                        data-testid="onboarding-step-label"
                    >
                        {t(`onboarding.step${activeStep}.label`)}
                    </div>
                </div>
                <button
                    type="button"
                    onClick={handleSkip}
                    disabled={busy}
                    data-testid="onboarding-skip-btn"
                    className="text-[10px] text-muted-foreground tracking-widest hover:text-foreground transition-colors disabled:opacity-40"
                >
                    {t("onboarding.skip")}
                </button>
            </div>

            <p
                className="text-xs sm:text-sm text-muted-foreground mb-4"
                data-testid="onboarding-step-body"
            >
                {t(`onboarding.step${activeStep}.body`)}
            </p>

            <div className="flex items-center gap-1.5 mb-4" data-testid="onboarding-progress">
                {[1, 2, 3, 4, 5].map((n) => (
                    <span
                        key={n}
                        className={`h-1.5 flex-1 rounded-sm ${
                            n < activeStep
                                ? "bg-amber"
                                : n === activeStep
                                ? "bg-amber/60"
                                : "bg-border"
                        }`}
                        data-testid={`onboarding-dot-${n}`}
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
                    {t(`onboarding.step${activeStep}.cta`)}
                </button>
                {isFinalStep && (
                    <button
                        type="button"
                        onClick={handleComplete}
                        disabled={busy}
                        data-testid="onboarding-complete-btn"
                        className="text-xs text-muted-foreground hover:text-foreground transition-colors underline-offset-4 hover:underline disabled:opacity-40"
                    >
                        {t("onboarding.finish")}
                    </button>
                )}
            </div>
        </section>
    );
}
