# Round 18.0 Follow-up — PM Decision Matrix

**Data**: 2026-07-04T16:30Z
**Contesto**: PM ha scelto **Opzione C** (proposta ragionata) sulle 15 domande bloccanti emerse dall'audit R18.0 sezione 16. Questo file NON apre R18.1, NON implementa nulla, NON modifica codice/DB/seed.
**Scope**: SOLO analisi + raccomandazioni + rischi + impatto. Le decisioni finali le prende il PM fuori da qui.
**Fonte dati**: `/app/memory/round180_adventurer_rework_audit.md` + `/app/memory/round180_adventurer_rework_raw_data.json`.

---

## 1. Executive summary

Delle **15 decisioni bloccanti**:
- **6 possono entrare in R18.1** subito (schema-only, append-only, no breaking change): D2, D3, D6, D7, D14, D15.
- **5 richiedono R18.2/R18.3**: D4 (rename), D5 (specs→talent), D8 (class-bound SOFT→HARD), D11 (retrain), D12 (tomi).
- **4 DEFERRED oltre R18.4**: D1 (15ª classe), D9 (Legendary formula), D10 (PWR switch), D13 (roster breakdown avanzato).

Linee guida PM riducono i 13 rischi Alta gravità di R18.0 a **8 rischi Media** in R18.1.

**Raccomandazione high-level**: R18.1 può partire append-only con 6 decisioni sbloccate, purché PM confermi 5 pre-condizioni minime (D2, D3, D7, D13, D15).

---

## 2. Le 15 decisioni bloccanti

| # | Titolo | Round target |
| :---: | --- | :---: |
| D1 | 14 vs 15 classi canoniche | DEFERRED |
| D2 | 91 adventurers orfani `class_slug=None` | **R18.1** |
| D3 | `grade` default value + policy veterani | **R18.1** |
| D4 | Rename classi IT (Warlock, ecc.) | R18.2 |
| D5 | 33 class_specializations → talent tier 1 | R18.2 |
| D6 | Talent tree struttura dimensionale | **R18.1** (schema) |
| D7 | Sblocco roster progressivo formula | **R18.1** |
| D8 | Class-bound HARD vs SOFT | R18.3→R18.4 |
| D9 | Legendary grade requisiti finali | DEFERRED |
| D10 | PWR solo-equip attivazione | R18.4 |
| D11 | Prima scelta classe (forced vs random+retrain) | R18.3 |
| D12 | Tomi drop-only vs craftable vs mix | R18.3 |
| D13 | Roster 50 breakdown | **R18.1** |
| D14 | `class_halls` → `training_fields` rename | **R18.1** (alias UI) |
| D15 | 6 orfani Guardian/Cleric aliasing | **R18.1** |

---

## 3. Raccomandazione breve per ogni decisione (one-liner)

| # | Opzione E1 | Motivazione sintetica |
| :---: | :---: | --- |
| D1 | DEFERRED | Nessun dato per giustificare 15ª ora — post-R18.2 |
| D2 | **B** | Nuova classe temporanea `recruit_unassigned` + banner UI |
| D3 | **A** | Common uniforme + compensazione retro-backfill history |
| D4 | **C** | Solo Warlock→Stregone, resto già IT accettato |
| D5 | **B** | 33 specs → tier 1 pre-allocato talent tree |
| D6 | **A** | 3 rami × 5 tier × 4 talent, `max_points=30` |
| D7 | **A** | `min(50, 10 + guild_level × 2)` |
| D8 | **B** | SOFT warning R18.3 → HARD R18.4 con preavviso |
| D9 | DEFERRED | Formula richiede simulation + variety audit |
| D10 | R18.4 A | Full-switch con snapshot + feature-flag |
| D11 | **B** | Class random + `is_recruit=true` 24h + retrain 1× |
| D12 | **C** | Mix drop+craft, no premium shop |
| D13 | **A** | 50 hard cap + grandfathering |
| D14 | **B** | Mantenere collection, alias UI "Sala di Addestramento" |
| D15 | **A** | Aliasing Guardian→paladin, Cleric→priest |

