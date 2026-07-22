# R18.6.RV3-IS2-B · Phase 2A · Final Closure Report

**Gate ID:** R18.6.RV3-IS2-B_Phase_2A  
**Gate Title:** Per-Item Budget Envelope Projection (120 blueprint units) · Final Closure  
**Regime:** DOCUMENTAL_ONLY · READ_ONLY · NO_APPLY · Italian_only  
**Closure Status:** `CLOSED_PM_LOCKED`  
**Anchor `lore_meta.py` SHA256:** `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` · INVARIATO  
**Created UTC:** 2026-07-22T13:08:59.244963+00:00

---

## 01 · PM Correction Verdict Citation
Il PM ha classificato il verdict re-inviato come **DUPLICATE_DISPATCH / NO-OP / SUPERSEDED**. Le attivita' P1-N1 addendum + Phase 2A envelope erano gia' state completate correttamente. L'unica azione autorizzata da questo dispatch e' la **FORMAL CLOSURE PHASE 2A ONLY**, con normalizzazione documentale del wording di feasibility e senza alcuna rigenerazione degli artefatti Phase 2A o P1-N1.

- **Classificazione**: `DUPLICATE_DISPATCH / NO-OP / SUPERSEDED`
- **Azione autorizzata esclusiva**: `FORMAL_CLOSURE_PHASE_2A_ONLY`
- **Rigenerazione envelope**: `NOT REQUIRED`
- **Recalculation**: `NOT REQUIRED`
- **Wording normalization scope**: `DOCUMENTATION_NORMALIZATION_ONLY`

## 02 · Phase 2A Ratifica · Corpus 120
- Active blueprint rows: **120**
- Dormant contingency rows: **0** (nel corpus attivo; 3 dormant riferiti in `roster_rev4 §10 contingency_exclusion` sono esclusi dal computo attivo con `exclusion_reason = DORMANT_CONTINGENCY_OUTSIDE_ACTIVE_ROSTER`)
- Duplicate blueprint codes: **0**
- Missing blueprint codes: **0**
- Fonte autoritativa corpus: `r18_6_rv3_is1_item_specification_roster_contract.json::roster_120_units`

**Tier distribution**: `T1=18 / T2=22 / T3=26 / T4=26 / T5=28` (Σ=120)  
**Rarity distribution**: `Common=42 / Uncommon=33 / Rare=27 / Epic=15 / Legendary=3` (Σ=120)  
**Slot bands**: `S=35 · A=29 · B=24 · C=32` (Σ=120)  
**Categories**: `ARMOR=60 · UNIVERSAL=39 · WEAPON=21` (Σ=120)  
**Weapon coefficients distribution**: `1.00=109 · 0.88=7 · 0.78=4` (Σ=120)

## 03 · Formula Ratificata (INVARIATA)
```
tier_reference_budget × slot_band_multiplier × weapon_coefficient_if_applicable × rarity_multiplier = gross_total_item_budget
```
- Ogni moltiplicatore applicato UNA sola volta
- Precisione interna: 4 decimali
- Nessun arrotondamento intermedio
- Rounding finale: `ROUND_HALF_UP`
- Ordine locked: `base_budget → slot_multiplier → weapon_coefficient → rarity_multiplier → budget_split → final_rounding`

## 04 · Scala Tier (Addendum P1-N1 · DESIGN_LOCKED)
| Tier | tier_reference_budget |
|------|----------------------:|
| T1 | 25 |
| T2 | 55 |
| T3 | 95 |
| T4 | 145 |
| T5 | 185 |

## 05 · Envelope Estremi Ratificati
- **MIN envelope** (`gross_total_item_budget`): **17.5000** (T1 · neck (B) · Common · non-weapon)
- **MAX envelope** (`gross_total_item_budget`): **342.2500** (T5 · slot S · Legendary · coefficient 1.00)
- **Nessun bonus esterno all'envelope autorizzato** (`no_extra_component_outside_total = True`)

### Legendary triplet · envelope ratificati
| Blueprint / Nome | Envelope |
|---|---:|
| `cdv_t5_chest_stoffa_001` · **Veste di Onirade** | **342.2500** |
| `cdv_t5_main_hand_focus_001` · **Occhio del Faro Rovesciato** | **342.2500** |
| `cdv_t5_main_hand_balestra_001` · **Balestra della Traiettoria certa** | **301.1800** |

## 06 · Feasibility Wording Normalization
**Wording ratificato (verbatim)**: `minimum_stat_budget ≥ main_stat_band_min`

- **Classificazione**: `DOCUMENTATION_NORMALIZATION_ONLY`
- **Envelope recalculation**: `NOT REQUIRED`
- **Rationale (PM verbatim intent)**: il proof P1-N1 garantisce la sostenibilita' del **minimo della banda** stat per ciascun tier, non necessariamente del massimo. La feasibility asseriva la corretta ampiezza dell'envelope a coprire il floor stat richiesto dal tier; nessun envelope viene modificato.
- **Wording deprecated (NON utilizzare in produzione documentale futura)**: `budget ≥ main_stat_band_max`

