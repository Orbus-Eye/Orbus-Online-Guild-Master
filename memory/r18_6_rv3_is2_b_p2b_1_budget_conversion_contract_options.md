# R18.6.RV3-IS2-B-P2B-1 · Budget Conversion Discovery & Contract Options

**Gate ID:** R18.6.RV3-IS2-B-P2B-1  
**Regime:** DOCUMENTAL_ONLY · READ-ONLY DISCOVERY · NO_APPLY · Italian_only  
**Artifact Status:** `ARTIFACT_WRITTEN_PENDING_PM_ADJUDICATION`  
**Closure Manifest Authorized:** `False`  
**PRD Append Authorized:** `False`  
**Anchor `lore_meta.py` SHA256:** `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`  
**Created UTC:** 2026-07-22T13:59:42.754277+00:00

---

## 01 · Executive Summary
Discovery read-only del runtime esistente per determinare come le ABSTRACT_ITEM_BUDGET_UNITS Phase 2A (envelope 17.5000-342.2500) possano essere convertite in costi comparabili per **Intelligenza · Costituzione · Destrezza** · effetti (13 categorie) · proc · durate · cooldown · utility · affix · Legendary.

**Constatazione critica**: il runtime esistente usa un modello **5-stat INGLESE** (`strength/agility/intellect/endurance/faith`) con formula power **lineare** (`Σ + level*2`). NON esistono runtime:
- soft-cap 100 su Intelligenza
- proc_chance su item · duration · cooldown item-driven
- mark/drain/fragment interaction
- taxonomy 13 categorie
- weapon coefficient

Il gate propone **tre modelli (A/B/C)**, simula **5 casi rappresentativi + 2 estremi**, identifica **2 blocker fail-stop critici** (`RUNTIME_STAT_VALUE_EVIDENCE_MISSING`, `DEX_CONVERSION_UNDERDEFINED`) e **12 PM open questions** (9 impact critical/high). Raccomandazione agente: **Model A · Equal-cost baseline** come transitional in attesa di ratifica PM.

## 02 · Scope
**In scope**: discovery read-only, confronto modelli A/B/C, simulazioni 5+2, costing methodology 13 categorie, affix/legendary methodology, PM open questions.  
**Out of scope**: assegnazioni per-item, modifiche runtime/DB/Registry/sealed, closure manifest, PRD append, alterazione hard caps/scala tier/formula.

## 03 · Governance
- `documental_only=True · read_only_discovery=True · no_apply=True`
- Modifiche a backend/frontend/OpenAPI/DB/registry/test/env/sigilli: **0**
- Sealed scripts byte-identical attesi: **36/36**
- `lore_meta.py` SHA256 invariante: `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`
- Compliance SHA Policy §31: True
- Chain immutabile: Phase 1 + P1-N1 + Phase 2A envelope + Phase 2A closure + IS2-A

## 04 · Source Chain
- Phase 1 Contract, Addendum P1-N1, Phase 2A envelope, Phase 2A closure/manifest, IS2-A Rev-4, IS2-A L1, IS1 corpus 120.

## 05 · Runtime Discovery (read-only files examined)
| Path | Role |
|---|---|
| `/app/backend/app/expeditions/formulas.py` | power & success chance formulas |
| `/app/backend/app/equipment/services.py` | equipment load/snapshot |
| `/app/backend/app/equipment/auto_equip.py` | fitness weighting + selection |
| `/app/backend/app/adventurers/common.py` · `services.py` · `generator.py` | adventurer stat baseline |
| `/app/backend/app/stats/public_catalog.py` | public 5-stat metadata |
| `/app/backend/app/items/services.py` · `/app/backend/app/inventory/services.py` | item public shape |
| `/app/backend/app/shared/constants.py` | rarity weights, slots, gameplay constants |
| `/app/backend/app/content/lore_meta.py` | anchor (immutable, read-only) |

