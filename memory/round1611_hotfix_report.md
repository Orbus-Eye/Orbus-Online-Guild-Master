# Round 16.1.1 HOTFIX — Raid Recovery + Forgia Mobile + Desktop Menu

**Data**: 30 giugno 2026
**Data chiusura ufficiale**: 30 giugno 2026 (post-verifica DevTools iPhone 14 + `e1_tester` 6/6 sub-check PASS)
**Tipo**: Hotfix dedicato (NON è R16.B, NON è R16.C).
**Stato**: 🟢 **OFFICIALLY CLOSED ✅** — 28/28 raid resolved (580 adv liberati, 29 audit `raid_recovered`), Forge mobile PASS (verifica utente DevTools iPhone 14), Desktop menu 6/6 sub-check PASS (fix v4 click-only pattern), 65/65 pytest pass, 0 regressioni.

---

## Sezione 1 — Numero raid bloccati trovati (dry-run)

**29 raid stuck** (status=`in_progress`, `ends_at` <= now).

| Metric | Valore |
|---|---|
| Stuck count | **29** |
| Distinct guilds | **29** (una per gilda) |
| Distinct adventurers blocked | **580** (29 × 20) |
| Raid dungeon | tutti `broken-bastion-siege` (raid endgame tier-2+) |
| Oldest stuck | `56a829ee…` — `ends_at=2026-06-26T20:58Z` (≈4 giorni fa) |
| Most recent stuck | `40d1c6d8…` — `ends_at=2026-06-27T17:48Z` |
| Raid score = 0 + in_progress | **29** (anomalia confermata) |
| Dup risk (`raid_completed`/`raid_recovered` già in audit_log per quei raid_id) | **0** (clean) |

Outcome distribution proposta dal dry-run (deterministic per raid_id):
- `wipe`: ~19
- `partial`: ~10
- `victory`: 0

---

## Sezione 2 — Causa probabile root del raid stuck

**Root cause**: l'endpoint `POST /api/raids/{raid_id}/complete` è **strettamente manuale + time-gated**. Nessuno scheduler/cron/background task lo richiama automaticamente quando `ends_at` viene superato.

Logica esistente (`backend/app/raids/__init__.py:449`):
- Frontend deve **esplicitamente** chiamare `/complete` dopo che il timer scade.
- Se il giocatore non visita la pagina, chiude il browser, o l'app frontend non gestisce il return-from-timer, il raid resta `in_progress` indefinitamente.
- I 29 raid stuck NON hanno mai ricevuto la `POST /complete` → restano congelati con score=0, squadra (20 adv) bloccata.
- Tutti del medesimo raid_dungeon `broken-bastion-siege` → probabile bug nella UI di quel raid specifico O timing race su client.

**Chi avrebbe dovuto risolverli**: il client frontend tramite `POST /api/raids/{id}/complete`. Non c'è fallback server-side esistente.

**Perché non l'ha fatto**: ipotesi non confermata (1) chiusura tab durante il timer, (2) refresh che resetta lo state in-flight, (3) hot-reload preview che droppa la callback. Nessuno scheduler globale a coprire questo caso.

---

## Sezione 3 — File backend modificati

| File | Stato | Diff |
|---|---|---|
| `backend/app/raids/recovery.py` | **NEW** | Nuovo modulo con `resolve_stuck_raid(db, raid_id, *, dry_run, reason)` + helper `auto_resolve_stuck_raids_for_guild` per on-visit fallback. |
| `backend/app/raids/__init__.py` | modified | Aggiunto on-visit fallback in `list_raids` (linea ~673) e `get_raid` (linea ~684) — best-effort, never raises. |
| `backend/app/audit/log.py` | modified | Aggiunto `raid_recovered` ad `EVENT_TYPES` (linea 86). |
| `backend/app/scripts/recover_stuck_raids.py` | **NEW** | Script CLI argparse `--dry-run` (default) / `--apply` / `--raid-id`. |
| `backend/tests/backend_round1611_raid_recovery_test.py` | **NEW** | 7 test pytest. |

