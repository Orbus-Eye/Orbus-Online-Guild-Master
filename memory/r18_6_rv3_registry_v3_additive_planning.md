# R18.6.RV3 Registry v3 Additive Planning · Cacciatore del Vuoto (pilot)

**Gate**: R18.6.RV3 · **Scope**: Registry v3 Additive Planning · **Class Pilot**: Cacciatore del Vuoto (`cacciatore_del_vuoto`)
**Generated**: 2026-07-08T21:30:00Z · **Status**: DRAFT · PLANNING ONLY · pending PM review
**Governance**: DOCUMENTAL ONLY · NO code · NO DB · NO migrations · NO Registry v3 apply · NO Registry v3 runtime generation · NO item rows · NO item mocks · NO CSV · NO modifica catalogo R18.5 LOCKED
**Seals anchor**: `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`
**Predecessor gates LOCKED**: R18.5 · R18.6 · R18.6.1 · R18.6.2 · G1 · G2 · G3 · G4 · G5
**Successor gate**: R18.6.3-G6 PLAYER_GUIDE (HOLD · attende RV3 review + PM GO)
**Canonical validation**: PASS · zero non-canonical class references · fonte unica `/app/memory/r18_6_1_canonical_27_class_halls_expansion.json`
**Planning target coverage**: ≈120 items · envelope 110-130

---

## 1 · Executive summary

Architettura Registry v3 **additiva** e **modulare** per estendere il Cacciatore del Vuoto **senza modificare il catalogo R18.5 LOCKED** e **senza generare item reali**.

**7 principi architetturali**:
1. **additive**: RV3 aggiunge moduli class-extension SOPRA Registry v2 · MAI riscrive · MAI modifica R18.5
2. **versioned**: ogni module ha version tag + backward-compatibility contract
3. **modular**: un modulo per class_slug · zero cross-class pollution
4. **class-extension-ready**: schema estendibile a 27 classi canoniche (Vuoto = template)
5. **backward-compatible**: R18.5 items invariati · zero rewrite/rigenerazione
6. **auditable**: SHA256 module snapshot · diff traceable
7. **read-only vs R18.5**: separation contract iron-clad

**Deliverable**: SOLO architettura + schema + dependencies. **NO item rows · NO CSV · NO apply · NO runtime · NO mock**.

## 2 · Obiettivi architetturali

1. Additive module schema RV3 che consumi G1-G5 senza modificarli
2. Preservare integrità Registry v2 + R18.5 catalog LOCKED (1500 items)
3. Class-extension model scalabile per 27 classi canoniche
4. Deduplication methodology per riuso universal/shared vs new class-specific
5. Enforce hard-cap policy G1-G5 via metadata flags
6. Legendary semantic handling (ILVL=60 · utility_unique senza overrides)
7. Class_slug + bridge handling (warlock → cacciatore_del_vuoto · mapped_design_only)
8. Versioning strategy semver + no-retroactive-breaking
9. Rollback/read-only strategy · disable module = fallback v2
10. Future class scalability (Monaco/Druido/Alchimista/Bardo/Negromante)

**Constraint assoluti**: NO item rows · NO catalog R18.5 modification · NO runtime apply · NO PvP untested effect (G4 HOLD)

## 3 · Registry v2 preservation strategy

- **Registry v2 = FROZEN** · zero rewrite · zero rigenerazione item · zero schema modification
- **R18.5 catalog LOCK** · 1500 items invariati · `can_be_sold_for_real_money=false` 1500/1500 preserved
- **Separation contract**: read_only vs R18.5 · no write · no delete · no schema mod · reference-only universal + shared_gear_candidates
- **Backward compatibility**: player esistenti + items R18.5 funzionano invariati · RV3 modules opzionali
- **Conflict resolution**: v2 vince (source of truth) · v3 = additive only
- **Audit trail**: SHA256 snapshot + diff per module

## 4 · Registry v3 additive module model