**Runtime stat model canonical (5 stats INGLESE)**: `strength, agility, intellect, endurance, faith`.  
**Design-layer stats CdV (Italiano)**: `Intelligenza, Costituzione, Destrezza`.  
**Mapping runtime → italiano**: `NON_ESPLICITAMENTE_DICHIARATO` in runtime. Mapping presunto solo semantico: `Intelligenza→intellect · Costituzione→endurance · Destrezza→agility`. **Non ratificato PM.**

## 06 · Stat Formula Discovery
- **Power formula (adventurer)** `formulas.py::adventurer_base_power`: `Σ(str,agi,int,end,faith) + level*2` · costo marginale power per punto stat = **1.0** · UGUALE per tutte le 5 stat.
- **Power formula (item)** `formulas.py::item_equip_power`: `Σ(str_b, agi_b, int_b, end_b, faith_b) + power_score`.
- **Team power** = `Σ(members_total_power) + role_bonus(Tank+5, Healer+5, DPS+5, all-three+10)`.
- **Success chance** = `50 + (team_power - recommended)` clamp `[10, 95]`.
- **Auto-equip fitness weights** (`auto_equip.py::46-48`, **ranking only**, NOT power formula): `PRIMARY_WEIGHT=3.0 · SECONDARY_WEIGHT=1.5 · POWER_WEIGHT=1.0`.
- Trait stacking: flat additive → percent additive → `(base+flat)*(1+Σpct/100)`, `max(0, int(round(x)))`.
- **NO** soft cap · **NO** diminishing returns · **NO** stat-specific damage/mitigation derivation.

## 07 · Existing Item Distribution Discovery
- Item bonus fields: `strength_bonus, agility_bonus, intellect_bonus, endurance_bonus, faith_bonus` + `power_score` (int).
- Runtime rarity_bonus (constants.py): `Common=0, Uncommon=0, Rare=1, Epic=2, Legendary=3` (semantic: **recruit-time bonus**, non design envelope scalar).
- **NO** `proc_chance` field · **NO** `duration` field · **NO** `cooldown` field · **NO** mark/drain/fragment taxonomy · **NO** weapon coefficient · **NO** slot band multiplier.

## 08 · Soft-Cap Discovery
- Phase 1 §7: `soft_cap_intelligenza = 100`.
- **Runtime evidence implementation soft cap**: **NONE**. Nessun diminishing returns, nessun hard cap oltre 100, nessun cost shift.
- **Conclusione**: soft cap 100 e' vincolo design-layer. Runtime accetta stat int arbitrari; power `Σ` e' lineare su tutti gli int. Post-soft-cap policy richiede ratifica PM.

## 09 · Intelligenza Valuation
- Runtime power marginal cost/point: **1.0** (linear)
- Runtime auto_equip ranking weight (as primary): **3.0**
- Phase 1 band ranges: `T1[10-25] · T2[25-45] · T3[45-70] · T4[70-90] · T5[90-115]`
- Model A cost: **1.0** · Model B hypothesis: **1.5** · Model C: **BLOCKED**
- Post-soft-cap policy options: identical / double_cost / quadratic / **hard_cap_no_overflow** (recommended)

## 10 · Costituzione Valuation
- Runtime power marginal cost/point: **1.0** · runtime auto_equip ranking weight (as secondary): **1.5**
- **NO** direct HP/mitigation scaling in runtime. Stoffa/cuoio differential runtime: **NONE**.
- Phase 1 profile: stoffa=basso_medio · cuoio=medio_alto
- Model A: **1.0** · Model B: **1.0** · Model C: **BLOCKED**
- Cost relativo raccomandato: `≤ Intelligenza · ≥ Destrezza`

