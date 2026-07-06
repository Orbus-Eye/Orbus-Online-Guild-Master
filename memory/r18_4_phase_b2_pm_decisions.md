# R18.4 Phase B2 — PM Decision Lock

- **Round**: R18.4 — Item Class-Bound Player-Facing — Phase B2
- **Stage**: Decision Lock (SQ1-SQ7 verbatim dal PM)
- **Locked at UTC**: `2026-07-06T05:05:00Z`
- **Seal Authority**: PM Orchestrator
- **Direzione**: Option 3 Hybrid Refined (LOCKED)
- **Perimetro**: documental-only decision lock. Zero code change runtime. Zero DB write. Sibling scripts B3 = DRY-RUN only.
- **Fonti**: `r18_4_phase_b1_deep_dive_audit.md`/`.json` + risposte PM verbatim SQ1..SQ7 (chat 2026-07-06).

---

## 1. Lock SQ1-SQ7 (verbatim risposta PM)

### SQ1 — Shield (2 items) slot mapping → **(a) mappa i 2 shield item in `armor`**
- Scelta SAFE, no 4° slot, no breaking UI/equip.
- Effetto: backfill slot_type → **140/140**.
- Backlog P3: `R18.4.followup — Shield slot mapping decision`.

### SQ2 — `specialization_unlocks` DEAD branch → **mantenere + documentare come "reserved for future specialization system"**
- NO rimuovere. NO usare come SoT R18.4. NO nuova logica.
- Backlog P3: `R18.4.backlog — specialization_unlocks dead branch cleanup`.

### SQ3 — `required_class_optional` (back-compat) + `item_binding_policy` (policy esplicita override governance) → **coexistence**
- Precedenza target LOCKED (da documentare in B2, applicabile a nuovi round; **NON runtime change in R18.4**):
  1. **Hard block esistente** (heavy_armor_forbidden, arcane_weapon_forbidden, level_gate, ownership)
  2. `required_class_optional` (back-compat, 11 items)
  3. `item_binding_policy` (nuovo campo, override esplicito)
  4. `recommended_classes` / `class_tags` (soft guidance)

### SQ4 — Items `required_class_optional=berserker/assassin` (6 items dormant) → **(a) lascia dormant + backlog P3 revisit**
- NO disattivare. NO rimuovere catalog. NO cambio classe target. NO unlock implicito berserker/assassin.
- Backlog P3: `R18.4.backlog — berserker/assassin dormant signature items`.

### SQ5 — EQUIP_WARNING rate-limit strategy → **(b) daily bucket per `(guild_id, adventurer_id, reason_code)`**
- Max 1 warning event / day per combo.
- `EQUIP_BLOCKED` resta audit pieno (no rate-limit).
- `EQUIP_WARNING` telemetry controllata.

### SQ6 — `item_binding_policy` schema campo default derivation (LOCKED)
```
E1 signature hard       → hard
E2 signature soft       → soft
A legacy only           → soft
C mixed                 → soft
G1 equippable generic   → soft
G2 materials/consumable → universal
```

### SQ7 — UI 4-state signal → **SÌ, aggiungere `recommended_for_class: bool` + `is_universal: bool` in `item_public()` response**
- Derivati runtime da current fields.
- UI target 4-state:
  1. Non equipaggiabile / Bloccato
  2. Equipaggiabile ma non consigliato
  3. Consigliato per questa classe
  4. Universale
- NO ambiguità tra hard block e soft warning.

---

## 2. Schema `item_binding_policy` field

```yaml
field:            items.item_binding_policy
type:             string (enum)
values:           [hard, soft, universal]
required:         false (nullable, default derivation via bucket)
serialization:    exposed in item_public()
governance:       R18.4 catalog metadata only — NO runtime enforcement change in R18.4
default_derivation_algorithm:
  1. IF items.required_class_optional populated (non-null, non-empty)     → hard
  2. IF items.item_type IN (material, material_continental,
                           material_event, consumable)                    → universal
  3. ELSE                                                                 → soft

precedenza_target_documental (SQ3, applicabile solo in round futuri):
  step_1_hard_blocks:  heavy_armor_forbidden | arcane_weapon_forbidden
                       | level_gate | ownership (bound_to_adventurer)
  step_2_required:     required_class_optional (back-compat, 11 items)
  step_3_policy:       item_binding_policy (nuovo override esplicito)
  step_4_soft:         recommended_classes / class_tags (soft guidance)
```

---

## 3. Mapping UI 4-state + signals API

