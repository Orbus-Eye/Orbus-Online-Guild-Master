# FASE 9 — Report finale della tranche (Class Identity Rework + Tester Fixes)
Data: 2026-08-11 · Branch: `Lavoro-partito-08/08/2026`

## HEAD

- **HEAD iniziale**: `69b8871` (fine FASE 8, verificato con fetch+ff-only).
- **Commit della tranche** (uno per macro-fase):

| Fase | Commit | Contenuto |
|---|---|---|
| 9A | `06129f8` | Hotfix tester: avatar upload (root cause CSRF), gerarchia Dashboard, report puliti ovunque, 6 fondatori |
| 9B+9C | `82460eb` | Registry 27 classi con ruolo FISSO; eliminate specializzazioni e 81 build |
| 9D+9E | `fbaca53` | Equip generico di classe + 108 set raid (540 pezzi) con bonus set |
| 9F+9G | `4496c94` | Class Hall redesign + 27 emblemi/banner SVG unici + Guida riscritta |
| 9H | `9be336b` | Traits fuori dal player-facing + audit runtime |
| 9I | `5d6bebf` | ADDESTRAMENTO solo-XP (2 posti, 24h, recupero +50%) |
| 9J | `e3b75a6` | Sigillo XP: audit + policy unica condivisa + copertura totale |
| 9K+9L | `df14286` | Banner personalizzato di gilda + gerarchia Dashboard definitiva |
| 9M | `b7844b8` | Migration `fase9_old_item_cleanup` (audit/dry-run/apply/verify) |
| 9N | (questo commit) | Suite finale, backlog slot di classe, report, push |

- **HEAD finale**: il commit 9N che contiene questo report
  (`git log --oneline -1` sul branch).

## Scorecard del mandato

