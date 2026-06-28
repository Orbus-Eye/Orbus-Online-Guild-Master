/**
 * Phase 19.4b — Mercato di Sistema NPC (replaces old player-to-player Market).
 *
 * Tab 1: COMPRA → daily offers grid + buy button + countdown reset
 * Tab 2: VENDI  → inventory dropdown + sell confirm modal
 *
 * Server-authoritative pricing/stock. Player-to-player listing UI is now
 * at `/auction`. Old `/api/market/listings*` calls now 307-redirect to
 * `/api/auction/*` automatically.
 */
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";

import { api, formatApiError, formatErrorDetail } from "../lib/api";
import AppHeader from "../components/AppHeader";
import { Button } from "../components/ui/button";

function relativeCountdown(targetIso) {
    if (!targetIso) return "";
    const ms = new Date(targetIso).getTime() - Date.now();
    if (ms <= 0) return "ora";
    const h = Math.floor(ms / 3_600_000);
    const m = Math.floor((ms % 3_600_000) / 60_000);
    return `${h}h ${m}m`;
}

const RarityBadge = ({ value }) => {
    const color = {
        Common: "#9ca3af",
        Uncommon: "#22c55e",
        Rare: "#3b82f6",
        Epic: "#a855f7",
        Legendary: "#f59e0b",
    }[value] || "#9ca3af";
    return (
        <span
            className="inline-block text-[10px] tracking-widest border px-1.5 py-0.5 rounded-sm"
            style={{ color, borderColor: color + "55" }}
        >
            {(value || "common").toUpperCase()}
        </span>
    );
};

