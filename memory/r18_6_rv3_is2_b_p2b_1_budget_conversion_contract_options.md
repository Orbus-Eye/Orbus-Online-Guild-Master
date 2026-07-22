# R18.6.RV3-IS2-B-P2B-1 · Budget Conversion Discovery & Contract Options (PATCHED · PM VERDICTS INTEGRATED)

**Gate ID:** R18.6.RV3-IS2-B-P2B-1  
**Regime:** DOCUMENTAL_ONLY · READ-ONLY DISCOVERY · NO_APPLY · Italian_only  
**Artifact Status:** `PATCHED_PM_VERDICTS_INTEGRATED_Q01_Q12_RESOLVED_MODEL_AT_LOCKED`  
**Model Selected:** `MODEL A-T · EQUAL-COST TRANSITIONAL` · **DESIGN-LOCKED**  
**Anchor `lore_meta.py` SHA256:** `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`  
**Created UTC (patch):** 2026-07-22T14:39:42.459953+00:00  
**PM Verdict Reference:** `PM_VERDICT_MSG_P2B1_ADJUDICATION`

---

## 01 · Executive Summary (post-verdict)
Discovery read-only del runtime completata. PM VERDICT integrato: **MODEL A-T · EQUAL-COST TRANSITIONAL** SELECTED e DESIGN-LOCKED (flat-stat scope). Q01-Q12 tutte RESOLVED · 0 blocking open questions residue. Costi unitari DESIGN-LOCKED: Intelligenza=1.00 · Costituzione=1.00 · Destrezza=1.00 budget unit/point. Mapping IT↔runtime DESIGN-LOCKED: Intelligenza↔intellect · Costituzione↔endurance · Destrezza↔agility · Strength/Faith INELIGIBLE per CdV. Soft-cap Int 100 con effective_return=0.50 oltre cap (loadout-level, NOT_IMPLEMENTED runtime). Proc/durata/cooldown = DEFERRED (`PROC_COST_RUNTIME_DEPENDENT`, `UPTIME_MODEL_RUNTIME_DEPENDENT`). Affix eligibility cost=0. Over-budget tolerance=0 · unspent ≤5%. Legendary unique-effect ≤30% gross (derivazione 0.50×0.60). Model B NOT_SELECTED (evidence-insufficient); Model C BLOCKED_BY_EVIDENCE. Runtime extension REQUIRED prima di effect assignment: gate futuro RT1 PLANNED/HOLD/NOT_AUTHORIZED. Runtime gaps rimangono prerequisiti espliciti, NON dichiarati implementati.

## 02 · Scope
In scope: discovery read-only + Q01-Q12 verdict integration + Model A-T locking.  
Out of scope: item-level cost assignment, effect assignment, runtime code changes, closure manifest emission (delegato in fase closure), PRD append (delegato in fase closure).

## 03 · Governance
- Documental only · read-only discovery · no apply
- Modifiche a backend/frontend/OpenAPI/DB/registry/test/env/sigilli: 0
- Sealed scripts byte-identical: 36/36
- `lore_meta.py` invariante: `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`
- SHA Policy §31 compliant
- Phase 2A/P1-N1/Phase 1/IS2-A chain: IMMUTABLE

## 04 · Source Chain
Contract options basato su: Phase 1 contract · Addendum P1-N1 · Phase 2A envelope + closure · IS2-A Rev-4 + L1 · IS1 corpus 120 unit.

## 05 · Runtime Discovery
11 file esaminati read-only in `/app/backend/`. Formule verbatim:
- `adventurer_base_power = Σ(str,agi,int,end,faith) + level*2` · marginal cost 1.0/point uniforme
- `item_equip_power = Σ(5_bonus_fields) + power_score`
- `success_chance = 50 + (team - recommended)` clamp `[10,95]`
- `auto_equip fitness weights`: `PRIMARY=3.0 · SECONDARY=1.5 · POWER=1.0` (ranking only, non power formula)