## 11 · Destrezza Valuation
- Runtime power marginal cost/point: **1.0** · runtime utility specifica per CdV: **NONE_DECLARED**
- Phase 1 forbidden: dex-primary CdV, dual Int/Dex primary, balestra Dex-primary, pugnale Dex-primary
- Model A: **1.0** · Model B hypothesis: **0.7** · Model C: **BLOCKED**
- **Blocker emesso: `DEX_CONVERSION_UNDERDEFINED`** — semantica runtime insufficient per differenziare Destrezza da agility generico. PM_REVIEW required.

## 12 · Model A · Equal-Cost Baseline
- `cost_per_int_unit=1.0 · cost_per_cost_unit=1.0 · cost_per_dex_unit=1.0`
- **Vantaggi**: coerente con runtime lineare · determinismo · zero runtime evidence extra · compatibile con item bonus schema esistente.
- **Rischi**: non riflette gerarchia ruoli · permette stat dumping · nessun disincentivo dex-primary · nessuna differenziazione stoffa/cuoio.
- **Compatibilita' runtime**: HIGH · **Low envelope**: MAYBE_PROBLEMATIC · **High envelope**: OVER_ABUNDANT
- **Agent score: 6/10**

## 13 · Model B · Role-Weighted
- `Int=1.5 · Cost=1.0 · Dex=0.7` (hypothesis, PM_REVIEW)
- **Vantaggi**: riflette priority order Phase 1 · disincentivo dex-drift indiretto · allinea con auto_equip fitness weights (3.0/1.5/1.0).
- **Rischi**: richiede ratifica multipliers · nessuna runtime evidence per role-differentiated marginal effect · potrebbe rendere low envelope infeasible.
- **Compatibilita' runtime**: MEDIUM · **Low envelope**: HIGH_RISK · **High envelope**: BALANCED
- **Agent score: 5/10**

## 14 · Model C · Marginal-Effectiveness Calibrated
- **BLOCKED**. Richiede evidence runtime NON PRESENTE per: damage/stat, mitigation/stat, HP scaling, proc engine, duration/cooldown engine, dodge/crit/evasion, class-specific stat multipliers.
- **Blocker emesso: `RUNTIME_STAT_VALUE_EVIDENCE_MISSING`** (critical).
- **Agent score: 0/10**

## 15 · Model Comparison Matrix
| Criterio | A | B | C |
|---|---|---|---|
| coherence_with_runtime_power_formula | HIGH | MEDIUM | N/A |
| aligns_with_phase_1_role_hierarchy | LOW | HIGH | TBD |
| no_extra_runtime_evidence_required | TRUE | FALSE | FALSE |
| low_envelope_feasibility | OK_WARN | AT_RISK | N/A |
| high_envelope_control | OVER_ABUNDANT | BALANCED | N/A |
| dex_primary_drift_disincentive | NONE | PARTIAL | TBD |
| stoffa_vs_cuoio_differentiation | NONE | NONE | TBD |
| pm_open_questions_needed | MANY | MORE | BLOCKING |

**Conclusione**: A baseline safe · B concettualmente utile ma richiede ratifica · C blocked.

## 16 · Low-Envelope Simulation · T1 Band C Common
- Envelope calcolato: **13.7500** (`25 × 0.55 × 1.00 × 1.00`)
- Nota: MIN envelope Phase 2A ratificato = `17.5000` (T1 Band B Common). Includiamo entrambi.