---

## 4. Rischi se scegliamo A/B/C

| # | A | B | C |
| :---: | :---: | :---: | :---: |
| D1 | 🔴 rework post-hoc | 🟢 chiude scope | 🟠 gap latente |
| D2 | 🟠 misclassify | 🟢 zero-loss | 🔴 confusion |
| D3 | 🟢 semplice | 🟠 complex | 🔴 P2W |
| D4 | 🟠 sweep massivo | 🟠 residui EN | 🟢 tocca solo Warlock |
| D5 | 🔴 hard delete | 🟢 zero waste | 🟠 rework parziale |
| D6 | 🟢 flessibile | 🟠 limitato | 🔴 esplosione content |
| D7 | 🟢 progressiva | 🟠 milestone shock | 🔴 cap subito shock |
| D8 | 🔴 breaking | 🟢 preavviso | 🟠 indefinito |
| D9 | — | — | — DEFERRED |
| D10 | 🔴 breaking balance | 🟠 duale confuso | — DEFERRED |
| D11 | 🔴 forced frustration | 🟢 UX soft | 🟠 economia tomi rotta |
| D12 | 🔴 farming | 🔴 grinding | 🟢 mix bilanciato |
| D13 | 🟢 chiaro | 🟠 UI mobile complex | 🔴 no cap perf |
| D14 | 🟠 rename massive | 🟢 alias zero-cost | 🟠 doppia collection |
| D15 | 🟢 lossless | 🔴 lossy | 🟠 fragile |

---

## 5. Decisioni che possono essere prese subito

**6 decisioni** con dati sufficienti per approvazione immediata:

- **D2**: 91 orfani confermati via query. Classe temporanea `recruit_unassigned` = zero rischio.
- **D3**: 2125 adventurers `grade=None` confermati. Common default lossless.
- **D6**: Schema puro, no content design richiesto.
- **D7**: Formula derivata da roster osservato attuale (guild Lv 5→20, Lv 15→40).
- **D14**: Alias i18n zero migration.
- **D15**: 6 Guardian/Cleric mappabili deterministicamente (già in R17.3 audit).

---

## 6. Decisioni che richiedono altro audit

| # | Audit necessario | Timing | Prerequisito |
| :---: | --- | :---: | --- |
| D1 | Gap-archetype audit post talent tree | post-R18.2 | Talent tree seedato |
| D4 | Localization Sweep (R16.5.4f già tracciato) | R18.2 | Nessuno |
| D5 | Class_specs mapping → talent tier | R18.2 | D6 approvato |
| D8 | Off-class equipping audit (quanti item equipaggiati off-class oggi?) | R18.3 | Nessuno |
| D9 | Legendary progression simulation + variety weights | post-R18.3 | Grade attivo |
| D10 | Recommended_power ricalibrazione 26 content + PvP matchmaking | R18.4 | D8 HARD |
| D11 | New-player onboarding drop-off analytics | R18.3 | Analytics setup |
| D12 | Tomi economy simulation supply/demand | R18.3 | D5 + D6 |
| D13 | Riserva/archivio UX (se PM preferisce 50+riserva) | R18.3 | D7 |

---

## 7. Impatto su R18.1

**Scope**: schema foundation + data backfill append-only, feature-flag globale `r18_rework_enabled = false`.

**Cosa entra** (6 decisioni): D2, D3, D6 (schema), D7, D14 (alias UI), D15

**Nuovi field `adventurers`** (default nullable):
- `grade` (str, default "Common")
- `race` (str, nullable — backfill R18.3)
- `talent_points_available` (int, default 0)
- `talent_points_earned_total` (int, default 0)
- `is_recruit` (bool, default false)
- `class_history` (list, default [])

**Nuovi field `guilds`**:
- `max_roster_cap` (int, default 50)
- `max_roster_current` (int, computed `min(50, 10 + level × 2)`)

