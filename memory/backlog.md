# Orbus Online — Backlog (P3 / debt / warnings tracker)

**Scope**: raccoglie WARN e Issue P3 emerse dai `e1_tester` pass senza
promuoverle in P0/P1 immediatamente. Nessuna deadline: verranno
schedulate in round dedicati.

Il file `BACKLOG.md` (uppercase) è dedicato agli addendum di TASK per
round attivi. Questo `backlog.md` (lowercase) è l'elenco piatto di
warnings/debt tracker persistente cross-round.

---

## Round 16.5.2 — Admin Polish (pianificato)

Scope: unificazione UX/tecnica delle pagine admin. Nessun cambio funzionale.

Items:

1. **Admin pages blank screen on F5 reload**
   - Route: `/admin/world-events`, `/admin/tester-tools`
   - Causa probabile: rehydrate admin guard non idempotente
   - Origine: `e1_tester` pass 2 (2026-07-02) Warning #1
   - Sintomo: premendo F5 sulla pagina admin il render ritorna vuoto per
     una frazione di secondo (o resta vuoto se la hydration di `useAuth`
     fallisce prima che `refreshMe()` riceva la risposta cookie-auth).
     Guard `is_admin` valutata prima del boot di `AuthContext.refreshMe()`
     → primo render vede `user === undefined` → race condition.
   - Impatto: solo UX admin. Nessuna leak di dati.

2. **Client-side guard mancante su `/admin/tester-tools`**
   - Origine: `e1_tester` pass 2 (2026-07-02)
   - Sintomo: non-admin vede l'UI del pannello (backend blocca 403 su
     ogni azione → sicurezza OK, UX da sistemare).
   - Fix proposto: montare guard `!user?.is_admin → NotAuthorized`
     (pattern già presente in `AdminOps.jsx`).

3. **`AdminWorldEvents.jsx` usa `axios` raw**
   - File: `/app/frontend/src/pages/AdminWorldEvents.jsx`
   - Origine: audit interno post-Round 16.5.1 E2
   - Sintomo latente: stesso pattern-bug CSRF risolto in
     `AdminTesterTools.jsx` (E2). Il cookie same-origin va comunque,
     ma il header CSRF non viene mai echeggiato → primo POST cookie-auth
     potrebbe trigger 403 (finora non riprodotto perché la flow admin
     su World Events è cookie+bearer misto).
   - Fix proposto: uniformare al wrapper `lib/api.js` (CSRF-aware,
     `formatApiError`, no `Authorization: Bearer` manuale da localStorage).

4. **Hook condiviso `useAdminGuard()`**
   - Generalizzazione dell'item 1 → hook riutilizzabile che ritorna
     `{ status: 'loading' | 'authorized' | 'denied' }` e renderizza uno
     skeleton finché `user === undefined`.
   - Consumer: `Admin`, `AdminOps`, `AdminAudit`, `AdminGameHealth`,
     `AdminWorldEvents`, `AdminTesterTools`.
   - Fix proposto: "Accesso negato" leggibile in italiano, redirect
     coerente su tutte le rotte `/admin/*`.

5. **Stringhe residue in inglese sui componenti admin**
   - `AdminTesterTools.jsx`:
     - `"Carica status"` (bottone) → `"Carica stato"`
     - `"Status caricato"` (toast) → `"Stato caricato"`
     - `"Status: {email}"` (card title) → `"Stato: {email}"`
     - `${tool} eseguito` toast → mappare slug → label italiana
       (`grant-adventurers` → "Assegnazione avventurieri", ecc.)
     - Header `"Admin — Tester Tools"` → `"Admin — Strumenti Tester"`
   - `AdminWorldEvents.jsx`: eventuale audit stringhe (finora non emerse).
   - Origine: audit post-fix i18n F2 (2026-07-02).
   - Fix proposto: passata unica su tutti gli admin component (grep
     `/tester|admin/` pages/).

6. **Nota tecnica cross-item**
   - Il fix i18n F2 di Round 16.5.1 ha toccato solo le 3 label bottone
     principali (`Grant adventurers`, `Set MAX`, `Set MIN`). L'AlertDialog
     title si aggiorna automaticamente perché renderizza `{label}`.

**Priorità**: P3 (nessun blocker, solo polish).

**Vincoli**: no modifiche a balance/reward/drop/XP/PvP/economia.

---

## Convenzioni

- Ogni item elenca: pagina/file, sintomo, root cause sospetta,
  impatto, priorità, fix proposto.
- Chiusura: item risolto → sposta in changelog del round che lo
  esegue e rimuovi da qui.
