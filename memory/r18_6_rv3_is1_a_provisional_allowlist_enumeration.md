# R18.6.RV3-IS1-A · Provisional Allowlist Enumeration & Binding Review

**Regime**: DOCUMENTAL ONLY · READ-ONLY DISCOVERY · ITALIANO

**Generato**: 2026-07-12T06:51:18.260136+00:00

**Sealed integrity expected**: 36/36

**Anchor SHA `lore_meta.py`**: `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` — INVARIANT

**SHA policy §31**: no_self_referential_sha_embedded_in_this_file

**IS1 roster generation status**: `PAUSED_pending_pm_verdict_on_IS1_A`


## §1 · Governance Locks (immutati)

| Lock | Value |
|---|---|
| `apply_authorized` | `False` |
| `item_creation_authorized` | `False` |
| `registry_apply_authorized` | `False` |
| `field_addition_authorized` | `False` |
| `backfill_authorized` | `False` |
| `class_slug_write_count` | `0` |
| `db_write_count` | `0` |
| `mutation_forbidden` | `True` |
| `sealed_files_immutability` | `True` |
| `backend_frontend_openapi_change_count` | `0` |
| `prd_appended_in_this_dispatch` | `False` |
| `is1_source_artifacts_created` | `False` |
| `auto_binding_authorized` | `False` |
| `auto_promotion_authorized` | `False` |

## §2 · Catena di Gate Prerequisiti

- `R18.6.RV3-EV`
- `R18.6.RV3-EV-F1`
- `R18.6.RV3-EV-F2`
- `R18.6.RV3-AFX1`
- `R18.6.RV3-IC1`

## §3 · Discovery Criteria (PM Dispatch Verbatim)

### §3.1 · Common Filters (obbligatori per ogni candidato)

| Field | Requirement |
|---|---|
| `item_binding_policy` | `soft` |
| `stat_tags_must_include` | `intellect` |
| `class_tags_must_not_include` | `warlock` |
| `lore_tags_must_not_include` | `['vuoto', 'oblio']` |
| `mutation_required` | `False` |
| `excluded_by_EV_F2` | `False` |

### §3.2 · Bucket · Weapon literal G2 (expected=2)

- Allowed families: `focus, dagger, pugnale (semantic alias)`
- Forbidden families: `tome, staff, grimoire, wand, rod, flask, bow, instrument, flute`
- Slot types: `['weapon', 'weapon_main']`

### §3.3 · Bucket · Armor stoffa/cuoio (expected=11)

- Armor tag pool: `['cloth', 'robe', 'light', 'leather', 'medium']`
- Separation mandatory: `['stoffa', 'cuoio']`
- Slot types: `['armor', 'chest', 'helm']`

### §3.4 · Bucket · Accessory universal-neutral (expected=19)

- Slot types: `['accessory', 'amulet', 'ring']`
- Identity check manual: `True`
- Note: accessory with other-class identity (Mago/Paladino/Cacciatore di Mostri) is NOT auto-universal-neutral

### §3.5 · Derivation attestation

- `derivation_source`: PM dispatch R18.6.RV3-IS1-A verbatim criteria
- `derivation_rule`: `candidate_discovery_filters_NOT_auto_approval`
- `PM_approval`: `pending`
- `confidence`: `HIGH`

## §4 · Exclusion Ledger EV-F2 (28 tracked · 27 unique)

**Tracked count**: 28
**Unique slug count**: 27
**Overlap note**: voidpiercer-bow tracked twice (track_idx=5 identity_conflict, track_idx=28 weapon_family_excluded_bow) — same slug, dual-classification per PM instruction
**Excluded hits inside bucket queries**: 0 (zero — pre-filtered by common_filters)

