# R16.5.4d — Mobile Expedition Rewards & Guild Prestige Progression

**Data apertura**: 2026-07-03T11:35:00Z (UTC).
**Round precedente**: R16.5.4c CLOSED & SEALED ✅ (vedi `round1654c_final_report.md` §14 + sezione "R16.5.4c — CLOSED & SEALED"). 64/64 pytest verde, E2E 4/4 accettati dal PM.

**Vincoli tassativi**: no nuove feature; no modifiche a Auto-Equip, seed item, PvP, Stalla, World Boss, economia, premium, drop rate; no hard delete; Dry-Run su ogni write DB.

---

## Sezione 1 — Audit PROBLEMA 1 (Mobile Expedition Rewards)

### 1.1 Setup audit
- Login `tester@orbus.test` / `password123`.
- Expedition target: `8a5f26c0-f050-4ed6-b0c2-6b383b1c7932` (Sewer Nest, Success, 25g reward, 1 loot Driftwood Charm, 0 materials).
- Viewport testati: `390×844` (iPhone 12/13/14), `375×667` (iPhone SE), `430×932` (iPhone 15 Pro Max).
- Screenshot salvati: `/tmp/exp390_top.png`, `exp390_mid.png`, `exp390_bottom.png`.

### 1.2 Componenti frontend rilevanti
| File | Ruolo |
| --- | --- |
| `frontend/src/pages/ExpeditionReport.jsx` | Pagina report post-spedizione (`<main class="max-w-4xl mx-auto px-4 sm:px-6 py-8">`). |
| `frontend/src/components/MobileBottomNav.jsx` | Bottom nav mobile-only (`md:hidden fixed bottom-0 left-0 right-0 z-30`, altezza reale 65px). |
| `frontend/src/index.css` | Global CSS: `body { padding-bottom: calc(4rem + env(safe-area-inset-bottom)); }` (64px + safe area). Reset a 0 su `min-width: 768px`. |

### 1.3 Findings mobile 390×844

Metrics DOM raccolte a scroll max (`scrollY = 1755`, `docHeight = 2599`, `viewportH = 844`):

| Elemento | `top` (viewport) | `bottom` (viewport) | Note |
| --- | --- | --- | --- |
| `[data-testid="mobile-bottom-nav"]` | 779 | 844 | altezza 65 |
| `[data-testid="report-materials-section"]` | 734.75 | **811.75** | ⚠️ estende 32.75px SOTTO il top del bottom nav |
| `[data-testid="report-loot-grid"]` | 603.25 | 710.75 | ok, visibile |
| `body { padding-bottom }` | — | — | `64px` (rilevato via `getComputedStyle`) |

**Bug riprodotto: SÌ (parziale)**. Il footer della pagina report (sezione `:: MATERIALI TROVATI` — vuota nel test case) viene coperto per ~32px dal bottom nav quando si scrolla fino in fondo. Il body ha `padding-bottom: 64px` a coprire il nav (`h-16` = 64px), ma la card empty-state `"Nessun materiale raccolto."` è renderizzata immediatamente dopo il titolo `:: MATERIALI TROVATI` senza margin-bottom extra, e la fine di `<main>` (con `py-8` = 32px bottom padding) non basta a compensare i 65px reali del nav (`h-16` = 64px, ma height rendered = 65 per bordi).

**Cause identificate**:
1. **Off-by-one visivo**: bottom nav = 65px effettivi (`h-16` + border-t 1px), body `padding-bottom = 64px`. Manca 1px + il `border-t` (~1px). Impatto reale: nessun contenuto realmente perso, ma il "safety margin" tra fine contenuto e nav è zero.
2. **Elementi con `mb-*` mancante** sul contenitore radice del footer: `<section data-testid="report-materials-section">` non ha `mb-6` (a differenza delle sezioni sopra `mb-6`), e non ha nemmeno un `pb-*` aggiuntivo per gestire il caso mobile.
3. **Il testo del report non è tagliato**, ma il tester può percepire la lista materiali empty-state come "nascosta" perché il card empty è a filo con la barra tabs.

### 1.4 Cosa NON è un bug

