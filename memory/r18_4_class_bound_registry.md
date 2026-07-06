<!-- 🔒 R18.4 — Item Class-Bound Player-Facing — CLOSED & SEALED -->
<!-- R18.4 CLOSED & SEALED -->
<!-- SHA256 registered in /app/memory/r18_4_phase_b4_contract_lock_and_seal_report.md -->
# R18.4 Class Bound Registry — Bucket Assignment + Policy Target

- **Round**: R18.4 — Item Class-Bound Player-Facing
- **Purpose**: registry documental-only con bucket assignment (7 buckets A/B/C/D/E/F/G) + target `item_binding_policy` per ognuno dei 178 items del catalog.
- **Generated at UTC**: `2026-07-06T05:05:00Z`
- **Governance**: documental only. NO runtime enforcement. NO DB write. Sibling scripts B3 = dry-run only. Sigilli byte-identical.
- **Fonte primaria**: query read-only su `items` collection (live) + PM decision lock B2 (SQ1-SQ7).

---

## 1. Totals

| Metric | Count |
|---|---|
| Total items | 178 |
| Hard policy target | 11 |
| Universal policy target | 21 |
| Soft policy target | 146 |
| Overlap hard∩universal | 0 |
| Backfill slot_type target | 140 |
| Already-populated slot_type | 17 |

---

## 2. Policy Derivation Algorithm (SQ6 locked)

```python
def derive_item_binding_policy(item):
    # Step 1: hard (highest priority)
    if item.get("required_class_optional"):  # non-null, non-empty
        return "hard"
    # Step 2: universal (materials + consumables)
    if item.get("item_type") in {"material", "material_continental",
                                  "material_event", "consumable"}:
        return "universal"
    # Step 3: soft (default residual)
    return "soft"
```

---

## 3. Slot Type Backfill Target (140 items)

Filter: `slot_type IN (null, missing) AND item_type IN (weapon, armor, accessory, shield)`.

Mapping (SQ1 locked):
```
weapon    → slot_type = "weapon"      (54 items)
armor     → slot_type = "armor"       (42 items)
accessory → slot_type = "accessory"   (42 items)
shield    → slot_type = "armor"        (2 items, SQ1 opzione a)
TOTAL: 140 items
```

**Shield items mappati in armor**:
- `spec_signature_aegis_of_the_defender` (Egida del Difensore)
- `spec_signature_thornwood_shield` (Scudo di Spinalegno)

**Items già con slot_type populated (17, SKIP)** — non toccati dal backfill (mantengono i valori granulari già in DB):
- 3 drake_slayer_* → slot_type={helm, chest, weapon_main}
- 14 spec_signature_* → slot_type={weapon_main, chest, amulet}

---

## 4. Hard Bucket (11 items → policy=hard)

Derivati da `required_class_optional` populated. Include 3 legacy pre-signature + 8 E1 signature.

| # | Slug | required_class | item_type | slot_type | dormant |
|---|---|---|---|---|---|
| 1 | drake_slayer_helm | warrior | armor | helm | no |
| 2 | drake_slayer_chest | warrior | armor | chest | no |
| 3 | drake_slayer_blade | warrior | weapon | weapon_main | no |
| 4 | spec_signature_truestrike_bow | ranger | weapon | weapon_main | no |
| 5 | spec_signature_bloodied_greataxe | berserker | weapon | weapon_main | **YES (SQ4 dormant)** |
| 6 | spec_signature_breakers_gauntlets | warrior | armor | chest | no |
| 7 | spec_signature_silent_kris | assassin | weapon | weapon_main | **YES (SQ4 dormant)** |
| 8 | spec_signature_storm_rod | mage | weapon | weapon_main | no |
| 9 | spec_signature_corrupted_blade | necromancer | weapon | weapon_main | no |
| 10 | spec_signature_twin_blades | rogue | weapon | weapon_main | no |
| 11 | spec_signature_runic_aegis | paladin | armor | chest | no |

---

## 5. Universal Bucket (21 items → policy=universal)

Derivati da `item_type ∈ {material, material_continental, material_event, consumable}`.

### material (8)
- arcane_dust
- dragon_essence
- dull_gem
- greater_arcane_dust
- healing_herb
- iron_shard
- lesser_arcane_dust
- raw_leather

### material_continental (8)
- cenere_di_velur
- cristallo_di_ambash
- frammento_di_ergolat
- linfa_di_soe
- nucleo_di_efreto
- osso_di_irthe
- seme_di_nathos
- sigillo_di_aveol

### material_event (3)
- eco_della_luna_morta
- filo_lunare_spezzato
- frammento_obelisco_vuoto

### consumable (2)
- minor_healing_potion
- travel_ration

---

## 6. Soft Bucket (146 items → policy=soft)

Residuo: `not hard AND not universal`. Include buckets A (legacy_only), C (mixed), E2 (soft signature), G1 (equippable generic no slot_type).

Breakdown per item_type:
| item_type | count |
|---|---|
| weapon | 53 |
| armor | 43 |
| accessory | 48 |
| shield | 2 |
| **TOTAL soft** | **146** |

Note: 6 signature E2 (`aegis_of_the_defender`, `battle_standard`, `runed_focus`, `sacred_chalice`, `thornwood_shield`, `warhorn`) ricadono in soft (nessun `required_class_optional`).

---

## 7. Manual Overrides

**Nessuna manual override registrata in R18.4 B2.**

Tutti gli 11 hard e i 21 universal derivano deterministicamente dal PM default rule (SQ6). Se in un round futuro emergono item che richiedono policy diversa dal default derivation, saranno documentati come manual override esplicito con PM gate.

---

## 8. Cross-reference con backlog P3

| Backlog entry | Related SQ | Related items |
|---|---|---|
| R18.4.followup — Shield slot mapping decision | SQ1 | spec_signature_aegis_of_the_defender, spec_signature_thornwood_shield |
| R18.4.backlog — specialization_unlocks dead branch cleanup | SQ2 | 0 items runtime (branch dormant) |
| R18.4.backlog — berserker/assassin dormant signature items | SQ4 | spec_signature_bloodied_greataxe, spec_signature_silent_kris |

---

## 9. Self-check Registry

- ✅ Totals 178 = 11 hard + 21 universal + 146 soft
- ✅ Overlap hard ∩ universal = 0
- ✅ Hard exhaustive list (11 items) verified via DB read-only query
- ✅ Universal exhaustive list (21 items) verified via DB read-only query
- ✅ Backfill target (140 items) verified via DB read-only query
- ✅ Shield → armor mapping documented (SQ1 opzione a)
- ✅ Cross-reference with 3 backlog P3 entries
- ✅ Zero DB write. Zero runtime wire. Zero touch to sealed files.