### Model A (cost/Int=1.0)
| case | tier | band | rarity | envelope | stat_env_max | band_min | band_max | cost/Int | cost@min | residual | min_reach | max_reach |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| T1 Band C Common (non-weapon) | T1 | C | Common | 13.7500 | 12.3750 | 10 | 25 | 1.0 | 10.0 | 2.375 | True | False |
| T2 Band A Uncommon (non-weapon) | T2 | A | Uncommon | 53.7625 | 43.0100 | 25 | 45 | 1.0 | 25.0 | 18.01 | True | False |
| T3 Band S Rare (non-weapon) | T3 | S | Rare | 128.2500 | 89.7750 | 45 | 70 | 1.0 | 45.0 | 44.775 | True | True |
| T4 Band B Epic (non-weapon) | T4 | B | Epic | 162.4000 | 97.4400 | 70 | 90 | 1.0 | 70.0 | 27.44 | True | True |
| T5 Band S Legendary (focus/chest) | T5 | S | Legendary | 342.2500 | 171.1250 | 90 | 115 | 1.0 | 90.0 | 81.125 | True | True |
| MIN extreme · T1 Band B Common non-weapon | T1 | B | Common | 17.5000 | 15.7500 | 10 | 25 | 1.0 | 10.0 | 5.75 | True | False |
| MAX extreme · T5 Band S Legendary non-weapon (focus/chest) | T5 | S | Legendary | 342.2500 | 171.1250 | 90 | 115 | 1.0 | 90.0 | 81.125 | True | True |

## 17 · Mid-Envelope Simulation · T2 Band A Uncommon · T3 Band S Rare
Vedi tabella §16 (righe 2-3).

## 18 · High-Envelope Simulation · T4 Band B Epic · T5 Band S Legendary + MAX extreme
Vedi tabella §16 (righe 4-5-7).

### Model B (cost/Int=1.5 · cost/Cost=1.0 · cost/Dex=0.7)
| case | tier | band | rarity | envelope | stat_env_max | band_min | band_max | cost/Int | cost@min | residual | min_reach | max_reach |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| T1 Band C Common (non-weapon) | T1 | C | Common | 13.7500 | 12.3750 | 10 | 25 | 1.5 | 15.0 | -2.625 | False | False |
| T2 Band A Uncommon (non-weapon) | T2 | A | Uncommon | 53.7625 | 43.0100 | 25 | 45 | 1.5 | 37.5 | 5.51 | True | False |
| T3 Band S Rare (non-weapon) | T3 | S | Rare | 128.2500 | 89.7750 | 45 | 70 | 1.5 | 67.5 | 22.275 | True | False |
| T4 Band B Epic (non-weapon) | T4 | B | Epic | 162.4000 | 97.4400 | 70 | 90 | 1.5 | 105.0 | -7.56 | False | False |
| T5 Band S Legendary (focus/chest) | T5 | S | Legendary | 342.2500 | 171.1250 | 90 | 115 | 1.5 | 135.0 | 36.125 | True | False |
| MIN extreme · T1 Band B Common non-weapon | T1 | B | Common | 17.5000 | 15.7500 | 10 | 25 | 1.5 | 15.0 | 0.75 | True | False |
| MAX extreme · T5 Band S Legendary non-weapon (focus/chest) | T5 | S | Legendary | 342.2500 | 171.1250 | 90 | 115 | 1.5 | 135.0 | 36.125 | True | False |

### Model C
BLOCKED — vedi §14.

## 19 · Effect Taxonomy Costing Methodology (13 categorie)
Formula concettuale: `effect_cost = base_magnitude_cost × expected_uptime_factor × reliability_factor × scope_factor × stacking_factor`.

**PAYOFF_UTILITY resta internal-only** (no player-facing text con "Payoff").

Per-category factors documentati nel JSON §19 (13 categorie con magnitude/uptime/reliability/scope/stacking/boss_safeguard).

## 20 · Magnitude Costing
- `base_magnitude_cost` = costo interno per unita' canonica di magnitude (1% damage, 1 flat stat, 1 defense).
- Default flat stat: **1.0** · %-bonus stat: **PM_REVIEW (3.0-5.0/%)** · flat damage: **PM_REVIEW (2.0)** · flat defense: **PM_REVIEW (2.0)**
- Precisione residual: 4 decimals internal.

## 21 · Uptime Costing
- Baseline encounter window: **30s**
- Default uptime: PASSIVE_STAT=1.00 · MARK=5s/30s=0.17 · DRAIN=marked_5s/30s=0.17 · PROC=15%_over_30s=0.15 · CHANNEL_MOB=3s/30s=0.10 · TRIGGERED_1x=0.03
- Nessuna estensione oltre hard cap (`mark_duration_hard_cap=10s` rispettato).

