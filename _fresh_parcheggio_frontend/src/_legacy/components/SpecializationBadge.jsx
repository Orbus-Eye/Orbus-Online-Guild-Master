// ROUND 6C — Specialization UI primitives.
// Two exports:
//   <SpecChip spec={adv.specialization} lang="it"/> — compact inline badge for
//     name cells in roster lists.
//   <SpecializationPanel spec={adv.specialization} lang="it"/> — boxed sheet
//     row for /adventurers/:id details (AdventurerDetailModal).
//
// Both render nothing when `spec` is null/undefined so call sites can drop
// them in without conditionals.
const STAT_LABEL = {
    strength: "STR",
    agility: "AGI",
    intellect: "INT",
    endurance: "END",
    faith: "FAI",
};

function pickName(spec, lang) {
    if (!spec) return "";
    return (lang === "it" ? spec.name_it : spec.name_en) || spec.name_it || spec.name_en || spec.slug;
}

export function SpecChip({ spec, lang = "it", testid }) {
    if (!spec) return null;
    const name = pickName(spec, lang);
    return (
        <span
            data-testid={testid}
            title={name}
            className="inline-block text-[9px] tracking-widest border border-amber/60 text-amber px-1.5 py-0.5 rounded-sm whitespace-nowrap"
        >
            ✦ {name}
        </span>
    );
}

export function SpecializationPanel({ spec, lang = "it", t }) {
    if (!spec) return null;
    const name = pickName(spec, lang);
    const tierLabel =
        spec.tier === "starter"
            ? t?.("specialization.tier_starter", "Starter") || "Starter"
            : t?.("specialization.tier_full", "Full hybrid") || "Full hybrid";
    const mods = Object.entries(spec.modifiers || {});
    return (
        <div className="mt-5">
            <div className="text-[10px] text-muted-foreground tracking-widest mb-2">
                {t?.("specialization.badge_label", "SPECIALIZATION") || "SPECIALIZATION"}
            </div>
            <div
                data-testid="adventurer-modal-specialization"
                className="border border-amber/40 bg-amber/5 rounded-sm p-3"
            >
                <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="font-bold text-amber text-sm">
                        ✦ {name}
                    </div>
                    <span className="text-[9px] text-muted-foreground tracking-widest">
                        {tierLabel}
                    </span>
                </div>
                {spec.applied_at_level ? (
                    <div className="text-[10px] text-muted-foreground mb-2">
                        {(t?.("specialization.applied_at_lvl", "Applied at Lv{n}") ||
                            "Applied at Lv{n}").replace("{n}", String(spec.applied_at_level))}
                    </div>
                ) : null}
                {mods.length > 0 && (
                    <div className="text-[10px] text-foreground/80">
                        <span className="text-muted-foreground tracking-widest mr-2">
                            {t?.("specialization.modifiers_label", "MODIFIERS") || "MODIFIERS"}:
                        </span>
                        {mods.map(([k, v]) => (
                            <span key={k} className="inline-block mr-2 text-amber/90">
                                +{v} {STAT_LABEL[k] || k.toUpperCase()}
                            </span>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default SpecChip;
