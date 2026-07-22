# R18.6.RV3-IS2-B-Phase-1-N1 · Tier Reference Budget Addendum

**Gate ID:** R18.6.RV3-IS2-B-Phase-1-N1  
**Parent Gate:** R18.6.RV3-IS2-B_Phase_1 (IMMUTABLE)  
**Regime:** DOCUMENTAL_ONLY · READ_ONLY · NO_APPLY  
**Lingua:** Italiano  
**Status:** ADDENDUM_DESIGN_LOCKED_PM_VERBATIM  
**Anchor `lore_meta.py` SHA256:** `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`  
**Created UTC:** 2026-07-22T09:03:29.030844+00:00  
**PM Dispatch:** Message 92 · Verdict §16 (Resume Conditional Phase 2A)  
**Blocker Resolved:** `IS2B_P2A_BLOCKER_01`

---

## 01 · Executive Summary
Addendum P1-N1 al Contratto `R18.6.RV3-IS2-B_Phase_1`. Introduce ESCLUSIVAMENTE la scala numerica di riferimento `tier_reference_budget` (T1..T5) precedentemente lasciata implicita nella sezione 9 del Contratto Phase 1. Nessun altro campo del Contratto Phase 1 viene modificato o rivalutato. L'Addendum sblocca esclusivamente l'esecuzione della Fase 2A (Per-Item Budget Envelope Projection) risolvendo il Blocker `IS2B_P2A_BLOCKER_01`.

## 02 · Scope
**In scope**
- Scala numerica `tier_reference_budget` per T1..T5
- Status per-tier: `DESIGN_LOCKED`
- Etichetta di derivazione: `WORST_CASE_MAIN_STAT_FEASIBILITY`
- Compatibilita' con sezioni Phase 1: §9, §10, §15, §16, §19, §47
- Certificazione readiness Phase 2A

**Out of scope**
- Modifica delle sezioni del Contratto Phase 1
- Assegnazione numerica per-item
- Assegnazione affix
- Effetti finali Legendary
- Generazione Registry
- Apply runtime · DB writes · Sealed scripts modifications

## 03 · Governance
- `documental_only = True`
- `read_only = True`
- `no_apply = True`
- Modifiche a backend/frontend/OpenAPI/DB/registry/test/env/sigilli: **0**
- Sealed scripts byte-identical attesi: **36/36**
- `lore_meta.py` SHA256 invariante: `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`
- Compliance SHA Policy §31: True
- File Contratto Phase 1 IMMUTABILI (4 file)

## 04 · Source of Truth
- **PM Verdict Reference:** Message 92 · Section 16 · Resume Conditional Phase 2A
- **PM Dispatched Scale (verbatim):** T1=25 · T2=55 · T3=95 · T4=145 · T5=185
- **PM Derivation Label (verbatim):** `WORST_CASE_MAIN_STAT_FEASIBILITY`
- **PM Status Per Tier (verbatim):** `DESIGN_LOCKED`

## 05 · Blocker Reference
- **Blocker ID:** `IS2B_P2A_BLOCKER_01`
- **Descrizione:** Absent numeric scale for `tier_reference_budget` prevented deterministic per-item envelope calculation for Phase 2A.
- **Status:** RESOLVED_VIA_ADDENDUM_P1_N1
- **Resolution Dispatch:** PM Message 92

## 06 · Tier Reference Budget Scale
| Tier | tier_reference_budget | status         | derivation                          |
|------|----------------------:|----------------|-------------------------------------|
| T1   |                    25 | DESIGN_LOCKED  | WORST_CASE_MAIN_STAT_FEASIBILITY    |
| T2   |                    55 | DESIGN_LOCKED  | WORST_CASE_MAIN_STAT_FEASIBILITY    |
| T3   |                    95 | DESIGN_LOCKED  | WORST_CASE_MAIN_STAT_FEASIBILITY    |
| T4   |                   145 | DESIGN_LOCKED  | WORST_CASE_MAIN_STAT_FEASIBILITY    |
| T5   |                   185 | DESIGN_LOCKED  | WORST_CASE_MAIN_STAT_FEASIBILITY    |

## 07 · Monotonicity Invariant
- Regola: `T1 < T2 < T3 < T4 < T5`
- Osservato: `25 < 55 < 95 < 145 < 185`
- Pass: **True**

## 08 · Worst-Case Main Stat Feasibility Certification
Regola: per ciascun tier, `tier_reference_budget >= main_stat_band_max` del tier stesso, garantendo la fattibilita' del worst-case main_stat (Common · slot_band S · weapon_coefficient_if_applicable=1.00 · rarity_multiplier=1.00).

| Tier | budget | band_max Phase 1 §9 | residual | feasible |
|------|-------:|--------------------:|---------:|----------|
| T1   |     25 |                  25 |        0 | True     |
| T2   |     55 |                  45 |       10 | True     |
| T3   |     95 |                  70 |       25 | True     |
| T4   |    145 |                  90 |       55 | True     |
| T5   |    185 |                 115 |       70 | True     |

**Esito globale:** `all_tiers_feasible = True`.

