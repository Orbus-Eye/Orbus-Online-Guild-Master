// FASE 9F — Sale di Classe ridisegnate: CLASSE → RUOLO FISSO.
// Niente specializzazioni, niente build selector, niente Build Lab.
// Backed by GET /api/class-halls (27 sale canoniche, arricchite dal
// registry: ruolo, identità, meccanica, punti di forza, tag equip).

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { toast } from "sonner";
import { CheckCircle2, Lock } from "lucide-react";
import AppHeader from "../components/AppHeader";
import ClassHallAssignmentJourney from "../components/ClassHallAssignmentJourney";
import ClassHallItemTrack from "../components/ClassHallItemTrack";
import ClassHallCollectionBook from "../components/ClassHallCollectionBook";
import GameImage from "../components/GameImage";
import { useT } from "../i18n/I18nContext";
import { roleLabel } from "../utils/displayLabels";

const ROLE_STYLE = {
    DPS: "text-red-300 border-red-400/50",
    TANK: "text-sky-300 border-sky-400/50",
    HEALER: "text-emerald-300 border-emerald-400/50",
};

function RoleBadge({ role }) {
    if (!role) return null;
    return (
        <span
            data-testid={`class-role-badge-${role}`}
            className={`inline-block text-[10px] tracking-widest border rounded-sm px-2 py-0.5 ${ROLE_STYLE[role] || "text-muted-foreground border-border"}`}
        >
            {roleLabel(role).toUpperCase()} · {role}
        </span>
    );
}

function HallCard({ hall }) {
    const cs = hall.class_slug;
    const advCount = hall.adventurers_of_class || 0;
    const top = hall.top_adventurers || [];
    const sets = hall.class_raid_sets || [];

    return (
        <div
            data-testid={`class-hall-card-${cs}`}
            className="border border-border bg-card rounded-sm p-4 flex flex-col gap-3"
        >
            {/* Header: emblema + nome + ruolo FISSO + identità */}
            <header className="flex items-start gap-3">
                <GameImage
                    sources={[
                        `/assets/classes/${hall.class_emblem || cs}.svg`,
                        "/assets/avatars/default.svg",
                    ]}
                    alt=""
                    className="w-14 h-14 rounded-sm border border-amber/30 shrink-0"
                />
                <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-base font-semibold tracking-tight font-fantasy">
                            {hall.class_name_it || cs}
                        </h3>
                        <RoleBadge role={hall.class_role} />
                    </div>
                    {hall.class_identity_it && (
                        <p className="text-[11px] text-amber/85 italic mt-0.5">
                            “{hall.class_identity_it}”
                        </p>
                    )}
                    <p className="text-[10px] text-muted-foreground mt-0.5">
                        {advCount === 1
                            ? "1 avventuriero di questa classe"
                            : `${advCount} avventurieri di questa classe`}
                    </p>
                </div>
                {hall.is_unlocked ? (
                    <span
                        data-testid={`class-hall-status-${cs}`}
                        className="inline-flex items-center gap-1 text-[10px] tracking-widest text-emerald-400/90 border border-emerald-400/40 rounded-sm px-2 py-0.5 shrink-0"
                    >
                        <CheckCircle2 size={12} aria-hidden="true" />
                        SALA ATTIVA
                    </span>
                ) : (
                    <span
                        data-testid={`class-hall-status-${cs}`}
                        className="inline-flex items-center gap-1 text-[10px] tracking-widest text-muted-foreground border border-border rounded-sm px-2 py-0.5 shrink-0"
                    >
                        <Lock size={12} aria-hidden="true" />
                        VUOTA
                    </span>
                )}
            </header>

            {/* Stile di combattimento */}
            {hall.class_mechanics_it && (
                <p
                    data-testid={`class-hall-mechanics-${cs}`}
                    className="text-[11px] text-foreground/85 leading-relaxed"
                >
                    {hall.class_mechanics_it}
                </p>
            )}

            {/* Punti di forza */}
            {(hall.class_strengths_it || []).length > 0 && (
                <section data-testid={`class-hall-strengths-${cs}`}>
                    <div className="text-[10px] text-muted-foreground tracking-widest mb-1">
                        :: PUNTI DI FORZA
                    </div>
                    <ul className="text-[11px] text-foreground/80 space-y-0.5">
                        {hall.class_strengths_it.map((s) => (
                            <li key={s}>• {s}</li>
                        ))}
                    </ul>
                </section>
            )}

            {/* Equip di classe */}
            {((hall.armor_tags || []).length > 0
                || (hall.weapon_tags || []).length > 0) && (
                <section data-testid={`class-hall-equip-${cs}`}>
                    <div className="text-[10px] text-muted-foreground tracking-widest mb-1">
                        :: EQUIPAGGIAMENTO DI CLASSE
                    </div>
                    <div className="flex flex-wrap gap-1">
                        {[...(hall.weapon_tags || []), ...(hall.armor_tags || [])].map((tag) => (
                            <span
                                key={tag}
                                className="text-[9px] tracking-wide text-muted-foreground border border-border/60 rounded-sm px-1.5 py-0.5"
                            >
                                {tag}
                            </span>
                        ))}
                    </div>
                </section>
            )}

            {hall.is_unlocked ? (
                <>
                    {/* Progressione: top membri */}
                    {top.length > 0 && (
                        <section data-testid={`class-hall-top-${cs}`}>
                            <div className="text-[10px] text-muted-foreground tracking-widest mb-1">
                                :: PROGRESSIONE — TOP MEMBRI
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
                                            Lv{a.level} · {a.total_power} PWR
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        </section>
                    )}
                </>
            ) : (
                <p className="text-[11px] text-muted-foreground italic"
                   data-testid={`class-hall-unlock-hint-${cs}`}>
                    {hall.unlock_hint_it
                        || "Assegna almeno un avventuriero a questa classe per sbloccare la Sala."}
                </p>
            )}

            {/* Set raid di classe (popolati dalla FASE 9E) */}
            {sets.length > 0 && (
                <section data-testid={`class-hall-raid-sets-${cs}`}>
                    <div className="text-[10px] text-muted-foreground tracking-widest mb-1">
                        :: SET RAID DI CLASSE
                    </div>
                    <ul className="text-[11px] space-y-0.5">
                        {sets.map((s) => (
                            <li key={s.set_id} className="flex justify-between gap-2">
                                <span className="truncate">{s.name_it}</span>
                                <span className="text-[10px] text-muted-foreground shrink-0">
                                    Lv {s.required_level} · {s.raid_name_it}
                                </span>
                            </li>
                        ))}
                    </ul>
                </section>
            )}
        </div>
    );
}

