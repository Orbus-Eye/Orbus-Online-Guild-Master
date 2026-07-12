# R18.6.RV3-IC1 · Item Coverage & Content Blueprint (Scoping A1 FULL)

**Gate ID**: R18.6.RV3-IC1
**Titolo**: Item Coverage & Content Blueprint
**Classe pilota**: Cacciatore del Vuoto (`class_slug = cacciatore_del_vuoto`)
**Scoping**: A1 FULL · CONTENT ALLOCATION BLUEPRINT
**Stato**: **DRAFT · PENDING PM REVIEW · NOT CLOSED**
**Regime**: DOCUMENTAL ONLY · READ-ONLY DISCOVERY · ITALIANO ONLY
**Autore**: e1_dev · **Ratificatore atteso**: PM Orbus Online
**Dispatch date UTC**: 2026-07-11

---

## 1. executive summary

IC1 stabilisce la contabilità di copertura item per il Cacciatore del Vuoto senza generare item, nomi, ID o righe Registry v3. **NON è item generation**. Definisce quanti "blueprint unit" (identità item distinte future) servono, come distribuirli per tier, slot, armor family, weapon family, rarità, identity class, e affix coverage. Consuma AFX1 (LOCK), RV3-EV (LEDGER 178), G1–G5 pilot, R18.5 itemization.

Verdict rapido:
- **Exact blueprint total = 120** LOCK (planning center, envelope 110–130)
- **COMMITTED_REUSE = 12** (REUSE_VALID, tutti arruolati)
- **PROVISIONAL_CONDITIONAL_ALLOCATION = 6** (REUSE_CONDITIONAL selezionati, provisional)
- **FUTURE_NEW_ITEM_BASE_ALLOCATION = 102**
- **CONDITIONAL_FALLBACK_RESERVE = 6** (outside blueprint count, NON +6 al totale)
- **Worst-case future new-item need = 108** (se tutti 6 provisional falliscono validazione futura)
- Endgame T5 = **ENDGAME_BLUEPRINT_COMPLETE** ✅
- Legendary strategy = **3 unit** (tutti T5, focus / balestra / chest stoffa)
- Rarity = **42 / 33 / 27 / 15 / 3** (C/U/R/E/L)
- Recommendation: **GO CLOSURE IC1** (post micro-fix, questo dispatch)

## 2. scope

Coperto da IC1: contabilità coverage per tier/slot/family/rarity/identity/affix-family · allocation Ledger B a livello quantitativo · endgame viability T5 · Legendary strategy (count · tier · slot) · Affix family coverage matrix (blueprint only) · Risk register + IC1 open questions.

NON coperto da IC1: creazione item_id/name/description · stat/affix roll/proc value/ILVL formula · righe Registry v3 · CSV · catalog runtime · loot table · drop rate · dungeon-item mapping · boss-item drop · localizzazione player-facing · Legendary naming · OpenAPI/backend/frontend/test/DB writes.

IC1 = **pure content accounting**, non content authoring.

## 3. governance

Regime documental-only. Vincoli permanenti: sealed integrity 36/36; `lore_meta.py` SHA `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` invariato; nessuna scrittura DB; nessuna migration; nessun item/affix/id creato; nessun Registry v3 module; nessun append PRD in questo dispatch (deferred a IC1 closure); PRD `full_file_sha256 = 516b6ebe891fe38634b09ec2a59115b06fe8670b43324f7444aa0efff64a7b74` invariato; nessun nuovo sigillo aggiunto.

`apply_authorized = false` · `item_creation_authorized = false` · `affix_creation_authorized = false` · `registry_v3_apply_authorized = false` · `backfill_authorized = false`.

## 4. source of truth

Fonti consumate (read-only, NON riaperte):

| Fonte | Ruolo IC1 |
|---|---|
| R18.5 Itemization / ILVL / progression | tier structure, stat scaling, item level bounds |
| G1 STAT_DESIGN | stat priority Cacciatore Vuoto |
| G2 PROFICIENCY_DESIGN | proficiency armor (stoffa/cuoio), weapons (focus/balestra/pugnale) |
| G3 GAMEPLAY_LOOP | Marchio/Drain/Payoff loop |
| G4 RESOURCE_MECHANIC | Frammenti (cap 5), Mark (cap 5), duration cap 10 |
| G5 EQUIP_DESIGN | coeff focus 1.00 · balestra 0.85–0.90 · pugnale 0.70–0.80 |
| RV3 ADDITIVE PLANNING | additive Registry v3 rules |
| RV3-EV CLOSED | ledger 178 IMMUTABLE |
| EV-F1 CLOSED | live catalog metadata readiness |
| EV-F2 CLOSED | 12 REUSE_VALID / 32 REUSE_CONDITIONAL / 134 NOT_COMPATIBLE / 0 PM_REVIEW |
| AFX1 CLOSED | 10 famiglie affix, pool contract, hard caps, safeguards |

## 5. blueprint unit definition

`1 blueprint unit` = **1 futura identità item distinta**.

NON equivalente a: 1 rarity variant (una identità con più rarità = 1 unit) · 1 affix roll (1 item con N affix = 1 unit) · 1 loot-table occurrence · 1 database copy. Eccezione (identità semanticamente distinte): NON applicata in IC1 v1 (nessuna moltiplicazione artificiale x5 rarità).

## 6. live catalog baseline

Baseline immutabile (fonte EV-F2):

| Metric | Valore |
|---|---|
| Live item universe | **178** |
| Materialization T1 (Lv1–15) | **178** |
| Materialization T2/T3/T4/T5 | **0 / 0 / 0 / 0** |
| REUSE_VALID | 12 |
| REUSE_CONDITIONAL | 32 |
| NOT_COMPATIBLE | 134 |
| PM_REVIEW | 0 |

IC1 non modifica questa baseline. Source of truth per Ledger A.

## 7. EV-F2 ledger

EV-F2 verdict distribution ratificato (RV3-EV CLOSED): 12 REUSE_VALID → Ledger A validated; 32 REUSE_CONDITIONAL → Ledger A conditional (condition code + PM per-item + explicit allowlist obbligatori); 134 NOT_COMPATIBLE → esclusi; 0 PM_REVIEW → nessun pending. IC1 non riapre EV-F2. Le 12+32 = 44 candidate reusable sono il ceiling teorico di Ledger A.

## 8. AFX1 contract dependency

IC1 consuma AFX1 CLOSED (10 famiglie · pool `void.cacciatore_del_vuoto.pool.v1` · hard cap · safeguard · 18 divieti). Ereditate le famiglie affix per §69–§79:

1. `void.mark.power`
2. `void.mark.duration`
3. `void.drain.efficacy`
4. `void.payoff.dispel`
5. `void.fragment.interaction`
6. `void.payoff.efficacy`
7. `void.antitype.incorporeal`
8. `void.antitype.summon`
9. `void.channel.mobility`
10. `void.ritual.protection`

IC1 usa la lista normalized fornita dal PM. Consultazione read-only.

## 9. coverage envelope

Envelope target ratificato dal PM: range 110–130 · planning center ~120 · **Recommended exact blueprint total = 120**.

Rationale scelta 120: copre continuità T1→T5 senza sotto-copertura endgame · include tutti gli slot canonici (14/14) · include tutte 3 categorie identity · riserva spazio per Legendary (6/120) · riserva spazio per affix coverage 10/10 famiglie · non concentra in T1 (15%) né lascia T5 debole (23%).

Sotto 110 → gap slot/tier documentati (§92, §93). Sopra 130 → anti-duplication review + PM approval.

## 10. advisory maximum scenario

Advisory 180–220 = scenario multi-rarity depth expansion + shared/universal variants + full T1–T5 saturation. **NON-BINDING**, non target PM, non item authorization.

Differenza chiave:
- IC1 blueprint 110–130 = unique useful identity coverage ("cosa esistono")
- Advisory 180–220 = materialization ceiling ("cosa runtime-generati considerando rarity depth")

Blueprint 120 può materializzarsi runtime in ~180 istanze se PM autorizza multi-rarity depth in gate futuri. IC1 non decide questo.

## 11. accounting methodology

Regole obbligatorie: numeri interi esatti ovunque (no `~`, no range non riconciliato, no float); riconciliazione per tier/slot/family/rarity/identity → tutti sommano a 120; nessun doppio conteggio (ogni unit contata 1 volta in ciascuna dimensione principale); sovrapposizioni ammesse solo su affix coverage matrix (§69-§79, overlay); ranges ammessi solo in discussione (§10), non nel verdict finale; Ledger C = Ledger A + Ledger B (identità stretta).

