// ROUND 6A.2b — Centralized trait label resolver.
//
// Single source of truth for "what to show for a trait" across every UI
// surface (roster, recruitment, raid builder, expedition picker, equip
// modal, admin panel). Prefers IT translation when present, falls back to
// EN display, then raw `name`, finally a visible em-dash so the row is
// never silently blank.
export function getTraitLabel(trait) {
    if (!trait) return "—";
    return (
        trait.display_name_it
        || trait.display_name
        || trait.display_name_en
        || trait.name
        || "—"
    );
}