**Nuove collezioni** (vuote):
- `talent_catalog`, `adventurer_talents`, `adventurer_history`, `adventurer_achievements`

**Nuova classe temp**: `recruit_unassigned` in `adventurer_classes` (per 91 orfani)

**Migration script append-only** `round181_schema_foundation.py`:
1. update_many nuovi field default
2. Aliasing 6 Guardian/Cleric → paladin/priest
3. 91 orfani → `recruit_unassigned`
4. Feature flag global off

**Testing**: 1 nuovo pytest `backend_round181_migration_test.py`.

**Rischi R18.1 post-mitigazione**:
- 🟠 Media: migration 2125 adventurer → snapshot + dry-run
- 🟠 Media: banner UI orfani "Da riassegnare"
- 🟠 Media: query preventiva "gilde >50 attuali"
- 🟢 Bassa: nuove collezioni vuote

---

## 8. Impatto su R18.2 / R18.3 / R18.4

**R18.2 — Talent Tree Engine + UI** (sblocca D4, D5, D6-content)
- Rename classi IT (D4 C)
- 33 specs → tier 1 seed (D5 B)
- ~840 talent totali seed (D6 A content)
- Endpoint talent tree, UI DAG, Auto-Equip aggregation
- Beta gilde volontarie

**R18.3 — Grade + Tomi + Roster 50 + Class-Bound SOFT** (sblocca D8-soft, D11, D12, D13)
- D8 SOFT warning attivato
- D11 class random + retrain 1× (`is_recruit` logic)
- D12 tomi item_type + endpoint change-class
- D13 roster enforcement `POST /create` con cap
- Grade upgrade formula placeholder (D9 finale DEFERRED)
- Race backfill retroattivo
- History counters retro-backfill da audit_events

**R18.4 — PWR Solo-Equip + Content Rework + PvP Reset** (sblocca D10, D8-hard)
- D8 HARD switch
- D10 PWR solo-equip full-switch
- Ricalibrazione 23 dungeon + 3 raid
- Bridge Raids Lv12-17 (originariamente R17.3 Step 3)
- Endgame Lv15-20 (3 dungeon nuovi)
- Achievement endgame 10-15
- PvP season freeze + reset ELO

---

## 9. Domande finali da portare al PM

**Bloccanti per aprire R18.1** (5 conferme minime):
1. **D2 B** — nuova classe temporanea `recruit_unassigned` per 91 orfani?
2. **D3 A** — tutti Common + compensazione via history retro-backfill?
3. **D7 A** — formula `min(50, 10 + guild_level × 2)`?
4. **D13 A** — 50 hard cap con grandfathering? (Serve query preventiva "gilde >50 attuali")
5. **D15 A** — aliasing Guardian→paladin, Cleric→priest?

**Domande secondarie**:
- 6. R16.5.4f Localization Sweep — round parallelo o fuse R18.2?
- 7. Beta gilde R18.2 — opt-in volontaria o assignment casuale?
- 8. Backup DB pre-R18.1 — snapshot automatico o manuale?
- 9. Analytics setup per D11 drop-off — quale tool?

**Esplicitamente DEFERRED (no risposta ora)**:
- D1 15ª classe · D4 rename residui · D5 specs mapping · D8 HARD · D9 Legendary · D10 PWR · D11 forced/random · D12 mix · Set di classe · Formule finali PWR/grade/Legendary · Rework dungeon/raid · Nomi talent · Talenti specifici

---

## Sezione dettaglio 15 decisioni

### D1 — 14 vs 15 classi canoniche

**Problema:**
- DB ha 14 classi in `db.adventurer_classes`. Visione PM parla di 15. 91 orfani `class_slug=None` (D2) potrebbero suggerire classe mancante.

**Opzioni:**
- A) Aggiungere 15ª subito
- B) Restare a 14
- C) DEFERRED post-R18.2

**Raccomandazione e1_dev:** **C DEFERRED**. Motivazione: talent tree evidenzierà se emergono archetipi scoperti; le 14 attuali coprono Tank/Healer/DPS/Support/Hybrid ampiamente.