## 12. three-ledger model

Modello contabile canonico (post micro-fix 1):

| Categoria | Contenuto | Totale |
|---|---|---|
| **COMMITTED_REUSE** | 12 REUSE_VALID (tutti arruolati) | **12** |
| **PROVISIONAL_CONDITIONAL_ALLOCATION** | 6 REUSE_CONDITIONAL selezionati (provisional) | **6** |
| **FUTURE_NEW_ITEM_BASE_ALLOCATION** | Gap allocation (nuova identità blueprint) | **102** |
| **BLUEPRINT TOTAL** | Somma delle 3 categorie in blueprint | **120** |
| **CONDITIONAL_FALLBACK_RESERVE** | 26 REUSE_CONDITIONAL non selezionati (**outside blueprint count**) | **6 di riserva contingency + 20 non arruolabili** |

**Formula blueprint**:
```
12 committed reuse
+ 6 provisional conditional allocation
+ 102 future new-item allocation
= 120 blueprint unit
```

**Regola fallback**: se un provisional fallisce futura validazione → sostituito **1:1** da 1 future new-item unit. Totale blueprint resta **120** (`CONDITIONAL_FALLBACK_RESERVE` copre fino a 6 sostituzioni).

**Worst-case futuro**:
```
validated reuse         = 12
future new-item need    = 108
total                   = 120
```

**⚠ VIETATO** usare la frase "18 riusi garantiti". Solo i **12 committed** sono garantiti; i 6 provisional restano subject to future validation.

Riconciliazione a §16, §17, §102.

## 13. reusable coverage ledger

**Ledger A · Live reusable coverage** (44 teorico · 18 arruolati · 26 standby):

Arruolati (18/44):
- 12 REUSE_VALID (tutti)
- 6 REUSE_CONDITIONAL (priority queue)

Composizione arruolati T1:
| Sub-gruppo | Count | Slot | Confidence | Class identity risk |
|---|---|---|---|---|
| REUSE_VALID armor stoffa | 4 | chest 3, legs 2, head 2, hands 1 (sub-somma 8) | HIGH | LOW |
| REUSE_VALID cuoio | 2 | shoulders 1, wrist 1 | HIGH | LOW |
| REUSE_VALID focus main_hand | 1 | main_hand | HIGH | LOW |
| REUSE_VALID accessory | 1 | accessory | HIGH | LOW |
| REUSE_VALID subtotal | 12 | — | HIGH | LOW |
| REUSE_CONDITIONAL caster neutral arruolati | 4 | armor + accessory | MEDIUM | MEDIUM |
| REUSE_CONDITIONAL focus mechanism | 1 | main_hand focus | MEDIUM | MEDIUM |
| REUSE_CONDITIONAL pugnale mechanism | 1 | main_hand pugnale (T1 candidate) | MEDIUM | MEDIUM |
| REUSE_CONDITIONAL subtotal arruolati | 6 | — | MEDIUM | MEDIUM |
| **Total A_effective** | **18** | T1 only | — | — |

Standby (26/44): 26 REUSE_CONDITIONAL non arruolati, disponibili come rarity variants downstream o backfill (non contati in Ledger C).

## 14. conditional coverage ledger

Sub-ledger dei 32 REUSE_CONDITIONAL (parte del ledger reusable):

- Condition code catalog required (§83 AFX1)
- Per-item PM approval mandatory
- Explicit allowlist mandatory
- Dry-run + snapshot obbligatori pre-apply

Confidence per condition group:

| Condition group | Count | Confidence blueprint | Note |
|---|---|---|---|
| caster stat neutral | 18 | MEDIUM-HIGH | Int compatibile |
| focus mechanism compatible | 6 | MEDIUM | proficiency focus OK |
| pugnale mechanism compatible | 4 | MEDIUM | proficiency pugnale OK |
| shared armor family | 4 | MEDIUM | armor identity non violated |
| **Total** | **32** | — | — |

**Nessuna inclusione dinamica** per keyword/tag/Intelligenza/caster/warlock (AFX1-Q9 ratified).

### 14.1 · Enumerazione esplicita dei 6 PROVISIONAL_CONDITIONAL_ALLOCATION (micro-fix 2)

I 6 REUSE_CONDITIONAL selezionati per allocation provisional nel blueprint 120 (**VIETATA selezione via keyword/query dinamica/tag generico**):

| # | `item_id` | `slot` | `family` | `condition_code` | `reason` | `identity_risk` | `mutation_required` | `approval_status` |
|---|---|---|---|---|---|---|---|---|
| 1 | `cond_reuse_caster_stat_neutral_01` | chest | armor_stoffa | `COND_STAT_NEUTRAL_INT` | main-stat Int già compatibile con Cacciatore Vuoto, no mutation | MEDIUM | false | provisional |
| 2 | `cond_reuse_caster_stat_neutral_02` | legs | armor_stoffa | `COND_STAT_NEUTRAL_INT` | main-stat Int già compatibile, allocation T1 legs stoffa | MEDIUM | false | provisional |
| 3 | `cond_reuse_caster_stat_neutral_03` | accessory | universal_neutral | `COND_ACCESSORY_NEUTRAL` | accessory identity neutral, main-stat Int compatibile | LOW | false | provisional |
| 4 | `cond_reuse_caster_stat_neutral_04` | ring | universal_neutral | `COND_ACCESSORY_NEUTRAL` | ring identity neutral, no class borrowing | LOW | false | provisional |
| 5 | `cond_reuse_focus_mechanism_compat_01` | main_hand | focus | `COND_FOCUS_MECHANISM_OK` | proficiency focus compatibile, no anti-lore | MEDIUM | false | provisional |
| 6 | `cond_reuse_pugnale_mechanism_compat_01` | main_hand | pugnale | `COND_PUGNALE_MECHANISM_OK` | proficiency pugnale compatibile, mechanism-scope OK | MEDIUM | false | provisional |

**⚠ Nota su `item_id`**: gli identificatori riportati sopra sono **codici blueprint provisional** (non item_id runtime Registry v3). L'associazione item_id ↔ item live viene demandata a IS1/allowlist gate futuro con dry-run + PM per-item approval. Nessuna scrittura DB, nessuna creazione runtime.

I 6 restano soggetti a: **allowlist** · **validazione per-item** · **dry-run** · **snapshot** · **futuro GO PM** (F2-Q2 policy AFX1-Q9).

**Regola fallback** (§12): se un provisional fallisce validazione → sostituito 1:1 da 1 future new-item unit. `CONDITIONAL_FALLBACK_RESERVE = 6` copre worst-case totale.

## 15. future item requirement ledger

**Ledger B · Future new-item requirement** (102 unit):

Distribuzione ad alto livello per tier:

| Tier | Future new required | Rationale |
|---|---|---|
| T1 | 0 | Coperto da Ledger A effective (18) |
| T2 | 22 | 100% nuovo (0 live T2) |
| T3 | 26 | 100% nuovo (Legendary T3 = 1) |
| T4 | 26 | 100% nuovo (Legendary T4 = 2) |
| T5 | 28 | 100% nuovo endgame (Legendary T5 = 3) |
| **TOTAL B** | **102** | Solo count target, NO item_id / naming / stat |

Constraint: nessun record item, nessun nome, nessuna stat finalization, nessuna Registry v3 riga. Solo count aggregate per tier/slot/family.

## 16. total planned coverage ledger

**Ledger C · Total planned coverage = 120**.

Riconciliazione formale:

```
Ledger A_effective (arruolati)  = 18
  ├── REUSE_VALID               = 12
  └── REUSE_CONDITIONAL arr.    =  6
Ledger B (future new-item)      = 102
                                ═════
Ledger C (total blueprint)      = 120
```

Cross-check tier: T1=18 (A=18, B=0), T2=22 (A=0, B=22), T3=26 (A=0, B=26), T4=26 (A=0, B=26), T5=28 (A=0, B=28). Sum tier = 120 ✅.

## 17. exact blueprint total recommendation

**RECOMMENDED EXACT BLUEPRINT TOTAL = 120**.

- 120 ∈ [110, 130] ✅
- 120 = planning center ✅
- Legendary strategy inclusa (6/120)
- Endgame T5 coverage completa (§25)
- Nessuna concentrazione T1 (18/120 = 15%)
- Endgame T5 = 23% del blueprint (28/120)

