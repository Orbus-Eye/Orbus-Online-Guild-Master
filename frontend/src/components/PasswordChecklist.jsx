import { checkPasswordPolicy } from "../lib/passwordPolicy";

/**
 * ROUND 16.5.4a — Checklist dinamica dei 4 requisiti password.
 *
 * Rende visivo lo stato di ogni requisito mentre l'utente digita:
 *   ✓ verde = soddisfatto
 *   ✗ rosso = mancante
 *
 * Usa il helper condiviso `checkPasswordPolicy` (mirror del validator
 * backend). Ottimizzato mobile: dimensioni compatte + wrap naturale.
 */
export default function PasswordChecklist({ password, testid = "pw-checklist" }) {
    const p = checkPasswordPolicy(password);
    const rows = [
        { key: "length", ok: p.length, label: "Almeno 8 caratteri" },
        { key: "upper", ok: p.upper, label: "Almeno una lettera maiuscola" },
        { key: "digit", ok: p.digit, label: "Almeno un numero" },
        { key: "special", ok: p.special, label: "Almeno un carattere speciale" },
    ];
    return (
        <ul
            data-testid={testid}
            className="mt-2 space-y-1 text-[11px] leading-snug"
        >
            {rows.map((r) => (
                <li
                    key={r.key}
                    data-testid={`${testid}-${r.key}`}
                    data-ok={r.ok ? "true" : "false"}
                    className={`flex items-center gap-2 ${
                        r.ok ? "text-emerald-500" : "text-muted-foreground"
                    }`}
                >
                    <span
                        className={`inline-block w-3 text-center font-bold ${
                            r.ok ? "text-emerald-500" : "text-destructive"
                        }`}
                        aria-hidden="true"
                    >
                        {r.ok ? "✓" : "✗"}
                    </span>
                    <span>{r.label}</span>
                </li>
            ))}
        </ul>
    );
}