| Track # | Slug | Reason | EV-F2 Verdict | Bucket Class |
|---:|---|---|---|---|
| 1 | `drake_slayer_helm` | identity_conflict | `NOT_COMPATIBLE_wrong_stat_hard_binding` | `lore_identity` |
| 2 | `drake_slayer_chest` | identity_conflict | `NOT_COMPATIBLE_wrong_stat_hard_binding` | `lore_identity` |
| 3 | `drake_slayer_blade` | identity_conflict + sword_proficiency | `NOT_COMPATIBLE_wrong_stat_hard_binding_sword` | `lore_identity` |
| 4 | `goblin_hunter_ring` | identity_conflict + cacciatore_di_mostri | `NOT_COMPATIBLE_wrong_stat_cross_class` | `lore_identity` |
| 5 | `voidpiercer-bow` | identity_conflict + retro_branding_forbidden + bow_family_excluded | `REJECTED_NOT_COMPATIBLE_FINAL` | `lore_identity_AND_weapon_family_excluded` |
| 6 | `arcane_adept_orb` | preserved_opzione_A + triggers_future_void_native_successor | `NOT_COMPATIBLE_preserved_Opzione_A` | `preserved_no_mutation` |
| 7 | `warlock_apprentice_tome` | famiglia_esclusa_da_G2 (tome) | `NOT_COMPATIBLE_post_strict_G2` | `weapon_family_excluded_tome` |
| 8 | `warlock_hex_grimoire` | famiglia_esclusa_da_G2 (tome) | `NOT_COMPATIBLE_post_strict_G2` | `weapon_family_excluded_tome` |
| 9 | `warlock_shadowbound_grimoire` | famiglia_esclusa_da_G2 (tome) | `NOT_COMPATIBLE_post_strict_G2` | `weapon_family_excluded_tome` |
| 10 | `warlock_witchking_codex` | famiglia_esclusa_da_G2 (tome) | `NOT_COMPATIBLE_post_strict_G2` | `weapon_family_excluded_tome` |
| 11 | `warlock_apprentice_grimoire` | famiglia_esclusa_da_G2 (tome) | `NOT_COMPATIBLE_post_strict_G2` | `weapon_family_excluded_tome` |
| 12 | `warlock_pact_binder` | famiglia_esclusa_da_G2 (tome) | `NOT_COMPATIBLE_post_strict_G2` | `weapon_family_excluded_tome` |
| 13 | `cracked-staff` | famiglia_esclusa_da_G2 (staff) | `NOT_COMPATIBLE_declassed` | `weapon_family_excluded_staff` |
| 14 | `spiritglass-staff` | famiglia_esclusa_da_G2 (staff) | `NOT_COMPATIBLE_declassed` | `weapon_family_excluded_staff` |
| 15 | `embermind-focus` | famiglia_esclusa_da_G2 (wand) | `NOT_COMPATIBLE_declassed` | `weapon_family_excluded_wand` |
| 16 | `apprentice-wand` | famiglia_esclusa_da_G2 (wand) | `NOT_COMPATIBLE_declassed` | `weapon_family_excluded_wand` |
| 17 | `hex-rod` | famiglia_esclusa_da_G2 (staff) | `NOT_COMPATIBLE_declassed` | `weapon_family_excluded_staff` |
| 18 | `moonsilver-bow` | famiglia_esclusa_da_G2 (bow) | `NOT_COMPATIBLE_declassed` | `weapon_family_excluded_bow` |
| 19 | `warlocks-grimoire` | famiglia_esclusa_da_G2 (grimoire) | `NOT_COMPATIBLE_declassed` | `weapon_family_excluded_grimoire` |
| 20 | `archmagi-staff` | famiglia_esclusa_da_G2 (staff) | `NOT_COMPATIBLE_declassed` | `weapon_family_excluded_staff` |
| 21 | `songsteel-flute` | famiglia_esclusa_da_G2 (instrument_sonic) | `NOT_COMPATIBLE_declassed` | `weapon_family_excluded_instrument` |
| 22 | `apprentice_staff` | famiglia_esclusa_da_G2 (staff) | `NOT_COMPATIBLE_declassed` | `weapon_family_excluded_staff` |
| 23 | `legendary_staff_efreto` | famiglia_esclusa_da_G2 (staff) | `NOT_COMPATIBLE_declassed` | `weapon_family_excluded_staff` |
| 24 | `alchemist_apprentice_flask` | famiglia_esclusa_da_G2 (alchemical_flask) | `NOT_COMPATIBLE_declassed` | `weapon_family_excluded_flask` |
| 25 | `alchemist_elemental_flask` | famiglia_esclusa_da_G2 (alchemical_flask) | `NOT_COMPATIBLE_declassed` | `weapon_family_excluded_flask` |
| 26 | `alchemist_transmuters_tome` | famiglia_esclusa_da_G2 (tome) | `NOT_COMPATIBLE_declassed` | `weapon_family_excluded_tome` |
| 27 | `alchemist_philosophers_flask` | famiglia_esclusa_da_G2 (alchemical_flask) | `NOT_COMPATIBLE_declassed` | `weapon_family_excluded_flask` |
| 28 | `voidpiercer-bow` | SECONDARY_TRACKING · weapon_family_bow_excluded (semantic overlap with identity_conflict at track_idx=5) | `REJECTED_NOT_COMPATIBLE_FINAL (dual-classified)` | `weapon_family_excluded_bow` |

## §5 · Discovery Counts Summary

| Bucket | Raw Count | Expected (PM) | Match |
|---|---:|---:|:---:|
| weapon_literal_G2 | 2 | 2 | ✅ |
| armor_stoffa_cuoio | 11 | 11 | ✅ |
| accessory_universal | 19 | 19 | ✅ |
| **TOTAL** | **32** | **32** | **✅** |

### §5.1 · Armor Breakdown (stoffa vs cuoio)

- **stoffa** = 10: `apprentice-robe, initiate_robe, aether-weave-robe, alchemist_apron, alchemist_brewers_apron, alchemist_quicksilver_vest, alchemist_ember_lined_vest, druid_grovewarden_mantle, alchemist_quintessence_robe, druid_elder_vestments`
- **cuoio** = 1: `alchemist_philosophers_plate`

### §5.2 · Accessory Slot Breakdown

| slot_type raw | count | canonical alias |
|---|---:|---|
| `accessory` | 16 | `accessory` |
| `amulet` | 3 | `neck` (PM alias EV-F2 §slot_taxonomy) |
| `ring` | 0 | `ring` |

