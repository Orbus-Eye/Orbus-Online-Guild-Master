import { useEffect, useMemo, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import { useT } from "../i18n/I18nContext";
import { toast } from "sonner";
import AppHeader from "../components/AppHeader";
import { Button } from "../components/ui/button";
import { useAuth } from "../context/AuthContext";

const RARITY_COLOR = {
    Common: "#9ca3af",
    Uncommon: "#22c55e",
    Rare: "#3b82f6",
    Epic: "#a855f7",
};

const RarityBadge = ({ rarity }) => (
    <span
        className="inline-block text-[10px] tracking-widest border px-1.5 py-0.5 rounded-sm"
        style={{
            color: RARITY_COLOR[rarity] || RARITY_COLOR.Common,
            borderColor: (RARITY_COLOR[rarity] || RARITY_COLOR.Common) + "55",
        }}
    >
        {rarity?.toUpperCase()}
    </span>
);

// Client-side preview matching backend formula (must be kept in sync — but backend is authoritative)
// Phase 6: uses `total_power` (base + equipment) as authoritative per-member contribution when present.
function previewTeamPower(team) {
    let total = 0;
    const roles = new Set();
    for (const a of team) {
        if (typeof a.total_power === "number") {
            total += a.total_power;
        } else {
            total +=
                a.strength + a.agility + a.intellect + a.endurance + a.faith + a.level * 2;
        }
        if (a.class_role) roles.add(a.class_role);
    }
    if (roles.has("Tank")) total += 5;
    if (roles.has("Healer")) total += 5;
    if (roles.has("DPS")) total += 5;
    if (roles.has("Tank") && roles.has("Healer") && roles.has("DPS")) total += 10;
    return total;
}

function previewSuccessChance(teamPower, recommended) {
    return Math.max(10, Math.min(95, 50 + (teamPower - recommended)));
}

export default function ExpeditionNew() {
    const { t, tContent } = useT();
    const { slug } = useParams();
    const navigate = useNavigate();
    const { refreshGuild } = useAuth();
    const [dungeon, setDungeon] = useState(null);
    const [advs, setAdvs] = useState([]);
    const [selected, setSelected] = useState([]);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        (async () => {
            try {
                const [du, ad] = await Promise.all([
                    api.get("/dungeons"),
                    api.get("/adventurers"),
                ]);
                const d = du.data.dungeons.find((x) => x.slug === slug);
                if (!d) {
                    toast.error(t("expedition_new.toast_dungeon_not_found"));
                    navigate("/dungeons", { replace: true });
                    return;
                }
                setDungeon(d);
                setAdvs(ad.data.adventurers.filter((a) => a.is_available));
            } catch (err) {
                toast.error(formatApiError(err));
            } finally {
                setLoading(false);
            }
        })();
    }, [slug, navigate, t]);

    const requiredSize = dungeon?.required_team_size ?? 3;

    const toggleSelect = (adv) => {
        setSelected((prev) => {
            if (prev.find((p) => p.id === adv.id)) {
                return prev.filter((p) => p.id !== adv.id);
            }
            if (prev.length >= requiredSize) {
                toast.message(`You can only select ${requiredSize} heroes.`);
                return prev;
            }
            return [...prev, adv];
        });
    };

    const teamPower = useMemo(() => previewTeamPower(selected), [selected]);
    const equipmentBonus = useMemo(
        () => selected.reduce((s, a) => s + (a.equipment_power || 0), 0),
        [selected],
    );
    const successChance = useMemo(
        () => (dungeon ? previewSuccessChance(teamPower, dungeon.recommended_power) : 0),
        [teamPower, dungeon],
    );
    const underpowered = useMemo(
        () => Boolean(dungeon && selected.length === requiredSize && teamPower < dungeon.recommended_power),
        [dungeon, selected.length, requiredSize, teamPower],
    );

    const composition = useMemo(() => {
        const c = { Tank: 0, DPS: 0, Healer: 0 };
        for (const a of selected) if (c[a.class_role] !== undefined) c[a.class_role]++;
        return c;
    }, [selected]);

    const submit = async () => {
        if (!dungeon || selected.length !== requiredSize) return;
        setSubmitting(true);
        try {
            const { data } = await api.post("/expeditions", {
                dungeon_id: dungeon.id,
                adventurer_ids: selected.map((a) => a.id),
            });
            toast.success(t("expedition_new.toast_dispatched", { seconds: dungeon.base_duration_seconds }));
            await refreshGuild();
            navigate(`/expeditions/${data.expedition.id}`, { replace: true });
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-background">
                <AppHeader subtitleKey="expedition_new.brand_subtitle" />
                <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8 text-xs text-muted-foreground">
                    loading<span className="caret-blink" />
                </main>
            </div>
        );
    }

    if (!dungeon) return null;

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg">
            <AppHeader subtitleKey="expedition_new.brand_subtitle" />

            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
                <Link to="/dungeons" className="text-xs text-muted-foreground hover:text-foreground" data-testid="back-to-dungeons">
                    {t("expedition_new.back_to_dungeons")}
                </Link>
                <div className="text-xs text-amber tracking-widest mt-4 mb-2">
                    {t("expedition_new.section_dispatch_party")}
                </div>
                <h1 className="text-3xl font-semibold tracking-tight">
                    {tContent("dungeon", dungeon.slug, "name", dungeon.name)}
                </h1>
                <p className="text-sm text-muted-foreground mt-2 max-w-2xl">
                    {t("expedition_new.subtitle_select", { n: requiredSize })}
                </p>

                <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6 mt-8">
                    {/* Roster */}
                    <section>
                        <div className="text-[10px] text-muted-foreground tracking-widest mb-3">
                            :: AVAILABLE ROSTER ({advs.length})
                        </div>
                        {advs.length === 0 && (
                            <div
                                data-testid="no-available-adventurers"
                                className="border border-border bg-card rounded-sm p-6 text-sm text-muted-foreground"
                            >
                                No available adventurers. Recruit more or wait for active
                                expeditions to return.
                            </div>
                        )}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            {advs.map((a) => {
                                const isSelected = !!selected.find((s) => s.id === a.id);
                                return (
                                    <button
                                        type="button"
                                        key={a.id}
                                        onClick={() => toggleSelect(a)}
                                        data-testid={`select-adventurer-${a.id}`}
                                        className={`text-left border rounded-sm p-4 transition-colors ${
                                            isSelected
                                                ? "border-amber bg-amber/5"
                                                : "border-border bg-card hover:bg-secondary/40"
                                        }`}
                                    >
                                        <div className="flex items-start justify-between mb-2 gap-2">
                                            <div className="min-w-0">
                                                <div className="font-medium truncate">
                                                    {a.name}
                                                </div>
                                                <div className="text-[11px] text-muted-foreground mt-0.5">
                                                    {a.class_name} · {a.class_role} · lvl {a.level}
                                                </div>
                                            </div>
                                            <div className="flex flex-col items-end gap-1">
                                                <RarityBadge rarity={a.rarity} />
                                                {isSelected && (
                                                    <span className="text-[10px] text-amber">
                                                        ✓ SELECTED
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-5 gap-1 text-[11px] text-muted-foreground">
                                            <span>STR {a.strength}</span>
                                            <span>AGI {a.agility}</span>
                                            <span>INT {a.intellect}</span>
                                            <span>END {a.endurance}</span>
                                            <span>FAI {a.faith}</span>
                                        </div>
                                    </button>
                                );
                            })}
                        </div>
                    </section>

                    {/* Preview side-panel */}
                    <aside className="lg:sticky lg:top-20 self-start">
                        <div className="border border-border bg-card rounded-sm p-5">
                            <div className="text-[10px] text-amber tracking-widest mb-2">
                                {t("expedition_new.section_briefing")}
                            </div>
                            <div className="text-sm font-medium mb-3">{tContent("dungeon", dungeon.slug, "name", dungeon.name)}</div>
                            <div className="text-[11px] text-muted-foreground mb-4">
                                {t("expedition_new.dungeon_meta", {
                                    difficulty: dungeon.difficulty,
                                    seconds: dungeon.base_duration_seconds,
                                    power: dungeon.recommended_power,
                                })}
                            </div>

                            <div className="border-t border-border pt-3 mt-3 space-y-1.5 text-xs">
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">{t("expedition_new.selected")}</span>
                                    <span data-testid="selected-count" className="font-medium">
                                        {selected.length}/{requiredSize}
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">TANK</span>
                                    <span>{composition.Tank}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">DPS</span>
                                    <span>{composition.DPS}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">HEALER</span>
                                    <span>{composition.Healer}</span>
                                </div>
                                <div className="flex justify-between pt-2 border-t border-border/60">
                                    <span className="text-muted-foreground">{t("expedition_new.equipment_bonus_label")}</span>
                                    <span
                                        data-testid="preview-equipment-bonus"
                                        className="text-amber font-semibold"
                                    >
                                        +{equipmentBonus}
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">{t("expedition_new.team_power_final_label")}</span>
                                    <span
                                        data-testid="preview-team-power"
                                        className="text-[#22c55e] font-semibold"
                                    >
                                        {teamPower}
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">{t("expedition_new.success_chance_label")}</span>
                                    <span
                                        data-testid="preview-success-chance"
                                        className={
                                            "font-semibold " +
                                            (selected.length === requiredSize
                                                ? successChance > 75
                                                    ? "text-[#22c55e]"
                                                    : successChance >= 40
                                                      ? "text-amber"
                                                      : "text-destructive"
                                                : "text-muted-foreground")
                                        }
                                    >
                                        {selected.length === requiredSize ? `${successChance}%` : "—"}
                                    </span>
                                </div>
                            </div>

                            {underpowered && (
                                <div
                                    data-testid="underpowered-warning"
                                    className="text-[11px] text-amber border border-amber/40 bg-amber/10 px-3 py-2 rounded-sm mt-3"
                                >
                                    {t("expedition_new.underpowered_warning", { recommended: dungeon.recommended_power, actual: teamPower })}
                                </div>
                            )}

                            <Button
                                onClick={submit}
                                data-testid="btn-send-expedition"
                                disabled={selected.length !== requiredSize || submitting}
                                className="w-full h-10 rounded-sm mt-5 bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {submitting
                                    ? t("expedition_new.dispatching_btn")
                                    : `Send Expedition (${selected.length}/${requiredSize})`}
                            </Button>
                            <p className="text-[10px] text-muted-foreground mt-2 text-center">
                                Estimated values; backend recomputes on dispatch.
                            </p>
                        </div>
                    </aside>
                </div>
            </main>
        </div>
    );
}
