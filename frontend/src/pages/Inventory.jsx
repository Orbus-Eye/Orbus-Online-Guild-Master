import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import { toast } from "sonner";
import AppHeader from "../components/AppHeader";
import { Button } from "../components/ui/button";

const RARITY_COLOR = {
    Common: "#9ca3af",
    Uncommon: "#22c55e",
    Rare: "#3b82f6",
    Epic: "#a855f7",
};

const RarityBadge = ({ rarity }) => (
    <span
        className="inline-block text-[10px] tracking-widest border px-1.5 py-0.5 rounded-sm"
        style={{
            color: RARITY_COLOR[rarity] || RARITY_COLOR.Common,
            borderColor: (RARITY_COLOR[rarity] || RARITY_COLOR.Common) + "55",
        }}
    >
        {rarity?.toUpperCase()}
    </span>
);

const TypeBadge = ({ t }) => (
    <span className="inline-block text-[10px] tracking-widest border border-border bg-secondary text-muted-foreground px-1.5 py-0.5 rounded-sm">
        {t?.toUpperCase()}
    </span>
);

export default function Inventory() {
    const [rows, setRows] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        (async () => {
            try {
                const { data } = await api.get("/inventory");
                setRows(data.inventory);
            } catch (err) {
                toast.error(formatApiError(err));
                setRows([]);
            } finally {
                setLoading(false);
            }
        })();
    }, []);

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg">
            <AppHeader subtitle="VAULT" />

            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
                <div className="flex items-end justify-between gap-3 mb-6 flex-wrap">
                    <div>
                        <div className="text-xs text-amber tracking-widest mb-2">
                            :: GUILD VAULT
                        </div>
                        <h1 className="text-3xl font-semibold tracking-tight">Inventory</h1>
                        <p className="text-sm text-muted-foreground mt-2 max-w-2xl">
                            Items recovered from dungeon expeditions.
                        </p>
                    </div>
                    <div className="text-right">
                        <div className="text-[10px] text-muted-foreground tracking-widest">
                            STACKS
                        </div>
                        <div
                            data-testid="inventory-stack-count"
                            className="text-2xl font-semibold text-amber"
                        >
                            {rows?.length ?? "—"}
                        </div>
                    </div>
                </div>

                {loading && (
                    <div className="text-xs text-muted-foreground">
                        loading<span className="caret-blink" />
                    </div>
                )}

                {!loading && rows && rows.length === 0 && (
                    <div
                        data-testid="inventory-empty"
                        className="border border-border bg-card rounded-sm p-10 text-center"
                    >
                        <div className="text-amber text-xs tracking-widest mb-2">
                            :: VAULT EMPTY
                        </div>
                        <p className="text-sm text-muted-foreground mb-5 max-w-md mx-auto">
                            Your vault is empty. Complete expeditions to find loot.
                        </p>
                        <Link to="/dungeons">
                            <Button
                                data-testid="inventory-goto-dungeons"
                                className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm"
                            >
                                Go to Dungeons →
                            </Button>
                        </Link>
                    </div>
                )}

                {!loading && rows && rows.length > 0 && (
                    <>
                        {/* desktop table */}
                        <div className="hidden sm:block border border-border rounded-sm overflow-x-auto">
                            <table data-testid="inventory-table" className="w-full text-sm min-w-[640px]">
                                <thead className="bg-secondary/40 text-[10px] text-muted-foreground tracking-widest">
                                    <tr>
                                        <th className="text-left px-3 py-2 font-normal border-b border-border">NAME</th>
                                        <th className="text-left px-3 py-2 font-normal border-b border-border">RARITY</th>
                                        <th className="text-left px-3 py-2 font-normal border-b border-border">TYPE</th>
                                        <th className="text-left px-3 py-2 font-normal border-b border-border">QTY</th>
                                        <th className="text-left px-3 py-2 font-normal border-b border-border">POWER</th>
                                        <th className="text-left px-3 py-2 font-normal border-b border-border">DESCRIPTION</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {rows.map((r) => {
                                        const it = r.item;
                                        return (
                                            <tr
                                                key={r.id}
                                                data-testid={`inventory-row-${r.id}`}
                                                className="border-b border-border/60 hover:bg-secondary/20"
                                            >
                                                <td className="px-3 py-2 font-medium whitespace-nowrap">{it?.name || "—"}</td>
                                                <td className="px-3 py-2 whitespace-nowrap"><RarityBadge rarity={it?.rarity} /></td>
                                                <td className="px-3 py-2 whitespace-nowrap"><TypeBadge t={it?.item_type} /></td>
                                                <td className="px-3 py-2">×{r.quantity}</td>
                                                <td className="px-3 py-2">{it?.power_score ?? 0}</td>
                                                <td className="px-3 py-2 text-muted-foreground text-xs">{it?.description}</td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>

                        {/* mobile stacked cards */}
                        <div className="sm:hidden space-y-3" data-testid="inventory-cards">
                            {rows.map((r) => {
                                const it = r.item;
                                return (
                                    <div
                                        key={r.id}
                                        data-testid={`inventory-card-${r.id}`}
                                        className="border border-border bg-card rounded-sm p-4"
                                    >
                                        <div className="flex items-start justify-between gap-2 mb-2">
                                            <div className="min-w-0">
                                                <div className="font-medium truncate">{it?.name || "—"}</div>
                                                <div className="text-[11px] text-muted-foreground mt-0.5">
                                                    {it?.item_type} · power {it?.power_score ?? 0}
                                                </div>
                                            </div>
                                            <div className="flex flex-col items-end gap-1">
                                                <RarityBadge rarity={it?.rarity} />
                                                <span className="text-xs text-amber">×{r.quantity}</span>
                                            </div>
                                        </div>
                                        {it?.description && (
                                            <p className="text-[11px] text-muted-foreground mt-2">
                                                {it.description}
                                            </p>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </>
                )}
            </main>
        </div>
    );
}