**Structure per module**:
- `module_id`: `class_extension:<class_slug>`
- `module_version`: semver v<M>.<m>.<p>
- `module_scope`: single canonical class
- `module_dependencies`: Registry v2 base + G1-G5 LOCK
- `module_output`: metadata + references + coverage plan (NO item rows)

**6 contract rules**:
1. additive_only · MAI modifica v2
2. isolated_per_class · zero cross-class overlap
3. version_locked_dependencies · aggiornamento dep = version bump
4. read_only_shared · references sono read-only vs v2
5. no_conflict_pollution · zero alterazione altre classi
6. disable_reversible · disable = fallback v2 · no data loss

**Pilot instance**: `class_extension:cacciatore_del_vuoto` · v1.0.0-draft · status=PLANNING_ONLY · runtime_status=disabled

## 5 · Schema field proposal

- `registry_version`: v3.x semver
- `base_registry_reference`: Registry v2 (frozen · read-only)
- `class_extension_modules`: array<module_id>
- `shared_item_references`: read-only pointer a v2
- `universal_eligibility_references`: read-only pointer universal slots
- `new_class_specific_items_future`: PLANNING SLOT ONLY (NO rows)
- `new_shared_family_items_future`: PLANNING SLOT ONLY (NO rows)
- `class_proficiency` → G2 (armor stoffa/cuoio · weapon focus/balestra/pugnale)
- `main_stat_target` → G1 (Int · soft cap 100 non-minimum · linear-flattening)
- `armor_whitelist` = `["stoffa", "cuoio"]` LOCK G2
- `weapon_whitelist` = `["focus", "balestra", "pugnale"]` LOCK G2
- `resource_ref` → Frammenti di Onirade (cap 5 · G4 LOCK)
- `affix_family_refs` → 10 famiglie G5
- `budget_profile_ref` → G5 T1-T5 (1.0→2.7)
- `tier_profile_ref` → T1 Lv1-15 · T2 Lv16-30 · T3 Lv31-45 · T4 Lv46-55 · **T5 Lv56-60**
- `rarity_profile_ref` → G5 (Common 1.00 → Legendary 1.85)
- `ilvl_policy_ref` → G1 formula
- `hard_cap_policy_refs`: resource_cap=5 · marchi_max=5 · durata_max=10T · proc_max=45% · reliability_max=98% · legendary_ilvl=60
- `legendary_semantic_rules`: utility_unique senza overrides · nessun bonus Intelligenza pari a 60 aggiunto
- `runtime_apply_ready` = **false**
- `migration_status` = **planning_only · no execution**

## 6 · Class extension module (template + pilot instance)

**Template**: `class_extension:<class_slug>` · replicabile per 27 classi canoniche

**Pilot instance `class_extension:cacciatore_del_vuoto`**:
- `class_slug`: cacciatore_del_vuoto
- `readiness_gates_refs`: G1-STAT_DESIGN · G2-PROFICIENCY_DESIGN · G3-GAMEPLAY_LOOP · G4-RESOURCE_MECHANIC · G5-EQUIP_DESIGN
- `proficiency_refs`: armor `[stoffa, cuoio]` · weapon `[focus, balestra, pugnale]`
- `resource_ref`: Frammenti di Onirade
- `affix_family_refs`: 10 families (potenza_marchio · durata_marchio · efficacia_drain · qualita_dispel · interazione_frammenti · efficacia_payoff · anti_incorporeo · anti_summon · mobilita_canalizzazione · protezione_rituali)
- `coverage_plan_ref`: **scenario_B_bilanciato** (recommended)
- `hard_cap_metadata_refs`: 6 caps flags
- `legendary_semantic_ref`: utility_unique_no_stat_override
- `runtime_status`: **disabled**
- `status`: planning_draft

## 7 · Shared item reference model

- **Definition**: shared item = item Registry v2 esistente eligible per Vuoto · reference read-only
- **Eligibility criteria (4)**:
  1. armor_type match whitelist Vuoto (stoffa/cuoio)
  2. main_stat compatible (Intelligenza primary · o universal stats)
  3. class_requirement absent OR includes cacciatore_del_vuoto
  4. no forbidden affix (14 G5 rules)
