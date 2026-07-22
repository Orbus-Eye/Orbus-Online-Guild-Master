# R18.6.RV3-IS2-B Phase 1 · Stat Budget & Mechanical Effect Contract

**Gate**: `R18.6.RV3-IS2-B Phase 1 · Stat Budget & Mechanical Effect Contract`
**Regime**: DOCUMENTAL ONLY · READ-ONLY · NO APPLY
**Stato**: **PATCHED WITH PM VERDICTS Q01–Q08** · **PM OPEN QUESTIONS = 0** · **FORMAL CLOSURE PENDING (executed same dispatch)**
**Baseline consumata (read-only)**: R18.5 Itemization · CdV G1-G5 · AFX1 · IC1 · IS1 · IS2-A Phase 1 · IS2-A Phase 2 Rev-4 · IS2-A-L1
**Lingua**: Italiano
**Regola cardine**: contratto (come assegnare) senza fissare valori numerici item-by-item. Coefficient weapon ora `DESIGN_LOCKED` post-verdict PM.

---

## 1. Executive summary

Phase 1 di IS2-B consegna il **contratto di stat budget** e la **taxonomy meccanica** che governeranno l'assegnazione futura di stat, coefficienti, budget e effetti ai 111 nomi attivi del corpus (108 non-Legendary selected + 3 Legendary PM-selected). Post-verdict PM: Q01-Q08 (10 sub-questions) **RESOLVED**, `blocking residue = 0`. Coefficient weapon, slot bands, rounding, stacking, Legendary directions e utility/effect ceilings sono **DESIGN_LOCKED**. Item-by-item numeric assignment resta `null` (Phase 2 competence).

## 2. Scope

- **In scope Phase 1**: contract-level definitions (§7-§54), PM-adjudicated verdicts Q01-Q08 (§55), Phase 2 readiness (§56), GO/HOLD (§57).
- **Out of scope Phase 1**: numeri item-by-item · effetti finali · affix assignment · Legendary effect finali · Registry generation · Registry apply · migration · DB writes · runtime item · sealed test refactor.

## 3. Governance

- DOCUMENTAL ONLY · READ-ONLY · NO APPLY.
- Zero mod backend/frontend/OpenAPI/DB/Registry/test/env/sigilli.
- 36/36 sigilli byte-identical; `lore_meta.py` anchor invariato.
- §31 rispettato: nessun file embed il proprio SHA finale.
- Ramo IS2-A (Phase 1, Phase 2 Rev-4, L1) è **LOCKED/IMMUTABLE**.

## 4. Source of truth (consumata read-only)

| Fonte | Versione | Ruolo |
|---|---|---|
| R18.5 Itemization baseline | ratificata | Budget framework |
| CdV G1-G5 | ratificati | Gate design storici |
| AFX1 | ratificato | Affix architecture |
| IC1 | ratificato | Item contract genesi |
| IS1 | IS1-SEALED | Preserved identity locks |
| IS2-A Phase 1 | CLOSED | Naming lock foundations |
| IS2-A Phase 2 Rev-4 | PM_LOCKED | Roster 120 baseline |
| IS2-A-L1 | CLOSED / PM-LOCKED | Legendary PM-selected trio |

## 5. IS2-A dependency

Phase 1 IS2-B eredita **senza riaprire**: corpus attivo 111 (108 non-Leg + 3 Leg PM-selected), 9 Preserved (IS1-SEALED), 3 contingency dormant (0 generated names), Legendary trio: «Veste di Onirade» · «Occhio del Faro Rovesciato» · «Balestra della Traiettoria certa».

## 6. Active roster baseline

- Total active new design names: **111**
- Non-Legendary selected: **108** · Legendary PM-selected: **3**
- Preserved identities: **9** · Dormant contingency: **3** (0 generated)

## 7. Main-stat contract

- **Main stat CdV**: **Intelligenza**.
- **Priority order**: Intelligenza → Costituzione → Destrezza.
- **Soft cap Intelligenza**: 100.
- **Item-level assignment**: `null` in Phase 1 (contratto = come, non quanto).