Runtime stats canonical (5, English): `strength, agility, intellect, endurance, faith`. Design layer stats CdV (Italian, 3): `Intelligenza, Costituzione, Destrezza`.

## 06 · Stat Formula Discovery
Power formula lineare · marginal cost 1.0/point uniforme · no soft cap runtime · no diminishing returns · no stat-specific damage/mitigation.

## 07 · Existing Item Distribution
5 bonus fields + `power_score`. NO `proc_chance`, `duration`, `cooldown`, mark/drain/fragment, weapon_coefficient, slot_band_multiplier runtime.

## 08 · Soft Cap Discovery
Phase 1 §7 `soft_cap_intelligenza=100`. Runtime evidence implementation: **NONE**.

## 09 · Intelligenza Valuation (PM VERDICT Q01+Q02 INTEGRATED)
- **PM Verdict Q01 (pre-soft-cap)**: point cost = **1.00** budget unit · range `equipped total Intelligence ≤ 100` · **DESIGN_LOCKED**
- **PM Verdict Q02 (post-soft-cap)**:
  - nominal item-point cost = **1.00** (invariato)
  - effective contribution above 100 = **0.50** per nominal point
  - effective cost above 100 = **2.00** budget units per 1 effective Intelligence
  - scaling post-cap = **LOADOUT-LEVEL, NON item-level**
  - runtime status = **NOT_IMPLEMENTED** · nessun item pronto per live finche' non implementato+testato
- Model A-T cost = **1.00**

## 10 · Costituzione Valuation (PM VERDICT Q03 INTEGRATED)
- **PM Verdict Q03**: point cost = **1.00** budget unit · runtime mapping = **`Endurance`** · **DESIGN_LOCKED**
- Assunzioni vietate: `health_scaling · mitigation_scaling · stoffa_cuoio_runtime_differential · interruption_resistance` (richiedono evidence o implementazione futura)
- Model A-T cost = **1.00**

## 11 · Destrezza Valuation (PM VERDICT Q04 INTEGRATED)
- **PM Verdict Q04**: point cost = **1.00** budget unit · runtime mapping = **`Agility`** · **TRANSITIONAL_DESIGN_LOCK**
- Semantica attuale: `generic_base_power_contribution_only`
- NON attribuire a Destrezza: `precisione · critico · velocita · schivata · proc_chance · potenza_balestra · potenza_pugnale` (non implementate)
- Preservare: `Dex-primary CdV = FORBIDDEN` · `dual-primary Int/Dex = FORBIDDEN`
- **Safeguard identita'**:
  - `Dexterity share ≤ 20% del flat-stat budget`
  - `Dexterity budget < Intelligence budget` per ogni item class-specific CdV
  - Nota: limite di identita', **NON prova di efficacia runtime**
- Blocker `DEX_CONVERSION_UNDERDEFINED` = **RESOLVED_TRANSITIONALLY**
- Model A-T cost = **1.00**

## 12 · Model A-T · Equal-Cost Transitional (SELECTED · DESIGN-LOCKED)
- **PM Verdict**: `SELECTED_AS_MODEL_A_T_EQUAL_COST_TRANSITIONAL_DESIGN_LOCKED`
- `cost_per_int_unit = 1.00 · cost_per_cost_unit = 1.00 · cost_per_dex_unit = 1.00`
- **Scope FINAL**: flat-stat only
- **Scope INCOMPLETE / RUNTIME-DEPENDENT**: effects, proc, duration, cooldown, mark, drain, fragment
- Soft-cap treatment: **loadout-level effective_return=0.50 above 100** · runtime **NOT_IMPLEMENTED**
- **Motivo selezione (PM verbatim)**: coincide col valore marginale runtime osservato · deterministico · sostiene envelope bassi · evita pesi inventati · calibrazione futura senza alterare Phase 2A.

## 13 · Model B · Role-Weighted (NOT_SELECTED)
- **PM Verdict**: `NOT_SELECTED`
- **Motivo verbatim**: `ROLE_WEIGHTS_NON_SUPPORTATI_DA_EVIDENZA_RUNTIME`
- Preservato nel report come opzione analizzata · **NON APPLICARE**