- **Reference only** · NO modification R18.5 · NO item creation al RV3
- **Future item planning refs only**

## 8 · Universal eligibility model

- **Universal slots G5** (EQ-Q6 LOCK): `back` · `neck` · `ring` · `accessory`
- **Affix universal types**: vitalità · mana arcana · regen · movement speed · generic defensive
- **Eligibility shared across classes**: TRUE
- **NO class-specific affix on universal** (anti-monopolio G5 LOCK)
- **Reference-only from Registry v2** · no new universal rows needed (maggior parte già in v2)

## 9 · Deduplication methodology

**Principle**: massimizzare coverage utile · minimizzare duplicazione artificiale

**Avoid duplication of**:
- universal items già in Registry v2 (usa reference)
- shared family items compatible in v2 (usa reference)
- item creati solo per raggiungere 120 (violazione EQ-Q1 · anti-artificial-inflation)

**Prioritize creation of**:
- item class-specific con affix families 1-10 non replicabili altrove
- weapon focus/balestra/pugnale class-specific per Vuoto
- Legendary utility_unique T5 (2 accessory + 3 weapon)
- accessory rituali class-specific (reliquia Vuoto)

**Formula concept**: `total_coverage = new_class_specific + new_shared_family + existing_shared + existing_universal · target ≈120`
**Gap tolerance**: 0-10 accettabile · ≥10 richiede rework
**No padding with fillers** · qualità > quantità · EQ-Q1 LOCK

## 10 · Three numeric coverage scenarios (NON-BINDING · PENDING PM · NO ITEM GENERATION)

| Scenario | new_class_specific | new_shared_family | existing_universal_refs | existing_gear_candidate_refs | Total coverage | Gap | Risk | Runtime apply |
|---|---|---|---|---|---|---|---|---|
| **A · conservative** | 95-105 | 10-15 | 5-10 | 3-5 | 113-135 | 0-5 | **HIGH** (inflation) | ❌ disabled |
| **B · balanced ⭐** | 65-80 | 20-28 | 15-22 | 8-12 | 108-142 | 0-5 | **MEDIUM** (intended trade-off) | ❌ disabled |
| **C · max reuse** | 40-55 | 30-40 | 25-35 | 12-18 | 107-148 | 0-10 | **LOW-MEDIUM** (identity trade-off) | ❌ disabled |

**PM RECOMMENDATION**: **Scenario B balanced_reuse** · onere item creation gestibile + identity preserved + Registry v2 preservation robust.

Target envelope: **110-130** · planning center **≈120**. **NON obbligatorio creare 120 nuove righe**. Obiettivo: max copertura utile / min duplicazione artificiale.

Tutte le stime marcate: **NON-BINDING · PENDING PM · NO ITEM GENERATION**.

## 11 · Tier coverage analysis (Scenario B)

| Tier | stoffa Int | cuoio Int | focus | balestra | pugnale | universal reused | trinket/accessory class-specific | Affix families active |
|---|---|---|---|---|---|---|---|---|
| **T1 Lv1-15** | 4-5 | 3-4 | 1 | 1 | 1 | 3-4 | 0 | 2 lite |
| **T2 Lv16-30** | 7-8 | 6-7 | 2 | 2 | 2 | 5-7 | 0 | 3-4 |
| **T3 Lv31-45** | 8-9 | 5-6 | 2 | 2 | 2 | 6-8 | 1 Rare | 5-7 |
| **T4 Lv46-55** | 9-10 | 5 | 2 | 2 | 2 | 6-8 | 1 Epic | 8-10 |
| **T5 Lv56-60** | 10 | 4 (30% share) | 2 + 1 Legendary | 2 + 1 Legendary | 2 + 1 Legendary | 6-8 | 2 (Epic + 2 Legendary utility_unique) | 10 full |

**Gap notes**: T1-T2 onboarding · T3 Marchi cap 4 (Int50) · T4 Marchi cap 5 (Int90) · T5 Int soft cap 100 target · knee point.

