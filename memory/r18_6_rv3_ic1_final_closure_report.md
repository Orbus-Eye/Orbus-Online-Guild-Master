# R18.6.RV3-IC1 · Item Coverage & Content Blueprint · FINAL CLOSURE REPORT

**Gate ID**: R18.6.RV3-IC1
**Titolo**: Item Coverage & Content Blueprint
**Classe pilota**: Cacciatore del Vuoto (`class_slug = cacciatore_del_vuoto`)
**Scoping**: A1 FULL · CONTENT ALLOCATION BLUEPRINT
**Stato**: **CLOSED · PM-LOCKED · IMMUTABLE**
**Data closure**: 2026-07-11 UTC
**Regime**: DOCUMENTAL ONLY · NO CODE · NO DB WRITE · NO ITEM · NO AFFIX · NO REGISTRY MODULE
**Autore**: e1_dev · **Ratificatore**: PM Orbus Online

Il presente documento certifica formalmente la chiusura del gate R18.6.RV3-IC1 dopo l'applicazione dei 6 micro-fix PM (terminologia contabile, enumerazione 6 provisional, Legendary 6→3, rarity redistribution, next gate IS1, verifica contabilità). IC1 diventa IMMUTABILE al termine del presente dispatch.

---

## 1. PM verdict IC1

Il PM ha emesso **verdict finale conclusivo** su IC1:

- Draft accettato con 6 micro-fix correttivi obbligatori
- Micro-fix applicati puntualmente (no rewrite completo)
- Contabilità canonica ratificata: **12 committed + 6 provisional + 102 future = 120**
- **GO CLOSURE IC1** autorizzata nello stesso dispatch
- IS1 kickoff = HOLD (non autorizzato in questo dispatch)

Ratifiche invariate: IC1-Q1 (120 blueprint total), Q3 (tier 18/22/26/26/28), Q5 (armor 42/18, 70/30 T5), Q6 (weapon focus-primary), Q7 (identity 68/30/22), Q9 (Legendary gap deferred), Q10 (26 REUSE_CONDITIONAL STANDBY confirmed), Q12 (endgame complete), Affix overlay 140 approvato.

## 2. IC1 CLOSED

Stato ratificato: `gate_id = R18.6.RV3-IC1` · `state = CLOSED` · `pm_locked = true` · `immutable_after_this_dispatch = true` · `reopen_authorization = NOT_AUTHORIZED (deferred to hypothetical IC2 future gate)`.

Contratti chiusi:
- Blueprint total 120 LOCK
- Terminologia contabile (12 committed + 6 provisional + 102 future + 6 fallback outside)
- 3 categorie identity split (68/30/22)
- Rarity distribution (42/33/27/15/3)
- Legendary policy T5 ONLY (count 3)
- Slot canonici 14 LOCK

## 3. Blueprint total 120 LOCK

**BLUEPRINT TOTAL = 120** (planning center, envelope 110–130). LOCK immutabile post-closure. Modifiche future = nuovo gate (IC2 hypothetical).

- 120 ∈ [110, 130] ✅
- Nessuna concentrazione T1 (18/120 = 15%)
- Endgame T5 corposo (28/120 = 23.3%)
- 14 slot canonici tutti coperti ≥ 5 unit
- 10 famiglie affix tutte con coverage overlay

## 4. Blueprint unit definition

`1 blueprint unit` = **1 futura identità item distinta**.

NON equivalente a: 1 rarity variant · 1 affix roll · 1 loot-table occurrence · 1 database copy. IC1 v1 NON applica moltiplicazione artificiale x5 rarity per unit.

## 5. COMMITTED_REUSE = 12

**12 REUSE_VALID** ratificati EV-F2, tutti arruolati nel blueprint:
- 12 unit tutti T1 (baseline live catalog)
- Slot mix: chest 3, legs 2, head 2, hands 1, shoulders 1, wrist 1, main_hand focus 1, accessory 1
- Rarity live: Common 6, Uncommon 4, Rare 2
- Confidence: **HIGH** (già validati EV-F2, no ulteriore validazione)

