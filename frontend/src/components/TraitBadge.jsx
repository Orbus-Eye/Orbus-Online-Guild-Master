// Shared trait badge component
const TRAIT_POSITIVE_COLOR = "#22c55e";
const TRAIT_NEGATIVE_COLOR = "#ef4444";

const formatTraitEffect = (t) => {
    if (!t) return "";
    const val = t.modifier_value;
    if (t.modifier_type === "flat") {
        const sign = val >= 0 ? "+" : "";
        return `${sign}${val} ${t.affected_stat}`;
    }
    if (t.modifier_type === "percent") {
        const sign = val >= 0 ? "+" : "";
        return `${sign}${val}% ${t.affected_stat}`;
    }
    return `${val} ${t.affected_stat}`;
};

export const TraitBadge = ({ trait }) => {
    const positive = !!trait?.is_positive;
    const color = positive ? TRAIT_POSITIVE_COLOR : TRAIT_NEGATIVE_COLOR;
    return (
        <span
            data-testid={`trait-${trait?.name?.toLowerCase().replace(/\s+/g, "-")}`}
            title={formatTraitEffect(trait)}
            className="inline-block text-[10px] tracking-wider border px-1.5 py-0.5 rounded-sm"
            style={{ color, borderColor: color + "55" }}
        >
            {trait?.name} <span className="opacity-70">{formatTraitEffect(trait)}</span>
        </span>
    );
};

export const TraitList = ({ traits, testid }) => {
    if (!traits || traits.length === 0) {
        return <span className="text-[10px] text-muted-foreground italic">no traits</span>;
    }
    return (
        <div data-testid={testid} className="flex flex-wrap gap-1">
            {traits.map((t) => (
                <TraitBadge key={t.id || t.name} trait={t} />
            ))}
        </div>
    );
};