---

## Sezione 4 — Script recovery creato

**Path**: `/app/backend/app/scripts/recover_stuck_raids.py`

**Esempi invocazione**:
```bash
# Dry-run (default — read-only)
cd /app/backend && set -a && source .env && set +a && \
  python -m app.scripts.recover_stuck_raids --dry-run

# Apply (ATTUALE: in attesa conferma utente)
cd /app/backend && set -a && source .env && set +a && \
  python -m app.scripts.recover_stuck_raids --apply

# Singolo raid
cd /app/backend && set -a && source .env && set +a && \
  python -m app.scripts.recover_stuck_raids --apply --raid-id 56a829ee-...
```

Output tabellare: `raid_id | guild_id | members | outcome | dup_risk | action`.

---

## Sezione 5 — Output dry-run recovery

```
=== Raid Recovery [DRY-RUN] — 29 candidate(s) ===
raid_id    guild_id    members outcome    dup_risk   action
--------------------------------------------------------------------------------
56a829ee.. b8f1c4eb..       20 wipe       no         previewed
a7c6640c.. 99b861e2..       20 wipe       no         previewed
0d937929.. 11346be4..       20 partial    no         previewed
21875d23.. af162cdf..       20 partial    no         previewed
6e89935b.. b4be264c..       20 wipe       no         previewed
5f48f480.. 45c8a6df..       20 wipe       no         previewed
6c6c33e4.. e7d57ce4..       20 wipe       no         previewed
457aec87.. 29e03e58..       20 partial    no         previewed
d1e65210.. 31ad701c..       20 wipe       no         previewed
deaf2a3f.. 9beb76cf..       20 wipe       no         previewed
6611ceab.. ea155cda..       20 wipe       no         previewed
9820cb93.. bfc7e528..       20 wipe       no         previewed
24b525cf.. 38c429db..       20 wipe       no         previewed
290e98e6.. 27d90995..       20 wipe       no         previewed
3bbd9991.. d3c1b81e..       20 partial    no         previewed
4856042a.. ed222c0d..       20 partial    no         previewed
9f9a4593.. 78f4b72f..       20 wipe       no         previewed
b7c27879.. 93b6eced..       20 partial    no         previewed
62308c79.. adc91cad..       20 wipe       no         previewed
99a3fcb9.. 44c87187..       20 wipe       no         previewed
9e4e7d15.. f8630be6..       20 wipe       no         previewed
bcde756d.. 956129af..       20 wipe       no         previewed
2478c389.. fab5789b..       20 partial    no         previewed
d07eaec7.. bfcb7688..       20 wipe       no         previewed
eac74bf2.. 6eec9a18..       20 wipe       no         previewed
1353250e.. c7ea9228..       20 partial    no         previewed
fc0e3c83.. 6a1eb668..       20 partial    no         previewed
d45d2189.. e8e87e3d..       20 wipe       no         previewed
40d1c6d8.. 0788722b..       20 wipe       no         previewed
--------------------------------------------------------------------------------
Totals: {'resolved': 0, 'skipped': 0, 'previewed': 29, 'error': 0}

(DRY-RUN — nothing was written. Re-run with --apply to commit.)
```

**Note**: il raid `40d1c6d8…` appartenente alla gilda "The Iron Lantern" del tester era stuck — è stato risolto automaticamente dall'**on-visit fallback** durante test in corso (visibile da `db.raids.find_one` post-test: `status=completed`, `recovered=True`). Quindi 28/29 attendono ora `--apply`.

---

## Sezione 6 — Output apply recovery

✅ **APPLIED 2026-06-30 19:35 UTC**.