## 22 · Proc Costing
- Combined proc cap: **45%** ADDITIVE_BEFORE_CAP · **no multiplicative bypass**.
- Proposta cost/point %: linear 0.5 sotto 30% · quadratica sopra 30%.
- Differentials offensive/defensive/utility: PM_REVIEW.
- **NO proc assignment agli item in P2B-1**.

## 23 · Duration Costing
- Hard cap mark duration: **10s**.
- Proposta cost/second (sotto hardcap): **PM_REVIEW · 0.2 unita' × sec**.
- Interaction: durata × cooldown × magnitude NON pagati separatamente; usare `expected_uptime_calculation`.
- Refresh semantics: `REFRESH_no_auto_extend` (Phase 1 §48).

## 24 · Cooldown Costing
- Cooldown inversamente relato a `expected_uptime_factor`.
- Proposta cost/second cooldown saved: **PM_REVIEW · -0.1 unita' × sec saved**.
- Hard floor cooldown: **PM_REVIEW · 3s min**.
- Interaction via uptime_factor only · no double-counting.

## 25 · Scope & Reliability Factors
- Scope: SELF=1.0 · SINGLE_TARGET=1.0 · AOE_SMALL=1.5 · AOE_LARGE=2.0 · BOSS_ONLY=0.8
- Reliability: baseline 1.0; chance-gated < 1.0 (via proc_costing); resistant-to-counters > 1.0
- Nessun amplify beyond hard caps.

## 26 · Stacking Interaction
Da Phase 1 §48 (Q05 DESIGN_LOCKED):
- Passive flat stats: `ADDITIVE within budget/soft_cap/system_cap`
- Same unique effect nominal: `NON_STACKING · HIGHEST_EFFECTIVE_VALUE_WINS`
- Same family default: `NON_STACKING`
- Durations: `REFRESH no_auto_extend`
- Proc chance: `ADDITIVE_BEFORE_CAP · 45%`
- Legendary same identity: `NON_STACKING`
- Proposta stacking penalty famiglia replicata: `-20% budget per replicated family occurrence` (PM_REVIEW).

## 27 · Boss Safeguard Costing
- Categorie che richiedono `boss_safeguard_required=true`: **ANTI_SUMMON · DISPEL_UTILITY · ANTI_INCORPOREAL**
- Proposta cost condition budget: **PM_REVIEW · 5-15% del combined_effect_utility_ceiling**
- Forbidden: `direct_boss_nullification · boss_immunity_bypass · unconditional_summon_deletion · ignore_boss_safeguard`

## 28 · Utility Costing
- Families: `PAYOFF_UTILITY · DISPEL_UTILITY · CHANNEL_MOBILITY · RITUAL_PROTECTION`
- Utility share internal max: `non_legendary=40% · legendary=50%` del combined_effect_utility_ceiling
- Residue disposition: `to_effect_or_base_stat · never_extra_external`
- Cost methodology baseline = effect_cost scaled by utility_share_internal_max_pct.

## 29 · Affix Costing
- Slot per tier (Phase 1 §11): `T1=1 · T2=2 · T3=3 · T4=4 · T5=5`
- Proposta `affix_budget_unit`: 5% budget per slot flat (max 25% a T5)
- Proposta `grade_multiplier`: 1.0/1.5/2.0/3.0
- Flat stat affix = PASSIVE_STAT cost · Conditional = PASSIVE × conditional_uptime · Utility = PAYOFF_UTILITY × utility_share_cap
- Duplicate family penalty: **-20% per replicated affix family** (recommended, PM_REVIEW)
- **NO affix assignment in P2B-1**. AFX1 read-only. `affix_eligibility ≠ affix_assignment` preservato.