## 09 · Relationship to Phase 1 Contract
- Sezioni Phase 1 referenziate (read-only): §9, §10, §15, §16, §19, §47
- Sezioni Phase 1 modificate: **nessuna**
- Verdetti Phase 1 modificati: **nessuno**
- Status Contratto Phase 1: `IMMUTABLE_PATCHED_PM_VERDICTS_INTEGRATED_Q01_TO_Q08_RESOLVED`
- Relazione Addendum: `ADDITIVE_NON_INVASIVE`

## 10 · Application Scope
- **Corpus target:** `R18.6.RV3-IS2-B_Phase_2A_per_item_envelope_projection`
- **Corpus units:** 120
- **Composizione corpus:**
  - Non-legendary NEW_FUTURE: 108
  - Preserved REUSE_VALID: 6
  - Preserved REUSE_CONDITIONAL: 3
  - Legendary PM-selected: 3
- **Fonte autoritativa:** `r18_6_rv3_is1_item_specification_roster_contract.json::roster_120_units`
- **Esclusi dalla proiezione attiva:** 3 (motivo: `DORMANT_CONTINGENCY_OUTSIDE_ACTIVE_ROSTER`)
  - Riferimento: `r18_6_rv3_is2_a_phase2_full_identity_naming_lore_roster_rev4.json` §10 `contingency_exclusion` (count=3, `content_status=DORMANT_NOT_GENERATED`).

## 11 · Formula Recap (Phase 1 §16)
```
tier_reference_budget × slot_band_multiplier × weapon_coefficient_if_applicable × rarity_multiplier = TOTAL_ITEM_BUDGET
```
- Ogni moltiplicatore applicato UNA sola volta.
- Precisione interna: 4 decimali.
- Nessun arrotondamento intermedio.
- Rounding finale: `ROUND_HALF_UP_final_only`.
- Target di distribuzione downstream: `stat` · `effetti` · `utility` · `affix`.
- Nessun componente aggiuntivo fuori dal totale.

## 12 · Anti-Double-Counting Reaffirmation (Phase 1 §14)
- `single_source_of_power`
- `rarity_multiplier_applied_once_at_total_level`
- `each_component_consumes_same_total`
- `no_affix_replication_across_families`
- `unspent_budget_does_not_become_extra_external_power`
- Ruolo `tier_reference_budget`: `SOLE_NUMERIC_BASE_OF_TOTAL_ITEM_BUDGET_FORMULA`.

## 13 · Rounding Policy Reaffirmation (Q04 · Phase 1 §47)
- Precisione interna: 4 decimali
- Metodo: `ROUND_HALF_UP` (NON banker's rounding)
- Precisioni output: flat_stats=intero · %=1 dec · durate=1 dec sec · coefficienti=2 dec · budget interni=4 dec
- Ordine applicazione locked: `base_budget → slot_multiplier → weapon_coefficient → rarity_multiplier → budget_split → final_rounding`.

## 14 · Stacking & Proc Cap Reaffirmation (Q05 · Phase 1 §48 / §35)
- Combined proc cap %: **45**
- Combination mode procs: `ADDITIVE_BEFORE_CAP`
- No multiplicative composition bypass
- `tier_reference_budget` NON autorizza alcun bypass di cap.

## 15 · Hard Cap Protections Immutabili Reaffirmation (Phase 1 §36)
- `fragments_cap = 5`
- `mark_duration_hard_cap = 10`
- `active_marks_hard_cap = 5`
- `combined_proc_cap_pct = 45`
- `focus_bonus_per_resource_segment = 2`
- `pugnale_ritual_close_bonus_per_mark_application = 1`
- Violabilita' da `tier_reference_budget` o Addendum P1-N1: **False**.

## 16 · Fail-Stop Conditions
- Deviazione qualsiasi da 25/55/95/145/185 → **STOP_addendum_invalid**
- Modifica ai 4 file Contratto Phase 1 → **STOP_immutability_violation**
- Alterazione formula → **STOP_scope_violation**
- Violazione hard cap → **STOP_re_escalate_no_autonomous_decision**
- Sealed scripts deviazione da 36/36 → **STOP_integrity_violation**
- Deviazione SHA256 `lore_meta.py` → **STOP_anchor_violation**

## 17 · Change Ledger
- `phase_1_contract_md_changed = False`
- `phase_1_contract_json_changed = False`
- `phase_1_closure_report_md_changed = False`
- `phase_1_closure_report_json_changed = False`
- File Addendum creati:
  - `r18_6_rv3_is2_b_phase1_n1_tier_reference_budget_addendum.md`
  - `r18_6_rv3_is2_b_phase1_n1_tier_reference_budget_addendum.json`
  - `r18_6_rv3_is2_b_phase1_n1_closure_manifest.json`
- `prd_append_required = True`

## 18 · Closure Conditions
- **Addendum Status:** `DESIGN_LOCKED_PM_VERBATIM_SAME_DISPATCH`
- **Phase 2A Authorization:** `GRANTED_CONDITIONAL_ON_ADDENDUM_APPLIED`
- **Next Action:** `R18.6.RV3-IS2-B_Phase_2A_per_item_budget_envelope_projection_execution`
- **Phase 2A closure manifest authorized:** `False`
- **Phase 2A PRD append authorized:** `False`
- **Awaiting PM Verdict:** `True`