```
=== Raid Recovery [APPLY] — 28 candidate(s) ===
raid_id    guild_id    members outcome    dup_risk   action
--------------------------------------------------------------------------------
56a829ee.. b8f1c4eb..       20 wipe       no         resolved
a7c6640c.. 99b861e2..       20 wipe       no         resolved
0d937929.. 11346be4..       20 partial    no         resolved
21875d23.. af162cdf..       20 partial    no         resolved
6e89935b.. b4be264c..       20 wipe       no         resolved
5f48f480.. 45c8a6df..       20 wipe       no         resolved
6c6c33e4.. e7d57ce4..       20 wipe       no         resolved
457aec87.. 29e03e58..       20 partial    no         resolved
d1e65210.. 31ad701c..       20 wipe       no         resolved
deaf2a3f.. 9beb76cf..       20 wipe       no         resolved
6611ceab.. ea155cda..       20 wipe       no         resolved
9820cb93.. bfc7e528..       20 wipe       no         resolved
24b525cf.. 38c429db..       20 wipe       no         resolved
290e98e6.. 27d90995..       20 wipe       no         resolved
3bbd9991.. d3c1b81e..       20 partial    no         resolved
4856042a.. ed222c0d..       20 partial    no         resolved
9f9a4593.. 78f4b72f..       20 wipe       no         resolved
b7c27879.. 93b6eced..       20 partial    no         resolved
62308c79.. adc91cad..       20 wipe       no         resolved
99a3fcb9.. 44c87187..       20 wipe       no         resolved
9e4e7d15.. f8630be6..       20 wipe       no         resolved
bcde756d.. 956129af..       20 wipe       no         resolved
2478c389.. fab5789b..       20 partial    no         resolved
d07eaec7.. bfcb7688..       20 wipe       no         resolved
eac74bf2.. 6eec9a18..       20 wipe       no         resolved
1353250e.. c7ea9228..       20 partial    no         resolved
fc0e3c83.. 6a1eb668..       20 partial    no         resolved
d45d2189.. e8e87e3d..       20 wipe       no         resolved
--------------------------------------------------------------------------------
Totals: {'resolved': 28, 'skipped': 0, 'previewed': 0, 'error': 0}
```

**28 resolved / 0 skipped / 0 error / 0 duplicate reward** (tutti `dup_risk=no`).

### Post-apply DB smoke check

```
[1] STUCK raids (in_progress + ends_at<=now): 0  ✅ (expected 0)
[2] advs from recovered raids still flagged blocked: 0  ✅ (expected 0)
[3] audit_log event_type=raid_recovered: 29  ✅ (28 apply + 1 on-visit pre-apply)
[4] raids with recovered=True: 29  ✅
```

### Regression pytest (R16.A + R16.1 + R16.1.1 + Phase 14.4 + dev-seed)

```
================== 65 passed, 1 skipped, 2 warnings in 9.42s ===================
```

**65 passed, 0 fail, 0 regressioni**.

### Frontend lint + webpack

```
ESLint Forge.jsx:      ✅ No issues found
ESLint AppHeader.jsx:  ✅ No issues found
webpack:               ✅ Compiled successfully!
```

---

## Sezione 7 — Conferma squadra/e rilasciate

✅ **APPLIED — 580 avventurieri liberati** (29 raid × 20 membri = 580).

Smoke check post-apply:
```
[2] advs from recovered raids still flagged blocked: 0  (expected 0)
```

Tutti gli avventurieri che erano in `expedition_in_progress=true` o `is_available=false` per i raid recovered ora sono `is_available=true, expedition_in_progress=false`.

Test T02 (`test_stuck_raid_releases_squad_members`) verifica:
```python
assert out["members_released"] == 6  # 6 adv inseriti via _seed_raid
# DB check post-recovery:
still_blocked = await db.adventurers.count_documents({
    "id": {"$in": adv_ids},
    "$or": [{"is_available": False}, {"expedition_in_progress": True}],
})
assert still_blocked == 0
```
**Verde**: 0 avventurieri restano bloccati dopo recovery.

Quando `--apply` verrà lanciato sui 28 raid stuck rimanenti: ~560 avventurieri liberati.

---

## Sezione 8 — Conferma nessuna reward duplicata

