// R18.Reset.2 — R18ResetBanner
// Player-facing informativo IT byte-exact. Dismissibile con persistenza
// server-side (guild-level). Zero leak metadata tecnici (no apply_id,
// no backup path, no archive counts, no reset script version).

import { useCallback, useEffect, useState } from "react";
import { X } from "lucide-react";
import { api } from "../lib/api";
import { Button } from "./ui/button";

export default function R18ResetBanner() {
    const [banner, setBanner] = useState(null);
    const [dismissing, setDismissing] = useState(false);

    const fetchBanner = useCallback(async () => {
        try {
            const res = await api.get("/guilds/me/r18-reset-banner");
            setBanner(res.data);
        } catch (e) {
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
            await api.post("/guilds/me/r18-reset-banner/dismiss");
            setBanner((b) => (b ? { ...b, show: false, dismissed: true } : b));
        } catch (e) {
            // Non bloccare UI su errore dismiss
        } finally {
            setDismissing(false);
        }
    }, [dismissing]);

    if (!banner || !banner.show) {
        return null;
    }

    return (
        <div
            data-testid="r18-reset-banner"
            className="border border-border/60 bg-muted/30 rounded-sm p-4 mb-4"
        >
            <div className="flex items-start gap-3">
                <div className="flex-1">
                    <p
                        data-testid="r18-reset-banner-message-it"
                        className="text-sm text-foreground leading-relaxed"
                    >
                        {banner.message_it}
                    </p>
                </div>
                <Button
                    data-testid="r18-reset-banner-dismiss-btn"
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