### §5.3 · Weapon Family Breakdown

- **focus** = 2
- **pugnale/dagger** = 0

## §6 · Structural Gaps Detected (CRITICAL)


### GAP-1 · pugnale_family_absent_from_intellect_eligible_pool

- **Evidence**: 3 items with weapon_tags=dagger exist in DB (goblin-dagger, hunting-knife, balanced_dagger) but all have stat_tags=[agility|strength] — zero dagger with stat_tags=intellect
- **Impact on binding**: `cond_reuse_pugnale_mechanism_compat_01`
- **Severity**: `HIGH_structural`
- **PM mitigation options** (PM decides):
  - A: Drop pugnale binding from IC1 §14 (roster becomes 5 conditional binds)
  - B: Rebind cond_reuse_pugnale_mechanism_compat_01 to focus family (with explicit family_mismatch note) — VIOLATES PM validation family_mismatch=0
  - C: Escalate to FUTURE_ITEM_NEW pugnale-intellect creation in Registry v3 (post AFX1) — cond_reuse_pugnale becomes REQUIRES_NEW_ITEM_FUTURE, removed from IS1 conditional pool
  - D: Rethink IC1 §14 mapping — PM proposes alternative slot/family target

### GAP-2 · ring_slot_absent_from_intellect_eligible_neutral_pool

- **Evidence**: Only 1 slot_type=ring exists in DB (goblin_hunter_ring) — excluded by EV-F2 identity_conflict (lore=oblio+vuoto, stat=agility, cacciatore_di_mostri rec_classes)
- **Impact on binding**: `cond_reuse_caster_stat_neutral_04`
- **Severity**: `HIGH_structural`
- **PM mitigation options** (PM decides):
  - A: Drop ring binding from IC1 §14 (roster becomes 5 conditional binds if GAP-1 too)
  - B: Rebind cond_reuse_caster_stat_neutral_04 to accessory slot generic (with explicit slot_mismatch note) — VIOLATES PM validation slot_mismatch=0
  - C: Escalate to FUTURE_ITEM_NEW ring-intellect-neutral creation in Registry v3 — cond_reuse_caster_stat_neutral_04 becomes REQUIRES_NEW_ITEM_FUTURE, removed from IS1 conditional pool
  - D: Rethink IC1 §14 mapping — PM proposes alternative slot (e.g. remap to amulet/neck given amulet pool has 3 candidates)

## §7 · Allowlist Candidates 32/32 (canonical order)

