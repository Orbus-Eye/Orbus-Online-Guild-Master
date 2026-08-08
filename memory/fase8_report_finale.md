# FASE 8 — Report finale della tranche
Data: 2026-08-08 · Branch: `Lavoro-partito-08/08/2026`

## 1. HEAD iniziale e finale

- **HEAD iniziale (baseline)**: `f1d5996` (fine Tranche 1, Fasi 1–7).
- **Commit della tranche** (in ordine):

| Fase | Commit | Contenuto |
|---|---|---|
| 8A | `dbdb698` | Rebalance difficoltà dungeon: modello formale del potere, curva +50–200%, gate 70%, k=5.5 |
| 8B | `05afa8f` | Raid: gate a potere combinato (75% del consigliato), level-gate rimosso (livello solo informativo) |
| 8C | `36b643a` | Dungeon a stanze per tutti i 22 canonici + bivi con conseguenze |
| 8D | `83aa527` | Raid a fasi: pilota completo "Veglia di Lunacaduta" |
| 8E | `3c82801` | Italianizzazione completa + Guida aggiornata all'era attuale |
| 8F | `4e866ca` | Polish asset: generatore v2 e rigenerazione dei 132 SVG |
| 8G | `db7f8da` | Fix collisione BACKLOG.md/backlog.md + `yarn lint` verde (ESLint 9) |
| 8H | (questo commit) | Suite finale, fix contratto curva level-80, questo report, push |

- **HEAD finale**: il commit FASE 8H che contiene questo report
  (verificabile con `git log --oneline -1` sul branch).

## 2. Prova di difficoltà: Lv15 NON farma più il Lv40 (8A)

Modello reale misurato dal codice (`app/shared/power_model.py`):
membro ≈ 33+3·livello, +10 slot equip che crescono con livello/rarità,
+bonus ruolo fino a +25. Parità (Rating 100%) = squadra *media* di pari
livello; curva logistica k=5.5; gate d'ingresso 70% del consigliato
(raid 75%). Output integrale: `app/scripts/fase8_dungeon_difficulty_audit.py`
e `memory/fase8_dungeon_difficulty_rebalance.md`.

Accettazione (squadra Lv15 di 5, curva NUOVA — dal simulatore):

| Squadra Lv15 | Dg Lv15 (535) | Dg Lv20 (670) | Dg Lv25 (775) | Dg Lv30 (850) | **Dg Lv40 (1350, gate 945)** |
|---|---|---|---|---|---|
| sottopotenziata (455) | 30% | BLOCK | BLOCK | BLOCK | **BLOCK** |
| media (535) | 50% | 25% | BLOCK | BLOCK | **BLOCK** |
| ben equipaggiata (615) | 70% | 39% | 24% | 18% | **BLOCK** |
| molto forte (865) | 97% | 83% | 66% | 53% | **BLOCK** |

Tutti i criteri del mandato sono rispettati: la squadra Lv15 normale
gioca il suo livello, tenta il Lv20, vede il Lv25–30 fuori portata e
**non entra proprio** nel Lv40 (nessun hard level-gate: è il potere a
decidere — anche la Lv15 "molto forte" da 865 resta sotto il gate 945).
L'Overpower resta intatto per farmare i contenuti vecchi (squadra
endgame su dungeon di fascia bassa → ×3.0 su oggetti e materiali).

## 3. Raid: gating e flusso a fasi (8B + 8D)

- **Gate**: `app/raids/power_gate.py` — 75% del potere combinato
  consigliato (`RAID_CURVE` canonico: 3100 / 7700 / 10925 / 24100),
  errore 423 `raid.power_too_low` con dettagli. Level-gate rimosso da
  preview e start; il livello resta visibile come fascia consigliata
  (badge informativo ambra nel RaidBuilder).
- **Fasi (pilota completo)**: "Veglia di Lunacaduta" (`moonfall-vigil`),
  5 fasi: avvicinamento → guardiani (miniboss) → bivacco (**checkpoint
  con scelta**: Rituale di Purificazione +5 / Assalto Diretto −8 ma
  +25% oro) → rito (evento) → Araldo (boss finale). RNG deterministico
  per fase, avanzamento sul timer del `/complete` esistente, scelta via
  `POST /raids/{id}/advance`. Sconfitta prima del checkpoint = defeat,
  dopo = vittoria parziale. Le ricompense passano dal flusso legacy
  invariato (con `phase_gold_factor`). FE: timeline fasi, pannello
  checkpoint e polling in `RaidReport.jsx`.

## 4. Dungeon a stanze e bivi (8C)

- **22/22 dungeon canonici** con blueprint autoriale
  (`app/dungeons/rooms_blueprints.py`): 89 stanze base + **12 bivi**
  in **12 dungeon** (goblin-warrens, cursed-mines, lich-sanctum,
  dragons-hoard, silent-monastery-5p, pirate-fleet-5p,
  obsidian-arena-5p con boss opzionale "Campione in Carica",
  clockwork-vault-5p, voidspire-5p, infernal-pit-5p,
  celestial-citadel-5p, world-tree-roots-5p).
- Ogni bivio ha conseguenze leggibili: via prudente (+5) contro via
  ricca (−8/−10, stanza del tesoro o boss opzionale); scadenza
  decisione 24h → prosegue da solo sulla via prudente. Invariati:
  timer, bottino "in spalla", riposo +8%, fuga 50/50/50, XP a
  completamento +25%, salvage 25/25/40, CAS idempotente.

## 5. Localizzazione (8E): prima / dopo