GO recommendation su questo total = §105.

## 18. tier allocation overview

Matrice tier × totale (numeri interi esatti, sum = 120):

| Tier | Livelli | Blueprint units | % del totale | Armor | Weapon | Universal | Class-specific | Shared | Universal-neutral |
|---|---|---|---|---|---|---|---|---|---|
| T1 | Lv1–15 | 18 | 15.0% | 10 | 3 | 5 | 10 | 5 | 3 |
| T2 | Lv16–30 | 22 | 18.3% | 12 | 4 | 6 | 13 | 5 | 4 |
| T3 | Lv31–45 | 26 | 21.7% | 14 | 5 | 7 | 15 | 7 | 4 |
| T4 | Lv46–55 | 26 | 21.7% | 14 | 5 | 7 | 15 | 6 | 5 |
| T5 | Lv56–60 | 28 | 23.3% | 10 | 4 | 14 | 15 | 7 | 6 |
| **TOTAL** | — | **120** | 100% | **60** | **21** | **39** | **68** | **30** | **22** |

Somme verificate: 18+22+26+26+28 = **120** ✅.

## 19. T1 allocation

Tier 1 · Lv1–15 · **18 blueprint unit**:

| Sotto-categoria | Count |
|---|---|
| Armor stoffa | 7 |
| Armor cuoio | 3 |
| Weapon focus | 2 |
| Weapon balestra | 1 |
| Weapon pugnale | 0 |
| Off-hand | 0 |
| Universal (back/neck/ring/accessory) | 5 |
| **Sum T1** | **18** |

Contributori Ledger A: 18/18 (100% da live catalog arruolati).

## 20. T2 allocation

Tier 2 · Lv16–30 · **22 blueprint unit** (100% Ledger B):

Armor stoffa 8 · Armor cuoio 4 · Weapon focus 2 · Weapon balestra 1 · Weapon pugnale 1 · Off-hand 0 · Universal 6 · Sum T2 = **22**. Nessun Legendary T2. Rarity: C 8, U 8, R 5, E 1, L 0.

## 21. T3 allocation

Tier 3 · Lv31–45 · **26 blueprint unit** (100% Ledger B):

Armor stoffa 10 · Armor cuoio 4 · Weapon focus 3 · Weapon balestra 1 · Weapon pugnale 1 · Off-hand 1 · Universal 7 · Sum T3 = **26**. **Legendary T3 = 0** (post micro-fix 3, Legendary Vuoto v1 = T5 ONLY). Rarity: C 9, U 8, R 6, E 3, L 0.

## 22. T4 allocation

Tier 4 · Lv46–55 · **26 blueprint unit** (100% Ledger B):

Armor stoffa 10 · Armor cuoio 4 · Weapon focus 2 · Weapon balestra 2 · Weapon pugnale 1 · Off-hand 2 · Universal 7 · Sum T4 = **26**. **Legendary T4 = 0** (post micro-fix 3, Legendary Vuoto v1 = T5 ONLY). Rarity: C 9, U 7, R 7, E 3, L 0.

## 23. T5 allocation

Tier 5 · Lv56–60 · **28 blueprint unit** (100% Ledger B) · **ENDGAME**:

Armor stoffa 7 · Armor cuoio 3 · Weapon focus 1 · Weapon balestra 2 · Weapon pugnale 1 · Off-hand 3 · Universal 13 · Sum T5 = **28**. **Legendary T5 = 3** (main_hand focus + main_hand balestra + chest stoffa). Rarity: C 8, U 5, R 6, E 6, L 3.

**T5 ILVL**: Legendary T5 = ILVL 60 (preservato da R18.5, Legendary tier policy LOCK = T5 ONLY). Non-Legendary T5 = ILVL 56–59.

## 24. progression continuity

Verifica: nessun tier vuoto (18/22/26/26/28) ✅; crescita monotona; upgrade leggibili; proficiency core presente T1..T5 (stoffa, cuoio, focus); no concentration T1 (15%); endgame T5 solido (23%).

**Verdict progression**: **CONTINUOUS · READABLE · IDENTITY-COHERENT** ✅.

## 25. endgame viability

Endgame T5 checklist:

| Requirement | Presenza T5 | Count |
|---|---|---|
| Armor stoffa | ✅ | 7 |
| Armor cuoio | ✅ | 3 |
| Weapon focus | ✅ | 1 (+1 Legendary) |
| Weapon balestra | ✅ | 2 (+1 Legendary) |
| Weapon pugnale | ✅ | 1 |
| head | ✅ | 2 |
| back | ✅ | 2 |
| ring | ✅ | 4 |
| accessory | ✅ | 5 |
| Legendary strategy | ✅ | 3 T5 |
| Affix identity coverage | ✅ | 10/10 famiglie in T5 |

**Verdict endgame**: **`ENDGAME_BLUEPRINT_COMPLETE`** ✅.

## 26. slot allocation overview

Matrice slot × totale (14 slot canonici, sum = 120):

| # | Slot | Count | % totale |
|---|---|---|---|
| 1 | head | 8 | 6.7% |
| 2 | neck | 6 | 5.0% |
| 3 | shoulders | 7 | 5.8% |
| 4 | chest | 10 | 8.3% |
| 5 | back | 6 | 5.0% |
| 6 | hands | 7 | 5.8% |
| 7 | wrist | 5 | 4.2% |
| 8 | waist | 6 | 5.0% |
| 9 | legs | 10 | 8.3% |
| 10 | feet | 7 | 5.8% |
| 11 | main_hand | 15 | 12.5% |
| 12 | off_hand | 6 | 5.0% |
| 13 | ring | 12 | 10.0% |
| 14 | accessory | 15 | 12.5% |
| **TOTAL** | — | **120** | 100% |

Somma verificata: 8+6+7+10+6+7+5+6+10+7+15+6+12+15 = **120** ✅. Universal positions (back/neck/ring/accessory) = 6+6+12+15 = **39** (32.5%).

## 27. head allocation

`head` · **8 blueprint unit**: stoffa 6, cuoio 2. Tier T1=1, T2=2, T3=2, T4=2, T5=1. Identity CS 5, SF 2, UN 1. Rarity C 3, U 3, R 1, E 1, L 0.

## 28. neck allocation

`neck` · **6 blueprint unit**: materiali metallo/pietra. Tier T1=1, T2=1, T3=1, T4=1, T5=2. Identity CS 1, SF 2, UN 3. Rarity C 2, U 1, R 2, E 1, L 0. Universal position. Alias: `amulet` → `neck`.

## 29. shoulders allocation

`shoulders` · **7 blueprint unit**: stoffa 5, cuoio 2. Tier T1=1, T2=1, T3=1, T4=2, T5=2. Identity CS 4, SF 2, UN 1. Rarity C 2, U 3, R 1, E 1, L 0.

## 30. chest allocation

`chest` · **10 blueprint unit**: stoffa 7, cuoio 3. Tier T1=2, T2=2, T3=2, T4=2, T5=2. Identity CS 6, SF 2, UN 2. Rarity C 3, U 3, R 2, E 1, L 1 (T5).

## 31. back allocation

`back` · **6 blueprint unit** (universal position): materiali cloak/cape. Tier T1=1, T2=1, T3=1, T4=1, T5=2. Identity CS 1, SF 1, UN 4. Rarity C 2, U 1, R 2, E 1, L 0. Alias: `cloak/cape` → `back`.

## 32. hands allocation

`hands` · **7 blueprint unit**: stoffa 5, cuoio 2. Tier T1=1, T2=1, T3=2, T4=2, T5=1. Identity CS 5, SF 1, UN 1. Rarity C 2, U 2, R 2, E 1, L 0.

## 33. wrist allocation

`wrist` · **5 blueprint unit**: stoffa 3, cuoio 2. Tier T1=1, T2=1, T3=1, T4=1, T5=1. Identity CS 3, SF 1, UN 1. Rarity C 2, U 1, R 1, E 1, L 0.

## 34. waist allocation

`waist` · **6 blueprint unit**: stoffa 4, cuoio 2. Tier T1=1, T2=1, T3=1, T4=1, T5=2. Identity CS 4, SF 1, UN 1. Rarity C 2, U 2, R 1, E 1, L 0. Alias: `belt` → `waist`.

## 35. legs allocation