I 12 sono i **soli** riusi garantiti nel blueprint. NO frase "18 riusi garantiti" (vietata da micro-fix 1).

## 6. PROVISIONAL_CONDITIONAL_ALLOCATION = 6 (enumerati)

6 REUSE_CONDITIONAL selezionati per allocation provisional, enumerati esplicitamente (fonte: §14 del blueprint MD, sezione dedicata post micro-fix 2):

| # | `item_id` (blueprint code) | `slot` | `family` | `condition_code` | `identity_risk` | `mutation_required` | `approval_status` |
|---|---|---|---|---|---|---|---|
| 1 | `cond_reuse_caster_stat_neutral_01` | chest | armor_stoffa | `COND_STAT_NEUTRAL_INT` | MEDIUM | false | provisional |
| 2 | `cond_reuse_caster_stat_neutral_02` | legs | armor_stoffa | `COND_STAT_NEUTRAL_INT` | MEDIUM | false | provisional |
| 3 | `cond_reuse_caster_stat_neutral_03` | accessory | universal_neutral | `COND_ACCESSORY_NEUTRAL` | LOW | false | provisional |
| 4 | `cond_reuse_caster_stat_neutral_04` | ring | universal_neutral | `COND_ACCESSORY_NEUTRAL` | LOW | false | provisional |
| 5 | `cond_reuse_focus_mechanism_compat_01` | main_hand | focus | `COND_FOCUS_MECHANISM_OK` | MEDIUM | false | provisional |
| 6 | `cond_reuse_pugnale_mechanism_compat_01` | main_hand | pugnale | `COND_PUGNALE_MECHANISM_OK` | MEDIUM | false | provisional |

**VIETATA** selezione via: keyword · query dinamica · tag caster generico · tag warlock generico · presenza generica di Intelligenza.

Ogni provisional è soggetto a: allowlist · validazione per-item · dry-run · snapshot · futuro GO PM (F2-Q2 policy AFX1-Q9).

## 7. FUTURE_NEW_ITEM_BASE_ALLOCATION = 102

**102 blueprint unit** future new-item. Distribuzione per tier:
- T1 = 0 (coperto interamente da 12 committed + 6 provisional = 18)
- T2 = 22 (100% new)
- T3 = 26 (100% new, Legendary T3=0 post micro-fix 3)
- T4 = 26 (100% new, Legendary T4=0 post micro-fix 3)
- T5 = 28 (100% new, Legendary T5=3)

Constraint: nessun record item, nessun nome, nessuna stat finalization, nessuna Registry v3 riga. Solo count aggregate.

## 8. CONDITIONAL_FALLBACK_RESERVE = 6 (outside blueprint)

**Fallback reserve = 6 unit** REUSE_CONDITIONAL non selezionati come provisional ma disponibili per sostituzione 1:1 se un provisional fallisce validazione futura.

- **OUTSIDE blueprint count** (NON sommato al 120)
- Regola: se `cond_reuse_X` fallisce validazione → sostituito 1:1 da 1 future new-item unit; il fallback reserve copre worst-case totale di 6 sostituzioni
- Rimangono altri 20 REUSE_CONDITIONAL fuori dal fallback reserve, classificati **STANDBY POOL** (disponibili per rarity variants downstream, non blueprint unit e non fallback)

## 9. Worst-case future new-item need = 108

Worst-case scenario (tutti 6 provisional falliscono validazione futura):

```
validated reuse (COMMITTED)  = 12
future new-item need         = 108  (102 base + 6 sostituzioni)
────────────────────────────────
total blueprint              = 120
```

## 10. Tier allocation 18/22/26/26/28

Matrice tier × totale (sum = 120):

| Tier | Livelli | Count | % |
|---|---|---|---|
| T1 | Lv1–15 | 18 | 15.0% |
| T2 | Lv16–30 | 22 | 18.3% |
| T3 | Lv31–45 | 26 | 21.7% |
| T4 | Lv46–55 | 26 | 21.7% |
| T5 | Lv56–60 | 28 | 23.3% |
| **Total** | — | **120** | 100% |

