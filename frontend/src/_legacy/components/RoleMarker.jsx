// Phase 19.2 — P2.1 ASCII role markers.
// Decorative-only prefix used in adventurer / team / report lists.
// Tank → [T] · Healer → [+] · DPS → [D] · Ranger → [R] · Mage → [M] · Support → [S]
//
// Usage:
//   <RoleMarker role="Tank" />              // [T]
//   <RoleMarker role="Healer" withLabel />  // [+] Healer
//
// Pure presentation. No click handlers, no filters. Safe to drop anywhere.

const MARKERS = {
    tank: "[T]",
    healer: "[+]",
    dps: "[D]",
    ranger: "[R]",
    mage: "[M]",
    support: "[S]",
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
                <span className="text-muted-foreground">{role}</span>
            )}
        </span>
    );
}

export { MARKERS, markerFor };
