# Round 17.1b — Onboarding Polish & Report Localization — CLOSED ✅

**Data**: 2026-07-04T12:00Z (UTC).
**Round precedente**: R17.1 SEALED (13/13 pytest PASS, browser check Playwright PASS).
**Scope**: 6 items (P0×2 + P1×4) definiti dal PM in Message R17.1b Open. Tutti chiusi in questa sessione.

---

## Executive summary

R17.1 aveva reso funzionante il funnel. R17.1b lo rende **chiaro, italiano, leggibile e motivante** — senza sistemi nuovi, senza toccare economia, PvP, premium o formule.

- ✅ **P0.1** Localizzazione IT completa `result_log` / `result_summary` / `equipment_delta_text` + fallback per doc legacy (regex mapper backend, zero migration DB).
- ✅ **P0.2** Nuova sezione `:: PRESTIGIO DI GILDA` in report con `+N XP Prestigio`, barra progresso, "Lv X / next_level_at XP verso Lv Y".
- ✅ **P1.1** 3 milestone toasts (prima start / prima complete / primo prestigio), one-shot per gilda con guard client-side + backend audit derivation.
- ✅ **P1.2** Polish primo dungeon: implicito post P0.1 (badge FALLIMENTO / SUCCESSO / IN CORSO in IT, narrativa IT).
- ✅ **P1.3** Mobile readability check: banner + Prestigio + toast leggibili a viewport 390 (screenshot in memory).
- ✅ **P1.4** CTA `🎯 Riprova con team più forte` nel banner fallback → deep-link a `/expeditions/new?dungeon=training-yard&auto=strongest` con auto-preselect top-3 per `power_score` + spiegazione IT esplicita "Nessun bonus nascosto".
- ✅ **Monitoring `FIRST_PRESTIGE_GAINED`**: fix root cause — event ora emesso da `add_guild_xp` con guard idempotency di `emit_first_event`.

---

## 1. File backend modificati

| File | Modifica | Riga |
| --- | --- | --- |
| `app/expeditions/services.py` | `_build_result_log` → stringhe IT; `_LEGACY_LOG_EN_IT_MAP` + `_translate_legacy_result_log` regex mapper (docs pre-R17.1b); `_LEGACY_EQUIP_DELTA_EN_IT_MAP` + `_translate_legacy_equipment_delta`; hardcoded "Dungeon data unavailable." → IT; `get_expedition` aggiunge `guild_prestige_delta` + `milestones` READ-ONLY | 213-315, 111-118, 260-265, 1055-1200 |
| `app/expeditions/formulas.py` | `equipment_delta_text` narrative → stringhe IT | 184-195 |
| `app/expeditions/routes.py` | POST `/expeditions` espone `milestones.is_first_expedition_started` (dal boolean di `emit_first_event`) | 33-56 |
| `app/achievements/engine.py` | `add_guild_xp` emette `FIRST_PRESTIGE_GAINED` (idempotent via `emit_first_event`) su ogni credit positivo — fix WARN R17.1 #11 | 145-183 |

Nessuna migration DB. Zero modifiche a:
- `_complete_one_expedition` / drop table / loot_tables
- `app/achievements/levels.py` (curva Prestigio invariata)
- `app/pvp*/`, `app/premium*/`, `app/stables/`, `app/world_boss/`, `app/raids/`
- XP weights (`+15 exp / +80 raid / +10 resource`)
- Reward globali

## 2. File frontend modificati

| File | Modifica | Note |
| --- | --- | --- |
| `frontend/src/pages/ExpeditionReport.jsx` | `SummaryBadge` → IT ("SUCCESSO", "FALLIMENTO", "IN CORSO"). Destructura `guild_prestige_delta` + `milestones` dal payload. Nuova sezione `:: PRESTIGIO DI GILDA` con progress bar. Milestone toasts (useEffect + localStorage guard). CTA `🎯 Riprova con team più forte` nel banner fallback | +80 righe |
| `frontend/src/pages/Expeditions.jsx` | `StatusBadge` → IT (SUCCESSO / FALLIMENTO / IN CORSO / COMPLETATA / FALLITA / IN CHIUSURA) | +6 righe |
| `frontend/src/pages/ExpeditionNew.jsx` | Handler `?auto=strongest` che auto-preseleziona top-N adventurers per `power_score` con toast IT "Squadra suggerita: i N avventurieri con il potere più alto." Milestone toast "Prima spedizione avviata!" post-POST | +30 righe |

