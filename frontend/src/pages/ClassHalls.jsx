// ROUND 16.0 — Phase 7 — Class Halls page.
// Shows the 10 base-class halls for the current guild. For each hall:
//  - Unlock state (✓ / 🔒) + level
//  - List of 3 specializations with per-spec unlock state + unlock button
//  - Locked halls show a hint telling the user to recruit an adventurer
//    of that class to unlock the hall.
// Italian copy only. Data: GET /api/class-halls (lazy seed on first call),
// POST /api/class-halls/{slug}/unlock-specialization.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { toast } from "sonner";
import { Loader2, Lock, CheckCircle2 } from "lucide-react";
import AppHeader from "../components/AppHeader";
import { Button } from "../components/ui/button";
import { classLabel, specLabel } from "../utils/displayLabels";

// Italian narrative names for each Class Hall.
const HALL_NAME_IT = {
    warrior: "Sala del Guerriero",
    rogue: "Sala del Ladro",
    mage: "Sala del Mago",
    priest: "Sala del Sacerdote",
    ranger: "Sala del Ranger",
    paladin: "Sala del Paladino",
    druid: "Sala del Druido",
    monk: "Sala del Monaco",
    bard: "Sala del Bardo",
    warlock: "Sala dello Stregone",
};

// The 3 specializations per base class (slugs).
const SPECS_BY_CLASS = {
    warrior: ["berserker_spec", "guardian_spec", "weapon_master_spec"],
    rogue: ["assassin_spec", "duelist_spec", "shadow_spec"],
    mage: ["necromancer_spec", "elementalist_spec", "arcanist_spec"],
    priest: ["healer_spec", "exorcist_spec", "oracle_spec"],
    ranger: ["marksman_spec", "monster_hunter_spec", "scout_spec"],
    paladin: ["oath_defender_spec", "rune_knight_spec", "vindicator_spec"],
    druid: ["leafwarden_spec", "shapeshifter_spec", "shaman_spec"],
    monk: ["inner_fist_spec", "spirit_guardian_spec", "ascetic_spec"],
    bard: ["warsinger_spec", "herald_spec", "inspiration_weaver_spec"],
    warlock: ["demon_pact_spec", "void_pact_spec", "stellar_pact_spec"],
};

const BASE_ORDER = [
    "warrior", "rogue", "mage", "priest", "ranger",
    "paladin", "druid", "monk", "bard", "warlock",
];

