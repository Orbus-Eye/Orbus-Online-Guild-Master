# R18.6.RV3-IS2-B · Phase 2A · Per-Item Budget Envelope Projection

**Gate ID:** R18.6.RV3-IS2-B_Phase_2A  
**Regime:** DOCUMENTAL_ONLY · READ_ONLY · NO_APPLY  
**Lingua:** Italiano  
**Artifact Status:** `ARTIFACT_WRITTEN_PENDING_PM_ADJUDICATION`  
**Closure Manifest Authorized:** `False`  
**PRD Append Authorized:** `False`  
**Anchor `lore_meta.py` SHA256:** `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`  
**Created UTC:** 2026-07-22T09:07:26.414393+00:00  
**PM Dispatch:** Message 92 · Section 16 · Resume Conditional Phase 2A  
**Addendum Reference:** R18.6.RV3-IS2-B-Phase-1-N1

---

## 01 · Executive Summary
Proiezione deterministica degli envelope di budget per **120 blueprint units**. Applica la formula del Contratto Phase 1 §16 con la scala numerica DESIGN_LOCKED dell'Addendum P1-N1 (T1=25 · T2=55 · T3=95 · T4=145 · T5=185). Nessuna assegnazione item-level: **12 campi item-level preservati `null`**. Artifact in stato `ARTIFACT_WRITTEN_PENDING_PM_ADJUDICATION`. **Nessun** closure manifest e **nessun** PRD append emessi per Fase 2A.

## 02 · Scope
**In scope**: computo deterministico envelope per 120 unita', audit fattibilita', audit monotonicita', audit riconciliazione, audit null-field.  
**Out of scope**: assegnazioni item-level, selezione affix, effetti finali Legendary, generazione Registry, apply runtime, DB writes, modifiche sealed scripts, closure manifest, PRD append.

## 03 · Governance
- `documental_only=True · read_only=True · no_apply=True`
- Modifiche a backend/frontend/OpenAPI/DB/registry/test/env/sigilli: **0**
- Sealed scripts byte-identical attesi: **36/36**
- `lore_meta.py` SHA256 invariante: `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`
- Compliance SHA Policy §31: True
- Phase 1 Contract files IMMUTABILI: True
- Addendum P1-N1 files IMMUTABILI post-creazione: True

## 04 · Source of Truth
- Contratto Phase 1: `r18_6_rv3_is2_b_phase1_stat_budget_mechanical_effect_contract.json`
- Addendum P1-N1: `r18_6_rv3_is2_b_phase1_n1_tier_reference_budget_addendum.json`
- Corpus 120: `r18_6_rv3_is1_item_specification_roster_contract.json::roster_120_units`
- Legendary L1: `r18_6_rv3_is2_a_l1_legendary_candidate_selection_report.json`
- Roster Rev-4: `r18_6_rv3_is2_a_phase2_full_identity_naming_lore_roster_rev4.json`

## 05 · Addendum Reference
- Gate ID: `R18.6.RV3-IS2-B-Phase-1-N1`
- Scala: T1=25 · T2=55 · T3=95 · T4=145 · T5=185
- Status per tier: `DESIGN_LOCKED`
- Derivazione: `WORST_CASE_MAIN_STAT_FEASIBILITY`

## 06 · Formula Declaration
```
tier_reference_budget × slot_band_multiplier × weapon_coefficient_if_applicable × rarity_multiplier = TOTAL_ITEM_BUDGET
```
- Ogni moltiplicatore applicato UNA sola volta
- Precisione interna: 4 decimali
- Nessun arrotondamento intermedio
- Rounding finale: `ROUND_HALF_UP`
- Ordine locked: `base_budget → slot_multiplier → weapon_coefficient → rarity_multiplier → budget_split → final_rounding`

## 07 · Lookup · Tier Reference Budget
| Tier | Budget |
|------|-------:|
| T1   | 25 |
| T2   | 55 |
| T3   | 95 |
| T4   | 145 |
| T5   | 185 |

## 08 · Lookup · Slot Band Multiplier
| Band | Weight | Slots |
|------|-------:|-------|
| S | 1.00 | main_hand, chest, legs |
| A | 0.85 | head, shoulders, hands, feet |
| B | 0.70 | neck, back, waist, off_hand |
| C | 0.55 | wrist, ring, accessory |

## 09 · Lookup · Weapon Coefficient
| Family | Coefficient |
|--------|------------:|
| focus | 1.00 |
| balestra | 0.88 |
| pugnale | 0.78 |

## 10 · Lookup · Rarity Multiplier
| Rarity | Multiplier |
|--------|-----------:|
| Common | 1.00 |
| Uncommon | 1.15 |
| Rare | 1.35 |
| Epic | 1.60 |
| Legendary | 1.85 |