| Voce | Esito |
|---|---|
| Avatar upload | **PASS** — root cause RIPRODOTTA: la catena backend era sana (TestClient sull'app completa: PNG/JPEG/WEBP 200, SVG 422, >2MB 413); il bug era il client: CAMBIA RITRATTO era l'unico POST player-facing su axios "nudo", quindi senza il retry CSRF dell'istanza `api` → con token in-memory nullo/stantio falliva sempre con 403 `auth.csrf.invalid`. Fix: istanza `api` (CSRF+retry). In più: l'audit `avatar_uploaded` veniva scartato come unknown event → sanato. |
| Dashboard hierarchy | **PASS** — 1 HERO gilda (banner+nome+descrizione+livello+info) → 2 STREAK → 3 PROSSIME AZIONI → 4 PROGRESSIONE → 5 RESTO; desktop e mobile; data-testid storici conservati. |
| Report cleaned → recommended actions | **PASS** — flag reale `report_dismissed_at`; ora rispettato ANCHE da dashboard/suggestions, /expeditions/last-completed (card+replay) e /raids/last. FE già refetchava dopo PULISCI. |
| Starter adventurers | **6/6** — STARTER_TARGET=6 ("Sesta Recluta", razza reale `dragonborn_red`), FREE_FOUNDER_COUNT=6 (costo dal 7°), reset tester 6, testi aggiornati, tutti senza classe via Class Hall. |
| Classes | **27** (registry canonico `app/classes/registry.py`, allineato 1:1 al mandato) |
| DPS | **13** |
| Tank | **6** |
| Healer | **8** |
| Selectable specializations | **0** — rimossi endpoint unlock-spec e specialize/respec, SPEC_DEFINITIONS, SPECS_BY_CLASS, pannelli/chip FE, filtri spec, modificatori spec dal potere. |
| Selectable builds | **0** — rimossi BuildIdentity (81), Build Lab (BE+FE), build_reachability, wave A–E, analytics di tuning per-build; la risonanza è di CLASSE (vesti la tua classe → +2, stessi numeri di prima). |
| Legacy items remaining | **0 target** — la migration 9M li identifica (item firma spec, spec-locked/build fuori catalogo) e li disattiva (`is_active=false`+`is_legacy_removed`); Auto-Equip/loot/craft filtrano `is_active`. Da APPLICARE sull'ambiente col DB (mai automatico). |
| Orphan equipment references | **0** — verifica integrata nello script (equipped/inventory orfani = 0, fail-closed exit code). |
| Raid sets expected | **108** |
| Raid sets actual | **108** (27×4, 540 pezzi, verificati programmaticamente da 8 test) |
| Class Hall redesign | **PASS** — pagina a 27 sale: emblema, ruolo fisso (badge colore), identità, stile, punti di forza, equip di classe, prova/kit, top membri, 4 set raid in progressione; niente spec/build. |
| Class visual identities | **27/27** — emblemi SVG con glifo UNICO per classe + 27 banner; identity map verificabile nel registry (`emblem_symbol`) e nel manifest; onestà: SVG procedurali rifiniti, non art dipinta (swap-in a zero cambi di codice). |
| Traits removed from Guide | **PASS** — TraitsCatalogSection, pagina pubblica /traits e voci menu eliminate. |
| Traits removed from Adventurers | **PASS** — colonna Tratti, TraitList/TraitBadge/TraitPreviewWidget e pannello modal eliminati. |
| Trait runtime effects remaining | **TRAIT_RUNTIME_STILL_ACTIVE** — (1) PWR: `apply_trait_modifiers` sulle stat → potere effettivo di dungeon/raid; (2) XP: `sum_xp_percent` (tratti xp_gain) al completamento spedizioni; (3) combat dungeon/raid: counter_tags dei tratti nel sistema minacce (fino a +12% successo / −8% ferite); (4) loot: NESSUN effetto (mai esistito). NON invisibili: restano documentati nell'anteprima narrata delle spedizioni (ExpeditionExplainer conservato apposta). |
| Training capacity | **2** |
| Training max duration | **24h** |
| Training catch-up | **+50%** (benchmark = media dei top-5 livelli; applicato UNA sola volta: XP di addestramento piatta, senza trait/consumabili/catch-up spedizioni) |
| XP Seal dungeon coverage | **23/23** — Pietra della Conoscenza (`pietra_della_conoscenza`, 20% flat, solo successo, mai moltiplicata dall'Overpower): policy estratta in un helper condiviso usato da ENTRAMBI i path di completamento (legacy + stanze) → tutti i dungeon attivi coperti; drop rate canonico mantenuto, nessun duplicato. |
| Guild custom banner | **PASS** — POST/DELETE /api/guilds/banner con la stessa sicurezza degli avatar (magic bytes, no SVG, cap 4MB, filename server-side, ownership, cleanup, cache-busting), storage persistente + StaticFiles, priorità sul banner standard con fallback, UI CAMBIA/RIMUOVI sull'hero. |
| Backend tests | **171/171 verdi** (pure, `pytest --noconftest`, senza Mongo): fase1–8 (86 storici incl. avatar endpoint) + FASE 9: avatar endpoint (5), fondatori (4), registry classi (9), set raid (8), training (7), sigillo XP (5), banner gilda (4), cleanup (2) + contratti curva/T2/T6/T8/slice/classless aggiornati. **Suite d'integrazione (Mongo/HTTP) NON eseguibile in locale**: dichiarata, da eseguire sull'ambiente col DB. |
| Frontend tests | **Jest 13/13 verdi** |
| yarn lint | **PASS** (0 errori, 0 warning) |
| yarn build | **PASS** (Compiled successfully) |
| Sealed integrity | **PASS** — nessuno script/report sealed R18.* modificato; storia intatta (i soli file di test spec-era eliminati sono test runtime della feature rimossa, conservati nella history git). |
| Working tree | **CLEAN** (verificato dopo il commit 9N) |
| Remote branch | **PUSHED** (verifica `git ls-remote` a fine tranche) |

## Il criterio fondamentale (architettura davvero scollegata)

Non è solo UI: `specialization/build` è stato scollegato da...
- **gameplay**: `adventurer_effective_power` non applica più modificatori
  spec; il bonus di composizione squadra usa i ruoli canonici del
  registry; i counter delle minacce arrivano da CLASSE (in risonanza)
  e trait, la collection `class_specializations` è fuori dal runtime;
- **equipaggiamento**: compatibility senza ramo `specialization_unlocks`;
  catalogo T6 senza campi `build_path_*` (stat sul RUOLO via
  `role_focus_stats`); Auto-Equip senza proiezioni spec;
- **Class Hall**: 27 sale canoniche, niente unlock-spec/Build Lab
  (endpoint RIMOSSI), seed senza `unlocked_specializations`;
- **dungeon/raid**: preview e threat-resolution senza canale spec;
  tester journey/smoke matrix class-based (risonanza 27/27, ruoli
  13/6/8);
- **Auto-Equip / item legacy**: migration 9M li disattiva e ripulisce
  equip/reservation/inventory/mercato/loot/ricette con verifica
  fail-closed.

Nuovo Source of Truth: **CLASS → FIXED ROLE → CLASS EQUIPMENT → RAID SETS**
(registry `backend/app/classes/registry.py`; design completo in
`memory/fase9_class_identity_rework_design.md`; catalogo set generato in
`memory/fase9_raid_sets_catalog.md`).

## SLOT DI CLASSE (futuro, NON implementato)

Direzione approvata ma esclusa da questa tranche, come da mandato.
Architettura pronta senza refactor futuro: campo `hybrid_slot` riservato
nel registry (sempre `None`, testato). Registrato in `memory/backlog.md`
(FASE9.backlog, P2, richiede GO owner).

## Rollout sull'ambiente col DB (in ordine, mai automatico su production)

1. Deploy del branch; al boot i seed idempotenti attivano: classi
   canoniche con ruoli nuovi, catalogo T6 sanato, **540 pezzi set raid**.
2. `python -m app.scripts.fase2_redistribuzione_team_size` → `--apply`
   (se non ancora applicata) e
   `python -m app.scripts.fase8_apply_rebalance` (dry-run) → `--apply`.
3. **`python -m app.scripts.fase9_old_item_cleanup`** (dry-run) →
   review del report JSON in memory/ → `--apply`
   (con APP_ENV=production serve anche `--confirm-production`).
   La verifica integrata deve chiudere con `ok: true`.
4. Suite d'integrazione completa (`pytest backend/tests` con DB di test).
5. Collaudo manuale: avatar (PNG/JPEG/WEBP/SVG/2MB/remove), banner gilda
   (upload/priorità/rimozione/fallback, desktop+mobile), gerarchia
   Dashboard, PULISCI → Prossime azioni/ultimo report/ultimo raid,
   6 fondatori su gilda nuova e reset tester, Sale di Classe (27, ruolo,
   emblemi, set), Addestramento (2 posti, 24h, +50%, interruzione),
   drop set nei 4 raid, Pietra della Conoscenza su dungeon vari.

**Il go-live su orbusonline.net resta una decisione dell'owner.**
