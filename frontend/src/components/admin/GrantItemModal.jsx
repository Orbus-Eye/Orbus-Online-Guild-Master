/* ROUND 11.2 TASK 5b — Admin Ops: Grant Item Modal with double-confirm.
 * Step 1: item_slug + quantity + reason. Continue disabled if invalid.
 * Step 2: strong confirmation. On confirm → POST grant-item.
 * 4xx error mapping: unknown_slug / bound / p2w → readable inline message.
 */
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { api, formatApiError } from "@/lib/api";

const MAX_QTY = 1000;

export default function GrantItemModal({ guild, onClose, onGranted }) {
    const [step, setStep] = useState(1);
    const [itemSlug, setItemSlug] = useState("");
    const [quantity, setQuantity] = useState("");
    const [reason, setReason] = useState("");
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState(null);
    // ROUND 11.2 TASK 5b P1 — sync guard against double-click race.
    const submittingRef = useRef(false);

    const qty = parseInt(quantity, 10);
    const validQty = Number.isFinite(qty) && qty > 0 && qty <= MAX_QTY;
    const validSlug = itemSlug.trim().length > 0;
    const validReason = reason.trim().length >= 3;
    const canContinue = validQty && validSlug && validReason;

    useEffect(() => {
        const onKey = (e) => { if (e.key === "Escape") onClose(); };
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, [onClose]);

    const submit = async () => {
        // SYNC guard: blocks second click BEFORE React commits setBusy.
        if (submittingRef.current) return;
        submittingRef.current = true;
        setBusy(true); setError(null);
        try {
            const { data } = await api.post(
                `/admin/guilds/${guild.public_id || guild.id}/grant-item`,
                { item_slug: itemSlug.trim(), quantity: qty, reason: reason.trim() },
            );
            toast.success(`Grant completato. Audit ID: ${data.audit_event_id || "—"}`);
            onGranted?.(data);
            onClose();
        } catch (err) {
            // Map known 4xx codes to inline error in step 1.
            const detail = err?.response?.data?.detail;
            let msg = formatApiError(err);
            if (typeof detail === "object" && detail) {
                if (detail.code === "admin.item.unknown_slug") {
                    msg = `Item slug '${itemSlug}' non riconosciuto.`;
                } else if (detail.code === "admin.item.bound_not_grantable") {
                    msg = "Questo item è bound, non grantabile.";
                } else if (detail.code === "admin.item.p2w_blocked") {
                    msg = "Item bloccato da policy anti-P2W (real-money + combat).";
                }
            }
            setError(msg);
            setStep(1);  // back to form so admin can correct slug
        } finally {
            setBusy(false);
            submittingRef.current = false;  // re-enable after the call completes
        }
    };

    return (
        <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="grant-item-title"
            data-testid="grant-item-modal"
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
            onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
        >
            <div className="bg-card border border-border rounded-sm max-w-md w-full p-5 space-y-4 max-h-[90vh] overflow-y-auto">
                <div className="flex items-start justify-between gap-3">
                    <h2 id="grant-item-title" className="text-sm font-semibold uppercase tracking-wider text-amber">
                        Grant Item {step === 2 && "— Conferma"}
                    </h2>
                    <button
                        aria-label="Close"
                        data-testid="grant-item-close"
                        onClick={onClose}
                        className="text-muted-foreground hover:text-foreground text-sm px-1"
                    >
                        ✕
                    </button>
                </div>
                <p className="text-xs text-muted-foreground">
                    Target: <strong>{guild.name}</strong>{" "}
                    <span className="font-mono text-[10px]">({guild.public_id})</span>
                </p>

                {step === 1 && (
                    <>
                        <div className="space-y-2">
                            <label className="text-xs uppercase tracking-wider">Item slug</label>
                            <input
                                type="text"
                                value={itemSlug}
                                onChange={(e) => setItemSlug(e.target.value)}
                                placeholder="es. iron_shard"
                                data-testid="grant-item-slug"
                                className="w-full bg-secondary border border-border rounded-sm px-3 py-2 text-sm font-mono"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-xs uppercase tracking-wider">Quantity</label>
                            <input
                                type="number" min={1} max={MAX_QTY}
                                value={quantity}
                                onChange={(e) => setQuantity(e.target.value)}
                                placeholder={`1 – ${MAX_QTY}`}
                                data-testid="grant-item-quantity"
                                className="w-full bg-secondary border border-border rounded-sm px-3 py-2 text-sm"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-xs uppercase tracking-wider">
                                Reason <span className="text-muted-foreground">(min 3 char)</span>
                            </label>
                            <textarea
                                rows={3} maxLength={300}
                                value={reason}
                                onChange={(e) => setReason(e.target.value)}
                                data-testid="grant-item-reason"
                                className="w-full bg-secondary border border-border rounded-sm px-3 py-2 text-sm"
                            />
                        </div>
                        {error && (
                            <p data-testid="grant-item-error" className="text-xs text-red-400">{error}</p>
                        )}
                        <button
                            data-testid="grant-item-continue"
                            onClick={() => setStep(2)}
                            disabled={!canContinue}
                            className="w-full bg-amber/90 text-background px-4 py-2 rounded-sm text-xs font-bold disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Continua →
                        </button>
                    </>
                )}

                {step === 2 && (
                    <>
                        <div
                            className="border border-amber/50 bg-amber/5 rounded-sm p-3 space-y-2 text-sm"
                            data-testid="grant-item-confirm-card"
                        >
                            <p>⚠ Stai per grantare:</p>
                            <p className="font-mono text-xs">
                                {qty} × <strong>{itemSlug}</strong>
                            </p>
                            <p className="text-xs">A: {guild.name} ({guild.public_id})</p>
                            <p className="text-xs">
                                <span className="text-muted-foreground">Motivo:</span> {reason}
                            </p>
                            <p className="text-xs text-amber">Sei sicuro?</p>
                        </div>
                        <div className="flex flex-col sm:flex-row gap-2">
                            <button
                                data-testid="grant-item-confirm"
                                onClick={submit}
                                disabled={busy}
                                className="bg-amber/90 text-background px-4 py-2 rounded-sm text-xs font-bold disabled:opacity-50 disabled:cursor-not-allowed flex-1"
                            >
                                {busy ? "…" : "Conferma"}
                            </button>
                            <button
                                data-testid="grant-item-back"
                                onClick={() => setStep(1)}
                                disabled={busy}
                                className="border border-border hover:bg-secondary/50 px-4 py-2 rounded-sm text-xs flex-1"
                            >
                                ← Indietro
                            </button>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