## 8. Secondary-stat contract

- **Costituzione**: secondary defensive priority.
- **Destrezza**: tertiary utility/opportunistic priority.
- **Vietati**: Destrezza main stat CdV · dual-primary Int/Dex · conversione retroattiva Dex→Int · build CdV Dex-primary.

## 9. Tier budget architecture

| Tier | Intelligenza band |
|---|---|
| T1 | 10–25 |
| T2 | 25–45 |
| T3 | 45–70 |
| T4 | 70–90 |
| T5 | 90–115 |

Item-level value = `null` in Phase 1.

## 10. Rarity budget architecture

**Rarity multiplier = TOTAL BUDGET MULTIPLIER** (incluse utility uniche):

| Rarity | Multiplier |
|---|---:|
| Common | 1.00 |
| Uncommon | 1.15 |
| Rare | 1.35 |
| Epic | 1.60 |
| Legendary | 1.85 |

Non additivo sopra effetti già completi. Non moltiplicatore separato per sotto-budget. Anti-double-counting §14.

## 11. Affix budget boundary

**Affix slots**: T1=1 · T2=2 · T3=3 · T4=4 · T5=5.
Overlay: **140 family occurrences** eleggibili su **120 blueprint units** = **eligibility** (chi PUÒ prendere quale famiglia), non assegnazione.

## 12. Utility budget boundary (Q07-locked)

- Utility budget = sotto-porzione del budget totale post-multiplier.
- **Utility share interna (Q07 · DESIGN_LOCKED)**:
  - non-Legendary utility ≤ **40%** del combined effect+utility budget
  - Legendary utility ≤ **50%** del combined effect+utility budget
  - Resto = effect budget OPPURE restituito al base-stat budget
- Include: PAYOFF_UTILITY, DISPEL_UTILITY, CHANNEL_MOBILITY, RITUAL_PROTECTION.
- Anti-double-counting §14 preservato.

## 13. Effect budget boundary (Q07-locked)

- **Combined effect + utility ceiling per rarity (Q07 · DESIGN_LOCKED · MAXIMUM CAPS, non target)**:
  - Common ≤ **10%** total item budget
  - Uncommon ≤ **20%**
  - Rare ≤ **30%**
  - Epic ≤ **40%**
  - Legendary ≤ **50%**
- **Budget statistico minimo**: Common ≥90% · Uncommon ≥80% · Rare ≥70% · Epic ≥60% · Legendary ≥50%.
- Budget non speso **NON diventa potenza extra esterna**.
- Effect status default: `DIRECTION_ONLY`. Item-level `effect_value = null` in Phase 1.

## 14. Anti-double-counting rule

- **TOTAL ITEM BUDGET** = **unica sorgente di potenza**, comprendente: base stats + mechanical effects + utility + affix contribution + unique Legendary contribution.
- **Vietato**: `rarity multiplier + full-stat budget + full-effect budget + full-affix budget + free unique utility`.
- Rarity multiplier applicato **una sola volta** al totale globale.
- Ogni componente consuma il medesimo totale. Nessun affix replicato tra family diverse.

## 15. Slot budget bands (Q03 · DESIGN_LOCKED)

**4 bande base-budget relative** (relative weights, NON statistiche/multiplier separati per affix/coefficienti aggiuntivi):

| Banda | Weight | Slots |
|---|---:|---|
| **S** Primary | **1.00** | main_hand · chest · legs |
| **A** Major | **0.85** | head · shoulders · hands · feet |
| **B** Standard | **0.70** | neck · back · waist · off_hand |
| **C** Utility | **0.55** | wrist · ring · accessory |

**Utility slot chiarimento**: wrist/ring/accessory hanno budget statistico base inferiore ma possono usare quota relativamente maggiore del proprio budget per utility/conditional effect/identity effect. NON aumenta il budget totale, modifica solo la distribuzione interna.

## 16. Armor budget

Formula concettuale unica (Q03/Q01/Q02 applicati insieme):
`tier reference budget × slot band multiplier × weapon coefficient (se applicabile) × rarity multiplier = TOTAL ITEM BUDGET`
Applicare ogni moltiplicatore **una sola volta** (§14).

