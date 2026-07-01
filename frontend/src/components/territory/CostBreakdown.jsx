// ROUND 11.2 EXT-2 — Per-card cost preview for Territory upgrades.
//
// Renders gold + materials required vs. owned with ✅/❌ markers.
// Materials are click-targets that open `MaterialSourceModal` via the
// `onMaterialClick(slug)` callback hoisted in `Territory.jsx`.
//
// Data contract (mirrors `territory.services._enrich_territory_with_inventory`):
//   nextLevelCost = {
//     target_level: int,
//     gold: int,                                  // required
//     owned_gold: int,
//     can_afford: bool,
//     materials: { [slug]: required_qty },        // flat map
//     materials_detail: [                          // enriched
//       { slug, display_name_it, display_name_en, required, owned, missing }
//     ],
//     missing: { gold: int, materials: [{ slug, display_name_it, missing }] }
//   }
//
// `null` (no upgrade available — max level or legacy) → renders nothing.
import { memo } from "react";

function Row({ ok, label, value, onClick, testid }) {
    const Tag = onClick ? "button" : "div";
    return (
        <Tag
            type={onClick ? "button" : undefined}
            onClick={onClick}
            data-testid={testid}
            className={`flex items-center justify-between gap-2 w-full text-left text-[11px] py-1 px-2 rounded-sm ${
                onClick
                    ? "hover:bg-amber/10 hover:text-amber transition-colors cursor-pointer"
                    : ""
            }`}
        >
            <span className="flex items-center gap-1.5 min-w-0">
                <span
                    aria-hidden="true"
                    className={ok ? "text-emerald-400" : "text-red-400"}
                >
                    {ok ? "✅" : "❌"}
                </span>
                <span className="truncate">{label}</span>
            </span>
            <span
                className={`font-mono shrink-0 ${ok ? "text-foreground" : "text-red-400"}`}
            >
                {value}
            </span>
        </Tag>
    );
}

function CostBreakdownBase({ nextLevelCost, lang = "it", onMaterialClick, slug }) {
    if (!nextLevelCost) return null;

    const goldReq = Number(nextLevelCost.gold || 0);
    const goldOwned = Number(nextLevelCost.owned_gold || 0);
    const goldOk = goldOwned >= goldReq;

    const details = Array.isArray(nextLevelCost.materials_detail)
        ? nextLevelCost.materials_detail
        : [];

    const labels = lang === "it"
        ? { title: "Costo prossimo livello", gold: "Oro", needed: "Ti mancano" }
        : { title: "Next level cost", gold: "Gold", needed: "Missing" };

    const missingGold = Number(nextLevelCost?.missing?.gold || 0);
    const missingMats = Array.isArray(nextLevelCost?.missing?.materials)
        ? nextLevelCost.missing.materials
        : [];

    return (
        <div
            data-testid={`territory-cost-breakdown${slug ? `-${slug}` : ""}`}
            className="mt-2 border border-border/60 bg-background/40 rounded-sm py-2"
        >
            <div className="px-2 pb-1 text-[10px] tracking-widest text-muted-foreground">
                {labels.title} — Lv{nextLevelCost.target_level || ""}
            </div>
            <Row
                ok={goldOk}
                label={labels.gold}
                value={`${goldOwned}/${goldReq}`}
                testid={`cost-row-gold${slug ? `-${slug}` : ""}`}
            />
            {details.map((m) => {
                const ok = Number(m.owned || 0) >= Number(m.required || 0);
                const display = lang === "it"
                    ? (m.display_name_it || m.slug)
                    : (m.display_name_en || m.display_name_it || m.slug);
                return (
                    <Row
                        key={m.slug}
                        ok={ok}
                        label={display}
                        value={`${m.owned || 0}/${m.required || 0}`}
                        onClick={onMaterialClick ? () => onMaterialClick(m.slug) : undefined}
                        testid={`cost-row-mat-${m.slug}${slug ? `-${slug}` : ""}`}
                    />
                );
            })}
            {nextLevelCost.can_afford === false && (
                <div
                    className="mt-1 px-2 pt-1 border-t border-border/60 text-[10px] text-red-400"
                    data-testid={`cost-missing-summary${slug ? `-${slug}` : ""}`}
                >
                    {labels.needed}:{" "}
                    {missingGold > 0 && (
                        <span className="mr-2">{missingGold}g</span>
                    )}
                    {missingMats.map((m) => (
                        <span key={m.slug} className="mr-2">
                            {m.missing}× {m.display_name_it || m.slug}
                        </span>
                    ))}
                </div>
            )}
        </div>
    );
}

const CostBreakdown = memo(CostBreakdownBase);
export default CostBreakdown;
export { CostBreakdownBase };
