// ROUND 16.1 Phase 3 — Class Halls expanded page.
// Backed by enriched GET /api/class-halls payload:
//   - kpi { halls_unlocked, halls_total, specs_unlocked, specs_total }
//   - halls[].adventurers_of_class, available_to_specialize, top_adventurers[]
//   - halls[].specializations[] {slug, name_it/en, role, is_unlocked,
//     is_unlockable, requires_class_hall_level}
//   - halls[].bonuses [] (placeholder for Round 16.A)
// Bilingual IT + EN. Dark theme. Mobile-first card grid.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { toast } from "sonner";
import { Loader2, Lock, CheckCircle2, Users } from "lucide-react";
import AppHeader from "../components/AppHeader";
import { Button } from "../components/ui/button";
import { useT } from "../i18n/I18nContext";

const HALL_NAME = {
    warrior:   { it: "Sala del Guerriero",  en: "Hall of the Warrior" },
    rogue:     { it: "Sala del Ladro",       en: "Hall of the Rogue" },
    mage:      { it: "Sala del Mago",        en: "Hall of the Mage" },
    priest:    { it: "Sala del Sacerdote",   en: "Hall of the Priest" },
    ranger:    { it: "Sala del Ranger",      en: "Hall of the Ranger" },
    paladin:   { it: "Sala del Paladino",    en: "Hall of the Paladin" },
    druid:     { it: "Sala del Druido",      en: "Hall of the Druid" },
    monk:      { it: "Sala del Monaco",      en: "Hall of the Monk" },
    bard:      { it: "Sala del Bardo",       en: "Hall of the Bard" },
    warlock:   { it: "Sala dello Stregone",  en: "Hall of the Warlock" },
    alchemist: { it: "Sala dell'Alchimista", en: "Hall of the Alchemist" },
};

const BASE_ORDER = [
    "warrior", "rogue", "mage", "priest", "ranger",
    "paladin", "druid", "monk", "bard", "warlock", "alchemist",
];

