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

2. **Client-side guard mancante su `/admin/tester-tools`** — ✅ MITIGATO in R16.5.2 hotfix visibility
   - Fix applicato: guard di **visibilità** inline nel menu (dropdown desktop + drawer mobile) —
     `user?.is_admin && user.email?.endsWith("@orbus.test")` — impedisce che un non-tester
     scopra l'esistenza della rotta tramite il menu.
   - Resta aperto (P3): guard **hard** client-side lato pagina (redirect / "Accesso negato")
     per il caso in cui un admin non-`@orbus.test` digiti manualmente l'URL. Backend blocca
     comunque 403, quindi UX-only.
   - Vedi `/app/memory/round1652_visibility_fix_report.md`.

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

## Round 16.5.4 — Guild XP V2 Extended Hooks (PLANNED)

Scope: estendere il Prestigio di Gilda con le 7 fonti mancanti non implementate nella V1 (R16.5.3 STEP 2.B bare-minimum).

Hook rimanenti da attivare:

1. **continental_event_participation** (+25, cap 1/settimana/evento) — richiede tracker settimanale distinto (differente dalla granularità giornaliera dei drip R16.5.3)
2. **daily_contract_claimed** (+20, cap 3/giorno) — solo se sistema daily contract già esiste (`app/contracts/` presente, verificare che il flow di claim sia raggiungibile)
3. **weekly_contract_claimed** (+150, cap 1/settimana) — tracker settimanale
4. **structure_upgraded** (+30, cap 3/giorno, one-time per struttura) — hook in `app/territory/*` sulla structure upgrade action; usare `structure_id` come `source_id` per idempotenza permanente (non solo giornaliera)
5. **guild_specialization_chosen** (+200, one-shot per lifetime) — hook in `app/guild_specialization/*` sulla scelta iniziale
6. **trade_pact_signed** (+50, cap 2/giorno) — hook in `app/trade_pacts/*` (verificare esistenza del sistema)
7. **pvp_battle_completed** (+15, cap 3/giorno) — hook post battle chiuso (win/loss entrambi); usare `battle_id` come `source_id`

**Prerequisiti**: audit rapido di esistenza dei moduli `contracts/`, `trade_pacts/`, `guild_specialization/`, `territory/structure_upgrade`, `pvp_continental/battle_resolver`. Se qualcuno di questi non ha ancora un endpoint di completion stabile, deferire il singolo hook al round successivo.

**Priorità**: P2 (miglioramento, non blocker).

**Vincoli**:
- No monetizzazione
- No backfill retroattivo
- Cap giornaliero/settimanale rigoroso (nuovo tracker `guild_xp_weekly_cap_tracker` per gli hook 1/3)
- Audit `GUILD_XP_GAINED` con `source` distinto per ogni hook (metriche future)
- Nessuna modifica alle formule drip R16.5.3 (expedition/raid/resource) — solo additivo

**Note tecniche riprese da R16.5.3**:
- Il pattern `sweep_activities_for_guild` in `app/core/activity_sweep.py` è estendibile: se in R16.5.4 emergono altre attività lazy, aggiungere il resolver best-effort lì.
- Il modulo `app/achievements/xp_hooks.py` centralizza già `_credit_xp` con cap + idempotency: i 7 nuovi hook sono thin wrapper che chiamano `_credit_xp` con nuove chiavi cap. Nessun refactor infra richiesto.

---

## Round 16.5.4c — Seed Integrity & Class Equipment Coverage (PLANNED)

**Priority**: P1 (chiude i buchi rilevati durante audit R16.5.4b).

**Origine**: audit STEP 1 R16.5.4b (`/app/memory/round1654b_audit_report.md`).

### Items

