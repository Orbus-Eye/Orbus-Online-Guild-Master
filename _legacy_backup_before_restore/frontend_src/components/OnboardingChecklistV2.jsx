// ROUND 16.1 Phase 1 — 8-step onboarding checklist (R16.1 redesign).
// Fetches GET /api/dashboard/onboarding which derives completion state
// from live DB counters. Bilingual labels. Auto-hides when all steps
// are done OR the guild has dismissed it explicitly.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useT } from "../i18n/I18nContext";
import { Check } from "lucide-react";

export default function OnboardingChecklistV2() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [dismissing, setDismissing] = useState(false);
    const { lang } = useT();
    const it = lang === "it";

    const load = async () => {
        setLoading(true);
        try {
            const r = await api.get("/dashboard/onboarding");
            setData(r.data);
        } catch {
            setData(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { load(); }, []);

    if (loading || !data) return null;
    // ROUND 16.1 Phase 4 — honour the new `dismissed_implicit` flag so
    // mature guilds (level ≥3 OR ≥3 completed expeditions) never see the
    // onboarding card again, even if a single derived step never flipped.
    if (data.all_completed || data.dismissed || data.dismissed_implicit) return null;

    const headerTitle = it ? "INIZIA BENE" : "GET STARTED";
    const progressLabel = it ? "completati" : "completed";

    const handleDismiss = async () => {
        setDismissing(true);
        try {
            await api.post("/dashboard/onboarding/dismiss", {});
            setData((d) => d && { ...d, dismissed: true });
        } catch {
            // silent; reload may reflect server state
        } finally {
            setDismissing(false);
        }
    };

    return (
        <section
            className="border border-border bg-card rounded-sm p-4"
            data-testid="onboarding-checklist"
        >
            <header className="flex items-center justify-between gap-3 mb-3">
                <div>
                    <div className="text-[10px] text-muted-foreground tracking-widest">
                        {headerTitle}
                    </div>
                    <div className="text-[11px] text-amber/80 mt-1">
                        {data.completed_count}/{data.total_count} {progressLabel}
                    </div>
                </div>
                <button
                    type="button"
                    data-testid="onboarding-dismiss"
                    disabled={dismissing}
                    onClick={handleDismiss}
                    className="text-[10px] text-muted-foreground hover:text-foreground tracking-widest underline-offset-2 hover:underline"
                >
                    {it ? "Nascondi" : "Hide"}
                </button>
            </header>

            <ul className="space-y-1.5">
                {data.steps.map((s) => {
                    const title = it ? s.title_it : s.title_en;
                    const cta = it ? s.cta_it : s.cta_en;
                    if (s.completed) {
                        return (
                            <li
                                key={s.id}
                                data-testid={`onboarding-step-${s.id}`}
                                className="flex items-center justify-between gap-3 border border-border/60 rounded-sm px-3 py-2 bg-secondary/30"
                            >
                                <span className="flex items-center gap-2 min-w-0">
                                    <Check size={14} className="text-emerald-400/90 shrink-0" />
                                    <span className="text-sm text-muted-foreground line-through truncate">
                                        {title}
                                    </span>
                                </span>
                                <span className="text-[10px] tracking-widest text-emerald-400/80">
                                    ✓
                                </span>
                            </li>
                        );
                    }
                    return (
                        <li
                            key={s.id}
                            data-testid={`onboarding-step-${s.id}`}
                        >
                            <Link
                                to={s.link}
                                className="flex items-center justify-between gap-3 border border-border/60 rounded-sm px-3 py-2 hover:bg-secondary/50 transition-colors"
                            >
                                <span className="flex items-center gap-2 min-w-0">
                                    <span
                                        aria-hidden="true"
                                        className="w-3.5 h-3.5 rounded-sm border border-border shrink-0"
                                    />
                                    <span className="text-sm text-foreground truncate">
                                        {title}
                                    </span>
                                </span>
                                <span className="text-[10px] tracking-widest text-amber/85 shrink-0">
                                    {cta} →
                                </span>
                            </Link>
                        </li>
                    );
                })}
            </ul>
        </section>
    );
}
