# Round 16.5.2 — Visibility Fix Report (hotfix admin control panel)

**Data**: 2026-07-02T07:55Z
**Scope**: cablare 3 rotte admin orfane nel dropdown ACCOUNT desktop + drawer mobile. Nessun cambio backend/DB.
**Origine**: utente ha aperto Control Panel come `tester@orbus.test` e non vedeva `/admin/world-events` e `/admin/tester-tools` (R16.5.1) + `/admin/audit` (R16.A).

---

## 1. File modificati (elenco esatto)

- `/app/frontend/src/components/AppHeader.jsx` — dropdown ACCOUNT desktop, blocco `user?.is_admin` (righe 121-155 pre-fix → 121-186 post-fix).
- `/app/frontend/src/components/MobileMenuDrawer.jsx` — drawer mobile, blocco `user?.is_admin` (righe 161-191 pre-fix → 161-222 post-fix).

**Nessun altro file toccato.** Nessuna modifica backend, DB, env, seed, test.

---

## 2. Voci aggiunte nel dropdown account desktop (AppHeader.jsx)

Ordine finale del gruppo admin:

| Ordine | Label | Rotta | Guard visibilità | `data-testid` |
|:-:|---|---|---|---|
| 1 | Admin | `/admin` | `user?.is_admin` | `desktop-menu-admin` |
| 2 | **Eventi continentali** | `/admin/world-events` | `user?.is_admin` | `desktop-menu-admin-world-events` |
| 3 | **Strumenti tester (TEST ONLY)** | `/admin/tester-tools` | `user?.is_admin && user.email?.endsWith("@orbus.test")` | `desktop-menu-admin-tester-tools` |
| 4 | **Audit** | `/admin/audit` | `user?.is_admin` | `desktop-menu-admin-audit` |
| 5 | Admin Ops | `/admin/ops` | `user?.is_admin` | `desktop-menu-admin-ops` |
| 6 | Game Health | `/admin/game-health` | `user?.is_admin` | `desktop-menu-admin-game-health` |

Le 3 voci **in grassetto** sono le nuove. Ordine allineato al brief PM (Q3-b: subito dopo `Admin`, prima di `Admin Ops`).

---

## 3. Voci aggiunte nel drawer mobile (MobileMenuDrawer.jsx)

Stesse 3 voci nello stesso ordine, con `data-testid` prefissati `mobile-menu-*`:

- `mobile-menu-admin-world-events`
- `mobile-menu-admin-tester-tools` (racchiuso in `{user.email?.endsWith("@orbus.test") && (…)}`)
- `mobile-menu-admin-audit`

Style coerente col pattern esistente: `block px-6 py-3 text-sm text-foreground/85 hover:bg-secondary/40` + `style={{ minHeight: 44 }}` per tap target ≥44px.

---

## 4. Guard applicato (righe inline)

**Desktop (AppHeader.jsx)**:
- `Eventi continentali` e `Audit`: coperti dal wrapper esterno `{user?.is_admin && (…)}` (linea 121).
- `Strumenti tester (TEST ONLY)`: guard inline aggiuntivo linea 144 → `{user.email?.endsWith("@orbus.test") && (…)}`.

**Mobile (MobileMenuDrawer.jsx)**:
- `Eventi continentali` e `Audit`: coperti dal wrapper esterno `{user?.is_admin && (…)}` (linea 161).
- `Strumenti tester (TEST ONLY)`: guard inline aggiuntivo linea 182 → `{user.email?.endsWith("@orbus.test") && (…)}`.

**Nessuna nuova astrazione** (no hook `useTesterToolsAccess()`) — Q5-a rispettato.

Coerenza con backend:
- `/api/admin/world-events/*` chiede solo `Depends(get_admin_user)` → visibilità frontend `is_admin` allineata.
- `/api/admin/audit/*` chiede solo `Depends(get_admin_user)` → visibilità frontend `is_admin` allineata.
- `/api/admin/tester-tools/*` chiede `Depends(get_admin_user)` per il caller + `_is_test_user(target)` con OR su `email.endswith("@orbus.test")` → visibilità frontend `is_admin && email @orbus.test` è **più stretta del backend** (che accetterebbe anche altri admin) ma è la scelta corretta perché il tester tool ha semantica "test-user-only" e il PM ha esplicitamente richiesto questa granularità.