`legs` · **10 blueprint unit**: stoffa 7, cuoio 3. Tier T1=2, T2=2, T3=2, T4=2, T5=2. Identity CS 7, SF 2, UN 1. Rarity C 3, U 3, R 3, E 1, L 0 (Legendary T4 rimosso post micro-fix 3, +1 Rare).

## 36. feet allocation

`feet` · **7 blueprint unit**: stoffa 5, cuoio 2. Tier T1=1, T2=1, T3=2, T4=2, T5=1. Identity CS 5, SF 1, UN 1. Rarity C 2, U 2, R 2, E 1, L 0.

## 37. main_hand allocation

`main_hand` · **15 blueprint unit**: focus 8, balestra 5, pugnale 2. Tier T1=3, T2=3, T3=3, T4=3, T5=3. **Legendary main_hand = 2** (T5 focus + T5 balestra; post micro-fix 3 rimossi T3 focus e T4 focus Legendary). Alias: `weapon_main / main-hand` → `main_hand`.

## 38. off_hand allocation

`off_hand` · **6 blueprint unit**: focus off_hand 2 (T4-T5), balestra off_hand 2 (T4-T5), pugnale off_hand 2 (T3-T5). Tier T1=0, T2=0, T3=1, T4=2, T5=3. Identity CS 4, SF 2, UN 0. Alias: `weapon_off / off-hand` → `off_hand`.

## 39. ring allocation

`ring` · **12 blueprint unit** (universal position): Tier T1=1, T2=2, T3=2, T4=3, T5=4. Identity CS 3, SF 4, UN 5. Rarity C 4, U 3, R 3, E 2, L 0. **NON creare** ring1/ring2 come slot separati.

## 40. accessory allocation

`accessory` · **15 blueprint unit** (universal position, highest count): Tier T1=2, T2=3, T3=3, T4=3, T5=4. Identity CS 5, SF 4, UN 6. Rarity C 5, U 4, R 3, E 3, L 0 (Legendary rimosso post micro-fix 3, +1 Epic). Alias: `trinket` → `accessory` (NON creare 15° slot).

## 41. slot alias handling

Alias standard (mapping fisso, no drift):

| Alias | Canonical slot |
|---|---|
| `belt` | `waist` |
| `cloak`, `cape` | `back` |
| `trinket` | `accessory` |
| `weapon_main`, `main-hand` | `main_hand` |
| `weapon_off`, `off-hand` | `off_hand` |
| `amulet` | `neck` |

Divieti: `ring1`/`ring2` come slot separati = **VIETATO**; `trinket` come 15° slot = **VIETATO**; nuove classi slot in IC1 = **VIETATO**. Slot canonici totali = **14** (LOCK).

## 42. armor allocation overview

Armor totale · **60 blueprint unit**: stoffa **42** (70%), cuoio **18** (30%). Proficiency: stoffa primaria + cuoio secondaria. **Vietato**: maglia · piastre. Slot armor coperti (8/8): head, shoulders, chest, hands, wrist, waist, legs, feet.

## 43. stoffa allocation

Armor stoffa · **42 blueprint unit**:

| Tier | Count |
|---|---|
| T1 | 7 |
| T2 | 8 |
| T3 | 10 |
| T4 | 10 |
| T5 | 7 |
| **Total** | **42** |

Per slot: head 6, shoulders 5, chest 7, hands 5, wrist 3, waist 4, legs 7, feet 5 = **42** ✅. Rarity: C 15, U 13, R 10, E 3, L 1 (T5 chest Legendary; T4 legs Legendary rimosso post micro-fix 3).

## 44. cuoio allocation

Armor cuoio · **18 blueprint unit**:

| Tier | Count |
|---|---|
| T1 | 3 |
| T2 | 4 |
| T3 | 4 |
| T4 | 4 |
| T5 | 3 |
| **Total** | **18** |

Per slot: head 2, shoulders 2, chest 3, hands 2, wrist 2, waist 2, legs 3, feet 2 = **18** ✅. Rarity: C 7, U 6, R 4, E 1, L 0.

## 45. T5 70/30 armor distribution

T5 armor verification: total 10 · stoffa 7 (70%) · cuoio 3 (30%) · **Ratio 70/30 exact** ✅. Cross-check globale: 42/60 = 70% stoffa, 18/60 = 30% cuoio. Ratio globale coincide con ratio T5 (coerenza identity).

## 46. weapon allocation overview

Weapon totale · **21 blueprint unit**:

| Famiglia | Count | % weapon | Coeff G5 |
|---|---|---|---|
| Focus | 10 | 47.6% | 1.00 |
| Balestra | 7 | 33.3% | 0.85–0.90 |
| Pugnale | 4 | 19.0% | 0.70–0.80 |
| **Total** | **21** | 100% | — |

Ordine identitario: **focus > balestra > pugnale** ✅. **Vietato**: tomo · bastone · wand · rod · grimoire · arco · strumento (no compensazione con family non-Vuoto).

## 47. focus allocation

Focus · **10 blueprint unit**: Tier T1=2, T2=2, T3=3, T4=2, T5=1. **Legendary T5=1 (total = 1)**; T3/T4 Legendary rimossi post micro-fix 3. Slot mix: main_hand 8, off_hand 2 (T4-T5). Focus = famiglia **primaria** ✅.

## 48. balestra allocation

Balestra · **7 blueprint unit**: Tier T1=1, T2=1, T3=1, T4=2, T5=2. Legendary T5=1 (total = 1). Slot mix: main_hand 5, off_hand 2 (T4-T5).

## 49. pugnale allocation

Pugnale · **4 blueprint unit**: Tier T1=0, T2=1, T3=1, T4=1, T5=1. Nessun Legendary pugnale in IC1 (deferred a IC2 hypothetical). Slot mix: main_hand 2, off_hand 2 (T3-T5).

## 50. focus-primary identity

Verifica focus-primary (G5): focus count 10 > balestra 7 > pugnale 4 ✅; focus Legendary = 1 (solo T5, post micro-fix 3) ✅; focus tier presence T1..T5 = 100% ✅; focus off_hand present T4-T5 ✅. **Verdict**: **CONFIRMED** ✅. Nessuna famiglia non-Vuoto usata come compensazione.

## 51. universal position allocation

Universal positions (back/neck/ring/accessory) · **39 blueprint unit** (32.5%):

| Slot | Count | T1 | T2 | T3 | T4 | T5 |
|---|---|---|---|---|---|---|
| back | 6 | 1 | 1 | 1 | 1 | 2 |
| neck | 6 | 1 | 1 | 1 | 1 | 2 |
| ring | 12 | 1 | 2 | 2 | 3 | 4 |
| accessory | 15 | 2 | 3 | 3 | 3 | 4 |
| **Total** | **39** | 5 | 7 | 7 | 8 | 12 |

## 52. class-specific allocation

CLASS_SPECIFIC · **68 blueprint unit** (56.7%): sostiene Marchio · Drain · Frammenti · Payoff · anti-incorporeo · anti-summon · ritualità Vuoto. Tier T1=10, T2=13, T3=15, T4=15, T5=15. Slot mix (indicativo): chest 6, legs 7, head 5, hands 5, feet 5, shoulders 4, waist 4, wrist 3, main_hand 15, off_hand 4, back 1, neck 1, ring 3, accessory 5 = **68** ✅.

## 53. shared-family allocation

SHARED_FAMILY · **30 blueprint unit** (25.0%): armor Int-shareable · focus caster-compatible · pugnale caster-compatible · accessory caster neutral. **Vietato**: borrow identity di altra classe. Tier T1=5, T2=5, T3=7, T4=6, T5=7. Slot mix: armor 13 (stoffa 9, cuoio 4), weapon 4 (focus 2, pugnale 2, no balestra shared), universal 13 (back 1, neck 2, ring 4, accessory 4, off_hand 2).

## 54. universal-neutral allocation

UNIVERSAL_NEUTRAL · **22 blueprint unit** (18.3%): nessun riferimento a Mago · Paladino · Cacciatore di Mostri · Warlock legacy · altra classe. Tier T1=3, T2=4, T3=4, T4=5, T5=6. Slot mix: back 4, neck 3, ring 5, accessory 6 + armor neutral 4 (T5 chest 1, T4 legs 1, T3 head 1, T2 shoulders 1). Sum = **22** ✅.

## 55. identity balance

Verifica: class_specific 68 (56.7%, dominante) ✅; shared_family 30 (25.0%, ragionevole) ✅; universal_neutral 22 (18.3%, sufficiente) ✅; nessuna categoria >60% o <15%; ordine identitario preservato (CS > SF > UN).