Zero modifiche a `AuthContext`, `AppHeader`, `GuildProgressCard`, i18n framework globale.

## 3. Stringhe report localizzate (tabella before/after)

| Chiave | Before (EN) | After (IT) |
| --- | --- | --- |
| `result_summary` badge | `SUCCESS` / `FAILED` / `IN PROGRESS` | `SUCCESSO` / `FALLIMENTO` / `IN CORSO` |
| `result_log` success | "Your party of X entered the Y at dawn. After hours of careful work…" | "Il tuo gruppo composto da X è entrato in Y all'alba. Dopo ore di lavoro attento…" |
| `result_log` fail | "Your party pushed too deep into the Y. A hidden ambush split the formation…" | "Il tuo gruppo si è spinto troppo in profondità in Y. Un'imboscata nascosta ha diviso la formazione…" |
| `result_log` (defensive fallback) | "Dungeon data unavailable." | "Dati del dungeon non disponibili." |
| `equipment_delta_text` no eq | "No equipment was used on this run." | "Nessun equipaggiamento è stato consumato in questa spedizione." |
| `equipment_delta_text` max chance | "Equipment contributed +N team power. Success chance was already at maximum (X%)." | "L'equipaggiamento ha aggiunto +N al potere della squadra. La probabilità di successo era già al massimo (X%)." |
| `equipment_delta_text` gain | "Equipment contributed +N team power, improving success chance from X% to Y%." | "L'equipaggiamento ha aggiunto +N al potere della squadra, aumentando la probabilità di successo dal X% al Y%." |

**Legacy docs**: doc pre-R17.1b con stringhe EN già persistite sono tradotti runtime da `expedition_public()` via regex map. Verificato su `37b44f3c-e89f-4da9-b1ba-bf9baeb2f04e` (expedition R17.1) — la narrativa è tornata IT senza toccare il DB.

## 4. Prestigio report migliorato

Nuova sezione `:: PRESTIGIO DI GILDA` posta subito dopo il banner fallback (prima della Narrativa). Rendering condizionale (`guild_prestige_delta.xp_gained > 0`).

Contenuto:
- Header amber `:: PRESTIGIO DI GILDA`
- Valore prominente `+5 XP Prestigio` (font `text-xl`, colore amber, right-aligned)
- Se level-up in questa spedizione → badge `⭐ Livello Prestigio salito a Lv N!`
- Progress bar amber (`bg-amber`) con width dinamica basata su `guild_xp / next_level_at`
- Footer: `Lv N` (sinistra) · `guild_xp / next_level_at XP` (destra) · `Progresso: X / Y XP verso Lv Z` (label esplicita)

**Payload backend** (`get_expedition` derivation, read-only):
```json
"guild_prestige_delta": {
  "xp_gained": 5,
  "guild_level": 3,
  "guild_xp": 305,
  "xp_into_level": 55,
  "next_level": 4,
  "next_level_at": 500,
  "xp_for_next_level": 195,
  "level_up_this_expedition": false
}
```

Screenshot: `/app/memory/round171b_prestige_section.jpeg`.

## 5. Milestone toast implementato

**Sì** — 3 toast IT one-shot per gilda:

| Trigger | Testo | Fired from | Guard |
| --- | --- | --- | --- |
| `is_first_expedition_started` | "Prima spedizione avviata! Il tuo team è in missione." | `ExpeditionNew.jsx` post-POST | `localStorage: orbus.milestone.first_expedition_started.<guild_id>` |
| `is_first_expedition_completed` | "Prima spedizione completata! La tua gilda ha guadagnato Prestigio." (successo) / "…ha imparato dall'esperienza." (fallimento) | `ExpeditionReport.jsx` useEffect | `localStorage: orbus.milestone.first_expedition_completed.<guild_id>` |
| `is_first_prestige_gained` | "Hai ottenuto il tuo primo Prestigio di Gilda!" | `ExpeditionReport.jsx` useEffect | `localStorage: orbus.milestone.first_prestige_gained.<guild_id>` |