## 30 · Legendary Costing Methodology (3 pillar)
| Legendary | Pillar | Envelope | Methodology |
|---|---|---:|---|
| **Veste di Onirade** (`cdv_t5_chest_stoffa_*`) | `RITUAL_CHANNEL_PROTECTION` | 342.2500 | 5-15% envelope per LEGENDARY_UNIQUE_EFFECT + Cost-heavy passive stoffa · protection during channel · ritual stability · resilience Costituzione · reduced Drain risk · DIRECTION_ONLY |
| **Occhio del Faro Rovesciato** (`cdv_t5_main_hand_focus_001`) | `IDENTIFY_MARK_ORCHESTRATION` | 342.2500 | 5-15% envelope per LEGENDARY_UNIQUE + WEAPON_IDENTITY_EFFECT · better Identify→Mark · controlled Drain · conditional Fragment · target readability · DIRECTION_ONLY |
| **Balestra della Traiettoria certa** (`cdv_t5_main_hand_balestra_001`) | `RANGED_PRECISION_DISPEL` | 301.1800 | 5-15% envelope per LEGENDARY_UNIQUE + WEAPON_IDENTITY_EFFECT · ranged ritual precision · targeted Mark · selective dispel · anti-summon on valid targets · DIRECTION_ONLY |

**Shared rules**: `LEGENDARY_UNIQUE_EFFECT` status Phase 1=`DIRECTION_ONLY` · consume legendary total budget · not additive over rarity_multiplier · duplication forbidden by identity lock.  
**NON definiti in P2B-1**: effetto finale, magnitude, proc, duration, cooldown.

## 31 · Rounding & Residue
- Internal precision: 4 decimals · No intermediate rounding · Final: ROUND_HALF_UP
- Output precisions: flat_stats=integer · %=1 dec · duration=1 dec sec · coef=2 dec · budget=4 dec
- Residue assignment order: `main_stat_intelligenza → costituzione`
- No extra budget from residues.

## 32 · Spend Tolerance
- `minimum_spend_ratio_recommended`: **0.95**
- `maximum_spend_ratio_recommended`: **1.00**
- `acceptable_unspent_budget_max_pct`: **5.0%**
- `over_budget_tolerance_recommended`: **0.0** (strict)
- `rounding_tolerance_recommended_units`: **0.5**
- Note: `over_budget_tolerance > 0` → PM_REVIEW. Unspent budget non diventa mai potere esterno (Phase 1 §13).

## 33 · Anti-Double-Counting
Reaffirmed rules (Phase 1 §14):
- `single_source_of_power` · `rarity_multiplier_applied_once_at_total_level` · `each_component_consumes_same_total`
- `no_affix_replication_across_families` · `unspent_budget_does_not_become_extra_external_power`
- Budget split disjoint pools (stat, effect, utility, affix) entro il totale · No component outside `gross_total_item_budget`.

## 34 · Risk Register
11 rischi identificati (dettagli in JSON §34). Highlights:
- **R1 critical** `runtime_stat_marginal_evidence_missing` → blocker `RUNTIME_STAT_VALUE_EVIDENCE_MISSING`
- **R2 high** italian↔runtime mapping unratified
- **R3 high** soft_cap 100 no runtime implementation
- **R4 high** low envelope infeasibility under Model B
- **R5 medium** dex semantics underdefined → blocker `DEX_CONVERSION_UNDERDEFINED`
- **R6-R11** double-counting / affix drift / legendary scope creep / spend tolerance / rarity mismatch / phase 2A envelope conflict (NOT triggered)

## 35 · PM Open Questions (12 total · 12 blocking · 5 critical · 6 high · 1 medium-high)