**Impatto:** nessuno.

**Rischio globale:** basso · **Serve decisione PM?** no · **Può entrare in R18.1?** no

---

### D2 — 91 adventurers orfani `class_slug=None`

**Problema:**
- `db.adventurers.count_documents({'class_slug': None}) = 91`. Linea guida PM: NO hard delete.

**Opzioni:**
- A) Aliasing deterministico da `class` legacy
- B) Nuova classe temporanea `recruit_unassigned` + banner UI
- C) Retire soft-delete

**Raccomandazione e1_dev:** **B**. Motivazione: aliasing rischia misclassify se legacy `class` ambiguo; retire lossy; classe temporanea preserva 91 doc con opt-in reassignment via retrain gratis (R18.3).

**Impatto:**
- DB: +1 doc `adventurer_classes`, update 91 doc
- Backend: role mapping default DPS o "Nessuno"
- Frontend: banner "Riassegna classe" + toast
- Balance: escludi `recruit_unassigned` da expedition finché riassegnato
- Migrazione: append-only, reversibile
- Rischio player-facing: mitigato da retrain gratis 1× (R18.3)

**Rischio globale:** basso · **Serve decisione PM?** sì · **Può entrare in R18.1?** **sì**

---

### D3 — `grade` default value + policy veterani

**Problema:**
- 100% adventurers hanno `grade=None`. Compensare veterani.

**Opzioni:**
- A) Common uniforme + retro-backfill history counters
- B) Tier scalati per level (Lv 1-5=Common, 6-10=Uncommon, …)
- C) Basato su achievements guild

**Raccomandazione e1_dev:** **A**. Motivazione: soluzione semplice + retro-backfill history da audit_events permette veterani di guadagnare grade rapidamente post-R18.3, senza "regalare" tier iniziali (evita P2W-feel).

**Impatto:**
- DB: update_many 2125 con `grade='Common'`
- Backend: modulo `app/adventurer_grade/` R18.3
- Frontend: badge grade
- Balance: nessuno in R18.1
- Migrazione: append-only + retro history
- Rischio player-facing: veterani lamentele — mitigazione: comunicazione + history counters

**Rischio globale:** basso · **Serve decisione PM?** sì · **Può entrare in R18.1?** **sì**

---

### D4 — Rename classi IT

**Problema:**
- 14 classi con `display_name_it` popolato. Residui EN: Warlock, Berserker, Ranger (accettati IT). Solo Warlock puro EN.

**Opzioni:**
- A) Rename tutti (sweep massivo)
- B) Lascia tutti EN
- C) Solo Warlock→Stregone

**Raccomandazione e1_dev:** **C**. Motivazione: Berserker/Ranger sono parole IT d'uso; solo Warlock è puramente straniero.

**Impatto:** update `display_name_it` warlock; i18n keys; UI label; migrazione banale.

**Rischio globale:** basso · **Serve decisione PM?** sì · **Può entrare in R18.1?** no (**R18.2**)

---

### D5 — 33 class_specializations → talent tier 1

**Problema:**
- `db.class_specializations` ha 33 doc (~2-3 per classe). Schema già `{stat_bonus, weapon_tag_unlocks, armor_tag_unlocks, requires_class_hall_level}`.

**Opzioni:**
- A) Hard delete + riscrivere talent tree
- B) Conservare come tier 1 pre-allocato
- C) Rework parziale

**Raccomandazione e1_dev:** **B**. Motivazione: le 33 specs sono già "talenti" con stat_bonus + gate; il talent tree può includerle come tier 1 dedicati. Zero data-loss.

**Impatto:**
- DB: field `talent_tier=1` + `talent_branch='primary'` (o link table)
- Backend: query talent tree include specs come tier 1
- Frontend: UI tier 1 con specs esistenti
- Balance: preservato
- Migrazione: append-only annotation

