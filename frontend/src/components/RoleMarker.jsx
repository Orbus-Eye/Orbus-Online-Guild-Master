// Phase 19.2 — P2.1 ASCII role markers.
// Decorative-only prefix used in adventurer / team / report lists.
// Tank → [T] · Healer → [+] · DPS → [D] · Ranger → [R] · Mage → [M] · Support → [S]
//
// Usage:
//   <RoleMarker role="Tank" />              // [T]
//   <RoleMarker role="Healer" withLabel />  // [+] Healer
//
// Pure presentation. No click handlers, no filters. Safe to drop anywhere.

// FASE 9B — ruoli canonici DPS/TANK/HEALER; i marker legacy restano
// solo come fallback di lettura per snapshot storici.
const MARKERS = {
    tank: "[T]",
    healer: "[+]",
    dps: "[D]",
    ranger: "[R]",
    mage: "[M]",
    support: "[S]",
};

const LABELS_IT = {
    tank: "Difensore",
    healer: "Guaritore",
    dps: "Danno",
};

function markerFor(role) {
    if (!role) return "[?]";
    const k = String(role).trim().toLowerCase();
    return MARKERS[k] || "[?]";
}

export default function RoleMarker({ role, withLabel = false, className = "" }) {
    const m = markerFor(role);
    return (
        <span
            data-testid={`role-marker-${(role || "unknown").toString().toLowerCase()}`}
            className={`inline-flex items-center gap-1 text-[10px] font-mono tracking-widest ${className}`}
            title={role || ""}
        >
            <span className="text-amber">{m}</span>
            {withLabel && role && (
                <span className="text-muted-foreground">
                    {LABELS_IT[String(role).trim().toLowerCase()] || role}
                </span>
            )}
        </span>
    );
}

export { MARKERS, markerFor };
