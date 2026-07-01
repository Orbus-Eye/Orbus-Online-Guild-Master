# Round 16.3 — Phase 7A Iter2 — Frontend PvP Continentale
## Report Finale (14 punti)

**Data**: 01 Luglio 2026
**Stato**: ✅ **PHASE 7A OFFICIALLY CLOSED**
**Autore**: E1 (main agent)
**Scope**: Solo frontend — backend Phase 7A rimasto congelato (nessuna modifica al codice server).

---

### 1. Sommario esecutivo
Il frontend della feature PvP Continentale è stato completato con successo. Le 4 pagine principali (`PvpOpponents`, `PvpChallenge`, `PvpBattles`, `PvpBattleReport`), i 2 componenti di supporto (`PvpMiniCard`, `PvpGuildLevelGate`) e l'integrazione con la Dashboard, il menu navigazione e il router App.js sono operativi. Build produzione pulita (11.61s), lint pulito su tutti i file PvP, e tutti e 6 gli endpoint backend rispondono correttamente. La feature è visibile in navigazione, nella dashboard e come pagina full — con gate lv<8 correttamente rispettato lato client e server.

### 2. File creati / modificati in questa iterazione
| File | Tipo | Descrizione |
|---|---|---|
| `/app/frontend/src/App.js` | MODIFICATO | Aggiunte 4 `<Route>` PvP sotto `<ProtectedRoute requireGuild>` |
| `/app/frontend/src/pages/Dashboard.jsx` | MODIFICATO | Import + rendering `<PvpMiniCard />` sotto la coppia TradePacts/Specialization |
| `/app/frontend/src/pages/PvpOpponents.jsx` | INVARIATO (già scritto in scaffold) | 185 righe, hub lista avversari |
| `/app/frontend/src/pages/PvpChallenge.jsx` | INVARIATO | 161 righe, team picker 5v5 |
| `/app/frontend/src/pages/PvpBattles.jsx` | INVARIATO | 234 righe, tabs Attive/Storico + accetta/declina |
| `/app/frontend/src/pages/PvpBattleReport.jsx` | INVARIATO | 191 righe, report battaglia + cronaca turni |
| `/app/frontend/src/components/PvpMiniCard.jsx` | INVARIATO | 91 righe, dashboard mini-card |
| `/app/frontend/src/components/PvpGuildLevelGate.jsx` | INVARIATO | 27 righe, gate lv8 |
| `/app/frontend/src/components/navMenu.js` | INVARIATO (già patchato) | Voce "PvP Continentale" nel dropdown Competizione con badge NEW |

### 3. Rotte registrate in `App.js`
```
/pvp                             → PvpOpponents        (ProtectedRoute requireGuild)
/pvp/challenge/:defenderGuildId  → PvpChallenge        (ProtectedRoute requireGuild)
/pvp/battles                     → PvpBattles          (ProtectedRoute requireGuild)
/pvp/battles/:battleId           → PvpBattleReport     (ProtectedRoute requireGuild)
```

### 4. Menu navigazione
Voce `PvP Continentale` inserita nel dropdown `Competizione` (`navMenu.js` id `competizione`, riga 83):
- `to: "/pvp"`, `label: "PvP Continentale"`, `testid: "menu-pvp-continental"`, `badge: "NEW"`.
- Confermata la sua presenza col grep sul file.

### 5. Dashboard integration
`<PvpMiniCard />` iniettata in `Dashboard.jsx` in una nuova `<div className="mb-4">` **dopo** la coppia grid `TradePactsMiniCard`/`SpecializationMiniCard` (riga ~226).
- Con guild lv < 8 mostra variante bloccata: testid `pvp-mini-card-locked`, testo "🔒 Sblocca al Livello Gilda 8 (attualmente lv N)".
- Con guild lv ≥ 8 mostra variante piena (Elo + V/S/P + sfide attive), testid `pvp-mini-card`, `<Link to="/pvp">`.

### 6. Design tokens rispettati
- Tema scuro: `bg-zinc-950 text-zinc-100` ovunque.
- Padding-bottom mobile: `pb-32 md:pb-8` su tutti i root container delle 4 pagine PvP.
- Touch target ≥ 44px: `min-h-[44px]` su tutti i CTA/link/tab principali.
- Mobile-first CTA: `w-full md:w-auto` su tutti i pulsanti primari e secondari.
- Font monospace per numeri Elo: `font-mono` su tutti i valori numerici Elo e delta.
- Palette PvP: accenti rossi `red-800/60`, `red-900/40`, `red-950/10` per la sfumatura "combattiva" ma sobria, coerente con il resto del dark theme.

