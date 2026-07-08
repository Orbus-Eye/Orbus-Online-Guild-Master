# R18.5 · Item Registry v2 · Dry-Run Documental Layer

**Round**: R18.5 (Itemization, ILVL & Gear Progression Rework)
**Phase**: **Registry v2 Dry-Run** (Q7=B in C6 Final Closure)
**Locked at (UTC)**: 2026-07-08T14:30:00Z
**Authority**: PM Orchestrator — Registry v2 dry-run in C6
**Regime**: **DOCUMENTAL ONLY** — 23 fields × 1500 rows · **NO apply · NO DB write · NO migration · NO registry live**.

---

## 0 · Executive Summary

Il **Registry v2** è la **rappresentazione documentale canonica** di tutti i 1500 items post-R18.5 Phase C. È una **dry-run design layer**: **runtime_apply_ready = false** su 1500/1500. La sua applicazione runtime è deferita all'**Apply Phase** (PM gate dedicato).

Rispetto al Registry v1 (Phase C1), v2 aggiunge:
- **Slug Errata Q1+Q5** applicata (canonical class slug italiani obbligatori)
- **4-field class taxonomy** per ogni riga
- **`slot_canonical`** popolato via alias map (14 canonical + 2 universal)
- **`source_canonical` + `source_type`** su 5 categorie (dungeon_canonical / raid_canonical / secondary_source / source_alias / meta_source)
- **`class_slug_resolution_status = 'deferred_to_r18_3f'`** enforced 1500/1500

---

## 1 · Schema (23 campi per riga)

```
item_id · nome_it · tier · rarity · required_level · ilvl ·
class_proficiency · legacy_class_label · canonical_class_slug · class_slug_resolution_status ·
slot_original · slot_canonical ·
source_original · source_canonical · source_type ·
armor_type · weapon_family · main_stat_target ·
can_be_sold_for_real_money · runtime_apply_ready · registry_status · progressive_marker · notes
```

---

## 2 · Slug Errata Applied (canonical mapping)

| legacy_class_label | legacy_class_key | canonical_class_slug | canonical_class_name_it |
|---|---|---|---|
| Warrior | `warrior` | `guerriero` | Guerriero |
| Rogue | `rogue` | `ladro` | Ladro |
| Mage | `mage` | `mago` | Mago |
| Priest | `priest` | **`paladino`** | Paladino |
| Ranger | `ranger` | **`cacciatore_di_mostri`** | Cacciatore di Mostri |

Ogni riga popola `legacy_class_label` (source of truth D1-D5) e `canonical_class_slug` (target R18.3f). Il `class_slug_resolution_status` = `deferred_to_r18_3f` per tutte le 1500 righe.

---

## 3 · Aggregate Summary

- **total_rows**: **1500**
- **registry_status_distribution**:
  - `applicable`: **1486**
  - `progressive_marker`: **10** (T4 Epic teaser)
  - `reserved`: **4** (Progressive Discovery P1-P4 Legendary)
- **canonical_class_slug_distribution**:
  - `guerriero`: 300 · `ladro`: 300 · `mago`: 300 · `paladino`: 300 · `cacciatore_di_mostri`: 300
- **slot_canonical_distribution**:
  - `main_hand`: 613 · `off_hand`: 129 · `chest`: 232 · `head`: 103 · `legs`: 83 · `feet`: 72
  - `accessory`: 68 · `ring`: 59 · `hands`: 58 · `neck`: 57
  - `consumable`: 17 · `material`: 9 (universal_allowed)
- **source_type_distribution**:
  - `dungeon_canonical`: 1040 · `raid_canonical`: 208 · `meta_source`: 191 · `secondary_source`: 53 · `source_alias`: 8
- **`progressive_marker=true`**: **10** ✅
- **`runtime_apply_ready=true`**: **0** ✅ (dry-run regime enforced)
- **`can_be_sold_for_real_money=false`**: **1500 / 1500** ✅ (anti-P2W)

---

## 4 · Rules Applied

1. **Progressive Discovery P1-P4** (4 Legendary reserved):
   - `registry_status = 'reserved'`
   - `runtime_apply_ready = false`
   - `source_canonical = 'PENDING_PM'`
   - `notes = 'Progressive Discovery placeholder · source PENDING PM post-C6 · runtime_apply_ready=false'`
2. **Tutti gli altri 1496 items**: `runtime_apply_ready = false` (regime documentale).
3. **NO apply · NO DB write · NO migration · NO registry live**.
4. **4-field class taxonomy** per ogni riga: `legacy_class_label` + `legacy_class_key` (implicit da SLUG_MAP) + `canonical_class_slug` + `class_slug_resolution_status`.
5. **`slot_canonical`** popolato via alias map o direct canonical:
   - `trinket → accessory` · `main-hand → main_hand` · `off-hand → off_hand` · `amulet → neck` · `belt → waist` · `cloak/cape → back` · `weapon_main → main_hand` · `weapon_off → off_hand`
6. **`source_canonical`** popolato via 5 categorie: `dungeon_canonical` (60 canonical) · `raid_canonical` (12 canonical) · `source_alias` (`void-heart-sanctum`) · `secondary_source` (`hollow-monastery`) · `meta_source` (tutorial/npc/vendor/crafting/ranking/achievement/quest/event/chest/starter-crafting/unknown/pending).

---

## 5 · Governance

- **File JSON companion**: `/app/memory/r18_5_registry_v2_dry_run.json`
- **Regime**: DOCUMENTAL ONLY · 36 seals byte-identical · zero DB/code/migrations/sealed touch
- **`lore_meta.py`**: INVARIATO (SHA256 confermato)
- **runtime_apply_ready**: **0 / 1500** (nessuna applicazione runtime)
- **Apply Phase**: 🔒 HOLD (PM gate dedicato, non C6)

---

## 6 · 🛑 STOP after Registry v2 Dry-Run

Registry v2 vive **solo come design layer documentale**. Nessuna operazione runtime, nessuna registrazione DB, nessuna migrazione. L'applicazione richiede **GO PM esplicito** per l'**Apply Phase**.