export default function Market() {
    const [tab, setTab] = useState("buy"); // buy | sell
    const [offers, setOffers] = useState([]);
    const [nextResetAt, setNextResetAt] = useState(null);
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(false);

    // Sell state
    const [inventory, setInventory] = useState([]);
    const [selectedRow, setSelectedRow] = useState(null);
    const [sellQty, setSellQty] = useState(1);
    const [confirmOpen, setConfirmOpen] = useState(false);
    const [guildGold, setGuildGold] = useState(null);

    const loadOffers = useCallback(async () => {
        setLoading(true);
        try {
            const { data } = await api.get("/shop/daily_offers");
            setOffers(data.offers || []);
            setNextResetAt(data.next_reset_at);
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setLoading(false);
        }
    }, []);

    const loadGuild = useCallback(async () => {
        try {
            const { data } = await api.get("/guilds/me");
            setGuildGold(data.guild?.gold ?? null);
        } catch { /* silent */ }
    }, []);

    const loadInventory = useCallback(async () => {
        try {
            const { data } = await api.get("/inventory");
            // P19.4a fix carry-over: read `data.inventory` key (NOT `data.items`)
            const rows = (data.inventory || []).filter((r) => {
                const tradeable = r.item?.is_tradeable !== false
                    && r.item?.can_be_sold_for_gold !== false;
                return r.is_bound !== true
                    && (r.available_quantity ?? r.quantity ?? 0) > 0
                    && tradeable;
            });
            setInventory(rows);
        } catch (err) {
            toast.error(formatApiError(err));
        }
    }, []);

    useEffect(() => {
        loadOffers();
        loadGuild();
    }, [loadOffers, loadGuild]);
    useEffect(() => {
        if (tab === "sell") loadInventory();
    }, [tab, loadInventory]);

    async function buyOffer(offer) {
        if (busy) return;
        setBusy(true);
        try {
            const { data } = await api.post("/shop/buy", {
                offer_id: offer.offer_id, quantity: 1,
            });
            toast.success(`Acquistato ${offer.item.name} ×1 (−${data.gold_spent} gold)`);
            setGuildGold(data.guild_gold);
            await loadOffers();
        } catch (err) {
            const detail = err?.response?.data?.detail;
            const status = err?.response?.status;
            if (status === 402) toast.error("Oro insufficiente.");
            else if (status === 409) toast.error("Offerta esaurita.");
            else if (status === 410) toast.error("Offerta scaduta. Aggiorna la pagina.");
            else if (status === 429) toast.error("Rallenta un attimo.");
            else if (detail) toast.error(formatErrorDetail(detail));
            else toast.error(formatApiError(err));
        } finally {
            setBusy(false);
        }
    }

    async function confirmSell() {
        if (!selectedRow || busy) return;
        setBusy(true);
        try {
            const { data } = await api.post("/shop/sell", {
                instance_id: selectedRow.instance_id || selectedRow.id,
                quantity: sellQty,
            });
            toast.success(`Venduto ${data.item_sold.name} ×${data.quantity} (+${data.gold_earned} gold)`);
            setGuildGold(data.guild_gold);
            setConfirmOpen(false);
            setSelectedRow(null);
            setSellQty(1);
            await loadInventory();
        } catch (err) {
            const detail = err?.response?.data?.detail;
            const status = err?.response?.status;
            if (status === 409 && detail?.startsWith("shop.sell.")) {
                const reason = {
                    "market.bound_to_adventurer_not_sellable": "Oggetto bound — non vendibile.",
                    "shop.sell.bound": "Oggetto bound — non vendibile.",
                    "shop.sell.equipped": "Oggetto equipaggiato — rimuovi prima.",
                    "shop.sell.listed": "Oggetto già in Asta.",
                    "shop.sell.not_tradeable": "Oggetto non commerciabile.",
                    "shop.sell.no_stock": "Stock insufficiente.",
                }[detail] || detail;
                toast.error(reason);
            } else if (status === 429) toast.error("Rallenta un attimo.");
            else toast.error(detail || formatApiError(err));
        } finally {
            setBusy(false);
        }
    }

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg">
            <AppHeader subtitleKey="nav.market" />
            <main className="max-w-5xl mx-auto px-4 sm:px-6 py-6">
                <div className="text-xs text-amber tracking-widest mb-2">:: MERCATO DI SISTEMA</div>
                <div className="flex items-start justify-between gap-3 mb-4 flex-wrap">
                    <div>
                        <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight">Mercato</h1>
                        <p className="text-xs text-muted-foreground mt-1 max-w-2xl">
                            Negozio gestito dal Mastro Mercante. Offerte giornaliere che ruotano alle <strong>04:00 UTC</strong>.
                            Per vendere a un altro giocatore vai all&apos;<Link to="/auction" className="underline">Asta</Link>.
                        </p>
                    </div>
                    <div className="text-right">
                        <div className="text-[10px] tracking-widest text-muted-foreground">ORO GILDA</div>
                        <div className="text-amber text-xl font-medium tabular-nums" data-testid="shop-guild-gold">
                            {guildGold !== null ? guildGold : "—"}
                        </div>
                    </div>
                </div>

                <div className="flex gap-1 mb-4 border-b border-border/60">
                    <button
                        type="button"
                        data-testid="shop-tab-buy"
                        onClick={() => setTab("buy")}
                        className={"px-3 py-2 text-xs tracking-widest border-b-2 " + (tab === "buy" ? "border-amber text-amber" : "border-transparent text-muted-foreground")}
                    >
                        COMPRA
                    </button>
                    <button
                        type="button"
                        data-testid="shop-tab-sell"
                        onClick={() => setTab("sell")}
                        className={"px-3 py-2 text-xs tracking-widest border-b-2 " + (tab === "sell" ? "border-amber text-amber" : "border-transparent text-muted-foreground")}
                    >
                        VENDI AL MERCATO
                    </button>
                </div>

                {tab === "buy" && (
                    <>
                        <div className="text-[11px] text-muted-foreground mb-3 flex items-center justify-between">
                            <span data-testid="shop-daily-offers">Offerte giornaliere ({offers.length})</span>
                            <span data-testid="shop-countdown">
                                Reset tra <strong>{relativeCountdown(nextResetAt)}</strong>
                            </span>
                        </div>
                        {loading && <div className="text-xs text-muted-foreground">Caricamento…</div>}
                        {!loading && offers.length === 0 && (
                            <div className="border border-border bg-card rounded-sm p-6 text-center text-xs text-muted-foreground">
                                Nessuna offerta disponibile oggi. Torna alle 04:00 UTC.
                            </div>
                        )}
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                            {offers.map((o) => (
                                <div
                                    key={o.offer_id}
                                    data-testid={`shop-offer-card-${o.offer_id}`}
                                    className="border border-border bg-card rounded-sm p-4 flex flex-col"
                                >
                                    <div className="flex items-start justify-between gap-2 mb-2">
                                        <div className="font-medium text-sm">{o.item.name}</div>
                                        <RarityBadge value={o.item.rarity} />
                                    </div>
                                    <div className="text-[11px] text-muted-foreground mb-3">
                                        {o.item.item_type} · liv. {o.item.level_required}
                                    </div>
                                    <div className="flex items-center justify-between mb-3 text-xs">
                                        <span>Prezzo: <strong className="text-amber">{o.buy_price} oro</strong></span>
                                        <span className="text-muted-foreground">stock: {o.stock_remaining}/{o.max_quantity}</span>
                                    </div>
                                    <Button
                                        type="button"
                                        data-testid={`shop-buy-btn-${o.offer_id}`}
                                        disabled={busy || o.stock_remaining < 1 || (guildGold !== null && guildGold < o.buy_price)}
                                        onClick={() => buyOffer(o)}
                                        className="h-8 px-3 text-xs bg-amber text-black hover:bg-amber/80 rounded-sm disabled:opacity-40"
                                    >
                                        {o.stock_remaining < 1 ? "Esaurito" :
                                            (guildGold !== null && guildGold < o.buy_price) ? "Oro insuff." : "▶ Compra ×1"}
                                    </Button>
                                </div>
                            ))}
                        </div>
                    </>
                )}

                {tab === "sell" && (
                    <>
                        <p className="text-[11px] text-muted-foreground mb-3">
                            Vendi al Mercato di Sistema. Prezzo = 40% del prezzo d&apos;acquisto. Niente trattativa,
                            niente attesa. Item bound/equipaggiati/in Asta sono esclusi.
                        </p>
                        {inventory.length === 0 ? (
                            <div
                                data-testid="shop-sell-empty"
                                className="border border-border bg-card rounded-sm p-6 text-center text-xs text-muted-foreground"
                            >
                                Nessun oggetto vendibile nel deposito.
                            </div>
                        ) : (
                            <div className="border border-border bg-card rounded-sm divide-y divide-border/40">
                                {inventory.map((r) => (
                                    <div
                                        key={r.id}
                                        data-testid={`shop-sell-row-${r.id}`}
                                        className="flex items-center justify-between gap-3 px-4 py-2 text-xs"
                                    >
                                        <div className="flex items-center gap-2 flex-1">
                                            <RarityBadge value={r.item.rarity} />
                                            <span className="font-medium">{r.item.name}</span>
                                            <span className="text-muted-foreground">×{r.available_quantity ?? r.quantity}</span>
                                        </div>
                                        <Button
                                            type="button"
                                            data-testid={`shop-sell-open-${r.id}`}
                                            onClick={() => { setSelectedRow(r); setSellQty(1); setConfirmOpen(true); }}
                                            className="h-7 px-3 text-[11px] bg-amber/80 text-black hover:bg-amber rounded-sm"
                                        >
                                            Vendi
                                        </Button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </>
                )}

                {/* Sell confirm modal */}
                {confirmOpen && selectedRow && (
                    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
                        <div className="bg-card border border-amber rounded-sm max-w-sm w-full p-5" data-testid="shop-sell-confirm">
                            <div className="text-xs text-amber tracking-widest mb-2">:: CONFERMA VENDITA</div>
                            <div className="text-sm mb-4">
                                Vendere <strong>{selectedRow.item.name}</strong> ×<strong>{sellQty}</strong>?
                            </div>
                            <div className="flex items-center gap-2 mb-4 text-xs">
                                <label>Quantità:</label>
                                <input
                                    type="number" min="1"
                                    max={selectedRow.available_quantity ?? selectedRow.quantity ?? 1}
                                    value={sellQty}
                                    onChange={(e) => setSellQty(Math.max(1, Math.min(99, parseInt(e.target.value) || 1)))}
                                    data-testid="shop-sell-qty"
                                    className="w-20 bg-background border border-border rounded-sm px-2 py-1"
                                />
                            </div>
                            <div className="flex justify-end gap-2">
                                <Button
                                    type="button"
                                    onClick={() => { setConfirmOpen(false); setSelectedRow(null); }}
                                    className="h-8 px-3 text-xs bg-secondary text-foreground hover:bg-secondary/80 rounded-sm"
                                >
                                    Annulla
                                </Button>
                                <Button
                                    type="button"
                                    data-testid="shop-sell-confirm-btn"
                                    disabled={busy}
                                    onClick={confirmSell}
                                    className="h-8 px-3 text-xs bg-amber text-black hover:bg-amber/80 rounded-sm disabled:opacity-50"
                                >
                                    Conferma
                                </Button>
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