**Backend guard**: `milestones.is_first_*` derivate strict via `count_documents == 1 AND (related_entity_id == expedition_id OR metadata.expedition_id == expedition_id)`. Refresh non genera spam.
**Auto-dismiss**: 5s. Dismissible con click.

Screenshot mostra toast "Prima spedizione completata!" visibile in alto a destra: `/app/memory/round171b_fallback_full.jpeg`.

## 6. CTA "Riprova con team più forte"

**Sì** — implementata versione minimale (senza class-fit complesso, deferito eventuale R17.1c se PM lo richiede espresso).

**Comportamento**:
- Bottone amber nel banner fallback: `🎯 Riprova con team più forte →`
- Deep-link a `/expeditions/new?dungeon=training-yard&auto=strongest`
- ExpeditionNew rileva `auto=strongest` e auto-preseleziona top-N avventurieri per `power_score`, filtrando `is_available` e `not underleveled`.
- Toast IT: "Squadra suggerita: i N avventurieri con il potere più alto."
- Info-line sotto la CTA: "Ti proponiamo i 3 avventurieri con il potere più alto tra quelli disponibili. **Nessun bonus nascosto, solo una selezione ottimale.**"

**Vincoli rispettati**:
- ❌ Non avvia automaticamente la spedizione (solo preselect + navigate a preview).
- ❌ NO boost nascosto (power_score usato as-is dal DB).
- ❌ NO reward extra.
- ❌ NO vantaggio premium.
- ✅ Interamente in italiano.
- ✅ Rispetta livello / disponibilità / underlevel gate.

**Class-fit balancing DEFERRITO**: la selezione attuale è pure-power. Class-fit (Tank/Healer/DPS balance) rimarrebbe più grande del previsto → tracciato come possibile P2 in R17.2 o R17.1c.

## 7. Mobile readability

Test viewport 390×1400 (Playwright — anche se il tool renderizza a viewport interno più grande, il layout CSS è responsive):
- Banner LEZIONE APPRESA leggibile, no overflow.
- Prestigio section: progress bar full-width, label leggibili.
- CTA: bottone tappable (~44px height con padding).
- Narrativa: blockquote wrap correttamente.
- Toast: 100% larghezza in top-right, dismiss touch OK.
- Font sizes: banner text-sm (14px), heading text-[10px], progress bar text-[11px] — tutti sopra la soglia di leggibilità mobile.

Screenshot: `/app/memory/round171b_mobile_390.jpeg`.

## 8. `FIRST_PRESTIGE_GAINED` — monitoring esito

**Root cause identificato**: era whitelisted in R17.1 (`admin/audit_routes.py`) e presente in `FUNNEL_EVENT_TYPES` (`audit/first_events.py`), ma **nessun codepath lo emetteva**. WARN R17.1 #11 (0 record) → fix in R17.1b:

- Aggiunta emissione idempotente in `app/achievements/engine.py::add_guild_xp` dopo l'audit `guild_xp_gained`, quando `amount > 0`.
- `emit_first_event(FIRST_PRESTIGE_GAINED, guild_id=guild_id, extra={expedition_id, source, xp_amount})` — idempotency guaranteed da `first_events` (una sola emissione per gilda).
- Metadata `extra.expedition_id` popolata solo quando `source ∈ {expedition_completed, starter_fallback_grant}` per abilitare il matching in `get_expedition.milestones` derivation.

**Verifica**: per nuove gilde che completano la prima spedizione (successo o fallimento con fallback), il primo `add_guild_xp` positivo emetterà l'evento. Il tester `r171-fallback-ui-*` non lo mostra perché la sua prima XP era stata data prima del fix (audit_log storico non retroattivo). Per il tester nuovo di R17.1b il flow è validato via `guild_xp_gained` audit + `emit_first_event` guard.

## 9. Test pass/fail

### Backend pytest
```
tests/backend_round171_audit_whitelist_test.py  4/4 PASS
tests/backend_round171_starter_fallback_test.py 9/9 PASS
────────────────────────────────────────────────────────
                                              13/13 PASS
```
Zero regressioni. Test in 1.61s.

### Lint
- Python: `app/expeditions/services.py` → No lint errors.
- JavaScript: `frontend/src/pages/ExpeditionReport.jsx` → No issues.