**Rischio globale:** basso · **Serve decisione PM?** sì (R18.2) · **Può entrare in R18.1?** parziale (link schema, no attivazione)

---

### D6 — Talent tree struttura dimensionale

**Problema:**
- Nessun modello dati talent tree. Serve decidere dimensione prima di seedare.

**Opzioni:**
- A) 3 rami × 5 tier × 4 talent = 60 slot/classe, `max_points=30`
- B) 2 rami × 3 tier × 3 talent = 18 slot (limitato)
- C) 4 rami × 5 tier × 5 talent = 100 slot (esplosione content)

**Raccomandazione e1_dev:** **A**. Motivazione: 60 slot/classe con `max_points=30` permette scelte strategiche; compatibile con 33 specs come tier 1 base.

**Impatto:**
- DB: nuove collezioni `talent_catalog` (vuota) + `adventurer_talents` (index)
- Backend: nessuna logica R18.1
- Frontend: nessuna UI R18.1
- Balance: nessuno (schema-only)

**Rischio globale:** basso · **Serve decisione PM?** sì · **Può entrare in R18.1?** **sì** (schema solo)

---

### D7 — Sblocco roster progressivo formula

**Problema:**
- Guild schema NON ha `max_roster`. Cap implicito via `guild_level`. Roster osservato: Lv 5→~20, Lv 15→~40.

**Opzioni:**
- A) `min(50, 10 + guild_level × 2)` (progressiva)
- B) Milestone Lv 5/10/15/20
- C) Hard cap 50 subito

**Raccomandazione e1_dev:** **A**. Motivazione: A rispetta comportamento player attuale; B crea shock; C player-hostile.

**Impatto:**
- DB: nuovi field `max_roster_cap`, `max_roster_current`
- Backend: enforcement R18.3
- Frontend: badge "24/30 avventurieri"
- Migrazione: update_many

**Rischio globale:** basso · **Serve decisione PM?** sì · **Può entrare in R18.1?** **sì** (schema + backfill)

---

### D8 — Class-bound HARD vs SOFT

**Problema:**
- `recommended_classes` è SOFT hint oggi. Visione PM: HARD enforce.

**Opzioni:**
- A) Full-switch HARD in R18.3
- B) SOFT warning R18.3 → HARD R18.4 con 2 round preavviso
- C) SOFT indefinito

**Raccomandazione e1_dev:** **B**. Motivazione: full-switch (A) rompe inventory esistente; C contraddice visione. B è compromise safe.

**Impatto:**
- DB: nessuno R18.3, enforcement backend R18.4
- Backend: `POST /equip` warning R18.3 → reject R18.4
- Frontend: banner UI R18.3
- Balance: audit preventivo off-class equipping
- Rischio player-facing: medio (senza preavviso frustra)

**Rischio globale:** medio · **Serve decisione PM?** sì (R18.3) · **Può entrare in R18.1?** no (**R18.3 SOFT, R18.4 HARD**)

---

### D9 — Legendary grade requisiti finali

**Problema:**
- Visione PM: 100 raid + 1000 dungeon + variety. Nessun contatore per-adventurer oggi.

**Opzioni:**
- A) Formula fissa
- B) Formula scalata dinamica (percentili)
- C) DEFERRED con simulation audit

**Raccomandazione e1_dev:** **C DEFERRED**. Motivazione: senza contatori per-adventurer + simulation non si può bilanciare; prima R18.3 contatori attivi, poi audit dedicato.

**Impatto:** nessuno in R18.1.

**Rischio globale:** basso (DEFERRED) · **Serve decisione PM?** no · **Può entrare in R18.1?** no

---

### D10 — PWR solo-equip attivazione

**Problema:**
- PWR oggi = base stats + equip. Visione: solo equip. 23 dungeon + 3 raid + PvP + auto-equip + expedition preview leggono PWR.

**Opzioni:**
- A) Full-switch R18.4 con snapshot
- B) Duale per 2 round (`stats.pwr` deprecated read-only)
- C) DEFERRED con audit ricalibrazione