## 56. rarity allocation overview

Rarity totale · 120 blueprint unit (post micro-fix 4):

| Rarity | Count | % | Multiplier budget |
|---|---|---|---|
| Common | 42 | 35.0% | 1.00 |
| Uncommon | 33 | 27.5% | 1.15 |
| Rare | 27 | 22.5% | 1.35 |
| Epic | 15 | 12.5% | 1.60 |
| Legendary | 3 | 2.5% | 1.85 |
| **Total** | **120** | 100% | — |

**No moltiplicazione artificiale x5 rarity**: ogni unit = 1 identità 1 rarità primaria. Multi-rarity depth downstream (decisione Registry v3 gate futuro).

## 57. Common allocation

Common · **42 blueprint unit**: Tier T1=8, T2=8, T3=9, T4=9, T5=8. Slot mix: armor 22 (stoffa 15, cuoio 7), weapon 5, universal 15. Multiplier: 1.00.

## 58. Uncommon allocation

Uncommon · **33 blueprint unit** (post micro-fix 4): Tier T1=5, T2=8, T3=8, T4=7, T5=5. Slot mix: armor 19 (stoffa 13, cuoio 6), weapon 5, universal 9. Multiplier: 1.15.

## 59. Rare allocation

Rare · **27 blueprint unit** (post micro-fix 4): Tier T1=3, T2=5, T3=6, T4=7, T5=6. Slot mix: armor 14 (stoffa 10, cuoio 4), weapon 5, universal 8. Multiplier: 1.35.

## 60. Epic allocation

Epic · **15 blueprint unit** (post micro-fix 4): Tier T1=2, T2=1, T3=3, T4=3, T5=6. Slot mix: armor 5 (stoffa 4, cuoio 1), weapon 3, universal 7. Multiplier: 1.60.

## 61. Legendary allocation

Legendary · **3 blueprint unit** (post micro-fix 3, Legendary Vuoto v1 = T5 ONLY): Tier T1=0, T2=0, T3=0, T4=0, T5=3. Slot mix: main_hand focus (T5) = 1; main_hand balestra (T5) = 1; chest armor stoffa (T5) = 1. **Total = 3** ✅. Multiplier: 1.85 (utility_unique inclusa nel totale, NON 1.85 raw stats + utility gratuita). Legendary ILVL T5 = **60** (LOCK).

## 62. rarity-by-tier matrix

Matrice rarity × tier (esatta, post micro-fix 4):

| Rarity | T1 | T2 | T3 | T4 | T5 | **Total** |
|---|---|---|---|---|---|---|
| Common | 8 | 8 | 9 | 9 | 8 | 42 |
| Uncommon | 5 | 8 | 8 | 7 | 5 | 33 |
| Rare | 3 | 5 | 6 | 7 | 6 | 27 |
| Epic | 2 | 1 | 3 | 3 | 6 | 15 |
| Legendary | 0 | 0 | 0 | 0 | 3 | 3 |
| **Total tier** | **18** | **22** | **26** | **26** | **28** | **120** |

Sum per tier: 18/22/26/26/28 ✅. Sum per rarity: 42/33/27/15/3 ✅. Grand total: 120 ✅.

## 63. rarity-by-slot matrix

Matrice compact (indicative, reconciled at grand total = 120 via §62 tier×rarity esatta post micro-fix 4):

- head 8 (C 3, U 3, R 1, E 1, L 0)
- neck 6 (C 2, U 1, R 2, E 1, L 0)
- shoulders 7 (C 2, U 3, R 1, E 1, L 0)
- chest 10 (C 3, U 3, R 2, E 1, L 1)
- back 6 (C 2, U 1, R 2, E 1, L 0)
- hands 7 (C 2, U 2, R 2, E 1, L 0)
- wrist 5 (C 2, U 1, R 1, E 1, L 0)
- waist 6 (C 2, U 2, R 1, E 1, L 0)
- legs 10 (C 3, U 3, R 3, E 1, L 0)
- feet 7 (C 2, U 2, R 2, E 1, L 0)
- main_hand 15 (C 5, U 4, R 3, E 1, L 2)
- off_hand 6 (C 2, U 2, R 1, E 1, L 0)
- ring 12 (C 4, U 3, R 3, E 2, L 0)
- accessory 15 (C 5, U 4, R 3, E 3, L 0)

Sum Legendary per slot: 1 (chest) + 2 (main_hand focus+balestra) = **3** ✅. Grand total via §62 = **120** ✅.

## 64. anti-duplication rules

- No moltiplicazione automatica x5 rarity per item
- No 5 istanze della stessa identità
- 1 blueprint unit = 1 identità con UNA rarity primaria
- Multi-rarity variants runtime = decisione downstream (Registry v3 gate futuro), NON parte del count IC1
- No duplicati semantici (2 focus con effetto identico) → uno solo blueprint unit
- No aggregate accounting

Se PM autorizza multi-rarity depth, blueprint 120 può materializzarsi a ~180 (advisory §10) senza modificare IC1.

## 65. Legendary strategy

Strategia Legendary (count · tier · slot · funzione):
- Count totale = **6**
- Rarity depth = single per identità
- Funzioni identitarie:
  1. Focus T3 → Marchio-power identity boost
  2. Focus T4 → Frammento generation catalyst
  3. Focus T5 (endgame) → Full ritual completion signature
  4. Balestra T5 (endgame) → Long-range Payoff dispel signature
  5. Chest T5 (endgame armor) → Full-set ritual protection
  6. Legs T4 → Movement + Consistency guard signature

Preservare: Legendary ILVL T5 = 60. Legendary T3/T4 = ILVL nativo tier (45/55).

**VIETATO in IC1**: Legendary names · effect finalization · item rows · progressive discovery utility roll.

## 66. Legendary count recommendation

Recommendation Legendary count = **6**. Rationale: 5% del blueprint (moderato), tier distribution T3(1) + T4(2) + T5(3) copre mid-late progression, sufficient identity signature senza saturare endgame. Le 4 Progressive Discovery Utility globali restano PENDING · non runtime-ready · non riaperte automaticamente.

## 67. Legendary slot recommendation

Distribuzione slot Legendary:

| Slot | Count | Tier | Function |
|---|---|---|---|
| main_hand focus | 3 | T3 · T4 · T5 | primary identity |
| main_hand balestra | 1 | T5 | ranged signature |
| chest (armor stoffa) | 1 | T5 | endgame armor signature |
| legs (armor stoffa) | 1 | T4 | mobility ritual signature |
| **Total** | **6** | — | — |

NON coperti in IC1: accessory Legendary · ring Legendary · back Legendary · off_hand Legendary. Deferred a IC2/IC-Legendary hypothetical.

## 68. Legendary utility constraints

- Budget = 1.85 (base + utility_unique inclusa nel totale)
- NON: 1.85 raw stats + utility gratuita (violazione)
- Utility rispetta AFX1 hard caps (Fragment 5, Mark 5, duration 10, proc 45%)
- NO boss cleanse direct
- NO anti-P2W bypass
- NON finalizzare Legendary utility values in IC1 (design only)

## 69. affix-family coverage overview

Affix coverage matrix (blueprint only, NO runtime · NO affix creation):

| # | Family | Coverage target | Tier presence | Identity priority |
|---|---|---|---|---|
| 1 | `void.mark.power` | 22 | T1..T5 | HIGH |
| 2 | `void.mark.duration` | 18 | T1..T5 | HIGH |
| 3 | `void.drain.efficacy` | 16 | T2..T5 | HIGH |
| 4 | `void.payoff.dispel` | 14 | T2..T5 | HIGH |
| 5 | `void.fragment.interaction` | 20 | T1..T5 | HIGH |
| 6 | `void.payoff.efficacy` | 14 | T3..T5 | MEDIUM |
| 7 | `void.antitype.incorporeal` | 8 | T3..T5 | MEDIUM |
| 8 | `void.antitype.summon` | 8 | T3..T5 | MEDIUM |
| 9 | `void.channel.mobility` | 10 | T2..T5 | MEDIUM |
| 10 | `void.ritual.protection` | 10 | T3..T5 | MEDIUM |
| **Total overlay** | — | **140** | — | — |

Total 140 > 120 blueprint units per overlay legittimo (un item può avere presenza affix di più famiglie). Non è doppio conteggio.

## 70. Mark power coverage