## 17. Stoffa budget

Direzione: **potenza rituale · canalizzazione · Marchio · Drenaggio · dissipazione**. Costituzione: profilo secondary basso/medio. No primary mobility. No identità Ladro / Cacciatore di Mostri.

## 18. Cuoio budget

Direzione: **mobilità · Costituzione · protezione rituale · opportunità · controllo distanza**. Costituzione: profilo medio/alto. **Vietato** Dex-primary · identità Ladro · identità Cacciatore di Mostri.

## 19. Weapon coefficient architecture (Q01/Q02 · DESIGN_LOCKED)

| Weapon family | Coefficient | Status |
|---|:---:|---|
| **focus** | **1.00** | **DESIGN_LOCKED** |
| **balestra** | **0.88** | **DESIGN_LOCKED** (Q01) |
| **pugnale** | **0.78** | **DESIGN_LOCKED** (Q02) |

**Regola di applicazione**: `weapon coefficient` si applica al budget totale base della weapon unit **prima** del rarity multiplier. Non applicare separatamente a stat/effetti/utility/affix.

**Formula concettuale unica**: `tier-slot base budget × weapon coefficient × rarity multiplier = TOTAL AVAILABLE ITEM BUDGET` → poi distribuito fra stat/effetti/utility/affix. Nessuna componente aggiunta fuori dal totale.

## 20. Focus contract (DESIGN_LOCKED)

- Focus = **primary class weapon** CdV.
- Coefficient = **1.00** (DESIGN_LOCKED · baseline immutabile).
- **PUÒ** autorizzare: maggiore potenza diretta · migliore efficienza canalizzazione · migliore coerenza Marchio/Drenaggio.
- **NON PUÒ** autorizzare: resource cap increase · Frammenti oltre 5 · focus bonus oltre 2 per resource segment · boss safeguard bypass.

## 21. Balestra contract (Q01 · DESIGN_LOCKED · 0.88)

- Balestra = **ranged ritual signature**.
- Coefficient = **0.88** (DESIGN_LOCKED · banda 0.85-0.90).
- **Razionale PM verbatim**: identità a distanza · sicurezza posizionale · precisione/dissipazione mirata · minore potenza vs focus · nessuna deriva Dex-primary.
- Budget direzione: precisione · distanza · proiezione · dissipazione mirata.
- **Vietato**: trasformazione Dex primaria · arco · weapon family generica.

## 22. Pugnale contract (Q02 · DESIGN_LOCKED · 0.78)

- Pugnale = **ritual/opportunistic weapon**.
- Coefficient = **0.78** (DESIGN_LOCKED · banda 0.70-0.80).
- **Razionale PM verbatim**: rischio da prossimità · identità rituale/opportunistica · minore potenza strutturale vs focus · compensazione parziale per rischio ravvicinato · nessuna conversione Dex-primary.
- **Ritual close bonus**: **≤ 1 per applicazione Marchio**, refresh Marchio **NON resetta** il limite.
- **0.78 NON autorizza**: proc aggiuntivi fuori budget · secondo bonus ravvicinato · generazione gratuita Frammenti · superamento cap G4.

## 23. Effect taxonomy (13 famiglie)

1. `PASSIVE_STAT` · 2. `CONDITIONAL_STAT` · 3. `MARK_INTERACTION` · 4. `DRAIN_INTERACTION` · 5. `FRAGMENT_INTERACTION` · 6. `PAYOFF_UTILITY` (tecnico interno, non player-facing "Payoff") · 7. `DISPEL_UTILITY` · 8. `ANTI_INCORPOREAL` · 9. `ANTI_SUMMON` · 10. `CHANNEL_MOBILITY` · 11. `RITUAL_PROTECTION` · 12. `WEAPON_IDENTITY_EFFECT` · 13. `LEGENDARY_UNIQUE_EFFECT`.

## 24. Effect status taxonomy

