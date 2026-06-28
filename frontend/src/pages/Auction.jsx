/* Phase 14.8 (ROUND 3.C) — Marketplace page.

Three tabs:
  • Buy   → public listings with filters & sort
  • Sell  → form to list one of your sellable items
  • Mine  → your own listings (active + history)
*/
import { useEffect, useMemo, useState, useCallback } from "react";
import { toast } from "sonner";

import AppHeader from "../components/AppHeader";
import { useAuth } from "../context/AuthContext";
import { useT } from "../i18n/I18nContext";
// ROUND 6B.3 Wave 3 — FIX BUG 2: normalise fetch-based error details to
// a string so `toast.error(...)` never renders `[object Object]` when the
// backend returns a structured `detail` payload (Pydantic list / dict).
import { formatErrorDetail } from "../lib/api";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

const RARITY_COLOR = {
    Common: "text-muted-foreground",
    Uncommon: "text-emerald-300",
    Rare: "text-sky-300",
    Epic: "text-fuchsia-300",
    Legendary: "text-amber-300",
};

const Pill = ({ children, className = "" }) => (
    <span className={`px-2 py-0.5 text-xs rounded-sm border border-border ${className}`}>
        {children}
    </span>
);

const SectionTitle = ({ children }) => (
    <h2 className="text-xs tracking-widest text-muted-foreground uppercase mb-3">
        {children}
    </h2>
);

// ROUND 11.1 Slice 2 — `authedFetch` re-implemented on top of the
// centralized axios `api` wrapper. The `token` parameter is now unused
// (cookie auth + CSRF interceptors handle auth) but retained in the
// signature so existing call sites do not need to change. Returns a
// `Response`-like object with `.ok`, `.status`, `.json()`.
async function authedFetch(_token, path, init = {}) {
    const method = (init.method || "GET").toUpperCase();
    const body = init.body ? JSON.parse(init.body) : undefined;
    try {
        const r = await api.request({
            url: path, method,
            data: body,
            headers: init.headers,
        });
        return { ok: true, status: r.status, json: async () => r.data };
    } catch (e) {
        const status = e?.response?.status || 0;
        const data = e?.response?.data;
        return { ok: false, status, json: async () => data };
    }
}

