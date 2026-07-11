# R18.6.RV3-AFX1 · Affix Vocabulary & Pool Contract · FINAL CLOSURE REPORT

**Gate ID**: R18.6.RV3-AFX1
**Classe pilota**: Cacciatore del Vuoto
**Stato**: **CLOSED · PM-LOCKED**
**Data closure**: 2026-07-11 UTC
**Regime**: DOCUMENTAL ONLY · NO CODE · NO DB WRITE · NO MIGRATION · NO ITEM · NO AFFIX
**Autore**: e1_dev (agent Emergent)
**Ratificatore**: Product Manager (Orbus Online)

Il presente documento certifica formalmente la chiusura del gate R18.6.RV3-AFX1
(Affix Vocabulary & Pool Contract) dopo l'applicazione dei 7 micro-fix contrattuali
richiesti dal PM e l'estrazione verbatim delle 12 PM open questions con relative
ratifiche. Nessuna scrittura applicativa è stata effettuata. AFX1 diventa
IMMUTABILE al termine di questo dispatch.

---

## 1. PM verdict

Il Product Manager ha emesso il verdetto finale conclusivo su AFX1:

- **Draft aggiornato accettato** (post-7-micro-fix + AFX1-Q verbatim extraction)
- **Nessun ulteriore micro-fix richiesto**
- **12/12 AFX1-Qn ratificate individualmente** (Q1..Q12, incluse Q12 resolution)
- **AFX1 = PM APPROVED · READY FOR FORMAL CLOSURE · PM-LOCKED AFTER CLOSURE**
- **GO Formal Closure** autorizzata su un singolo dispatch (solo generazione artifact + PRD append + validazione governance)
- **Nessun kickoff IC1 in questo dispatch**; IC1 resta HOLD

Riferimenti tracciabili:
- Draft dispatch 1 (creazione base): commit `0812f7a`
- Dispatch 2 (7 micro-fix + AFX1-Qn extraction): commit `2333d43` (HEAD attuale, 2026-07-11 20:37 UTC)
- Ratifica finale PM: presente dispatch (contenente questo closure report)

## 2. AFX1 CLOSED

Stato ratificato in questo report:

- `gate_id = R18.6.RV3-AFX1`
- `state = CLOSED`
- `pm_locked = true`
- `immutable_after_this_dispatch = true`
- `reopen_authorization = NOT AUTHORIZED (deferred to hypothetical AFX2 future gate)`

Dipendenze contrattuali chiuse:
- Contratto vocabolario affix Cacciatore del Vuoto **congelato v1**
- Contratto pool selector class-specific **congelato v1**
- Schema affix definition **congelato v1**
- Slot budget, cap meccanici, boss safeguard, divieti **congelati v1**

Le modifiche future al vocabolario o al pool contract di AFX1 richiederanno l'apertura
di un nuovo gate (candidato: **AFX2**). Nessuna modifica retroattiva in-place è consentita.

## 3. 85/85 sezioni

Il documento sorgente `r18_6_rv3_afx1_affix_vocabulary_pool_contract.md` risulta
completo secondo la spec dispatch 1 + dispatch 2:

- **Section count `^## [0-9]+`** = **85 / 85** (verificato via `grep -c`)
- **Line count** = **1525** righe
- **SHA256 (full_file)** = `6600273d8a2412a9ed373e229e168d69c21b231b3d8ada48f3e5016dc7ee86df`
- **JSON companion (root keys)** = **14** (verificato via `python -c "import json;len(json.load(open(...)).keys())"`)
- **JSON parse** = VALID
- **JSON line count** = **596**
- **JSON SHA256** = `7b4cc068e2cd69f24591b49b8a3c960985ae298df52cc6b78cc513ac9fe1d08e`

Copertura sezioni AFX1 (blocchi A–H):
- Block A `governance_precedenza` = §1–§8
- Block B `class_identity_lock` = §9–§16
- Block C `10_affix_families` = §17–§66 (10 famiglie × 5 sub-sezioni)
- Block D `vincoli_meccanici` = §67–§72
- Block E `divieti_boss_safeguard` = §73–§77
- Block F `affix_pool_tag_contract` = §78–§80
- Block G `ev_f2_interaction_item_specifics` = §81–§83
- Block H `risk_register_closure` = §84–§85

## 4. 10 famiglie affix

Le **10 famiglie canonical class-specific v1** LOCK per Cacciatore del Vuoto:

| # | Family namespace | Family label IT | Internal tag |
|---|---|---|---|
| 1 | `void.mark.power` | Potenza del Marchio | `AFX_MARK_POWER` |
| 2 | `void.mark.duration` | Durata del Marchio | `AFX_MARK_DURATION` |
| 3 | `void.fragment.yield` | Resa Frammenti | `AFX_FRAG_YIELD` |
| 4 | `void.dispel.quality` | **Qualità della Dissipazione** (micro-fix 1) | `AFX_DISPEL_QUALITY` |
| 5 | `void.focus.channel` | Focus Channel Bonus | `AFX_FOCUS_CHANNEL` |
| 6 | `void.resolution.efficacy` | **Efficacia della Risoluzione** (micro-fix 1) | `AFX_RESOLUTION_EFFICACY` |
| 7 | `void.dagger.close` | Ritual-Close Pugnale | `AFX_DAGGER_CLOSE` |
| 8 | `void.summon.suppression` | Soppressione Summon | `AFX_SUMMON_SUPPRESSION` |
| 9 | `void.proc.stability` | Stabilità Procs | `AFX_PROC_STABILITY` |
| 10 | `void.consistency.guard` | Consistency Guard | `AFX_CONSISTENCY_GUARD` |

Tutte e 10 sono classificate come **class-specific v1** (ownership = `cacciatore_del_vuoto`).
Nessuna famiglia shared/universal è definita in AFX1.

## 5. Namespace ratificati

Namespace canonici approvati (AFX1-Q1 = APPROVED PM):

- Pattern: `void.<family>.<sub>` (formato immutabile v1)
- Tutte 10 famiglie sono conformi al pattern
- **`family_namespace`** identifica la famiglia (dominio semantico/effect_scope)
- **`internal_tag`** = enum stabile per lookup interno (10 canonical, uno per famiglia)
- Nessun namespace inventato al di fuori del set di 10
- Estensioni namespace future = aperture nuovo gate (non modifica retroattiva)

## 6. Label player-facing corrette

Terminology micro-fix 1 applicato (definitivo):

| Famiglia | Label IT precedente (draft 1) | Label IT ratificato (post micro-fix 1) |
|---|---|---|
| F4 `void.dispel.quality` | ~~Qualità del Dispel~~ | **Qualità della Dissipazione** |
| F6 `void.resolution.efficacy` | ~~Efficacia del Risolvente~~ | **Efficacia della Risoluzione** |

Localization scope (AFX1-Q10 = APPROVED PM):
- **IT primary** + **EN readiness** (struttura i18n) obbligatori v1
- Altre lingue (FR/DE/ES/JP/BR/…) → gate localizzazione futuro (Registry v3)
- Content player-facing corrente = **ITALIANO ONLY** (nessuna traduzione EN implementata)

## 7. family_namespace distinto da affix_pool_tag

Micro-fix 2 applicato · disclaimer permanente contrattuale:

- **`family_namespace`** ≠ **`affix_pool_tag`** (sono due concetti diversi, mai fungibili)
- `family_namespace` = **famiglia semantica** dell'affix (`void.<family>.<sub>`), 10 valori canonical
- `affix_pool_tag` = **selettore pool sull'item** (single-value v1), classifica quale set di affix è selezionabile per quell'item
- Un item ha **1** `affix_pool_tag` che punta a **1** pool contenente affix di **N famiglie diverse**
- Correzione claim §80: la formulazione "10 famiglie class-specific · 0 shared/universal" descrive **la ownership delle famiglie**, non la **cardinalità dei pool**
- Il pool class-specific di Vuoto è **uno solo** (§8 sotto)

Riferimenti sorgente:
- §1256 MD `### Micro-fix 2 · Chiarimento family_namespace ≠ affix_pool_tag`
- JSON key `pm_micro_fix_addendum.micro_fix_2_family_namespace_vs_affix_pool_tag_disclaimer`

## 8. Pool v1: `void.cacciatore_del_vuoto.pool.v1`

Micro-fix 3 applicato · pool contract:

- **Canonical value**: `void.cacciatore_del_vuoto.pool.v1`
- **Status**: **CONTRACT LOCK · NOT POPULATED · NOT APPLIED**
- **Ownership**: class-specific `cacciatore_del_vuoto`
- **Cardinality**: **UNO solo pool class-specific v1** (non "uno per famiglia")
- **Populations**: **NOT AUTHORIZED** (nessun affix creato in AFX1)
- **Runtime apply**: **NOT AUTHORIZED**
- **Registry v3 write**: **NOT AUTHORIZED**

Riferimenti sorgente:
- §1275–§1276 MD `canonical value proposto (Vuoto): void.cacciatore_del_vuoto.pool.v1` + `status: CONTRACT LOCK · NOT POPULATED · NOT APPLIED`
- §1279 MD: definizione semantica ("L'item è eleggibile al pool affix v1 del Cacciatore del Vuoto.")
- §1310 MD (esempio SCHEMA ONLY): `pool = void.cacciatore_del_vuoto.pool.v1`
- §1340 MD tabella §80 corretta
- JSON key `pm_micro_fix_addendum.micro_fix_3_affix_pool_tag_correct_contract`

## 9. Single-value pool selector

AFX1-Q7 = APPROVED PM · politica cardinalità pool:

- **v1 (AFX1)**: `affix_pool_tag` = **single-value** per ogni item
  - Un item → **esattamente 1** `affix_pool_tag`
  - Vietato multi-value in v1 (evita ambiguità di risoluzione)