`DIRECTION_ONLY` · `BUDGET_CLASSIFIED` · `DRAFT_REQUIRED` · `PM_REVIEW` · `PM_APPROVED` · `DESIGN_LOCKED`. In Phase 1: item-level `effect = null` · `effect value = null`.

## 25. AFX1 relationship

AFX1 read-only. Nessuna modifica alle affix families. Nessuna nuova family introdotta in Phase 1. Eligibility 140/120 (§11).

## 26. Mark boundaries

- **Active marks hard cap = 5** (immutabile).
- **Mark duration hard cap = 10** (immutabile).
- Ogni MARK_INTERACTION rispetta i cap. No extension automatica.

## 27. Drain boundaries

- Marked target required (no unmarked resource generation, §37).
- No permanent cross-phase drain.
- Boss safeguard required (§34).

## 28. Fragment boundaries

- **Frammenti cap = 5** (immutabile).
- No cap increase effects.
- Focus bonus ≤ **2** per resource segment.

## 29. Dispel boundaries

- Target definition required.
- No unconditional boss buff dispel.
- Boss safeguard required.

## 30. Anti-incorporeal boundaries

- Valid incorporeal targets only.
- Budget classification: utility_budget o weapon_identity_effect.
- No boss safeguard bypass via combo.

## 31. Anti-summon boundaries

- **Solo** su **valid boss-summoned add** con safeguard/condition/budget dichiarati.
- Vietata unconditional summon deletion (§37).
- Vietata boss immunity bypass (§34).

## 32. Channel-mobility boundaries

- Mobility during channel only.
- No class-mobility-primary drift.
- Compatibile con focus/balestra/pugnale identity.

## 33. Ritual-protection boundaries

- Defensive rituali · no tank/healer role overlap · combined proc cap §35 rispettato.

## 34. Boss safeguards

**Vietato**:
- direct boss nullification
- boss immunity bypass
- unconditional summon deletion
- ignore boss safeguard

Direzioni future ammesse **solo** su: **valid boss-summoned add** con safeguard/condition/budget. Ogni ANTI_SUMMON, DISPEL_UTILITY, ANTI_INCORPOREAL deve dichiarare `boss_safeguard_required = true` (schema §45).

## 35. Proc cap rules

- **Combined proc cap = 45%** su qualsiasi combinazione multi-effect.
- Nessun singolo effetto oltre 45% proc rate.
- Combinazione additive-before-cap; nessuna composizione moltiplicativa può eludere il cap.

## 36. Hard-cap protections (immutabili)

| Voce | Valore |
|---|:---:|
| Frammenti cap | **5** |
| Marchio duration hard cap | **10** |
| Active marks hard cap | **5** |
| Combined proc cap | **45%** |
| Focus bonus per resource segment | **≤ 2** |
| Pugnale ritual-close bonus per Mark application | **≤ 1** |

Nessun item, combinazione, affix, Legendary unique può violare questi cap.

## 37. Forbidden mechanics

Elenco esteso (post-Q08):

- resource cap increase
- active marks > 5 · Mark duration > 10
- unmarked resource generation
- direct boss nullification · boss safeguard bypass
- P2W (§38)
- dual Int/Dex primary · cross-class optimal item
- focus bonus > 2 per segment · ritual-close bonus > 1 per Mark
- untested PvP effects · cross-phase persistence
- random full-resource waste
- **mechanical set bonuses** (2p/4p/6p, set progression, set-exclusive proc) — **FORBIDDEN · DESIGN_LOCKED (Q08)**. Consentite solo **cohesive naming families** senza collegamento meccanico / bonus cumulativo / requisito equipaggiamento congiunto.

## 38. Anti-P2W

`can_be_sold_for_real_money = false` per: combat item · progression item · ranking item · economy-impacting item. La potenza NON deriva da acquisto real-money. Conflict con monetizzazione → gameplay integrity wins.

## 39. Legendary chest boundary — «Veste di Onirade» (Q06a · DESIGN_LOCKED direction)

