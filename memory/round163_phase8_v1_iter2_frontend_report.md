# ROUND 16.3 Phase 8 V1 Iter2 Frontend — Stalle & Cavalcature

**Status**: ✅ COMPLETO
**Data**: 2026-07-01
**Verdetto**: **PHASE 8 V1 OFFICIALLY CLOSED ✅**

---

## 1. Cosa è stato implementato

Frontend completo per la feature Stalla, con pagina hub a 3 tab, mini-card dashboard, integrazione nav, e doppio disclaimer anti-P2W. Zero modifiche a backend, balance, endpoint contract, seed o anti-P2W flags.

### Componenti creati (3)

- **`components/MountCard.jsx`** — card riutilizzabile per singolo mount:
  - Emoji leggera per icona (🐎🪲🦌🐺🦎🐕🐟👻🦅), no immagini pesanti
  - Rarity badge tenue (common/uncommon/rare/epic con colori zinc/green/blue/purple)
  - Dominio + descrizione + lore breve
  - Se posseduta: bordo colorato + badge "ATTIVA" se `is_active`
  - Se non posseduta: opacity ridotta + "Come ottenere: <source_type_it>"
  - Bottoni "Attiva" / "Disattiva" (touch ≥44px mobile, full-width mobile)
  - Export helper `mountEmoji(slug)` e `domainLabelIt(slug)`

- **`components/NarrativeRouteCard.jsx`** — card per rotta narrativa:
  - Nome + descrizione + lore + reward type/name in italiano
  - Status pill: verde `Percorribile` | grigio `✓ Completata` | rosso `Cavalcatura mancante`
  - Bottone "Cavalca la Rotta" solo se `can_travel && !completed`
  - Missing reason mostrato quando `can_travel=false`

- **`components/StablesMiniCard.jsx`** — mini-card dashboard:
  - Icona mount attivo (o 🥾 se a piedi)
  - Count "X/9 sbloccate" (font-mono)
  - CTA `Vai →`
  - Micro-disclaimer anti-P2W: "Solo cosmetico · nessun bonus di gioco"

### Pagina creata (1)

- **`pages/Stables.jsx`** — hub principale:
  - Header con titolo + badge NEW + count possedute + mount attivo
  - CTA "Rivendica il Ronzino" (solo se non ancora claimed)
  - 3 tab: **Le Mie Cavalcature** / **Catalogo Completo** / **Rotte Narrative**
  - Loading state, empty state, toast italiani su ogni azione
  - **Anti-P2W disclaimer visibile completo** in fondo (4 righe, box emerald)

### File modificati (3)

- **`App.js`** — import `Stables` + route `<Route path="/stables">` con `requireGuild`
- **`Dashboard.jsx`** — import + `<StablesMiniCard />` subito sotto `<PvpSeasonMiniCard />`
- **`navMenu.js`** — voce "Stalla" in sezione **Gilda** (dopo Territorio, prima di Cronaca) con `badge: "NEW"` e `testid: "menu-stables"`

---

## 2. Endpoint utilizzati (7)

Tutti già esistenti da Iter1, nessuna modifica:

| Metodo | Path | Uso |
|---|---|---|
| GET | `/api/stables/catalog` | Load tab Catalogo + mini-card |
| GET | `/api/stables/mine` | Load tab Le Mie + mini-card |
| POST | `/api/stables/set-active` | Attiva mount / deseleziona con `mount_slug: null` |
| POST | `/api/stables/quest/starter/claim` | CTA "Rivendica il Ronzino" |
| GET | `/api/stables/narrative-routes` | Load tab Rotte |
| POST | `/api/stables/narrative-routes/{slug}/travel` | Bottone "Cavalca la Rotta" |
| GET | `/api/stables/narrative-rewards/mine` | (Riservato per Phase 8 V2, non usato in questo Iter) |

---

## 3. Anti-P2W disclaimer visibile ×2

1. **Pagina Stables** (`data-testid="stables-antip2w-disclaimer"`): box emerald con 4 righe:
   - "Le cavalcature e le rotte narrative sono **puramente decorative**."
   - "Nessuna cavalcatura modifica potenza, oro, XP, drop rate, reputazione, velocità di viaggio o qualunque parametro competitivo. Le ricompense delle rotte narrative sono **esclusivamente** badge cosmetici, titoli onorifici o frammenti di lore."
   - "Tutti i contenuti della Stalla sono **free-to-earn**: non esiste alcuna via di acquisto con valuta reale."

2. **StablesMiniCard** (`data-testid="stables-mini-antip2w"`): 1 riga italic emerald tenue:
   - "Solo cosmetico · nessun bonus di gioco"

---

## 4. Screenshot verifica (desktop 1920×800 + mobile 375×800)

### Desktop
- Tab "Le Mie": Lupo delle Fronde (Attiva) + Ronzino (Comune, non attivo). Grid 2 colonne, disclaimer emerald visibile in fondo. ✅
- Tab "Catalogo": 9 mount in grid 2 colonne, ognuno con rarità/dominio/descrizione, opacity ridotta per non-owned. ✅
- Tab "Rotte Narrative": 5 rotte con status pill (Percorribile/Completata/Cavalcatura mancante), reward name in italiano. ✅