- **v2 (eventuale futuro)**: estensione multi-value ammessa **solo** se PM directive dedicata autorizzerà l'apertura di un nuovo gate (candidato AFX2)
- **NON in AFX1**: nessuna implementazione multi-value, nessuna sintassi (es. array), nessun parser

Riferimenti sorgente:
- AFX1-Q7 verbatim (MD riga 1418): `Testo: affix_pool_tag single-value con estensione multi-value in v2?`
- Recommendation e1_dev: `APPROVE (§78)`
- PM Ratification: `APPROVE single-value v1 · multi-value v2 futuro (PM directive dedicata)`

## 10. Multi-affix item contract

Micro-fix 5 applicato · chain semantica:

- **Contract chain**: `1 item → 1 affix_pool_tag (single-value) → N affix (di famiglie diverse)`
- Un item con `affix_pool_tag = void.cacciatore_del_vuoto.pool.v1` può ricevere
  **più affix** provenienti da **famiglie differenti** entro i vincoli tier/rarity/conflict/hard-cap
- Vietata l'interpretazione "un pool_tag diverso per ogni famiglia" nel modello v1
- Nessun affix effettivamente creato: **il contratto vive solo come schema/policy design-only**

Vincoli additivi al contract multi-affix:
- Slot budget tier (§11 sotto)
- Rarity budget (Common minor / Legendary maggiore)
- Conflict rules (§21/§26/etc `conflict_group` per famiglia)
- Hard cap meccanici (§20 sotto)
- Mutual exclusion (`conflict_group` matching)

## 11. T1–T5 slot budget

Micro-fix 5 (slot policy) applicato · LOCK v1 design contract only, **non popolato**:

| Tier | Nome | Affix slots per item |
|---|---|---|
| T1 | Aspirante | **1** |
| T2 | Cacciatore | **2** |
| T3 | Iniziato | **3** |
| T4 | Rituale | **4** |
| T5 | Vuoto | **5** |

Semantica:
- Cardinalità **stabile e monotona** T1→T5 (crescita lineare +1 per tier)
- **Non popolato in AFX1**: nessun item viene modificato, nessun affix è assegnato
- Runtime enforcement = deferred a gate futuri (Registry v3 apply)
- Marker interno: `LOCK v1 · design contract only · non popolata`

Riferimento: MD righe 1321–1333, JSON key `pm_micro_fix_addendum.micro_fix_5_multi_affix_slot_budget_lock_v1`.

## 12. Affix definition contract 13/13

Micro-fix 4 applicato · schema affix definition v1 (13 campi):

| # | Field | Type | Note |
|---|---|---|---|
| 1 | `affix_id` | string | future_value · **NO creation in AFX1** |
| 2 | `family_namespace` | string enum (10 canonical) | §17–§66 |
| 3 | `internal_tag` | string enum (10 canonical) | e.g. `AFX_MARK_POWER` |
| 4 | `player_label_key` | string i18n key | localization deferred |
| 5 | `description_key` | string i18n key | localization deferred |
| 6 | `effect_scope` | string enum | Mark / Drain / Payoff / … |
| 7 | `eligible_item_families` | list[string] | focus / pugnale / armor / accessory / … |
| 8 | `eligible_tiers` | list[string] | subset T1–T5 |
| 9 | `eligible_rarities` | list[string] | subset Common – Legendary |
| 10 | `stacking_rule` | string enum | e.g. `additive_intra_slot_max_1` |
| 11 | `hard_cap_rule` | string / number | family-specific cap |
| 12 | `conflict_group` | string enum | e.g. `MARK_MAGNITUDE_GROUP` |
| 13 | `version` | integer | `v1` per AFX1 |

Vincoli schema:
- **VIETATO** creare in AFX1: `affix_id` reali · righe affix · item · DB field · Registry v3 module
- **CONSENTITO** solo: schema, esempio concettuale, terminology
- **v1 = 13 campi LOCK**; estensioni schema future = AFX2 hypothetical gate

Riferimento: MD righe 1285–1305, JSON key `pm_micro_fix_addendum.micro_fix_4_affix_definition_schema_contract`.

## 13. Shared pool reserved

Micro-fix 6 applicato · **Shared pool NON DEFINITO v1**:

- **Status v1**: `NON DEFINITO · reserved_future_contract`
- **Semantica riservata (design-only)**: pool che raggruppa affix condivisi da un
  sottoinsieme di classi (es. tutte le classi "caster/void-oriented") — struttura teorica
- **Vietato in AFX1**: inventare valori come `shared.pool.v1`, `void_family.shared.pool.v1`,
  o qualsiasi tag shared arbitrario
- **Attivazione**: solo tramite futuro gate dedicato (candidato AFX2 o gate Registry v3 specifico)
- **Non blocca IC1**: IC1 può procedere in futuro senza shared pool