Progressione continua · nessun tier vuoto · monotona non-lineare · endgame T5 corposo.

## 11. Armor 42/18 (70/30 T5)

Armor totale = **60** (50% del blueprint). Stoffa **42** (70%), cuoio **18** (30%).

T5 armor = **10**: stoffa **7** (70%) / cuoio **3** (30%) → **ratio 70/30 exact** ✅.

**Vietato**: maglia · piastre. Slot armor coperti (8/8): head, shoulders, chest, hands, wrist, waist, legs, feet.

## 12. Weapon focus 10 / balestra 7 / pugnale 4 (focus-primary)

Weapon totale = **21**. Focus **10** (47.6%) · Balestra **7** (33.3%) · Pugnale **4** (19.0%).

Coeff G5 (design direction only, non runtime formula): focus 1.00 · balestra 0.85–0.90 · pugnale 0.70–0.80.

**Focus > balestra > pugnale** (10 > 7 > 4) → **Focus-primary CONFIRMED** ✅.

**Vietato**: tomo · bastone · wand · rod · grimoire · arco · strumento (no compensazione con family non-Vuoto).

## 13. Identity 68/30/22

Identity split (sum = 120):
- **class_specific = 68** (56.7%) — sostiene Marchio · Drain · Frammenti · Payoff · anti-incorporeo · anti-summon · ritualità Vuoto
- **shared_family = 30** (25.0%) — armor Int-shareable · focus caster-compatible · pugnale caster-compatible · accessory caster neutral. **Vietato borrow identity** di altra classe
- **universal_neutral = 22** (18.3%) — nessun riferimento a Mago · Paladino · Cacciatore di Mostri · Warlock legacy · altra classe

Nessuna categoria >60% o <15%. Ordine identitario preservato (CS > SF > UN).

## 14. Rarity 42/33/27/15/3

Rarity distribution (post micro-fix 4, sum = 120):

| Rarity | Count | % | Multiplier |
|---|---|---|---|
| Common | 42 | 35.0% | 1.00 |
| Uncommon | 33 | 27.5% | 1.15 |
| Rare | 27 | 22.5% | 1.35 |
| Epic | 15 | 12.5% | 1.60 |
| Legendary | 3 | 2.5% | 1.85 |
| **Total** | **120** | 100% | — |

**No moltiplicazione artificiale x5 rarity**: ogni unit = 1 identità 1 rarità primaria. Multi-rarity depth downstream (decisione Registry v3 gate futuro).

## 15. Legendary count = 3 · T5 only

Legendary count = **3** (2.5%, post micro-fix 3). **Legendary tier policy LOCK = T5 ONLY**.

- NO Legendary T1 · NO Legendary T2 · NO Legendary T3 · NO Legendary T4
- Solo Legendary T5 (endgame)
- **Rimossi post micro-fix 3** (rispetto al draft precedente): T3 main_hand focus · T4 main_hand focus · T4 legs stoffa
- Motivo: densità 5% vs baseline R18.5 1% → power creep risk

## 16. Legendary distribution (focus / balestra / chest stoffa T5)

Distribuzione slot Legendary:

| Slot | Count | Tier | Function |
|---|---|---|---|
| main_hand focus | 1 | T5 | primary identity (full ritual completion signature) |
| main_hand balestra | 1 | T5 | ranged signature (long-range Payoff dispel) |
| chest (armor stoffa) | 1 | T5 | endgame armor signature (full-set ritual protection) |
| **Total** | **3** | T5 ONLY | — |

NON coperti in IC1: pugnale · legs · accessory · ring · back · off_hand Legendary. Deferred a hypothetical IC-Legendary o Registry v3 Legendary gate futuro (IC1-Q9 approved).

## 17. Legendary ILVL 60 · multiplier 1.85 budget totale