```yaml
api_response_additions_item_public:
  recommended_for_class:  bool  # true se class_slug in recommended_classes o class_tags
  is_universal:           bool  # true se item_binding_policy=='universal' OR item_type in universal_types
  # NOTE: derivati runtime, NON persistiti in DB

ui_states_locked:
  state_1_blocked:
    signal:      severity == "block" (da check_equip_compatibility)
    ui_badge:    icon rossa · label "Non equipaggiabile"
    reason:      reason_it dal backend
  state_2_warning:
    signal:      severity == "warning"
    ui_badge:    icon gialla · label "Non consigliato"
    reason:      warning_it dal backend
  state_3_recommended:
    signal:      severity == "ok" AND recommended_for_class == true
    ui_badge:    icon verde · label "Consigliato"
    reason:      —
  state_4_universal:
    signal:      severity == "ok" AND is_universal == true AND !recommended_for_class
    ui_badge:    icon grigia · label "Universale"
    reason:      —
  state_5_neutral_ok:
    signal:      severity == "ok" AND !recommended_for_class AND !is_universal
    ui_badge:    nessuno
    reason:      —
```

---

## 4. Rate-limit strategy EQUIP_WARNING

```yaml
audit_event_equip_blocked:
  event_type:       EQUIP_BLOCKED
  rate_limit:       UNLIMITED (rare event, sempre audit pieno)
  metadata:         {guild_id, adventurer_id, item_id, item_slug, reason_code,
                     class_slug, source_route, timestamp}

audit_event_equip_warning:
  event_type:       EQUIP_WARNING
  rate_limit:       daily bucket per (guild_id, adventurer_id, reason_code)
  max_per_day:      1 (per la combo)
  bucket_id:        f"{guild_id}:{adventurer_id}:{reason_code}:{YYYY-MM-DD-UTC}"
  storage:          audit_log con idempotency_key = bucket_id (upsert-on-write)
  metadata:         {guild_id, adventurer_id, item_id, item_slug, reason_code,
                     class_slug, source_route, timestamp, rate_bucket_id}
  fallback:         se collezione idempotency non disponibile → skip write
  telemetry_only:   true (no player-facing side effect)
```

---

## 5. Default derivation con conteggi finali per policy

Query eseguita in read-only sul DB live (`items` collection, 178 doc):

| Policy | Count | Derivation rule | Item type distribution |
|---|---|---|---|
| **hard** | **11** | `required_class_optional` populated | armor: 3 · weapon: 8 |
| **universal** | **21** | `item_type` ∈ {material, material_continental, material_event, consumable} | material: 8 · material_continental: 8 · material_event: 3 · consumable: 2 |
| **soft** | **146** | else (residuo catalog) | weapon: 53 · armor: 43 · accessory: 48 · shield: 2 |
| **Total** | **178** | — | verified: overlap hard∩universal = 0 |

---

## 6. Lista item HARD (esaustiva, 11)

| # | Slug | required_class_optional | item_type | slot_type target |
|---|---|---|---|---|
| 1 | `drake_slayer_helm` | warrior | armor | armor (già `helm`) |
| 2 | `drake_slayer_chest` | warrior | armor | armor (già `chest`) |
| 3 | `drake_slayer_blade` | warrior | weapon | weapon (già `weapon_main`) |
| 4 | `spec_signature_truestrike_bow` | ranger | weapon | weapon (già `weapon_main`) |
| 5 | `spec_signature_bloodied_greataxe` | berserker (dormant) | weapon | weapon (già `weapon_main`) |
| 6 | `spec_signature_breakers_gauntlets` | warrior | armor | armor (già `chest`) |
| 7 | `spec_signature_silent_kris` | assassin (dormant) | weapon | weapon (già `weapon_main`) |
| 8 | `spec_signature_storm_rod` | mage | weapon | weapon (già `weapon_main`) |
| 9 | `spec_signature_corrupted_blade` | necromancer | weapon | weapon (già `weapon_main`) |
| 10 | `spec_signature_twin_blades` | rogue | weapon | weapon (già `weapon_main`) |
| 11 | `spec_signature_runic_aegis` | paladin | armor | armor (già `chest`) |

- **Dormant subset (SQ4)**: item #5 (`bloodied_greataxe`) + item #7 (`silent_kris`) — de facto unusable (0 adventurer live per berserker/assassin post-reset). Lasciati dormant per PM lock.
- Nota: tutti gli 11 hard hanno GIÀ `slot_type` populated (livello "granulare" tipo `weapon_main`/`chest`/`helm`). Il backfill slot_type in B3 NON tocca questi (11 items).

---

## 7. Lista item UNIVERSAL (esaustiva, 21)

Derivati via `item_type ∈ {material, material_continental, material_event, consumable}`.

```
item_type=material (8):
  - determinati via query dry-run — vedi registry
    /app/memory/r18_4_class_bound_registry.json chiave "universal_items"

item_type=material_continental (8):
  - determinati via query dry-run — vedi registry

item_type=material_event (3):
  - determinati via query dry-run — vedi registry

item_type=consumable (2):
  - determinati via query dry-run — vedi registry
```