| # | source_item_id | slug | bucket | slot_type | norm_slot | wpn_family | armor_type | id_class | risk | rarity | L | cond_code |
|---:|---|---|---|---|---|---|---|---|:---:|---|---:|---|
| 1 | `72c4f06f-55c0-4d44-a6c2-b40ad1443196` | `alchemist_glass_wand` | `weapon_literal_G2` | `weapon` | `main_hand` | `focus` | `None` | `class_specific_non_caster` | `MEDIUM` | `Uncommon` | `3` | `COND_FOCUS_MECHANISM_OK` |
| 2 | `164d4575-5188-4615-9b01-79d84815c161` | `alchemist_catalyst_flask` | `weapon_literal_G2` | `weapon` | `main_hand` | `focus` | `None` | `class_specific_non_caster` | `MEDIUM` | `Rare` | `5` | `COND_FOCUS_MECHANISM_OK` |
| 3 | `8efacc3f-3afc-490d-b5e2-c140f8cf5b3d` | `apprentice-robe` | `armor_stoffa_cuoio` | `armor` | `chest` | `None` | `stoffa` | `shared_family_multi_caster` | `LOW` | `Common` | `1` | `COND_STAT_NEUTRAL_INT` |
| 4 | `c6c89f1e-437e-4044-92b7-b4e6b9b7793d` | `aether-weave-robe` | `armor_stoffa_cuoio` | `armor` | `chest` | `None` | `stoffa` | `multi_role_wide` | `LOW` | `Epic` | `8` | `COND_STAT_NEUTRAL_INT` |
| 5 | `794e89a3-59c0-4ea3-9eef-0e0e31fe7761` | `initiate_robe` | `armor_stoffa_cuoio` | `armor` | `chest` | `None` | `stoffa` | `multi_role_wide` | `LOW` | `Common` | `1` | `COND_STAT_NEUTRAL_INT` |
| 6 | `a86520a8-5bc2-41eb-a89d-8ef769e05846` | `alchemist_apron` | `armor_stoffa_cuoio` | `armor` | `chest` | `None` | `stoffa` | `class_specific_non_caster` | `MEDIUM` | `Common` | `1` | `COND_STAT_NEUTRAL_INT` |
| 7 | `2a163db4-753d-471b-9881-d53cffa5f56c` | `alchemist_ember_lined_vest` | `armor_stoffa_cuoio` | `armor` | `chest` | `None` | `stoffa` | `class_specific_non_caster` | `MEDIUM` | `Rare` | `5` | `COND_STAT_NEUTRAL_INT` |
| 8 | `f87b2ddd-7353-4221-a14b-809427e1a60d` | `alchemist_quintessence_robe` | `armor_stoffa_cuoio` | `armor` | `chest` | `None` | `stoffa` | `class_specific_non_caster` | `MEDIUM` | `Epic` | `8` | `COND_STAT_NEUTRAL_INT` |
| 9 | `60d202f4-c324-4132-80b6-c336b5e23897` | `druid_grovewarden_mantle` | `armor_stoffa_cuoio` | `armor` | `chest` | `None` | `stoffa` | `class_specific_non_caster` | `MEDIUM` | `Rare` | `5` | `COND_STAT_NEUTRAL_INT` |
| 10 | `2931f2b3-0630-4c9c-a7f5-0b44c69c9f8b` | `druid_elder_vestments` | `armor_stoffa_cuoio` | `armor` | `chest` | `None` | `stoffa` | `class_specific_non_caster` | `MEDIUM` | `Epic` | `8` | `COND_STAT_NEUTRAL_INT` |
| 11 | `e8a57ea9-8209-4d46-8dc1-d5738108662e` | `alchemist_brewers_apron` | `armor_stoffa_cuoio` | `armor` | `chest` | `None` | `stoffa` | `class_specific_non_caster` | `MEDIUM` | `Common` | `1` | `COND_STAT_NEUTRAL_INT` |
| 12 | `7ad70e1d-bd5e-421f-ada2-c8868e43f4d6` | `alchemist_quicksilver_vest` | `armor_stoffa_cuoio` | `armor` | `chest` | `None` | `stoffa` | `class_specific_non_caster` | `MEDIUM` | `Uncommon` | `3` | `COND_STAT_NEUTRAL_INT` |
| 13 | `67a6f0e5-570e-4dc4-9ad3-a6751d09727c` | `alchemist_philosophers_plate` | `armor_stoffa_cuoio` | `armor` | `chest` | `None` | `cuoio` | `class_specific_non_caster` | `MEDIUM` | `Rare` | `5` | `COND_STAT_NEUTRAL_INT` |
| 14 | `265db775-259b-488f-b15a-30f69ea823fe` | `relic-signet` | `accessory_universal` | `accessory` | `accessory` | `None` | `None` | `multi_role_wide` | `LOW` | `Rare` | `5` | `COND_ACCESSORY_NEUTRAL` |
| 15 | `36add57c-6f53-46d6-9003-7adaba7ac701` | `hoardlords-seal` | `accessory_universal` | `accessory` | `accessory` | `None` | `None` | `multi_role_wide` | `LOW` | `Epic` | `8` | `COND_ACCESSORY_NEUTRAL` |
| 16 | `0bc1d330-8b05-4fc0-946f-e994f33539b7` | `herbalist-pouch` | `accessory_universal` | `accessory` | `accessory` | `None` | `None` | `shared_family_multi_caster` | `LOW` | `Common` | `1` | `COND_ACCESSORY_NEUTRAL` |
| 17 | `89309769-fb51-4f95-94b4-f4c61972c8bc` | `scholars-spectacles` | `accessory_universal` | `accessory` | `accessory` | `None` | `None` | `shared_family_multi_caster` | `LOW` | `Uncommon` | `3` | `COND_ACCESSORY_NEUTRAL` |
| 18 | `770e6f4f-af58-4e29-a585-6ffa6bfe2db6` | `seers-monocle` | `accessory_universal` | `accessory` | `accessory` | `None` | `None` | `multi_role_wide` | `LOW` | `Rare` | `5` | `COND_ACCESSORY_NEUTRAL` |
| 19 | `57906a5e-6644-4edd-8ad1-ddd7168ae4fe` | `oracle-pendant` | `accessory_universal` | `accessory` | `accessory` | `None` | `None` | `multi_role_wide` | `LOW` | `Rare` | `5` | `COND_ACCESSORY_NEUTRAL` |
| 20 | `f93ad143-df97-492e-910f-305c8c683361` | `crown-of-stillness` | `accessory_universal` | `accessory` | `accessory` | `None` | `None` | `multi_role_wide` | `LOW` | `Epic` | `8` | `COND_ACCESSORY_NEUTRAL` |
| 21 | `77147f82-6b36-4bb2-85a7-7ec817ee43f3` | `apprentice-handbook` | `accessory_universal` | `accessory` | `accessory` | `None` | `None` | `shared_family_multi_caster` | `LOW` | `Common` | `1` | `COND_ACCESSORY_NEUTRAL` |
| 22 | `a8d89758-c34f-46e5-a58c-8594ea919505` | `wanderer_amulet` | `accessory_universal` | `accessory` | `accessory` | `None` | `None` | `multi_role_wide` | `LOW` | `Uncommon` | `3` | `COND_ACCESSORY_NEUTRAL` |
| 23 | `e260b599-ca87-4a38-b099-1842cc48d241` | `minor_sigil` | `accessory_universal` | `accessory` | `accessory` | `None` | `None` | `multi_role_wide` | `LOW` | `Rare` | `5` | `COND_ACCESSORY_NEUTRAL` |
| 24 | `spec_signature_sacred_chalice` | `spec_signature_sacred_chalice` | `accessory_universal` | `amulet` | `neck` | `None` | `None` | `multi_role_wide` | `LOW` | `Rare` | `5` | `COND_ACCESSORY_NEUTRAL` |
| 25 | `spec_signature_battle_standard` | `spec_signature_battle_standard` | `accessory_universal` | `amulet` | `neck` | `None` | `None` | `multi_role_wide` | `LOW` | `Rare` | `5` | `COND_ACCESSORY_NEUTRAL` |
| 26 | `spec_signature_runed_focus` | `spec_signature_runed_focus` | `accessory_universal` | `amulet` | `neck` | `None` | `None` | `multi_role_wide` | `LOW` | `Epic` | `8` | `COND_ACCESSORY_NEUTRAL` |
| 27 | `bb23ee48-5959-4d28-b0bc-30327b5f33c6` | `legendary_amulet_nathos` | `accessory_universal` | `accessory` | `accessory` | `None` | `None` | `multi_role_wide` | `LOW` | `Legendary` | `8` | `COND_ACCESSORY_NEUTRAL` |
| 28 | `9684d81a-238f-4f90-8e42-9804f4897881` | `alchemist_reagent_pouch` | `accessory_universal` | `accessory` | `accessory` | `None` | `None` | `class_specific_non_caster` | `MEDIUM` | `Common` | `1` | `COND_ACCESSORY_NEUTRAL` |
| 29 | `93b8fc54-411d-45b1-8347-b4fddf7b50f5` | `alchemist_alembic_pendant` | `accessory_universal` | `accessory` | `accessory` | `None` | `None` | `class_specific_non_caster` | `MEDIUM` | `Rare` | `5` | `COND_ACCESSORY_NEUTRAL` |
| 30 | `1aad80f8-fe95-4809-90af-3763bc7326f4` | `alchemist_transmutation_medallion` | `accessory_universal` | `accessory` | `accessory` | `None` | `None` | `class_specific_non_caster` | `MEDIUM` | `Epic` | `8` | `COND_ACCESSORY_NEUTRAL` |
| 31 | `e1ac0940-a7bb-4d2e-a023-9cbbe9210aed` | `alchemist_catalyst_ring` | `accessory_universal` | `accessory` | `accessory` | `None` | `None` | `class_specific_non_caster` | `MEDIUM` | `Uncommon` | `3` | `COND_ACCESSORY_NEUTRAL` |
| 32 | `c089bf70-08c7-485e-a78c-c873002c1877` | `alchemist_golden_vial` | `accessory_universal` | `accessory` | `accessory` | `None` | `None` | `class_specific_non_caster` | `MEDIUM` | `Rare` | `5` | `COND_ACCESSORY_NEUTRAL` |