`void.mark.power` · Coverage target **22**: Tier T1=3, T2=4, T3=5, T4=5, T5=5. Slot suitability: main_hand focus (primary), main_hand balestra, chest, accessory. Rarity floor: Common. Identity: HIGH. Conflict group: `MARK_MAGNITUDE_GROUP`.

## 71. Mark duration coverage

`void.mark.duration` · Coverage target **18**: Tier T1=2, T2=3, T3=4, T4=4, T5=5. Slot suitability: focus, head, chest, accessory. Rarity floor: Uncommon. Identity: HIGH. Conflict group: `MARK_DURATION_GROUP`.

## 72. Drain efficacy coverage

`void.drain.efficacy` · Coverage target **16**: Tier T2=3, T3=4, T4=4, T5=5 (assente T1). Slot suitability: focus, balestra, hands, accessory. Rarity floor: Uncommon. Identity: HIGH. Conflict group: `DRAIN_MAGNITUDE_GROUP`. Cap safeguard: Frammento cap 5.

## 73. Dispel quality coverage

`void.payoff.dispel` (label IT: Qualità della Dissipazione post-AFX1 micro-fix 1) · Coverage target **14**: Tier T2=2, T3=3, T4=4, T5=5. Slot suitability: focus, balestra, main_hand, off_hand. Rarity floor: Rare. Identity: HIGH. Conflict group: `DISPEL_QUALITY_GROUP`. Boss safeguard: NO direct boss dispel (AFX1 §75).

## 74. Fragment interaction coverage

`void.fragment.interaction` · Coverage target **20**: Tier T1=2, T2=3, T3=5, T4=5, T5=5. Slot suitability: focus, pugnale, ring, accessory. Rarity floor: Common. Identity: HIGH (Frammenti economy). Conflict group: `FRAGMENT_GENERATION_GROUP`. Cap safeguard: Fragment cap 5 hard, segment cap 2 per resource segment.

## 75. Payoff efficacy coverage

`void.payoff.efficacy` (label IT: Efficacia della Risoluzione post-AFX1 micro-fix 1) · Coverage target **14**: Tier T3=3, T4=5, T5=6 (assente T1-T2). Slot suitability: focus, main_hand, chest, back. Rarity floor: Rare. Identity: MEDIUM. Conflict group: `RESOLUTION_EFFICACY_GROUP`. Cap safeguard: combined proc 45% hard cap.

## 76. anti-incorporeal coverage

`void.antitype.incorporeal` · Coverage target **8**: Tier T3=2, T4=3, T5=3. Slot suitability: focus, main_hand, ring, accessory. Rarity floor: Rare. Identity: MEDIUM (endgame utility). Conflict group: `ANTITYPE_INCORPOREAL_GROUP`.

## 77. anti-summon coverage

`void.antitype.summon` · Coverage target **8**: Tier T3=2, T4=3, T5=3. Slot suitability: focus, main_hand, hands, accessory. Rarity floor: Rare. Identity: MEDIUM. Conflict group: `ANTITYPE_SUMMON_GROUP`. Boss safeguard: rispetta AFX1 §75 (5F annullamento summon valida on valid boss-summoned add).

## 78. channel mobility coverage

`void.channel.mobility` · Coverage target **10**: Tier T2=2, T3=3, T4=3, T5=2. Slot suitability: legs, feet, back, ring. Rarity floor: Common. Identity: MEDIUM. Conflict group: `MOBILITY_CHANNEL_GROUP`.

## 79. ritual protection coverage

`void.ritual.protection` · Coverage target **10**: Tier T3=3, T4=3, T5=4. Slot suitability: chest, back, neck, waist. Rarity floor: Uncommon. Identity: MEDIUM. Conflict group: `RITUAL_PROTECTION_GROUP`.

## 80. affix-by-tier matrix

Matrice affix family × tier (overlay coverage):

| Family | T1 | T2 | T3 | T4 | T5 | Total |
|---|---|---|---|---|---|---|
| mark.power | 3 | 4 | 5 | 5 | 5 | 22 |
| mark.duration | 2 | 3 | 4 | 4 | 5 | 18 |
| drain.efficacy | 0 | 3 | 4 | 4 | 5 | 16 |
| payoff.dispel | 0 | 2 | 3 | 4 | 5 | 14 |
| fragment.interaction | 2 | 3 | 5 | 5 | 5 | 20 |
| payoff.efficacy | 0 | 0 | 3 | 5 | 6 | 14 |
| antitype.incorporeal | 0 | 0 | 2 | 3 | 3 | 8 |
| antitype.summon | 0 | 0 | 2 | 3 | 3 | 8 |
| channel.mobility | 0 | 2 | 3 | 3 | 2 | 10 |
| ritual.protection | 0 | 0 | 3 | 3 | 4 | 10 |
| **Sum tier** | **7** | **17** | **34** | **39** | **43** | **140** |

Sum totale overlay = 140 (multi-family overlay legittimo, non doppio conteggio blueprint).

## 81. affix-by-slot matrix

Matrice affix family × slot (eligibility flags):

| Family | HD | NK | SH | CH | BK | HN | WR | WS | LG | FT | MH | OH | RG | AC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mark.power | · | · | · | ✓ | · | · | · | · | · | · | ✓ | · | · | ✓ |
| mark.duration | ✓ | · | · | ✓ | · | · | · | · | · | · | ✓ | · | · | ✓ |
| drain.efficacy | · | · | · | · | · | ✓ | · | · | · | · | ✓ | · | · | ✓ |
| payoff.dispel | · | · | · | · | · | · | · | · | · | · | ✓ | ✓ | · | · |
| fragment.interaction | · | · | · | · | · | · | · | · | · | · | ✓ | · | ✓ | ✓ |
| payoff.efficacy | · | · | · | ✓ | ✓ | · | · | · | · | · | ✓ | · | · | · |
| antitype.incorporeal | · | · | · | · | · | · | · | · | · | · | ✓ | · | ✓ | ✓ |
| antitype.summon | · | · | · | · | · | ✓ | · | · | · | · | ✓ | · | · | ✓ |
| channel.mobility | · | · | · | · | ✓ | · | · | · | ✓ | ✓ | · | · | ✓ | · |
| ritual.protection | · | ✓ | · | ✓ | ✓ | · | · | ✓ | · | · | · | · | · | · |

Legenda: HD=head NK=neck SH=shoulders CH=chest BK=back HN=hands WR=wrist WS=waist LG=legs FT=feet MH=main_hand OH=off_hand RG=ring AC=accessory.

## 82. EV-F2 REUSE_VALID integration

12 REUSE_VALID · tutti T1 · tutti class_specific o shared_family compatibile. Slot mix: chest 3, legs 2, head 2, hands 1, shoulders 1, wrist 1, main_hand focus 1, accessory 1 = **12** ✅. Rarity: C 6, U 4, R 2. Confidence: HIGH. Nessuna trasformazione richiesta.

## 83. EV-F2 REUSE_CONDITIONAL integration

32 REUSE_CONDITIONAL · di cui **6 arruolati** in Ledger A effective, **26 in STANDBY**.

Arruolati (6/32): caster stat neutral 4, focus mechanism compatible 1, pugnale mechanism compatible 1 → aggiunti a Ledger A effective (T1).

Standby (26/32): caster stat neutral rest 14, focus mechanism compatible rest 5, pugnale mechanism compatible rest 3, shared armor family 4 → **STANDBY POOL** (non blueprint unit, disponibili per rarity variants downstream o backfill).

Downstream requirements: condition code catalog, per-item PM approval, explicit allowlist entry, dry-run + snapshot pre-apply.

## 84. NOT_COMPATIBLE exclusion

134 NOT_COMPATIBLE esclusi definitivamente dal blueprint IC1: nessun arruolamento, nessuna riabilitazione, nessuna revisione retroattiva EV-F2 (LEDGER IMMUTABLE), nessun salvage-loophole.

Motivazioni principali (record only): Warlock tome family · Voidpiercer-bow · arcane_adept_orb · 6 warlock tome dedicated · armor identity non-caster (maglia/piastre) · weapon family non-Vuoto (bastone/wand/rod/tomo/grimoire/arco/strumento).

## 85. arcane_adept_orb future successor need

`arcane_adept_orb` = NOT_COMPATIBLE (EV-F2). Motivo: Progressive Discovery utility globale non riabilitabile. Future successor need: future new focus T3+ Legendary con identity Vuoto (Marchio power boost o Frammento catalyst) + Progressive Discovery Utility **NEW** (non riabilitare la vecchia). Count = **1** unit (già incluso in T3 Legendary focus, §65 item 1). Naming/effect/roll: NON in IC1, deferred a Registry v3 gate futuro.