1. **ADJ-9 — Backfill `class_slug` sugli avventurieri legacy** ⭐ (nuovo, scoperto in R16.5.4b REOPEN)
   - Sintomo empirico: `db.adventurers.count_documents({class_slug: {$exists: true, $ne: null}})` restituisce ~6% dei documenti; il restante **~94% non ha `class_slug`** popolato (solo `class_name` o `class`).
   - Impatto: il loader class-aware `_load_class_meta(db, _resolve_class_slug(adv))` in `auto_equip.py` avrebbe restituito `{}` per la maggior parte degli avventurieri, degradando la fitness al solo `power_score` — è il sintomo che i tester live hanno riportato.
   - Mitigazione già presente (runtime): `_resolve_class_slug()` (righe 145-150 di `auto_equip.py`) fa fallback `class_slug → class_name → class`, tutti lowercased. Il 100% degli avventurieri esistenti ora ha primary_stat corretta.
   - Fix data-integrity proposto: script `round1654c_backfill_class_slug.py` dry-run+apply, lookup `class_name → class_slug` via catalogo `adventurer_classes`, update idempotente `update_many({class_slug: null}, {$set: {class_slug: <resolved>}})`.
   - Modifica anche `POST /api/adventurers/recruit` per popolare sempre `class_slug` in write path (root cause: le recruit routes storiche popolavano solo `class_name`).
   - Test: `100% adventurers hanno class_slug post-backfill` + regressione su `_resolve_class_slug` per garantire il fallback resti.

2. **ADJ-1 — Rarity case-mismatch normalization**
   - Sintomo: `db.items` contiene `rare/epic/legendary` (lowercase) accanto a `Rare/Epic/Legendary` (~11+ docs). Le tabelle di gate (rarity→level) sono case-sensitive.
   - Fix proposto: script idempotente `round1654c_rarity_case_normalize.py` con dry-run/apply + snapshot che uppercase-a il primo carattere (whitelist `rare|epic|legendary` → `Rare|Epic|Legendary`).
   - Vincolo: solo campo `rarity`, whitelist esplicita.