## 12 · Slot coverage analysis

- **Canonical slots approvati EQ-Q6**: `back` · `neck` · `ring` · `accessory`
- **Class-specific slots**: helmet · shoulders · chest · gloves · belt · legs · boots · main_hand · off_hand
- **`trinket` = alias legacy** → riferisce `accessory` (NON nuovo slot operativo · EQ-Q6 LOCK)
- **ring A/B = POSIZIONI** equip · slot canonico è `ring` unico (NO ring1/ring2 canonici)
- **Class-specific coverage**: 10 slot × 5 tier × ~2 rarity = ~100 potential · Scenario B popola ~65-80 new rows
- **Universal coverage**: 4 slot × 5 tier × ~2 rarity = ~40 potential · Scenario B ~15-22 references v2 + eventuali shared_family additions

## 13 · Armor coverage analysis

- **Distribuzione stoffa/cuoio LOCK G5+EQ-Q3**: T1 55/45 · T2 55/45 · T3 60/40 · T4 65/35 · **T5 70/30**
- **stoffa identity EQ-Q3 LOCK**: canalizzazione · Marchio · Drain · Intelligenza primaria
- **cuoio identity EQ-Q3 LOCK**: mobilità · posizionamento · protezione leggera · Intelligenza primaria (**MAI Destrezza hybrid**)
- **Scenario B estimates**:
  - stoffa new class-specific rows: 35-45
  - cuoio new class-specific rows: 20-30
  - shared family stoffa Int references: 10-15
  - shared family cuoio Int references: 5-10
- **NO build Destrezza alternativa** LOCK

## 14 · Weapon coverage analysis

- **Whitelist G2 LOCK**: `focus` · `balestra` · `pugnale`
- **Coefficient direzionali EQ-Q7 LOCK**:
  - focus = **1.00 baseline**
  - balestra = **0.85-0.90 direzionale**
  - pugnale = **0.70-0.80 direzionale**
- **NO scaling Destrezza** LOCK · **NO runtime formula** LOCK
- **Scenario B estimates**:
  - focus new class-specific: 10 (5T × 2R) + 1 Legendary utility_unique T5
  - balestra new class-specific: 10 + 1 Legendary utility_unique
  - pugnale new class-specific: 10 + 1 Legendary utility_unique
  - **Total weapon new rows**: ~33 class-specific
  - shared weapon references: 0-5 (pugnale generic Int-focus se presente v2)
- **Cross-class weapon note**: balestra family condivisa con Cacciatore di Mostri (fisica scaling Dex) · pugnale condiviso con Ladro (Dex) · sharing SOLO via family name · scaling e affix distinti Int-focus Vuoto

## 15 · Affix reference architecture (10 famiglie G5 LOCK)

| ID | Famiglia | Slots eligible | Hard-cap alignment |
|---|---|---|---|
| 1 | potenza_marchio | helmet · chest · accessory · main_hand | no bypass 10T · no bypass Marchi 5 |
| 2 | durata_marchio | helmet · shoulders · chest · accessory | hard cap 10T LOCK |
| 3 | efficacia_drain | gloves · main_hand · off_hand · accessory | combined proc 45% LOCK EQ-Q5 |
| 4 | qualita_dispel | main_hand · off_hand · accessory · back | boss arcane leggendario immune G4 |
| 5 | interazione_frammenti | belt · accessory · off_hand | resource_cap 5 LOCK |
| 6 | efficacia_payoff | chest · accessory · main_hand | anti-random-waste safeguard G4 · summon standard 100% |
| 7 | anti_incorporeo | gloves · main_hand · accessory | identity anti-arcano |
| 8 | anti_summon | shoulders · back · accessory | boss diretto MAI silenziato |
| 9 | mobilita_canalizzazione | boots · legs · belt | no free move · anti-cheese knockback |
| 10 | protezione_rituali | chest · shoulders · back | MAI immunità hard-CC boss enrage/leggendario |

