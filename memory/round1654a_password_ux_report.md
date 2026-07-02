# Round 16.5.4a — Registration Password UX Fix (CLOSED ✅)

**Data**: 2026-07-02T16:00Z
**Scope**: nuova policy password Q1-C + payload strutturato italiano + checklist dinamica FE.
**Approvazione PM**: Q1-C, Q2-a, Q3-a.

---

## 1. Policy finale applicata

**8 char + 1 maiuscola + 1 numero + 1 speciale**

| Requisito | Regex |
|---|---|
| Lunghezza | `len(pw) >= 8` |
| Lettera maiuscola | `[A-Z]` |
| Numero | `\d` |
| Carattere speciale | `[!@#$%^&*(),.?":{}|<>[\]/_\-+=~\`'\\]` |

**Applicata a**:
- `POST /api/auth/register` (`auth/routes.py:78`)
- `POST /api/auth/password-reset/confirm` (`auth/routes.py:167`)

**NON applicata a** `POST /api/auth/login` (retro-compatibilità: gli utenti pre-fix conservano il login).

---

## 2. File backend modificati

- `/app/backend/app/core/security.py`
  - Aggiunte regex `PASSWORD_REGEX_UPPER` + `PASSWORD_REGEX_SPECIAL`
  - Aggiornato `PASSWORD_RULES_MESSAGE` in italiano
  - Riscritto `validate_password_strength()` con 4 requisiti + payload strutturato

**Nessun altro file backend toccato.** Nessuna modifica DB, nessun nuovo endpoint.

---

## 3. File frontend modificati/creati

- **NEW** `/app/frontend/src/lib/passwordPolicy.js` — helper `checkPasswordPolicy(pw)` + costante `PASSWORD_POLICY_MESSAGE`, mirror esatto del validator backend.
- **NEW** `/app/frontend/src/components/PasswordChecklist.jsx` — checklist dinamica riutilizzabile.
- **MOD** `/app/frontend/src/pages/Register.jsx` — validazione client con `checkPasswordPolicy`, checklist inline, bottone submit disabilitato finché policy KO o password mismatch, hint "Le password non coincidono" inline.
- **MOD** `/app/frontend/src/pages/PasswordResetConfirm.jsx` — stessa checklist + validazione client + testo istruzioni tradotto in italiano + button label italiano.

---

## 4. Checklist UI visibile in registrazione

Sotto il campo password (e sotto "Nuova password" nel reset):

```
REQUISITI PASSWORD
✓ Almeno 8 caratteri
✗ Almeno una lettera maiuscola
✗ Almeno un numero
✗ Almeno un carattere speciale
```

Ogni riga aggiorna in tempo reale mentre l'utente digita:
- Verde (`text-emerald-500`) + `✓` se soddisfatto (attributo `data-ok="true"`)
- Rosso `✗` grigio testo se mancante (`data-ok="false"`)

`data-testid` per test:
- `register-password-checklist` (contenitore)
- `register-password-checklist-length`, `-upper`, `-digit`, `-special`
- `pwreset-password-checklist-*` (specular per reset)

Sotto conferma password, hint inline "Le password non coincidono" quando differiscono (`data-testid="register-mismatch-hint"` / `pwreset-mismatch-hint`).

Il bottone submit è disabilitato (`disabled={!canSubmit}`) finché tutti i 4 requisiti + match confirm password non sono soddisfatti — evita di sprecare una round-trip verso il backend.

---

## 5. Messaggio backend strutturato italiano (payload esatto)

```json
{
  "detail": {
    "code": "password.requirements_not_met",
    "user_message": "La password deve contenere almeno 8 caratteri, una lettera maiuscola, un numero e un carattere speciale."
  }
}
```

HTTP status: **400**.

Il helper `formatApiError()` esistente (`lib/api.js`) estrae automaticamente `detail.user_message` → il toast e l'errore inline mostrano il messaggio italiano leggibile senza cambiamenti al frontend error-handling.

---

## 6. Register test (esiti sulle 5 password)

Verificato via `pytest tests/backend_round1654a_test.py -k policy` con `ISOLATED_HTTP_TESTS=1` su `orbus_r16_test`:

| Password | HTTP | Rifiuto causa | Atteso | Esito |
|---|:-:|---|:-:|:-:|
| `password` | 400 | manca maiuscola + numero + speciale | ❌ | ✅ PASS |
| `Password1` | 400 | manca speciale | ❌ | ✅ PASS |
| `password1!` | 400 | manca maiuscola | ❌ | ✅ PASS |
| `Password!` | 400 | manca numero | ❌ | ✅ PASS |
| `Password1!` | 201 | tutti i requisiti soddisfatti | ✅ | ✅ PASS |

Ogni 400 include `detail.code = "password.requirements_not_met"` + `user_message` italiano.

---

## 7. Change-password test

`POST /api/auth/password-reset/confirm` con `new_password: "weak"` (troppo corta + no upper/digit/special):
- HTTP 400
- `detail.code = "password.requirements_not_met"`
- `user_message` italiano

Confermato: la stessa `validate_password_strength()` è chiamata prima di `confirm_password_reset()`. Nessun endpoint di change-password separato esiste (l'unico flusso di cambio è via reset).

---

## 8. Frontend lint/build

- ✅ ESLint `security.py` (Python): 0 errori
- ✅ ESLint `passwordPolicy.js`: 0 issues
- ✅ ESLint `PasswordChecklist.jsx`: 0 issues
- ✅ ESLint `Register.jsx`: 0 issues
- ✅ ESLint `PasswordResetConfirm.jsx`: 0 issues (rimosso `eslint-disable` obsoleto)
- ✅ Webpack: `Compiled successfully!` (3 hot reload confermati nei log)

---

## 9. Backend test isolati

**Suite `backend_round1654a_test.py`**: **8/8 PASS** ✅

Dettaglio:
- `test_register_password_policy[password]` → PASS (400 rifiuto)
- `test_register_password_policy[Password1]` → PASS (400 rifiuto)
- `test_register_password_policy[password1!]` → PASS (400 rifiuto)
- `test_register_password_policy[Password!]` → PASS (400 rifiuto)
- `test_register_password_policy[Password1!]` → PASS (201 accettata)
- `test_register_rejects_password_missing_special` → PASS (case P0 esplicito)
- `test_change_password_uses_same_policy` → PASS (password-reset/confirm applica policy)
- `test_existing_users_login_still_works` → PASS (login continua a funzionare)

Comando: `ISOLATED_HTTP_TESTS=1 pytest tests/backend_round1654a_test.py` su `orbus_r16_test` port 8002.

---

## 10. Conferma NESSUNA modifica a login/sessioni/cookie/CSRF

- ❌ `POST /api/auth/login` (`auth/routes.py:96`): invariato. `verify_password()` (bcrypt check) NON è cambiato.
- ❌ Nessuna modifica a `_set_access_cookie`, `_set_csrf_cookie`, `_clear_auth_cookies`.
- ❌ `CSRFMiddleware` (`app/core/csrf.py`): invariato.
- ❌ Refresh token flow (`_consume_refresh_token`, `_revoke_refresh_token`): invariato.
- ❌ JWT create/decode (`create_access_token`, `decode_token`): invariato.
- ❌ Guard `get_current_user`: invariato.
- ✅ Test `test_existing_users_login_still_works` prova la retro-compatibilità.

---

## Note

- **Retro-compatibilità utenti esistenti**: gli hash bcrypt salvati NON vengono ri-validati al login. Chi si è registrato con password che non soddisfano la nuova policy continua a fare login normalmente. La nuova policy vale solo per:
  1. Nuovi register
  2. Cambio password via reset link email
- **Verifica manuale via curl** (opzionale per PM):
  ```bash
  API=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2)
  curl -s -X POST "$API/api/auth/register" \
       -H "Content-Type: application/json" \
       -d '{"email":"t@orbus.test","password":"Password1","username":"t"}' \
       | python3 -m json.tool
  # Atteso: 400 detail.code=password.requirements_not_met
  ```

**Round 16.5.4a CLOSED — pronto per revisione utente.**