### Mobile (375px)
- **Horizontal scroll overflow**: 0px ✅
- Layout single-column, tabs scrollabili orizzontalmente
- Bottoni full-width mobile (`w-full md:w-auto`), touch target ≥44px
- Dashboard mini-card visibile sopra Daily Quests con "2/9 sbloccate · Solo cosmetico" ✅

---

## 5. Test build / lint

- ✅ `yarn build` **Compiled successfully** (+3.61 kB gzip su JS main bundle)
- ✅ `yarn lint` (ESLint) **No issues** su tutti i 4 file nuovi (`MountCard`, `NarrativeRouteCard`, `StablesMiniCard`, `Stables`)
- ✅ Warning preesistente `ClassHalls.jsx:248` accettato come noto (non introdotto qui)

---

## 6. Nav / Route

- **Route**: `/stables` → `<ProtectedRoute requireGuild><Stables /></ProtectedRoute>`
- **Nav posizione**: sezione **Gilda** (posizione 5/6, dopo Territorio, prima di Cronaca) — coerente con Stalla = patrimonio di gilda (come Territorio)
- **Badge NEW**: presente sia in nav che nel titolo pagina che nella mini-card dashboard

Motivazione posizionamento nav: la Stalla è infrastruttura di gilda a lungo termine, non un'attività di missione o mondo. Coerente con nav dell'app: `Home / Imprese / Incarichi / Territorio / **Stalla** / Cronaca`.

---

## 7. Regressione

| Endpoint | Status |
|---|---|
| GET `/api/stables/catalog` | 200 ✅ |
| GET `/api/stables/mine` | 200 ✅ |
| GET `/api/stables/narrative-routes` | 200 ✅ |
| GET `/api/stables/narrative-rewards/mine` | 200 ✅ |
| GET `/api/guilds/me` | 200 ✅ |
| GET `/api/pvp-season/current` | 200 ✅ |
| GET `/api/pvp-season/leaderboard/ambash` | 200 ✅ |

**OpenAPI**: 260 paths totali (9 stables come atteso). Nessuna regressione su path esistenti.

---

## 8. Data-testid principali (per test locator)

Pagina Stables:
- `stables-title`, `stables-count`
- `stables-starter-cta`, `stables-claim-starter-btn`
- `stables-tabs`, `stables-tab-{mine|catalog|routes}`
- `stables-mine-list`, `stables-catalog-list`, `stables-routes-list`
- `stables-antip2w-disclaimer`

MountCard: `mount-card-{slug}`, `mount-name-{slug}`, `mount-active-badge-{slug}`, `mount-activate-btn-{slug}`, `mount-deactivate-btn-{slug}`

NarrativeRouteCard: `route-card-{slug}`, `route-name-{slug}`, `route-status-{slug}`, `route-travel-btn-{slug}`

Mini-card: `stables-mini-card`, `stables-mini-active`, `stables-mini-antip2w`

Nav: `menu-stables`

---

## 9. Verifica vincoli critici

- ❌ NO modifiche backend, balance, endpoint contract, anti-P2W flags — ✅ zero modifiche a `/app/backend`
- ❌ NO Phase 8 V2 (-5% bonus) — ✅ solo cosmetic
- ❌ NO seed/migration, NO drop, NO hard delete — ✅ nessuna
- ❌ NO full pytest (P3 debt aperto) — ✅ solo smoke curl
- ❌ NO tocco `test_database` — ✅
- ✅ Mobile-first (`pb-32 md:pb-8`, touch ≥44px, CTA `w-full md:w-auto`) — ✅ verificato mobile 375px, 0px overflow
- ✅ Italiano ovunque — ✅ 100% IT (titoli, descrizioni, toast, disclaimer, status, error messages)
- ✅ Tema dark coerente — ✅ zinc-950 background, zinc-800 borders, green-500 accent
- ✅ **Anti-P2W disclaimer visibile ×2** — ✅ verificato con data-testid + screenshot

---

## 10. Regressioni note

**Nessuna**. Solo warning preesistente `ClassHalls.jsx:248` (missing dep 'load' in useEffect) — non introdotto in questo Iter, accettato come stato pre-esistente.

---

## 11. Next Action Items

1. **Phase 8 V2** — Rotte narrative sui 3 domini restanti (ambash, irthe, nathos) + variante esplorativa con `-5% travel time` opzionale (P2, esplorativo non combat)
2. **P3 debt residuo** — pytest HTTP admin bypass su prod-dev DB (documentato in `pytest_db_isolation_policy.md`)
3. **Round 16.4** — nuovo focus da decidere con user

---

## Verdetto finale

**PHASE 8 V1 OFFICIALLY CLOSED ✅**

Backend Iter1 (28/28 pytest + 78/78 regression baseline) + Frontend Iter2 (build+lint pulito, mobile-first, anti-P2W ×2, screenshot verificati desktop+mobile) = feature completa, funzionalmente giocabile, anti-P2W esplicito e verificato runtime + UI.