- **Blueprint**: `cdv_t5_chest_stoffa_002` · slot chest · subtype stoffa
- **Mechanical identity pillar**: **`RITUAL_CHANNEL_PROTECTION`**
- **Budget class**: **`LEGENDARY_DEFENSIVE_RITUAL`** · rarity Legendary · multiplier 1.85
- **Direzione autorizzata (Q06a verbatim)**: protezione durante canalizzazione · stabilità rituale · resilienza tramite Costituzione · riduzione rischio durante Drain.
- **Unique-effect boundary**: `LEGENDARY_UNIQUE_EFFECT` · status **`DIRECTION_ONLY`** in Phase 1.
- **Vietato (Q06a verbatim)**: invulnerabilità · immunità completa · assorbimento illimitato · annullamento totale delle interruzioni · persistenza cross-phase · superamento di cap.
- **Effetto finale**: consumerà il budget Legendary totale, NON aggiuntivo sopra il moltiplicatore 1.85.
- `effect_final_phase_1 = null` · `effect_value = null` · `proc_chance = null` · `duration = null` · `cooldown = null`.

## 40. Legendary focus boundary — «Occhio del Faro Rovesciato» (Q06b · DESIGN_LOCKED direction)

- **Blueprint**: `cdv_t5_main_hand_focus_001` · slot main_hand · subtype focus
- **Mechanical identity pillar**: **`IDENTIFY_MARK_ORCHESTRATION`**
- **Budget class**: **`LEGENDARY_PRIMARY_CONTROL`** · rarity Legendary · multiplier 1.85 · coefficient 1.00
- **Direzione autorizzata (Q06b verbatim)**: migliore orchestrazione Identify→Mark · efficienza controllata del Drain · interazione condizionale con Frammenti · leggibilità bersaglio prioritario.
- **Unique-effect boundary**: `LEGENDARY_UNIQUE_EFFECT` + `WEAPON_IDENTITY_EFFECT` · status **`DIRECTION_ONLY`** in Phase 1.
- **Vietato (Q06b verbatim)**: aumento cap Frammenti oltre 5 · generazione Frammenti senza Marchio · focus bonus oltre 2 per segment · Marchi attivi oltre 5 · durata Marchio oltre 10 · proc combinato oltre 45% · boss safeguard bypass.
- **Nota bilanciamento**: focus resta arma primaria. La Legendary NON deve rendere le altre famiglie inutilizzabili.
- `effect_final_phase_1 = null` · `effect_value = null` · `proc_chance = null` · `duration = null` · `cooldown = null`.

## 41. Legendary balestra boundary — «Balestra della Traiettoria certa» (Q06c · DESIGN_LOCKED direction)

- **Blueprint**: `cdv_t5_main_hand_balestra_001` · slot main_hand · subtype balestra
- **Mechanical identity pillar**: **`RANGED_PRECISION_DISPEL`**
- **Budget class**: **`LEGENDARY_RANGED_UTILITY`** · rarity Legendary · multiplier 1.85 · coefficient 0.88
- **Direzione autorizzata (Q06c verbatim)**: precisione rituale a distanza · Marchio mirato · dissipazione selettiva · interazione anti-summon su bersagli validi.
- **Unique-effect boundary**: `LEGENDARY_UNIQUE_EFFECT` + `WEAPON_IDENTITY_EFFECT` · status **`DIRECTION_ONLY`** in Phase 1.
- **Vietato (Q06c verbatim)**: colpo garantito · precisione assoluta · eliminazione automatica evocazioni · nullificazione diretta boss · bypass immunità boss · trasformazione in arma Dex-primary.
- **Anti-summon futuro**: consentito solo su **valid boss-summoned add** con safeguard + condizione + budget dichiarati.
- `effect_final_phase_1 = null` · `effect_value = null` · `proc_chance = null` · `duration = null` · `cooldown = null`.

## 42. Shared-family limits

Effetti WEAPON_IDENTITY_EFFECT non replicabili identici tra weapon-family diverse. Affix families condivise coerenti con AFX1. Combined proc cap §35 non bypassabile via stacking.

## 43. Universal-neutral limits