**Affix forbidden rules G5 (14 rules)** LOCK · elenco esteso · rispetto integrale G1-G4.

## 16 · Hard-cap enforcement metadata

| Cap flag | Valore | Fonte LOCK |
|---|---|---|
| `resource_cap_max_frammenti` | **5** | G4 RM-Q1 |
| `marchi_active_max` | **5** | G4 RM-Q5 |
| `marchio_duration_max_turns` | **10** | G4 RM-Q5 |
| `proc_combined_max_percent` | **45%** | G4 + EQ-Q5 |
| `reliability_max_percent` | **98%** | G4 |
| `legendary_ilvl_lock` | **60** | G1 semantic |

**Enforcement rule**: ogni class-extension module DEVE enforcer questi cap · violazione = module rejection al planning gate. NO bypass via affix · NO bypass via Legendary · NO bypass via set bonus futuri.

## 17 · Legendary semantic handling

- **Semantic LOCK G1**: `Legendary ILVL = 60 · nessun bonus Intelligenza pari a 60 aggiunto · utility_unique senza overrides scaling · G1 semantic correction preserved`
- **EQ-Q4 LOCK Multiplier 1.85×**: budget TOTALE inclusa utility_unique · **MAI** 1.85× stat grezze · **MAI** stat-stick generico · utility unica consuma parte del budget
- **Utility_unique examples concept** (QoL · MAI stat override):
  - "Focus di Onirade" T5: Payoff 5F cast time 0.5T
  - "Sigillo del Vuoto" T5 accessory: Marchio +0.5T silence (rispetta hard cap 10T)
  - "Cuore di Onirade" T5 accessory: Payoff 3F feedback esteso
- **NO stat scaling override · NO cap bypass · NO Progressive Discovery stat leak**

## 18 · Class_slug / bridge handling

- **Canonical class_slug**: `cacciatore_del_vuoto` (snake_case lowercase LOCK)
- **Canonical source**: `/app/memory/r18_6_1_canonical_27_class_halls_expansion.json`
- **Legacy bridge warlock**:
  - direction: `warlock → cacciatore_del_vuoto`
  - status: `mapped_design_only`
  - runtime_status: `not_applied · runtime_disabled`
  - auto_derive: **false**
  - note: bridge documentale · MAI applicato runtime · gate futuro dedicated per applicazione
- **Zero non-canonical class references** ✅
- **Canonical validation status**: **PASS** ✅

## 19 · Versioning strategy

- **Registry version**: `v3.<x>.<y>` semver-like · additive iterations
- **Module version**: `v<M>.<m>.<p>` per class-extension module
- **Additive patches**: `+.0.1` · MAI rompono v2
- **Minor bump**: nuovo affix family/slot canonical
- **Major bump**: schema breaking (**MAI retroactive**)
- **Backward compatibility guarantee** LOCK
- **Module snapshot SHA256** · diff traceability per patch

## 20 · Rollback / read-only strategy

- **Rollback mechanism**: disable class-extension module · fallback automatico Registry v2 comportamento
- **No data loss on rollback** · No R18.5 corruption on rollback
- **Read-only contract** vs R18.5 e Registry v2 (iron-clad)
- **Audit trail** su disable: reason · timestamp · reversibile con enable
- **Safe disable ready**: planning-only · NON runtime · no rollback necessario ora
- **Emergency disable capability**: gate futuro implementation deve garantire disable-in-1-op

## 21 · Future class scalability

- **Template ready per 27 classi canoniche** ✅
- **Covered currently**: 1 (Vuoto pilot)
- **Pending readiness**: 26
- **Class extension module template reusable** ✅
- **Per-class gate sequence**: G1 → G2 → G3 → G4 → G5 → RV3 module planning
- **Wave 1 successors**: Monaco · Druido · Alchimista · Bardo · Negromante
- **Wave 1 status**: 🔒 **HOLD** · attende Vuoto pilot closure completa (RV3 CLOSED + Gate 6 CLOSED + eventuale playtest)
- **Cross-class shared resources no pollution** ✅ · **isolation per class module** LOCK