**Raccomandazione e1_dev:** **A in R18.4**. Motivazione: linea guida PM "non in R18.1". Full-switch con feature-flag + snapshot più pulito del duale (confonde balance). Accompagnato da ricalibrazione −30-40% recommended_power.

**Impatto:**
- DB: `adventurer.stats.pwr` deprecated R18.4
- Backend: refactor expedition/preview/PvP matchmaking
- Balance: **critico** — ricalibrazione 26 content
- Rischio player-facing: alto se mal comunicato

**Rischio globale:** alto (in R18.4) · **Serve decisione PM?** sì (R18.4) · **Può entrare in R18.1?** no

---

### D11 — Prima scelta classe

**Problema:**
- Adventurer nasce con `class_slug` random. Visione PM: Common Recluta → training → classe.

**Opzioni:**
- A) Forced training (adventurer no expedition finché trainato)
- B) Class random + `is_recruit=true` 24h + retrain gratis 1× lifetime
- C) No training obbligatorio, tomi solo post-training

**Raccomandazione e1_dev:** **B**. Motivazione: A frustra new player; C rompe economia tomi; B è compromise player-friendly.

**Impatto:**
- DB: field `is_recruit` + `recruit_until`
- Backend: retrain endpoint R18.3
- Frontend: badge "Recluta" + retrain UI

**Rischio globale:** basso · **Serve decisione PM?** sì (R18.3) · **Può entrare in R18.1?** parziale (schema `is_recruit` sì)

---

### D12 — Tomi drop-only vs craftable vs mix

**Problema:**
- Nessun `item_type=tome` oggi. Zero infrastruttura mastery.

**Opzioni:**
- A) Drop-only (farming risk)
- B) Craftable-only (grinding class_hall)
- C) Mix: common drop, rare craftable, no premium

**Raccomandazione e1_dev:** **C**. Motivazione: mix garantisce path multipli, anti-P2W (linea guida PM), riusa class_halls (D14).

**Impatto:**
- DB: `item_type='class_tome'` seed R18.3
- Backend: modulo `app/tomes/` + endpoint change-class
- Balance: **critico** (drop rate + craft cost)

**Rischio globale:** medio (R18.3) · **Serve decisione PM?** sì (R18.3) · **Può entrare in R18.1?** no

---

### D13 — Roster 50 breakdown

**Problema:**
- Nessun cap oggi. Alcune gilde potrebbero avere >50 avv.

**Opzioni:**
- A) 50 hard cap + grandfathered
- B) 50 attivi + 10 riserva
- C) 50 soft warning

**Raccomandazione e1_dev:** **A**. Motivazione: hard cap chiaro; grandfathering evita frustrazione; B confonde UI mobile.

**Impatto:**
- DB: `max_roster_cap=50` + query preventiva
- Backend: `POST /create` deny in R18.3
- Rischio player-facing: medio se gilde molto sopra 50

**Rischio globale:** basso · **Serve decisione PM?** sì (+ query preventiva) · **Può entrare in R18.1?** **sì**

---

### D14 — `class_halls` rename

**Problema:**
- 1673 doc `class_halls`. Visione PM parla di "training field".

**Opzioni:**
- A) Rename collection `class_halls` → `training_fields` (migration heavy)
- B) Mantenere collection, alias UI "Sala di Addestramento"
- C) Nuova collection separata

**Raccomandazione e1_dev:** **B**. Motivazione: le 1673 class_halls sono perfette per training; rename è cosmetico; alias UI risolve senza migration.

**Impatto:**
- DB: nessuno
- Frontend: aggiornamento label i18n
- Migrazione: nessuna

**Rischio globale:** basso · **Serve decisione PM?** sì · **Può entrare in R18.1?** **sì** (alias UI)

---

### D15 — 6 orfani Guardian/Cleric

**Problema:**
- 6 adventurers `class_name='Guardian'` o `'Cleric'` — non esistenti in catalog. Già raccomandato aliasing in R17.3 audit residuo P3.