const ROLE_ORDER = { TANK: 0, HEALER: 1, DPS: 2 };

export default function ClassHalls() {
    const { lang } = useT();
    const it = lang === "it";
    const [halls, setHalls] = useState(null);
    const [kpi, setKpi] = useState(null);
    const [loading, setLoading] = useState(true);
    const [roleFilter, setRoleFilter] = useState("");

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const r = await api.get("/class-halls");
            const list = r.data?.halls || [];
            list.sort((a, b) => (
                (ROLE_ORDER[a.class_role] ?? 9) - (ROLE_ORDER[b.class_role] ?? 9)
                || String(a.class_name_it || a.class_slug)
                    .localeCompare(String(b.class_name_it || b.class_slug))
            ));
            setHalls(list);
            setKpi(r.data?.kpi || null);
        } catch (err) {
            const msg = err?.response?.data?.detail?.user_message
                || "Impossibile caricare le Sale di Classe.";
            toast.error(msg);
            setHalls([]);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { load(); }, [load]);

    const visible = (halls || []).filter(
        (h) => !roleFilter || h.class_role === roleFilter
    );

    return (
        <div className="min-h-screen bg-background">
            <AppHeader subtitleKey="nav.brand_subtitle_dashboard" />
            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
                <div className="mb-4 flex items-baseline justify-between gap-3 flex-wrap">
                    <div>
                        <h1
                            data-testid="class-halls-title"
                            className="text-xl sm:text-2xl font-semibold tracking-tight font-fantasy"
                        >
                            Sale di Classe
                        </h1>
                        <p className="text-xs text-muted-foreground mt-1">
                            27 classi, ognuna con un ruolo fisso: 13 da Danno,
                            6 Difensori, 8 Guaritori. La classe È l&apos;identità:
                            niente specializzazioni, niente build.
                        </p>
                    </div>
                    {kpi && (
                        <div
                            data-testid="class-halls-summary"
                            className="text-[11px] tracking-widest text-muted-foreground"
                        >
                            {it ? "Sale attive" : "Halls unlocked"}{" "}
                            <span className="text-emerald-400/90">
                                {kpi.halls_unlocked}/{kpi.halls_total}
                            </span>
                        </div>
                    )}
                </div>

                <ClassHallAssignmentJourney />
                <ClassHallItemTrack />
                <ClassHallCollectionBook />

                <div className="flex items-center justify-between gap-3 flex-wrap mb-4">
                    <div className="flex gap-1.5" data-testid="class-halls-role-filter">
                        {["", "DPS", "TANK", "HEALER"].map((r) => (
                            <button
                                key={r || "all"}
                                type="button"
                                onClick={() => setRoleFilter(r)}
                                className={`text-[10px] tracking-widest border rounded-sm px-2.5 py-1 transition-colors ${
                                    roleFilter === r
                                        ? "border-amber text-amber"
                                        : "border-border text-muted-foreground hover:text-foreground"
                                }`}
                            >
                                {r === "" ? "TUTTE" : `${roleLabel(r).toUpperCase()}`}
                            </button>
                        ))}
                    </div>
                    <Link
                        to="/adventurers"
                        className="text-xs text-muted-foreground hover:text-foreground underline-offset-2 hover:underline"
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
                    <div
                        data-testid="class-halls-empty"
                        className="border border-border bg-card rounded-sm p-6 text-center text-xs text-muted-foreground"
                    >
                        <p className="mb-3">
                            Nessuna Sala di Classe ancora attiva. Recluta
                            avventurieri e assegna loro una classe.
                        </p>
                        <Link
                            to="/recruitment"
                            className="inline-block text-[11px] tracking-widest text-amber border border-amber/55 hover:bg-amber/10 px-3 py-1.5 rounded-sm"
                        >
                            VAI A RECLUTAMENTO →
                        </Link>
                    </div>
                )}

                {!loading && visible.length > 0 && (
                    <div
                        data-testid="class-halls-grid"
                        className="grid grid-cols-1 md:grid-cols-2 gap-4"
                    >
                        {visible.map((h) => (
                            <HallCard key={h.class_slug} hall={h} />
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}