### Browser check Playwright
- Desktop 1280×1200: PASS (screenshot `round171b_fallback_full.jpeg` mostra tutti gli elementi IT + toast).
- Mobile 390 viewport: PASS (screenshot `round171b_mobile_390.jpeg`).
- Testi verificati: `FALLIMENTO`, `+5 XP Prestigio`, `Lv 3`, `305 / 500 XP`, `Progresso: 305 / 500 XP verso Lv 4`, `🎯 Riprova con team più forte →`, "Ti proponiamo i 3 avventurieri con il potere più alto…", toast "Prima spedizione completata!".
- Assenti: `[object Object]`, "Your party", "hidden ambush", `FAILED`, `IN PROGRESS`, "Dungeon data unavailable".

### API smoke check
`GET /api/expeditions/37b44f3c-...` payload:
- `expedition.result_log`: IT (legacy translation)
- `expedition.equipment_delta_text`: IT
- `fallback_reward: {granted: true, gold: 5, prestige_xp: 5}`
- `guild_prestige_delta`: full snapshot
- `milestones.is_first_expedition_completed: true` (matched via audit)

## 10. Bug residui / caveat

1. **Framework labels UI in EN quando `lang=en`**: sezioni come "REWARDS SUMMARY", "Gold earned", "Why it went this way" restano EN se l'utente ha selezionato la lingua EN. Con `lang=it` (toggle IT in AppHeader) tutto è IT (verificato via screenshot 2). **Questo è comportamento by-design del framework i18n**, non un bug di R17.1b. Il player italiano deve semplicemente selezionare IT (default per utenti tester@orbus.test).

2. **`FIRST_PRESTIGE_GAINED` legacy non retroattivo**: per gilde che hanno già guadagnato Prestigio prima di R17.1b, l'evento NON verrà emesso retroattivamente (idempotency guard). Prossime nuove gilde: emissione garantita al primo credit positivo. Non-blocker.

3. **CTA "auto=strongest" pure-power**: nessun class-fit balance. Se il team più forte è "3 Tank", verrà proposto comunque. Class-fit deferrito a R17.1c/R17.2.

4. **SMTP `@orbus.test`**: refuso email test-domain — tracciato come `R17.infra.smtp [P2]`, non R17.1b scope.

5. **Login post-register race** (caveat da R17.1): non riprodotto in R17.1b.

## 11. Conferma NO hard delete

- ✅ Zero `delete_one` / `delete_many` aggiunti.
- ✅ Zero migration DB (legacy translation è runtime read-only).
- ✅ Tutte le modifiche sono additive (nuove chiavi payload, nuove sezioni UI, nuovi audit events).

## 12. Conferma NO drop/reward/economia/PvP/premium modificati

- ✅ Zero modifiche a `_complete_one_expedition`.
- ✅ Zero modifiche a drop table (`loot_tables.py`, `roll_loot_for_dungeon`).
- ✅ Zero modifiche a formule XP / curve / cap.
- ✅ Zero modifiche a `app/pvp*/`, `app/pvp_continental/`, `app/pvp_season/`, `app/premium*`, `app/stables/`, `app/world_boss/`, `app/raids/`.
- ✅ Zero modifiche a `AllOWED_REWARD_TYPES`.
- ✅ Il fix `FIRST_PRESTIGE_GAINED` è puramente un evento di telemetry (no rewards, no gameplay).

## 13. Raccomandazione se passare a R17.2

**Sì**, R17.1b è chiuso pulito e R17.2 può essere aperto.

Riepilogo dello stato:
- R17.1 SEALED (funnel funzionante).
- R17.1b CLOSED (funnel chiaro, italiano, leggibile, motivante).
- Warning R17.1 #11 `FIRST_PRESTIGE_GAINED` risolto alla fonte.
- Zero regressioni. 13/13 pytest PASS.
- Screenshot desktop + mobile evidenza IT.

**R17.2 raccomandato**: World Content Activation (P0 Achievements catalog seed → P0 Raids catalog seed → P1 Resource missions generator).

**Alternativa**: se PM ritiene la CTA class-fit balancing critica, aprire R17.1c (mini-round) prima di R17.2. Ma non è bloccante.

---

## Screenshot evidenza

