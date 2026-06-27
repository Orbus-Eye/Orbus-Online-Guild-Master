// ROUND 6B.3 Wave 1.5 — Reusable over-cap banner.
// Renders a sticky red strip with cap state + CTA when current > cap.
// Used on Recruitment, Expeditions, Raids, Squads and Territory pages so
// the player never finds themselves clicking a CTA that silently 423s.
import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { useT } from "../i18n/I18nContext";

export default function OverCapBanner({ source = "page" }) {
    const { t } = useT();
    const [state, setState] = useState(null);

    useEffect(() => {
        let cancelled = false;
        async function load() {
            try {
                // We piggyback on /api/territory + /api/adventurers (already
                // cached by the Dashboard). One round-trip is enough for
                // the cap state.
                const [terr, advs] = await Promise.all([
                    api.get("/territory"),
                    api.get("/adventurers"),
                ]);
                if (cancelled) return;
                const dormLevel = Number(
                    terr.data?.territory?.structures?.dormitories?.level || 0,
                );
                const CAP_BY_LEVEL = [0, 5, 10, 15, 20, 25, 30, 50];
                const cap = CAP_BY_LEVEL[dormLevel] || 0;
                const current = (advs.data?.adventurers || []).filter(
                    (a) => !a.is_retired,
                ).length;
                setState({ current, cap, dormLevel });
            } catch (_) {
                // best-effort widget: silent failure leaves the banner hidden
            }
        }
        load();
        return () => { cancelled = true; };
    }, []);

    if (!state) return null;
    if (state.current <= state.cap) return null;

    const mustRetire = state.current - state.cap;

    return (
        <div
            data-testid={`overcap-banner-${source}`}
            className="border border-red-400/60 bg-red-500/10 text-red-200 rounded-sm px-4 py-3 mb-4 text-xs flex items-center justify-between gap-3 flex-wrap"
        >
            <span className="flex items-center gap-2">
                <span className="font-bold">⚠</span>
                <span>
                    {t("overcap.banner_text", {
                        current: state.current,
                        cap: state.cap,
                        must_retire: mustRetire,
                    })}
                </span>
            </span>
            <Link
                to="/roster/manage"
                data-testid={`overcap-banner-cta-${source}`}
                className="text-amber font-bold tracking-widest hover:underline"
            >
                {t("overcap.manage_cta")} →
            </Link>
        </div>
    );
}
