// ExpeditionExplainer — Phase 14.5 (ROUND 2 Fase 3).
//
// Render-only component. Consumes the `report_summary` + `report_steps`
// fields injected by GET /api/expeditions/{id}. Graceful fallback when
// the fields are null/empty (legacy or in-progress expedition).
import { useT } from "../i18n/I18nContext";

const RESULT_COLOR = {
    success: "#22c55e",
    partial: "#f59e0b",
    failure: "#ef4444",
    neutral: "#9ca3af",
};

const POLARITY_COLOR = {
    positive: "#22c55e",
    negative: "#ef4444",
    mixed: "#f59e0b",
};

const STEP_TYPE_GLYPH = {
    exploration: "◇",
    traps: "△",
    combat: "✕",
    boss: "★",
    loot: "◆",
    recovery: "↩",
    reward: "+",
};

function StepBadge({ resultKey, t }) {
    const color = RESULT_COLOR[resultKey] || RESULT_COLOR.neutral;
    return (
        <span
            className="inline-block text-[10px] tracking-widest border px-1.5 py-0.5 rounded-sm"
            style={{ color, borderColor: color + "55" }}
            data-testid={`step-result-${resultKey}`}
        >
            {t(`expedition_report_page.step_result_${resultKey}`).toUpperCase()}
        </span>
    );
}

function PolarityChip({ polarity, label, testid }) {
    const color = POLARITY_COLOR[polarity] || POLARITY_COLOR.mixed;
    return (
        <span
            data-testid={testid}
            className="inline-block text-[10px] border px-1.5 py-0.5 rounded-sm whitespace-nowrap"
            style={{ color, borderColor: color + "55" }}
        >
            {label}
        </span>
    );
}

function collectKeyModifiers(steps) {
    // Deduplicate trait `display_name` across all steps, preserving polarity.
    const out = new Map();
    for (const s of steps || []) {
        for (const tr of s.involved_traits || []) {
            if (!tr.display_name) continue;
            const key = tr.display_name.toLowerCase();
            if (!out.has(key)) out.set(key, tr);
        }
    }
    return [...out.values()];
}

function generateTips(summary, steps, members, t) {
    if (!summary) return [];
    const tips = [];
    if (
        summary.recommended_power > 0 &&
        summary.team_power < summary.recommended_power - 10 &&
        summary.outcome === "failure"
    ) {
        tips.push(t("expedition_report_page.tip_underpowered"));
    }
    const hasHealer = (members || []).some(
        (m) => (m.role_snapshot || "").toLowerCase() === "healer"
    );
    if (!hasHealer && (summary.injuries || 0) > 0) {
        tips.push(t("expedition_report_page.tip_no_healer"));
    }
    return tips;
}

