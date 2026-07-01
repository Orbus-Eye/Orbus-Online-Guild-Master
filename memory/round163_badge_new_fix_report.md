# Round 16.3 — Fix trasversale badge "NEW" nella nav

**Data**: 01 Luglio 2026
**Stato**: ✅ **BADGE NEW FIX CHIUSO**
**Autore**: E1 (main agent)
**Scope**: Solo frontend. Nessuna modifica a `navMenu.js`, backend o dati.

---

## Contesto

`navMenu.js` dichiara `badge: "NEW"` su 10 voci (Incarichi di Sede, World Boss, 4× voci Mondo, Forgia Leggendaria, Forgia di Arfus, Specializzazione Gilda, Patti Commerciali, PvP Continentale) ma i componenti nav non leggevano la property → nessun badge appariva in UI.

## File modificati

| File | Modifica |
|---|---|
| `/app/frontend/src/components/AppHeader.jsx` | Aggiunto componente `<NavBadge label={...} />` esportato + refactor rendering item desktop dropdown (span disabled + Link) a layout `flex items-center justify-between gap-2` con label a sinistra e badge a destra |
| `/app/frontend/src/components/MobileMenuDrawer.jsx` | Import `NavBadge` da `./AppHeader` + refactor rendering item drawer (span disabled + Link) allo stesso pattern flex + badge |
| `/app/frontend/src/components/MobileBottomNav.jsx` | **INVARIATO** — non usa `NAV_SECTIONS`; renderizza `MOBILE_BOTTOM_TABS` (5 slot fissi Home/Avv/Missioni/Econ/Menu), nessuno con `badge`. Nessun fix necessario. |
| `/app/frontend/src/components/navMenu.js` | **INVARIATO** — la property `badge` era già presente |

## Design token — `<NavBadge>`

```jsx
export const NavBadge = ({ label }) => (
    <span
        data-testid={`nav-badge-${String(label).toLowerCase()}`}
        className="shrink-0 px-1.5 py-0.5 text-[9px] font-mono uppercase tracking-wider bg-emerald-500/15 text-emerald-400 border border-emerald-500/40 rounded"
    >
        {label}
    </span>
);
```

- **Colore**: emerald (verde-freddo, coerente con `text-emerald-400` già usato in mini-cards per stati "positivi" — vittorie, delta Elo positivi). Non usa amber (che è l'accent primario, riservato ai CTA/attivi) per differenziarsi cromaticamente dagli item selected.
- **Tipografia**: `font-mono text-[9px] uppercase tracking-wider` — stile "terminal" coerente col resto della UI Orbus.
- **Layout**: `shrink-0` per non essere compresso in dropdown stretti; padding minimale `px-1.5 py-0.5` per non rompere l'altezza riga.
- **Data-testid**: `nav-badge-new` (dinamico su lowercase del label) → un unico testid uniforme per tutti i badge, facile da contare in E2E.

## Rendering pattern uniforme

Sia desktop dropdown (AppHeader) che mobile drawer (MobileMenuDrawer) ora usano:

```jsx
<Link ... className="flex items-center justify-between gap-2 ...">
    <span>{it.label}</span>
    {it.badge && <NavBadge label={it.badge} />}
</Link>
```

Layout: label a sinistra, badge a destra, gap 2 unit. `justify-between` garantisce che il badge sia sempre allineato al bordo destro dell'item, indipendentemente dalla lunghezza della label.

## Build & Lint

```
$ yarn lint AppHeader.jsx MobileMenuDrawer.jsx  → ✅ No issues found
$ yarn build                                    → ✅ Compiled with warnings
   → Solo warning preesistente ClassHalls.jsx:244 (non-blocker, ereditato)

File sizes after gzip:
  361.6 kB (+119 B)  build/static/js/main.483853dd.js
  14.8 kB (+11 B)    build/static/css/main.6a6ca572.css
Done in 11.47s.
```

Delta bundle: **+119 B gzip JS + 11 B gzip CSS** — impatto trascurabile.

## Test visivi (screenshot)

Login `tester@orbus.test` / `password123`, guild lv1.

1. **Desktop viewport 1280×800** — dropdown `Competizione` aperto:
   - `PvP Continentale` → badge `NEW` verde visibile a destra
   - Screenshot `/tmp/desktop_competizione.png`

2. **Desktop viewport 1280×800** — dropdown `Economia` aperto:
   - `Forgia Leggendaria` → NEW ✅
   - `Forgia di Arfus` → NEW ✅
   - `Specializzazione` → NEW ✅
   - `Patti Commerciali` → NEW ✅
   - 4 badge simultanei allineati a destra, tipografia mono coerente
   - Screenshot `/tmp/desktop_economia.png`

3. **Mobile viewport 390×844** — drawer aperto via bottom nav, sezione `Economia` espansa:
   - Identici 4 badge NEW visibili accanto ai relativi item
   - Layout responsive, nessun overflow orizzontale, tap target rispettato (≥44px)
   - Screenshot `/tmp/mobile_drawer.png`

**Conteggi testid `nav-badge-*` rilevati in E2E**:
- Desktop Competizione dropdown open: **1 badge**
- Desktop Economia dropdown open: **4 badge**
- Mobile drawer Economia espansa: **4 badge**

## Compliance vincoli

- ✅ Nessuna modifica backend
- ✅ Nessuna modifica `navMenu.js` (la property `badge` esisteva già)
- ✅ Nessun nuovo endpoint
- ✅ Nessuna modifica balance / economia
- ✅ Coerenza tema dark (emerald è già presente in codebase per stati positivi)
- ✅ Mobile responsive (badge `shrink-0`, layout `flex justify-between gap-2`)
- ✅ Italiano ovunque
- ✅ 3 file target: solo 2 modificati (MobileBottomNav non richiedeva fix, documentato sopra)

## Verdetto

**BADGE NEW FIX CHIUSO ✅**

Il badge NEW ora è visibile ovunque venga dichiarato in `navMenu.js`:
- Desktop dropdown (AppHeader)
- Mobile drawer accordion (MobileMenuDrawer)

Componente `NavBadge` riusabile ed esportato, `data-testid` uniforme per test E2E.

Pronto per orchestrazione `e1_tester` smoke veloce prima di passare a **Phase 7B — Leaderboard PvP settimanale + cosmetici**.