## §8 · Ranking Preferences (recorded, non-authoritative)

Ordine di preferenza applicato per raccomandazione (dal PM dispatch):
1. slot esatto
2. famiglia esatta
3. identità neutra
4. Intelligenza compatibile
5. binding soft
6. nessuna mutation
7. rischio identitario più basso (LOW → MEDIUM → HIGH)
8. metadata più completi
9. tie-break stabile per slug (asc)

_NB · Il tie-break NON trasforma la proposta in approvazione (`PM_authoritative=false` per tutti i 6 bindings)._

## §9 · 6 Proposed Bindings (PROPOSED_PENDING_PM)


### §9.1 · `cond_reuse_caster_stat_neutral_01`

- **Slot target** (IC1): `chest`
- **Family target** (IC1): `armor_stoffa`
- **Condition code**: `COND_STAT_NEUTRAL_INT`
- **Pool source**: `armor_stoffa`
- **Pool size disponibile**: `11`
- **Binding status**: `PROPOSED_PENDING_PM`
- **PM_authoritative**: `False` · **apply_authorized**: `False` · **registry_authorized**: `False`
- **Recommended binding**: `8efacc3f-3afc-490d-b5e2-c140f8cf5b3d` (`apprentice-robe`)
- **Recommended reason**: ranking: risk=LOW · id_class=shared_family_multi_caster · rarity=Common L1 · slug tie-break asc
- **slot_mismatch**: `true` · recommended live slot_type='armor' (generic) · sub-slot chest/legs derivation deferred to future taxonomy gate (EV-F2 §slot_type_distinct.canonical_remapping_deferred_to_future_gate=true). Systemic, not a candidate defect.
- **family_mismatch**: `False`
- **Alternatives** (9):
  - `794e89a3-59c0-4ea3-9eef-0e0e31fe7761` `initiate_robe` · id_class=`multi_role_wide` · risk=`LOW` · `Common L1`
  - `c6c89f1e-437e-4044-92b7-b4e6b9b7793d` `aether-weave-robe` · id_class=`multi_role_wide` · risk=`LOW` · `Epic L8`
  - `a86520a8-5bc2-41eb-a89d-8ef769e05846` `alchemist_apron` · id_class=`class_specific_non_caster` · risk=`MEDIUM` · `Common L1`
  - `e8a57ea9-8209-4d46-8dc1-d5738108662e` `alchemist_brewers_apron` · id_class=`class_specific_non_caster` · risk=`MEDIUM` · `Common L1`
  - `7ad70e1d-bd5e-421f-ada2-c8868e43f4d6` `alchemist_quicksilver_vest` · id_class=`class_specific_non_caster` · risk=`MEDIUM` · `Uncommon L3`
  - `2a163db4-753d-471b-9881-d53cffa5f56c` `alchemist_ember_lined_vest` · id_class=`class_specific_non_caster` · risk=`MEDIUM` · `Rare L5`
  - `60d202f4-c324-4132-80b6-c336b5e23897` `druid_grovewarden_mantle` · id_class=`class_specific_non_caster` · risk=`MEDIUM` · `Rare L5`
  - `f87b2ddd-7353-4221-a14b-809427e1a60d` `alchemist_quintessence_robe` · id_class=`class_specific_non_caster` · risk=`MEDIUM` · `Epic L8`
  - `2931f2b3-0630-4c9c-a7f5-0b44c69c9f8b` `druid_elder_vestments` · id_class=`class_specific_non_caster` · risk=`MEDIUM` · `Epic L8`

