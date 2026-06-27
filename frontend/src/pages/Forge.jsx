// ROUND 4 — Forge / Workshop page (MVP minimale per kick-off preview).
// 4 tab: Refine / Enchant / Reroll / Disenchant. Server-authoritative.
import { useEffect, useState, useCallback } from "react";
import { api, formatApiError } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { useT } from "../i18n/I18nContext";
import AppHeader from "../components/AppHeader";
import { toast } from "sonner";


const TABS = [
    { key: "refine",     i18n: "forge.tab_refine" },
    { key: "enchant",    i18n: "forge.tab_enchant" },
    { key: "reroll",     i18n: "forge.tab_reroll" },
    { key: "disenchant", i18n: "forge.tab_disenchant" },
];


export default function Forge() {
    const { user, guild } = useAuth();
    const { t } = useT();
    const [tab, setTab] = useState("refine");
    const [inv, setInv] = useState([]);
    const [items, setItems] = useState({});
    const [selected, setSelected] = useState(null);
    const [busy, setBusy] = useState(false);
    const [enchOptions, setEnchOptions] = useState(null);

    const load = useCallback(async () => {
        try {
            const [{ data: invRes }, { data: itemsRes }] = await Promise.all([
                api.get("/inventory"),
                api.get("/items"),
            ]);
            const itemsList = invRes.items || invRes.inventory || invRes || [];
            setInv(Array.isArray(itemsList) ? itemsList : []);
            const map = {};
            (itemsRes.items || itemsRes || []).forEach((it) => { map[it.id] = it; });
            setItems(map);
        } catch (err) {
            toast.error(formatApiError(err));
        }
    }, []);

    useEffect(() => { if (user && guild) load(); }, [user, guild, load]);

    if (!user || !guild) return null;

    const eligibleItems = inv.filter((r) => {
        const it = items[r.item_id];
        if (!it) return false;
        if (it.item_type === "material" || it.item_type === "consumable") return false;
        if (r.disenchanted_at) return false;
        if (tab === "reroll") return (r.affixes || []).length > 0;
        return true;
    });

    const onAction = async () => {
        if (!selected) return;
        const iid = selected.instance_id || selected.id;
        setBusy(true);
        try {
            if (tab === "refine") {
                const { data } = await api.post(`/inventory/${iid}/refine`);
                toast.success(data.success
                    ? t("forge.refine_success", { lvl: data.refinement_level })
                    : t("forge.refine_failed"));
                await load();
                setSelected(null);
            } else if (tab === "enchant") {
                if (!enchOptions) {
                    const { data } = await api.post(`/inventory/${iid}/enchant-options`);
                    setEnchOptions(data.options || []);
                } else {
                    toast.info(t("forge.enchant_pick_option"));
                }
            } else if (tab === "reroll") {
                const { data } = await api.post(`/inventory/${iid}/reroll-affixes`);
                toast.success(t("forge.reroll_success", { n: data.reroll_count }));
                await load();
            } else if (tab === "disenchant") {
                const { data } = await api.post(`/inventory/${iid}/disenchant`);
                const mats = [...(data.materials_guaranteed || []), ...(data.materials_bonus || [])]
                    .map((m) => `${m.qty}×${m.slug}`).join(", ");
                toast.success(t("forge.disenchant_success", { mats }));
                await load();
                setSelected(null);
            }
        } catch (err) {
            toast.error(formatApiError(err));
        } finally { setBusy(false); }
    };

    const applyEnchant = async (slug) => {
        if (!selected) return;
        const iid = selected.instance_id || selected.id;
        setBusy(true);
        try {
            await api.post(`/inventory/${iid}/enchant`, { enchant_slug: slug });
            toast.success(t("forge.enchant_applied"));
            setEnchOptions(null);
            await load();
            setSelected(null);
        } catch (err) {
            toast.error(formatApiError(err));
        } finally { setBusy(false); }
    };

    return (
        <div className="min-h-screen bg-background text-foreground">
            <AppHeader />
            <main className="max-w-5xl mx-auto px-4 py-6 font-mono">
                <header className="mb-6">
                    <h1 data-testid="forge-title" className="text-amber text-xl tracking-widest">:: {t("forge.title")}</h1>
                    <p className="text-[11px] text-muted-foreground mt-1">{t("forge.intro")}</p>
                </header>
                <div className="flex gap-1 border-b border-border/40 mb-4 overflow-x-auto">
                    {TABS.map((tb) => (
                        <button
                            key={tb.key}
                            data-testid={`forge-tab-${tb.key}`}
                            onClick={() => { setTab(tb.key); setSelected(null); setEnchOptions(null); }}
                            className={"text-[10px] tracking-widest px-3 py-2 " +
                                (tab === tb.key ? "text-amber border-b-2 border-amber" : "text-muted-foreground hover:text-foreground")}
                        >{t(tb.i18n)}
                        </button>
                    ))}
                </div>
                <div className="grid md:grid-cols-2 gap-4">
                    <section data-testid="forge-item-list" className="border border-border/60 bg-card/40 rounded-sm p-3">
                        <div className="text-amber tracking-widest text-[11px] mb-2">:: {t("forge.select_item")}</div>
                        {eligibleItems.length === 0 ? (
                            <div className="text-[11px] text-muted-foreground italic">:: {t("forge.no_eligible")}</div>
                        ) : (
                            <ul className="space-y-1 max-h-[60vh] overflow-y-auto">
                                {eligibleItems.map((r) => {
                                    const it = items[r.item_id];
                                    const iid = r.instance_id || r.id;
                                    return (
                                        <li key={iid}>
                                            <button
                                                data-testid={`forge-item-${iid}`}
                                                onClick={() => { setSelected(r); setEnchOptions(null); }}
                                                className={"w-full text-left text-[11px] px-2 py-1.5 border-l-2 " +
                                                    (selected?.instance_id === r.instance_id ? "border-amber bg-amber/5" : "border-border/40 hover:border-amber/40")}
                                            >
                                                <div className="text-foreground/90">{it.name} {r.refinement_level > 0 ? `+${r.refinement_level}` : ""}</div>
                                                <div className="text-[10px] text-muted-foreground">
                                                    {it.rarity} · {it.item_type}
                                                    {r.is_bound ? <span className="ml-2 text-amber">[BOUND]</span> : null}
                                                </div>
                                            </button>
                                        </li>
                                    );
                                })}
                            </ul>
                        )}
                    </section>
                    <section className="border border-border/60 bg-card/40 rounded-sm p-3">
                        <div className="text-amber tracking-widest text-[11px] mb-2">:: {t("forge.operation_panel")}</div>
                        {!selected ? (
                            <div className="text-[11px] text-muted-foreground italic">:: {t("forge.pick_one")}</div>
                        ) : (
                            <div className="text-[12px] space-y-2">
                                <div className="text-foreground">{items[selected.item_id]?.name}</div>
                                {tab === "refine" && (
                                    <div className="text-[10px] text-muted-foreground">{t("forge.refine_hint", { lvl: selected.refinement_level })}</div>
                                )}
                                {tab === "enchant" && enchOptions && (
                                    <ul className="space-y-1" data-testid="forge-enchant-options">
                                        {enchOptions.map((e) => (
                                            <li key={e.slug}>
                                                <button
                                                    data-testid={`forge-enchant-option-${e.slug}`}
                                                    onClick={() => applyEnchant(e.slug)}
                                                    disabled={busy}
                                                    className="w-full text-left text-[11px] px-2 py-1 border border-border/60 rounded-sm hover:border-amber"
                                                >
                                                    <span className="text-foreground/90">{e.name}</span>
                                                    <span className="text-muted-foreground ml-2">{e.rarity} · +{e.bonus_value} {e.bonus_stat} · {e.cost_gold}g</span>
                                                </button>
                                            </li>
                                        ))}
                                    </ul>
                                )}
                                {tab === "disenchant" && (
                                    <div className="text-[10px] text-red-400/80">{t("forge.disenchant_warning")}</div>
                                )}
                                <div className="text-[10px] text-amber pt-2 border-t border-border/30">
                                    ⚠ {t("forge.boe_warning")}
                                </div>
                                <button
                                    data-testid={`forge-confirm-${tab}`}
                                    onClick={onAction}
                                    disabled={busy}
                                    className="text-[10px] tracking-widest px-3 py-1.5 border border-amber text-amber rounded-sm hover:bg-amber/10 disabled:opacity-50"
                                >
                                    {busy ? "…" : t(`forge.confirm_${tab}`)}
                                </button>
                            </div>
                        )}
                    </section>
                </div>
            </main>
        </div>
    );
}