## 14 · Model C · Marginal-Effectiveness Calibrated (BLOCKED_BY_EVIDENCE)
- **PM Verdict**: `BLOCKED_BY_EVIDENCE`
- Blocker `RUNTIME_STAT_VALUE_EVIDENCE_MISSING` = **ACKNOWLEDGED_RESOLVED_BY_TRANSITIONAL_MODEL_AND_RUNTIME_HOLD**
- Rivalutabile solo dopo: formule stat-specifiche · telemetria · simulazioni · runtime implementation dedicata

## 15 · Model Comparison (post-verdict)
| Modello | Status | Note |
|---|---|---|
| A-T | **SELECTED · DESIGN-LOCKED** | flat-stat scope · transitional |
| B   | NOT_SELECTED | role weights non supportati da evidenza runtime |
| C   | BLOCKED_BY_EVIDENCE | acknowledged/resolved transitionally |

## 16 · Low-Envelope Simulation (T1 Band C Common + MIN extreme)
Simulazioni Model A-T. Envelope T1 Band C Common `= 25 × 0.55 × 1.00 × 1.00 = 13.7500`. MIN extreme (T1 Band B Common) `= 17.5000` preserved da Phase 2A. Dettagli dry-run in JSON §16.

## 17 · Mid-Envelope Simulation (T2 Band A Uncommon · T3 Band S Rare)
Simulazioni Model A-T. T2 Band A Uncommon `= 55 × 0.85 × 1.00 × 1.15 = 53.7625`. T3 Band S Rare `= 95 × 1.00 × 1.00 × 1.35 = 128.2500`. Dettagli dry-run in JSON §17.

## 18 · High-Envelope Simulation (T4 Band B Epic · T5 Band S Legendary + MAX extreme)
Simulazioni Model A-T. T4 Band B Epic `= 145 × 0.70 × 1.00 × 1.60 = 162.4000`. T5 Band S Legendary (focus/chest) `= 185 × 1.00 × 1.00 × 1.85 = 342.2500` (coincide con MAX extreme). Dettagli dry-run in JSON §18.

## 19 · Effect Taxonomy Costing (13 categorie · methodology only)
Formula concettuale documentata. Applicazione numerica DEFERRED (vedi §22/§23 verdetti Q05/Q06). PAYOFF_UTILITY internal-only.

## 20 · Magnitude Costing
Baseline flat stat = 1.00 (allineato Model A-T). Percent/damage/defense costings: DEFERRED runtime.

## 21 · Uptime Costing
Methodology documentata. Uptime factor concettuale. Applicazione numerica DEFERRED (Q06).

## 22 · Proc Costing (PM VERDICT Q05 INTEGRATED)
- **PM Verdict Q05**: numeric proc conversion **NOT RATIFIED** · item-level proc assignment **FORBIDDEN**
- Ragione: `proc_trigger_frequency · event_rate · internal_cooldown · target_eligibility · runtime_execution_semantics` = **MISSING**
- Combined proc cap 45% resta **DESIGN-LOCKED** ma insufficiente per costo per punto
- **Classificazione verbatim**: `PROC_COST_RUNTIME_DEPENDENT`
- Deferimento obbligatorio · **NO valore inventato**

## 23 · Duration Costing (PM VERDICT Q06 INTEGRATED)
- **PM Verdict Q06**: duration/cooldown/uptime conversion **NOT RATIFIED**
- Un costo valido richiede almeno: `expected_uptime · trigger_frequency · proc_chance · duration · cooldown · refresh_behavior · stack_behavior`
- Finche' non esistono: `duration=null · cooldown=null · proc_chance=null` per tutti gli item
- **Classificazione verbatim**: `UPTIME_MODEL_RUNTIME_DEPENDENT`

## 24 · Cooldown Costing
Vedi §23 (Q06 shared). Cooldown = null per tutti gli item. Classificazione `UPTIME_MODEL_RUNTIME_DEPENDENT`.

