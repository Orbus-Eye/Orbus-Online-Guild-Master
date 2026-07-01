// Phase 19.2 — P1.1 Rename adventurer modal (max 2 lifetime).
// Opens from Adventurers list / detail. Submits PATCH /api/adventurers/{id}/name.
// Disables Save when out of renames; backend remains the source of truth.
import { useEffect, useRef, useState } from "react";
import { X } from "lucide-react";
import { api, formatApiError } from "../lib/api";
import { toast } from "sonner";
import { useT } from "../i18n/I18nContext";

export default function AdventurerRenameModal({ adventurer, onClose, onRenamed }) {
    const { t } = useT();
    const [value, setValue] = useState("");
    const [busy, setBusy] = useState(false);
    const inputRef = useRef(null);

    useEffect(() => {
        if (!adventurer) return undefined;
        setValue(adventurer.name || "");
        const onKey = (e) => { if (e.key === "Escape" && !busy) onClose(); };
        document.addEventListener("keydown", onKey);
        setTimeout(() => inputRef.current?.focus(), 30);
        return () => document.removeEventListener("keydown", onKey);
    }, [adventurer, onClose, busy]);

    if (!adventurer) return null;

    const renameMax = adventurer.rename_max ?? 2;
    const renameCount = adventurer.rename_count ?? 0;
    const remaining = Math.max(0, renameMax - renameCount);
    const limitReached = remaining <= 0;
    const trimmed = (value || "").trim();
    const tooShort = trimmed.length < 2;
    const tooLong = trimmed.length > 30;
    const unchanged = trimmed === (adventurer.name || "");

    const canSubmit = !busy && !limitReached && !tooShort && !tooLong && !unchanged;

    const submit = async (e) => {
        e?.preventDefault?.();
        if (!canSubmit) return;
        setBusy(true);
        try {
            const res = await api.patch(`/adventurers/${adventurer.id}/name`, {
                name: trimmed,
            });
            toast.success(t("rename.toast_renamed", "Avventuriero rinominato"));
            onRenamed?.(res.data.adventurer);
            onClose();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setBusy(false);
        }
    };

    return (
        <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="rename-title"
            data-testid="adventurer-rename-modal"
            className="fixed inset-0 z-[60] flex items-center justify-center px-3 py-6"
            onClick={(e) => { if (e.target === e.currentTarget && !busy) onClose(); }}
        >
            <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" aria-hidden="true" onClick={() => !busy && onClose()} />
            <form
                onSubmit={submit}
                className="relative w-full max-w-md border border-border bg-card rounded-sm p-5 sm:p-6 shadow-xl"
            >
                <button
                    type="button"
                    onClick={() => !busy && onClose()}
                    aria-label="Chiudi"
                    data-testid="rename-modal-close"
                    className="absolute top-3 right-3 p-1.5 rounded-sm text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-amber"
                >
                    <X size={18} />
                </button>

                <div className="text-[10px] text-amber tracking-widest mb-2">:: {t("rename.header", "RINOMINA AVVENTURIERO")}</div>
                <h2 id="rename-title" className="text-xl font-semibold tracking-tight">{adventurer.name}</h2>
                <div className="text-xs text-muted-foreground mt-1">
                    {adventurer.class_name} · {adventurer.class_role} · Lv {adventurer.level}
                </div>

                <div className="mt-5">
                    <label htmlFor="adv-new-name" className="text-[10px] text-muted-foreground tracking-widest">
                        {t("rename.new_name_label", "Nuovo nome")}
                    </label>
                    <input
                        id="adv-new-name"
                        ref={inputRef}
                        type="text"
                        data-testid="rename-input"
                        value={value}
                        onChange={(e) => setValue(e.target.value)}
                        disabled={busy || limitReached}
                        maxLength={30}
                        placeholder={t("rename.placeholder", "es. Aria di Tempesta")}
                        className="mt-1.5 w-full bg-background border border-border rounded-sm px-3 py-2 text-sm focus-visible:outline-none focus-visible:border-amber/60 disabled:opacity-40"
                    />
                    <div className="mt-2 text-[11px] text-muted-foreground flex items-center justify-between">
                        <span data-testid="rename-counter">
                            {t("rename.remaining_label", "Rinomine rimaste")}:{" "}
                            <strong className={remaining > 0 ? "text-amber" : "text-destructive"}>
                                {remaining}/{renameMax}
                            </strong>
                        </span>
                        <span>{trimmed.length}/30</span>
                    </div>
                </div>

                {limitReached && (
                    <div
                        data-testid="rename-limit-reached"
                        className="mt-3 text-[11px] text-destructive border border-destructive/40 bg-destructive/10 rounded-sm px-3 py-2"
                    >
                        {t("rename.limit_reached", "Limite rinomine raggiunto (2/2). Nessuna rinomina ulteriore consentita.")}
                    </div>
                )}

                {!limitReached && (tooShort || tooLong) && trimmed.length > 0 && (
                    <div className="mt-3 text-[11px] text-amber">
                        {tooShort
                            ? t("rename.too_short", "Il nome deve avere almeno 2 caratteri.")
                            : t("rename.too_long", "Il nome non può superare i 30 caratteri.")}
                    </div>
                )}

                <div className="mt-5 flex items-center justify-end gap-2">
                    <button
                        type="button"
                        onClick={() => !busy && onClose()}
                        data-testid="rename-cancel-btn"
                        disabled={busy}
                        className="text-[11px] tracking-widest border border-border px-3 py-1.5 rounded-sm hover:bg-secondary disabled:opacity-40"
                    >
                        {t("rename.cancel", "Annulla")}
                    </button>
                    <button
                        type="submit"
                        data-testid="rename-submit-btn"
                        disabled={!canSubmit}
                        title={limitReached ? t("rename.limit_reached") : undefined}
                        className="text-[11px] tracking-widest bg-amber text-black px-3 py-1.5 rounded-sm hover:bg-amber/80 disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                        {busy ? "…" : t("rename.save", "Salva")}
                    </button>
                </div>
            </form>
        </div>
    );
}