Test T03 (`test_resolve_does_not_duplicate_rewards_on_retry`) verifica:
```python
gold_before = guild["gold"]
out1 = await resolve_stuck_raid(...)   # 1st call → resolved
gold_after_first = (await db.guilds.find_one(...))["gold"]
out2 = await resolve_stuck_raid(...)   # 2nd call → skipped
gold_after_second = (await db.guilds.find_one(...))["gold"]
assert gold_after_second == gold_after_first   # NO double-spend
```
**Verde**: il 2° call ritorna `action=skipped, reason=already_<status>` (CAS lock fallisce su `status=in_progress`) → reward NON duplicate.

Test T04 (`test_resolve_does_not_duplicate_audit_event`) verifica:
```python
count = await db.audit_log.count_documents({
    "related_entity_id": raid_id, "event_type": "raid_recovered",
})
assert count == 1  # exactly one row even after retry
```
**Verde**.

---

## Sezione 9 — Test backend raid eseguiti

```
$ cd /app/backend && python -m pytest tests/backend_round1611_raid_recovery_test.py -v
============================================================
tests/backend_round1611_raid_recovery_test.py::test_raid_in_progress_with_past_ends_at_gets_resolved PASSED
tests/backend_round1611_raid_recovery_test.py::test_stuck_raid_releases_squad_members PASSED
tests/backend_round1611_raid_recovery_test.py::test_resolve_does_not_duplicate_rewards_on_retry PASSED
tests/backend_round1611_raid_recovery_test.py::test_resolve_does_not_duplicate_audit_event PASSED
tests/backend_round1611_raid_recovery_test.py::test_raid_still_running_is_not_touched PASSED
tests/backend_round1611_raid_recovery_test.py::test_score_zero_anomaly_resolved_with_recovered_metadata PASSED
tests/backend_round1611_raid_recovery_test.py::test_on_visit_fallback_auto_resolves_expired_raid PASSED
========================= 7 passed, 1 warning in 1.59s =========================
```

**7/7 PASS**.

**Regression check pre-esistente**: ho lanciato anche tests/backend_phase18_1_raids_lifecycle, phase19_2_raid_review_smoke, phase93_email, R16.A, R16.1.

Risultato: **12 fail pre-esistenti** confermati via `git stash` + re-run pre-fix (gli stessi fail già esistevano su HEAD prima del mio hotfix). Le failures sono drift di gating territory (`feature.locked: war_room L2`) e drift openapi paths count — NON regressioni del mio hotfix.

Test miei dell'hotfix R16.1.1: **7/7 verdi** · R16.A P1+P2+P3: **29/29 PASS + 1 skipped** (no regressione).

---

## Sezione 10 — File frontend modificati per Forgia mobile

| File | Modifica |
|---|---|
| `frontend/src/pages/Forge.jsx` | Riscritto con: `pb-32 md:pb-6` su `<main>` (lascia 128px clear sotto la bottom nav), `min-h-[44px]` su tutti i tap target, `w-full md:w-auto` sul confirm button, `scroll-mt-20` sull'operation panel, `useRef + scrollIntoView` per auto-scroll mobile quando si seleziona un item, lista riducibile a `max-h-[40vh]` su mobile per lasciare spazio al pannello azione. |

---

## Sezione 11 — Conferma `Confirm Refine` visibile da mobile

**Confirm Refine**: `Forge.jsx:206-213` — bottone `data-testid="forge-confirm-refine"`, `w-full md:w-auto`, `min-h-[44px]`, `px-4 py-2.5`, `border-amber font-bold` (alta prominenza). Padding bottom main `pb-32` su mobile → 128px di spazio sotto, ben oltre la bottom nav (~64px h).

**Comportamento mobile** (single column, viewport <768px):
1. User vede la lista item (`max-h-[40vh]`).
2. Clicca item → `setSelected(item)`.
3. `useEffect([selected])` triggera `scrollIntoView({behavior: "smooth", block: "start"})` sul `operationPanelRef`.
4. Il pannello azione scrolla in vista, il confirm button è chiaramente visibile sopra il padding 128px.