function HallCard({ hall, onUnlock, busySlug }) {
    const classSlug = hall.class_slug;
    const unlockedSpecs = new Set(hall.unlocked_specializations || []);
    const allSpecs = SPECS_BY_CLASS[classSlug] || [];
    return (
        <div
            data-testid={`class-hall-card-${classSlug}`}
            className="border border-border bg-card rounded-sm p-4 flex flex-col gap-3"
        >
            <header className="flex items-baseline justify-between gap-2 flex-wrap">
                <h3 className="text-base font-semibold tracking-tight">
                    {HALL_NAME_IT[classSlug] || classLabel(classSlug)}
                </h3>
                {hall.is_unlocked ? (
                    <span
                        data-testid={`class-hall-status-${classSlug}`}
                        className="inline-flex items-center gap-1 text-[10px] tracking-widest text-emerald-400/90 border border-emerald-400/40 rounded-sm px-2 py-0.5"
                    >
                        <CheckCircle2 size={12} aria-hidden="true" />
                        SBLOCCATA · LV {hall.level || 1}
                    </span>
                ) : (
                    <span
                        data-testid={`class-hall-status-${classSlug}`}
                        className="inline-flex items-center gap-1 text-[10px] tracking-widest text-muted-foreground border border-border rounded-sm px-2 py-0.5"
                    >
                        <Lock size={12} aria-hidden="true" />
                        BLOCCATA
                    </span>
                )}
            </header>

            {!hall.is_unlocked ? (
                <p className="text-[11px] text-muted-foreground italic">
                    Recluta almeno un avventuriero di questa classe per sbloccare la Sala.
                </p>
            ) : (
                <div className="space-y-2">
                    <div className="text-[10px] tracking-widest text-muted-foreground">
                        :: SPECIALIZZAZIONI
                    </div>
                    {allSpecs.map((spec) => {
                        const isUnlocked = unlockedSpecs.has(spec);
                        const isBusy = busySlug === `${classSlug}:${spec}`;
                        return (
                            <div
                                key={spec}
                                data-testid={`class-hall-spec-${classSlug}-${spec}`}
                                className="flex items-center justify-between gap-2 border border-border/60 rounded-sm px-3 py-2"
                            >
                                <div className="min-w-0">
                                    <div className="text-sm">{specLabel(spec)}</div>
                                    <div className="text-[10px] text-muted-foreground">
                                        {isUnlocked ? "Disponibile per gli avventurieri" : "Non ancora sbloccata"}
                                    </div>
                                </div>
                                {isUnlocked ? (
                                    <span
                                        className="text-[10px] tracking-widest text-emerald-400/90"
                                        aria-label="Sbloccata"
                                    >
                                        ✓
                                    </span>
                                ) : (
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        data-testid={`class-hall-unlock-btn-${classSlug}-${spec}`}
                                        disabled={isBusy}
                                        onClick={() => onUnlock(classSlug, spec)}
                                    >
                                        {isBusy ? (
                                            <Loader2 size={12} className="animate-spin" />
                                        ) : (
                                            "Sblocca"
                                        )}
                                    </Button>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

export default function ClassHalls() {
    const [halls, setHalls] = useState(null);
    const [loading, setLoading] = useState(true);
    const [busySlug, setBusySlug] = useState(null);

    const load = async () => {
        setLoading(true);
        try {
            const r = await api.get("/class-halls");
            const list = r.data?.halls || [];
            // Always render in canonical base-class order.
            const byKey = Object.fromEntries(list.map((h) => [h.class_slug, h]));
            const ordered = BASE_ORDER.map((s) => byKey[s]).filter(Boolean);
            setHalls(ordered);
        } catch (err) {
            const msg = err?.response?.data?.detail?.user_message
                || "Impossibile caricare le Sale di Classe.";
            toast.error(msg);
            setHalls([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { load(); }, []);

    const handleUnlock = async (classSlug, specSlug) => {
        setBusySlug(`${classSlug}:${specSlug}`);
        try {
            await api.post(`/class-halls/${classSlug}/unlock-specialization`, {
                specialization_slug: specSlug,
            });
            toast.success(`Specializzazione "${specLabel(specSlug)}" sbloccata!`);
            await load();
        } catch (err) {
            const msg = err?.response?.data?.detail?.user_message
                || "Sblocco non riuscito. Riprova fra poco.";
            toast.error(msg);
        } finally {
            setBusySlug(null);
        }
    };

    const unlockedCount = (halls || []).filter((h) => h.is_unlocked).length;
    const totalSpecsUnlocked = (halls || []).reduce(
        (n, h) => n + (h.unlocked_specializations?.length || 0), 0);

    return (
        <div className="min-h-screen bg-background">
            <AppHeader subtitleKey="nav.brand_subtitle_dashboard" />
            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
                <div className="mb-6 flex items-baseline justify-between gap-3 flex-wrap">
                    <div>
                        <h1
                            data-testid="class-halls-title"
                            className="text-xl sm:text-2xl font-semibold tracking-tight"
                        >
                            Sale di Classe
                        </h1>
                        <p className="text-xs text-muted-foreground mt-1">
                            10 sale, una per ogni classe base. Sblocca le specializzazioni per
                            avanzare gli avventurieri della tua gilda.
                        </p>
                    </div>
                    {halls && (
                        <div
                            data-testid="class-halls-summary"
                            className="text-[11px] tracking-widest text-muted-foreground"
                        >
                            Sale sbloccate <span className="text-emerald-400/90">{unlockedCount}/10</span>
                            {" · "}
                            Spec sbloccate <span className="text-amber/90">{totalSpecsUnlocked}/30</span>
                        </div>
                    )}
                </div>

                <div className="text-xs mb-4">
                    <Link
                        to="/adventurers"
                        className="text-muted-foreground hover:text-foreground underline-offset-2 hover:underline"
                    >
                        ← Torna al roster
                    </Link>
                </div>

                {loading && (
                    <div className="text-xs text-muted-foreground border border-border bg-card rounded-sm p-6">
                        Caricamento delle Sale<span className="caret-blink" />
                    </div>
                )}

                {!loading && halls && halls.length === 0 && (
                    <div className="text-xs text-muted-foreground border border-border bg-card rounded-sm p-6">
                        Nessuna Sala di Classe disponibile per questa gilda.
                    </div>
                )}

                {!loading && halls && halls.length > 0 && (
                    <div
                        data-testid="class-halls-grid"
                        className="grid grid-cols-1 md:grid-cols-2 gap-4"
                    >
                        {halls.map((h) => (
                            <HallCard
                                key={h.class_slug}
                                hall={h}
                                onUnlock={handleUnlock}
                                busySlug={busySlug}
                            />
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}
