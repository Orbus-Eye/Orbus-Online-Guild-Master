// Shared trait badge component (Phase 14.3-c).
// Supports both legacy traits (name, is_positive, modifier_*) coming from
// recruitment candidates and the player-facing shape (display_name,
// polarity, description, rarity) returned by /api/adventurers.

const POLARITY_COLOR = {
    positive: "#22c55e",
    negative: "#ef4444",
    mixed: "#eab308",
};

const RARITY_LABEL = {
    common: "Comune",
    uncommon: "Non comune",
    rare: "Raro",
    epic: "Epico",
};

const formatLegacyEffect = (t) => {
    if (!t || t.modifier_type === undefined || t.modifier_value === undefined) return "";
    const val = t.modifier_value;
    const sign = val >= 0 ? "+" : "";
    if (t.modifier_type === "flat") return `${sign}${val} ${t.affected_stat}`;
    if (t.modifier_type === "percent") return `${sign}${val}% ${t.affected_stat}`;
    return `${val} ${t.affected_stat || ""}`;
};

const derivePolarity = (t) => {
    if (!t) return "positive";
    if (t.polarity) return t.polarity;
    return t.is_positive === false ? "negative" : "positive";
};

const deriveLabel = (t) => {
    if (!t) return "";
    // ROUND 6A.2b — prefer human IT display name when present.
    // Traits generated post-migration carry `display_name_it` in their subdoc.
    return t.display_name_it || t.display_name || t.name || "";
};

export const TraitBadge = ({ trait }) => {
    const polarity = derivePolarity(trait);
    const color = POLARITY_COLOR[polarity] || POLARITY_COLOR.positive;
    const label = deriveLabel(trait);
    const description = trait?.description || formatLegacyEffect(trait) || "";
    const rarity = (trait?.rarity || "").toLowerCase();
    const rarityLabel = RARITY_LABEL[rarity];
    return (
        <span
            data-testid={`trait-${label.toLowerCase().replace(/\s+/g, "-")}`}
            title={description}
            className="inline-flex items-center gap-1 text-[10px] tracking-wider border px-1.5 py-0.5 rounded-sm"
            style={{ color, borderColor: color + "55" }}
        >
            <span>{label}</span>
            {rarityLabel && (
                <span className="opacity-60 text-[9px] uppercase">· {rarityLabel}</span>
            )}
        </span>
    );
};

export const TraitList = ({ traits, testid }) => {
    if (!traits || traits.length === 0) {
        return <span className="text-[10px] text-muted-foreground italic">no traits</span>;
    }
    return (
        <div data-testid={testid} className="flex flex-wrap gap-1">
            {traits.map((t, idx) => (
                <TraitBadge key={t.id || `${t.display_name || t.name || idx}-${idx}`} trait={t} />
            ))}
        </div>
    );
};