**Opzioni:**
- A) Aliasing deterministico: Guardian→paladin, Cleric→priest
- B) Retire soft-delete (perde 6 avv)
- C) Backfill random

**Raccomandazione e1_dev:** **A**. Motivazione: Guardian ~= paladin (Tank+Faith); Cleric ~= priest (Healer+Faith). Aliasing preserva narrativa; B lossy; C no basi.

**Impatto:**
- DB: update 6 doc con nuovo `class_slug`
- Frontend: label aggiornata
- Migrazione: idempotente + snapshot

**Rischio globale:** basso · **Serve decisione PM?** sì · **Può entrare in R18.1?** **sì**

---

## STOP

**Firma**: E1 Coding Agent · 2026-07-04T16:30Z

Nessuna modifica DB/codice/seed eseguita. Nessuna decisione sigillata come definitiva. R18.1 NON aperto.

---

## §10. PM Confirmations — Round 1 (parziali)

**Data**: 2026-07-04T16:45Z
**Scope**: conferme parziali del PM prima dell'apertura R18.1. Zero apply, zero implementazione. Registrazione testuale in memoria.

### D2 → CONFIRMED B (con vincoli)

- Classe temporanea / stato tecnico: `recruit_unassigned`.
- Banner UI: "Da riassegnare".
- **NON** trattare come 15ª classe canonica.
- **NON** compare nella guida come classe giocabile.
- **NON** entra nei talent tree.
- **NON** droppa item dedicati.
- Solo stato tecnico safe per recuperare orfani, zero delete, zero perdita dati.
- UI deve dire chiaramente "l'avventuriero deve essere riassegnato".

### D3 → CONFIRMED A (con caveat)

- `grade = Common` è **default tecnico iniziale**, NON retrocessione player-facing.
- Obbligatorio: feature flag `r18_rework_enabled=false` in R18.1.
- NON mostrare ancora il grade ai player in produzione.
- Preservare storia/counter esistenti.
- Preparare `career_history` (o equivalente) come tabella append-only.
- Zero perdita progressione, zero reset equip, zero forced downgrade visibile.
- Compensazione veterani da decidere in R18.3 **prima** che il grade diventi visibile.
- **Testo esatto**: "grade=Common è uno stato iniziale tecnico per normalizzare lo schema, non una decisione finale di progressione veterani."

### D6 → CONFIRMED A come scaffolding schema-only

- 3 rami × 5 tier × 4 talenti per tier = 60 slot teorici / classe, max 30 punti.
- **NON** creare talenti reali.
- **NON** decidere nomi rami.
- **NON** decidere talenti specifici.
- **NON** applicare bonus.
- **NON** creare UI completa.
- **NON** cambiare combat math.
- Serve solo a validare che lo schema supporta questa dimensione.

### D15 → CONFIRMED A (con vincoli operativi)

- Guardian → `paladin`, Cleric → `priest`.
- Mapping deterministico.
- Dry-run obbligatorio prima.
- Preview dei 6 documenti prima dell'apply (nomi, guild, level).
- Apply solo se corrispondono esattamente ai 6 identificati nell'audit.
- Nessun altro avventuriero toccato.
- Idempotenza: secondo apply = 0 modifiche.
- Audit log obbligatorio.

### D7 / D13 → PENDING

Attesa query roster read-only (vedi `/app/memory/round180_roster_distribution_query.md`).

### Pre-condizioni R18.1 → APPROVATE (non apply)

- Snapshot DB completo pre-R18.1.
- Feature flag globale `r18_rework_enabled=false`.
- Test suite `backend_round181_migration_test.py`.
- Dry-run obbligatorio per ogni backfill.
- Preview diff obbligatorio.
- Apply idempotente.
- Rollback plan documentato.

**Status**: 4/6 decisioni R18.1 confermate (D2/D3/D6/D15), 2 pending (D7/D13) in attesa dati query roster. R18.1 NON aperto. Zero apply.