Elenco pieno slug in `/app/memory/r18_4_class_bound_registry.json` (sezione `universal_items`).

---

## 8. Lista eccezioni / manual override

**Nessuna eccezione manuale registrata in B2.**

Tutti gli 11 hard e i 21 universal derivano dal PM default derivation rule (SQ6). Non ci sono manual override richiesti dal PM in questa fase.

Se in futuro emergono item che richiedono binding policy diversa dal default (es. un item weapon che deve essere universal per lore reasons), sarà aggiunto in un round dedicato con PM gate esplicito.

---

## 9. Backfill plan slot_type

```yaml
target_collection:       items
target_count:            140 / 140 (100%)
target_filter:           slot_type IN (null, missing) AND item_type IN (weapon, armor, accessory, shield)

mapping_rule:
  weapon    → slot_type = "weapon"
  armor     → slot_type = "armor"
  accessory → slot_type = "accessory"
  shield    → slot_type = "armor"    # SQ1 opzione (a): mappa in armor (SAFE, no 4° slot)

breakdown_target:
  weapon:    54 items → slot_type="weapon"
  armor:     42 items → slot_type="armor"
  accessory: 42 items → slot_type="accessory"
  shield:     2 items → slot_type="armor"
  TOTAL:    140 items

edge_cases_handling:
  already_populated: 17 items con slot_type non-null (livello granulare "weapon_main", "helm", "chest", "amulet", "ring", "gloves") — SKIP (no overwrite)
  materials/consumable: 21 items con item_type NOT in equipable set — SKIP (out of scope)
  item_type_missing: 0 items — nessuno

script_governance:
  file: /app/backend/app/scripts/round18_4_backfill_slot_type.py
  APPLY_ENABLED: false (LOCKED — richiede nuovo PM gate per True)
  double_flag_required: --apply --i-understand-this-will-backfill-slot-type
  default_mode: dry-run
  guard_hard_stop: BLOCKED_FIELDS = {class_slug, role, primary_stat, secondary_stats,
                                     base_*, is_playable, is_active, is_canonical,
                                     item_binding_policy (backfill separato),
                                     required_class_optional, class_tags, recommended_classes}
  audit_event_would_emit: R18_4_SLOT_TYPE_BACKFILL_APPLIED (aggregated, 1 evento globale)
  backup_snapshot_would_write: /app/memory/r18_4_slot_type_pre_apply_snapshot_<ts>.json
```

---

## 10. Risk matrix aggiornata + precedenza fields

| Rischio | Livello | Blocked | Note |
|---|---|---|---|
| Backfill slot_type 140 items (dry-run only) | 🟢 SAFE | NO | mapping deterministico; only null → populated; skip 17 existing |
| Shield → armor mapping (2 items) | 🟢 SAFE | NO | SQ1(a) confermato; no breaking UI/equip |
| `item_binding_policy` catalog field add | 🟢 SAFE | NO | catalog metadata only, no runtime enforcement in R18.4 |
| UI 4-state signal (`recommended_for_class`/`is_universal`) | 🟢 SAFE | NO | derived at read-time in `item_public()`, no DB change |
| Rate-limit strategy audit EQUIP_WARNING | 🟢 SAFE | NO | idempotency_key upsert; no player-facing |
| Rimozione berserker/assassin dormant items | 🔴 BLOCKED | YES | SQ4(a): dormant + P3 backlog revisit |
| Rimozione specialization_unlocks branch | 🔴 BLOCKED | YES | SQ2: mantenere + doc; P3 backlog cleanup |
| Enforcement runtime nuovo (item_binding_policy in compatibility.py) | 🔴 BLOCKED | YES | fuori scope R18.4; separato round PM |
| Migration adventurers.class_slug → canonical IT | 🔴 BLOCKED | YES | R18.3f dedicated round |
| Bridge R18.3e runtime wiring | 🔴 BLOCKED | YES | R18.3f gate |
| Unlock recruitment CdM/CdV | 🔴 BLOCKED | YES | separate round |
| Modifica VALID_ROLES (Bard drift) | 🔴 BLOCKED | YES | R18.3d.followup backlog |
| Change player-facing labels classi | 🔴 BLOCKED | YES | separate round |

**Precedenza fields target (SQ3, documental-only R18.4)**:
```
1. hard_block (heavy_armor | arcane_weapon | level | ownership)
2. required_class_optional (back-compat, 11 items)
3. item_binding_policy (new override explicit)
4. recommended_classes / class_tags (soft guidance)
```

---

## 11. Test plan B3

