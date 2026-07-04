import { useEffect, useMemo, useRef, useState } from "react";
import { useParams, useNavigate, useSearchParams, Link } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import { useT } from "../i18n/I18nContext";
import { toast } from "sonner";
import AppHeader from "../components/AppHeader";
import OverCapBanner from "../components/OverCapBanner";
import { Button } from "../components/ui/button";
import { useAuth } from "../context/AuthContext";
import {
    isAdventurerUnderLeveled,
    advMinLevelBadge,
    advDungeonTooltip,
} from "../utils/levelGate";
import { rarityLabel } from "../utils/displayLabels";
import DungeonPreviewModal from "../components/DungeonPreviewModal";

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
        {rarityLabel(rarity).toUpperCase()}
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
    const { t, tContent, lang } = useT();
    const { slug } = useParams();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const squadIdParam = searchParams.get("squad_id") || "";
    const autoLoadedRef = useRef(false);
    const { refreshGuild } = useAuth();
    const [dungeon, setDungeon] = useState(null);
    const [advs, setAdvs] = useState([]);
    const [selected, setSelected] = useState([]);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [preview, setPreview] = useState(null);
    const [previewLoading, setPreviewLoading] = useState(false);
    // ROUND 6A.2b — saved squads dropdown
    const [squads, setSquads] = useState([]);
    // ROUND 16.1 Phase 2 — narrated pre-launch preview modal.
    const [showNarratedPreview, setShowNarratedPreview] = useState(false);

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

    // ROUND 6A.2b — fetch saved squads of the matching size (dungeon_3/dungeon_5).
    useEffect(() => {
        if (!dungeon) return;
        const type = requiredSize === 3 ? "dungeon_3" : requiredSize === 5 ? "dungeon_5" : null;
        if (!type) return;
        api.get(`/squads?type=${type}`)
            .then(({ data }) => setSquads(data.squads || []))
            .catch(() => setSquads([]));
    }, [dungeon, requiredSize]);

    // Apply a saved squad → repopulate `selected` with the live adventurer
    // docs that still belong to the guild AND are currently available.
    // Missing/unavailable ones are toasted so the user can fill them manually.
    const loadSquad = (squadId) => {
        if (!squadId) return;
        const sq = squads.find((s) => s.squad_id === squadId);
        if (!sq) return;
        const byId = new Map(advs.map((a) => [a.id, a]));
        const next = [];
        const missing = [];
        for (const aid of sq.adventurer_ids) {
            const adv = byId.get(aid);
            if (adv) next.push(adv);
            else missing.push(aid);
        }
        setSelected(next.slice(0, requiredSize));
        if (missing.length > 0) {
            toast.warning(
                `${missing.length} avventuriere/i della squadra non sono disponibili (impegnati o rimossi). Completa manualmente.`
            );
        } else {
            toast.success(`Squadra "${sq.name}" caricata`);
        }
    };

    // ROUND 6A.2c — auto-load squad from ?squad_id once dungeon + squads + advs are ready.
    // RATIONALE (ROUND 6B FASE B): `loadSquad` is intentionally NOT in the
    // dep list. The `autoLoadedRef` guard makes this effect strictly
    // one-shot per mount: adding `loadSquad` (which is recreated every
    // render) would not change behavior but would clutter the deps. The
    // listed deps (squadIdParam/dungeon/squads/advs) are the SEMANTIC
    // triggers — we wait until the data needed to resolve the squad is
    // present, then fire exactly once.
    useEffect(() => {
        if (!squadIdParam || autoLoadedRef.current) return;
        if (!dungeon || squads.length === 0 || advs.length === 0) return;
        const sq = squads.find((s) => s.squad_id === squadIdParam);
        if (!sq) {
            autoLoadedRef.current = true;
            toast.error("Squadra non trovata o non compatibile con questo dungeon");
            return;
        }
        autoLoadedRef.current = true;
        loadSquad(squadIdParam);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [squadIdParam, dungeon, squads, advs]);

    const minAdvLevel = dungeon?.min_adventurer_level ?? 1;

    // ROUND 17.3 Step 2 E — Class-fit / role-balanced team selection.
    // Estende R17.1b P1.4: oltre a `?auto=strongest` (pure-power) supporta
    // `?auto=classfit` che considera class-fit primary/secondary stat +
    // role balance (Tank/Healer/DPS). NO hidden boost, NO reward tweak —
    // solo UX pre-selection.
    //
    // Role mapping (14 classi da `adventurer_classes` catalog):
    //   Tank    → warrior, paladin
    //   Healer  → priest, druid
    //   Support → bard
    //   DPS     → berserker, mage, necromancer, warlock, alchemist,
    //             assassin, ranger, rogue, monk
    //
    // Ideal role mix (parametrico su team_size):
    //   3-player: [Tank, Healer, DPS]  (fallback: any DPS)
    //   5-player: [Tank, Healer, DPS, DPS, DPS]
    //   Others:  Tank + Healer + rest DPS
    const ROLE_TANK = new Set(["warrior", "paladin"]);
    const ROLE_HEALER = new Set(["priest", "druid"]);
    const ROLE_SUPPORT = new Set(["bard"]);
    const classToRole = (adv) => {
        const slug = (adv?.class_slug || adv?.class_name || "").toLowerCase();
        if (ROLE_TANK.has(slug)) return "Tank";
        if (ROLE_HEALER.has(slug)) return "Healer";
        if (ROLE_SUPPORT.has(slug)) return "Support";
        return "DPS";
    };
    const idealRoleMix = (size) => {
        if (size <= 0) return [];
        if (size === 1) return ["DPS"];
        if (size === 2) return ["Tank", "Healer"];
        // 3+: 1 Tank, 1 Healer, rest DPS.
        const mix = ["Tank", "Healer"];
        for (let i = 2; i < size; i++) mix.push("DPS");
        return mix;
    };

    // ROUND 17.1b P1.4 (existing) + R17.3 Step 2 E (new classfit).
    useEffect(() => {
        const autoParam = searchParams.get("auto");
        if (!autoParam || autoLoadedRef.current) return;
        if (!dungeon || advs.length === 0) return;
        const size = dungeon?.required_team_size || 3;

        // Filter available + level-compatible (shared by both modes).
        const pool = advs
            .filter((a) => a.is_available !== false)
            .filter((a) => !isAdventurerUnderLeveled(a, minAdvLevel));

        if (pool.length === 0) {
            autoLoadedRef.current = true;
            toast.error(
                "Non hai ancora una squadra adatta. Recluta o migliora altri avventurieri prima di riprovare.",
                { duration: 5000 }
            );
            return;
        }

        // Mode 1: strongest (pure-power, R17.1b fallback CTA).
        if (autoParam === "strongest") {
            const eligible = pool
                .slice()
                .sort((x, y) => (Number(y.power_score) || 0) - (Number(x.power_score) || 0))
                .slice(0, size);
            if (eligible.length > 0) {
                autoLoadedRef.current = true;
                setSelected(eligible);
                toast.success(
                    `Squadra suggerita: i ${eligible.length} avventurieri con il potere più alto.`,
                    { duration: 4000 }
                );
            }
            return;
        }

        // Mode 2: classfit (R17.3 Step 2 E — role-balanced).
        if (autoParam === "classfit") {
            if (pool.length < size) {
                // Fallback: not enough available → pure-power on what we have.
                autoLoadedRef.current = true;
                const fallback = pool
                    .slice()
                    .sort((x, y) => (Number(y.power_score) || 0) - (Number(x.power_score) || 0))
                    .slice(0, size);
                setSelected(fallback);
                toast.info(
                    "Non abbastanza avventurieri disponibili per un team bilanciato. Selezione pura per potere.",
                    { duration: 5000 }
                );
                return;
            }
            const roles = idealRoleMix(size);
            const team = [];
            const remaining = pool.slice();
            const nameList = [];
            for (const target of roles) {
                let candidates = remaining.filter((a) => classToRole(a) === target);
                if (candidates.length === 0) candidates = remaining.slice();
                candidates.sort(
                    (x, y) => (Number(y.power_score) || 0) - (Number(x.power_score) || 0)
                );
                const pick = candidates[0];
                if (!pick) break;
                team.push(pick);
                nameList.push(pick.name || pick.class_name || pick.id);
                const idx = remaining.findIndex((r) => r.id === pick.id);
                if (idx >= 0) remaining.splice(idx, 1);
            }
            if (team.length === size) {
                autoLoadedRef.current = true;
                setSelected(team);
                toast.success(
                    `Squadra suggerita: ${nameList.join(", ")}.`,
                    {
                        description:
                            "Scelti perché hanno il livello richiesto e il potere migliore per questa spedizione. Composizione bilanciata (Tank / Healer / DPS).",
                        duration: 6000,
                    }
                );
            } else {
                autoLoadedRef.current = true;
                toast.info(
                    "Non hai ancora una squadra bilanciata. Selezione parziale per potere.",
                    { duration: 5000 }
                );
                setSelected(team);
            }
            return;
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [searchParams, dungeon, advs, minAdvLevel]);

    const toggleSelect = (adv) => {
        // Round 11.3 — UI gate: block under-leveled adventurers client-side.
        // Backend remains authoritative; this is purely UX.
        if (isAdventurerUnderLeveled(adv, minAdvLevel)) {
            toast.error(advDungeonTooltip(minAdvLevel));
            return;
        }
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

    // Round 11.3 — at least one selected member is below the dungeon min level.
    const hasUnderLeveledSelected = useMemo(
        () => selected.some((a) => isAdventurerUnderLeveled(a, minAdvLevel)),
        [selected, minAdvLevel],
    );

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

    // Phase 14.3-c — backend-authoritative preview (success chance, injury risk,
    // expected reward, modifiers). Fired only when the team is complete.
    useEffect(() => {
        if (!dungeon || selected.length !== requiredSize) {
            setPreview(null);
            return;
        }
        const ids = selected.map((a) => a.id);
        let cancelled = false;
        setPreviewLoading(true);
        api.post("/expeditions/preview", {
            dungeon_id: dungeon.id,
            adventurer_ids: ids,
        })
            .then(({ data }) => {
                if (!cancelled) setPreview(data);
            })
            .catch(() => {
                if (!cancelled) setPreview(null);
            })
            .finally(() => {
                if (!cancelled) setPreviewLoading(false);
            });
        return () => {
            cancelled = true;
        };
    }, [dungeon, selected, requiredSize]);

    const submit = async () => {
        if (!dungeon || selected.length !== requiredSize) return;
        setSubmitting(true);
        try {
            const { data } = await api.post("/expeditions", {
                dungeon_id: dungeon.id,
                adventurer_ids: selected.map((a) => a.id),
            });
            toast.success(t("expedition_new.toast_dispatched", { seconds: dungeon.base_duration_seconds }));

            // ROUND 17.1b P1.1 — milestone toast primo start (idempotente per guild).
            if (data?.milestones?.is_first_expedition_started) {
                const guildId = data.expedition?.guild_id;
                const key = `orbus.milestone.first_expedition_started.${guildId}`;
                if (guildId && !localStorage.getItem(key)) {
                    toast.success(
                        "Prima spedizione avviata! Il tuo team è in missione.",
                        { duration: 5000, id: `milestone-first-start-${guildId}` }
                    );
                    try { localStorage.setItem(key, new Date().toISOString()); } catch { /* noop */ }
                }
            }

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
                <OverCapBanner source="expedition-new" />
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
                        {/* ROUND 6A.2b — saved squad loader */}
                        <div className="mb-4 border border-neutral-800 rounded-sm p-3 bg-secondary/30">
                            <div className="text-[10px] text-muted-foreground tracking-widest mb-2">
                                :: CARICA SQUADRA SALVATA ({squads.length})
                            </div>
                            {squads.length === 0 ? (
                                <div className="flex items-center justify-between gap-3 flex-wrap">
                                    <p className="text-[11px] text-muted-foreground italic">
                                        Nessuna squadra {requiredSize}p salvata.
                                    </p>
                                    <Link
                                        to={`/squads/new?type=${requiredSize === 3 ? "dungeon_3" : "dungeon_5"}`}
                                        data-testid="exp-create-squad-link"
                                        className="text-[11px] tracking-widest border border-amber/60 text-amber px-3 py-1 hover:bg-amber hover:text-background transition-colors"
                                    >
                                        + Crea squadra ora
                                    </Link>
                                </div>
                            ) : (
                                <div className="flex items-center gap-2 flex-wrap">
                                    <select
                                        onChange={(e) => loadSquad(e.target.value)}
                                        defaultValue=""
                                        data-testid="expedition-load-squad"
                                        className="bg-secondary border border-neutral-700 px-3 py-1.5 text-xs focus:border-amber outline-none flex-1 min-w-[200px]"
                                    >
                                        <option value="">— Seleziona squadra —</option>
                                        {squads.map((s) => (
                                            <option key={s.squad_id} value={s.squad_id}>
                                                {s.name} (PWR {s.total_power}{s.missing_adventurer_ids?.length ? ` · ⚠ ${s.missing_adventurer_ids.length} mancanti` : ""})
                                            </option>
                                        ))}
                                    </select>
                                    <Link
                                        to="/squads"
                                        className="text-[10px] tracking-widest text-muted-foreground hover:text-foreground"
                                    >
                                        Gestisci →
                                    </Link>
                                </div>
                            )}
                        </div>
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
                                const underLeveled = isAdventurerUnderLeveled(a, minAdvLevel);
                                return (
                                    <button
                                        type="button"
                                        key={a.id}
                                        onClick={() => toggleSelect(a)}
                                        disabled={underLeveled}
                                        title={underLeveled ? advDungeonTooltip(minAdvLevel) : ""}
                                        data-testid={`select-adventurer-${a.id}`}
                                        data-underleveled={underLeveled ? "1" : "0"}
                                        className={`text-left border rounded-sm p-4 transition-colors ${
                                            isSelected
                                                ? "border-amber bg-amber/5"
                                                : "border-border bg-card hover:bg-secondary/40"
                                        } ${underLeveled ? "opacity-40 cursor-not-allowed hover:bg-card" : ""}`}
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
                                                {underLeveled && (
                                                    <span
                                                        data-testid={`underleveled-badge-${a.id}`}
                                                        className="text-[10px] tracking-wider border border-destructive/55 text-destructive px-1.5 py-0.5 rounded-sm"
                                                    >
                                                        {advMinLevelBadge(minAdvLevel)}
                                                    </span>
                                                )}
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

                            {/* Phase 14.3-c — backend-driven preview panel */}
                            {selected.length === requiredSize && (
                                <div
                                    data-testid="dispatch-preview-panel"
                                    className="mt-4 border-t border-border pt-4"
                                >
                                    <div className="text-[10px] text-amber tracking-widest mb-3">
                                        {t("expedition_new.preview_title")}
                                    </div>
                                    {previewLoading && (
                                        <div className="text-xs text-muted-foreground">
                                            {t("expedition_new.preview_loading")}
                                        </div>
                                    )}
                                    {!previewLoading && !preview && (
                                        <div className="text-xs text-muted-foreground italic">
                                            {t("expedition_new.preview_unavailable")}
                                        </div>
                                    )}
                                    {!previewLoading && preview && (
                                        <>
                                            <div className="flex items-center justify-between text-xs mb-2">
                                                <span className="text-muted-foreground">{t("expedition_new.preview_injury_risk")}</span>
                                                <span
                                                    data-testid="preview-injury-risk"
                                                    className={
                                                        "px-2 py-0.5 rounded-sm text-[10px] uppercase tracking-wider border " +
                                                        (preview.injury_risk === "low"
                                                            ? "text-[#22c55e] border-[#22c55e]/55"
                                                            : preview.injury_risk === "high"
                                                              ? "text-destructive border-destructive/55"
                                                              : "text-amber border-amber/55")
                                                    }
                                                >
                                                    {t(`expedition_new.preview_injury_${preview.injury_risk}`)}
                                                </span>
                                            </div>

                                            <div className="text-xs space-y-1 mb-3">
                                                <div className="text-muted-foreground">{t("expedition_new.preview_expected_loot")}</div>
                                                <div
                                                    data-testid="preview-gold-range"
                                                    className="text-amber"
                                                >
                                                    {t("expedition_new.preview_gold_range", {
                                                        min: preview.expected_reward.gold_range[0],
                                                        max: preview.expected_reward.gold_range[1],
                                                    })}
                                                </div>
                                                <div data-testid="preview-xp-range">
                                                    {t("expedition_new.preview_xp_range", {
                                                        min: preview.expected_reward.xp_range[0],
                                                        max: preview.expected_reward.xp_range[1],
                                                    })}
                                                </div>
                                                <div className="text-[10px] text-muted-foreground italic">
                                                    {t(`expedition_new.preview_loot_rarity_${preview.expected_reward.loot_rarity_hint}`)}
                                                </div>
                                            </div>

                                            <div className="text-[10px] text-muted-foreground tracking-widest mb-2 mt-3">
                                                {t("expedition_new.preview_modifiers")}
                                            </div>
                                            <div data-testid="preview-modifiers-list" className="flex flex-wrap gap-1.5">
                                                {preview.modifiers.length === 0 && (
                                                    <span className="text-[10px] text-muted-foreground italic">
                                                        {t("expedition_new.preview_no_modifiers")}
                                                    </span>
                                                )}
                                                {preview.modifiers.map((m, idx) => {
                                                    const color =
                                                        m.polarity === "negative"
                                                            ? "#ef4444"
                                                            : m.polarity === "mixed"
                                                              ? "#eab308"
                                                              : "#22c55e";
                                                    return (
                                                        <span
                                                            key={`${m.source}-${m.code}-${idx}`}
                                                            data-testid={`preview-modifier-${m.code}`}
                                                            title={m.description}
                                                            className="inline-flex items-center text-[10px] tracking-wider border px-1.5 py-0.5 rounded-sm"
                                                            style={{ color, borderColor: color + "55" }}
                                                        >
                                                            {m.display_name}
                                                        </span>
                                                    );
                                                })}
                                            </div>
                                        </>
                                    )}
                                </div>
                            )}

                            <Button
                                onClick={() => setShowNarratedPreview(true)}
                                data-testid="btn-narrated-preview"
                                disabled={selected.length !== requiredSize || submitting || hasUnderLeveledSelected}
                                variant="outline"
                                className="w-full h-10 rounded-sm mt-5 border-amber/60 text-amber hover:bg-amber/10 disabled:opacity-50"
                            >
                                {lang === "it" ? "✦ Anteprima narrata" : "✦ Narrated preview"}
                            </Button>

                            <Button
                                onClick={submit}
                                data-testid="btn-send-expedition"
                                disabled={selected.length !== requiredSize || submitting || hasUnderLeveledSelected}
                                title={hasUnderLeveledSelected ? advDungeonTooltip(minAdvLevel) : ""}
                                className="w-full h-10 rounded-sm mt-2 bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {submitting
                                    ? t("expedition_new.dispatching_btn")
                                    : `Send Expedition (${selected.length}/${requiredSize})`}
                            </Button>
                            {hasUnderLeveledSelected && (
                                <p
                                    data-testid="dispatch-blocked-underleveled"
                                    className="text-[11px] text-destructive mt-2 text-center"
                                >
                                    {advDungeonTooltip(minAdvLevel)}
                                </p>
                            )}
                            {!hasUnderLeveledSelected && minAdvLevel > 1 && (
                                <p
                                    data-testid="dungeon-min-level-notice"
                                    className="text-[10px] text-muted-foreground mt-2 text-center"
                                >
                                    Liv. minimo dungeon: {minAdvLevel}
                                </p>
                            )}
                            <p className="text-[10px] text-muted-foreground mt-2 text-center">
                                Estimated values; backend recomputes on dispatch.
                            </p>
                        </div>
                    </aside>
                </div>
            </main>
            <DungeonPreviewModal
                open={showNarratedPreview}
                slug={slug}
                teamIds={selected.map((a) => a.id)}
                onClose={() => setShowNarratedPreview(false)}
                onConfirm={async () => {
                    setShowNarratedPreview(false);
                    await submit();
                }}
                confirming={submitting}
            />
        </div>
    );
}