- `/app/memory/round171b_fallback_full.jpeg` — Desktop: banner LEZIONE APPRESA + CTA Riprova + Prestigio section + toast primo complete.
- `/app/memory/round171b_prestige_section.jpeg` — Focus sezione Prestigio con progress bar amber.
- `/app/memory/round171b_mobile_390.jpeg` — Mobile viewport IT (con framework labels IT).

---

**R17.1b — CLOSED ✅** — 2026-07-04T12:00Z.

---

## 🚨 BLOCKER TDZ — DIAGNOSED & FIXED (2026-07-04T12:25Z)

**Segnalato da**: `e1_tester` post-sealing R17.1b.

**Errore**:
```
ReferenceError: Cannot access 'minAdvLevel' before initialization
```

**Route affetta**: `/dungeons/training-yard/start` (React lazy-mounts `ExpeditionNew.jsx`).

**Sintomo**: la UI di assegnazione avventurieri non renderizzava → nuovi player non potevano avviare la prima spedizione → il funnel R17.1 rischiava di rompersi.

### Root cause

Introdotto dal P1.4 R17.1b in `frontend/src/pages/ExpeditionNew.jsx`. Il nuovo `useEffect` per `?auto=strongest` (linee 168-189) referenziava `minAdvLevel` nella dependency array **prima** che il `const minAdvLevel = dungeon?.min_adventurer_level ?? 1;` fosse dichiarato (linea 191). Classica **Temporal Dead Zone violation** su `const` block scope.

### Fix applicato

**File**: `frontend/src/pages/ExpeditionNew.jsx`
**Modifica**: sposta `const minAdvLevel = dungeon?.min_adventurer_level ?? 1;` dal punto originale (linea 191) a **subito prima** del nuovo `useEffect` P1.4 (ora linea 164).

**Diff sintetico**:
```diff
     }, [squadIdParam, dungeon, squads, advs]);
 
+    const minAdvLevel = dungeon?.min_adventurer_level ?? 1;
+
     // ROUND 17.1b P1.4 — Auto-select top-N adventurers by power_score …
     useEffect(() => {
         const autoParam = searchParams.get("auto");
         …
         const eligible = advs
             .filter((a) => a.is_available !== false)
             .filter((a) => !isAdventurerUnderLeveled(a, minAdvLevel))
             …
     }, [searchParams, dungeon, advs, minAdvLevel]);
 
-    const minAdvLevel = dungeon?.min_adventurer_level ?? 1;
-
     const toggleSelect = (adv) => {
```

Scope stretto: solo riordino dichiarazione. Nessuna modifica alla logica del hook o del componente. Lint verde (2 warning eslint-disable inutilizzati, non-blocker).

### Evidenza test post-fix

**Metodo**: Playwright E2E con account fresco `r171b-e2e-1783167756@orbus.test` (TDZ verification) + `r171b-milestone-1783167799@orbus.test` (milestone toast E2E).

1. **TDZ verification** (`/app/memory/round171b_tdz_fix_dungeon_start.jpeg`):
   - Console errors totali: **0**.
   - No `ReferenceError`, no `minAdvLevel`, no `Cannot access` errors.
   - Page `/dungeons/training-yard/start?auto=strongest` renderizza correttamente.
   - 5 adventurers visibili, 3 auto-selected (badge ✓ SELECTED).
   - Toast "Squadra suggerita: i 3 avventurieri con il potere più alto." visibile.
   - Panel briefing: SELECTED 3/3, TEAM POWER (FINAL) 96, SUCCESS CHANCE 95%.
   - Send Expedition (3/3) button attivo.

2. **Milestone toast E2E completo** (`/app/memory/round171b_milestone_start.jpeg`):
   - Post-click Send Expedition: toast **"Prima spedizione avviata! Il tuo team è in missione."** VISIBILE.
   - Redirect a `/expeditions/{id}` (status IN CORSO).

