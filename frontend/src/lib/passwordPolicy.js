/**
 * ROUND 16.5.4a — Password policy helper (client-side).
 *
 * Mirror della validazione backend (`app/core/security.py::validate_password_strength`).
 * Se una delle due si aggiorna, ricordarsi di allineare l'altra.
 *
 * Policy Q1-C (PM approved 2026-07-02):
 *   - length >= 8
 *   - almeno una lettera MAIUSCOLA
 *   - almeno un NUMERO
 *   - almeno un CARATTERE SPECIALE
 *
 * Il set di caratteri speciali è identico al backend:
 *   [ ! @ # $ % ^ & * ( ) , . ? " : { } | < > [ ] / _ - + = ~ ` ' \ ]
 */

const SPECIAL_REGEX = /[!@#$%^&*(),.?":{}|<>[\]/_\-+=~`'\\]/;

/**
 * @param {string} pw password in chiaro
 * @returns {{length: boolean, upper: boolean, digit: boolean, special: boolean, allValid: boolean}}
 */
export function checkPasswordPolicy(pw) {
    const s = pw || "";
    const length = s.length >= 8;
    const upper = /[A-Z]/.test(s);
    const digit = /\d/.test(s);
    const special = SPECIAL_REGEX.test(s);
    return {
        length,
        upper,
        digit,
        special,
        allValid: length && upper && digit && special,
    };
}

export const PASSWORD_POLICY_MESSAGE =
    "La password deve contenere almeno 8 caratteri, una lettera maiuscola, un numero e un carattere speciale.";
