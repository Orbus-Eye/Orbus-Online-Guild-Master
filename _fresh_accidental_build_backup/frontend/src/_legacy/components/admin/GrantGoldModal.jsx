/* ROUND 11.2 TASK 5b — Admin Ops: Grant Gold Modal with double-confirm.
 * Step 1: amount + reason form. Continue disabled if invalid.
 * Step 2: strong confirmation showing target guild + amount + reason.
 * On confirm → POST /api/admin/guilds/{id}/grant-gold and refresh detail.
 */
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { api, formatApiError } from "@/lib/api";

const MAX_GOLD = 100000;

export default function GrantGoldModal({ guild, onClose, onGranted }) {
    const [step, setStep] = useState(1);
    const [amount, setAmount] = useState("");
    const [reason, setReason] = useState("");
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState(null);
    // ROUND 11.2 TASK 5b P1 — synchronous guard against double-click.
    // `disabled={busy}` is not enough: React batches setState, so a fast
    // second click executes BEFORE `setBusy(true)` is committed. The ref
    // mutation is synchronous and blocks the second handler immediately.
    const submittingRef = useRef(false);

    const amt = parseInt(amount, 10);
    const validAmount = Number.isFinite(amt) && amt > 0 && amt <= MAX_GOLD;
    const validReason = typeof reason === "string" && reason.trim().length >= 3;
    const canContinue = validAmount && validReason;

    useEffect(() => {
        const onKey = (e) => { if (e.key === "Escape") onClose(); };
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, [onClose]);

    const onSubmit = async () => {
        // SYNC guard: blocks the second click BEFORE React commits setBusy.
        if (submittingRef.current) return;
        submittingRef.current = true;
        setBusy(true); setError(null);
        try {
            const { data } = await api.post(
                `/admin/guilds/${guild.public_id || guild.id}/grant-gold`,
                { amount: amt, reason: reason.trim() },
            );
            toast.success(`Grant completato. Audit ID: ${data.audit_event_id || "—"}`);
            onGranted?.(data);
            onClose();
        } catch (err) {
            setError(formatApiError(err));
        } finally {
            setBusy(false);
            submittingRef.current = false;  // re-enable after the call completes
        }
    };

    return (
        <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="grant-gold-title"
            data-testid="grant-gold-modal"
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
            onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
        >
            <div className="bg-card border border-border rounded-sm max-w-md w-full p-5 space-y-4 max-h-[90vh] overflow-y-auto">
                <div className="flex items-start justify-between gap-3">
                    <h2 id="grant-gold-title" className="text-sm font-semibold uppercase tracking-wider text-amber">
                        Grant Gold {step === 2 && "— Conferma"}
                    </h2>
                    <button
                        aria-label="Close"
                        data-testid="grant-gold-close"
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
                            <label className="text-xs uppercase tracking-wider">Amount (gold)</label>
                            <input
                                type="number" min={1} max={MAX_GOLD}
                                value={amount}
                                onChange={(e) => setAmount(e.target.value)}
                                placeholder={`1 – ${MAX_GOLD}`}
                                data-testid="grant-gold-amount"
                                className="w-full bg-secondary border border-border rounded-sm px-3 py-2 text-sm"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-xs uppercase tracking-wider">
                                Reason <span className="text-muted-foreground">(min 3 char)</span>
                            </label>
                            <textarea
                                rows={3}
                                value={reason} maxLength={300}
                                onChange={(e) => setReason(e.target.value)}
                                data-testid="grant-gold-reason"
                                className="w-full bg-secondary border border-border rounded-sm px-3 py-2 text-sm font-mono"
                            />
                            <p className="text-[10px] text-muted-foreground text-right">
                                {reason.length}/300
                            </p>
                        </div>
                        <button
                            data-testid="grant-gold-continue"
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
                            data-testid="grant-gold-confirm-card"
                        >
                            <p>⚠ Stai per grantare <strong>{amt} gold</strong> a:</p>
                            <p className="font-mono text-xs">
                                {guild.name} ({guild.public_id})
                            </p>
                            <p className="text-xs">
                                <span className="text-muted-foreground">Motivo:</span> {reason}
                            </p>
                            <p className="text-xs text-amber">Sei sicuro?</p>
                        </div>
                        {error && (
                            <p data-testid="grant-gold-error" className="text-xs text-red-400">{error}</p>
                        )}
                        <div className="flex flex-col sm:flex-row gap-2">
                            <button
                                data-testid="grant-gold-confirm"
                                onClick={onSubmit}
                                disabled={busy}
                                className="bg-amber/90 text-background px-4 py-2 rounded-sm text-xs font-bold disabled:opacity-50 disabled:cursor-not-allowed flex-1"
                            >
                                {busy ? "…" : "Conferma"}
                            </button>
                            <button
                                data-testid="grant-gold-back"
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