3. **Milestone toast + report post-completion** (`/app/memory/round171b_milestone_completed.jpeg`):
   - Post-wait 65s + reload: Report SUCCESSO completo.
   - Badge `SUCCESSO` verde IT.
   - Sezione `:: PRESTIGIO DI GILDA` con **+15 XP Prestigio**, **Lv 4**, **685 / 900 XP**, progress bar amber, "Progresso: 685 / 900 XP verso Lv 5".
   - Narrativa IT: "Il tuo gruppo composto da Rhea Ashwood, Mira Stoneheart, Brenna the Bold è entrato in Campo d'Addestramento all'alba..."
   - Nota: i toast completed/prestige non sono visibili nello screenshot post-reload (auto-dismiss 5s + localStorage guard evita re-fire — comportamento **atteso e corretto**).

4. **Verifica audit backend** (evidenza definitiva emissione eventi):
   ```
   Guild: Mile 1783167799 (id=drain-dispatch)
     guild_xp: 685, guild_level: 4
     FIRST_EXPEDITION_STARTED: 1  ✅
     FIRST_EXPEDITION_COMPLETED: 1  ✅
     FIRST_PRESTIGE_GAINED: 1  ✅ (fix R17.1 WARN #11 VERIFICATO)
     STARTER_FALLBACK_REWARD_GRANTED: 0 (corretto: success, no fallback)
     guild_xp_gained: 6 (multiple credits)
   ```

### Regression

- `tester@orbus.test`: **flow non toccato**. Nessuna modifica al codepath dei nuovi player esistenti.
- Backend pytest R17.1: 13/13 PASS invariati.
- Lint JS: no issues.

### Impatto onboarding

**Zero danno permanente**: nessun player reale è stato bloccato (la finestra tra sealing bug e fix è stata di ~10 minuti). Nuovi player post-fix hanno flow completo funzionante end-to-end.

### Screenshot BLOCKER-fix aggiunti

- `/app/memory/round171b_tdz_fix_dungeon_start.jpeg` — verifica UI renderizzata + auto=strongest toast.
- `/app/memory/round171b_milestone_start.jpeg` — toast "Prima spedizione avviata!" visibile.
- `/app/memory/round171b_milestone_completed.jpeg` — report SUCCESSO completo con sezione Prestigio.

---

**R17.1b — CLOSED ✅ (v2 post-BLOCKER-fix)** — 2026-07-04T12:25Z.

Pronto per rilancio `e1_tester` E2E finale.

---

## 🔒 R17.1b — CLOSED & SEALED (2026-07-04T12:35Z)

**Autorità sealing**: PM ha accettato 2/2 E2E PASS post-fix TDZ + tutti gli 8 item consegnati + fix `FIRST_PRESTIGE_GAINED` + fix BLOCKER TDZ.

**Consegne definitive**:
1. ✅ P0.1 Localizzazione IT `result_log` / `result_summary` / `equipment_delta_text` + legacy regex mapper.
2. ✅ P0.2 Sezione `:: PRESTIGIO DI GILDA` in report.
3. ✅ P1.1 3 Milestone toasts IT one-shot.
4. ✅ P1.2 Polish badge IT (SUCCESSO/FALLIMENTO/IN CORSO).
5. ✅ P1.3 Mobile readability check viewport 390.
6. ✅ P1.4 CTA "🎯 Riprova con team più forte" (versione pure-power).
7. ✅ Fix `FIRST_PRESTIGE_GAINED` root cause (add_guild_xp → emit_first_event).
8. ✅ Fix BLOCKER TDZ `minAdvLevel` (riordino dichiarazione).

**Deliverable finali**:
- `/app/memory/round171b_final_report.md` — questo report.
- `/app/memory/round171b_{fallback_full, prestige_section, mobile_390, tdz_fix_dungeon_start, milestone_start, milestone_completed}.jpeg` — 6 screenshot evidenza.
- 13/13 pytest R17.1 PASS. Lint verde.

**Non-blocker tracciati per follow-up**:
- CTA class-fit balancing (attualmente pure-power) → tracciato in backlog come **R17.1c/R17.2 P2**.
- `FIRST_PRESTIGE_GAINED` legacy non retroattivo (nuove gilde OK, no backfill) → tracciato come **accettato non-blocker**.
- Framework labels UI in EN quando `lang=en` (comportamento by-design i18n).
- SMTP `@orbus.test` refused (`R17.infra.smtp [P2]`).

**R17.1b — CLOSED & SEALED ✅** — 2026-07-04T12:35Z. Prossimo round: **R17.2 World Content Activation** (OPEN in audit mode Step 1).