Vincoli Legendary:
- Legendary ILVL T5 = **60** (LOCK, preservato da R18.5)
- Multiplier budget = **1.85** (utility_unique inclusa nel totale)
- **NON**: 1.85 raw stats + utility gratuita (violazione budget)
- Utility rispetta AFX1 hard caps (Fragment 5, Mark 5, duration 10, proc 45%)
- **NO** boss cleanse direct · **NO** anti-P2W bypass
- Item names / effects / rows / progressive discovery utility roll = **NOT AUTHORIZED** in IC1

## 18. Endgame verdict ENDGAME_BLUEPRINT_COMPLETE

Endgame T5 checklist (verifica presenza obbligatoria):
- Armor stoffa ✅ 7 · Armor cuoio ✅ 3
- Focus ✅ 1+1L · Balestra ✅ 2+1L · Pugnale ✅ 1
- head ✅ 2 · back ✅ 2 · ring ✅ 4 · accessory ✅ 5
- Legendary strategy ✅ 3 T5 (focus + balestra + chest)
- Affix identity coverage T5 ✅ 10/10 famiglie

**Verdict endgame**: **`ENDGAME_BLUEPRINT_COMPLETE`** ✅ (gap Legendary pugnale/ring/accessory endgame = DEFERRED accettabile IC1 v1, IC1-Q9).

## 19. Affix overlay 140 (non-item count)

Affix coverage overlay = **140** su 120 blueprint units (multi-family per unit legittimo, non doppio conteggio blueprint):

| Family | Target |
|---|---|
| void.mark.power | 22 |
| void.mark.duration | 18 |
| void.drain.efficacy | 16 |
| void.payoff.dispel | 14 |
| void.fragment.interaction | 20 |
| void.payoff.efficacy | 14 |
| void.antitype.incorporeal | 8 |
| void.antitype.summon | 8 |
| void.channel.mobility | 10 |
| void.ritual.protection | 10 |
| **Total overlay** | **140** |

Non è item count. È coverage overlay per famiglia (un item ha affix di più famiglie).

## 20. AFX1 pool consumption

IC1 consuma AFX1 CLOSED via:
- Pool selector = `void.cacciatore_del_vuoto.pool.v1` (LOCK)
- 10 famiglie affix ratificate AFX1 (§8)
- Nessuna riapertura AFX1
- Nessuna creazione affix_id / roll / value in IC1
- Nessuna assegnazione item-affix in IC1

## 21. Hard cap preservation

AFX1 hard caps preservati (nessuna allocazione IC1 li può violare):
- Fragment cap = 5 (LOCK)
- Active marks cap = 5 (LOCK)
- Mark duration cap = 10 turni (LOCK)
- Combined proc hard cap = 45% (LOCK)
- Focus channel bonus +1F, segment cap 2F per resource segment (LOCK)
- Pugnale ritual-close bonus +1F, max 1x per applicazione Marchio (LOCK)

## 22. Anti-P2W

Ogni futura blueprint unit richiederà `can_be_sold_for_real_money = false`:
- T1-T5 (tutti tier) ✅
- Common-Legendary (tutte rarity) ✅
- class_specific + shared_family + universal_neutral (tutte identity) ✅
- 12 committed + 6 provisional + 102 future + 6 fallback outside (tutti ledger) ✅

Backfill 50 item live con field mancante = **NOT AUTHORIZED** in IC1 (deferred Data Quality gate).

## 23. EV-F2 ledger immutability

Ledger EV-F2 **IMMUTABILE** post-closure RV3-EV. IC1 non modifica:
- 178 live item baseline
- 12 REUSE_VALID
- 32 REUSE_CONDITIONAL (di cui 6 provisional selezionati + 6 fallback + 20 standby)
- 134 NOT_COMPATIBLE (esclusi)
- 0 PM_REVIEW

Nessuna riapertura EV-F2, nessuna revisione retroattiva verdict.

## 24. 12 IC1-Q resolutions (verbatim)

Estrazione IC1-Qn verbatim + ratifica finale:

