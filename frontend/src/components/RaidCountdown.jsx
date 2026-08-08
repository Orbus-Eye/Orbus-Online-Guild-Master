import { useEffect, useState } from "react";

/** ROUND 16.5.1 B.4 UI — Countdown live per raid in_progress.
 *
 * Riceve:
 *  - endsAt: ISO string (`raid.ends_at`)
 *  - remainingSeconds: valore server-side iniziale (evita drift al mount)
 *  - status: `raid.status` per branching (in_progress / completed / …)
 *
 * Rendering:
 *  - status=in_progress e remaining>0 → "Finisce tra Xh Ym Zs"
 *  - status=in_progress e remaining<=0 → "Completato — in attesa di resolution"
 *  - status=completed → "Completato — risultato disponibile"
 *
 * Aggiorna ogni 1s ricalcolando da `endsAt` per evitare drift.
 */
export default function RaidCountdown({ endsAt, remainingSeconds,
                                          status, className = "",
                                          testid = "raid-countdown" }) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (status !== "in_progress") return undefined;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [status]);

  if (status === "completed") {
    return (
      <span className={`text-emerald-400 ${className}`} data-testid={testid}>
        Completato — risultato disponibile
      </span>
    );
  }

  // Calcolo remaining runtime (server-authoritative baseline via endsAt)
  let remaining;
  if (endsAt) {
    const end = new Date(endsAt).getTime();
    if (!Number.isNaN(end)) {
      remaining = Math.floor((end - now) / 1000);
    }
  }
  // Fallback al valore server-side se endsAt manca (raro)
  if (remaining === undefined && typeof remainingSeconds === "number") {
    remaining = remainingSeconds;
  }
  if (remaining === undefined || remaining === null) {
    return (
      <span className={`text-slate-400 ${className}`} data-testid={testid}>
        —
      </span>
    );
  }

  if (remaining <= 0) {
    return (
      <span className={`text-amber-400 ${className}`} data-testid={testid}>
        Completato — in attesa di resolution
      </span>
    );
  }

  return (
    <span className={`font-mono ${className}`} data-testid={testid}>
      Finisce tra {formatDuration(remaining)}
    </span>
  );
}

function formatDuration(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}