```yaml
test_suite_target: /app/backend/tests/backend_r18_4_class_bound_test.py
minimum_tests:     16
test_isolation:    orbus_r18_4_test (fresh test DB, cleanup via prefix)

test_groups:
  group_1_registry_shape (3 tests):
    - t01_registry_json_parsable
    - t02_registry_totals_178_11_21_146
    - t03_registry_hard_items_exact_11_slugs

  group_2_bucket_derivation (4 tests):
    - t04_hard_derivation_required_class_optional
    - t05_universal_derivation_material_consumable
    - t06_soft_derivation_residual
    - t07_no_overlap_hard_intersect_universal

  group_3_backfill_dry_run (4 tests):
    - t08_backfill_dry_run_target_count_140
    - t09_backfill_shield_maps_to_armor
    - t10_backfill_skip_already_populated_17
    - t11_backfill_apply_enabled_false_blocks_write

  group_4_class_bound_dry_run (3 tests):
    - t12_class_bound_dry_run_would_add_binding_policy_178
    - t13_class_bound_guard_hard_stop_rejects_blocked_fields
    - t14_class_bound_apply_enabled_false_blocks_write

  group_5_rate_limit_and_signals (2 tests):
    - t15_rate_limit_bucket_key_format
    - t16_derived_signals_recommended_for_class_and_universal

regression_gate:
  - 27 test R16.5.4b esistenti → devono continuare a passare
  - 24 sigilli byte-identical → verify sha256sum invariato pre/post B3
```

---

## 12. Explicit no-go boundaries (LOCKED per B3 dry-run)

**B3 NON deve toccare (hard-stop guard nei sibling script)**:

- ❌ **`class_slug`** su qualsiasi collezione (adventurers, adventurer_classes, items)
- ❌ **`role`** su adventurer_classes
- ❌ **`primary_stat`** / **`secondary_stats`** su adventurer_classes / adventurers
- ❌ **`base_strength`** / **`base_agility`** / **`base_intellect`** / **`base_endurance`** / **`base_faith`** (base_*) su adventurer_classes
- ❌ **`is_playable`** / **`is_active`** / **`is_canonical`** su adventurer_classes
- ❌ **`VALID_ROLES`** in `backend/app/admin/services.py`
- ❌ **`adventurers` collection** — zero write
- ❌ **items rewrite canonical IT** (name, display_name, description in canonical translation)
- ❌ **Unlock recruitment CdM / CdV**
- ❌ **Unlock berserker / assassin** (dormant classes)
- ❌ **`is_active=false`** su qualsiasi item dormant (mantenere dormant SQ4)
- ❌ **Rimozione** di qualsiasi item dal catalog
- ❌ **Rimozione branch `specialization_unlocks`** in `compatibility.py`
- ❌ **Modifica Bard role drift** (`bard.role='Support'`)
- ❌ **Cambio player-facing label** delle classi
- ❌ **Hard delete** su qualsiasi collezione
- ❌ **Touch dei 19 file sigillati** (14 R18.Reset + 5 R18.3d + 5 R18.3e; verify byte-identical via SHA256)
  - Nota: aggregate governance count PM = 24 (include contract-lock docs); enforcement hard SHA256 = 19 file esplicitamente registrati in `r18_3e_seal_registry.json`

**Hard-stop nel script**: qualsiasi tentativo di apply payload che contenga uno dei field/target sopra → `raise SystemExit("[GUARD FAIL-FAST] ...")`.

**APPLY_ENABLED lock**: entrambi i sibling script (`round18_4_backfill_slot_type.py`, `round18_4_apply_class_bound.py`) hanno `APPLY_ENABLED = False` hard-coded. Il PM può flippare solo via review pre-report B3 + nuovo GO esplicito. Fino ad allora, `--apply` viene sempre rigettato con SystemExit.

---

## Self-Check B2 10/10

1. ✅ 11 sezioni obbligatorie complete + section 12 no-go boundaries
2. ✅ SQ1-SQ7 lock verbatim dal PM
3. ✅ Schema `item_binding_policy` documentato (enum, default derivation, precedenza)
4. ✅ UI 4-state mapping + signal API `recommended_for_class` + `is_universal`
5. ✅ Rate-limit strategy EQUIP_WARNING (daily bucket, key format)
6. ✅ Default derivation counts (11 hard + 21 universal + 146 soft = 178)
7. ✅ Lista item hard esaustiva (11)
8. ✅ Backfill plan slot_type (140/140, shield→armor)
9. ✅ Risk matrix + precedenza fields
10. ✅ Test plan B3 (16 test, 5 gruppi) + explicit no-go boundaries (13 vincoli)

**STOP Phase B2**. Ready to open **Phase B3 — Dry-Run only** (autorizzato condizionalmente dal PM).