| ID | Recommendation e1_dev | PM Ratification | Stato |
|---|---|---|---|
| IC1-Q1 | APPROVE (blueprint 120) | **APPROVED = LOCK** | RATIFIED |
| IC1-Q2 | APPROVE split 18/102 | **CORRECTED** → 12 committed + 6 provisional + 102 future + 6 fallback outside (micro-fix 1) | RATIFIED |
| IC1-Q3 | APPROVE tier 18/22/26/26/28 | **APPROVED** | RATIFIED |
| IC1-Q4 | APPROVE Legendary 6 (T3/T4/T5 = 1/2/3) | **CORRECTED** → Legendary 3 T5 ONLY (micro-fix 3) | RATIFIED |
| IC1-Q5 | APPROVE armor stoffa 42 / cuoio 18 | **APPROVED** (no maglia/piastre) | RATIFIED |
| IC1-Q6 | APPROVE weapon focus 10 / balestra 7 / pugnale 4 | **APPROVED** (focus-primary lock, coeff G5 direction only) | RATIFIED |
| IC1-Q7 | APPROVE identity CS 68 / SF 30 / UN 22 | **APPROVED** (no class borrowing) | RATIFIED |
| IC1-Q8 | APPROVE rarity 42/32/26/14/6 | **CORRECTED** → 42/33/27/15/3 (micro-fix 4) | RATIFIED |
| IC1-Q9 | APPROVE Legendary endgame gap DEFERRED | **APPROVED** (v1 non-blocker) | RATIFIED |
| IC1-Q10 | CONFIRM 26 REUSE_CONDITIONAL STANDBY | **CONFIRMED** (outside 120, no auto-promotion) | RATIFIED |
| IC1-Q11 | APPROVE next gate = Registry v3 content | **CORRECTED** → next gate = IS1 (micro-fix 5) | RATIFIED |
| IC1-Q12 | CONFIRM ENDGAME_BLUEPRINT_COMPLETE | **CONFIRMED** | RATIFIED |

**Copertura**: 12 / 12 domande ratificate (7 APPROVED as-is, 4 CORRECTED via micro-fix, 1 CONFIRMED as-is).

## 25. IS1 next planned gate (HOLD)

**NEXT PLANNED GATE = R18.6.RV3-IS1 · Item Specification & Roster Contract**

Regime futuro IS1: DOCUMENTAL ONLY · NO item generation · NO Registry module · NO apply.

Scope futuro IS1: trasformare le 120 blueprint unit in specifiche strutturate (roster · codice blueprint · tier · slot · family · identity · rarity intent · affix pool eligibility · stat-budget band · source reuse/new · condition code per i 6 provisional).

NON definirà: item_id runtime · record DB · loot table · apply script · effect finalization.

**Stato IS1**: **HOLD · NOT AUTHORIZED IN THIS DISPATCH**.

## 26. AFX2 reserved future

AFX2 (hypothetical vocabulary v2) rimane **RESERVED FUTURE · NOT AUTHORIZED · NOT REQUIRED FOR IS1** (invariato da AFX1 closure §26).

Trigger di apertura AFX2: shared pool · universal pool · multi-pool architecture · multi-value pool selector · affix vocabulary v2 · cross-class affix contracts.

Nessuno di questi requirement è necessario ora.

## 27. NC1 HOLD

**NC1 · Null Conflict Remediation Planning** = **HOLD** (invariato).

- NC1 resta obbligatorio come **pre-migration dependency** (prima di Registry v3 apply)
- NON è successore lineare di IC1
- NC1 può essere aperto **in parallelo** a IS1 (post-IC1 closure) su decisione PM
- Nessun kickoff NC1 in questo dispatch

## 28. Registry v3 apply disabled

Registry v3 apply = **NOT AUTHORIZED**:
- Registry v3 content generation = **NOT AUTHORIZED**
- Registry v3 module generation = **NOT AUTHORIZED**
- `affix_pool_tag` population = **NOT AUTHORIZED**
- `rec_classes` field update = **NOT AUTHORIZED**
- Backfill 50 item can_be_sold missing = **NOT AUTHORIZED**
- Backfill 21 item slot_type null = **NOT AUTHORIZED**