- ✅ Reward `GOLD REWARD` (25g), `TEAM POWER` (320), `FINAL SCORE`, `SUCCESS CHANCE` sono renderizzati in una griglia responsive `grid-cols-2 sm:grid-cols-4` — tutti visibili su tutti e 3 i viewport.
- ✅ XP reward per adventurer (`+18 XP` per ognuno) visibile nella sezione `:: PARTY`.
- ✅ `OGGETTI TROVATI` (`Driftwood Charm`) renderizzato correttamente in card `border border-border bg-card rounded-sm p-3`.
- ✅ `NARRATIVE`, `WHY IT WENT THIS WAY`, `MINACCE E CONTROMISURE`, `EXPEDITION ANALYSIS` tutti scrollabili.
- ✅ Nessun overflow orizzontale (`horizontalOverflow: false` misurato).
- ✅ Nessun `[object Object]` visibile.
- ✅ Empty state italiano corretto: `"Nessun oggetto trovato in questa run."` (loot) e `"Nessun materiale raccolto."` (materiali).
- ❌ Alcune label persistono in inglese: `TEAM POWER`, `SUCCESS CHANCE`, `FINAL SCORE`, `GOLD REWARD`, `Replay This Run` (button), `Save as squad` (link), `back to expeditions` (link), `AFTER-ACTION REPORT`, `NARRATIVE`, `EXPEDITION ANALYSIS`, `PARTY (n)`. **La lingua nel report è mista IT/EN.**

### 1.5 File da modificare (fix proposto)