## 25 · Scope & Reliability Factors
Methodology documentata. Applicazione numerica DEFERRED.

## 26 · Stacking Interaction
Da Phase 1 §48 (Q05 DESIGN_LOCKED preservato). ADDITIVE_BEFORE_CAP procs · REFRESH durations · NON_STACKING same-family.

## 27 · Boss Safeguard Costing
Boss safeguard required flag preservato per ANTI_SUMMON · DISPEL_UTILITY · ANTI_INCORPOREAL. Cost quantitativo DEFERRED.

## 28 · Utility Costing
Utility share caps preservati (non_legendary=40% · legendary=50% del combined ceiling). Costing numerico DEFERRED.

## 29 · Affix Costing (PM VERDICT Q07 INTEGRATED)
- **PM Verdict Q07**: **`affix_eligibility_cost = 0`**
- Uno slot affix disponibile **NON consuma budget da solo**
- Il contenuto futuro consumera' budget secondo natura: `flat-stat · effect · utility`
- Preservare: `affix_eligibility ≠ affix_assignment`
- `affix_budget_reserved = null`
- **NON applicare** tassa fissa per slot affix
- **NON selezionare** affix in P2B-1

## 30 · Legendary Costing Methodology (PM VERDICT Q12 INTEGRATED)
- **PM Verdict Q12**: Legendary unique-effect **maximum = 30% del gross item budget**
- **Derivazione verbatim**: `Legendary combined effect+utility ceiling = 50% gross · unique effect share ≤ 60% del combined ceiling · 0.50 × 0.60 = 0.30 gross`
- L'effetto unico: **incluso nel combined ceiling** · **NON bonus esterno** · **NO surcharge PM_SELECTED** · **NON superabile via affix**
- Per le 3 Legendary (Veste di Onirade · Occhio del Faro Rovesciato · Balestra della Traiettoria certa): `final_effect=null · effect_value=null`

## 31 · Rounding & Residue
4-decimal internal precision · ROUND_HALF_UP final · residue assignment: main_stat_intelligenza → costituzione. No extra budget from residues.

## 32 · Spend Tolerance (PM VERDICT Q08 INTEGRATED)
- **PM Verdict Q08**:
  - `over_budget_tolerance = 0` · un item **NON puo' superare** gross envelope
  - Target futuro: `budget spend ratio = 95%-100%`
  - Unspent budget: **≤ 5% = ACCEPTABLE** · **> 5% = PM_REVIEW**
  - Residuo tecnico: `< 1.00 budget unit = ROUNDING_RESIDUE_ALLOWED`
- Il residuo: **NON trasferito ad altri item** · **NON genera potenza gratuita** · puo' rimanere inutilizzato

## 33 · Anti-Double-Counting
Preservato da Phase 1 §14: single_source_of_power · rarity_multiplier once at total · each_component_consumes_same_total · no_affix_replication_across_families · unspent_budget_does_not_become_extra_external_power.

## 34 · Risk Register (post-verdict)
- R1 `runtime_stat_marginal_evidence_missing`: **ACKNOWLEDGED_RESOLVED_BY_TRANSITIONAL_MODEL_AND_RUNTIME_HOLD**
- R5 `dex_semantics_underdefined`: **RESOLVED_TRANSITIONALLY_via_agility_mapping_and_identity_safeguards**
- R2-R4, R6-R11: preservati con mitigations documentate