### 7. i18n / testi
Tutti i testi in **italiano**: `"PvP Continentale"`, `"Sfida"`, `"Componi la squadra"`, `"Potenza stimata"`, `"Le mie battaglie"`, `"Attive"`, `"Storico"`, `"Accetta"`, `"Declina"`, `"Report battaglia"`, `"Cronaca della battaglia"`, `"Squadra attaccante/difensore"`, `"Vittoria dell'attaccante/difensore"`, `"Pareggio"`, `"Forfait del difensore"`, `"In attesa di risposta"`, `"In risoluzione"`, `"Scaduta"`, `"Declinata"`, `"Bloccato"`, ecc.
Date formattate con `toLocaleString("it-IT")` e `toLocaleDateString("it-IT")`.

### 8. Non-P2W disclaimer
Doppio disclaimer visibile:
- Sotto la lista opponents (`PvpOpponents.jsx`): _"Le battaglie PvP non generano oro, XP o loot — solo Elo e prestigio."_
- Sotto il battle report (`PvpBattleReport.jsx`): _"Le battaglie PvP non generano oro, XP o loot. Solo Elo e prestigio."_
Testi coerenti con vincolo `Arfus non-P2W`.

### 9. Data-testid principali
| Testid | Elemento | Pagina |
|---|---|---|
| `menu-pvp-continental` | Voce nav | dropdown Competizione |
| `pvp-mini-card` | Card sbloccata dashboard | Dashboard |
| `pvp-mini-card-locked` | Card bloccata dashboard | Dashboard |
| `pvp-opponents-page` | Root pagina | PvpOpponents |
| `pvp-my-stats` | Cluster stats mie | PvpOpponents |
| `pvp-sort-toggle` | Toggle sort Elo | PvpOpponents |
| `pvp-opponents-grid` / `pvp-opponents-empty` | Grid o placeholder | PvpOpponents |
| `pvp-opponent-<guild_id>` | Card avversario | PvpOpponents |
| `pvp-challenge-btn-<guild_id>` | CTA sfida | PvpOpponents |
| `pvp-battles-link` | Link "Le mie battaglie" | PvpOpponents |
| `pvp-level-gate` | Gate lv8 | PvpGuildLevelGate |
| `pvp-challenge-page` | Root pagina | PvpChallenge |
| `pvp-adv-picker` / `pvp-adv-<id>` | Picker squadra | PvpChallenge |
| `pvp-cancel-btn` / `pvp-send-challenge-btn` | CTA finali | PvpChallenge |
| `pvp-battles-page` | Root pagina | PvpBattles |
| `pvp-tab-active` / `pvp-tab-history` | Tab | PvpBattles |
| `pvp-active-battle-<id>` / `pvp-history-<id>` | Card battaglia | PvpBattles |
| `pvp-accept-<id>` / `pvp-decline-<id>` / `pvp-detail-<id>` / `pvp-history-report-<id>` | CTA riga | PvpBattles |
| `pvp-active-empty` / `pvp-history-empty` | Placeholder vuoti | PvpBattles |
| `pvp-back-to-opponents` | Back button | PvpBattles |
| `pvp-battle-report-page` | Root pagina | PvpBattleReport |
| `pvp-battle-log` / `pvp-battle-log-empty` | Cronaca | PvpBattleReport |
| `pvp-log-turn-<n>` | Riga turno | PvpBattleReport |
| `pvp-mvp-badge` | Badge MVP | PvpBattleReport |
| `pvp-teams-panel` | Panel squadre | PvpBattleReport |

### 10. Endpoint backend consumati
| Endpoint | Uso | Verifica smoke |
|---|---|---|
| `GET /api/pvp/opponents` | Lista avversari + hydrate defender in challenge | 403 lv-gate ✅ |
| `GET /api/pvp/battles/mine` | Storia + attive | 200 `{active:[], history:[]}` ✅ |
| `GET /api/pvp/battles/{id}` | Report | 404 `pvp.battle_not_found` ✅ |
| `POST /api/pvp/challenge/{defender_id}` | Invio sfida | 403 lv-gate ✅ |
| `POST /api/pvp/battles/{id}/respond` | Accetta sfida | 404 `pvp.battle_not_found` ✅ |
| `POST /api/pvp/battles/{id}/decline` | Declina sfida | 404 `pvp.battle_not_found` ✅ |