**Tap target**: tutti i bottoni hanno `min-h-[44px]` (Apple HIG ✓).

---

## Sezione 12 — Conferma smonta/riassegna/incanta visibili da mobile

Tutti e 4 i tab usano lo **stesso bottone unico** `forge-confirm-${tab}` (linea 206):
- `forge-confirm-refine` (Conferma Raffinazione)
- `forge-confirm-enchant` (Conferma Incanta — apre options panel)
- `forge-confirm-reroll` (Conferma Riassegna)
- `forge-confirm-disenchant` (Conferma Smonta)

Tutti beneficiano del medesimo fix mobile (pb-32, min-h-44, scroll-into-view, w-full). Inoltre i bottoni delle enchant options (`forge-enchant-option-${slug}`) sono stati ingranditi a `min-h-[44px] py-2`.

**Reassign**: nella Forgia il "reassign" è chiamato "reroll" (riassegna affissi). Tab `reroll` → confirm visibile.

---

## Sezione 13 — File frontend modificati per desktop menu

| File | Modifica |
|---|---|
| `frontend/src/components/AppHeader.jsx` | Refactor: lifted `openId` state al parent `AppHeader`, passato come prop a `DesktopMenuButton` + `DesktopAccountMenu`. Solo 1 dropdown aperto alla volta. Click-based open (con auto-switch hover se un dropdown è già aperto, per UX fluida). `useEffect` click-outside listener (`mousedown` + `touchstart`) chiude il dropdown aperto. Z-index bumped da 30 a 50. Auto-close al click su una voce + auto-close al cambio route. |

---

## Sezione 14 — Conferma dropdown desktop non accavallati

**Comportamento ora** (post v3 hotfix — `click` listener post-bubble):

1. User clicca sezione A → A si apre.
2. **User clicca sezione B → A si chiude, B si apre nello stesso click** ✅ (atomic switch ripristinato in v3).
3. User hover sezione C (mentre B è aperto) → B si chiude, C si apre (auto-switch hover gating).
4. **User clicca su body (centro dashboard) / header whitespace / qualsiasi area fuori da trigger e panel → dropdown si chiude** ✅ (sub-check a + b risolti in v3).
5. User clicca su elemento UI fuori header → dropdown si chiude ✅ (c).
6. User clicca su panel space vuoto (dentro `<ul>`) → resta aperto ✅ (e).
7. User clicca link → navigation + chiusura via route effect (Link onClick fa setOpenId(null) prima, poi navigation).
8. Cambio route → dropdown si chiude (useEffect on pathname).
9. Highlight pagina corrente → preservato ✅ (f).

### Evoluzione storica del fix (per audit)

| Versione | Pattern | Problema |
|---|---|---|
| v1 | `mousedown` + `navRef.current.contains(target)` | Falliva quando il click cadeva su elementi tecnicamente dentro `navRef` ma fuori dai trigger/panel (es. brand link, LanguageSwitcher area). |
| v2 | `mousedown` + `target.closest('[data-dropdown-region]')` | Marker corretto, ma `mousedown` arriva PRIMA dell'`onClick` del trigger. Race condition: il listener vede ancora il vecchio `openId` quando l'utente clicca un nuovo trigger → atomic switch rotto (serviva doppio click). Sub-check (a)+(b)+(d) FAIL. |
| v3 | `click` (post-bubble) + marker + **hover auto-switch su trigger** | Listener click pattern OK (5/6 PASS), ma l'`onMouseEnter` auto-switch causava un conflitto: hover sul trigger settava `openId=section.id` → click successivo sullo stesso trigger eseguiva il toggle `prev === id ? null : id` → **chiudeva** invece di mantenerlo aperto. Sub-check (d) ancora FAIL. |
| **v4 (current)** | **`click` post-bubble + marker, NO hover auto-switch** | Rimosso `onMouseEnter` da `DesktopMenuButton` e `DesktopAccountMenu`. Pattern click-only standard (GitHub/Linear/GitLab style). Hover NON apre né cambia dropdown. Toggle pulito: `setOpenId(isOpen ? null : section.id)` esegue una sola volta per click. Atomic switch funziona perché click su trigger B trova `openId="A"` → `isOpen=false` → apre B; il listener click vede `closest()=B` → skip close. 6/6 PASS atteso. |