## 11 · Lookup · Main Stat Band (Phase 1 §9)
| Tier | min | max |
|------|----:|----:|
| T1 | 10 | 25 |
| T2 | 25 | 45 |
| T3 | 45 | 70 |
| T4 | 70 | 90 |
| T5 | 90 | 115 |

## 12 · Lookup · Affix Slots per Tier
T1=1 · T2=2 · T3=3 · T4=4 · T5=5

## 13 · Lookup · Combined Effect+Utility Ceiling (%)
Common=10 · Uncommon=20 · Rare=30 · Epic=40 · Legendary=50

## 14 · Lookup · Statistical Budget Minimum (%)
Common=90 · Uncommon=80 · Rare=70 · Epic=60 · Legendary=50

## 15 · Lookup · Utility Share Internal Max (%)
non_legendary=40 · legendary=50

## 16 · Null-Preserved Item-Level Fields (12)
`main_stat_value` · `constitution_value` · `dexterity_value` · `other_stat_value` · `selected_affix` · `affix_value` · `effect_family_selected` · `final_effect` · `effect_value` · `proc_chance` · `duration` · `cooldown`

## 17 · Corpus Composition
- Totale attivo: **120**
- Non-legendary NEW_FUTURE: 108
- Preserved REUSE_VALID: 6
- Preserved REUSE_CONDITIONAL: 3
- Legendary PM-selected: 3
- Dormant contingency escluso: **3** (`DORMANT_CONTINGENCY_OUTSIDE_ACTIVE_ROSTER`)

## 18 · Projected Rows Count
`len(projected_rows) = 120`

## 19 · Reconciliation Audit
- Expected: 120 · Projected: 120 · Pass: **True**
- Dormant excluded records: 3 (`DORMANT_CONTINGENCY_OUTSIDE_ACTIVE_ROSTER`)
- Total declared (active + dormant): 123

## 20 · Monotonicity Audit
`25 < 55 < 95 < 145 < 185` · Pass: **True**

## 21 · Worst-Case Main Stat Feasibility Audit
| Tier | budget | band_max §9 | residual | feasible |
|------|-------:|------------:|---------:|----------|
| T1 | 25  | 25  | 0  | True |
| T2 | 55  | 45  | 10 | True |
| T3 | 95  | 70  | 25 | True |
| T4 | 145 | 90  | 55 | True |
| T5 | 185 | 115 | 70 | True |

## 22 · Distribution Audit
- **By tier**: {'T1': 18, 'T2': 22, 'T3': 26, 'T4': 26, 'T5': 28}
- **By rarity**: {'Common': 42, 'Rare': 27, 'Legendary': 3, 'Epic': 15, 'Uncommon': 33}
- **By slot band**: {'A': 29, 'C': 32, 'B': 24, 'S': 35}
- **By equipment category**: {'ARMOR': 60, 'UNIVERSAL': 39, 'WEAPON': 21}
- **By family**: {'stoffa': 42, 'cuoio': 18, 'universal_position': 39, 'focus': 10, 'balestra': 7, 'pugnale': 4}
- **Weapon coefficient distribution**: {'1.0': 109, '0.88': 7, '0.78': 4}

## 23 · Extreme Values Audit
- **Min gross_total_item_budget_raw**: 17.5 · row `cdv_t1_neck_universal_position_001` · T1 neck Common
- **Max gross_total_item_budget_raw**: 342.25 · row `cdv_t5_chest_stoffa_001` · T5 chest Legendary

## 24 · Null Field Audit
- All 12 null-preserved fields = `None` per ciascuna delle 120 righe: **True**
- Per-field null count (expected 120 each): {'main_stat_value': 120, 'constitution_value': 120, 'dexterity_value': 120, 'other_stat_value': 120, 'selected_affix': 120, 'affix_value': 120, 'effect_family_selected': 120, 'final_effect': 120, 'effect_value': 120, 'proc_chance': 120, 'duration': 120, 'cooldown': 120}

## 25 · Legendary Projection Summary (3 units)
| blueprint_code | tier | slot | family | gross_raw | eff+util ceiling | utility_max | effect_max | stat_env_max |
|---|---|---|---|---:|---:|---:|---:|---:|
| cdv_t5_chest_stoffa_001 | T5 | chest | stoffa | 342.2500 | 171.1250 | 85.5625 | 85.5625 | 171.1250 |
| cdv_t5_main_hand_focus_001 | T5 | main_hand | focus | 342.2500 | 171.1250 | 85.5625 | 85.5625 | 171.1250 |
| cdv_t5_main_hand_balestra_001 | T5 | main_hand | balestra | 301.1800 | 150.5900 | 75.2950 | 75.2950 | 150.5900 |

## 26 · Anti-Double-Counting Reaffirmation (Phase 1 §14)
`single_source_of_power=True · each_component_consumes_same_total=True · no_extra_component_outside_total=True · rarity_multiplier_applied_once_at_total_level=True`.