function HallCard({ hall, onUnlock, busySlug, lang }) {
    const it = lang === "it";
    const cs = hall.class_slug;
    const title = HALL_NAME[cs]?.[lang] || cs;
    const advCount = hall.adventurers_of_class || 0;
    const noSpec = hall.available_to_specialize || 0;
    const top = hall.top_adventurers || [];
    const specs = hall.specializations || [];
    const bonuses = hall.bonuses || [];

    return (
        <div
            data-testid={`class-hall-card-${cs}`}
            className="border border-border bg-card rounded-sm p-4 flex flex-col gap-3"
        >
            <header className="flex items-start justify-between gap-2 flex-wrap">
                <div>
                    <h3 className="text-base font-semibold tracking-tight">{title}</h3>
                    <p className="text-[10px] text-muted-foreground tracking-wide mt-0.5">
                        {it ? `${advCount} avventurier${advCount === 1 ? "o" : "i"} appartenent${advCount === 1 ? "e" : "i"}`
                            : `${advCount} adventurer${advCount === 1 ? "" : "s"} of this class`}
                    </p>
                </div>
                {hall.is_unlocked ? (
                    <span
                        data-testid={`class-hall-status-${cs}`}
                        className="inline-flex items-center gap-1 text-[10px] tracking-widest text-emerald-400/90 border border-emerald-400/40 rounded-sm px-2 py-0.5"
                    >
                        <CheckCircle2 size={12} aria-hidden="true" />
                        {it ? `SBLOCCATA · LV ${hall.level || 1}` : `UNLOCKED · LV ${hall.level || 1}`}
                    </span>
                ) : (
                    <span
                        data-testid={`class-hall-status-${cs}`}
                        className="inline-flex items-center gap-1 text-[10px] tracking-widest text-muted-foreground border border-border rounded-sm px-2 py-0.5"
                    >
                        <Lock size={12} aria-hidden="true" />
                        {it ? "BLOCCATA" : "LOCKED"}
                    </span>
                )}
            </header>

            {!hall.is_unlocked ? (
                <p className="text-[11px] text-muted-foreground italic"
                   data-testid={`class-hall-unlock-hint-${cs}`}>
                    {hall.unlock_hint_it && it
                        ? hall.unlock_hint_it
                        : (hall.unlock_hint_en
                            || (it
                                ? "Recluta almeno un avventuriero di questa classe per sbloccare la Sala."
                                : "Recruit at least one adventurer of this class to unlock the Hall."))}
                </p>
            ) : (
                <>
                    {/* Top 3 adventurers */}
                    {top.length > 0 && (
                        <section data-testid={`class-hall-top-${cs}`}>
                            <div className="text-[10px] text-muted-foreground tracking-widest mb-1">
                                {it ? ":: TOP MEMBRI" : ":: TOP MEMBERS"}
                            </div>
                            <ul className="space-y-0.5">
                                {top.map((a) => (
                                    <li key={a.id}
                                        className="flex justify-between text-xs border-b border-border/40 py-0.5">
                                        <Link
                                            to={`/adventurers?focus=${encodeURIComponent(a.id)}`}
                                            className="text-foreground/90 hover:text-amber truncate"
                                        >
                                            {a.name}
                                        </Link>
                                        <span className="text-[10px] text-muted-foreground shrink-0">
                                            Lv{a.level} · {a.total_power}p
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        </section>
                    )}

                    {noSpec > 0 && (
                        <div
                            data-testid={`class-hall-no-spec-${cs}`}
                            className="text-[10px] text-amber/90 border-l-2 border-amber/55 pl-2 py-0.5 flex items-center gap-1"
                        >
                            <Users size={11} aria-hidden="true" />
                            {it
                                ? `${noSpec} senza specializzazione — assegnane una per potenziarli.`
                                : `${noSpec} without specialization — assign one to power them up.`}
                        </div>
                    )}

                    {/* Specializations */}
                    <section>
                        <div className="text-[10px] tracking-widest text-muted-foreground mb-1">
                            {it ? ":: SPECIALIZZAZIONI" : ":: SPECIALIZATIONS"}
                        </div>
                        <div className="space-y-1.5">
                            {specs.map((spec) => {
                                const name = it ? spec.name_it : spec.name_en;
                                const isUnlocked = !!spec.is_unlocked;
                                const isBusy = busySlug === `${cs}:${spec.slug}`;
                                return (
                                    <div
                                        key={spec.slug}
                                        data-testid={`class-hall-spec-${cs}-${spec.slug}`}
                                        className="flex items-center justify-between gap-2 border border-border/60 rounded-sm px-3 py-2"
                                    >
                                        <div className="min-w-0 flex-1">
                                            <div className="text-sm flex items-center gap-2 flex-wrap">
                                                <span>{name}</span>
                                                {spec.role && (
                                                    <span className="text-[9px] tracking-widest text-muted-foreground border border-border rounded-sm px-1">
                                                        {spec.role}
                                                    </span>
                                                )}
                                            </div>
                                            <div className="text-[10px] text-muted-foreground">
                                                {isUnlocked
                                                    ? (it ? "Disponibile per gli avventurieri" : "Available to adventurers")
                                                    : spec.is_unlockable
                                                        ? (it ? "Sbloccabile ora" : "Unlockable now")
                                                        : (it
                                                            ? `Richiede Hall Lv ${spec.requires_class_hall_level}`
                                                            : `Requires Hall Lv ${spec.requires_class_hall_level}`)}
                                            </div>
                                        </div>
                                        {isUnlocked ? (
                                            <span
                                                className="text-[10px] tracking-widest text-emerald-400/90"
                                                aria-label={it ? "Sbloccata" : "Unlocked"}
                                            >
                                                ✓
                                            </span>
                                        ) : (
                                            <Button
                                                size="sm"
                                                variant="outline"
                                                data-testid={`class-hall-unlock-btn-${cs}-${spec.slug}`}
                                                disabled={isBusy || !spec.is_unlockable}
                                                onClick={() => onUnlock(cs, spec.slug)}
                                            >
                                                {isBusy ? (
                                                    <Loader2 size={12} className="animate-spin" />
                                                ) : (
                                                    it ? "Sblocca" : "Unlock"
                                                )}
                                            </Button>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </section>

                    {/* Bonuses placeholder — Round 16.A */}
                    <section data-testid={`class-hall-bonuses-${cs}`}>
                        <div className="text-[10px] tracking-widest text-muted-foreground mb-1">
                            {it ? ":: BONUS ATTIVI" : ":: ACTIVE BONUSES"}
                        </div>
                        {bonuses.length === 0 ? (
                            <p className="text-[11px] text-muted-foreground italic">
                                {it
                                    ? "Nessun bonus attivo — i bonus di Sala arriveranno nel Round 16.A."
                                    : "No active bonuses — Hall bonuses arrive in Round 16.A."}
                            </p>
                        ) : (
                            <ul className="text-xs space-y-0.5">
                                {bonuses.map((b, i) => (
                                    <li key={i}>{it ? b.label_it : b.label_en}</li>
                                ))}
                            </ul>
                        )}
                    </section>
                </>
            )}
        </div>
    );
}

export default function ClassHalls() {
    const { lang } = useT();
    const it = lang === "it";
    const [halls, setHalls] = useState(null);
    const [kpi, setKpi] = useState(null);
    const [loading, setLoading] = useState(true);
    const [busySlug, setBusySlug] = useState(null);

    const load = async () => {
        setLoading(true);
        try {
            const r = await api.get("/class-halls");
            const list = r.data?.halls || [];
            const byKey = Object.fromEntries(list.map((h) => [h.class_slug, h]));
            const ordered = BASE_ORDER.map((s) => byKey[s]).filter(Boolean);
            setHalls(ordered);
            setKpi(r.data?.kpi || null);
        } catch (err) {
            const msg = err?.response?.data?.detail?.user_message
                || (it ? "Impossibile caricare le Sale di Classe." : "Failed to load Class Halls.");
            toast.error(msg);
            setHalls([]);
        } finally {
            setLoading(false);
        }
    };

    // ROUND 16.3 Iter B (P2.5) — `load` is intentionally called only at mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    useEffect(() => { load(); }, []);

    const handleUnlock = async (classSlug, specSlug) => {
        setBusySlug(`${classSlug}:${specSlug}`);
        try {
            await api.post(`/class-halls/${classSlug}/unlock-specialization`, {
                specialization_slug: specSlug,
            });
            toast.success(it ? "Specializzazione sbloccata!" : "Specialization unlocked!");
            await load();
        } catch (err) {
            const msg = err?.response?.data?.detail?.user_message
                || (it ? "Sblocco non riuscito. Riprova fra poco." : "Unlock failed. Try again shortly.");
            toast.error(msg);
        } finally {
            setBusySlug(null);
        }
    };

    return (
        <div className="min-h-screen bg-background">
            <AppHeader subtitleKey="nav.brand_subtitle_dashboard" />
            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
                <div className="mb-4 flex items-baseline justify-between gap-3 flex-wrap">
                    <div>
                        <h1
                            data-testid="class-halls-title"
                            className="text-xl sm:text-2xl font-semibold tracking-tight"
                        >
                            {it ? "Sale di Classe" : "Class Halls"}
                        </h1>
                        <p className="text-xs text-muted-foreground mt-1">
                            {it
                                ? "Progressione della tua gilda per ogni classe. Sblocca le specializzazioni per potenziare i tuoi avventurieri."
                                : "Your guild's progression per class. Unlock specializations to power up your adventurers."}
                        </p>
                    </div>
                    {kpi && (
                        <div
                            data-testid="class-halls-summary"
                            className="text-[11px] tracking-widest text-muted-foreground"
                        >
                            {it ? "Sale sbloccate" : "Halls unlocked"}{" "}
                            <span className="text-emerald-400/90">{kpi.halls_unlocked}/{kpi.halls_total}</span>
                            {" · "}
                            {it ? "Spec sbloccate" : "Specs unlocked"}{" "}
                            <span className="text-amber/90">{kpi.specs_unlocked}/{kpi.specs_total}</span>
                        </div>
                    )}
                </div>

                <div className="text-xs mb-4">
                    <Link
                        to="/adventurers"
                        className="text-muted-foreground hover:text-foreground underline-offset-2 hover:underline"
                    >
                        {it ? "← Torna al roster" : "← Back to roster"}
                    </Link>
                </div>

                {loading && (
                    <div className="text-xs text-muted-foreground border border-border bg-card rounded-sm p-6">
                        {it ? "Caricamento delle Sale" : "Loading halls"}<span className="caret-blink" />
                    </div>
                )}

                {!loading && halls && halls.length === 0 && (
                    <div
                        data-testid="class-halls-empty"
                        className="border border-border bg-card rounded-sm p-6 text-center text-xs text-muted-foreground"
                    >
                        <p className="mb-3">
                            {it
                                ? "Nessuna Sala di Classe ancora attiva. Recluta avventurieri per sbloccare le tue prime Sale."
                                : "No Class Halls active yet. Recruit adventurers to unlock your first Halls."}
                        </p>
                        <Link
                            to="/recruitment"
                            className="inline-block text-[11px] tracking-widest text-amber border border-amber/55 hover:bg-amber/10 px-3 py-1.5 rounded-sm"
                        >
                            {it ? "VAI A RECLUTAMENTO →" : "GO TO RECRUITMENT →"}
                        </Link>
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
                                lang={lang}
                            />
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}
