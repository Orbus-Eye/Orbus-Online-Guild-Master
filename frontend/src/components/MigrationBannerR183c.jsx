// ROUND 18.3c — MigrationBannerR183c
// Player-facing informativo IT byte-exact. Dismissibile con persistenza
// server-side (guild-level). Zero leak metadata tecnici.

import { useCallback, useEffect, useState } from "react";
import { X } from "lucide-react";
import { api } from "../lib/api";
import { Button } from "./ui/button";

export default function MigrationBannerR183c() {
    const [banner, setBanner] = useState(null);
    const [expanded, setExpanded] = useState(false);
    const [dismissing, setDismissing] = useState(false);

    const fetchBanner = useCallback(async () => {
        try {
            const res = await api.get("/guilds/me/migration-banner");
            setBanner(res.data);
        } catch {
            // Silenzioso — best-effort UI
            setBanner(null);
        }
    }, []);

    useEffect(() => {
        fetchBanner();
    }, [fetchBanner]);

    const handleDismiss = useCallback(async () => {
        if (dismissing) return;
        setDismissing(true);
        try {
            await api.post("/guilds/me/migration-banner/dismiss");
            setBanner((b) => (b ? { ...b, show: false, dismissed: true } : b));
        } catch {
            // Non bloccare UI su errore dismiss
        } finally {
            setDismissing(false);
        }
    }, [dismissing]);

    if (!banner || !banner.show || banner.migrated_count === 0) {
        return null;
    }

    return (
        <div
            data-testid="migration-banner-r18-3c"
            className="border border-amber/40 bg-amber/5 rounded-sm p-4 mb-4"
        >
            <div className="flex items-start gap-3">
                <div className="flex-1">
                    <p
                        data-testid="migration-banner-message-it"
                        className="text-sm text-foreground leading-relaxed"
                    >
                        {banner.message_it}
                    </p>
                    {banner.mappings && banner.mappings.length > 0 && (
                        <div className="mt-3">
                            <button
                                data-testid="migration-banner-toggle-details"
                                type="button"
                                onClick={() => setExpanded((v) => !v)}
                                className="text-xs text-amber underline hover:text-amber/80"
                            >
                                {expanded ? "Nascondi dettagli" : "Dettagli"}
                            </button>
                            {expanded && (
                                <ul
                                    data-testid="migration-banner-mapping-list"
                                    className="mt-2 space-y-1 text-xs text-muted-foreground"
                                >
                                    {banner.mappings.map((m, idx) => (
                                        <li
                                            key={`${m.from_it}-${m.to_it}-${idx}`}
                                            data-testid={`migration-banner-mapping-${idx}`}
                                        >
                                            {m.from_it} → {m.to_it}
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>
                    )}
                </div>
                <Button
                    data-testid="migration-banner-dismiss-btn"
                    variant="ghost"
                    size="sm"
                    onClick={handleDismiss}
                    disabled={dismissing}
                    aria-label="Chiudi"
                    className="shrink-0 h-8 w-8 p-0"
                >
                    <X className="h-4 w-4" />
                </Button>
            </div>
        </div>
    );
}