## 27 · Hard Cap Protections Reaffirmation (Phase 1 §36)
`fragments_cap=5 · mark_duration_hard_cap=10 · active_marks_hard_cap=5 · combined_proc_cap_pct=45 · focus_bonus_per_resource_segment=2 · pugnale_ritual_close_bonus_per_mark_application=1 · violated_by_projection=False`.

## 28 · Forbidden Mechanics Reaffirmation (Phase 1 §37)
`resource_cap_increase · active_marks_gt_5 · mark_duration_gt_10 · unmarked_resource_generation · direct_boss_nullification · boss_safeguard_bypass · p2w · dual_int_dex_primary · cross_class_optimal_item · focus_bonus_gt_2_per_segment · ritual_close_bonus_gt_1_per_mark · untested_pvp_effects · cross_phase_persistence · random_full_resource_waste · mechanical_set_bonuses_Q08_DESIGN_LOCKED`.

## 29 · Boss Safeguard Flag Status
`phase_2a_declaration_null_for_all_120_units=True` · downstream declaration phase: `IS2-B_Phase_2B_or_later`.

## 30 · PM Open Questions (Phase 2A)
- Blocking: **0**
- Open: **0**
- Note: la scala numerica T1-T5 dell'Addendum P1-N1 ha risolto completamente `IS2B_P2A_BLOCKER_01`.

## 31 · Fail-Stop Conditions
- Any row `gross_total_item_budget_raw <= 0` → STOP
- Any row missing lookup value → STOP
- Null-field leak into populated state → STOP
- Reconciliation deviation da 120 → STOP
- Monotonicity violation → STOP
- Feasibility failure di qualunque tier → STOP
- Sealed scripts deviazione da 36/36 → STOP_integrity_violation
- Deviazione SHA256 `lore_meta.py` → STOP_anchor_violation

## 32 · Change Ledger
- Phase 1 Contract files changed: **False**
- Addendum P1-N1 files changed: **False**
- Sealed scripts changed: **False**
- `lore_meta.py` changed: **False**
- Runtime apply: **False**
- DB writes: **0**

## 33 · Next Action
- Action ID: `PM_ADJUDICATION_REQUEST_PHASE_2A`
- Requires: `PM_VERDICT_ON_ENVELOPES`
- Closure manifest authorized: **False**
- PRD append authorized: **False**
- Downstream phase on PM GO: `R18.6.RV3-IS2-B_Phase_2B`

## 34 · Projected Rows (120 units · 38 fields per row · 12 preserved null)

Vedi sezione `sections.34_projected_rows` del JSON per il payload completo.  
Tabella riassuntiva (colonne chiave):

