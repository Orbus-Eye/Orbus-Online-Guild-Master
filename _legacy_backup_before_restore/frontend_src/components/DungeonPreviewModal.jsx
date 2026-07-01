// ROUND 16.1 Phase 2 — Pre-launch narrated dungeon preview modal.
// Reads from GET /api/dungeons/{slug}/preview?team_ids=...
// Bilingual IT + EN. Dark theme. Mobile-friendly.

import { useEffect, useState } from "react";
import { api, formatApiError } from "../lib/api";
import { useT } from "../i18n/I18nContext";
import { toast } from "sonner";

const RISK_LABEL = {
    low:    { it: "BASSO",  en: "LOW",    cls: "text-[#22c55e] border-[#22c55e]/55" },
    medium: { it: "MEDIO",  en: "MEDIUM", cls: "text-amber border-amber/55" },
    high:   { it: "ALTO",   en: "HIGH",   cls: "text-destructive border-destructive/55" },
};

export default function DungeonPreviewModal({
    open,
    slug,
    teamIds,
    onClose,
    onConfirm,
    confirming = false,
}) {
    const { lang } = useT();
    const it = lang === "it";
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState(null);

    useEffect(() => {
        if (!open || !slug) return;
        let cancelled = false;
        setLoading(true);
        setErr(null);
        const q = (teamIds && teamIds.length) ? `?team_ids=${teamIds.join(",")}` : "";
        api.get(`/dungeons/${slug}/preview${q}`)
            .then(({ data }) => {
                if (cancelled) return;
                if (data?.error === "not_found") {
                    setErr(it ? "Dungeon non trovato." : "Dungeon not found.");
                } else {
                    setData(data);
                }
            })
            .catch((e) => {
                if (cancelled) return;
                setErr(formatApiError(e));
                toast.error(formatApiError(e));
            })
            .finally(() => { if (!cancelled) setLoading(false); });
        return () => { cancelled = true; };
    }, [open, slug, teamIds, it]);

    if (!open) return null;

    const dName = it ? data?.dungeon?.name_it : data?.dungeon?.name_en;
    const risk = data?.injury_risk ? RISK_LABEL[data.injury_risk] : null;
    const weakness = it
        ? data?.weakness_suggestion_it
        : data?.weakness_suggestion_en;

    return (
        <div
            data-testid="dungeon-preview-modal"
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-3 sm:p-6"
            onClick={onClose}
        >
            <div
                className="bg-card border border-border rounded-sm max-w-2xl w-full max-h-[90vh] overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="sticky top-0 z-10 flex items-center justify-between gap-3 px-5 py-3 bg-card border-b border-border">
                    <div>
                        <div className="text-[10px] text-amber tracking-widest mb-0.5">
                            {it ? ":: ANTEPRIMA NARRATA" : ":: NARRATED PREVIEW"}
                        </div>
                        <h2 className="text-lg font-semibold tracking-tight" data-testid="dungeon-preview-title">
                            {dName || (it ? "Caricamento…" : "Loading…")}
                        </h2>
                    </div>
                    <button
                        type="button"
                        data-testid="dungeon-preview-close"
                        onClick={onClose}
                        className="text-muted-foreground hover:text-foreground text-xl leading-none px-2"
                        aria-label={it ? "Chiudi" : "Close"}
                    >×</button>
                </div>

                <div className="px-5 py-4 text-sm">
                    {loading && (
                        <div className="text-xs text-muted-foreground" data-testid="dungeon-preview-loading">
                            {it ? "Caricamento anteprima…" : "Loading preview…"}
                            <span className="caret-blink" />
                        </div>
                    )}

                    {err && (
                        <div className="text-xs text-destructive border border-destructive/50 rounded-sm p-3">
                            {err}
                        </div>
                    )}

                    {!loading && !err && data && (
                        <>
                            {/* Top stats grid */}
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
                                <Stat
                                    label={it ? "POTERE" : "POWER"}
                                    value={data.team_power}
                                    testid="dungeon-preview-team-power"
                                />
                                <Stat
                                    label={it ? "POT. CONSIGLIATO" : "REC. POWER"}
                                    value={data.dungeon?.recommended_power ?? "—"}
                                    testid="dungeon-preview-rec-power"
                                />
                                <Stat
                                    label={it ? "PROB. SUCCESSO" : "SUCCESS CHANCE"}
                                    value={`${data.success_chance}%`}
                                    testid="dungeon-preview-success"
                                    accent
                                />
                                <Stat
                                    label={it ? "RISCHIO FERITE" : "INJURY RISK"}
                                    value={
                                        risk ? (
                                            <span className={`text-[11px] tracking-widest border px-2 py-0.5 rounded-sm ${risk.cls}`}>
                                                {it ? risk.it : risk.en}
                                            </span>
                                        ) : "—"
                                    }
                                    testid="dungeon-preview-risk"
                                />
                            </div>

                            {/* Threats matrix */}
                            <section className="mb-4">
                                <div className="text-[10px] text-muted-foreground tracking-widest mb-2">
                                    {it ? ":: MINACCE E CONTROMISURE" : ":: THREATS & COUNTERS"}
                                </div>
                                <div className="border border-border rounded-sm p-3 bg-background/40">
                                    {(data.threats || []).length === 0 ? (
                                        <p className="text-xs text-muted-foreground italic" data-testid="dungeon-preview-no-threats">
                                            {it
                                                ? "Questo dungeon non ha minacce con contromisure specifiche."
                                                : "This dungeon has no specific threat counters."}
                                        </p>
                                    ) : (
                                        <div className="flex flex-wrap gap-2">
                                            {data.threats.map((t) => {
                                                const name = it ? t.name_it : t.name_en;
                                                const ok = t.countered;
                                                const tooltip = ok && t.by?.length
                                                    ? (it
                                                        ? `Contrastata da: ${t.by.map((b) => b.name).join(", ")}`
                                                        : `Countered by: ${t.by.map((b) => b.name).join(", ")}`)
                                                    : (it ? "Non contrastata" : "Not countered");
                                                return (
                                                    <span
                                                        key={t.slug}
                                                        data-testid={`dungeon-preview-threat-${t.slug}`}
                                                        title={tooltip}
                                                        className={`text-[11px] tracking-wide border px-2 py-1 rounded-sm cursor-help ${
                                                            ok
                                                                ? "border-[#22c55e]/55 text-[#22c55e]"
                                                                : "border-amber/55 text-amber"
                                                        }`}
                                                    >
                                                        {name} {ok ? "✓" : "⚠"}
                                                    </span>
                                                );
                                            })}
                                        </div>
                                    )}
                                </div>
                            </section>

                            {/* Weakness suggestion */}
                            {weakness && (
                                <section className="mb-4">
                                    <div className="text-[10px] text-muted-foreground tracking-widest mb-2">
                                        {it ? ":: SUGGERIMENTO" : ":: SUGGESTION"}
                                    </div>
                                    <div
                                        data-testid="dungeon-preview-weakness"
                                        className="text-xs text-amber border-l-2 border-amber pl-3 py-2 bg-amber/5 italic"
                                    >
                                        {weakness}
                                    </div>
                                </section>
                            )}

                            {/* Rewards preview */}
                            <section className="mb-4">
                                <div className="text-[10px] text-muted-foreground tracking-widest mb-2">
                                    {it ? ":: RICOMPENSE STIMATE" : ":: ESTIMATED REWARDS"}
                                </div>
                                <div className="grid grid-cols-2 gap-2 text-xs">
                                    <div className="border border-border rounded-sm p-2 flex justify-between">
                                        <span className="text-muted-foreground">{it ? "Oro" : "Gold"}</span>
                                        <span className="text-amber font-medium" data-testid="dungeon-preview-gold">
                                            {data.rewards_preview?.gold_range?.[0]}–{data.rewards_preview?.gold_range?.[1]}g
                                        </span>
                                    </div>
                                    <div className="border border-border rounded-sm p-2 flex justify-between">
                                        <span className="text-muted-foreground">XP</span>
                                        <span className="font-medium" data-testid="dungeon-preview-xp">
                                            {data.rewards_preview?.xp_range?.[0]}–{data.rewards_preview?.xp_range?.[1]}
                                        </span>
                                    </div>
                                </div>
                                {data.caps_info && (
                                    <p className="text-[10px] text-muted-foreground mt-2 italic">
                                        {it
                                            ? `Cap bonus successo: +${data.caps_info.success_bonus_cap_pct}% · Riduzione ferite: -${data.caps_info.injury_reduction_cap_pct}%. Solo dungeon Vuoto/Non-morti.`
                                            : `Success bonus cap: +${data.caps_info.success_bonus_cap_pct}% · Injury reduction: -${data.caps_info.injury_reduction_cap_pct}%. Void/Undead only.`}
                                    </p>
                                )}
                            </section>
                        </>
                    )}
                </div>

                {/* Footer actions */}
                <div className="sticky bottom-0 flex items-center justify-end gap-2 px-5 py-3 border-t border-border bg-card">
                    <button
                        type="button"
                        data-testid="dungeon-preview-cancel"
                        onClick={onClose}
                        disabled={confirming}
                        className="px-3 py-2 text-[11px] tracking-widest border border-border text-muted-foreground hover:text-foreground rounded-sm"
                    >
                        {it ? "ANNULLA" : "CANCEL"}
                    </button>
                    {onConfirm && (
                        <button
                            type="button"
                            data-testid="dungeon-preview-confirm"
                            onClick={onConfirm}
                            disabled={confirming || loading || !!err}
                            className="px-4 py-2 text-[11px] tracking-widest font-bold bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm disabled:opacity-50"
                        >
                            {confirming
                                ? (it ? "INVIO…" : "DISPATCHING…")
                                : (it ? "CONFERMA SPEDIZIONE" : "CONFIRM EXPEDITION")}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

function Stat({ label, value, testid, accent }) {
    return (
        <div className="border border-border bg-background/40 rounded-sm p-2">
            <div className="text-[10px] text-muted-foreground tracking-widest mb-1">{label}</div>
            <div
                data-testid={testid}
                className={`text-sm font-semibold ${accent ? "text-amber" : ""}`}
            >
                {value}
            </div>
        </div>
    );
}