| File | Modifica proposta |
| --- | --- |
| `frontend/src/pages/ExpeditionReport.jsx` | Aggiungere `pb-24 sm:pb-8` su `<main>` per garantire spazio extra sotto il bottom nav su mobile (oppure `mb-24 sm:mb-6` sull'ultima `<section>`). Localizzare in IT le label sopra elencate (scope stretto: solo questa pagina, no modifiche a i18n globale). |
| `frontend/src/components/MobileBottomNav.jsx` | Nessuna modifica prevista (nav già corretto). |

**NO** modifiche previste a: drop, reward calcolo, PvP, economia, premium.

---

## Sezione 2 — Audit PROBLEMA 2 (Guild Prestige "fermo a Lv3")

### 2.1 Semantica: sono 2 campi diversi

Il DB `guilds` ha **due campi "livello"** distinti:

| Campo | Origine | Update path | Visibilità UI |
| --- | --- | --- | --- |
| `guild.level` (legacy) | Phase 5.5c, default `1` alla creazione. | **Nessun bumping automatico**. Grep `\$inc.*level` su tutto il backend → 0 match. Solo settaggi manuali via admin tool o vecchia migration. | Dashboard `[data-testid="stat-level"]` label `"LIVELLO"`. |
| `guild.guild_level` (Prestigio, R15/R16.A) | Derivato da `guild.guild_xp` via `current_level_for_xp()`. | Aggiornato in `app.achievements.engine.add_guild_xp` a ogni credito XP. | Dashboard `<GuildProgressCard />` label `"PRESTIGIO DI GILDA"` + `"LV PRESTIGIO"`. Pagina `/achievements`. |

**Curva soglie Prestigio** (`app.achievements.levels.xp_required_for_level`):
```
Lv1=0, Lv2=100, Lv3=250, Lv4=500, Lv5=900, Lv6=1500,
Lv7=2200, Lv8=3000, Lv9=4000, Lv10=5000, ...
```
Gap Lv3→Lv4: **+250 XP**. Con expedition +15/success: 17 spedizioni. Con raid +80/victory (cap 1/giorno): 4 giorni. Con resource mission +10: 25 missioni.

### 2.2 Stato di `tester@orbus.test`

Live curl audit (2026-07-03T11:28Z):
```
guild.level (legacy):       15    ← settato manualmente in passato
guild.guild_level (Prestigio): 6
guild.guild_xp:           2115
guild.reputation:          1000
guild.gold:              100625
xp_to_next_level (Lv7):     +85 XP mancanti
last_guild_level_up_at:  2026-07-02T18:01:24Z (Lv5→Lv6 via achievement)
```

Payload `/api/guilds/me` (usato dalla Dashboard) espone: `level=15` (legacy), NON espone `guild_level` né `guild_xp`.

Payload `/api/achievements/summary` (usato da `GuildProgressCard`) espone: `guild_level=6, guild_xp=2115, achievement_points=98, progress.xp_into_level=615, progress.xp_for_next_level=85, next_level_at=2200`.

Il tester NON è "fermo a Lv3". È a Prestigio Lv6.

### 2.3 Distribuzione a livello sistema

Su 289 gilde totali:
- **192 guilde (66%) a Prestigio Lv3 con `guild_xp ≈ 300`** ← plateau naturale.
- 96 guilde a Prestigio Lv0 (mai bumped, `guild_xp = 0`).
- 1 guilda a Prestigio Lv6 (il tester).

Pattern chiaro: le 192 guilde ferme a Lv3 hanno ricevuto **~300 XP da achievement iniziali** (probabilmente unlock starter achievement bundle), poi non hanno completato abbastanza attività per superare i 500 XP di Lv4.

### 2.4 Hook XP verificati

| Hook | File call-site | Amount | Cap/day | Idempotente su | Status |
| --- | --- | --- | --- | --- | --- |
| `on_expedition_completed` | `expeditions/services.py:512` | +15 success / +5 fail | 8 | `expedition_id` | ✅ collegato |
| `on_raid_completed` | `raids/__init__.py:544` + `raids/recovery.py:339` | +80 victory / +40 partial / +15 defeat | 1 | `raid_id` | ✅ collegato |
| `on_resource_mission_completed` | `resources/__init__.py:386` | +10 su success | 6 | `mission_id` | ✅ collegato |

Cap tracker attivo su tester (verificato in `guild_xp_daily_cap_tracker`):
```
expedition_completed  date=2026-07-02  count=1
raid_completed        date=2026-07-02  count=1
```

Audit `guild_xp_gained` per tester (last 15 events): 1 expedition_completed (+15), 1 raid_completed (+80), 18 achievement_unlock (totali +2020). Cap non saturato oggi (2026-07-03).

### 2.5 Audit route decoration

- `add_guild_xp` è la **single-entry-point** per ogni credit XP. Emette `guild_xp_gained` audit event con `xp_amount, source, source_id, new_total_xp, new_level, level_changed`. ✅
- `write_audit` include `related_entity_id` = `source_id` (activity_id) per idempotency dedup. ✅
- Level recompute atomico via `current_level_for_xp` dopo `$inc`. ✅
- `last_guild_level_up_at` settato solo se `new_level > prev_level`. ✅

### 2.6 Cause candidate → verifica

| # | Ipotesi | Verifica | Esito |
| --- | --- | --- | --- |
| 1 | XP guadagnata ma UI cache non aggiornata | `GuildProgressCard` fetcha ogni mount di Dashboard | ⚠️ non c'è polling attivo, ma refresh su navigation. Non blocking. |
| 2 | XP guadagnata ma `prestige_level` non ricalcolato | `add_guild_xp` ricalcola atomicamente in singolo `find_one_and_update` | ✅ nessun bug |
| 3 | XP non guadagnata perché hook non chiamato | Grep call-sites tutti presenti | ✅ hook OK |
| 4 | XP bloccata da cap giornaliero senza messaggio | Cap tracker attivo, ma FE non mostra "cap raggiunto" | ⚠️ UX gap (non blocking) |
| 5 | Formula soglie errata | Test `xp_required_for_level` presenti e passanti | ✅ curva OK |
| 6 | **Tester confonde `guild.level` legacy vs Prestigio** | Dashboard mostra ENTRAMBI: `LIVELLO N` (legacy) + `Lv M` (Prestigio) | ⚠️ **ambiguità critica** |
| 7 | Admin `Set MAX` ha creato stato incoerente | Nessuna evidenza; solo tester ha `level=15` | ✅ nessun bug diffuso |
| 8 | Activity sweep non triggera XP | Sweep chiama hook completions | ✅ verificato in call-site expeditions |
| 9 | Resource mission hook non collegato | Presente in `resources/__init__.py:386` | ✅ collegato |
| 10 | Raid hook non collegato | Presente in `raids/__init__.py:544` + `recovery.py:339` | ✅ collegato |
| 11 | Expedition hook funziona solo in alcuni endpoint | Presente in `services.py:512` (chiamato da tutti gli endpoint di completion) | ✅ collegato |

**Root cause probabile**: **#6 — ambiguità semantica**. Il tester probabilmente sta guardando la Dashboard di una gilda "normale" (non tester@orbus.test) dove `guild.level = 1` (legacy) e `Prestigio Lv3` (nuovo). La UI mostra due "livelli" senza gerarchia chiara. Se il tester interpreta `Prestigio Lv3` come "il livello della gilda" e vede che non sale rapidamente, percepisce "fermo a Lv3" perché il gap Lv3→Lv4 richiede 250 XP (~17 spedizioni o ~4 giorni di raid).

### 2.7 Fix ancora NON applicato (blocking decision del PM)

Prima di procedere serve decisione UX. Vedi Sezione 3 (Domande al PM).

---

## Sezione 3 — Domande al PM (BLOCKING)

Prima di implementare fix su Problema 2, servono 2 decisioni PM:
1. **Terminologia UI**: che fare del campo legacy `guild.level`?
2. **Account tester**: qual è la gilda "ferma a Lv3" segnalata? (`tester@orbus.test` è a Lv6, non a Lv3).

Vedi la conversazione con il PM per le risposte.

---

## Sezione 4 — Decisioni PM & Fix applicati (2026-07-03T11:50Z)

Decisioni PM ricevute post-audit (msg del 2026-07-03):
- **1-C** Prestigio: pattern sistemico UX; nessun rebalancing curve/pesi XP; Dashboard più chiara + copy dinamico "cosa fare per salire".
- **2-A** Legacy `guild.level`: NASCONDI dalla Dashboard player-facing (non eliminare dal DB).
- **3-II** Mobile Report: padding fix + localizzazione IT completa.
- Extra: `KeyError: 'library'` fuori scope → nuova entry R16.5.4e in backlog.

### 4.1 Backlog aggiornato

Aggiunta sezione **"Round 16.5.4e — Territory KeyError Audit (PLANNED, P3)"** in `/app/memory/backlog.md`:
- Scope: `app/territory/services.py:53` + `structures.py:174` KeyError `'library'`.
- Strategie candidate: (a) fallback graceful, (b) migration idempotente, (c) add `library` al catalog.
- Vincoli: no hard delete di document territory; round DEDICATO.

### 4.2 Fix Mobile Report — File modificato

**File**: `frontend/src/pages/ExpeditionReport.jsx`

**Diff sintetico**:

| Change | Before | After |
| --- | --- | --- |
| Padding main | `<main class="max-w-4xl mx-auto px-4 sm:px-6 py-8">` | `<main class="max-w-4xl mx-auto px-4 sm:px-6 py-8 pb-24 sm:pb-8">` |
| Header report | `:: AFTER-ACTION REPORT` | `:: REPORT SPEDIZIONE` |
| Back link | `← back to expeditions` | `← Torna alle spedizioni` |
| Stat cell 1 | `TEAM POWER` | `POTERE SQUADRA` |
| Stat cell 2 | `SUCCESS CHANCE` | `PROBABILITÀ DI SUCCESSO` |
| Stat cell 3 | `FINAL SCORE` | `PUNTEGGIO FINALE` |
| Stat cell 4 | `GOLD REWARD` | `ORO GUADAGNATO` |
| Narrative | `:: NARRATIVE` | `:: NARRATIVA` |
| Analysis | `:: EXPEDITION ANALYSIS` | `:: ANALISI SPEDIZIONE` |
| Party | `:: PARTY ({n})` | `:: SQUADRA ({n})` |
| Replay btn | `Replay This Run` / `Starting…` | `Ripeti questa spedizione` / `Avvio…` |
| Replay title | `Dispatch the same team again` / `Cannot replay` | `Rimanda in missione la stessa squadra` / `Impossibile ripetere ora` |
| Save squad btn | `💾 Save as squad` | `💾 Salva squadra` |
| Sealed hint | `results sealed until party returns` | `risultati bloccati finché la squadra non torna` |
| Not-found | `:: NOT FOUND` / `That expedition is not in your guild log.` / `← back to expeditions` | `:: NON TROVATA` / `Questa spedizione non è nel registro della tua gilda.` / `← Torna alle spedizioni` |

Le stringhe IT sono hardcoded (scope stretto solo `ExpeditionReport.jsx`, senza toccare `i18n/lang/*.json`). Il language switch EN nel resto della UI resta funzionante ma il report è sempre in italiano — coerente con la regola PM "❌ testo in inglese nel report".

**Verifica scanner blacklist** (viewport 390×844 scrolled bottom, JS eval su `document.body.textContent`):
```
enBanned = ["TEAM POWER","SUCCESS CHANCE","FINAL SCORE","GOLD REWARD",
            "Replay This Run","AFTER-ACTION REPORT","NARRATIVE",
            "EXPEDITION ANALYSIS","PARTY (","Save as squad","results sealed"]
englishStringsLeaked: []   ✅ zero leak
```

**Verifica padding fix** (viewport 390×844 scrolled bottom, spedizione `8a5f26c0-...`):
```
BEFORE FIX: materialsBottom=811.75  bottomNavTop=779  → COPERTO 32.75px
AFTER FIX:  materialsBottom=747.75  bottomNavTop=779  → gap 31.25px  ✅
Viewport 375×667:
AFTER FIX:  materialsBottom=570.75  bottomNavTop=602  → gap 31.25px  ✅
```

Screenshot: `/tmp/afterfix_exp_top_390.png`, `afterfix_exp_bottom_390.png`, `afterfix_exp_bottom_375.png`, `afterfix_dashboard_390.png`.

### 4.3 Fix Prestigio Dashboard

**File 1**: `frontend/src/pages/Dashboard.jsx`
- Rimossa `<Stat label={t("dashboard.stats.level")} value={guild.level} testid="stat-level" accent />`.
- Comment esplicativo aggiunto (`ROUND 16.5.4d — legacy \`guild.level\` stat card rimossa`).
- Il campo resta in DB (`guilds` collection) intoccato per compatibilità.

**File 2**: `frontend/src/components/GuildProgressCard.jsx`
- Nuovo prompt dinamico "Cosa fare per salire":
  ```jsx
  Ti mancano <span className="text-amber font-mono">{xpToNext}</span> XP Prestigio
  per il prossimo livello (Lv {summary.guild_level + 1}). Completa attività per avanzare:
  ```
- `xpToNext` calcolato runtime da `summary.progress.xp_for_next_level` (payload backend, no hardcoding).
- Lista attività invariata (Completa una spedizione +15 XP / Vinci un raid +80 XP / Completa una missione risorse +10 XP).

**Verifica frontend** (tester@orbus.test viewport 390×844):
```
data-testid="stat-level":               NON presente (rimosso)          ✅
data-testid="guild-progress-card":      presente                        ✅
data-testid="card-guild-level":         "Lv 6"                           ✅
data-testid="xp-to-next-level-hint":   "Ti mancano 85 XP Prestigio per   ✅
                                         il prossimo livello (Lv 7).
                                         Completa attività per avanzare:"
Card XP bar text:                       "615 / 700 XP Prestigio"         ✅
```

Screenshot: `/tmp/dash_top_390.png`, `dash_prestige_390.png`.

### 4.4 Verifica hook XP (evidence audit log, last 30 days system-wide)

Aggregazione `audit_log.guild_xp_gained` per source:

| Source | Events | XP total | Note |
| --- | --- | --- | --- |
| `achievement_unlock` | 578 | +86020 | ✅ hook attivo, massiccio uso |
| `expedition_completed` | 1 | +15 | ✅ hook attivo (verificato con `source_id=8a5f26c0-f050-4ed6-b0c2-6b383b1c7932` — spedizione tester Sewer Nest) |
| `raid_completed` | 1 | +80 | ✅ hook attivo (verificato con tester@orbus.test, primo raid della gilda) |
| `resource_mission_completed` | 0 | 0 | ⚠️ nessun evento negli ultimi 30 giorni. Codice call-site collegato in `resources/__init__.py:386`. **Non è un bug**, semplicemente nessun player ha completato una resource mission nel periodo osservato. |

**Idempotency**: aggregazione `guild_xp_daily_cap_tracker` per chiave `(guild_id, source, source_id, date_utc_iso)` → 0 duplicati. ✅ no doppio conteggio XP.

**Sample eventi verificati**:
```
expedition_completed:  source_id=8a5f26c0-...  xp=+15  new_total=465  new_level=3  level_changed=False
raid_completed:        xp=+80  new_total=80
```

Nessuna anomalia rilevata sui pesi XP. Curve invariate (Lv3=250, Lv4=500, Lv5=900, Lv6=1500, Lv7=2200, ecc.).

### 4.5 Test browser end-to-end

**Test manuale eseguito** (playwright, tester@orbus.test):

| Test | Viewport | Esito |
| --- | --- | --- |
| Login OK + redirect dashboard | 390×844 | ✅ PASS |
| Dashboard: nessuna stat card `LIVELLO` legacy | 390×844 | ✅ PASS |
| Dashboard: Prestigio card mostra `Lv 6` | 390×844 | ✅ PASS |
| Dashboard: copy dinamico "Ti mancano 85 XP" | 390×844 | ✅ PASS |
| Report spedizione: `MATERIALI TROVATI` non coperto da bottom nav | 390×844 | ✅ PASS (gap 31.25px) |
| Report spedizione: `MATERIALI TROVATI` non coperto da bottom nav | 375×667 | ✅ PASS (gap 31.25px) |
| Report: zero stringhe EN blacklisted nel DOM | 390×844 | ✅ PASS (0/11) |
| Report: reward oro/XP/loot/party visibili | 390×844 | ✅ PASS |
| Report: nessun `[object Object]` renderizzato | 390×844 | ✅ PASS |
| Report: scrollabile (docHeight=2678, viewport=844) | 390×844 | ✅ PASS |
| Nessun overflow orizzontale | 390×844 | ✅ PASS |

Backend pytest: **nessuna modifica al codice backend eseguita in questo round** (R16.5.4d è puramente frontend + bookkeeping). La suite R16.5.4c i18n (64 test) resta verde.

### 4.6 Vincoli riconfermati

- ✅ Nessuna modifica a curve/pesi XP (Lv3=250, Lv4=500, ...): confermato via `git diff` su `app/achievements/levels.py` = 0 righe.
- ✅ Nessuna modifica ai valori dei hook XP (+15 exp / +80 raid / +10 resource): confermato via `git diff` su `app/achievements/xp_hooks.py` = 0 righe.
- ✅ Nessun hard delete: `git grep 'delete_one\|delete_many'` non modificato in questo round.
- ✅ Nessuna modifica a drop/reward/economia/PvP/premium/World Boss/Stalla/seed item/Auto-Equip.
- ✅ `territory/services.py` NON toccato in questo round (tracciato in R16.5.4e).
- ✅ Legacy `guild.level` NASCOSTO ma NON eliminato dal DB (`guild.level=15` di tester@orbus.test resta persistito).

### 4.7 Output finale — riepilogo per PM

1. **Fix mobile applicato**: `ExpeditionReport.jsx` con `pb-24 sm:pb-8` su `<main>` + 15 stringhe hardcoded IT (vedi tabella §4.2). Zero leak EN.
2. **Stringhe report tradotte**: 15 traduzioni applicate (tabella completa §4.2).
3. **Screenshot mobile prima-dopo**: `/tmp/afterfix_*.png` (390×844 + 375×667). `materialsCoveredByNav: false` post-fix.
4. **Legacy `LIVELLO` nascosto**: SÌ. File: `Dashboard.jsx` (1 riga rimossa + comment). Campo DB intatto.
5. **Prestigio Dashboard aggiornata**: `GuildProgressCard.jsx` con copy dinamico `"Ti mancano N XP Prestigio per il prossimo livello (Lv M+1). Completa attività per avanzare:"`. Valori runtime da `summary.progress.xp_for_next_level`. Screenshot `dash_prestige_390.png`.
6. **Hook XP verificati**: expedition +15 ✅, raid +80 ✅, resource_mission +10 ✅ (codice OK, 0 eventi periodo osservato). achievement_unlock +varie ✅. Idempotency ✅ (0 duplicati).
7. **Test PASS**: 11/11 test mobile browser eseguiti (§4.5). Backend pytest R16.5.4c: 64/64 verde (nessuna modifica backend).
8. **No modifiche XP curve/pesi**: confermato.
9. **No hard delete**: confermato.
10. **No modifiche drop/reward/PvP/economia/premium**: confermato.
11. **Territory KeyError**: lasciato fuori scope + entry R16.5.4e in `/app/memory/backlog.md`.

### 4.8 Note per il tester E2E

- Il badge lingua della UI (EN/IT in alto a destra) NON influenza più il Report Spedizione: sarà sempre in italiano (regola PM).
- La Dashboard mostra ora solo un "livello" (`Prestigio di Gilda Lv N`). Il vecchio `LIVELLO 1/15/…` è sparito.
- Il testo "Ti mancano N XP Prestigio per il prossimo livello (Lv M+1)" è dinamico e riflette il payload backend live.
- Su viewport ≤ 430px il `pb-24` su `<main>` garantisce che l'ultima sezione (`MATERIALI TROVATI`) resti sempre completamente visibile sopra il bottom nav.

**Sealing proposto**: subordinato al PASS del prossimo giro `e1_tester` sui viewport 390×844 e 375×667 (mobile) più desktop.