## 29. Item creation disabled

Item creation = **NOT AUTHORIZED**:
- Nessun item creato in IC1 (né in dry-run, né in staging, né in live)
- Nessun item_id assegnato
- Nessun nome item · nessuna descrizione · nessun flavor text
- Nessuno stat roll · nessuno affix roll · nessun proc value
- DB item collection = **INVARIATO**
- 178 item live catalog = **INVARIATO**

## 30. Governance evidence

Evidence raccolti alla closure:

- **Pytest sealed integrity** (`backend/tests/backend_r18_4_sealed_integrity_test.py`): **6 passed**, sigilli **36/36 byte-identical**
- **Anchor hash** `backend/app/content/lore_meta.py`: **`a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`** ✅ INVARIATO
- **Backend source changes** = 0
- **Frontend source changes** = 0
- **OpenAPI changes** = 0
- **DB writes** = 0
- **Migrations** = 0
- **Item creations** = 0
- **Affix creations** = 0
- **Affix backfill** = 0
- **Registry v3 apply** = 0
- **Registry v3 module gen** = 0
- **PRD operation** = APPEND-ONLY (nessuna riscrittura sezioni pre-esistenti)
- **New seals added** = 0
- **Test files created** = 0

Regime DOCUMENTAL-ONLY preservato al **100%**.

## 31. SHA policy compliance

Compliance con SHA policy §31 AFX1 closure (ratificata PM):

- **`full_file_sha256`** = hash reale del file completo on-disk (canonical usage)
- **`content_body_sha256`** = alternativa per body escluso footer (non usata in IC1)
- **Self-referential SHA VIETATO in-file**: il `full_file_sha256` post-append PRD **NON** è stato scritto nel PRD stesso
- **Tracciato esclusivamente** in `r18_6_rv3_ic1_closure_manifest.json` esterno + messaggio di output PM

Retro-application: PRD pre-append IC1 SHA = `516b6ebe...a7b74` (embedded valido, riferisce stato pregresso, non self-referential). PRD post-append IC1 SHA = tracciato solo esternamente.

**Policy §31 rispettata al 100%**.

## 32. Explicit STOP

**IC1 = CLOSED · PM-LOCKED · IMMUTABLE**

Governance locks finali:
- `apply_authorized = false`
- `item_creation_authorized = false`
- `affix_creation_authorized = false`
- `registry_v3_apply_authorized = false`
- `registry_v3_module_generation_authorized = false`
- `field_addition_authorized = false`
- `backfill_authorized = false`
- `is1_kickoff_authorized = false` (this dispatch)
- `ic1_closed = true`
- `ic1_reopen_authorized = false`
- `sealed_integrity_intact = true (36/36)`
- `lore_meta_sha_invariant = true (a18f708b...965b8f)`

**Next planned gate**: **R18.6.RV3-IS1** → HOLD.

**Non autorizzato in questo dispatch**: IS1 kickoff · IS1 draft · IS1 pre-work · NC1 kickoff · Gate 11 · Registry v3 apply · item creation · affix creation · reopen AFX1 / RV3-EV / EV-F1 / EV-F2 · modifiche PRD oltre l'append IC1 CLOSED · modifiche a source IC1 md/json post-closure.

**Stato roadmap post IC1 closure**:
- Cacciatore del Vuoto = ACTIVE-DESIGN-READY
- R18.3f = CLOSED · RV3-EV = CLOSED · AFX1 = CLOSED
- **IC1 = CLOSED** ← this dispatch
- IS1 = HOLD (next planned)
- AFX2 = RESERVED FUTURE
- NC1 = HOLD
- Registry v3 item generation = NOT AUTHORIZED
- Registry v3 apply = NOT AUTHORIZED
- Gate 11 = HOLD
- Monaco / Wave 1 = HOLD

**Attendo nuovo verdict PM per apertura del prossimo gate.**