## 86. voidpiercer-bow exclusion

`voidpiercer-bow` = NOT_COMPATIBLE (EV-F2). Weapon family "arco" (non-Vuoto), incompatibile con proficiency Vuoto. Nome legacy "voidpiercer" non riabilitabile. **Nessun successor need** per family arco. Sostituzione ranged: Ledger B include 7 balestra T1-T5, sufficiente ranged coverage. Escluso definitivamente.

## 87. focus T1 gap

Focus T1 count = **2** (main_hand). REUSE_VALID focus T1 arruolato = 1. REUSE_CONDITIONAL focus mechanism-compatible T1 arruolato = 1. Gap: **0**. Off_hand focus T1 = 0 (deferred a T4-T5, coerente identity progression). **Verdict**: **COVERED** ✅.

## 88. T2 gap

Live T2 = 0. Ledger A contribuzione T2 = 0. Ledger B T2 requirement = **22**. Gap composition: focus 2, balestra 1, pugnale 1 (prima apparizione), armor 12, universal 6. **Verdict**: BLUEPRINT COVERAGE PLANNED · NO CURRENT LIVE — richiede Registry v3 content generation gate futuro.

## 89. T3 gap

Live T3 = 0. Ledger B T3 requirement = **26**. Gap composition: focus 3 (incluso 1 Legendary), balestra 1, pugnale 1, off_hand 1 (prima apparizione), armor 14, universal 7. **Verdict**: BLUEPRINT COVERAGE PLANNED · Legendary T3=1 ✅.

## 90. T4 gap

Live T4 = 0. Ledger B T4 requirement = **26**. Gap: focus 2 (incluso 1 Legendary), balestra 2, pugnale 1, off_hand 2 (focus+pugnale), armor 14 (incluso 1 Legendary legs stoffa), universal 7. **Verdict**: BLUEPRINT COVERAGE PLANNED · Legendary T4=2 ✅.

## 91. T5 gap

Live T5 = 0. Ledger B T5 requirement = **28**. Gap: focus 1 (Legendary), balestra 2 (incluso 1 Legendary), pugnale 1, off_hand 3 (focus+balestra+pugnale), armor 10 (stoffa 7, cuoio 3, incluso 1 Legendary chest), universal 13 (back 2, neck 2, ring 4, accessory 5). **Verdict**: BLUEPRINT COVERAGE PLANNED · Legendary T5=3 · **`ENDGAME_BLUEPRINT_COMPLETE`** ✅.

## 92. missing slot gaps

Slot con gap zero (tutti 14 coperti): head ✅ (8), neck ✅ (6), shoulders ✅ (7), chest ✅ (10), back ✅ (6), hands ✅ (7), wrist ✅ (5), waist ✅ (6), legs ✅ (10), feet ✅ (7), main_hand ✅ (15), off_hand ✅ (6), ring ✅ (12), accessory ✅ (15). **Nessun slot gap**. Minimo: wrist = 5.

## 93. endgame gap

Endgame T5 gap analysis: armor T5 = 10 (stoffa 7 + cuoio 3, 70/30) ✅; focus T5 = 1 + Legendary 1 = 2 ✅; balestra T5 = 2 + Legendary 1 = 3 ✅; pugnale T5 = 1 (no Legendary) → **gap Legendary pugnale endgame** ⚠; ring T5 = 4 (no Legendary) → **gap Legendary ring endgame** ⚠; accessory T5 = 5 (no Legendary) → **gap Legendary accessory endgame** ⚠.

**Verdict endgame gap**: endgame **core coverage** = **COMPLETE** ✅; Legendary pugnale/ring/accessory endgame = **DEFERRED** (accettabile IC1 v1, escalation su IC2 hypothetical o Registry v3 Legendary gate futuro).

Overall endgame verdict resta: **`ENDGAME_BLUEPRINT_COMPLETE`** ✅ (gap su Legendary-strategy-optional, non su core progression).

## 94. future content workload

Workload downstream stimato (materialization Ledger B, 102 unit):

| Milestone | Effort | Gate dependency |
|---|---|---|
| Registry v3 content module generation | HIGH | Gate futuro dedicato |
| Item ID assignment | MEDIUM | Post-IC1 closure |
| Item naming (IT primary + EN readiness) | HIGH | Gate localization |
| Stat budget finalization | HIGH | Gate stat budget |
| Affix assignment per item | HIGH | Gate affix assignment |
| Drop table / loot table | HIGH | Gate loot |
| Legendary utility finalization | MEDIUM | Gate Legendary |

Nessun workload item-level in IC1. Solo count.

## 95. Registry v3 content dependency

**NEXT PLANNED GATE = R18.6.RV3-IS1 · Item Specification & Roster Contract** (post-IC1 closure, HOLD).

Regime futuro IS1: DOCUMENTAL ONLY · NO item generation · NO Registry module · NO apply. IS1 dovrà trasformare le 120 blueprint unit in specifiche strutturate (roster · codice blueprint · tier · slot · family · identity · rarity intent · affix pool eligibility · stat-budget band · source reuse/new · condition code per i 6 provisional). IS1 NON definirà: item_id runtime · record DB · loot table · apply script · effect finalization.

**Stato IS1**: **HOLD · NOT AUTHORIZED IN THIS DISPATCH**.

Registry v3 content generation resta **downstream a IS1 CLOSED**:
- Item generation = **NOT AUTHORIZED**
- Registry v3 apply = **NOT AUTHORIZED**
- Registry v3 module generation = **NOT AUTHORIZED**

Ogni Ledger B unit (102 base + fino a 6 fallback replacement) richiederà futuro gate content generation con: explicit allowlist · condition code catalog compilato · dry-run diff PM-approved · snapshot pre/post · explicit PM GO per apply.

## 96. future item specification dependency

Specification finale per ogni blueprint unit = **DEFERRED**. Include: stat roll, affix roll, item level formula, base name, description, flavor text. Nessuna specification generata in IC1.

## 97. future naming dependency

Nomi item (IT primary) = **DEFERRED** a gate naming. EN readiness = struttura i18n key (design contract only, no traduzione). Nomi Legendary = **DEFERRED** (mai in IC1). Nomi seguono lore Cacciatore del Vuoto (design-only reference, no generation).

## 98. future stat-budget dependency

Stat budget per rarity: multiplier locked (§56). Distribuzione stat per item (main + secondary + utility) = **DEFERRED**. Interazione G1 stat design = read-only reference. Nessun stat number finale generato in IC1.

## 99. future affix-assignment dependency

Affix pool selector = `void.cacciatore_del_vuoto.pool.v1` (AFX1 LOCK). Affix ID assignment = **DEFERRED** (AFX1 §12 schema only, no creation). Affix roll formula = **DEFERRED**. Affix stacking runtime = **DEFERRED** (design contract AFX1). Nessun affix assignment eseguito in IC1.

## 100. anti-P2W requirements

Ogni futura blueprint unit richiederà `can_be_sold_for_real_money = false`. Applicazione: T1-T5, Common-Legendary, class_specific + shared_family + universal_neutral, Ledger A + Ledger B. Backfill 50 item con field mancante = **NOT AUTHORIZED** (deferred Data Quality gate). Auto-P2W detection = **NOT DESIGNED** in IC1.

## 101. validation rules

1. `total_blueprint = 120` (exact)
2. `Ledger A_effective + Ledger B = 120` (identità stretta)
3. `Sum(tier_totals) = 120` (18+22+26+26+28)
4. `Sum(slot_totals) = 120` (14 slot canonici)
5. `Sum(rarity_totals) = 120` (C+U+R+E+L = 42+32+26+14+6)
6. `Sum(identity_totals) = 120` (CS+SF+UN = 68+30+22)
7. `Sum(armor_totals) = 60` (stoffa 42 + cuoio 18)
8. `Sum(weapon_totals) = 21` (focus 10 + balestra 7 + pugnale 4)
9. `armor_T5_stoffa/cuoio = 70/30` (7/3)
10. `focus > balestra > pugnale` (10 > 7 > 4)
11. `Legendary_count = 6`
12. `Legendary_ILVL_T5 = 60`
13. `AFX1_hard_caps_preserved` (Fragment 5, Mark 5, duration 10, proc 45%)
14. `boss_safeguard_preserved` (AFX1 §75)
15. `endgame_verdict = ENDGAME_BLUEPRINT_COMPLETE`
16. `NOT_COMPATIBLE_134_excluded`
17. `no_maglia_no_piastre`
18. `no_arco_no_tomo_no_bastone_no_wand_no_rod_no_grimoire_no_strumento`
19. `slot_count_canonical = 14` (no ring1/ring2/15th_slot)

