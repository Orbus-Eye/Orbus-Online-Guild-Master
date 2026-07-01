// ROUND 16.1 Phase 2 — Roster filter+sort toolbar (sessionStorage persisted).
// Hooks into the existing Adventurers page via callback. Italian + English.

import { useEffect, useState } from "react";
import { useT } from "../i18n/I18nContext";

const KEY = "orbus.r161.roster.filters";

const SORT_OPTIONS = [
    { value: "", label_it: "Default", label_en: "Default" },
    { value: "level_desc", label_it: "Livello ↓", label_en: "Level ↓" },
    { value: "level_asc", label_it: "Livello ↑", label_en: "Level ↑" },
    { value: "power_desc", label_it: "Potere ↓", label_en: "Power ↓" },
    { value: "power_asc", label_it: "Potere ↑", label_en: "Power ↑" },
    { value: "primary_desc", label_it: "Stat primaria ↓", label_en: "Primary stat ↓" },
    { value: "name_asc", label_it: "Nome A-Z", label_en: "Name A-Z" },
    { value: "class_asc", label_it: "Classe A-Z", label_en: "Class A-Z" },
];

const CLASS_OPTIONS = [
    ["", { it: "Tutte le classi", en: "All classes" }],
    ["warrior", { it: "Guerriero", en: "Warrior" }],
    ["paladin", { it: "Paladino", en: "Paladin" }],
    ["rogue", { it: "Ladro", en: "Rogue" }],
    ["ranger", { it: "Ranger", en: "Ranger" }],
    ["monk", { it: "Monaco", en: "Monk" }],
    ["mage", { it: "Mago", en: "Mage" }],
    ["priest", { it: "Sacerdote", en: "Priest" }],
    ["druid", { it: "Druido", en: "Druid" }],
    ["bard", { it: "Bardo", en: "Bard" }],
    ["warlock", { it: "Stregone", en: "Warlock" }],
    ["alchemist", { it: "Alchimista", en: "Alchemist" }],
];

const ROLE_OPTIONS = [
    ["", { it: "Tutti i ruoli", en: "All roles" }],
    ["Tank", { it: "Difensore", en: "Tank" }],
    ["DPS", { it: "Attaccante", en: "DPS" }],
    ["Healer", { it: "Guaritore", en: "Healer" }],
    ["Caster", { it: "Incantatore", en: "Caster" }],
    ["Support", { it: "Supporto", en: "Support" }],
];

export default function RosterFilterBar({ onChange, totalCount, filteredCount }) {
    const { lang } = useT();
    const it = lang === "it";
    const [state, setState] = useState(() => {
        try {
            const raw = sessionStorage.getItem(KEY);
            return raw ? JSON.parse(raw) : {};
        } catch { return {}; }
    });

    useEffect(() => {
        sessionStorage.setItem(KEY, JSON.stringify(state));
        onChange?.(state);
    }, [state]);  // eslint-disable-line react-hooks/exhaustive-deps

    const set = (k, v) => setState((s) => ({ ...s, [k]: v }));
    const reset = () => setState({});

    const hasAny = Object.values(state).some(Boolean);

    return (
        <div
            className="border border-border bg-card rounded-sm p-3 mb-4 flex flex-wrap items-center gap-2 text-xs"
            data-testid="roster-filter-bar"
        >
            <select
                data-testid="roster-filter-class"
                value={state.class_slug || ""}
                onChange={(e) => set("class_slug", e.target.value)}
                className="bg-secondary border border-border rounded-sm px-2 py-1 text-foreground"
            >
                {CLASS_OPTIONS.map(([v, l]) => (
                    <option key={v || "all"} value={v}>{it ? l.it : l.en}</option>
                ))}
            </select>
            <select
                data-testid="roster-filter-role"
                value={state.role || ""}
                onChange={(e) => set("role", e.target.value)}
                className="bg-secondary border border-border rounded-sm px-2 py-1 text-foreground"
            >
                {ROLE_OPTIONS.map(([v, l]) => (
                    <option key={v || "all"} value={v}>{it ? l.it : l.en}</option>
                ))}
            </select>
            <label className="flex items-center gap-1 text-muted-foreground">
                <input
                    type="checkbox"
                    data-testid="roster-filter-improvable"
                    checked={!!state.improvable_equip}
                    onChange={(e) => set("improvable_equip", e.target.checked)}
                />
                {it ? "Equip migliorabile" : "Improvable gear"}
            </label>
            <label className="flex items-center gap-1 text-muted-foreground">
                <input
                    type="checkbox"
                    data-testid="roster-filter-nospec"
                    checked={!!state.no_spec}
                    onChange={(e) => set("no_spec", e.target.checked)}
                />
                {it ? "Senza spec" : "No spec"}
            </label>
            <label className="flex items-center gap-1 text-muted-foreground">
                <input
                    type="checkbox"
                    data-testid="roster-filter-ready"
                    checked={!!state.ready_for_dungeon}
                    onChange={(e) => set("ready_for_dungeon", e.target.checked)}
                />
                {it ? "Pronto dungeon" : "Dungeon-ready"}
            </label>
            <select
                data-testid="roster-sort"
                value={state.sort || ""}
                onChange={(e) => set("sort", e.target.value)}
                className="bg-secondary border border-border rounded-sm px-2 py-1 text-foreground"
            >
                {SORT_OPTIONS.map((o) => (
                    <option key={o.value || "default"} value={o.value}>
                        {it ? `Ordina: ${o.label_it}` : `Sort: ${o.label_en}`}
                    </option>
                ))}
            </select>
            {hasAny && (
                <button
                    type="button"
                    data-testid="roster-filter-reset"
                    onClick={reset}
                    className="text-amber/85 hover:text-amber underline-offset-2 hover:underline"
                >
                    {it ? "Reset" : "Reset"}
                </button>
            )}
            <span className="ml-auto text-[10px] text-muted-foreground tracking-widest">
                {it
                    ? `${filteredCount ?? "?"} di ${totalCount ?? "?"} avventurieri`
                    : `${filteredCount ?? "?"} of ${totalCount ?? "?"} adventurers`}
            </span>
        </div>
    );
}