| # | question_id | topic | impact | blocking |
|---|---|---|---|---|
| 01 | P2B1_Q01 | cost_per_intelligenza_unit_pre_soft_cap | **critical** | Yes |
| 02 | P2B1_Q02 | cost_per_intelligenza_unit_post_soft_cap | **critical** | Yes |
| 03 | P2B1_Q03 | cost_per_costituzione_unit | **critical** | Yes |
| 04 | P2B1_Q04 | cost_per_destrezza_unit_and_semantic_scope_cdv | **high** | Yes |
| 05 | P2B1_Q05 | cost_per_proc_percent_point_and_curve_near_cap | **high** | Yes |
| 06 | P2B1_Q06 | cost_per_duration_second_and_cooldown_interaction | **high** | Yes |
| 07 | P2B1_Q07 | affix_cost_per_slot_and_family_grade | **high** | Yes |
| 08 | P2B1_Q08 | spend_tolerance_min_max_over_budget | **high** | Yes |
| 09 | P2B1_Q09 | final_recommended_model_A_B_C_or_hybrid | **critical** | Yes |
| 10 | P2B1_Q10 | italian_to_runtime_stat_mapping_ratification | **high** | Yes |
| 11 | P2B1_Q11 | runtime_extension_for_proc_duration_cooldown_mark_drain_fragment | **critical** | Yes |
| 12 | P2B1_Q12 | legendary_unique_effect_envelope_share_percent | **high** | Yes |

Dettagli evidence/options/recommendation/affected_systems in JSON §35.

## 36 · Recommended Model
**Raccomandazione agente: Model A · Equal-cost baseline** (transitional).

Rationale: coerente con runtime power formula lineare (Σ+level*2); nessuna runtime evidence extra richiesta; compatibile con low envelope; deterministic e trasparente; upgradabile a Model B senza rework envelope. Model B rimane concettualmente valido ma richiede ratifica PM su multipliers e non ha benefici runtime immediati. Model C: BLOCKED.

**Condizioni upgrade → Model B**:
1. PM ratifica multipliers Int=1.5 · Cost=1.0 · Dex=0.7 verbatim
2. PM ratifica DEX_CONVERSION scope per CdV
3. verifica low-envelope T1 Band C Common non infeasible con 1.5 Int cost

**Condizioni upgrade → Model C**:
1. Runtime extension gate (damage/mitigation/proc/duration/cooldown engines)
2. Empirical calibration evidence
3. PM ratify calibration constants

## 37 · Phase 2B Readiness
- Phase 2B current status: **HOLD_NOT_AUTHORIZED**
- Focus atteso Phase 2B: assegnazione per-item stat/effect/utility/affix 120 blueprint · Legendary final effect declaration · validation full corpus · migration boundary review
- Prerequisiti da P2B-1: 12 PM open questions risolte OR PM explicit accept-and-proceed con Model A transitional

## 38 · GO/HOLD Recommendation
**Agent recommendation: `HOLD_PENDING_PM_ADJUDICATION`**  
**Artifact Status: `ARTIFACT_WRITTEN_PENDING_PM_ADJUDICATION`**  
Closure manifest: **False** · PRD append: **False**  
Next action: `PM_VERDICT_ON_P2B_1_MODELS_AND_UNIT_COSTS`  
Downstream (PM GO): `R18.6.RV3-IS2-B_Phase_2B`

**Blockers emessi (2)**:
| Blocker ID | Impact | Scope |
|---|---|---|
| `RUNTIME_STAT_VALUE_EVIDENCE_MISSING` | critical | Model C · proc/duration/cooldown/mark/drain/fragment |
| `DEX_CONVERSION_UNDERDEFINED` | medium-high | Destrezza semantics per CdV |

**Blockers NON triggered**: `STAT_CONVERSION_SOURCE_CONFLICT · LOW_ENVELOPE_CONVERSION_FAILURE · PHASE2A_ENVELOPE_CONTRACT_CONFLICT`

### Stato finale
```
IS2-B-P2B-1        = ARTIFACT WRITTEN
PM adjudication    = REQUIRED
formal closure     = HOLD
IS2-B Phase 2B     = HOLD (non aperta)
```

---

**ATTENDO VERDICT PM.**