Riferimento: MD righe 1334–1342, JSON key `pm_micro_fix_addendum.micro_fix_6_shared_universal_pool_reserved_future_contract`.

## 14. Universal pool reserved

Micro-fix 6 applicato · **Universal pool NON DEFINITO v1**:

- **Status v1**: `NON DEFINITO · reserved_future_contract`
- **Semantica riservata (design-only)**: pool che raggruppa affix universali applicabili
  a **tutte** le classi (es. affix generici tipo `crit_chance`, `damage_flat`)
- **Vietato in AFX1**: inventare valori come `universal.pool.v1`, `all_classes.pool.v1`, o simili
- **Attivazione**: solo tramite futuro gate dedicato
- **Compatibilità pool tiers**: Class-specific / Shared / Universal costituiscono i **3 livelli
  gerarchici** di pool. AFX1 v1 definisce solo il livello **Class-specific** (Vuoto).

Nota: la scelta di non definire shared/universal in AFX1 è **intenzionale** per evitare
lock-in prematuro su architetture pool multi-livello.

## 15. Null handling

Micro-fix 7 applicato · caso **A · Null** (stato valido):

- `affix_pool_tag = null` → **assenza valida di pool**
- **Comportamento**: nessun affix class-specific assegnabile all'item
- **Errore**: **NO** (stato ammesso, non è una violazione)
- **Auto-derive**: **NO** (mai auto-inferire pool da nome/lore/keyword/famiglia)
- **Silent conversion**: **VIETATA** (vedi §18)
- **Runtime posture**: item con `affix_pool_tag = null` è consentito e non produce errore

Uso semantico:
- Item **legacy** senza pool esplicito → `null` come stato transitorio ammesso
- Item **cosmetic/non-equippable** che non necessitano di affix → `null` come stato definitivo
- Item **futuri Vuoto-native** senza pool inizializzato → `null` in fase di draft, promosso a valore reale a runtime tramite Registry v3 apply (gate futuro)

Riferimento: MD righe 1350–1355 (Caso A), JSON key `pm_micro_fix_addendum.micro_fix_7_null_unknown_invalid_handling_three_distinct_cases.case_a_null`.

## 16. Unknown fail-closed

Micro-fix 7 applicato · caso **B · Unknown** (FAIL CLOSED):

