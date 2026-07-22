# R18.6.RV3-IS2-B-P2B-1 · Final Closure Report

**Gate ID:** R18.6.RV3-IS2-B-P2B-1  
**Regime:** DOCUMENTAL_ONLY · READ-ONLY DISCOVERY · NO_APPLY · Italian_only  
**Closure Status:** `CLOSED_PM_LOCKED`  
**Anchor `lore_meta.py` SHA256:** `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` · **INVARIANT**  
**Created UTC:** 2026-07-22T14:39:42.459953+00:00

---

## 01 · Discovery Evidence
11 file backend esaminati read-only (`expeditions/formulas.py` · `equipment/{services,auto_equip}.py` · `adventurers/{common,services,generator}.py` · `stats/public_catalog.py` · `items/services.py` · `inventory/services.py` · `shared/constants.py` · `content/lore_meta.py`). Formule chiave: `adventurer_base_power = Σ(str,agi,int,end,faith) + level*2` · `item_equip_power = Σ(5_bonus_fields) + power_score` · `success_chance = 50 + (team-recommended)` clamp `[10,95]`. **Gap runtime**: no soft-cap, no proc engine, no duration/cooldown item, no mark/drain/fragment taxonomy, no weapon_coefficient runtime, no slot_band_multiplier runtime, no damage/mitigation stat-specifiche.

## 02 · PM Verdict
Model A-T · Equal-Cost Transitional **SELECTED** · **DESIGN-LOCKED**. Q01-Q12 tutte adjudicate (12/12 RESOLVED). Runtime extension REQUIRED prima di effect assignment (gate RT1 + RT2 futuri).

## 03 · P2B-1 CLOSED
Gate `R18.6.RV3-IS2-B-P2B-1` = **CLOSED_PM_LOCKED_MODEL_A_T**. Same-dispatch closure autorizzata dal PM.

## 04 · Model A-T Selected
`MODEL A-T · EQUAL-COST TRANSITIONAL · DESIGN-LOCKED`. Flat-stat scope final. Effect scope INCOMPLETE/RUNTIME-DEPENDENT.

## 05 · Equal Flat-Stat Cost
`cost_per_int_unit = 1.00 · cost_per_cost_unit = 1.00 · cost_per_dex_unit = 1.00` budget unit per nominal point.

## 06 · Int Soft-Cap Design Treatment
- Soft cap Intelligenza: **100** (Phase 1 §7)
- Nominal item-point cost above 100 = **1.00** (invariato)
- Effective contribution above 100 = **0.50** per nominal point (**loadout-level**, non item-level)
- Effective cost above 100 = **2.00** budget units per 1 effective Intelligence
- Runtime status: **NOT_IMPLEMENTED**
- Nessun item pronto per live finche' non implementato+testato

## 07 · Constitution Mapping
- Costituzione point_cost = **1.00**
- Runtime mapping verbatim = **`Endurance`**
- Assunzioni vietate: `health_scaling · mitigation_scaling · stoffa_cuoio_runtime_differential · interruption_resistance`

## 08 · Dexterity Mapping and Safeguard
- Destrezza point_cost = **1.00**
- Runtime mapping verbatim = **`Agility`**
- Status: `TRANSITIONAL_DESIGN_LOCK`
- Semantica attuale: `generic_base_power_contribution_only`
- **Preserved forbiddens**: Dex-primary CdV = FORBIDDEN · dual-primary Int/Dex = FORBIDDEN
- **Identity safeguards**: Dexterity share ≤ **20%** flat-stat budget · Dexterity budget < Intelligence budget per ogni item class-specific CdV

## 09 · Italian/Runtime Bridge (DESIGN-LOCKED)
| Italian (design) | Runtime (canonical) |
|---|---|
| Intelligenza | `intelligence / int` |
| Costituzione | `endurance / end` |
| Destrezza | `agility / agi` |
| — | `Strength = INELIGIBLE` per CdV |
| — | `Faith = INELIGIBLE` per CdV |

Runtime localization NOT_IMPLEMENTED. CANONICAL DESIGN BRIDGE = DESIGN-LOCKED. Vietato fallback impliciti o mapping per somiglianza non documentato.

## 10 · Model B Not Selected
`Model B · Role-Weighted` = **NOT_SELECTED**. Motivo verbatim: `ROLE_WEIGHTS_NON_SUPPORTATI_DA_EVIDENZA_RUNTIME`. Preservato nel report P2B-1 come opzione analizzata, **NON applicabile**.

## 11 · Model C Blocked
`Model C · Marginal-Effectiveness Calibrated` = **BLOCKED_BY_EVIDENCE**. Blocker `RUNTIME_STAT_VALUE_EVIDENCE_MISSING` acknowledged. Rivalutabile solo dopo: formule stat-specifiche, telemetria, simulazioni, runtime implementation dedicata.

## 12 · Proc Conversion Deferred (`PROC_COST_RUNTIME_DEPENDENT`)
Numeric proc conversion **NOT RATIFIED**. Item-level proc assignment **FORBIDDEN**. Missing runtime elements: `proc_trigger_frequency · event_rate · internal_cooldown · target_eligibility · runtime_execution_semantics`. Combined proc cap 45% resta DESIGN-LOCKED ma insufficiente per costo per punto.

## 13 · Duration/Cooldown Conversion Deferred (`UPTIME_MODEL_RUNTIME_DEPENDENT`)
Duration/cooldown/uptime conversion **NOT RATIFIED**. Finche' runtime elements mancano (`expected_uptime · trigger_frequency · proc_chance · duration · cooldown · refresh_behavior · stack_behavior`), tutti gli item: `duration=null · cooldown=null · proc_chance=null`.

