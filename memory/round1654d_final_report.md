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