Neutral effect budget cap = baseline utility budget. Neutral vs class-specific balance biased verso class-specific per identity preservation.

## 44. Class-specific limits

CdV effects: coerenti con Marchio/Drenaggio/Frammenti loop. Vietata deriva Negromante · identità Ladro · Cacciatore di Mostri. Vietata conversione retroattiva Dex→Int.

## 45. Future per-item schema

Campi previsti per ogni item del corpus 111. In Phase 1: tutti numerici = `null`, categoriali contract-derived.

| Campo | Tipo | Popolamento | Phase 1 value |
|---|---|---|---|
| `blueprint_code` | string | IS2-A | populated |
| `tier` | int 1-5 | IS2-A | populated |
| `rarity` | enum | IS2-A | populated |
| `slot` | enum 14 | IS2-A | populated |
| `equipment_category` | enum | IS2-A | populated |
| `armor_type` | enum | IS2-A | populated |
| `weapon_family` | enum | IS2-A | populated |
| `identity_class` | string | IS2-A | populated |
| `stat_budget_class` | enum {S, A, B, C} | IS2-B P1 | populated (Q03) |
| `main_stat` | enum | IS2-B P1 | Intelligenza (default CdV) |
| `main_stat_band` | enum tier | IS2-B P1 | populated |
| `main_stat_value` | int | IS2-B P2 | **null** |
| `secondary_stat_profile` | dict | IS2-B P1 | populated |
| `weapon_coefficient_status` | enum | IS2-B P1 | DESIGN_LOCKED |
| `weapon_coefficient_value` | float | IS2-B P1 (via Q01/Q02) | focus=1.00 / balestra=0.88 / pugnale=0.78 (contract), item-level = **null** |
| `base_budget` | float | IS2-B P2 | **null** |
| `rarity_multiplier` | float | IS2-B P1 | populated (§10) |
| `slot_band_multiplier` | float | IS2-B P1 | populated (§15) |
| `utility_budget` | float | IS2-B P2 | **null** |
| `effect_budget` | float | IS2-B P2 | **null** |
| `affix_budget` | int slots | IS2-B P1 | populated (§11) |
| `eligible_effect_families` | list | IS2-B P1 | populated |
| `effect_direction` | list | IS2-B P1 | populated (Legendary pillar) |
| `effect_status` | enum | IS2-B P1 | DIRECTION_ONLY default |
| `effect_value` | numeric | IS2-B P2 | **null** |
| `mechanic_boundary_flags` | dict | IS2-B P1 | populated |
| `boss_safeguard_required` | bool | IS2-B P1 | populated |
| `anti_p2w` | bool | IS2-B P1 | true |
| `validation_status` | enum | IS2-B P1 | populated |
| `PM_status` | enum | IS2-B P1 | populated |

## 46. Validation rules

- `main_stat` default Intelligenza per CdV.
- `main_stat_band` in tier bands §9.
- `rarity_multiplier` in §10.
- `slot_band_multiplier` in §15.
- `weapon_coefficient_value` = 1.00 / 0.88 / 0.78 secondo family (§19).
- Ogni effect dichiara status (§24) e family (§23).
- ANTI_SUMMON / DISPEL_UTILITY / ANTI_INCORPOREAL → `boss_safeguard_required = true`.
- `anti_p2w = true` per combat/progression/ranking/economy items.
- No hard-cap violation (§36). No dual Int/Dex primary.
- **No mechanical set bonuses** (§37 · Q08).

## 47. Rounding policy (Q04 · DESIGN_LOCKED)