### §9.2 · `cond_reuse_caster_stat_neutral_02`

- **Slot target** (IC1): `legs`
- **Family target** (IC1): `armor_stoffa`
- **Condition code**: `COND_STAT_NEUTRAL_INT`
- **Pool source**: `armor_stoffa`
- **Pool size disponibile**: `10`
- **Binding status**: `PROPOSED_PENDING_PM`
- **PM_authoritative**: `False` · **apply_authorized**: `False` · **registry_authorized**: `False`
- **Recommended binding**: `794e89a3-59c0-4ea3-9eef-0e0e31fe7761` (`initiate_robe`)
- **Recommended reason**: ranking: risk=LOW · id_class=multi_role_wide · rarity=Common L1 · slug tie-break asc
- **slot_mismatch**: `true` · recommended live slot_type='armor' (generic) · sub-slot chest/legs derivation deferred to future taxonomy gate (EV-F2 §slot_type_distinct.canonical_remapping_deferred_to_future_gate=true). Systemic, not a candidate defect.
- **family_mismatch**: `False`
- **Alternatives** (8):
  - `c6c89f1e-437e-4044-92b7-b4e6b9b7793d` `aether-weave-robe` · id_class=`multi_role_wide` · risk=`LOW` · `Epic L8`
  - `a86520a8-5bc2-41eb-a89d-8ef769e05846` `alchemist_apron` · id_class=`class_specific_non_caster` · risk=`MEDIUM` · `Common L1`
  - `e8a57ea9-8209-4d46-8dc1-d5738108662e` `alchemist_brewers_apron` · id_class=`class_specific_non_caster` · risk=`MEDIUM` · `Common L1`
  - `7ad70e1d-bd5e-421f-ada2-c8868e43f4d6` `alchemist_quicksilver_vest` · id_class=`class_specific_non_caster` · risk=`MEDIUM` · `Uncommon L3`
  - `2a163db4-753d-471b-9881-d53cffa5f56c` `alchemist_ember_lined_vest` · id_class=`class_specific_non_caster` · risk=`MEDIUM` · `Rare L5`
  - `60d202f4-c324-4132-80b6-c336b5e23897` `druid_grovewarden_mantle` · id_class=`class_specific_non_caster` · risk=`MEDIUM` · `Rare L5`
  - `f87b2ddd-7353-4221-a14b-809427e1a60d` `alchemist_quintessence_robe` · id_class=`class_specific_non_caster` · risk=`MEDIUM` · `Epic L8`
  - `2931f2b3-0630-4c9c-a7f5-0b44c69c9f8b` `druid_elder_vestments` · id_class=`class_specific_non_caster` · risk=`MEDIUM` · `Epic L8`

### §9.3 · `cond_reuse_caster_stat_neutral_03`