## 14 · Affix Eligibility Cost Zero
`affix_eligibility_cost = 0`. Uno slot affix disponibile **NON consuma budget da solo**. Contenuto futuro consuma per natura (flat-stat/effect/utility). `affix_budget_reserved = null`. `affix_eligibility ≠ affix_assignment` preservato. Nessuna tassa fissa per slot affix. Nessuna selezione affix in P2B-1.

## 15 · Spend Tolerance
- `over_budget_tolerance = 0` (strict, un item non puo' superare gross envelope)
- Target future budget spend ratio: **95%-100%**
- Unspent budget: **≤ 5% = ACCEPTABLE** · **> 5% = PM_REVIEW**
- Rounding residue: **< 1.00 budget unit = ROUNDING_RESIDUE_ALLOWED**
- Residuo: NON trasferibile · NON genera potenza gratuita · puo' rimanere inutilizzato

## 16 · Legendary Unique-Effect Ceiling
`legendary_unique_effect ≤ 30%` del gross item budget.  
**Derivazione verbatim**: `0.50` (Legendary combined effect+utility ceiling) × `0.60` (unique effect share of combined) = **`0.30` gross**.  
L'effetto unico: **incluso nel combined ceiling** · **NON bonus esterno** · **NO surcharge PM_SELECTED** · **NON superabile via affix**.  
Per le 3 Legendary (`cdv_t5_chest_stoffa_001` Veste di Onirade · `cdv_t5_main_hand_focus_001` Occhio del Faro Rovesciato · `cdv_t5_main_hand_balestra_001` Balestra della Traiettoria certa): `final_effect=null · effect_value=null`.

## 17 · Runtime Extension Boundary
Runtime extension **REQUIRED** prima di autorizzare: proc item-driven · durata item-driven · cooldown item-driven · diminishing returns oltre Int 100 · Mark/Drain/Fragment item interactions · effetti Legendary finali.

Prossima estensione in **DUE GATE SEPARATI**:
| Gate | Titolo | Regime | Status |
|---|---|---|---|
| `R18.6.RV3-IS2-B-P2B-RT1` | RUNTIME STAT & EFFECT SEMANTICS SPECIFICATION | DOCUMENTAL_ONLY | **PLANNED_HOLD_NOT_AUTHORIZED** |
| `R18.6.RV3-IS2-B-P2B-RT2` | RUNTIME IMPLEMENTATION (code/test/migration) | REQUIRES_SEPARATE_PM_AUTHORIZATION | **NOT_AUTHORIZED** |

**P2B-1 non autorizza codice**.

## 18 · All Twelve PM Questions Resolved
Q01-Q12 = **12/12 RESOLVED · 0 blocking open**. Dettaglio resolution_summary in P2B-1 patched contract §35.

## 19 · Item-Level Assignments Remain Zero
Per tutte le 120 unit del corpus: `proc_chance=null · duration=null · cooldown=null · effect_value=null · main_stat_value=null · constitution_value=null · dexterity_value=null · other_stat_value=null · selected_affix=null · affix_value=null · effect_family_selected=null · final_effect=null`.

## 20 · Phase 2B Remains HOLD
`R18.6.RV3-IS2-B_Phase_2B` = **HOLD_NOT_AUTHORIZED**. Prerequisite: runtime extension (RT1+RT2).

## 21 · Governance Evidence (tutti zero)
- backend_modifications: **0**
- frontend_modifications: **0**
- openapi_modifications: **0**
- db_registry_modifications: **0**
- test_suite_modifications: **0**
- env_secrets_modifications: **0**
- sealed_set_modifications: **0**
- new_seals_created: **0**
- db_writes: **0**
- runtime_item_id_generated_count: **0**
- item_generation: **0**
- registry_generation: **0**
- registry_apply: **0**
- sealed scripts byte-identical: **36/36**
- `lore_meta.py` SHA256 invariant: `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`

## 22 · Explicit STOP
| Item | Status |
|---|---|
| `R18.6.RV3-IS2-B-P2B-1` | **CLOSED_PM_LOCKED_MODEL_A_T** |
| `R18.6.RV3-IS2-B-P2B-RT1` | PLANNED_HOLD_NOT_AUTHORIZED (registrato, non aperto) |
| `R18.6.RV3-IS2-B-P2B-RT2` | NOT_AUTHORIZED |
| `R18.6.RV3-IS2-B_Phase_2A` | CLOSED_PM_LOCKED_IMMUTABLE |
| `R18.6.RV3-IS2-B-Phase-1-N1` | DESIGN_LOCKED_PM_APPROVED_IMMUTABLE |
| `R18.6.RV3-IS2-B_Phase_1` | IMMUTABLE_UNCHANGED |
| `R18.6.RV3-IS2-B_Phase_2B` | HOLD_NOT_AUTHORIZED |
| `R18.6.RV3-NC1` | HOLD |
| `R18.6_Gate_11` | HOLD |
| `Monaco` | HOLD |
| `Registry v3 Item Generation & Apply` | NOT_AUTHORIZED |
| `AFX2` | RESERVED_FUTURE_NOT_AUTHORIZED |
| `IS2-A branch` | LOCKED_IMMUTABLE |
| `Cacciatore del Vuoto` | ACTIVE-DESIGN-READY (design layer only) |
| Runtime gaps | **PREREQUISITE_EXPLICIT_NOT_IMPLEMENTED** |

---

**ATTENDO VERDICT PM.**