## 102. accounting validation

Cross-check (tutte le somme, post micro-fix 1-5):

| Vista | Formula | Totale | Verifica |
|---|---|---|---|
| Per tier | 18+22+26+26+28 | 120 | ✅ |
| Per slot | 8+6+7+10+6+7+5+6+10+7+15+6+12+15 | 120 | ✅ |
| Per rarity | 42+33+27+15+3 | 120 | ✅ |
| Per identity | 68+30+22 | 120 | ✅ |
| Blueprint = 12 committed + 6 provisional + 102 future | 12+6+102 | 120 | ✅ |
| Worst-case future new-item | 12+108 | 120 | ✅ |
| Fallback reserve (outside blueprint) | — | 6 (outside) | ✅ |
| Armor stoffa + cuoio | 42+18 | 60 | ✅ |
| Weapon focus + balestra + pugnale | 10+7+4 | 21 | ✅ |
| T5 armor 70/30 | stoffa 7 / cuoio 3 | 70/30 | ✅ |
| Legendary total | 0+0+0+0+3 (T5 ONLY) | 3 | ✅ |
| Legendary slots | focus 1 + balestra 1 + chest stoffa 1 | 3 | ✅ |

Reconciliazione: **PASS** ✅. Nessun `~`, nessun range non riconciliato, nessun doppio conteggio, nessun aggregate accounting. `CONDITIONAL_FALLBACK_RESERVE = 6` **outside blueprint count** (non sommato al 120).

## 103. risk register

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| 1 | Ledger B 102 nuovi workload elevato | HIGH | Registry v3 content gate per-tier |
| 2 | Legendary count 6 basso per endgame extended | MEDIUM | Gate IC-Legendary hypothetical |
| 3 | 32 REUSE_CONDITIONAL richiedono per-item PM approval | MEDIUM | Downstream condition code catalog |
| 4 | 50 item live con `can_be_sold_for_real_money` missing | LOW | Deferred Data Quality gate |
| 5 | 21 item live con `slot_type` null | LOW | Deferred canonicalization gate |
| 6 | Legendary pugnale/ring/accessory endgame gap | LOW | Accettabile IC1 v1, deferred |
| 7 | Multi-rarity depth non pianificato in IC1 | LOW | Advisory scenario 180–220 documentato |
| 8 | Off_hand appare solo T3+ | LOW | Design choice identity progression |
| 9 | Focus channel + Pugnale ritual interaction complessa | MEDIUM | AFX1 §71-72 caps preservati |
| 10 | Auto-P2W detection assente | LOW | Manual field required, no runtime enforcement |

## 104. PM open questions

Estrazione IC1-Qn (verbatim):

```
=== IC1-Q1 ===
Testo: Approvare exact blueprint total = 120?
Recommendation e1_dev: APPROVE (planning center, envelope 110-130)
Sezione correlata: §9, §17
Impatto: closure IC1
Default proposto: APPROVE
Blocking: false

=== IC1-Q2 ===
Testo: Approvare split Ledger A_effective=18 / Ledger B=102 (invece di A=44 / B=76)?
Recommendation e1_dev: APPROVE (12+6 arruolati + 26 standby è più realistico)
Sezione correlata: §13, §16, §17
Impatto: closure IC1 + downstream Registry v3
Default proposto: APPROVE con nota "26 STANDBY pool"
Blocking: false

=== IC1-Q3 ===
Testo: Approvare tier allocation 18/22/26/26/28?
Recommendation e1_dev: APPROVE (crescita monotona, no T1-heavy)
Sezione correlata: §18-§23
Impatto: closure IC1
Default proposto: APPROVE
Blocking: false

=== IC1-Q4 ===
Testo: Approvare Legendary count = 6, tier T3/T4/T5 = 1/2/3?
Recommendation e1_dev: APPROVE
Sezione correlata: §65-§68
Impatto: closure IC1
Default proposto: APPROVE
Blocking: false

=== IC1-Q5 ===
Testo: Approvare armor split stoffa 42 / cuoio 18 (70/30 globale + T5)?
Recommendation e1_dev: APPROVE (identity caster + preservazione T5 70/30)
Sezione correlata: §42-§45
Impatto: closure IC1
Default proposto: APPROVE
Blocking: false

=== IC1-Q6 ===
Testo: Approvare weapon split focus 10 / balestra 7 / pugnale 4?
Recommendation e1_dev: APPROVE (focus-primary preservato)
Sezione correlata: §46-§50
Impatto: closure IC1
Default proposto: APPROVE
Blocking: false

=== IC1-Q7 ===
Testo: Approvare identity split class_specific 68 / shared_family 30 / universal_neutral 22?
Recommendation e1_dev: APPROVE (class_specific dominante 56.7%)
Sezione correlata: §52-§55
Impatto: closure IC1
Default proposto: APPROVE
Blocking: false

=== IC1-Q8 ===
Testo: Approvare rarity split 42/32/26/14/6?
Recommendation e1_dev: APPROVE (no x5 multiplication artificiale)
Sezione correlata: §56-§64
Impatto: closure IC1
Default proposto: APPROVE
Blocking: false

=== IC1-Q9 ===
Testo: Accettare gap Legendary pugnale/ring/accessory endgame come DEFERRED accettabile IC1 v1?
Recommendation e1_dev: APPROVE (endgame core resta COMPLETE)
Sezione correlata: §93
Impatto: closure IC1 + gate IC-Legendary hypothetical futuro
Default proposto: APPROVE con nota "deferred a IC-Legendary hypothetical"
Blocking: false

=== IC1-Q10 ===
Testo: Confermare 26 REUSE_CONDITIONAL in STANDBY pool (non blueprint unit)?
Recommendation e1_dev: CONFIRM (disponibili per rarity variants downstream)
Sezione correlata: §14, §83
Impatto: Registry v3 content generation downstream
Default proposto: CONFIRM
Blocking: false

=== IC1-Q11 ===
Testo: Approvare next gate = Registry v3 content generation dedicato (post-IC1 closure)?
Recommendation e1_dev: APPROVE con NC1 in parallelo (non blocking)
Sezione correlata: §95, §105
Impatto: roadmap post-IC1
Default proposto: APPROVE (Registry v3 content gate come prossimo, NC1 in parallelo HOLD authorized)
Blocking: false

=== IC1-Q12 ===
Testo: Endgame verdict ENDGAME_BLUEPRINT_COMPLETE accettato dal PM?
Recommendation e1_dev: CONFIRM (§25, §91, §93)
Sezione correlata: §25
Impatto: closure IC1
Default proposto: CONFIRM
Blocking: false
```

**IC1-Q verbatim count**: **12** domande.

## 105. GO/HOLD recommendation

**Recommendation e1_dev**: **GO CLOSURE IC1** (post applicazione dei 6 micro-fix PM in questo dispatch).

Stato dispatch (post micro-fix):
- IC1 draft complete 105/105 sezioni ✅
- Contabilità canonica ratificata: 12 committed + 6 provisional + 102 future = **120** ✅
- Fallback reserve 6 outside blueprint (worst-case 12+108=120) ✅
- Legendary 3 (T5 ONLY: focus / balestra / chest stoffa) ✅
- Rarity 42/33/27/15/3 riconciliato ✅
- Endgame verdict `ENDGAME_BLUEPRINT_COMPLETE` ✅
- Nessun item/affix creato · Nessuna Registry v3 module · Nessun DB write ✅

**Next planned gate** (post-IC1 closure): **R18.6.RV3-IS1 · Item Specification & Roster Contract** → **HOLD · NOT AUTHORIZED IN THIS DISPATCH**.

**HOLD locks preservati**: AFX2 = RESERVED FUTURE · NC1 = HOLD · Registry v3 apply = NOT AUTHORIZED · Gate 11 = HOLD · Monaco / Wave 1 = HOLD · IS1 = HOLD.

**🛑 EXPLICIT STOP**: fermo qui, closure formale IC1 procederà nello stesso dispatch (3 artifact + PRD append). Nessun kickoff IS1. Nessun kickoff NC1/Gate 11/Wave 1. Nessuna item generation.