- **Slot target** (IC1): `accessory`
- **Family target** (IC1): `universal_neutral`
- **Condition code**: `COND_ACCESSORY_NEUTRAL`
- **Pool source**: `accessory_slot_accessory`
- **Pool size disponibile**: `17`
- **Binding status**: `PROPOSED_PENDING_PM`
- **PM_authoritative**: `False` · **apply_authorized**: `False` · **registry_authorized**: `False`
- **Recommended binding**: `77147f82-6b36-4bb2-85a7-7ec817ee43f3` (`apprentice-handbook`)
- **Recommended reason**: ranking: risk=LOW · id_class=shared_family_multi_caster · rarity=Common L1 · slug tie-break asc
- **slot_mismatch**: `false`
- **family_mismatch**: `False`
- **Alternatives** (15):
  - `0bc1d330-8b05-4fc0-946f-e994f33539b7` `herbalist-pouch` · id_class=`shared_family_multi_caster` · risk=`LOW` · `Common L1`
  - `89309769-fb51-4f95-94b4-f4c61972c8bc` `scholars-spectacles` · id_class=`shared_family_multi_caster` · risk=`LOW` · `Uncommon L3`
  - `a8d89758-c34f-46e5-a58c-8594ea919505` `wanderer_amulet` · id_class=`multi_role_wide` · risk=`LOW` · `Uncommon L3`
  - `e260b599-ca87-4a38-b099-1842cc48d241` `minor_sigil` · id_class=`multi_role_wide` · risk=`LOW` · `Rare L5`
  - `57906a5e-6644-4edd-8ad1-ddd7168ae4fe` `oracle-pendant` · id_class=`multi_role_wide` · risk=`LOW` · `Rare L5`
  - `265db775-259b-488f-b15a-30f69ea823fe` `relic-signet` · id_class=`multi_role_wide` · risk=`LOW` · `Rare L5`
  - `770e6f4f-af58-4e29-a585-6ffa6bfe2db6` `seers-monocle` · id_class=`multi_role_wide` · risk=`LOW` · `Rare L5`
  - `f93ad143-df97-492e-910f-305c8c683361` `crown-of-stillness` · id_class=`multi_role_wide` · risk=`LOW` · `Epic L8`
  - `36add57c-6f53-46d6-9003-7adaba7ac701` `hoardlords-seal` · id_class=`multi_role_wide` · risk=`LOW` · `Epic L8`
  - `bb23ee48-5959-4d28-b0bc-30327b5f33c6` `legendary_amulet_nathos` · id_class=`multi_role_wide` · risk=`LOW` · `Legendary L8`
  - `9684d81a-238f-4f90-8e42-9804f4897881` `alchemist_reagent_pouch` · id_class=`class_specific_non_caster` · risk=`MEDIUM` · `Common L1`
  - `e1ac0940-a7bb-4d2e-a023-9cbbe9210aed` `alchemist_catalyst_ring` · id_class=`class_specific_non_caster` · risk=`MEDIUM` · `Uncommon L3`
  - `93b8fc54-411d-45b1-8347-b4fddf7b50f5` `alchemist_alembic_pendant` · id_class=`class_specific_non_caster` · risk=`MEDIUM` · `Rare L5`
  - `c089bf70-08c7-485e-a78c-c873002c1877` `alchemist_golden_vial` · id_class=`class_specific_non_caster` · risk=`MEDIUM` · `Rare L5`
  - `1aad80f8-fe95-4809-90af-3763bc7326f4` `alchemist_transmutation_medallion` · id_class=`class_specific_non_caster` · risk=`MEDIUM` · `Epic L8`

### §9.4 · `cond_reuse_caster_stat_neutral_04`

- **Slot target** (IC1): `ring`
- **Family target** (IC1): `universal_neutral`
- **Condition code**: `COND_ACCESSORY_NEUTRAL`
- **Pool source**: `accessory_slot_ring`
- **Pool size disponibile**: `0`
- **Binding status**: `PROPOSED_PENDING_PM_UNBINDABLE_STRUCTURAL_GAP`
- **PM_authoritative**: `False` · **apply_authorized**: `False` · **registry_authorized**: `False`
- **Recommended binding**: `null` · **UNBINDABLE**
- **slot_mismatch**: `false`
- **family_mismatch**: `False`
- ⚠️ **Unbindable reason**: Zero candidates in pool `accessory_slot_ring` — structural gap in DB (see structural_gaps_detected)

### §9.5 · `cond_reuse_focus_mechanism_compat_01`

- **Slot target** (IC1): `main_hand`
- **Family target** (IC1): `focus`
- **Condition code**: `COND_FOCUS_MECHANISM_OK`
- **Pool source**: `weapon_focus`
- **Pool size disponibile**: `3`
- **Binding status**: `PROPOSED_PENDING_PM`
- **PM_authoritative**: `False` · **apply_authorized**: `False` · **registry_authorized**: `False`
- **Recommended binding**: `72c4f06f-55c0-4d44-a6c2-b40ad1443196` (`alchemist_glass_wand`)
- **Recommended reason**: ranking: risk=MEDIUM · id_class=class_specific_non_caster · rarity=Uncommon L3 · slug tie-break asc
- **slot_mismatch**: `false`
- **family_mismatch**: `False`
- **Alternatives** (1):
  - `164d4575-5188-4615-9b01-79d84815c161` `alchemist_catalyst_flask` · id_class=`class_specific_non_caster` · risk=`MEDIUM` · `Rare L5`

### §9.6 · `cond_reuse_pugnale_mechanism_compat_01`

- **Slot target** (IC1): `main_hand`
- **Family target** (IC1): `pugnale`
- **Condition code**: `COND_PUGNALE_MECHANISM_OK`
- **Pool source**: `weapon_pugnale`
- **Pool size disponibile**: `0`
- **Binding status**: `PROPOSED_PENDING_PM_UNBINDABLE_STRUCTURAL_GAP`
- **PM_authoritative**: `False` · **apply_authorized**: `False` · **registry_authorized**: `False`
- **Recommended binding**: `null` · **UNBINDABLE**
- **slot_mismatch**: `false`
- **family_mismatch**: `False`
- ⚠️ **Unbindable reason**: Zero candidates in pool `weapon_pugnale` — structural gap in DB (see structural_gaps_detected)