- **Prima** (censimento a inizio tranche): 19 sospetti FE + 38 BE.
- **Dopo**: **5 FE + 8 BE**, tutti classificati e NON involontari:
  identificatori tecnici nei tester tools (`guild.level`, …),
  riferimenti API nella guida tecnica (`required_adventurer_level`,
  codici HTTP 423), dot-code di squads/chat su cui il FE fa branching,
  e falsi positivi italiani dell'euristica (frasi con placeholder
  `{required}`). Censimento: `memory/fase1_censimento_testi_inglesi.md`.
- **Guida** aggiornata all'era attuale: 7 nuove sezioni ★ in cima
  (`frontend/src/pages/guide/Fase8GuideSections.jsx`) su PWR/Rating,
  Overpower, stanze e bivi, raid a fasi, reagenti e professioni,
  consumabili e Pietra, recupero XP/ritratti/sblocco; sezioni vecchie
  riscritte (level-gate → gate a potere, peak power → potere di picco).

## 6. Asset (8F)

- Generatore v2 (`scripts/fase4_genera_assets.py`): i 132 SVG rigenerati
  — ritratti con volto/armatura/luci, banner con stelle, profondità a
  tre quinte, glow sul glifo e cornice ornamentale. Tutti validati
  well-formed; stessi nomi file → zero cambi di codice FE.
- Valutazione onesta nel manifest (`memory/fase4_asset_manifest.md`):
  richiedono art dipinta esterna l'hero della Dashboard, i ritratti
  delle 8 razze principali, i 4 banner raid e le immagini dedicate dei
  dungeon endgame. Il resto è coperto adeguatamente dal procedurale.

## 7. Backlog ed ESLint (8G)

- **Collisione risolta**: l'indice conteneva sia `memory/BACKLOG.md`
  sia `memory/backlog.md` (le due voci puntavano allo **stesso blob**
  `fdf0696e` → nessuna perdita di dati). Rimossa la voce maiuscola;
  resta `memory/backlog.md` (il nome referenziato da roadmap, PRD,
  report R18.* e dal test `backend_r18_3d_stat_role_registry_test.py`).
  I checkout su filesystem case-insensitive ora sono puliti.
- **`yarn lint`: PASS con 0 errori e 0 warning** (quindi passa anche
  `lint:strict --max-warnings 0`). Nuovo `frontend/eslint.config.js`
  (flat, ESLint 9): @eslint/js + react/recommended + jsx-runtime +
  react-hooks + jsx-a11y; `no-unused-vars` come errore. Uniche regole
  spente, motivate nel file: `react/prop-types` (mai usati) e
  `react/no-unescaped-entities` (apostrofi del copy italiano).
  Corretti 30 errori reali nel codice (12 import React inutili, 5
  catch morti, 6 variabili morte) — nessun disable "all'ingrosso".

## 8. Test (8H) — cosa è stato ESEGUITO davvero

- **Backend puro (senza Mongo), eseguito in locale**: **86/86 verdi**
  (`pytest --noconftest`): fase1 auto-equip + visibilità (11), fase2
  bilanciamento (16), fase3 reagenti/consumabili (13), fase5 stanze
  riscritto per i 22 blueprint (14), fase6 avatar (6), fase8 rebalance
  (7) + raid power gate (7) + raid a fasi (8), contratto curva
  level-80 (4).
  - Fix in questa fase: `test_level80_content_curve.py` raggruppava le
    tracce di potere con la team size storica di `DUNGEON_ENCOUNTERS`;
    ora usa quella autoritativa post-Fase 2 (`DUNGEON_TEAM_SIZE_TARGETS`)
    — `sunken-library` è un'incursione da 3 e chiede correttamente meno
    potere di un 5-piazze pari livello.
- **Smoke**: `create_app()` monta **315 route** senza errori.
- **Frontend (Jest)**: **13/13 verdi** (regressione Deposito 4,
  GameImage 4, territorio 5). **Build di produzione: Compiled
  successfully.**
- **NON eseguito in locale (dichiarato, non "verde")**: la suite
  d'integrazione (`backend_phase*`, `backend_round*`, `test_t*`, …)
  richiede MongoDB (assente su questa macchina, niente Docker) e in
  parte colpisce un backend via HTTP: va eseguita sull'ambiente col DB
  prima del go-live (`pytest backend/tests` con conftest). Il test
  "sealed" R18.4 richiede i path `/app/...` del container (limite
  ambientale pre-esistente).

## 9. Rollout DB (immutato: dry-run di default, --apply, idempotenti)

1. `python -m app.seeds.seed_fase3_reagenti_consumabili`
2. `python -m app.scripts.fase2_redistribuzione_team_size` → `--apply`
3. `python -m app.scripts.fase8_apply_rebalance` (dry-run) → `--apply`
   — allinea `dungeons.recommended_power` e
   `raid_dungeons.recommended_power_combined` alla curva canonica.
4. Suite d'integrazione completa con DB di test.
5. Collaudo manuale (checklist Fase 7 §4 + nuovi flussi: bivi, raid a
   fasi con checkpoint, gate raid a potere).

**Nessuno script tocca il DB di produzione automaticamente.**

## 10. Stato finale

- Working tree: **pulito** dopo il commit 8H (verificato prima del push).
- Remote: push del branch `Lavoro-partito-08/08/2026` eseguito a fine
  tranche (verifica con `git ls-remote`). Nessun merge verso main,
  nessun force-push, nessuna riscrittura di storia.
- Il go-live su orbusonline.net resta una decisione dell'owner.
