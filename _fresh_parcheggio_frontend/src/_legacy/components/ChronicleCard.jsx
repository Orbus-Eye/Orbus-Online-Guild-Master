// Phase 16 — Server Chronicle: public read-only activity feed.
import { useEffect, useState, useCallback } from "react";
import { api } from "../lib/api";
import { useT } from "../i18n/I18nContext";


function formatRelative(iso, t) {
    if (!iso) return "";
    const then = new Date(iso).getTime();
    if (Number.isNaN(then)) return "";
    const seconds = Math.max(1, Math.floor((Date.now() - then) / 1000));
    if (seconds < 60) return t("chronicle.now");
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return t("chronicle.min_ago", { n: minutes });
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return t("chronicle.hour_ago", { n: hours });
    const days = Math.floor(hours / 24);
    return t("chronicle.day_ago", { n: days });
}


export default function ChronicleCard({ limit = 15 }) {
    const { t, lang } = useT();
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const load = useCallback(async () => {
        try {
            const { data } = await api.get(`/chronicle?limit=${limit}&lang=${lang || "it"}`);
            setEvents(data.events || []);
            setError(null);
        } catch (err) {
            setError(err?.message || "load_failed");
        } finally {
            setLoading(false);
        }
    }, [limit, lang]);

    useEffect(() => {
        load();
        const id = setInterval(load, 30_000);  // refresh ogni 30s
        return () => clearInterval(id);
    }, [load]);

    return (
        <div
            data-testid="chronicle-card"
            className="border border-border/60 bg-card/40 rounded-sm p-4 font-mono text-[12px]"
        >
            <div className="flex items-baseline justify-between mb-3 gap-2">
                <div className="text-amber tracking-widest text-[11px]">
                    :: {t("chronicle.title")}
                </div>
                <button
                    type="button"
                    onClick={load}
                    data-testid="chronicle-refresh"
                    className="text-[10px] text-muted-foreground hover:text-amber tracking-widest"
                >
                    {t("chronicle.refresh")}
                </button>
            </div>
            {loading ? (
                <div
                    data-testid="chronicle-loading"
                    className="text-[11px] text-muted-foreground"
                >
                    :: {t("chronicle.loading")}
                </div>
            ) : error ? (
                <div
                    data-testid="chronicle-error"
                    className="text-[11px] text-red-400/80"
                >
                    :: {t("chronicle.error")}
                </div>
            ) : events.length === 0 ? (
                <div
                    data-testid="chronicle-empty"
                    className="text-[11px] text-muted-foreground italic"
                >
                    :: {t("chronicle.empty")}
                </div>
            ) : (
                <ul className="space-y-1.5">
                    {events.map((e) => (
                        <li
                            key={e.id}
                            data-testid={`chronicle-event-${e.id}`}
                            className="border-l-2 border-border/40 pl-3 flex items-baseline justify-between gap-3"
                        >
                            <span className="flex-1 min-w-0 truncate text-foreground/90">
                                {e.text}
                            </span>
                            <span className="shrink-0 text-[10px] text-muted-foreground tracking-widest">
                                {formatRelative(e.created_at, t)}
                            </span>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