## 35 · PM Open Questions (12/12 RESOLVED · 0 blocking · 0 open)
| # | id | status | resolution_summary (verbatim key points) |
|--:|---|---|---|
| 01 | P2B1_Q01 | **RESOLVED** | Int cost=1.00 · range ≤100 · DESIGN_LOCKED |
| 02 | P2B1_Q02 | **RESOLVED** | nominal 1.00 · effective_return 0.50 above 100 · effective_cost 2.00 · loadout-level · NOT_IMPLEMENTED |
| 03 | P2B1_Q03 | **RESOLVED** | Cost=1.00 · runtime=Endurance · forbidden assumptions · DESIGN_LOCKED |
| 04 | P2B1_Q04 | **RESOLVED** | Dex=1.00 · runtime=Agility · TRANSITIONAL_DESIGN_LOCK · Dex_share ≤20% · Dex<Int budget |
| 05 | P2B1_Q05 | **RESOLVED** | proc numeric NOT_RATIFIED · assignment FORBIDDEN · PROC_COST_RUNTIME_DEPENDENT · deferred |
| 06 | P2B1_Q06 | **RESOLVED** | duration/cooldown/uptime NOT_RATIFIED · all null · UPTIME_MODEL_RUNTIME_DEPENDENT · deferred |
| 07 | P2B1_Q07 | **RESOLVED** | affix_eligibility_cost=0 · no fixed tax · affix_budget_reserved=null · no selection |
| 08 | P2B1_Q08 | **RESOLVED** | over_budget=0 · target 95-100% · unspent ≤5% ACCEPTABLE · rounding_residue<1 ALLOWED |
| 09 | P2B1_Q09 | **RESOLVED** | Model A-T SELECTED · flat-stat scope FINAL · effect scope INCOMPLETE runtime-dependent |
| 10 | P2B1_Q10 | **RESOLVED** | IT↔runtime bridge DESIGN-LOCKED · Int/Cost/Dex mapping · Str/Faith INELIGIBLE per CdV |
| 11 | P2B1_Q11 | **RESOLVED** | Runtime extension REQUIRED · gate RT1 (doc) + RT2 (code) SEPARATI · P2B-1 no code |
| 12 | P2B1_Q12 | **RESOLVED** | Legendary unique_effect ≤30% gross (0.50×0.60) · incluso in ceiling · no external · no surcharge |

## 36 · Recommended Model (post-verdict)
- **PM Final Selection**: `MODEL A-T · EQUAL-COST TRANSITIONAL · DESIGN-LOCKED`
- Scope final: `flat_stat_only`
- Scope incomplete runtime-dependent: `proc · duration · cooldown · mark · drain · fragment · legendary_final_effect`
- Agent recommendation upheld: **True**

## 37 · Phase 2B Readiness
- Phase 2B: **HOLD_NOT_AUTHORIZED**
- Runtime extension REQUIRED prima di effect assignment
- Gate futuri (planned/hold):
  - `R18.6.RV3-IS2-B-P2B-RT1` · RUNTIME STAT & EFFECT SEMANTICS SPECIFICATION · DOCUMENTAL_ONLY · **PLANNED_HOLD_NOT_AUTHORIZED**
  - `R18.6.RV3-IS2-B-P2B-RT2` · RUNTIME IMPLEMENTATION · REQUIRES_SEPARATE_PM_AUTHORIZATION · **NOT_AUTHORIZED**

## 38 · GO/HOLD Recommendation (post-verdict)
- **Agent recommendation**: `CLOSURE_READY_PM_APPROVED_Q01_Q12_RESOLVED`
- **Artifact Status**: `PATCHED_PM_VERDICTS_INTEGRATED_MODEL_A_T_LOCKED`
- Closure manifest emission: **True** (in same dispatch)
- PRD append emission: **True** (in same dispatch)
- Next action: `R18.6.RV3-IS2-B-P2B-1_FORMAL_CLOSURE_SAME_DISPATCH`
- **Blockers status**:
  - `RUNTIME_STAT_VALUE_EVIDENCE_MISSING` = `ACKNOWLEDGED_RESOLVED_BY_TRANSITIONAL_MODEL_AND_RUNTIME_HOLD`
  - `DEX_CONVERSION_UNDERDEFINED` = `RESOLVED_TRANSITIONALLY_via_agility_mapping_and_identity_safeguards`
- **Runtime gaps rimangono prerequisiti espliciti** · NON dichiarati implementati

---

**PM VERDICTS INTEGRATED · Q01-Q12 RESOLVED · MODEL A-T LOCKED · READY FOR FORMAL CLOSURE.**