- **Internal precision**: **4 decimal places**.
- Non arrotondare durante passaggi intermedi.
- **Ordine di applicazione**: `base budget → slot multiplier → weapon coefficient → rarity multiplier → budget split → final rounding`.
- **Metodo**: **`ROUND_HALF_UP`** (non banker's rounding).
- **Output futuro (Phase 2)**:
  - flat stats = integer
  - percentages = 1 decimal
  - durations = 1 decimal second
  - coefficients = 2 decimal places
  - internal budget = 4 decimal places
- **Residui di arrotondamento**: assegnati **prima alla main stat**, poi alla secondary defensive stat. Mai creare budget aggiuntivo.

## 48. Stacking policy (Q05 · DESIGN_LOCKED)

- **Passive flat stats**: stacking = **ADDITIVE** (entro budget item · soft cap · cap sistema).
- **Stesso unique effect nominale**: **NON_STACKING** · resolution = **`HIGHEST_EFFECTIVE_VALUE_WINS`**.
- **Effetti stessa family (default)**: **NON_STACKING**. Additivi **solo** se il futuro record dichiara `stacking_mode = ADD_WITHIN_CAP` con cap esplicito + budget esplicito + validazione dedicata.
- **Durate (default)**: reapplication = **`REFRESH`**. NON estendere automaticamente. Estensione solo con `stacking_mode = EXTEND_WITHIN_HARD_CAP`. Mark duration ≤ 10 preservato.
- **Proc chance**: combinazione **`ADDITIVE_BEFORE_CAP`** · cap combined ≤ **45%**. Nessuna composizione moltiplicativa può eludere il cap.
- **Legendary effects stessa identità**: **NON_STACKING**. Duplicazione futura → highest valid effect wins. Nessuna sinergia moltiplicativa automatica tra Legendary.

## 49. Conflict-resolution policy

- Stessa family, 2 effect: prevale il più restrictive (safeguard-oriented).
- Item-level vs class-level: prevale class-level (identity lock).
- Phase 1 contract vs IS2-A output: prevale IS2-A (LOCKED/IMMUTABLE).
- Contract vs sealed scripts: prevale sealed scripts (36/36 byte-identical).

## 50. Fallback policy

- Ogni Q01-Q08 è ora **RESOLVED** dal PM. Fallback non più applicabile.
- Se un futuro record introduce hard-cap violation → STOP, escalation PM, no autonomous decision.
- Se un futuro record introduce forbidden mechanic → STOP, escalation PM.

## 51. Migration boundary

Zero migration in Phase 1. Nessun DB write, nessuna schema alteration, nessun runtime mutation. Migration a 111 nomi → Phase 2 con Registry v3 apply autorizzato separatamente (attualmente NOT AUTHORIZED).

## 52. Registry boundary

`Registry_status` corpus 111: **`NOT_GENERATED`**. Registry v3 Item Generation & Apply: **`NOT_AUTHORIZED`**. Zero Registry entry, zero apply, zero runtime item.

## 53. Implementation boundary

Backend/Frontend/OpenAPI/Test suite/`.env`: nessuna modifica. Sigilli 36/36 byte-identical. Anchor `lore_meta.py` SHA `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` INVARIATO.

## 54. Risk register

| # | Rischio | Impact | Mitigazione contract-level |
|---|---|:---:|---|
| R1 | Balestra/Pugnale coefficient impact bilanciamento | risolto | Q01=0.88 · Q02=0.78 DESIGN_LOCKED |
| R2 | Slot budget bands sbilanciate | risolto | Q03: S/A/B/C = 1.00/0.85/0.70/0.55 |
| R3 | Stacking leak su proc cap | risolto | Q05 ADDITIVE_BEFORE_CAP + 45% cap |
| R4 | Rounding boundary ambigua | risolto | Q04 ROUND_HALF_UP final-only |
| R5 | Legendary direction troppo forte / debole | risolto | Q06a/b/c DIRECTION_ONLY locked |
| R6 | AFX1 family drift durante Phase 2 | mitigato | AFX1 read-only |
| R7 | Cross-phase persistence unintended | mitigato | §37 forbidden, §49 conflict |
| R8 | Boss safeguard bypass via combo | mitigato | §34, schema flag |
| R9 | Dex-primary drift CdV | mitigato | §8, §18, §37 |
| R10 | Item-by-item numeric leak in Phase 1 | mitigato | Vincolo hard: item-level numeric = null |
| R11 | Set-bonus power creep | risolto | Q08 mechanical set bonuses FORBIDDEN |
| R12 | Utility/effect share power creep | risolto | Q07 ceilings 10/20/30/40/50% + share caps |
| R13 | Anti-double-counting leak | risolto | §14 TOTAL BUDGET single-source |

## 55. PM open questions — TUTTE RESOLVED (Q01-Q08 · 10 sub-questions)

| question_id | Status | Verdict PM · Sintesi |
|---|---|---|
| `IS2B_P1_Q01` | **RESOLVED** | Balestra coefficient = **0.88** DESIGN_LOCKED |
| `IS2B_P1_Q02` | **RESOLVED** | Pugnale coefficient = **0.78** DESIGN_LOCKED |
| `IS2B_P1_Q03` | **RESOLVED** | Slot bands S/A/B/C = **1.00 / 0.85 / 0.70 / 0.55** DESIGN_LOCKED |
| `IS2B_P1_Q04` | **RESOLVED** | Rounding = **ROUND_HALF_UP** final-only · 4 decimal internal · residui → main stat |
| `IS2B_P1_Q05` | **RESOLVED** | Stacking = ADDITIVE passive · NON_STACKING unique + family + Legendary · REFRESH durate · ADDITIVE_BEFORE_CAP proc |
| `IS2B_P1_Q06a` | **RESOLVED** | Veste = **RITUAL_CHANNEL_PROTECTION** / LEGENDARY_DEFENSIVE_RITUAL · DIRECTION_ONLY |
| `IS2B_P1_Q06b` | **RESOLVED** | Occhio = **IDENTIFY_MARK_ORCHESTRATION** / LEGENDARY_PRIMARY_CONTROL · DIRECTION_ONLY |
| `IS2B_P1_Q06c` | **RESOLVED** | Balestra Leg = **RANGED_PRECISION_DISPEL** / LEGENDARY_RANGED_UTILITY · DIRECTION_ONLY |
| `IS2B_P1_Q07` | **RESOLVED** | Ceilings **10/20/30/40/50%** combined effect+utility per rarity · utility share 40% non-Leg · 50% Leg |
| `IS2B_P1_Q08` | **RESOLVED** | Mechanical set bonuses = **FORBIDDEN · DESIGN_LOCKED**; cohesive naming families permitted (no meccanica) |

**Blocking questions residue = 0** · **Open PM questions = 0** · Fase Q-resolution: **COMPLETE**.

## 56. Phase 2 readiness

Phase 1 è **contract-complete** con verdetti PM Q01-Q08 integrati. Phase 2 può aprire **solo dopo** autorizzazione PM esplicita successiva. Attualmente Phase 2 = **HOLD / NOT AUTHORIZED**.

Phase 2 focus (out of scope Phase 1): item-by-item main_stat value, coefficient value effettivi, base budget, utility/effect budget, effect value, affix assignment, Legendary unique effect finali, validation full-corpus, migration boundary review.

## 57. GO/HOLD recommendation

**Agent recommendation**: **CLOSURE READY** — Phase 1 draft aggiornato con i 10 verdetti PM è completo, deterministic, self-contained. Formal closure eseguibile nello stesso dispatch. Phase 2 rimane HOLD.

**Stato finale Phase 1**:

```
R18.6.RV3-IS2-B Phase 1        = CLOSURE READY / PM-APPROVED / Q01-Q08 RESOLVED (10/10)
                                 → CLOSED / PM-LOCKED (via closure artifacts in same dispatch)
R18.6.RV3-IS2-B Phase 2        = HOLD / NOT AUTHORIZED
R18.6.RV3-NC1                  = HOLD / NOT AUTHORIZED
R18.6 Gate 11                  = HOLD / NOT AUTHORIZED
Registry v3 Item Gen & Apply   = NOT AUTHORIZED
Monaco                         = HOLD / NOT AUTHORIZED
AFX2                           = RESERVED FUTURE / NOT AUTHORIZED

IS2-A ramo (Phase 1, Phase 2 Rev-4, L1) = LOCKED / IMMUTABLE
Cacciatore del Vuoto = ACTIVE-DESIGN-READY (design layer only)

ATTENDO VERDICT PM.
```