export default function ExpeditionExplainer({ summary, steps, members }) {
    const { t } = useT();
    const hasReport = !!summary && Array.isArray(steps) && steps.length > 0;

    if (!hasReport) {
        return (
            <section
                className="mb-6"
                data-testid="report-explainer-fallback"
            >
                <div className="text-[10px] text-muted-foreground tracking-widest mb-2">
                    :: {t("expedition_report_page.what_happened").toUpperCase()}
                </div>
                <div className="border border-border bg-card rounded-sm p-4 text-xs text-muted-foreground italic">
                    {t("expedition_report_page.legacy_fallback")}
                </div>
            </section>
        );
    }

    const keyModifiers = collectKeyModifiers(steps);
    const tips = generateTips(summary, steps, members, t);

    return (
        <>
            {/* Rewards summary card */}
            <section className="mb-6" data-testid="report-rewards-card">
                <div className="text-[10px] text-muted-foreground tracking-widest mb-2">
                    :: {t("expedition_report_page.rewards_title").toUpperCase()}
                </div>
                <div className="border border-border bg-card rounded-sm p-4">
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                        <div className="flex flex-col">
                            <span className="text-[10px] text-muted-foreground tracking-widest">
                                {t("expedition_report_page.rewards_gold")}
                            </span>
                            <span className="text-lg font-semibold text-amber" data-testid="report-rw-gold">
                                {summary.gold_earned}g
                            </span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[10px] text-muted-foreground tracking-widest">
                                {t("expedition_report_page.rewards_xp")}
                            </span>
                            <span className="text-lg font-semibold" data-testid="report-rw-xp">
                                +{summary.xp_earned}
                            </span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[10px] text-muted-foreground tracking-widest">
                                {t("expedition_report_page.rewards_loot")}
                            </span>
                            <span className="text-lg font-semibold" data-testid="report-rw-loot">
                                {(summary.loot_found || []).length || (
                                    <span className="text-xs text-muted-foreground italic">
                                        {t("expedition_report_page.rewards_no_loot")}
                                    </span>
                                )}
                            </span>
                            {(summary.loot_found || []).length > 0 && (
                                <ul className="mt-1 text-[10px] text-muted-foreground space-y-0.5">
                                    {summary.loot_found.slice(0, 4).map((it, i) => {
                                        const nm = (lang === "en"
                                            ? it.display_name_en
                                            : it.display_name_it) || it.name;
                                        return (
                                            <li key={i} data-testid={`report-loot-item-${i}`}>
                                                · {nm} <span className="opacity-60">({it.rarity})</span>
                                            </li>
                                        );
                                    })}
                                    {summary.loot_found.length > 4 && (
                                        <li className="opacity-60">+{summary.loot_found.length - 4}</li>
                                    )}
                                </ul>
                            )}
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[10px] text-muted-foreground tracking-widest">
                                {t("expedition_report_page.rewards_injuries")} · {t("expedition_report_page.rewards_fatigue").toLowerCase()}
                            </span>
                            <span className="text-lg font-semibold" data-testid="report-rw-injuries">
                                {summary.injuries}/{summary.fatigue}
                            </span>
                        </div>
                    </div>
                    {summary.narrative_summary && (
                        <p
                            className="text-xs text-foreground/90 mt-3 pt-3 border-t border-border/40 italic"
                            data-testid="report-narrative-summary"
                        >
                            {summary.narrative_summary}
                        </p>
                    )}
                </div>
            </section>

            {/* What happened (steps) */}
            <section className="mb-6" data-testid="report-steps-section">
                <div className="text-[10px] text-muted-foreground tracking-widest mb-3">
                    :: {t("expedition_report_page.what_happened").toUpperCase()}
                </div>
                <ol className="space-y-2">
                    {steps.map((s, idx) => (
                        <li
                            key={`${s.type}-${idx}`}
                            data-testid={`report-step-${s.type}`}
                            className="border border-border bg-card rounded-sm p-3"
                        >
                            <div className="flex items-start justify-between gap-2 flex-wrap">
                                <div className="flex items-center gap-2 min-w-0">
                                    <span className="text-amber">
                                        {STEP_TYPE_GLYPH[s.type] || "·"}
                                    </span>
                                    <span className="font-medium text-sm">
                                        {s.label}
                                    </span>
                                </div>
                                <StepBadge resultKey={s.result} t={t} />
                            </div>
                            <p className="text-[12px] text-foreground/90 mt-1.5">
                                {s.description}
                            </p>

                            {(s.modifiers && s.modifiers.length > 0) && (
                                <ul
                                    className="mt-2 text-[11px] text-muted-foreground space-y-0.5"
                                    data-testid={`report-step-modifiers-${s.type}`}
                                >
                                    {s.modifiers.map((m, i) => (
                                        <li key={i} className="before:content-['»_'] before:text-amber/70">
                                            {m}
                                        </li>
                                    ))}
                                </ul>
                            )}

                            {(s.involved_classes && s.involved_classes.length > 0) && (
                                <div className="flex flex-wrap gap-1.5 mt-2">
                                    {s.involved_classes.map((c, i) => (
                                        <span
                                            key={`${c.display_name}-${i}`}
                                            data-testid={`report-step-class-${s.type}-${i}`}
                                            className="text-[10px] border border-border/60 px-1.5 py-0.5 rounded-sm text-muted-foreground"
                                        >
                                            {c.display_name} · {c.role}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </li>
                    ))}
                </ol>
            </section>

            {/* Key modifiers (compilation) */}
            <section className="mb-6" data-testid="report-key-modifiers">
                <div className="text-[10px] text-muted-foreground tracking-widest mb-2">
                    :: {t("expedition_report_page.modifiers_important").toUpperCase()}
                </div>
                {keyModifiers.length === 0 ? (
                    <div className="border border-border bg-card rounded-sm p-3 text-xs text-muted-foreground italic">
                        {t("expedition_report_page.no_modifiers")}
                    </div>
                ) : (
                    <div className="flex flex-wrap gap-2">
                        {keyModifiers.map((tr, i) => (
                            <PolarityChip
                                key={`${tr.display_name}-${i}`}
                                polarity={tr.polarity}
                                label={tr.display_name}
                                testid={`report-modifier-${i}`}
                            />
                        ))}
                    </div>
                )}
            </section>

            {/* Tips */}
            {tips.length > 0 && (
                <section className="mb-6" data-testid="report-tips">
                    <ul className="text-[12px] space-y-1.5">
                        {tips.map((tip, i) => (
                            <li
                                key={i}
                                className="border-l-2 border-amber/60 pl-3 py-1 text-foreground/90"
                                data-testid={`report-tip-${i}`}
                            >
                                {tip}
                            </li>
                        ))}
                    </ul>
                </section>
            )}
        </>
    );
}