### Diff sintetico v3 → v4

```diff
  <button
      type="button"
      data-testid={`desktop-menu-trigger-${section.id}`}
      data-dropdown-region="trigger"
      onClick={() => setOpenId(isOpen ? null : section.id)}
-     onMouseEnter={() => {
-         // Auto-switch dropdown on hover ONLY if another one is already open
-         if (openId && openId !== section.id) setOpenId(section.id);
-     }}
      aria-expanded={isOpen}
      ...
  >
```
(Identico per `DesktopAccountMenu` trigger.)

Grep verifica: `grep onMouseEnter /app/frontend/src/components/AppHeader.jsx` → **0 occorrenze**.

### Pattern UX risultante (click-only)
- **Click** su trigger → toggle (apre se chiuso, chiude se aperto).
- **Hover** → solo highlight visivo (border / bg) tramite Tailwind, nessun cambio di state.
- **Click outside** → chiude (via listener `click` post-bubble).
- **Click su link interno al panel** → navigazione + chiusura.
- **Cambio route** → chiusura.

### Diff sintetico v2 → v3

```diff
- // ROUND 16.1.1 HOTFIX (v2) — robust click-away listener using
- // `data-dropdown-region` markers. ...
- useEffect(() => {
-     if (!openId) return;
-     const handler = (e) => {
-         const target = e.target;
-         if (target && typeof target.closest === "function" &&
-             target.closest('[data-dropdown-region]')) {
-             return;
-         }
-         setOpenId(null);
-     };
-     document.addEventListener("mousedown", handler);
-     document.addEventListener("touchstart", handler);
-     return () => {
-         document.removeEventListener("mousedown", handler);
-         document.removeEventListener("touchstart", handler);
-     };
- }, [openId]);

+ // ROUND 16.1.1 HOTFIX (v3) — canonical click-away pattern.
+ // Use `click` (post-bubble) instead of `mousedown`/`touchstart` so the
+ // trigger's onClick handler runs FIRST and updates `openId` atomically.
+ useEffect(() => {
+     if (!openId) return;
+     const handler = (e) => {
+         if (e.target?.closest?.('[data-dropdown-region]')) return;
+         setOpenId(null);
+     };
+     document.addEventListener("click", handler);
+     return () => document.removeEventListener("click", handler);
+ }, [openId]);
```

### DOM marker scope confermato
Grep `data-dropdown-region` su `/app/frontend/src/`:
- 4 occorrenze totali in `AppHeader.jsx`:
  - 2 × `DesktopMenuButton` (1 trigger button + 1 panel `<ul>`)
  - 2 × `DesktopAccountMenu` (1 trigger button + 1 panel `<ul>`)
- Nessun parent/sibling indesiderato. `closest('[data-dropdown-region]')` ritorna solo se il click è effettivamente su un trigger o dentro un panel aperto.

**Mobile drawer**: invariato (`MobileBottomNav` + `MobileMenuDrawer`, separati). 5 voci bottom + 8 sezioni drawer.

**Bottom nav**: 5 slot invariati (max-5 rispettato).

---

## Sezione 15 — Test frontend lint/build eseguiti

| Check | Risultato |
|---|---|
| ESLint `Forge.jsx` | ✅ No issues found |
| ESLint `AppHeader.jsx` | ✅ No issues found |
| Webpack dev build | ✅ `Compiled successfully!` (verificato in `/var/log/supervisor/frontend.out.log`) |

---

## Sezione 16 — Eventuali bug residui