// ─── BUY TAB ─────────────────────────────────────────────────────────────
function BuyTab({ token, lang, t, refreshGuild, myUserId, myGuildId, myGuildGold }) {
    const [listings, setListings] = useState([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(false);
    const [filters, setFilters] = useState({
        item_type: "", rarity: "", level_max: "", price_max: "",
        name_contains: "", sort_by: "created_at",
    });
    const [confirmId, setConfirmId] = useState(null);
    const [buyQty, setBuyQty] = useState(1);

    const load = useCallback(async () => {
        setLoading(true);
        const qs = new URLSearchParams({ lang, sort_by: filters.sort_by, limit: "50" });
        for (const k of ["item_type", "rarity", "level_max", "price_max", "name_contains"]) {
            if (filters[k] !== "" && filters[k] != null) qs.set(k, filters[k]);
        }
        const r = await fetch(`${API}/auction/listings?${qs}`);
        if (r.ok) {
            const body = await r.json();
            setListings(body.listings || []);
            setTotal(body.total || 0);
        }
        setLoading(false);
    }, [filters, lang]);

    useEffect(() => { load(); }, [load]);

    async function doBuy(listing) {
        const r = await authedFetch(token, `/auction/listings/${listing.id}/buy?lang=${lang}`, {
            method: "POST",
            body: JSON.stringify({ quantity: buyQty }),
        });
        const body = await r.json().catch(() => ({}));
        if (r.ok && body.success) {
            const itemName = body.item_received?.name || listing.item.name;
            toast.success(`${t("auction.toast_bought")}: ${body.item_received?.quantity}× ${itemName} — ${body.gold_spent}g`);
            setConfirmId(null);
            setBuyQty(1);
            await load();
            await refreshGuild();
        } else {
            toast.error(formatErrorDetail(body.detail) || "Errore");
        }
    }

    return (
        <div className="space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 text-xs"
                 data-testid="market-buy-filters">
                <select
                    data-testid="market-filter-type"
                    className="bg-secondary border border-border rounded-sm px-2 py-1.5"
                    value={filters.item_type}
                    onChange={(e) => setFilters((f) => ({ ...f, item_type: e.target.value }))}
                >
                    <option value="">{t("market.filter_type")}</option>
                    <option value="weapon">weapon</option>
                    <option value="armor">armor</option>
                    <option value="accessory">accessory</option>
                    <option value="material">material</option>
                    <option value="consumable">consumable</option>
                </select>
                <select
                    data-testid="market-filter-rarity"
                    className="bg-secondary border border-border rounded-sm px-2 py-1.5"
                    value={filters.rarity}
                    onChange={(e) => setFilters((f) => ({ ...f, rarity: e.target.value }))}
                >
                    <option value="">{t("market.filter_rarity")}</option>
                    {["Common", "Uncommon", "Rare", "Epic", "Legendary"].map((r) => (
                        <option key={r} value={r}>{r}</option>
                    ))}
                </select>
                <input
                    data-testid="market-filter-level"
                    type="number" min="1" placeholder={t("market.filter_level_max")}
                    className="bg-secondary border border-border rounded-sm px-2 py-1.5"
                    value={filters.level_max}
                    onChange={(e) => setFilters((f) => ({ ...f, level_max: e.target.value }))}
                />
                <input
                    data-testid="market-filter-price"
                    type="number" min="0" placeholder={t("market.filter_price_max")}
                    className="bg-secondary border border-border rounded-sm px-2 py-1.5"
                    value={filters.price_max}
                    onChange={(e) => setFilters((f) => ({ ...f, price_max: e.target.value }))}
                />
                <input
                    data-testid="market-filter-search"
                    placeholder={t("market.filter_search")}
                    className="bg-secondary border border-border rounded-sm px-2 py-1.5"
                    value={filters.name_contains}
                    onChange={(e) => setFilters((f) => ({ ...f, name_contains: e.target.value }))}
                />
                <select
                    data-testid="market-filter-sort"
                    className="bg-secondary border border-border rounded-sm px-2 py-1.5"
                    value={filters.sort_by}
                    onChange={(e) => setFilters((f) => ({ ...f, sort_by: e.target.value }))}
                >
                    <option value="created_at">{t("market.sort_created_at")}</option>
                    <option value="price_asc">{t("market.sort_price_asc")}</option>
                    <option value="price_desc">{t("market.sort_price_desc")}</option>
                    <option value="level">{t("market.sort_level")}</option>
                </select>
            </div>

            {loading && <p className="text-muted-foreground text-xs">…</p>}
            {!loading && listings.length === 0 && (
                <p className="text-muted-foreground text-sm" data-testid="market-buy-empty">
                    {t("market.empty_buy")}
                </p>
            )}
            <div className="text-xs text-muted-foreground">total: {total}</div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                {listings.map((l) => (
                    <div
                        key={l.id}
                        data-testid={`market-listing-${l.id}`}
                        className="border border-border rounded-sm bg-secondary/30 p-4 text-sm flex flex-col gap-2"
                    >
                        <div className="flex items-start justify-between gap-2">
                            <div>
                                <p className={`font-medium ${RARITY_COLOR[l.item.rarity] || ""}`}>
                                    {l.item.name}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                    {l.item.item_type} · {l.item.rarity} · lvl {l.item.level_required}
                                </p>
                            </div>
                            <Pill>{l.quantity}× — {l.price_per_unit}g</Pill>
                        </div>
                        <div className="text-xs text-muted-foreground">
                            {t("market.total")}: <span className="text-foreground">{l.total_price}g</span>
                            {" · "}
                            {t("market.seller")}: <span className="text-foreground">{l.seller.guild_name}</span>
                        </div>
                        {confirmId === l.id ? (
                            <div
                                className="border border-amber/50 rounded-sm p-3 bg-amber/5 space-y-3"
                                data-testid={`market-buy-modal-${l.id}`}
                                role="dialog"
                                aria-modal="true"
                                aria-labelledby={`market-buy-title-${l.id}`}
                            >
                                <div className="flex items-start justify-between gap-2">
                                    <p
                                        id={`market-buy-title-${l.id}`}
                                        className="text-xs font-semibold uppercase tracking-wider text-amber"
                                    >
                                        {t("market.buy_confirm")}
                                    </p>
                                    <button
                                        type="button"
                                        aria-label="Close"
                                        onClick={() => { setConfirmId(null); setBuyQty(1); }}
                                        className="text-muted-foreground hover:text-foreground text-xs px-1"
                                        data-testid={`market-buy-close-${l.id}`}
                                    >
                                        ✕
                                    </button>
                                </div>
                                <div className="flex items-center gap-2 text-xs">
                                    <label>{t("auction.buy_quantity")}:</label>
                                    <input
                                        type="number" min="1" max={l.quantity}
                                        value={buyQty}
                                        onChange={(e) => setBuyQty(parseInt(e.target.value, 10) || 1)}
                                        className="bg-secondary border border-border rounded-sm px-2 py-1 w-20"
                                        data-testid={`market-buy-qty-${l.id}`}
                                    />
                                    <span className="text-muted-foreground">
                                        = {(buyQty || 0) * l.price_per_unit}g
                                    </span>
                                </div>
                                <div className="flex flex-col sm:flex-row gap-2">
                                    <button
                                        className="bg-amber/90 text-background px-4 py-2 rounded-sm text-xs font-bold disabled:opacity-50 disabled:cursor-not-allowed flex-1"
                                        onClick={() => doBuy(l)}
                                        disabled={(buyQty || 0) * l.price_per_unit > myGuildGold}
                                        data-testid={`market-buy-confirm-${l.id}`}
                                    >
                                        {t("auction.buy_confirm_btn")}
                                    </button>
                                    <button
                                        className="border border-border hover:bg-secondary/50 px-4 py-2 rounded-sm text-xs flex-1"
                                        onClick={() => { setConfirmId(null); setBuyQty(1); }}
                                        data-testid={`market-buy-cancel-${l.id}`}
                                    >
                                        {t("auction.buy_cancel_btn")}
                                    </button>
                                </div>
                            </div>
                        ) : (() => {
                            // ROUND 6B.3 Wave 2 — explicit guard reasons so the
                            // FE never lets the player click a CTA that 4xx's.
                            // ROUND 11.1 B4 — server-authoritative `is_own`
                            // flag replaces the FE-side UUID comparison.
                            // `seller.user_id` is no longer exposed.
                            const isOwn = !!l.is_own;
                            // (now exposed by backend) instead of the previously
                            // missing seller.guild_id, so own-listing buttons are
                            // visibly disabled with structured tooltip.
                            const isInactive = l.status && l.status !== "active";
                            const cannotAfford = l.price_per_unit > myGuildGold;
                            const disabled = isOwn || isInactive || cannotAfford;
                            let reason = "";
                            if (isOwn) reason = t("auction.buy_disabled_own");
                            else if (isInactive) reason = t("auction.buy_disabled_status");
                            else if (cannotAfford) reason = t("auction.buy_disabled_gold");
                            return (
                                <button
                                    className={`px-3 py-1.5 rounded-sm text-xs ${
                                        disabled
                                            ? "border border-border text-muted-foreground cursor-not-allowed"
                                            : "border border-amber/60 text-amber hover:bg-amber/10 font-bold"
                                    }`}
                                    onClick={() => { setConfirmId(l.id); setBuyQty(l.quantity); }}
                                    disabled={disabled}
                                    title={reason || undefined}
                                    data-testid={`market-buy-btn-${l.id}`}
                                >
                                    {t("auction.buy_btn_short")} — {l.price_per_unit}g
                                </button>
                            );
                        })()}
                    </div>
                ))}
            </div>
        </div>
    );
}

// ─── SELL TAB ────────────────────────────────────────────────────────────
function SellTab({ token, lang, t, fee, refreshGuild }) {
    const [items, setItems] = useState([]);
    const [slug, setSlug] = useState("");
    const [qty, setQty] = useState(1);
    const [price, setPrice] = useState(10);
    const [submitting, setSubmitting] = useState(false);
    const [confirmOpen, setConfirmOpen] = useState(false);

    const loadInventory = useCallback(async () => {
        const r = await authedFetch(token, "/inventory");
        if (!r.ok) return;
        const data = await r.json();
        // Phase 19.4a — FIX P0 "Deposito non letto da Vendita":
        // Backend returns `{inventory: [...]}` (not `items`). The previous
        // `data.items || []` always returned [] → the sell form looked empty
        // even when the player owned tradeable, available stacks. Accept
        // both keys to be forward-compatible with any future shape tweak.
        const rows = data.inventory || data.items || [];
        // Filter to items with available > 0 AND tradeable
        const sellable = rows.filter((it) => {
            const available = it.available_quantity ?? (
                (it.total_quantity || it.quantity || 0)
                - (it.equipped_quantity || 0)
                - (it.market_locked_quantity || 0)
            );
            const tradeable = it.item?.is_tradeable !== false
                && it.item?.can_be_sold_for_gold !== false;
            // P19.4a: filter out bound stacks at the source so the user sees
            // a clear sell-list (BoE rows show in the Inventory page with
            // their bound badge; they just don't appear here).
            const notBound = it.is_bound !== true;
            return available > 0 && tradeable && notBound;
        });
        setItems(sellable);
        if (sellable.length && !slug) setSlug(sellable[0].item?.slug || "");
    }, [token, slug]);

    useEffect(() => { loadInventory(); }, [loadInventory]);

    const selected = useMemo(
        () => items.find((it) => it.item?.slug === slug),
        [items, slug]
    );
    const maxQty = selected
        ? (selected.available_quantity ?? (
            (selected.total_quantity || selected.quantity || 0)
            - (selected.equipped_quantity || 0)
            - (selected.market_locked_quantity || 0)
          ))
        : 0;
    const total = qty * price;
    const feeAmount = Math.floor((total * fee) / 100);
    const proceeds = total - feeAmount;

    async function submitListing() {
        if (!slug || qty < 1 || price < 1) return;
        setSubmitting(true);
        const r = await authedFetch(token, `/auction/listings?lang=${lang}`, {
            method: "POST",
            body: JSON.stringify({ item_slug: slug, quantity: qty, price_per_unit: price }),
        });
        const body = await r.json().catch(() => ({}));
        if (r.ok && body.success) {
            toast.success(`${t("auction.toast_listed")} — ${body.quantity}× @ ${body.price_per_unit}g`);
            setConfirmOpen(false);
            setQty(1);
            await loadInventory();
            await refreshGuild();
        } else {
            // ROUND 4 — translate the BoE 422 sentinel into a human i18n string.
            const detail = body.detail;
            if (
                r.status === 422 &&
                (detail === "market.bound_to_adventurer_not_sellable" ||
                 detail === "market.bound_item_not_sellable" ||
                 (typeof detail === "object" &&
                  detail?.code === "market.bound_to_adventurer_not_sellable"))
            ) {
                toast.error(t("market.error_bound_item"));
            } else {
                toast.error(formatErrorDetail(detail) || "Errore");
            }
        }
        setSubmitting(false);
    }

    if (items.length === 0) {
        return (
            <p className="text-muted-foreground text-sm" data-testid="market-sell-empty">
                {t("market.sell_no_items")}
            </p>
        );
    }

    return (
        <div className="space-y-4 max-w-xl" data-testid="market-list-form">
            <div className="space-y-2">
                <label className="block text-xs tracking-widest text-muted-foreground">
                    {t("market.sell_select_item")}
                </label>
                <select
                    data-testid="market-sell-item"
                    className="w-full bg-secondary border border-border rounded-sm px-2 py-2 text-sm"
                    value={slug}
                    onChange={(e) => { setSlug(e.target.value); setQty(1); }}
                >
                    {items.map((it) => (
                        <option key={it.item?.slug} value={it.item?.slug}>
                            {(it.item?.display_name_it || it.item?.display_name_en || it.item?.name)}
                            {" — "}
                            {t("market.available_qty")}: {it.available_quantity ?? (it.quantity || 0)}
                        </option>
                    ))}
                </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
                <div>
                    <label className="block text-xs text-muted-foreground mb-1">
                        {t("market.sell_quantity")} (max {maxQty})
                    </label>
                    <input
                        type="number" min="1" max={maxQty}
                        className="w-full bg-secondary border border-border rounded-sm px-2 py-2 text-sm"
                        value={qty}
                        onChange={(e) => setQty(Math.max(1, Math.min(maxQty, parseInt(e.target.value, 10) || 1)))}
                        data-testid="market-sell-qty"
                    />
                </div>
                <div>
                    <label className="block text-xs text-muted-foreground mb-1">
                        {t("market.sell_price_unit")}
                    </label>
                    <input
                        type="number" min="1"
                        className="w-full bg-secondary border border-border rounded-sm px-2 py-2 text-sm"
                        value={price}
                        onChange={(e) => setPrice(Math.max(1, parseInt(e.target.value, 10) || 1))}
                        data-testid="market-sell-price"
                    />
                </div>
            </div>

            <div className="border border-border rounded-sm bg-secondary/40 p-3 text-sm space-y-1">
                <div className="flex justify-between">
                    <span className="text-muted-foreground">{t("market.total")}</span>
                    <span>{total}g</span>
                </div>
                <div className="flex justify-between">
                    <span className="text-muted-foreground">{t("market.sell_fee_estimate")} ({fee}%)</span>
                    <span>-{feeAmount}g</span>
                </div>
                <div className="flex justify-between border-t border-border pt-1 mt-1">
                    <span className="text-amber">{t("market.sell_proceeds")}</span>
                    <span className="text-amber" data-testid="market-sell-proceeds">{proceeds}g</span>
                </div>
            </div>

            {!confirmOpen ? (
                <button
                    className="bg-amber text-background px-4 py-2 rounded-sm text-sm disabled:opacity-50"
                    disabled={!slug || qty < 1 || price < 1}
                    onClick={() => setConfirmOpen(true)}
                    data-testid="market-sell-submit"
                >
                    {t("market.sell_btn")}
                </button>
            ) : (
                <div className="border border-amber/50 rounded-sm p-3 bg-amber/5 space-y-2">
                    <p className="text-xs">{t("market.sell_confirm")}</p>
                    <div className="flex gap-2">
                        <button
                            className="bg-amber text-background px-3 py-1.5 rounded-sm text-xs"
                            onClick={submitListing}
                            disabled={submitting}
                            data-testid="market-sell-confirm"
                        >
                            ✓ {t("market.sell_btn")}
                        </button>
                        <button
                            className="border border-border px-3 py-1.5 rounded-sm text-xs"
                            onClick={() => setConfirmOpen(false)}
                        >
                            ×
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

// ─── MINE TAB ────────────────────────────────────────────────────────────
function MineTab({ token, lang, t, refreshGuild }) {
    const [rows, setRows] = useState([]);
    const [loading, setLoading] = useState(false);
    const [confirmCancel, setConfirmCancel] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        const r = await authedFetch(token, `/auction/listings/mine?lang=${lang}`);
        if (r.ok) {
            const body = await r.json();
            setRows(body.listings || []);
        }
        setLoading(false);
    }, [token, lang]);

    useEffect(() => { load(); }, [load]);

    async function cancelListing(id) {
        const r = await authedFetch(token, `/auction/listings/${id}`, { method: "DELETE" });
        const body = await r.json().catch(() => ({}));
        if (r.ok && body.success) {
            toast.success(t("market.toast_cancelled"));
            setConfirmCancel(null);
            await load();
            await refreshGuild();
        } else {
            toast.error(formatErrorDetail(body.detail) || "Errore");
        }
    }

    if (loading) return <p className="text-muted-foreground text-xs">…</p>;
    if (rows.length === 0) {
        return (
            <p className="text-muted-foreground text-sm" data-testid="market-mine-empty">
                {t("market.empty_mine")}
            </p>
        );
    }

    return (
        <div className="overflow-x-auto">
            <table className="w-full text-xs border-collapse" data-testid="market-mine-table">
                <thead>
                    <tr className="text-muted-foreground tracking-widest">
                        <th className="text-left py-2 px-2">item</th>
                        <th className="text-right py-2 px-2">{t("market.qty")}</th>
                        <th className="text-right py-2 px-2">{t("market.price_unit")}</th>
                        <th className="text-right py-2 px-2">{t("market.total")}</th>
                        <th className="text-left py-2 px-2">status</th>
                        <th className="text-left py-2 px-2">{t("market.buyer")}</th>
                        <th className="text-right py-2 px-2"></th>
                    </tr>
                </thead>
                <tbody>
                    {rows.map((l) => (
                        <tr key={l.id} className="border-t border-border" data-testid={`market-mine-row-${l.id}`}>
                            <td className="py-2 px-2">
                                <span className={`${RARITY_COLOR[l.item.rarity] || ""}`}>
                                    {l.item.name}
                                </span>
                                <span className="text-muted-foreground ml-2">
                                    ({l.item.rarity}, lvl {l.item.level_required})
                                </span>
                            </td>
                            <td className="text-right">{l.quantity}</td>
                            <td className="text-right">{l.price_per_unit}g</td>
                            <td className="text-right">{l.total_price}g</td>
                            <td><Pill>{t(`market.status_${l.status}`)}</Pill></td>
                            <td className="text-muted-foreground">{l.buyer?.guild_name || "—"}</td>
                            <td className="text-right">
                                {l.status === "active" && (
                                    confirmCancel === l.id ? (
                                        <span className="inline-flex gap-1">
                                            <button
                                                className="border border-rose-500/50 text-rose-300 px-2 py-1 rounded-sm"
                                                onClick={() => cancelListing(l.id)}
                                                data-testid={`market-cancel-confirm-${l.id}`}
                                            >
                                                ✓
                                            </button>
                                            <button
                                                className="border border-border px-2 py-1 rounded-sm"
                                                onClick={() => setConfirmCancel(null)}
                                            >
                                                ×
                                            </button>
                                        </span>
                                    ) : (
                                        <button
                                            className="border border-border px-2 py-1 rounded-sm hover:bg-secondary"
                                            onClick={() => setConfirmCancel(l.id)}
                                            data-testid={`market-cancel-btn-${l.id}`}
                                        >
                                            {t("market.cancel_btn")}
                                        </button>
                                    )
                                )}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

// ─── PAGE ────────────────────────────────────────────────────────────────
export default function Market() {
    // Bug fix Phase 16: AuthContext exposes {user, guild, refreshGuild}, NOT
    // {token, loading}. The previous code destructured non-existent fields,
    // which made the useEffect below always trigger navigate("/login")
    // (because `token` was undefined → `!token` was true). /login then
    // GuestOnly-redirected back to /dashboard, producing the observed
    // "Mercato → Dashboard" symptom.
    // ProtectedRoute already guards `user` and `guild`, so this component
    // does not need to re-check them.
    const { user, guild, refreshGuild } = useAuth();
    // ROUND 11.1 Slice 2 — `token` is no longer needed for child fetches;
    // `api` wrapper handles cookie auth + CSRF transparently. Kept as
    // `null` placeholder for the `authedFetch(_token, ...)` legacy signature.
    const token = null;
    const { t, lang } = useT();
    const [tab, setTab] = useState("buy");
    const FEE = 5;

    // Safety net only — ProtectedRoute is the real auth gate.
    if (user === undefined || guild === undefined) return null;
    if (!user || !guild) return null;

    return (
        <div className="min-h-screen bg-background text-foreground">
            <AppHeader subtitleKey="nav.brand_subtitle_dashboard" />
            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-6 space-y-6">
                <header>
                    <h1 className="text-3xl font-light tracking-wide">
                        {t("auction.title")}
                    </h1>
                    <p className="text-xs text-muted-foreground mt-1">
                        {t("auction.subtitle").replace("{fee}", FEE)}
                    </p>
                </header>

                <nav className="flex items-center gap-1 border-b border-border" data-testid="market-tabs">
                    {[
                        ["buy", "tab_buy", "market-tab-buy"],
                        ["sell", "tab_sell", "market-tab-sell"],
                        ["mine", "tab_mine", "market-tab-mine"],
                    ].map(([k, key, testid]) => (
                        <button
                            key={k}
                            data-testid={testid}
                            onClick={() => setTab(k)}
                            className={`px-3 py-2 text-xs tracking-widest border-b-2 transition-colors ${
                                tab === k
                                    ? "border-amber text-amber"
                                    : "border-transparent text-muted-foreground hover:text-foreground"
                            }`}
                        >
                            {t(`auction.${key}`)}
                        </button>
                    ))}
                </nav>

                <section>
                    <SectionTitle>
                        {tab === "buy" ? t("auction.tab_buy")
                            : tab === "sell" ? t("auction.tab_sell")
                            : t("auction.tab_mine")}
                    </SectionTitle>
                    {tab === "buy" && <BuyTab token={token} lang={lang} t={t} refreshGuild={refreshGuild} myUserId={user?.id} myGuildId={guild?.id} myGuildGold={guild?.gold || 0} />}
                    {tab === "sell" && <SellTab token={token} lang={lang} t={t} fee={FEE} refreshGuild={refreshGuild} />}
                    {tab === "mine" && <MineTab token={token} lang={lang} t={t} refreshGuild={refreshGuild} />}
                </section>
            </main>
        </div>
    );
}
