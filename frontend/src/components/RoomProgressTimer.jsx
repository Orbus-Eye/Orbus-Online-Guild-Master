// FASE 9P — Barra di avanzamento temporale della stanza corrente.
//
// Componente PURO lato dati: riceve i valori autoritativi del server
// (durata effettiva + secondi residui calcolati dal backend al fetch)
// e anima SOLO la visualizzazione, un tick al secondo. Nessuna
// scrittura verso il backend: il riallineamento avviene col refetch
// periodico della pagina (poll 5s) e con `onExpired` quando il
// countdown tocca zero.
//
//   inizio stanza → 0% · metà tempo → 50% · fine stanza → 100%
//   tempo residuo scritto DENTRO la barra, centrato, senza layout
//   shift (altezza fissa + tabular-nums).

import { useEffect, useRef, useState } from "react";

/** "43s" · "3m 42s" · "1h 12m" — mai negativo. */
export function formatRemaining(totalSeconds) {
    const s = Math.max(0, Math.floor(Number(totalSeconds) || 0));
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${sec}s`;
    return `${sec}s`;
}

/** progress = elapsed / total, clampato in [0, 100]. */
export function progressPercent(remainingSeconds, durationSeconds) {
    const total = Number(durationSeconds) || 0;
    if (total <= 0) return 100;
    const remaining = Math.max(0, Number(remainingSeconds) || 0);
    const elapsed = total - Math.min(remaining, total);
    return Math.min(100, Math.max(0, (elapsed / total) * 100));
}

/** Il timer compare SOLO sulla stanza realmente attiva (niente timer su
 *  stanze completate/future, bivi o attese di scelta). */
export function shouldShowRoomTimer(expedition, roomIdx) {
    return Boolean(
        expedition
        && expedition.status === "in_progress"
        && expedition.mode === "rooms"
        && expedition.room_state === "in_room"
        && roomIdx === expedition.current_room_idx
        && Number(expedition.room_duration_seconds) > 0,
    );
}

export default function RoomProgressTimer({
    durationSeconds,
    secondsRemaining,
    onExpired,
}) {
    const [remaining, setRemaining] = useState(
        Math.max(0, Number(secondsRemaining) || 0),
    );
    const expiredFiredRef = useRef(false);
    const onExpiredRef = useRef(onExpired);
    onExpiredRef.current = onExpired;

    // Riallineamento al server: ogni refetch della pagina aggiorna la
    // prop e il countdown locale si risincronizza (niente drift).
    useEffect(() => {
        const synced = Math.max(0, Number(secondsRemaining) || 0);
        setRemaining(synced);
        if (synced > 0) expiredFiredRef.current = false;
    }, [secondsRemaining]);

    // Tick locale 1s (solo visuale, zero chiamate di rete).
    useEffect(() => {
        const timer = setInterval(() => {
            setRemaining((r) => Math.max(0, r - 1));
        }, 1000);
        return () => clearInterval(timer);
    }, []);

    // Countdown a zero → UNA richiesta di riallineamento al parent
    // (che ha già il poll 5s: nessun loop aggressivo).
    useEffect(() => {
        if (remaining <= 0 && !expiredFiredRef.current) {
            expiredFiredRef.current = true;
            if (typeof onExpiredRef.current === "function") {
                onExpiredRef.current();
            }
        }
    }, [remaining]);

    const pct = progressPercent(remaining, durationSeconds);
    const resolving = remaining <= 0;

    return (
        <div
            data-testid="room-progress-timer"
            className="relative mt-1.5 h-6 w-full max-w-md border border-amber/50 rounded-sm bg-background/80 overflow-hidden card-fantasy"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={Math.round(pct)}
        >
            <div
                data-testid="room-progress-fill"
                className="h-full bg-gradient-to-r from-amber/50 to-amber/85 transition-[width] duration-1000 ease-linear"
                style={{ width: `${pct}%` }}
            />
            <span
                data-testid="room-progress-label"
                className="absolute inset-0 flex items-center justify-center text-[11px] font-mono tabular-nums tracking-wide text-foreground drop-shadow-[0_1px_2px_rgba(0,0,0,0.9)]"
            >
                {resolving
                    ? "Completamento in corso…"
                    : `${formatRemaining(remaining)} rimanenti`}
            </span>
        </div>
    );
}