1. **OpenAPI path count test drift** (pre-esistente, non hotfix): `test_openapi_paths_unchanged_at_39` e `test_paths_count_unchanged_at_40` falliscono perché il count è cresciuto a 158 paths. NON regressione del mio hotfix — già rotti su HEAD pre-fix. Vanno aggiornati in un futuro round housekeeping.
2. **Phase18/19 raid integration tests** falliscono per gating `war_room L2 required` (territory cost change pre-esistente). NON regressione.
3. **Adventurer rename duplicate** test fallisce per cleanup test data ordering. NON regressione.
4. **In-flight stale raid** (1 raid risolto via on-visit durante test) — comportamento atteso, dimostra che il fallback funziona già in preview.

---

## Sezione 17 — Conferma esplicita: NO hard delete

✅ **CONFERMATO**. Zero `delete_many` / `drop_collection` introdotti.

Le uniche delete sono nei **test fixtures** (`_cleanup_raid` per teardown — `db.raids.delete_one` su raid creati nel test stesso, `db.adventurers.delete_many({"_test_raid_recovery_stub": True})` con flag marker custom).

`audit_log.delete_many` nei test cleanup è solo per `event_type=raid_recovered` con `related_entity_id` dei raid di test specifici — mai produzione.

Recovery production logic: zero delete. Solo `update_one` + `insert_one` (su `audit_log`, `inventory_items`).

---

## Sezione 18 — Conferma esplicita: NO modifiche a economia/drop/XP/PvP

✅ **CONFERMATO**.

- Recovery **riusa** la stessa logica di `complete_raid` (rng deterministic by raid_id, formula multiplier, base_gold/xp dal raid_dungeon doc).
- Outcome identico a quello che il giocatore avrebbe ottenuto cliccando "Complete" manualmente.
- Nessuna modifica a `complete_raid` originale.
- Nessuna modifica a `app/expeditions/`, `app/pvp/`, `app/quests/`, `app/contracts/`, `app/seasons/`.
- Nessun cambio a `base_gold_reward`, `base_xp_per_member`, `guaranteed_dragon_essence_min/max`, success chance, multiplier ratios.
- PvP arena 1v1 (`app/pvp/services.py`): **NON toccato**. Il modulo raid (`app/raids/`) è separato da PvP. Double-check via `grep "from app.pvp" app/raids/` → 0 matches.

---

## Sezione 19 — Commit finale

⏸️ **NON ancora committato**.

Il commit avverrà solo dopo:
1. ✅ Conferma utente per `--apply` recovery (output da riportare).
2. ✅ Verifica `e1_tester` E2E browser sui 3 bug.

NESSUN deploy in nessun caso (vincolo inderogabile).

---

## RIASSUNTO esecuzione attesa post-apply

Quando l'utente conferma `--apply`:

1. Esegue script CLI → 28 raid risolti (1 già fatto via on-visit), ~560 adv rilasciati, ~28 audit row `raid_recovered`.
2. Verifico DB count post-apply:
   - `stuck = 0` (atteso)
   - `recovered = 29` (atteso, con il primo già auto-risolto)
   - `audit_log.event_type=raid_recovered` count >= 28
3. Riporto output `--apply`.
4. Attendo `e1_tester` per smoke test E2E browser sui 3 bug.

---

## Files modificati (riepilogo)

**Backend**:
- `backend/app/raids/recovery.py` (NEW, 327 righe)
- `backend/app/raids/__init__.py` (modified: +13 righe per on-visit fallback)
- `backend/app/audit/log.py` (modified: +1 riga `"raid_recovered"`)
- `backend/app/scripts/recover_stuck_raids.py` (NEW, 121 righe)
- `backend/tests/backend_round1611_raid_recovery_test.py` (NEW, 7 test)

**Frontend**:
- `frontend/src/pages/Forge.jsx` (rewritten: mobile fixes)
- `frontend/src/components/AppHeader.jsx` (rewritten: single-open dropdown)

**Memory**:
- `memory/round1611_hotfix_report.md` (questo file)

---

**Fine report. Attendo conferma utente per `--apply` recovery.**
