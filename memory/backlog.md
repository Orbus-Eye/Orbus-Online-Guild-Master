# Orbus Online — Backlog (P3 / debt / warnings tracker)

**Scope**: raccoglie WARN e Issue P3 emerse dai `e1_tester` pass senza
promuoverle in P0/P1 immediatamente. Nessuna deadline: verranno
schedulate in round dedicati.

Il file `BACKLOG.md` (uppercase) è dedicato agli addendum di TASK per
round attivi. Questo `backlog.md` (lowercase) è l'elenco piatto di
warnings/debt tracker persistente cross-round.

---

## R16.5.1 — Warnings da `e1_tester` (pass 2, 2026-07-02)

### W1 — Admin routes: schermata bianca su reload (F5) — P3
- **Pagine affette**: `/admin/world-events`, `/admin/tester-tools`
- **Sintomo**: premendo F5 (hard reload) sulla pagina admin il render
  ritorna vuoto per una frazione di secondo (o resta vuoto se la
  hydration di `useAuth` fallisce prima che `refreshMe()` riceva la
  risposta cookie-auth).
- **Root cause sospetta**: guard `is_admin` valutata prima del boot
  di `AuthContext.refreshMe()`. Il primo render vede `user === undefined`
  → il guard reindirizza o mostra placeholder → post-hydrate il
  componente monta ma con race condition su fetch.
- **Impatto**: solo UX admin (utenti finali non usano queste pagine).
  Nessuna leak di dati, nessun errore console bloccante.
- **Priorità**: **P3** — non blocca funzionalità core, workaround:
  navigare via link interno anziché reload.
- **Nota tecnica**: allargare fix a tutti gli admin components
  (`Admin`, `AdminOps`, `AdminAudit`, `AdminGameHealth`,
  `AdminWorldEvents`, `AdminTesterTools`) usando un pattern condiviso
  `useAdminGuard()` che ritorna `{ status: 'loading' | 'authorized' |
  'denied' }` e renderizza uno skeleton finché `user === undefined`.
- **Fix proposto**: round dedicato "Admin Guard UX P3".

### W2 — `AdminWorldEvents.jsx` usa ancora axios raw — P3
- **File**: `/app/frontend/src/pages/AdminWorldEvents.jsx`
- **Sintomo**: stesso pattern di CSRF-exposure risolto in
  `AdminTesterTools.jsx` (E2). Attualmente funziona SOLO perché tutti
  gli endpoint touched (`activate`/`deactivate`/`duplicate`/`create`)
  vanno con Bearer localStorage — che post ROUND 11.4a NON esiste più
  → potrebbe fallire silenziosamente con 401 → autologout.
- **Verifica richiesta**: se `AdminWorldEvents` è già stato usato con
  successo su prod post-11.4a è per via del cookie same-origin che
  ha bypassato il Bearer, ma la CSRF header NON viene echeggiata →
  primo POST cookie-auth **potrebbe** trigger 403 (stessa root cause
  del bug E2 su Tester Tools).
- **Impatto potenziale**: bassa probabilità (l'ammin è un ruolo
  singolo, e nel pass 2 non ha triggerato 403 su World Events forse
  perché il primo `axios.get` catalog è stato eseguito prima che il
  browser injectasse il cookie). Va comunque uniformato.
- **Priorità**: **P3** — allineare a `api` wrapper condiviso in un
  round "Frontend axios cleanup" (grep `import axios from "axios"`
  nel folder `pages/` → 5 file: `AdminWorldEvents.jsx`, `Arena.jsx`,
  `Leaderboard.jsx`, `Seasons.jsx`).
- **Fix proposto**: refactor 4-5 file rimanenti allo stesso wrapper
  usato in `AdminOps.jsx` (già cookie-auth+CSRF-safe).

---

## Convenzioni

- Ogni item elenca: pagina/file, sintomo, root cause sospetta,
  impatto, priorità, fix proposto.
- Chiusura: item risolto → sposta in changelog del round che lo
  esegue e rimuovi da qui.
