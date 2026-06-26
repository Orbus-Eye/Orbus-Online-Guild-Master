// Phase 18.1 — Raid Builder (4 party × 5).
// Layout: 4 party columns + roster pool. Pick-to-assign + remove buttons.
// No DnD library: click-to-assign keeps the bundle small. Submit blocked
// until 20 unique advs assigned. Backend dup-cross-party is enforced by
// compound unique index on `raid_participants (raid_id, adventurer_id)`.
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";

import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";
import { useT } from "../i18n/I18nContext";


const PARTY_COUNT = 4;
const PARTY_SIZE = 5;


export default function RaidBuilder() {
    const { t, lang } = useT();
    const { slug } = useParams();
    const navigate = useNavigate();
    const [raidDungeon, setRaidDungeon] = useState(null);
    const [advs, setAdvs] = useState([]);
    const [parties, setParties] = useState(
        () => Array.from({ length: PARTY_COUNT }, () => Array(PARTY_SIZE).fill(null)),
    );
    const [preview, setPreview] = useState(null);
    const [busy, setBusy] = useState(false);

    async function load() {
        try {
            const [cat, advR] = await Promise.all([
                api.get("/raids/catalog"),
                api.get("/adventurers"),
            ]);
            const rd = cat.data.raid_dungeons.find((r) => r.slug === slug);
            if (!rd) {
                toast.error("Raid non trovato");
                navigate("/raids");
                return;
            }
            setRaidDungeon(rd);
            setAdvs(advR.data.adventurers || []);
        } catch (err) {
            toast.error(formatApiError(err));
        }
    }
    useEffect(() => { load(); }, [slug]);

    const assignedIds = useMemo(() => {
        const s = new Set();
        for (const p of parties) for (const id of p) if (id) s.add(id);
        return s;
    }, [parties]);

    const totalAssigned = assignedIds.size;
    const available = useMemo(
        () => advs.filter((a) => a.is_available && !assignedIds.has(a.id)),
        [advs, assignedIds],
    );

    function nextEmptySlot(partyIdx) {
        return parties[partyIdx].findIndex((x) => x === null);
    }

    function assignAdv(advId, targetPartyIdx) {
        if (assignedIds.has(advId)) return;
        const partyIdx = targetPartyIdx ?? parties.findIndex((p) => p.includes(null));
        if (partyIdx < 0 || partyIdx >= PARTY_COUNT) return;
        const slotIdx = nextEmptySlot(partyIdx);
        if (slotIdx < 0) return;
        const next = parties.map((p) => [...p]);
        next[partyIdx][slotIdx] = advId;
        setParties(next);
        setPreview(null);
    }

    function removeAdv(advId) {
        const next = parties.map((p) => p.map((x) => (x === advId ? null : x)));
        setParties(next);
        setPreview(null);
    }

    function advName(id) {
        const a = advs.find((x) => x.id === id);
        if (!a) return "?";
        return `${a.name} L${a.level} (${a.class_role || "?"})`;
    }

    function payload() {
        return {
            raid_slug: slug,
            parties: parties.map((advs5, i) => ({
                party_idx: i + 1,
                adventurer_ids: advs5,
            })),
        };
    }

    async function doPreview() {
        if (totalAssigned < PARTY_COUNT * PARTY_SIZE) {
            toast.error(t("raids.builder.not_enough", { have: totalAssigned }));
            return;
        }
        setBusy(true);
        try {
            const r = await api.post("/raids/preview", payload());
            setPreview(r.data);
            toast.success(t("raids.builder.preview_done"));
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setBusy(false);
        }
    }

    async function doLaunch() {
        if (!preview) return;
        setBusy(true);
        try {
            const r = await api.post("/raids/start", payload());
            toast.success(t("raids.builder.launched"));
            navigate(`/raids/${r.data.raid.id}/report`);
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setBusy(false);
        }
    }

    if (!raidDungeon) {
        return (
            <div className="min-h-screen bg-background text-foreground">
                <AppHeader />
                <main className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
                    <div className="text-xs text-muted-foreground">…</div>
                </main>
            </div>
        );
    }

    const focusHints = raidDungeon.party_focus_hints || [];
    const raidName = lang === "it"
        ? t(`raids.catalog.${slug}.name`)
        : (raidDungeon.name || t(`raids.catalog.${slug}.name`));

    return (
        <div className="min-h-screen bg-background text-foreground">
            <AppHeader />
            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-6" data-testid="raid-builder-page">
                <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
                    <h1 className="text-xs tracking-[0.3em] text-amber">
                        :: {t("raids.builder.title")} — {raidName}
                    </h1>
                    <Link to="/raids" className="text-[11px] text-muted-foreground hover:underline" data-testid="builder-back-link">
                        {t("raids.builder.back_to_raids")}
                    </Link>
                </div>

                {/* 4 party columns */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
                    {parties.map((slots, idx) => {
                        const focus = focusHints[idx] || {};
                        const focusLabel = lang === "it" ? focus.label_it : focus.label_en;
                        return (
                            <div
                                key={idx}
                                data-testid={`raid-party-${idx + 1}`}
                                className="border border-border bg-card rounded-sm p-3"
                            >
                                <div className="text-[11px] tracking-widest text-amber mb-1">
                                    {t("raids.builder.party_label", { n: idx + 1 })}
                                </div>
                                {focusLabel && (
                                    <div className="text-[10px] text-muted-foreground italic mb-2">
                                        {focusLabel} {focus.preferred_role ? `(${focus.preferred_role})` : ""}
                                    </div>
                                )}
                                <ul className="space-y-1">
                                    {slots.map((advId, slotIdx) => (
                                        <li
                                            key={slotIdx}
                                            data-testid={`party-${idx + 1}-slot-${slotIdx + 1}`}
                                            className={`text-[11px] border ${advId ? "border-border" : "border-dashed border-border/40"} rounded-sm px-2 py-1.5 flex items-center justify-between gap-1`}
                                        >
                                            <span className="truncate">{advId ? advName(advId) : "—"}</span>
                                            {advId && (
                                                <button
                                                    onClick={() => removeAdv(advId)}
                                                    data-testid={`remove-${advId}`}
                                                    className="text-[10px] text-muted-foreground hover:text-destructive"
                                                >
                                                    ✕
                                                </button>
                                            )}
                                        </li>
                                    ))}
                                </ul>
                                {preview && (
                                    <div className="mt-2 text-[10px] text-muted-foreground" data-testid={`party-${idx + 1}-preview`}>
                                        pwr {preview.party_powers?.[idx] ?? "?"} · {preview.success_chance_per_party?.[idx] ?? "?"}%
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>

                {/* Roster pool */}
                <section className="border border-border bg-card rounded-sm mb-4" data-testid="raid-roster-pool">
                    <div className="px-4 py-2 border-b border-border/60 bg-secondary/30 text-xs tracking-widest text-amber flex items-center justify-between flex-wrap">
                        <span>:: {t("raids.builder.available_advs")} ({available.length})</span>
                        <span className="text-[10px] text-muted-foreground">
                            {totalAssigned}/{PARTY_COUNT * PARTY_SIZE}
                        </span>
                    </div>
                    <div className="p-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-1.5">
                        {available.length === 0 && (
                            <div className="text-[11px] text-muted-foreground italic">—</div>
                        )}
                        {available.map((a) => {
                            const fullPartyIdx = parties.findIndex((p) => p.includes(null));
                            return (
                                <button
                                    key={a.id}
                                    data-testid={`adv-pick-${a.id}`}
                                    onClick={() => assignAdv(a.id)}
                                    disabled={fullPartyIdx < 0}
                                    className="text-[11px] border border-border/60 rounded-sm px-2 py-1.5 text-left hover:bg-secondary/30 disabled:opacity-40 disabled:cursor-not-allowed"
                                >
                                    <div className="truncate">{a.name} L{a.level}</div>
                                    <div className="text-[10px] text-muted-foreground">
                                        {a.class_role || "?"} · pwr {a.total_power}
                                    </div>
                                </button>
                            );
                        })}
                    </div>
                </section>

                {/* Summary */}
                {preview && (
                    <section className="border border-amber/40 bg-amber/5 rounded-sm p-3 mb-4" data-testid="raid-builder-summary">
                        <div className="text-[11px]"><strong>{t("raids.builder.summary_power")}:</strong> {preview.team_power_combined} / rec {preview.recommended_power_combined}</div>
                        <div className="text-[11px]"><strong>{t("raids.builder.summary_success")}:</strong> {preview.success_chance_combined}%</div>
                        <div className="text-[10px] text-muted-foreground">
                            {t("raids.builder.summary_per_party")}: {(preview.success_chance_per_party || []).map((c) => `${c}%`).join(" · ")}
                        </div>
                    </section>
                )}

                <div className="flex flex-wrap gap-2">
                    <button
                        onClick={doPreview}
                        disabled={busy || totalAssigned < PARTY_COUNT * PARTY_SIZE}
                        data-testid="builder-preview-btn"
                        className="text-xs tracking-widest border border-border bg-secondary/50 hover:bg-secondary px-4 py-2 rounded-sm disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                        ⌖ {t("raids.builder.preview_btn")}
                    </button>
                    <button
                        onClick={doLaunch}
                        disabled={busy || !preview}
                        data-testid="builder-launch-btn"
                        className="text-xs tracking-widest border border-amber/60 text-amber bg-amber/10 hover:bg-amber/20 px-4 py-2 rounded-sm disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                        ▶ {t("raids.builder.launch_btn")}
                    </button>
                    <div className="text-[10px] text-muted-foreground self-center">
                        {totalAssigned < PARTY_COUNT * PARTY_SIZE
                            ? t("raids.builder.not_enough", { have: totalAssigned })
                            : ""}
                    </div>
                </div>
            </main>
        </div>
    );
}