### Feasibility per tier · wording normalizzato
| Tier | tier_reference_budget | main_stat_band_min §9 | `minimum_stat_budget ≥ main_stat_band_min` |
|------|----------------------:|----------------------:|:------------------------------------------:|
| T1 |  25 |  10 | ✅ |
| T2 |  55 |  25 | ✅ |
| T3 |  95 |  45 | ✅ |
| T4 | 145 |  70 | ✅ |
| T5 | 185 |  90 | ✅ |

Envelope estremi verificati sotto wording normalizzato:
- MIN envelope 17.5000 (T1 neck B Common non-weapon) copre `main_stat_band_min T1 = 10` · **feasible**
- MAX envelope 342.2500 (T5 slot S Legendary) copre `main_stat_band_min T5 = 90` · **feasible**

## 07 · Riferimenti Hash · Phase 2A Envelope Artefatti
| Path | Role | SHA256 |
|---|---|---|
| `r18_6_rv3_is2_b_phase2a_per_item_budget_envelope_projection.md` | IS2B_PHASE2A_ENVELOPE_MD | `957df620c4c7030bcf02d7fbc22cae9218a1d10a03ca2531c8c8e570e7d2e2fb` |
| `r18_6_rv3_is2_b_phase2a_per_item_budget_envelope_projection.json` | IS2B_PHASE2A_ENVELOPE_JSON | `7bf8275fa0cf42a38a3ac3bd9f319bd781c4661cd9617417fa5bf3a868178713` |

## 08 · Riferimenti Hash · Addendum P1-N1
| Path | Role | SHA256 |
|---|---|---|
| `r18_6_rv3_is2_b_phase1_n1_tier_reference_budget_addendum.md` | ADDENDUM_P1_N1_MD | `f96f363fd5b3ae77ddce2a48ecc6a9a32cdac11ca2c925207b4c63fde4579667` |
| `r18_6_rv3_is2_b_phase1_n1_tier_reference_budget_addendum.json` | ADDENDUM_P1_N1_JSON | `be378cabda97be24fd2bdd53c0321240f29f3d3cc7610dc0cfa4fdb7662ca193` |
| `r18_6_rv3_is2_b_phase1_n1_closure_manifest.json` | ADDENDUM_P1_N1_CLOSURE_MANIFEST | `89ef2408ead697e286d9bf050c317badcc7529331aba6af50f2cdc6fb152a234` |

## 09 · Riferimenti Hash · Phase 1 Contract (IMMUTABLE)
| Path | Role | SHA256 |
|---|---|---|
| `r18_6_rv3_is2_b_phase1_stat_budget_mechanical_effect_contract.md` | PHASE1_CONTRACT_MD | `a9f411bf1c3efd834ff543a432de00bbb12ed865088e4bb2e8b4330fe49e2dac` |
| `r18_6_rv3_is2_b_phase1_stat_budget_mechanical_effect_contract.json` | PHASE1_CONTRACT_JSON | `167d6e92fd6002343dd24095d22ab9fd1a49446cf277691216bef22990ebb4b8` |
| `r18_6_rv3_is2_b_phase1_final_closure_report.md` | PHASE1_CLOSURE_MD | `4d185cb0efbe484055c2cbac56f5ecb034fa64b337073be43c2bc5c61dfafaf9` |
| `r18_6_rv3_is2_b_phase1_final_closure_report.json` | PHASE1_CLOSURE_JSON | `b8163b9c4bd70d1562ecd8acf721ce0d96cd4f5387d2b7545df6a186cde28de8` |

## 10 · Riferimenti Hash · Chain IS2-A (LOCKED_IMMUTABLE)
| Path | Role | SHA256 |
|---|---|---|
| `r18_6_rv3_is2_a_phase2_full_identity_naming_lore_roster_rev4.md` | IS2A_PHASE2_REV4_MD | `eb3165fd958113fcf346a049d9f745605bf9971ceb711a689d8fd35048519d1d` |
| `r18_6_rv3_is2_a_phase2_full_identity_naming_lore_roster_rev4.json` | IS2A_PHASE2_REV4_JSON | `0d3d4d9b1b704ed8a06276fbc1928802bc9ecf07e21cf59fc99b482439ec4635` |
| `r18_6_rv3_is2_a_phase2_final_closure_report.md` | IS2A_PHASE2_CLOSURE_MD | `5111a12f0378fe129af9a1f3b3dd68fd9208f6fd2a6e1be6aa37cdf27919cd8a` |
| `r18_6_rv3_is2_a_phase2_final_closure_report.json` | IS2A_PHASE2_CLOSURE_JSON | `8f83564410f8a2380e90b3c3e886893121beffcfb97e9201ff13a8f791679a51` |
| `r18_6_rv3_is2_a_phase2_closure_manifest.json` | IS2A_PHASE2_CLOSURE_MANIFEST | `8e4f3c66c38aceaccc103bc75e7ed75e43df43d303f2faeb065d4a7f35a1fb6d` |
| `r18_6_rv3_is2_a_l1_legendary_candidate_selection_report.md` | IS2A_L1_REPORT_MD | `355b261e40082d90fd1450b44f79f58eede38e2cd3a7abbe51881984df3b3e20` |
| `r18_6_rv3_is2_a_l1_legendary_candidate_selection_report.json` | IS2A_L1_REPORT_JSON | `a97e64a4f8e4fc1212dc28b15d65059067cd80550c1b3d73eec9f0df15556849` |
| `r18_6_rv3_is2_a_l1_closure_manifest.json` | IS2A_L1_CLOSURE_MANIFEST | `907f1ef99d9086b0f8edb47e2a40b860d73f5bfd2e0b691497b691400da597bd` |