---

## 5. Test eseguiti

### Grep di conferma (post-modifica)

Comando:
```bash
grep -nE "Eventi continentali|Strumenti tester|Audit|admin/world-events|admin/tester-tools|admin/audit|@orbus.test" \
     /app/frontend/src/components/AppHeader.jsx \
     /app/frontend/src/components/MobileMenuDrawer.jsx
```

Risultato:

- **AppHeader.jsx**: 8 match — le 3 label + le 3 rotte + guard `@orbus.test` linea 144 + wrapper `Audit` (unica ricorrenza `Audit`).
- **MobileMenuDrawer.jsx**: 8 match — stessa struttura, righe 174-200.

**Verdetto**: le 3 nuove voci sono presenti in entrambi i componenti con guard e rotte corrette.

### Frontend lint (ESLint)

- `AppHeader.jsx`: ✅ No issues found
- `MobileMenuDrawer.jsx`: ✅ No issues found

### Webpack build (hot reload dev-server)

Log estratto da `/var/log/supervisor/frontend.out.log`:
```
Compiling...
Compiled successfully!
webpack compiled successfully
```

Nessun warning nuovo, nessun error, hot reload OK.

---

## 6. Esito frontend lint / webpack build

| Check | Esito |
|---|:-:|
| ESLint `AppHeader.jsx` | ✅ pass (0 issues) |
| ESLint `MobileMenuDrawer.jsx` | ✅ pass (0 issues) |
| Webpack compile | ✅ `Compiled successfully!` |
| Grep pattern match | ✅ 3 label × 2 file = 6 target confermati |

---

## 7. Conferma NESSUNA modifica backend

- ❌ Nessun file `/app/backend/**` modificato.
- ❌ Nessun endpoint nuovo/modificato.
- ❌ Nessun guard backend allentato.
- ❌ Nessun test backend aggiunto/rimosso.
- ✅ Middleware CSRF (`app/core/csrf.py`) invariato.
- ✅ Guard `get_admin_user`, `_is_test_user`, `_tools_enabled()` invariati.
- ✅ I 2 test E2 CSRF di R16.5.1 restano validi (coprono già le rotte visibili).

---

## 8. Conferma NESSUNA modifica DB

- ❌ Nessuno script di migrazione lanciato.
- ❌ Nessun `update_one`/`update_many` diretto.
- ❌ Nessuna promozione utenti (`is_admin`/`is_test_user`).
- ✅ Stato utenti verificato pre-fix e non toccato:
  - `tester@orbus.test`: `is_admin=True, is_test_user=<assente>` (invariato)
  - `admin@orbus.test`: `is_admin=True, is_test_user=True` (invariato)

---

## 9. Chiusura in backlog

`/app/memory/backlog.md` sezione "Round 16.5.2 — Admin Polish" — rimossi/aggiornati:

- Item precedente "Client-side guard mancante su `/admin/tester-tools`" (era proposta di implementare `useAdminGuard()` in preview) → **superato**: guard di visibilità inline nel menu evita l'ingresso non voluto sulle rotte tester-tools.
- La rotta orfana `/admin/audit` è ora **cablata** — item riferimento chiuso.
- Restano P3 vivi: item 1 (F5 blank), item 3 (`AdminWorldEvents.jsx` axios raw), item 4 (`useAdminGuard()` completo), item 5 (stringhe residue).

---

## 10. Pronto per e2e

**Round 16.5.2 visibility fix pronto per e1_tester** — login `tester@orbus.test`, aprire dropdown ACCOUNT desktop e drawer mobile (via `?viewport=mobile` o breakpoint), verificare 3 nuove voci + click apre le pagine target.

Verifica bonus: login utente non-admin (registrare nuovo user via `/api/auth/register` senza promozione) → nessuna voce admin visibile nel dropdown.