## §10 · Ambiguity Report

| Binding | Provisional | Ambiguity Type | Alt Count | Note |
|---:|---|---|---:|---|
| 1 | `cond_reuse_caster_stat_neutral_01` | `multiple_valid_candidates` | 9 | recommended live slot_type='armor' (generic) · sub-slot chest/legs derivation deferred to future taxonomy gate (EV-F2 §slot_type_distinct.canonical_remapping_deferred_to_future_gate=true). Systemic, not a candidate defect. |
| 2 | `cond_reuse_caster_stat_neutral_02` | `multiple_valid_candidates` | 8 | recommended live slot_type='armor' (generic) · sub-slot chest/legs derivation deferred to future taxonomy gate (EV-F2 §slot_type_distinct.canonical_remapping_deferred_to_future_gate=true). Systemic, not a candidate defect. |
| 3 | `cond_reuse_caster_stat_neutral_03` | `multiple_valid_candidates` | 15 | recommended_selected_via_deterministic_ranking |
| 4 | `cond_reuse_caster_stat_neutral_04` | `structural_gap_unbindable` | 0 | Zero candidates in pool `accessory_slot_ring` — structural gap in DB (see structural_gaps_detected) |
| 5 | `cond_reuse_focus_mechanism_compat_01` | `multiple_valid_candidates` | 1 | recommended_selected_via_deterministic_ranking |
| 6 | `cond_reuse_pugnale_mechanism_compat_01` | `structural_gap_unbindable` | 0 | Zero candidates in pool `weapon_pugnale` — structural gap in DB (see structural_gaps_detected) |

## §11 · Duplicate Checks

- Duplicate `source_item_id` nell'allowlist: `0` (attesa: 0)
- Duplicate slug nell'allowlist: `0`
- Duplicate `recommended_source_item_id` tra bindings: `0`
- Recommended UUIDs set size: `4`

## §12 · Condition Code Validation

- Approved codes: `['COND_STAT_NEUTRAL_INT', 'COND_ACCESSORY_NEUTRAL', 'COND_FOCUS_MECHANISM_OK', 'COND_PUGNALE_MECHANISM_OK']`
- Used codes distinct: `['COND_ACCESSORY_NEUTRAL', 'COND_FOCUS_MECHANISM_OK', 'COND_STAT_NEUTRAL_INT']`
- Unauthorized codes detected: `[]`
- Pass: `True`

## §13 · Governance Validations

| Check | Result |
|---|:---:|
| `candidate_universe_eq_32` | ✅ |
| `unique_candidate_uuid_eq_32` | ✅ |
| `weapon_candidates_eq_2` | ✅ |
| `armor_candidates_eq_11` | ✅ |
| `accessory_candidates_eq_19` | ✅ |
| `duplicate_uuid_eq_0` | ✅ |
| `excluded_item_included_eq_0` | ✅ |
| `mutation_required_true_eq_0` | ✅ |
| `unknown_source_id_eq_0` | ✅ |
| `proposed_bindings_eq_6` | ✅ |
| `duplicate_source_binding_eq_0` | ✅ |
| `slot_mismatch_eq_0_strict` | ❌ |
| `family_mismatch_eq_0` | ✅ |

**Slot mismatch systemic note**: chest/legs bindings live slot_type=armor generic — sub-slot canonical remapping deferred (EV-F2 §slot_type_distinct.canonical_remapping_deferred_to_future_gate=true). Not a candidate defect.

## §14 · Explicit STOP · PM Directive Required

- `is1_roster_generation`: `PAUSED_by_pm_dispatch_R18_6_RV3_IS1_A_directive`
- `is1_source_artifacts_absent`: `True`
- `is1_a_status_final`: `PROPOSED_PENDING_PM`
- `structural_gaps_blocking_full_binding`: `['GAP-1', 'GAP-2']`
- **PM directive required on**:
  - GAP-1_pugnale_family_absent_mitigation_ABCD
  - GAP-2_ring_slot_absent_mitigation_ABCD
  - ratification_of_4_bindable_recommended_bindings
  - authorization_or_denial_to_proceed_with_is1_roster_after_gaps_resolved
- `next_action`: `await_pm_verdict_on_IS1_A_including_gap_mitigation`

### Roadmap Status (record)

- AFX1 = `CLOSED_LOCKED`
- IC1 = `CLOSED_LOCKED`
- IS1 = `IN_PROGRESS_BLOCKED_ON_IS1_A`
- IS1-A = `PROPOSED_PENDING_PM`
- NC1 = `HOLD`
- Gate 11 = `HOLD`
- Wave 1 = `HOLD`
- Registry v3 apply = `NOT_AUTHORIZED`

---

_Fine documento R18.6.RV3-IS1-A · DOCUMENTAL ONLY · READ-ONLY DISCOVERY · Italiano_