## 11 · Null-Field Lock · 12 campi × 120 unita'
Per **tutte** le 120 unita' proiettate, i seguenti 12 campi item-level restano ESPLICITAMENTE `null`:

- `main_stat_value` · `constitution_value` · `dexterity_value` · `other_stat_value`
- `selected_affix` · `affix_value`
- `effect_family_selected` · `final_effect` · `effect_value`
- `proc_chance` · `duration` · `cooldown`

**Audit**: `null_count_per_field = 120` (12 campi × 120 unita' = 1440 null cells locked).

## 12 · Item-Level Assignments · Contatori Zero
- `item_level_stat_assignments`: **0**
- `item_level_effect_assignments`: **0**
- `item_level_affix_assignments`: **0**
- `item_level_legendary_final_effect_assignments`: **0**

## 13 · Runtime / Localization / Registry / Apply · NOT IMPLEMENTED
- `runtime_implementation`: **false**
- `localization_implementation`: **false**
- `registry_v3_item_generation`: **NOT_AUTHORIZED**
- `registry_v3_item_apply`: **NOT_AUTHORIZED**
- `db_writes`: **0**
- `runtime_item_id_generated_count`: **0**
- `mutation_forbidden`: **true**

## 14 · Governance Evidence · Tutti Zero
- Modifiche a **backend**: 0
- Modifiche a **frontend**: 0
- Modifiche a **OpenAPI**: 0
- Modifiche a **DB / Registry**: 0
- Modifiche a **test suite**: 0
- Modifiche a **env / secrets**: 0
- Modifiche a **sealed set**: 0
- **Nuovi sigilli**: 0
- Sealed scripts byte-identical: **36/36**
- `lore_meta.py` SHA256: `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` · **INVARIANT**

## 15 · Sealed Integrity
`pytest backend/tests/backend_r18_4_sealed_integrity_test.py` → **6 passed · 36/36 byte-identical** (pre-closure + post-closure).

## 16 · SHA Policy §31 Compliance
- Il `closure_manifest` di Phase 2A NON contiene il proprio `full_file_sha256`.
- Il SHA finale del closure_manifest e' comunicato **esclusivamente in chat**.
- Il PRD.md, dopo l'append idempotente, NON contiene al proprio interno il SHA finale del PRD.

## 17 · Idempotenza PRD (attesa post-append)
| Pattern | Expected occurrence count |
|---|---:|
| `^## R18.6.RV3-IS2-B · Phase 2A` | 1 |
| `^## R18.6.RV3-IS2-B-Phase-1-N1` | 1 (invariato) |
| `^## R18.6.RV3-IS2-B · Phase 1` | 1 (invariato) |
| `^## R18.6.RV3-IS2-A Phase 1` | 1 (invariato) |
| `^## R18.6.RV3-IS2-A Phase 2` | 1 (invariato) |
| `^## R18.6.RV3-IS2-A-L1` | 1 (invariato) |

## 18 · Explicit STOP Block · Roadmap Post-Closure
| Item | Status |
|---|---|
| `R18.6.RV3-IS2-B_Phase_2A` | **CLOSED_PM_LOCKED** |
| `R18.6.RV3-IS2-B-P2B-1` | **PLANNED / HOLD** (menzionato, NON aperto) |
| `R18.6.RV3-IS2-B_Phase_2B` | **HOLD** |
| `R18.6.RV3-NC1` | **HOLD** |
| `R18.6_Gate_11` | **HOLD** |
| `Monaco` | **HOLD** |
| `Registry_v3_Item_Generation_And_Apply` | **NOT_AUTHORIZED** |
| `AFX2` | **RESERVED_FUTURE / NOT_AUTHORIZED** |
| `IS2-A branch (Phase 1 · Phase 2 Rev-4 · L1)` | **LOCKED_IMMUTABLE** |
| `Phase 1 Contract (4 file)` | **IMMUTABLE_UNCHANGED** |
| `Addendum P1-N1 (3 file)` | **DESIGN_LOCKED · PM_APPROVED (invariati)** |
| `Phase 2A envelope (2 file)` | **PM_APPROVED · pm_locked (invariati)** |
| `Cacciatore del Vuoto` | **ACTIVE-DESIGN-READY** (design layer only) |
| `sealed_scripts` | **36/36 byte-identical** |
| `lore_meta.py` anchor | `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` · **INVARIANT** |

---

**ATTENDO VERDICT PM.**