## 22 · Risk register (15 rischi tracciati)

| ID | Rischio | Severity | Status |
|---|---|---|---|
| RV3-R1 | Scenario B eligibility_criteria mal calibrati | MEDIUM | DESIGNED |
| RV3-R2 | Scenario A inflation · budget balance oneroso | MEDIUM | DESIGNED |
| RV3-R3 | Scenario C identity Vuoto attenuata | MEDIUM | DESIGNED |
| RV3-R4 | Backward compatibility break versioning | MEDIUM | DESIGNED |
| RV3-R5 | R18.5 catalog accidentally modified runtime futuro | **HIGH** | TRACKED PG1 |
| RV3-R6 | Universal references duplicati class modules | LOW-MEDIUM | DESIGNED |
| RV3-R7 | Affix combined proc 45% bypass multi-class | MEDIUM | TRACKED PG2 |
| RV3-R8 | Class extension module version drift | LOW | DESIGNED |
| RV3-R9 | Lanterna reserved_future_review revoked → rework | LOW | DESIGNED |
| RV3-R10 | PvP effect HOLD futuro RV3 extension | LOW-MEDIUM | TRACKED PG2 |
| RV3-R11 | Wave 1 successors affix collision | LOW-MEDIUM | DESIGNED |
| RV3-R12 | Item quantity envelope PM re-eval | LOW | OPEN_FOR_PM |
| RV3-R13 | Legendary utility_unique stat sneak | MEDIUM | TRACKED PG1 |
| RV3-R14 | Slot `accessory` vs alias legacy `trinket` confusione | LOW | DESIGNED |
| RV3-R15 | Playtest post-Gate 6 item quantity insufficient | LOW-MEDIUM | TRACKED PG3 |

## 23 · PM Open Questions (RV3-Q1..RV3-Q8)

- **RV3-Q1** · *Scenario B balanced_reuse conferma?* → **a) LOCK Scenario B**
- **RV3-Q2** · *Planning target ≈120?* → **a) LOCK ≈120**
- **RV3-Q3** · *Eligibility validation gate pre-Item Creation?* → **a) LOCK validation gate obbligatoria**
- **RV3-Q4** · *Bridge warlock mapped_design_only + runtime_disabled?* → **a) LOCK**
- **RV3-Q5** · *Versioning semver + no-retroactive-breaking?* → **a) LOCK**
- **RV3-Q6** · *Slot `accessory` con alias legacy `trinket`?* → **a) LOCK · trinket=alias→accessory**
- **RV3-Q7** · *Wave 1 (Monaco/Druido/etc) HOLD fino Vuoto Gate 6+playtest?* → **a) LOCK HOLD Wave 1**
- **RV3-Q8** · *Read-only contract iron-clad vs R18.5+v2?* → **a) LOCK iron-clad**

## 24 · GO/HOLD Recommendation

- **RV3 status**: DRAFT · PLANNING ONLY · pending PM review + risposte RV3-Q1..RV3-Q8
- **Runtime status**: **disabled** · NO apply · NO item generation · NO CSV · NO mock
- **Gate 6 PLAYER_GUIDE**: 🔒 **HOLD** · attende PM ACK RV3 + GO esplicito
- **Wave 1 successors**: 🔒 **HOLD** · attende Vuoto pilot closure completa
- **NO Gate 6 auto-start · NO Monaco kickoff · NO R18.3f kickoff · NO Item Creation auto-start**
- **Recommended next step**: PM review RV3 architecture + risposte RV3-Q1..RV3-Q8 → RV3 CLOSED verdict → GO Gate 6 PLAYER_GUIDE

---

## 🛑 STOP obbligatorio a fine RV3 · Non procedere a Gate 6 senza nuovo GO PM

Attendo PM review Registry v3 Additive Planning + risposte a **RV3-Q1..RV3-Q8**. Nessun auto-start · nessuna modifica R18.5/R18.6/R18.6.1/R18.6.2/G1/G2/G3/G4/G5 (tutti LOCKED).