3. **ADJ-3 — Warlock + Alchemist + Druid item coverage** ⭐ (promosso a P1 IMPORTANTE 2026-07-02 dopo REOPEN #2 Q2-b(iii))
   - Sintomo: `warlock`, `alchemist` (post-R16.0) e `druid` (parzialmente) non hanno abbastanza item con `recommended_classes` compatibile.
   - Impatto REOPEN #2: con la nuova regola "Auto-Equip scarta warning" (approvata dal PM 2026-07-02), l'empty state per queste classi diventa molto più visibile. Un Druid Lv11 con inventario Legendary ma senza item druid-fit vedrà "Nessuna arma adatta a Druido Lv11 trovata in inventario" invece di ricevere Frostfang Claymore.
   - Fix proposto: seed pack minimale (weapon + armor + accessory per ciascuna classe, rarità Common/Uncommon/Rare/Epic, cinque livelli target); verificare che le drop table delle spedizioni includano item class-fit per ogni classe attiva post-R16.0. Design + balance separato per NON alterare drop rate esistenti.
   - Nessun P2W, nessun combat balance shift, nessun cambio primary_stat.

4. **ADJ-3.c [P2] NEW — Warning "equip fallito (HTTPException)" leaka nel payload** (scoperto in `e1_tester` Test 2 Mage 2026-07-02)
   - Sintomo: nel test Mage senza accessory class-fit, il payload `warnings_it` conteneva stringa "accessory: equip fallito (HTTPException)" invece di reason italiana pulita.
   - Root cause probabile: except generico in `auto_equip.py` che cattura `HTTPException` sollevato da `equip_item_service` e la stringifica senza estrarre il `detail`.
   - Fix: gestire il caso "nessun accessorio adatto" con reason italiana pulita (probabilmente non dovrebbe nemmeno raggiungere quel branch se il filtro warning-skip è già applicato — verifica se è un branch dormiente).
   - Test dedicato: mage senza accessory class-fit → nessun "HTTPException" stringato nel payload, solo reason IT.
   - Nessun impatto funzionale (l'auto-equip funziona correttamente), solo UX/log cleanup.

4. **ADJ-6 — write_audit senza `related_entity_id=adv.id`** — ✅ MITIGATO in R16.5.4b (aggiunto in `auto_equip.py`).
   - Chiudibile: audit `adventurer_auto_equipped` ora popola `related_entity_id`. Verificare che altri handler nel modulo `equipment/` seguano la stessa convenzione (`equip_item_service`, `unequip_item_service`).

5. **ADJ-7 — 423 level_gate mangiato da `except Exception` in auto-equip**
   - Sintomo: quando il gate `enforce_item_level_requirement` in `equip_item_service` restituisce 423, il wrapper `try/except` in `auto_equip.py:213-215` lo cattura come warning generico "equip fallito ({name})".
   - Fix proposto: fare bubble-up del `HTTPException.detail` come `warnings[i] = {code, user_message}` strutturato invece di string generica.
   - Rischio basso: R16.5.4b ha già introdotto il filtro pre-scoring `resolve_item_required_level`, quindi il 423 non dovrebbe più scattare in condizioni normali. Fix rimane per robustness contro race condition (item mod live durante auto-equip).

6. **Orfani già equipaggiati (segnalazione)**
   - Prima del backfill R16.5.4b, un utente lv1 poteva aver equipaggiato uno dei 6 Legendary a `required_adventurer_level:1`. Post-backfill quei riferimenti restano validi (nessun forced unequip).
   - Decisione utente: NON forzare l'unequip retroattivo (rispettato in questo round).
   - Se serve tracciarli: query `equipped_items` join `items` per rarità legendary + `adv.level < req_level`. Report separato, no fix automatico.

**Vincoli**:
- No drop rate / balance modificati
- No P2W
- No hard delete
- Dry-run + apply obbligatorio per ogni seed patch
- Snapshot rollback per ogni script

**Note tecniche**:
- Il pattern `round1654b_seed_integrity.py` (whitelist + snapshot + audit event) è il template per ADJ-1 e per il seed pack ADJ-3.

---

## Round 16.5.4c — COMPLETATO ✅ (2026-07-02, in attesa consolidamento PM)

Vedi `/app/memory/round1654c_final_report.md`. Sintesi:
- ADJ-9 backfill class_slug: **1909/1915 avventurieri backfillati** (99.71% coverage), 6 orfani Guardian/Cleric documentati.
- ADJ-3 seed pack Warlock/Alchemist/Druid: **22 nuovi item** approvati opzione A dal PM, Epic Lv8, no Legendary.
- ADJ-1 rarity normalize: **17 item** normalizzati a Capitalized + canonicalizer helper.
- ADJ-3.c (P2 accessory): **no più "HTTPException" leak** nei warning player-facing.
- ADJ-6 già a posto pre-R16.5.4c; ADJ-7 risolto insieme a P2.
- Test 54/54 PASS. Regression curl live invariata.

---

## Round 16.5.4d — Cleanup residuo & polish (PLANNED, P3)

Item residui non chiusi in R16.5.4c, tutti a bassa priorità.

**Status R16.5.4c (2026-07-03)**: **CLOSED & SEALED ✅** — TC1/TC2/TC3/TC4 accettati dal PM (TC3 accettato per simmetria con TC2). 64/64 pytest verde. Chiusi definitivamente:
- ✅ ADJ-9 (backfill class_slug + fix recruit path)
- ✅ ADJ-3 (22 nuovi item Warlock/Alchemist/Druid)
- ✅ ADJ-1 (rarity normalize + canonicalizer)
- ✅ P2 ADJ-3.c (no più leak `HTTPException`)
- ✅ ADJ-6 (audit `related_entity_id` verificato)
- ✅ ADJ-7 (423 level_gate bubble-up pulito)
- ✅ i18n Auto-Equip completa (backend `reason_it` + FE hardcoded IT modal REOPEN #5)
- ✅ Off-class silent-skip (regola PM Q2-b(iii))
- ✅ Class labels IT (mappa canonica 14 classi)
- ✅ Nuovo audit event `TEST_ADVENTURER_EQUIP_RESET` + reset TC1 Warlock
- ✅ E2E browser Warlock/Alchemist — verificato in R16.5.4c REOPEN #4-5, chiuso.

### P3 items (aperti / da tracciare)

1. **Orfani Guardian / Cleric** (P3, R16.5.4d o oltre)
   - 6 avventurieri legacy con `class_name ∈ {"Guardian", "Cleric"}`, classi non presenti in `adventurer_classes`.
   - Post R16.5.4c ADJ-9 sono l'unico residuo con `class_slug=null`.
   - Decisione di design pendente:
     - (a) mappare Guardian → paladin e Cleric → priest (aliasing);
     - (b) retire tramite endpoint standard (soft delete → collezione retired);
     - (c) aggiungere Guardian/Cleric al catalog come classi vere.
   - Impatto UX minimo (6 doc su 2037).

2. **P3 NEW — Auto-Equip report polish: interpolare la classe IT nel branch already-best** (tracciato 2026-07-03 dopo sealing R16.5.4c)
   - **Non bloccante, cosmetico.** Origine: PM ha rilevato che il criterio TC3 "Report contiene 'Guerriero'" era asimmetrico rispetto a TC2 (che non lo richiedeva).
   - **Current copy IT**: `"Arma: l'oggetto attualmente equipaggiato è già il migliore."` (identico per tutte le classi).
   - **Proposal**: `"Arma: l'oggetto attualmente equipaggiato è già il migliore per Guerriero."` — simmetrico anche per Mago/Alchimista/Occultista/Druido/Paladino/Berserker/Monaco/Bardo/Assassino/Negromante/Sacerdote/Ranger/Ladro.
   - Scope: solo `unchanged_slots_detail[].reason_it` in `equipment/auto_equip.py` branch `already-best`. Nessuna modifica al branch `reasons[]` (già include la classe nella copy corrente "migliore per {classe}").
   - Test da aggiornare: `test_30_already_the_best_it_all_three_slots`, `test_52_already_best_branch_exact_it_no_en_leak`, `test_53_no_swap_possible_branch_exact_it_no_en_leak` — allentare match esatto a `startswith(...) and endswith(" per {classe}.")` oppure aggiornare stringhe attese.
   - Priorità: P3 (UX polish, no impatto funzionale).

3. **UX polish Auto-Equip** (rimasto da R16.5.4b R16.5.5+):
   - Label più chiare "Slot Equipaggiati" vs "Zaino/Inventario".
   - Messaggio empty state più caloroso.



Raccolti durante REOPEN R16.5.4b (verifica browser `e1_tester`):
- **UI Auto-Equip label**: differenziare visivamente "Slot Equipaggiati" vs "Zaino/Inventario" (attualmente ambigui).
- **Messaggio empty state "già ottimale"**: `"Nessun item migliore disponibile"` → più caloroso, es. `"Equipaggiamento già ottimale ✨"` o `"L'oggetto attuale è la scelta migliore per questa classe."`

Nessun impatto funzionale, solo copy + microinterazioni.

---

## Round 16.5.4e — Territory KeyError Audit (PLANNED, P3)

**Origine**: crash `KeyError: 'library'` rilevato nei log backend durante audit R16.5.4d
(`territory/services.py:53` → `_public_doc` → `structures.py:174` → `STRUCTURE_CATALOG[slug]`).

**Scope**:
- Investigare `app/territory/services.py:53` e `app/territory/structures.py:174`.
- Root cause di `KeyError: 'library'`: gilde con documento territory che
  referenzia una struttura `library` non presente in `STRUCTURE_CATALOG`
  (probabile legacy schema pre-refactor).
- Decidere strategia: (a) fallback graceful in `get_structure_max_level`
  con `allow_legacy=True` per slug sconosciuti, (b) migration idempotente
  che rimuove/rinomina la struct `library` dai document `territory`,
  oppure (c) aggiungere `library` al catalog come struttura vera.

**Vincoli**:
- No hard delete di document territory (usare migration idempotente con snapshot).
- No modifiche a Auto-Equip, drop/reward, PvP, economia, premium.
- Round DEDICATO — non mischiare con altri fix.

**Priorità**: P3 (crasha solo `GET /api/territory/my` per gilde affette; non blocca gameplay core).
