// ROUND 11.2 EXT-2 — Material source lookup modal.
//
// Fetches `GET /api/materials/lookup/{slug}` (public, no-auth) and renders
// rarity + description + drop sources + used_for. Driven by an external
// `open`/`onOpenChange` pair so the parent (Territory.jsx) can host one
// modal instance shared by all StructureCards.
//
// Failure modes:
//   * 404 → "Materiale non documentato" (also for equipment/test/hidden).
//   * network → generic error.
//
// Uses shadcn `Dialog` for focus trap + ESC + backdrop click + a11y.
import { useEffect, useState } from "react";

import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "../ui/dialog";
import { api } from "../../lib/api";

const RARITY_COLOR = {
    common: "text-muted-foreground border-muted-foreground/40",
    uncommon: "text-emerald-400 border-emerald-400/40",
    rare: "text-sky-400 border-sky-400/40",
    epic: "text-purple-400 border-purple-400/40",
    legendary: "text-amber border-amber/40",
};

function RarityBadge({ rarity, lang: _lang }) {
    const cls = RARITY_COLOR[rarity] || RARITY_COLOR.common;
    const label = (rarity || "common").toUpperCase();
    return (
        <span
            data-testid="material-modal-rarity"
            className={`inline-block text-[10px] tracking-widest font-bold px-2 py-0.5 border rounded-sm ${cls}`}
        >
            {label}
        </span>
    );
}

export default function MaterialSourceModal({ slug, open, onOpenChange, lang = "it" }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!open || !slug) return;
        let cancelled = false;
        setData(null);
        setError(null);
        setLoading(true);
        api.get(`/materials/lookup/${slug}`)
            .then((res) => {
                if (cancelled) return;
                setData(res.data);
            })
            .catch((err) => {
                if (cancelled) return;
                const status = err?.response?.status;
                if (status === 404) {
                    setError("not_found");
                } else {
                    setError("network");
                }
            })
            .finally(() => {
                if (!cancelled) setLoading(false);
            });
        return () => {
            cancelled = true;
        };
    }, [open, slug]);

    const labels = lang === "it"
        ? {
            loading: "Caricamento…",
            notFound: "Materiale non documentato.",
            networkErr: "Errore di rete. Riprova.",
            sources: "Dove si trova",
            usedFor: "Usato per",
            none: "—",
            close: "Chiudi",
        }
        : {
            loading: "Loading…",
            notFound: "Material not documented.",
            networkErr: "Network error. Try again.",
            sources: "Sources",
            usedFor: "Used for",
            none: "—",
            close: "Close",
        };

    const displayName = data
        ? (lang === "it" ? data.display_name_it : data.display_name_en) || data.display_name_it || slug
        : slug;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent
                data-testid="material-source-modal"
                className="bg-card text-foreground border-border max-w-md"
            >
                <DialogHeader>
                    <DialogTitle
                        data-testid="material-modal-title"
                        className="text-base font-bold tracking-wide flex items-center gap-2"
                    >
                        <span>{displayName}</span>
                        {data?.rarity && <RarityBadge rarity={data.rarity} lang={lang} />}
                    </DialogTitle>
                    <DialogDescription data-testid="material-modal-description" className="text-xs leading-relaxed">
                        {loading && labels.loading}
                        {!loading && error === "not_found" && labels.notFound}
                        {!loading && error === "network" && labels.networkErr}
                        {!loading && !error && data && (
                            (lang === "it" ? data.description_it : data.description_en) || ""
                        )}
                    </DialogDescription>
                </DialogHeader>

                {!loading && !error && data && (
                    <div className="space-y-4 text-xs">
                        <section data-testid="material-modal-sources">
                            <div className="text-[10px] tracking-widest text-muted-foreground mb-1">
                                {labels.sources}
                            </div>
                            {(data.sources || []).length === 0 ? (
                                <div className="text-muted-foreground">{labels.none}</div>
                            ) : (
                                <ul className="space-y-1.5">
                                    {data.sources.map((s, idx) => {
                                        const label = lang === "it" ? s.label_it : s.label_en;
                                        const note = lang === "it" ? s.note_it : (s.note_it || "");
                                        return (
                                            <li
                                                key={`${s.type}-${idx}`}
                                                data-testid={`material-modal-source-${s.type}`}
                                                className="border border-border/60 bg-background/40 rounded-sm px-2 py-1.5"
                                            >
                                                <div className="flex items-center gap-2 flex-wrap">
                                                    <span className="font-bold text-foreground">{label}</span>
                                                    {s.tier && (
                                                        <span className="text-[10px] tracking-widest text-amber/80">
                                                            {s.tier}
                                                        </span>
                                                    )}
                                                    {s.frequency && (
                                                        <span className="text-[10px] text-muted-foreground">
                                                            {s.frequency}
                                                        </span>
                                                    )}
                                                </div>
                                                {note && (
                                                    <div className="text-muted-foreground mt-0.5">{note}</div>
                                                )}
                                            </li>
                                        );
                                    })}
                                </ul>
                            )}
                        </section>

                        {Array.isArray(data.used_for_it) && data.used_for_it.length > 0 && lang === "it" && (
                            <section data-testid="material-modal-used-for">
                                <div className="text-[10px] tracking-widest text-muted-foreground mb-1">
                                    {labels.usedFor}
                                </div>
                                <ul className="list-disc list-inside space-y-0.5 text-muted-foreground">
                                    {data.used_for_it.map((u, idx) => (
                                        <li key={idx}>{u}</li>
                                    ))}
                                </ul>
                            </section>
                        )}
                    </div>
                )}
            </DialogContent>
        </Dialog>
    );
}