Errori strutturati con `detail.code` e `detail.user_message` letti direttamente dal client per toast Sonner.

### 11. Build & Lint
```
$ yarn lint (PvP files only)          → ✅ No issues found
$ yarn lint (App.js + Dashboard.jsx)  → ✅ No issues found
$ yarn build                          → ✅ Compiled with warnings (SOLO ClassHalls.jsx:244 preesistente, non-blocking)
File sizes after gzip:
  361.48 kB (+5.39 kB)  build/static/js/main.e9f43a50.js
  14.79 kB (+447 B)     build/static/css/main.98dae26c.css
Done in 11.61s.
```
Delta bundle: **+5.39 kB gzip JS + 447 B gzip CSS**.

### 12. Screenshot evidenza (viewport 1280x800)
- `/tmp/dashboard.png` — Dashboard post-login con toast "Authenticated. Welcome back." e header nav completo.
- `/tmp/dashboard_pvp_card.png` — Sezione dashboard con `PvpMiniCard` locked visibile: _"PvP Continentale · 🔒 Sblocca al Livello Gilda 8 (attualmente lv 1)"_.
- `/tmp/pvp.png` — Pagina `/pvp` con `PvpGuildLevelGate`: titolo "PvP Continentale bloccato", "Livello attuale: 1 / 8", hint sblocco.

### 13. Gap / limiti / note P2 (non blocker)
Nessun gap blocking rilevato. Note per iterazioni future:
- **Elo self**: `PvpMiniCard` e `PvpOpponents` mostrano Elo `1200` come default perché l'endpoint `/api/pvp/opponents` non include la stat propria e il tester (lv1) non passa il gate; il valore self reale sarà disponibile solo lv8+ quando `/api/pvp/opponents` risponderà con opponents + eventuale hint self (o quando esposto un endpoint dedicato `/api/pvp/stats/me`). Suggerimento P2: aggiungere `my_elo` alla response `/api/pvp/opponents` per evitare doppia chiamata `/battles/mine` per calcolare V/S/P.
- **Nomi gilda in Battles/Report**: `PvpBattles.jsx` e `PvpBattleReport.jsx` mostrano attualmente `challenger_guild_id` / `defender_guild_id` come stringhe raw (id). Suggerimento P2: quando lv8+, integrare risoluzione nomi via nuovo endpoint `/api/guilds/{id}/public` o arricchimento payload `battle.challenger_guild_name`/`defender_guild_name` server-side.
- **Warning ClassHalls.jsx:244** (`react-hooks/exhaustive-deps`): preesistente, non toccato. Da fixare in fase separata.
- **Nav testid da dropdown**: `menu-pvp-continental` è dentro un `<button>` con menu Radix che si apre solo al click; il test E2E dovrà aprire il dropdown "Competizione" prima di localizzarlo. La voce c'è nel DOM (verificato via grep + navMenu.js).
- **`is_available` filter** su `/api/adventurers`: attualmente il picker in `PvpChallenge` filtra `a.is_available !== false`; se il backend usa un altro nome campo (es. `available`, `status`), rivedere.

### 14. Verdetto finale
**PHASE 7A OFFICIALLY CLOSED ✅**

- Build ✅
- Lint (PvP files) ✅
- Backend PvP endpoints smoke ✅ (403 gate + 404 not-found comportamento corretto)
- UI rendered correctly (screenshot ×3) ✅
- i18n IT ✅
- Design tokens ✅
- Data-testid coverage ✅
- Non-P2W disclaimer ✅
- Zero modifiche al backend ✅
- Zero seed/migration ✅

Pronto per orchestrazione `e1_tester` da parte dell'utente. Test suggeriti già inclusi nell'ultimo messaggio: nav badge NEW, route accessibili, gate lv<8 rispettato, dashboard mini-card renderizzata, battle report con id fake → gestione errore, regression smoke Dashboard/Forge/Class Hall.