| blueprint_code | tier | slot (band) | rarity | weapon_family | wcoef | gross_raw | eff+util | util_max | eff_max | stat_env | affix_slots |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| cdv_t1_head_stoffa_001 | T1 | head (A) | Common | - | 1.00 | 21.2500 | 2.1250 | 0.8500 | 1.2750 | 19.1250 | 1 |
| cdv_t2_head_stoffa_001 | T2 | head (A) | Common | - | 1.00 | 46.7500 | 4.6750 | 1.8700 | 2.8050 | 42.0750 | 2 |
| cdv_t2_head_stoffa_002 | T2 | head (A) | Common | - | 1.00 | 46.7500 | 4.6750 | 1.8700 | 2.8050 | 42.0750 | 2 |
| cdv_t3_head_stoffa_001 | T3 | head (A) | Common | - | 1.00 | 80.7500 | 8.0750 | 3.2300 | 4.8450 | 72.6750 | 3 |
| cdv_t3_head_cuoio_001 | T3 | head (A) | Common | - | 1.00 | 80.7500 | 8.0750 | 3.2300 | 4.8450 | 72.6750 | 3 |
| cdv_t4_head_stoffa_001 | T4 | head (A) | Common | - | 1.00 | 123.2500 | 12.3250 | 4.9300 | 7.3950 | 110.9250 | 4 |
| cdv_t4_head_cuoio_001 | T4 | head (A) | Common | - | 1.00 | 123.2500 | 12.3250 | 4.9300 | 7.3950 | 110.9250 | 4 |
| cdv_t5_head_stoffa_001 | T5 | head (A) | Common | - | 1.00 | 157.2500 | 15.7250 | 6.2900 | 9.4350 | 141.5250 | 5 |
| cdv_t2_accessory_universal_position_002 | T2 | accessory (C) | Rare | - | 1.00 | 40.8375 | 12.2513 | 4.9005 | 7.3508 | 28.5863 | 2 |
| cdv_t2_neck_universal_position_001 | T2 | neck (B) | Common | - | 1.00 | 38.5000 | 3.8500 | 1.5400 | 2.3100 | 34.6500 | 2 |
| cdv_t3_neck_universal_position_001 | T3 | neck (B) | Common | - | 1.00 | 66.5000 | 6.6500 | 2.6600 | 3.9900 | 59.8500 | 3 |
| cdv_t4_neck_universal_position_001 | T4 | neck (B) | Common | - | 1.00 | 101.5000 | 10.1500 | 4.0600 | 6.0900 | 91.3500 | 4 |
| cdv_t5_neck_universal_position_001 | T5 | neck (B) | Common | - | 1.00 | 129.5000 | 12.9500 | 5.1800 | 7.7700 | 116.5500 | 5 |
| cdv_t5_neck_universal_position_002 | T5 | neck (B) | Common | - | 1.00 | 129.5000 | 12.9500 | 5.1800 | 7.7700 | 116.5500 | 5 |
| cdv_t1_shoulders_stoffa_001 | T1 | shoulders (A) | Common | - | 1.00 | 21.2500 | 2.1250 | 0.8500 | 1.2750 | 19.1250 | 1 |
| cdv_t2_shoulders_stoffa_001 | T2 | shoulders (A) | Common | - | 1.00 | 46.7500 | 4.6750 | 1.8700 | 2.8050 | 42.0750 | 2 |
| cdv_t3_shoulders_stoffa_001 | T3 | shoulders (A) | Common | - | 1.00 | 80.7500 | 8.0750 | 3.2300 | 4.8450 | 72.6750 | 3 |
| cdv_t3_shoulders_cuoio_001 | T3 | shoulders (A) | Common | - | 1.00 | 80.7500 | 8.0750 | 3.2300 | 4.8450 | 72.6750 | 3 |
| cdv_t4_shoulders_stoffa_001 | T4 | shoulders (A) | Common | - | 1.00 | 123.2500 | 12.3250 | 4.9300 | 7.3950 | 110.9250 | 4 |
| cdv_t4_shoulders_cuoio_001 | T4 | shoulders (A) | Common | - | 1.00 | 123.2500 | 12.3250 | 4.9300 | 7.3950 | 110.9250 | 4 |
| cdv_t5_shoulders_stoffa_001 | T5 | shoulders (A) | Common | - | 1.00 | 157.2500 | 15.7250 | 6.2900 | 9.4350 | 141.5250 | 5 |
| cdv_t1_chest_stoffa_001 | T1 | chest (S) | Common | - | 1.00 | 25.0000 | 2.5000 | 1.0000 | 1.5000 | 22.5000 | 1 |
| cdv_t1_chest_stoffa_002 | T1 | chest (S) | Common | - | 1.00 | 25.0000 | 2.5000 | 1.0000 | 1.5000 | 22.5000 | 1 |
| cdv_t1_chest_stoffa_003 | T1 | chest (S) | Common | - | 1.00 | 25.0000 | 2.5000 | 1.0000 | 1.5000 | 22.5000 | 1 |
| cdv_t2_chest_stoffa_001 | T2 | chest (S) | Common | - | 1.00 | 55.0000 | 5.5000 | 2.2000 | 3.3000 | 49.5000 | 2 |
| cdv_t2_chest_cuoio_001 | T2 | chest (S) | Common | - | 1.00 | 55.0000 | 5.5000 | 2.2000 | 3.3000 | 49.5000 | 2 |
| cdv_t3_chest_stoffa_001 | T3 | chest (S) | Common | - | 1.00 | 95.0000 | 9.5000 | 3.8000 | 5.7000 | 85.5000 | 3 |
| cdv_t4_chest_stoffa_001 | T4 | chest (S) | Common | - | 1.00 | 145.0000 | 14.5000 | 5.8000 | 8.7000 | 130.5000 | 4 |
| cdv_t4_chest_cuoio_001 | T4 | chest (S) | Common | - | 1.00 | 145.0000 | 14.5000 | 5.8000 | 8.7000 | 130.5000 | 4 |
| cdv_t5_chest_stoffa_001 | T5 | chest (S) | Legendary | - | 1.00 | 342.2500 | 171.1250 | 85.5625 | 85.5625 | 171.1250 | 5 |
| cdv_t5_chest_cuoio_001 | T5 | chest (S) | Common | - | 1.00 | 185.0000 | 18.5000 | 7.4000 | 11.1000 | 166.5000 | 5 |
| cdv_t3_accessory_universal_position_001 | T3 | accessory (C) | Epic | - | 1.00 | 83.6000 | 33.4400 | 13.3760 | 20.0640 | 50.1600 | 3 |
| cdv_t2_back_universal_position_001 | T2 | back (B) | Common | - | 1.00 | 38.5000 | 3.8500 | 1.5400 | 2.3100 | 34.6500 | 2 |
| cdv_t3_back_universal_position_001 | T3 | back (B) | Common | - | 1.00 | 66.5000 | 6.6500 | 2.6600 | 3.9900 | 59.8500 | 3 |
| cdv_t4_back_universal_position_001 | T4 | back (B) | Common | - | 1.00 | 101.5000 | 10.1500 | 4.0600 | 6.0900 | 91.3500 | 4 |
| cdv_t5_back_universal_position_001 | T5 | back (B) | Common | - | 1.00 | 129.5000 | 12.9500 | 5.1800 | 7.7700 | 116.5500 | 5 |
| cdv_t5_back_universal_position_002 | T5 | back (B) | Common | - | 1.00 | 129.5000 | 12.9500 | 5.1800 | 7.7700 | 116.5500 | 5 |
| cdv_t2_accessory_universal_position_003 | T2 | accessory (C) | Epic | - | 1.00 | 48.4000 | 19.3600 | 7.7440 | 11.6160 | 29.0400 | 2 |
| cdv_t2_hands_stoffa_001 | T2 | hands (A) | Common | - | 1.00 | 46.7500 | 4.6750 | 1.8700 | 2.8050 | 42.0750 | 2 |
| cdv_t3_hands_stoffa_001 | T3 | hands (A) | Common | - | 1.00 | 80.7500 | 8.0750 | 3.2300 | 4.8450 | 72.6750 | 3 |
| cdv_t3_hands_cuoio_001 | T3 | hands (A) | Common | - | 1.00 | 80.7500 | 8.0750 | 3.2300 | 4.8450 | 72.6750 | 3 |
| cdv_t4_hands_stoffa_001 | T4 | hands (A) | Common | - | 1.00 | 123.2500 | 12.3250 | 4.9300 | 7.3950 | 110.9250 | 4 |
| cdv_t5_hands_stoffa_001 | T5 | hands (A) | Common | - | 1.00 | 157.2500 | 15.7250 | 6.2900 | 9.4350 | 141.5250 | 5 |
| cdv_t5_hands_cuoio_001 | T5 | hands (A) | Uncommon | - | 1.00 | 180.8375 | 36.1675 | 14.4670 | 21.7005 | 144.6700 | 5 |
| cdv_t2_wrist_stoffa_001 | T2 | wrist (C) | Uncommon | - | 1.00 | 34.7875 | 6.9575 | 2.7830 | 4.1745 | 27.8300 | 2 |
| cdv_t2_wrist_cuoio_001 | T2 | wrist (C) | Uncommon | - | 1.00 | 34.7875 | 6.9575 | 2.7830 | 4.1745 | 27.8300 | 2 |
| cdv_t3_wrist_stoffa_001 | T3 | wrist (C) | Uncommon | - | 1.00 | 60.0875 | 12.0175 | 4.8070 | 7.2105 | 48.0700 | 3 |
| cdv_t4_wrist_cuoio_001 | T4 | wrist (C) | Uncommon | - | 1.00 | 91.7125 | 18.3425 | 7.3370 | 11.0055 | 73.3700 | 4 |
| cdv_t5_wrist_stoffa_001 | T5 | wrist (C) | Uncommon | - | 1.00 | 117.0125 | 23.4025 | 9.3610 | 14.0415 | 93.6100 | 5 |
| cdv_t2_waist_stoffa_001 | T2 | waist (B) | Uncommon | - | 1.00 | 44.2750 | 8.8550 | 3.5420 | 5.3130 | 35.4200 | 2 |
| cdv_t3_waist_stoffa_001 | T3 | waist (B) | Uncommon | - | 1.00 | 76.4750 | 15.2950 | 6.1180 | 9.1770 | 61.1800 | 3 |
| cdv_t3_waist_stoffa_002 | T3 | waist (B) | Uncommon | - | 1.00 | 76.4750 | 15.2950 | 6.1180 | 9.1770 | 61.1800 | 3 |
| cdv_t3_waist_cuoio_001 | T3 | waist (B) | Uncommon | - | 1.00 | 76.4750 | 15.2950 | 6.1180 | 9.1770 | 61.1800 | 3 |
| cdv_t4_waist_stoffa_001 | T4 | waist (B) | Uncommon | - | 1.00 | 116.7250 | 23.3450 | 9.3380 | 14.0070 | 93.3800 | 4 |
| cdv_t5_waist_cuoio_001 | T5 | waist (B) | Uncommon | - | 1.00 | 148.9250 | 29.7850 | 11.9140 | 17.8710 | 119.1400 | 5 |
| cdv_t1_legs_stoffa_001 | T1 | legs (S) | Uncommon | - | 1.00 | 28.7500 | 5.7500 | 2.3000 | 3.4500 | 23.0000 | 1 |
| cdv_t1_legs_stoffa_002 | T1 | legs (S) | Uncommon | - | 1.00 | 28.7500 | 5.7500 | 2.3000 | 3.4500 | 23.0000 | 1 |
| cdv_t1_legs_stoffa_003 | T1 | legs (S) | Uncommon | - | 1.00 | 28.7500 | 5.7500 | 2.3000 | 3.4500 | 23.0000 | 1 |
| cdv_t2_legs_stoffa_001 | T2 | legs (S) | Uncommon | - | 1.00 | 63.2500 | 12.6500 | 5.0600 | 7.5900 | 50.6000 | 2 |
| cdv_t2_legs_cuoio_001 | T2 | legs (S) | Uncommon | - | 1.00 | 63.2500 | 12.6500 | 5.0600 | 7.5900 | 50.6000 | 2 |
| cdv_t3_legs_stoffa_001 | T3 | legs (S) | Uncommon | - | 1.00 | 109.2500 | 21.8500 | 8.7400 | 13.1100 | 87.4000 | 3 |
| cdv_t4_legs_stoffa_001 | T4 | legs (S) | Uncommon | - | 1.00 | 166.7500 | 33.3500 | 13.3400 | 20.0100 | 133.4000 | 4 |
| cdv_t4_legs_cuoio_001 | T4 | legs (S) | Uncommon | - | 1.00 | 166.7500 | 33.3500 | 13.3400 | 20.0100 | 133.4000 | 4 |
| cdv_t5_legs_stoffa_001 | T5 | legs (S) | Uncommon | - | 1.00 | 212.7500 | 42.5500 | 17.0200 | 25.5300 | 170.2000 | 5 |
| cdv_t5_legs_cuoio_001 | T5 | legs (S) | Uncommon | - | 1.00 | 212.7500 | 42.5500 | 17.0200 | 25.5300 | 170.2000 | 5 |
| cdv_t2_feet_stoffa_001 | T2 | feet (A) | Uncommon | - | 1.00 | 53.7625 | 10.7525 | 4.3010 | 6.4515 | 43.0100 | 2 |
| cdv_t3_feet_stoffa_001 | T3 | feet (A) | Uncommon | - | 1.00 | 92.8625 | 18.5725 | 7.4290 | 11.1435 | 74.2900 | 3 |
| cdv_t3_feet_stoffa_002 | T3 | feet (A) | Uncommon | - | 1.00 | 92.8625 | 18.5725 | 7.4290 | 11.1435 | 74.2900 | 3 |
| cdv_t3_feet_cuoio_001 | T3 | feet (A) | Uncommon | - | 1.00 | 92.8625 | 18.5725 | 7.4290 | 11.1435 | 74.2900 | 3 |
| cdv_t4_feet_stoffa_001 | T4 | feet (A) | Uncommon | - | 1.00 | 141.7375 | 28.3475 | 11.3390 | 17.0085 | 113.3900 | 4 |
| cdv_t4_feet_cuoio_001 | T4 | feet (A) | Uncommon | - | 1.00 | 141.7375 | 28.3475 | 11.3390 | 17.0085 | 113.3900 | 4 |
| cdv_t5_feet_stoffa_001 | T5 | feet (A) | Rare | - | 1.00 | 212.2875 | 63.6863 | 25.4745 | 38.2118 | 148.6013 | 5 |
| cdv_t1_main_hand_focus_001 | T1 | main_hand (S) | Uncommon | focus | 1.00 | 28.7500 | 5.7500 | 2.3000 | 3.4500 | 23.0000 | 1 |
| cdv_t1_main_hand_focus_002 | T1 | main_hand (S) | Uncommon | focus | 1.00 | 28.7500 | 5.7500 | 2.3000 | 3.4500 | 23.0000 | 1 |
| cdv_t1_main_hand_balestra_001 | T1 | main_hand (S) | Rare | balestra | 0.88 | 29.7000 | 8.9100 | 3.5640 | 5.3460 | 20.7900 | 1 |
| cdv_t2_main_hand_focus_001 | T2 | main_hand (S) | Uncommon | focus | 1.00 | 63.2500 | 12.6500 | 5.0600 | 7.5900 | 50.6000 | 2 |
| cdv_t2_main_hand_focus_002 | T2 | main_hand (S) | Uncommon | focus | 1.00 | 63.2500 | 12.6500 | 5.0600 | 7.5900 | 50.6000 | 2 |
| cdv_t2_main_hand_pugnale_001 | T2 | main_hand (S) | Rare | pugnale | 0.78 | 57.9150 | 17.3745 | 6.9498 | 10.4247 | 40.5405 | 2 |
| cdv_t3_main_hand_focus_001 | T3 | main_hand (S) | Rare | focus | 1.00 | 128.2500 | 38.4750 | 15.3900 | 23.0850 | 89.7750 | 3 |
| cdv_t3_main_hand_focus_002 | T3 | main_hand (S) | Rare | focus | 1.00 | 128.2500 | 38.4750 | 15.3900 | 23.0850 | 89.7750 | 3 |
| cdv_t3_main_hand_balestra_001 | T3 | main_hand (S) | Rare | balestra | 0.88 | 112.8600 | 33.8580 | 13.5432 | 20.3148 | 79.0020 | 3 |
| cdv_t4_main_hand_focus_001 | T4 | main_hand (S) | Uncommon | focus | 1.00 | 166.7500 | 33.3500 | 13.3400 | 20.0100 | 133.4000 | 4 |
| cdv_t4_main_hand_balestra_001 | T4 | main_hand (S) | Rare | balestra | 0.88 | 172.2600 | 51.6780 | 20.6712 | 31.0068 | 120.5820 | 4 |
| cdv_t4_main_hand_pugnale_001 | T4 | main_hand (S) | Rare | pugnale | 0.78 | 152.6850 | 45.8055 | 18.3222 | 27.4833 | 106.8795 | 4 |
| cdv_t5_main_hand_focus_001 | T5 | main_hand (S) | Legendary | focus | 1.00 | 342.2500 | 171.1250 | 85.5625 | 85.5625 | 171.1250 | 5 |
| cdv_t5_main_hand_balestra_001 | T5 | main_hand (S) | Legendary | balestra | 0.88 | 301.1800 | 150.5900 | 75.2950 | 75.2950 | 150.5900 | 5 |
| cdv_t5_main_hand_balestra_002 | T5 | main_hand (S) | Rare | balestra | 0.88 | 219.7800 | 65.9340 | 26.3736 | 39.5604 | 153.8460 | 5 |
| cdv_t3_off_hand_focus_001 | T3 | off_hand (B) | Rare | focus | 1.00 | 89.7750 | 26.9325 | 10.7730 | 16.1595 | 62.8425 | 3 |
| cdv_t4_off_hand_focus_001 | T4 | off_hand (B) | Rare | focus | 1.00 | 137.0250 | 41.1075 | 16.4430 | 24.6645 | 95.9175 | 4 |
| cdv_t4_off_hand_balestra_001 | T4 | off_hand (B) | Rare | balestra | 0.88 | 120.5820 | 36.1746 | 14.4698 | 21.7048 | 84.4074 | 4 |
| cdv_t5_off_hand_balestra_001 | T5 | off_hand (B) | Rare | balestra | 0.88 | 153.8460 | 46.1538 | 18.4615 | 27.6923 | 107.6922 | 5 |
| cdv_t5_off_hand_pugnale_001 | T5 | off_hand (B) | Rare | pugnale | 0.78 | 136.3635 | 40.9091 | 16.3636 | 24.5455 | 95.4545 | 5 |
| cdv_t5_off_hand_pugnale_002 | T5 | off_hand (B) | Rare | pugnale | 0.78 | 136.3635 | 40.9091 | 16.3636 | 24.5455 | 95.4545 | 5 |
| cdv_t2_accessory_universal_position_001 | T2 | accessory (C) | Rare | - | 1.00 | 40.8375 | 12.2513 | 4.9005 | 7.3508 | 28.5863 | 2 |
| cdv_t2_ring_universal_position_001 | T2 | ring (C) | Rare | - | 1.00 | 40.8375 | 12.2513 | 4.9005 | 7.3508 | 28.5863 | 2 |
| cdv_t2_ring_universal_position_002 | T2 | ring (C) | Rare | - | 1.00 | 40.8375 | 12.2513 | 4.9005 | 7.3508 | 28.5863 | 2 |
| cdv_t3_ring_universal_position_001 | T3 | ring (C) | Rare | - | 1.00 | 70.5375 | 21.1613 | 8.4645 | 12.6968 | 49.3763 | 3 |
| cdv_t3_ring_universal_position_002 | T3 | ring (C) | Rare | - | 1.00 | 70.5375 | 21.1613 | 8.4645 | 12.6968 | 49.3763 | 3 |
| cdv_t4_ring_universal_position_001 | T4 | ring (C) | Rare | - | 1.00 | 107.6625 | 32.2988 | 12.9195 | 19.3793 | 75.3638 | 4 |
| cdv_t4_ring_universal_position_002 | T4 | ring (C) | Rare | - | 1.00 | 107.6625 | 32.2988 | 12.9195 | 19.3793 | 75.3638 | 4 |
| cdv_t4_ring_universal_position_003 | T4 | ring (C) | Rare | - | 1.00 | 107.6625 | 32.2988 | 12.9195 | 19.3793 | 75.3638 | 4 |
| cdv_t5_ring_universal_position_001 | T5 | ring (C) | Rare | - | 1.00 | 137.3625 | 41.2088 | 16.4835 | 24.7253 | 96.1538 | 5 |
| cdv_t5_ring_universal_position_002 | T5 | ring (C) | Epic | - | 1.00 | 162.8000 | 65.1200 | 26.0480 | 39.0720 | 97.6800 | 5 |
| cdv_t5_ring_universal_position_003 | T5 | ring (C) | Epic | - | 1.00 | 162.8000 | 65.1200 | 26.0480 | 39.0720 | 97.6800 | 5 |
| cdv_t5_ring_universal_position_004 | T5 | ring (C) | Epic | - | 1.00 | 162.8000 | 65.1200 | 26.0480 | 39.0720 | 97.6800 | 5 |
| cdv_t1_accessory_universal_position_001 | T1 | accessory (C) | Rare | - | 1.00 | 18.5625 | 5.5688 | 2.2275 | 3.3413 | 12.9938 | 1 |
| cdv_t1_accessory_universal_position_002 | T1 | accessory (C) | Epic | - | 1.00 | 22.0000 | 8.8000 | 3.5200 | 5.2800 | 13.2000 | 1 |
| cdv_t1_accessory_universal_position_003 | T1 | accessory (C) | Epic | - | 1.00 | 22.0000 | 8.8000 | 3.5200 | 5.2800 | 13.2000 | 1 |
| cdv_t1_ring_universal_position_001 | T1 | ring (C) | Rare | - | 1.00 | 18.5625 | 5.5688 | 2.2275 | 3.3413 | 12.9938 | 1 |
| cdv_t1_neck_universal_position_001 | T1 | neck (B) | Common | - | 1.00 | 17.5000 | 1.7500 | 0.7000 | 1.0500 | 15.7500 | 1 |
| cdv_t1_hands_stoffa_001 | T1 | hands (A) | Common | - | 1.00 | 21.2500 | 2.1250 | 0.8500 | 1.2750 | 19.1250 | 1 |
| cdv_t1_back_universal_position_001 | T1 | back (B) | Common | - | 1.00 | 17.5000 | 1.7500 | 0.7000 | 1.0500 | 15.7500 | 1 |
| cdv_t3_accessory_universal_position_002 | T3 | accessory (C) | Epic | - | 1.00 | 83.6000 | 33.4400 | 13.3760 | 20.0640 | 50.1600 | 3 |
| cdv_t3_accessory_universal_position_003 | T3 | accessory (C) | Epic | - | 1.00 | 83.6000 | 33.4400 | 13.3760 | 20.0640 | 50.1600 | 3 |
| cdv_t4_accessory_universal_position_001 | T4 | accessory (C) | Epic | - | 1.00 | 127.6000 | 51.0400 | 20.4160 | 30.6240 | 76.5600 | 4 |
| cdv_t4_accessory_universal_position_002 | T4 | accessory (C) | Epic | - | 1.00 | 127.6000 | 51.0400 | 20.4160 | 30.6240 | 76.5600 | 4 |
| cdv_t4_accessory_universal_position_003 | T4 | accessory (C) | Epic | - | 1.00 | 127.6000 | 51.0400 | 20.4160 | 30.6240 | 76.5600 | 4 |
| cdv_t5_accessory_universal_position_001 | T5 | accessory (C) | Epic | - | 1.00 | 162.8000 | 65.1200 | 26.0480 | 39.0720 | 97.6800 | 5 |
| cdv_t5_accessory_universal_position_002 | T5 | accessory (C) | Epic | - | 1.00 | 162.8000 | 65.1200 | 26.0480 | 39.0720 | 97.6800 | 5 |
| cdv_t5_accessory_universal_position_003 | T5 | accessory (C) | Epic | - | 1.00 | 162.8000 | 65.1200 | 26.0480 | 39.0720 | 97.6800 | 5 |

## 35 · Final Declaration
- `R18.6.RV3-IS2-B_Phase_2A`: **`ARTIFACT_WRITTEN_PENDING_PM_ADJUDICATION`**
- `R18.6.RV3-IS2-B_Phase_2B`: HOLD_NOT_AUTHORIZED
- `R18.6.RV3-NC1`: HOLD_NOT_AUTHORIZED
- `R18.6_Gate_11`: HOLD_NOT_AUTHORIZED
- `Registry v3 Item Generation & Apply`: NOT_AUTHORIZED
- `Monaco`: HOLD_NOT_AUTHORIZED
- `AFX2`: RESERVED_FUTURE_NOT_AUTHORIZED
- `IS2-A branch`: LOCKED_IMMUTABLE (Phase 1 · Phase 2 Rev-4 · L1)
- `Phase 1 Contract`: IMMUTABLE_UNCHANGED
- `Addendum P1-N1`: DESIGN_LOCKED_CLOSED_PM_VERBATIM_SAME_DISPATCH
- `Cacciatore del Vuoto`: `ACTIVE-DESIGN-READY` (design layer only)
- `awaiting_pm_verdict`: **True**

---

**ATTENDO VERDICT PM.**