- Definizione: valore **sintatticamente valido** MA **non presente nel registry/versione conosciuta**
- Esempio: `void.somebody.pool.v99`, `void.unregistered_pool.v1`, `void.<future_family>.pool.v1` (non ancora ratificato)
- **Comportamento**: **VALIDATION ERROR**
- **Runtime posture**: **FAIL CLOSED** (blocca l'applicazione, non tenta ricovero)
- **Apply**: **NO APPLY** (l'item non riceve affix)
- **Logging**: obbligatorio (design-only, non implementato in AFX1)
- **Correzione**: **NO** silent conversion; richiede intervento esplicito e/o registrazione di quel pool nel registry

Riferimento: MD righe 1357–1361 (Caso B), JSON key `pm_micro_fix_addendum.micro_fix_7_null_unknown_invalid_handling_three_distinct_cases.case_b_unknown`.

## 17. Invalid fail-closed

Micro-fix 7 applicato · caso **C · Invalid** (FAIL CLOSED):

- Definizione: **tipo errato** · **formato errato** · **namespace errato** · **versione invalida**
- Esempi: `123` (non-string), `POOL_ABC` (non-namespace), `""` (empty), `null-str "null"` (string literal), `void.pool.v1` (namespace short), `void.family.pool.v-1` (versione negativa)
- **Comportamento**: **VALIDATION ERROR**
- **Runtime posture**: **FAIL CLOSED** (blocca)
- **Apply**: **NO APPLY**
- **Correzione**: **NO** silent conversion
- **Rigetto**: hard reject a livello schema (JSON schema / Pydantic model equivalente in gate futuro)

Riferimento: MD righe 1363–1367 (Caso C), JSON key `pm_micro_fix_addendum.micro_fix_7_null_unknown_invalid_handling_three_distinct_cases.case_c_invalid`.

## 18. No silent conversion

Regola contrattuale esplicita post-micro-fix 7:

- **NON convertire silentemente** `unknown` o `invalid` in `null`
- **NON convertire** valori invalid in default fallback (`void.cacciatore_del_vuoto.pool.v1` o altro)
- **NON auto-correggere** namespace mistypati
- **NON estendere** silenziosamente il registry con nuovi valori
- **Ogni deviazione** = errore esplicito + log + PM review

Runtime fallback futuro (**NON progettato in AFX1**):
- Un eventuale runtime fallback difensivo potrà:
  - (a) **NEGARE** gli effetti affix
  - (b) **LOGGARE** l'anomalia
  - (c) **NON** correggere il dato
- Design del fallback = gate futuro (Registry v3 runtime hardening)

Riferimento: MD riga 1371 "**Regola esplicita**: NON convertire silentemente unknown/invalid in null durante authoring, validation o apply."

## 19. 18 hard divieti

Divieti contrattuali immutabili post-AFX1 (Block E · §73–§77 del MD sorgente).
Elenco canonico ratificato:

| # | Divieto | Riferimento §MD |
|---|---|---|
| 1 | NO direct boss cleanse | §75 boss safeguard |
| 2 | NO direct boss nullification | §75 boss safeguard |
| 3 | NO instant kill affix | §73 |
| 4 | NO life-steal via affix (bypassa risorsa Vuoto) | §73 |
| 5 | NO permanent debuff su boss | §75 |
| 6 | NO player agency bypass (§74) | §74 |
| 7 | Boss safeguard bypass (proibito) | §75 |
| 8 | NO random full-resource waste senza player agency | §74 |
| 9 | NO shared/universal pool improvvisato | §80 · micro-fix 6 |
| 10 | NO auto-derive pool da nome/lore | §79 · micro-fix 7 |
| 11 | NO silent conversion unknown→null | §79 · micro-fix 7 |
| 12 | NO silent conversion invalid→null | §79 · micro-fix 7 |
| 13 | NO namespace inventato out-of-set | §17–§66 · AFX1-Q1 |
| 14 | NO multi-value `affix_pool_tag` in v1 | §78 · AFX1-Q7 |
| 15 | NO shared/universal populated v1 | §80 · AFX1-Q8 |
| 16 | NO Fragment cap > 5 | §67 · AFX1-Q3 |
| 17 | NO combined proc cap > 45% | §70 · AFX1-Q2 |
| 18 | NO retroactive edit AFX1 post-closure | policy CLOSED · PM-LOCKED |

Totale: **18/18 divieti ratificati**. Sono immutabili senza apertura di nuovo gate.

## 20. Mechanical hard caps

Vincoli meccanici LOCK v1 (Block D · §67–§72), ratificati:

| Cap | Valore | Riferimento | AFX1-Qn |
|---|---|---|---|
| Fragment cap | **5** | §67 | Q3 CONFIRMED |
| Active marks cap | **5** | §68 | Q3 CONFIRMED |
| Mark duration cap | **10 turni** | §69 | Q3 CONFIRMED |
| Combined proc hard cap | **45 %** | §70 | Q2 CONFIRMED |
| Focus channel bonus | **+1 Frammento** | §71 | Q4 APPROVED |
| Focus segment cap | **max 2 Frammenti per resource segment** | §71 | Q4 APPROVED |
| Pugnale ritual-close bonus | **+1 Frammento** | §72 | Q5 APPROVED |
| Pugnale ritual-close cap | **max 1x per applicazione Marchio** | §72 | Q5 APPROVED |

Tutti i cap sono **hard**: nessun affix, item, buff, evento può superarli.
Estensione = gate futuro con giustificazione bilanciamento esplicita.

## 21. Boss safeguards

Boss safeguard policy LOCK v1 (§75), ratificata via **AFX1-Q6 = CONFIRMED PM**:

- **3F (Three-Fragment area dispel)**: consentito su target non-boss
- **5F (Five-Fragment annullamento summon valida)**: consentito su valid boss-summoned adds con safeguard
- **Boss diretto**: **IMMUNE** a cleanse/nullify diretti da affix
- **Valid boss-summoned add**: consentito con safeguard (add validato con `type: summon`)
- **Random adds (non-boss-summoned)**: fully targetable

Divieti correlati:
- Nessun affix può eludere `boss.immune = true`
- Nessun affix può forzare cleanse su un boss target diretto
- Nessuna combinazione di affix può replicare l'effetto di un boss cleanse via loophole

Riferimenti: MD §75 righe ~940–1010, MD riga 1184 (AFX1-Q6 recommendation `CONFIRM (§75)`).

## 22. Anti-P2W

Contratto anti-Pay-to-Win preservato:

- Nessun affix in AFX1 può essere `can_be_sold_for_real_money = true`
- Nessun affix è generato per essere venduto sul market real-money
- Il campo `can_be_sold_for_real_money` sui 178 item live catalog **resta**:
  - `false/absent` in **128** item (compliant baseline)
  - `missing` (data quality gap) in **50** item (deferred a future Data Quality gate, PM directive)
- Nessun **backfill** autorizzato in AFX1 sui 50 item con field mancante
- **Auto-P2W-detection** = **NON progettato in AFX1**

Baseline immutabile:
- 178 item live (ledger EV-F2 canonico)
- 12 REUSE_VALID · 32 REUSE_CONDITIONAL · 134 NOT_COMPATIBLE · 0 PM_REVIEW
- Contratto anti-P2W = LOCK

## 23. EV-F2 ledger immutability

Il ledger EV-F2 rimane **IMMUTABILE** post-chiusura RV3-EV:

- **178 item live** (ratificato)
- **12 REUSE_VALID** (eligible ora per Vuoto)
- **32 REUSE_CONDITIONAL** (eligible con condition code + PM per-item approval + explicit allowlist)
- **134 NOT_COMPATIBLE** (definitivamente non riutilizzabili per Vuoto)
- **0 PM_REVIEW** (nessun pending)

Vincoli contrattuali (AFX1-Q9 = APPROVED PM):
- 32 REUSE_CONDITIONAL richiedono handling futuro con:
  - **Explicit allowlist**
  - **Per-item approval PM**
  - **Condition code catalog** (§83 AFX1)
  - **Dry-run obbligatorio**
  - **Snapshot pre/post**
  - **Explicit PM GO**
- **Nessuna inclusione dinamica** per keyword/tag/Intelligenza/caster/warlock/etc

Ledger 178 = source of truth per ogni gate downstream. Modifiche = nuovo gate dedicato.

## 24. 12/12 PM questions

Estrazione verbatim + ratifica finale (Block H · §84 → addendum righe 1376–1508 del MD):

| ID | Recommendation e1_dev | PM Ratification | Stato |
|---|---|---|---|
| AFX1-Q1 | APPROVE (nomi coerenti G3/G4 loop) | APPROVED | RATIFIED |
| AFX1-Q2 | CONFIRM (§70) | CONFIRMED (45%) | RATIFIED |
| AFX1-Q3 | CONFIRM (G4+G3 loop) | CONFIRMED (5/5/10) | RATIFIED |
| AFX1-Q4 | APPROVE (§71 G2 focus lock) | APPROVED (+1F, cap 2F) | RATIFIED |
| AFX1-Q5 | APPROVE (§72 G2 pugnale lock) | APPROVED (+1F, 1x/Marchio) | RATIFIED |
| AFX1-Q6 | CONFIRM (§75) | CONFIRMED (3F/5F/immune/valid add) | RATIFIED |
| AFX1-Q7 | APPROVE (§78) | APPROVED (single-value v1) | RATIFIED |
| AFX1-Q8 | APPROVE (§80) | APPROVED (class-specific v1) | RATIFIED |
| AFX1-Q9 | APPROVE (§83, F2-Q2 constraints) | APPROVED (allowlist+per-item+PM GO) | RATIFIED |
| AFX1-Q10 | APPROVE | APPROVED (IT primary + EN readiness) | RATIFIED |
| AFX1-Q11 | CONFIRM (§85) | REDEFINED (sequenza non lineare, §25 sotto) | RATIFIED |
| AFX1-Q12 | HOLD PM directive futura | **RESOLVED** (AFX2 reserved future, §25 sotto) | RATIFIED |

**Copertura**: 12 / 12 domande ratificate. Nessuna pending.

## 25. Q12 resolution

**AFX1-Q12 = RESOLVED · AFX2 = NOT REQUIRED NOW · RESERVED FUTURE**

Testo verbatim Q12: "AFX1 closure gate follow-up (AFX2 vocabulary v2 vs Registry v3 architecture)?"

**PM Ratification esplicita**:
- **AFX2 NOT REQUIRED NOW**
- **AFX2 RESERVED FUTURE**
- **AFX2 NOT AUTHORIZED**
- **AFX2 NOT REQUIRED FOR IC1**

Motivazione ratifica:
- AFX1 v1 **già definisce tutti** i requisiti gate v1:
  - 10 famiglie · namespace · pool class-specific · affix definition contract · cardinalità
  - stacking · conflict · hard cap · null/unknown/invalid behavior · Registry v3 integration rules
- IC1 (Item Coverage & Content Blueprint) può procedere senza AFX2
- Registry v3 content/spec gates possono procedere senza AFX2

**AFX2 sarà aperto solo se serviranno** (elenco esaustivo autorizzato):
1. Shared affix pool (definire il livello shared)
2. Universal affix pool (definire il livello universal)
3. Multi-pool architecture (item con multipli pool selector)
4. Multi-value `affix_pool_tag` (array selector)
5. Affix vocabulary v2 (nuove famiglie oltre le 10 di v1)
6. Cross-class affix contracts (affix condivisi fra classi diverse)

**Nessuno di questi 6 requirement è necessario ora**. AFX2 = HOLD indefinito.

## 26. AFX2 reserved future

Registrazione formale AFX2 (non-gate, riserva contrattuale):

- **Status**: `RESERVED FUTURE · NOT AUTHORIZED · NOT REQUIRED FOR IC1`
- **Trigger di apertura** = uno dei 6 requirement di §25
- **Precondizioni**:
  - AFX1 = CLOSED (soddisfatto da questo report)
  - IC1 avanzato o completato (raccomandato ma non strettamente necessario)
  - PM directive esplicita di apertura
- **NON blocca**:
  - IC1
  - Registry v3 content generation (in dry-run staging)
  - NC1 (Null Conflict Remediation Planning)
  - Gate 11
- **Non modifica retroattivamente AFX1**: AFX2 sarà **additive**, non replacement

## 27. IC1 next planned gate

**IC1 (Item Coverage & Content Blueprint)** = prossimo gate proposto:

- **Status**: `HOLD · PROPOSED NEXT GATE · NOT AUTHORIZED IN THIS DISPATCH`
- **Scope proposto** (bozza, subject to PM directive):
  - Definizione distribuzione item T1–T5 per Cacciatore del Vuoto
  - Coverage per slot type (weapon focus, weapon dagger, armor, accessory, …)
  - Coverage per rarity (Common → Legendary)
  - Content blueprint per Registry v3 (design-only, non apply)
  - Mappatura come le 12 REUSE_VALID + 32 REUSE_CONDITIONAL entrano nel content blueprint
- **Precondizioni soddisfatte**:
  - RV3-EV = CLOSED (ledger 178 canonico)
  - AFX1 = CLOSED (contratto affix v1 in vigore)
  - Cacciatore del Vuoto pilot = ACTIVE-DESIGN-READY
- **Precondizioni pending**: attesa esplicita PM directive di apertura IC1
- **In questo dispatch**: **NON aperto**, **NON draftato**, **NON pre-work**

## 28. Item generation disabled

Registrazione stato item generation post-AFX1 CLOSED:

- **Item generation** = **NOT AUTHORIZED**
- **Nessun item creato in AFX1** (né in dry-run, né in staging, né in live)
- **Registry v3 item modules** = **NON generati**
- **DB item collection** = **INVARIATO** (nessuna write)
- **178 item live catalog** = **INVARIATO** (immutato dal ledger EV-F2)

Regola contrattuale:
- Item generation richiede almeno IC1 CLOSED + Registry v3 content gate CLOSED + esplicito PM GO
- **Dry-run** consentito in gate futuri con snapshot + PM approval
- **Real apply** su DB **VIETATO** senza:
  - Dry-run diff review
  - Snapshot pre-apply
  - PM sign-off
  - Fail-closed rollback plan

## 29. Registry v3 apply disabled

Registrazione stato Registry v3 apply:

- **Registry v3 apply** = **NOT AUTHORIZED**
- **Registry v3 content generation** = **NOT AUTHORIZED**
- **Nessun modulo Registry v3** creato in AFX1
- **`affix_pool_tag` population** = **NOT AUTHORIZED**
- **`rec_classes` field update** = **NOT AUTHORIZED**
- **Backfill campi mancanti (50 item)** = **NOT AUTHORIZED**
- **Backfill `slot_type` (21 item)** = **NOT AUTHORIZED**

Regola contrattuale (AFX1-Q9 constraints, ratified):
- Registry v3 apply richiede:
  - AFX1 CLOSED (soddisfatto)
  - IC1 CLOSED (non aperto)
  - NC1 CLOSED (non aperto)
  - Explicit allowlist per item
  - Condition code catalog compilato
  - Dry-run diff PM-approved
  - Snapshot pre/post
  - Explicit PM GO per apply

**In questo dispatch**: **NO Registry v3 write · NO Registry v3 apply**.

## 30. Governance evidence

Evidence pytest + hash + git state raccolti al momento della closure:

- **Pytest sealed integrity** (`backend/tests/backend_r18_4_sealed_integrity_test.py`):
  - Risultato: **6 passed in 0.37s**
  - Sigilli byte-identical: **36 / 36**
- **Anchor hash** `backend/app/content/lore_meta.py`:
  - **`a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`** ✅ INVARIATO
- **Backend source files** = **0 changes**
- **Frontend source files** = **0 changes**
- **OpenAPI schema** = **0 changes**
- **DB writes** = **0** (nessuna operazione database in AFX1)
- **Migrations** = **0**
- **Item creations** = **0**
- **Affix creations** = **0**
- **Affix backfill** = **0**
- **Registry apply** = **0**
- **File governance PRD.md** = APPEND-ONLY (nessuna riscrittura di sezioni pre-esistenti)
- **Nuovi sigilli aggiunti** = **0** (nessuna nuova seal registration)

Il regime DOCUMENTAL-ONLY è **preservato al 100%** per l'intero ciclo AFX1.

## 31. SHA policy clarification (full_file_sha256 vs content_body_sha256, self-referential SHA policy)

**Policy ratificata dal PM in questo dispatch**:

### 31.1 · Distinzione nomi canonici

| Nome | Definizione | Uso |
|---|---|---|
| `full_file_sha256` | Hash SHA-256 del file **completo on-disk** (byte-for-byte come letto dal filesystem) | **Canonico** per: integrity check, closure manifest, audit comparison, filesystem verification, source-of-truth validation |
| `content_body_sha256` | Hash SHA-256 del **body escluso footer** (o altra porzione dichiarata del contenuto) | **Alternativa** per uso interno quando si vuole tracciare l'hash di una porzione stabile del contenuto, escludendo elementi che si aggiornano ricorsivamente |

I due valori **NON devono essere confusi** né usati intercambiabilmente.

### 31.2 · Regola self-referential (immutabile)

**VIETATO scrivere nel file il proprio `full_file_sha256` finale come se fosse verificabile byte-identical**.

Motivazione: scrivere `SHA256 di questo file = X` all'interno del file stesso crea un
paradosso self-referential: dopo la scrittura di quella riga, il vero SHA del file cambia
(perché il contenuto ora include la stringa `X`). Il valore scritto `X` corrisponde quindi
solo a un fotogramma intermedio del file **prima** che quella riga fosse presente. Un
verificatore esterno che rilegge il file e ricomputa lo SHA otterrà un valore diverso da
`X`, con conseguente **falso negativo di integrity check**.

### 31.3 · Best practice canonica

- **NON** scrivere il proprio `full_file_sha256` finale come stringa embedded nel file
- **Preferire**: tracciare il SHA in un **closure manifest esterno** (file JSON separato) calcolato dopo la scrittura del file principale
- **Ammesso**: dichiarare uno `content_body_sha256` se necessario (con perimetro dichiarato esplicitamente)
- **Ammesso**: dichiarare il SHA di **altri file** (non se stesso) all'interno di un file
- **Ammesso**: dichiarare **pre-append SHA** di un file, purché non venga poi scritto anche il post-append SHA nello stesso file

### 31.4 · Retro-applicazione al PRD.md

- SHA `5049a978...5653e3` = **pre-append RV3-EV** (embedded valido, riferisce stato prima dell'append)
- SHA `b7e81beac6d...378baf9` = **embedded pre-footer hash** (historical internal ledger value); **NON** è il `full_file_sha256` reale del PRD post-append per il paradosso self-referential
- SHA **`b8a9f54fc964...bca47f`** = **`full_file_sha256` reale on-disk** del PRD post RV3-EV closure e **pre AFX1 append** (baseline canonico per questo gate)
- **NON correggere retroattivamente il PRD RV3-EV** (footer self-referential resta come storico; policy applicata solo per gate futuri)

### 31.5 · Applicazione a questo gate (AFX1)

- **PRD.md `full_file_sha256` post-AFX1-append** = **NON** scritto all'interno del PRD stesso
- Tale valore sarà tracciato **esclusivamente** in `r18_6_rv3_afx1_closure_manifest.json` (closure manifest esterno) + messaggio di output al PM
- **Closure Report MD / JSON**: NON contengono il proprio `full_file_sha256`; il loro SHA è tracciato nel manifest esterno

**La policy §31 è vincolante per tutti i gate futuri (IC1, AFX2, NC1, Gate 11, Registry v3, …).**

## 32. Final STOP

**AFX1 = CLOSED · PM-LOCKED · IMMUTABLE**

Governance locks finali:
- `apply_authorized = false`
- `item_creation_authorized = false`
- `affix_creation_authorized = false`
- `registry_v3_apply_authorized = false`
- `registry_v3_module_generation_authorized = false`
- `field_addition_authorized = false`
- `backfill_authorized = false`
- `affix_population_authorized = false`
- `openapi_change_authorized = false`
- `backend_change_authorized = false`
- `frontend_change_authorized = false`
- `db_write_count = 0`
- `sealed_integrity_intact = true (36/36 byte-identical)`
- `lore_meta_sha_invariant = true (a18f708b...965b8f)`
- `afx1_closed = true`
- `afx1_reopen_authorized = false`

**Prossimo gate proposto**: **IC1** (Item Coverage & Content Blueprint) — **HOLD, NON AUTHORIZED IN QUESTO DISPATCH**.

**Non autorizzato in questo dispatch**:
- IC1 kickoff · IC1 draft · IC1 pre-work
- NC1 kickoff · NC1 draft · NC1 pre-work
- Gate 11 kickoff · Registry v3 apply · item creation · affix creation
- Modifiche a PRD.md oltre l'append `### R18.6.RV3-AFX1 — AFFIX VOCABULARY & POOL CONTRACT · CLOSED`
- Modifiche a `r18_6_rv3_afx1_affix_vocabulary_pool_contract.md` / `.json` (PM-LOCKED)
- Reopen di RV3-EV / EV-F1 / EV-F2 (IMMUTABLE)

**Stato roadmap post AFX1 closure**:
- Cacciatore del Vuoto = ACTIVE-DESIGN-READY
- R18.3f = CLOSED
- RV3-EV = CLOSED
- **AFX1 = CLOSED** ← this dispatch
- IC1 = HOLD (proposed next gate)
- AFX2 = RESERVED FUTURE
- NC1 = HOLD
- Registry v3 item generation = NOT AUTHORIZED
- Registry v3 apply = NOT AUTHORIZED
- Gate 11 = HOLD
- Monaco / Wave 1 = HOLD

**Attendo nuovo verdict PM per apertura del prossimo gate.**
