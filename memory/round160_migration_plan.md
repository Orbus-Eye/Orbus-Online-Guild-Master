# Round 16.0 — Migration Plan (Fase 1 draft)

> Piano di migrazione classi → 10 base + specializzazioni + Stregone.
> Tutti gli script sono **idempotenti** (rerun = 0 nuove modifiche) e **non distruttivi** (no hard delete, soft-deprecate via flag).
> **NON eseguiti** in Fase 1. Esecuzione attesa in Fase 2 dopo validazione del piano.

---

## 1. Mapping definitivo classi (13 entry)

| slug attuale | azione | nuovo slug | spec slug derivata | display_name_it |
|---|---|---|---|---|
| warrior | KEEP base | warrior | — | Guerriero |
| rogue | KEEP base | rogue | — | Ladro |
| mage | KEEP base | mage | — | Mago |
| priest | KEEP base | priest | — | Sacerdote |
| ranger | KEEP base | ranger | — | Ranger |
| paladin | KEEP base | paladin | — | Paladino |
| druid | KEEP base | druid | — | Druido |
| monk | KEEP base | monk | — | Monaco |
| bard | KEEP base | bard | — | Bardo |
| — | **NEW base** | **warlock** | — | **Stregone** |
| berserker | DEPRECATE→ migrate | warrior | berserker_spec | Berserker (spec di Guerriero) |
| assassin | DEPRECATE→ migrate | rogue | assassin_spec | Assassino (spec di Ladro) |
| necromancer | DEPRECATE→ migrate | mage | necromancer_spec | Negromante (spec di Mago) |

---

## 2. Schema design

### 2.1 `adventurer_classes` (campi aggiunti/modificati)

```python
{
  # Esistenti (preservati):
  "slug": str,                              # uno di {warrior, rogue, mage, priest, ranger, paladin, druid, monk, bard, warlock} per base; o {berserker, assassin, necromancer} per deprecate
  "name": str,                              # legacy EN (preservato)
  "display_name_it": str,
  "primary_stat": str,
  "secondary_stats": list[str],
  "role": str,
  "secondary_role": str | None,
  "allowed_weapon_tags": list[str],
  "allowed_armor_tags": list[str],
  "xp_primary_stat_policy": dict,           # R15 schema_v2 invariato
  "description_it": str,
  "is_active": bool,                        # true per 10 base; false per 3 deprecate

  # NUOVI Round 16.0:
  "is_base_class": bool,                    # true per 10 nuove classi base
  "deprecated_at": datetime | None,         # NULL per attive; valorizzato per deprecate
  "successor_slug": str | None,             # es. "warrior" per berserker
  "successor_specialization_slug": str | None,  # es. "berserker_spec" per berserker
  "round_intro": int,                        # 16 per warlock; mantenuto/ND per gli altri
}
```

### 2.2 `class_specializations` (nuova collection)

```python
{
  "slug": str,                              # es. "berserker_spec"
  "class_slug": str,                        # parent base class
  "display_name_it": str,
  "description_it": str,
  "stat_bonus": dict,                       # opzionale, es. {"strength": 1}
  "weapon_tag_unlocks": list[str],          # tag extra sbloccati
  "armor_tag_unlocks": list[str],
  "counter_tags": list[str],                # per Fase 4 threats/counters
  "is_unlockable": bool,                    # default True
  "requires_class_hall_level": int,         # default 1
  "is_active": bool,                        # default True
  "is_legacy_migration_target": bool,       # true per berserker_spec/assassin_spec/necromancer_spec (auto-mapped da deprecate)
  "created_at": datetime,
  "updated_at": datetime,
}
```

### 2.3 `adventurers` (campi aggiunti)

```python
{
  # Esistenti (invariati):
  "class_slug": str | None,                 # base class lowercase
  "class_name": str | None,                 # legacy display capitalized
  "specialization": dict | None,            # training/respec snapshot R6C (INVARIATO)

  # NUOVI Round 16.0:
  "specialization_slug": str | None,        # spec di CLASSE (es. "berserker_spec"); default None
  "specialization_applied_at": datetime | None,
  "specialization_applied_by_user_id": str | None,

  # NUOVI Fase 3:
  "race_slug": str | None,                  # default null; backfill atomico
  "gender": str | None,                     # "male" | "female"; backfill atomico
}
```

### 2.4 `class_halls` (nuova collection, struttura figlia di Training Territory)

```python
{
  "_id": "{guild_id}::{class_slug}",        # compound key idempotenza
  "guild_id": str,
  "class_slug": str,                        # base class
  "is_unlocked": bool,                      # default False
  "unlocked_at": datetime | None,
  "level": int,                             # 1..10
  "unlocked_specializations": list[str],    # subset di class_specializations.slug per quella class
  "training_territory_id": str | None,      # FK alla struttura padre (territory)
  "created_at": datetime,
  "updated_at": datetime,
}
```

### 2.5 `items` (campi aggiunti, opzionali)

```python
{
  # Esistenti invariati: class_tags, recommended_classes, weapon_tags, armor_tags

  # NUOVO Round 16.0 (opzionale, non rompe items legacy):
  "specialization_unlocks": list[str],      # es. ["berserker_spec"] per item che richiedono spec specifica
}
```

### 2.6 Equip validator extensions (Fase 5, NON Fase 2)

`equipment/compatibility.py::check_equip_compatibility` ragionerà su:
- `adventurer.class_slug` (base) + `adventurer.specialization_slug`
- `item.class_tags` (esistente) + `item.specialization_unlocks` (nuovo)

Compat retro:
- Item con `class_tags=["berserker"]` (legacy) → equipaggiabile da `class_slug="warrior" + specialization_slug="berserker_spec"`.
- Item universale (class_tags vuoto) → invariato.

---

## 3. Specializzazioni seedate (30 totali, 3 per classe)

### Guerriero
- `berserker_spec` (DPS rage, weapon_tag_unlocks=[two_handed, axe, rage], stat_bonus={strength:1})
- `guardian_spec` (Tank def, armor_tag_unlocks=[heavy, shield], stat_bonus={endurance:1})
- `weapon_master_spec` (Versatile DPS/Tank, weapon_tag_unlocks=[finesse], stat_bonus={strength:1, agility:1})

### Ladro
- `assassin_spec` (DPS burst, weapon_tag_unlocks=[poison], stat_bonus={agility:1, strength:1})
- `duelist_spec` (DPS finezza, weapon_tag_unlocks=[shortsword, finesse], stat_bonus={agility:1})
- `shadow_spec` (Sneak hybrid, stat_bonus={agility:1, intellect:1})

### Mago
- `necromancer_spec` (DoT, weapon_tag_unlocks=[scythe, dark], stat_bonus={intellect:1, agility:1})
- `elementalist_spec` (Burst AoE, stat_bonus={intellect:1})
- `arcanist_spec` (Control/Buff, stat_bonus={intellect:1, faith:1})

### Sacerdote
- `healer_spec` (Heal puro, stat_bonus={faith:1})
- `exorcist_spec` (Anti-Undead, counter_tags=[undead, void], stat_bonus={faith:1, intellect:1})
- `oracle_spec` (Buff/Predict, stat_bonus={faith:1, intellect:1})

### Ranger
- `marksman_spec` (Ranged DPS, weapon_tag_unlocks=[bow, crossbow], stat_bonus={agility:1})
- `monster_hunter_spec` (Anti-Beast, counter_tags=[beast, dragon], stat_bonus={agility:1, strength:1})
- `scout_spec` (Recon, stat_bonus={agility:1, intellect:1})

### Druido
- `leafwarden_spec` (Heal natura, stat_bonus={faith:1, intellect:1})
- `shapeshifter_spec` (Hybrid DPS/Tank, stat_bonus={strength:1, faith:1})
- `shaman_spec` (Caster elementi, weapon_tag_unlocks=[totem], stat_bonus={faith:1, intellect:1})

### Monaco
- `inner_fist_spec` (Pure martial, weapon_tag_unlocks=[unarmed], stat_bonus={agility:1, endurance:1})
- `spirit_guardian_spec` (Tank/Healer hybrid, stat_bonus={faith:1, endurance:1})
- `ascetic_spec` (Disciplined burst, stat_bonus={agility:1, faith:1})

### Bardo
- `warsinger_spec` (Combat support, weapon_tag_unlocks=[sword, dagger], stat_bonus={intellect:1, strength:1})
- `herald_spec` (Buff/Aura, stat_bonus={intellect:1, faith:1})
- `inspiration_weaver_spec` (Heal/Buff, stat_bonus={intellect:1, faith:1})

### Paladino
- `oath_defender_spec` (Pure Tank, armor_tag_unlocks=[shield, heavy], stat_bonus={endurance:1, faith:1})
- `rune_knight_spec` (Magic Tank hybrid, stat_bonus={faith:1, intellect:1})
- `vindicator_spec` (Anti-Undead/Demon, counter_tags=[undead, demon], stat_bonus={faith:1, strength:1})

### Stregone (Warlock)
- `demon_pact_spec` (DPS infernale, weapon_tag_unlocks=[tome], stat_bonus={intellect:1, faith:1})
- `void_pact_spec` (DoT debuffer, counter_tags=[void], stat_bonus={intellect:1, agility:1})
- `stellar_pact_spec` (Burst+heal hybrid, stat_bonus={intellect:1, faith:1})

Tutte: `is_unlockable=true`, `is_active=true`, `requires_class_hall_level=1`.

---

## 4. Script di migrazione (creati in Fase 1, eseguiti in Fase 2)

| # | File | Tipo | Output |
|---|---|---|---|
| 1 | `app/scripts/round160_class_audit.py` | READ-ONLY | Stampa snapshot equivalente a `class_audit.md` (per CI/CD) |
| 2 | `app/scripts/round160_seed_classes_v2.py` | UPSERT | +1 classe (warlock) · 10 classi marcate `is_base_class=true` · 3 marcate `deprecated_at + successor_*` · 30 specializzazioni seedate in `class_specializations` |
| 3 | `app/scripts/round160_migrate_adventurers_deprecated_classes.py` | UPDATE | Per ogni adv con `class_slug∈{berserker,assassin,necromancer}` o `class_name∈{Berserker,Assassin,Necromancer}` → set `class_slug=successor + specialization_slug=successor_spec + class_name=successor_capitalized`. Audit log `class_migrated_round160`. Skip se già migrato. |
| 4 | `app/scripts/round160_update_items_class_tags.py` | UPDATE | Per ogni item con `class_tags ∩ {berserker,assassin,necromancer}≠∅` → aggiunge base class (es. "warrior") al `class_tags` se manca + valorizza `specialization_unlocks=[spec_slug]`. Tag legacy preservato. |
| 5 | `app/scripts/round160_update_achievements_legacy_classes.py` | UPDATE | Sostituisce reference testuali nei `name_it`/`description_it` solo se citano "primary class" deprecata. 0 hit attesi (dry-run audit). |

### Garanzia di idempotenza
- Tutti gli script:
  1. Leggono lo stato corrente prima di scrivere
  2. Usano `$set` mirato + filtri "non-yet-migrated" (es. `successor_slug: {$exists: false}`)
  3. Audit log per ogni record toccato, **mai per record skippati**
  4. Restituiscono dict `{updated, skipped, errors}` per il caller
- Rerun atteso: `updated=0, skipped=N, errors=0`

### Strategia di rollback
- Nessun hard delete → rollback = riemettere classi deprecate come `is_active=true` + spostare adventurer.class_slug indietro tramite audit log replay
- Audit log dedicato `class_migrated_round160` traccia `before/after` di ogni adv migrato

---

## 5. Eventi audit log nuovi (saranno aggiunti alla whitelist in Fase 2)

```python
"class_deprecated_round160"      # quando classe marcata deprecate
"class_created_round160"          # quando warlock viene creato
"class_specialization_seeded"     # per ogni spec seedata
"adventurer_class_migrated"       # per ogni adv spostato berserker→warrior+spec, etc.
"item_class_tags_extended"        # per ogni item con base class aggiunta
```

---

## 6. Ordine esecuzione Fase 2

1. **2.1** Aggiungere whitelist eventi a `audit/log.py` (additive, no breaking)
2. **2.2** Eseguire `round160_seed_classes_v2.py` (catalog + specs)
3. **2.3** Eseguire `round160_migrate_adventurers_deprecated_classes.py` (~20.940 records, batch da 500 con cursor)
4. **2.4** Eseguire `round160_update_items_class_tags.py` (~123 records)
5. **2.5** Eseguire `round160_update_achievements_legacy_classes.py` (dry-run + no-op atteso)
6. **2.6** Verifica integrità: `class_slug` di ogni adv ∈ {10 base}, `specialization_slug` di ogni adv migrato è valido, items integri.
7. **2.7** Pytest full sweep: 127 stabili attesi + nuovi test invariant Round 16

---

## 7. Bloccanti / aperti

- Nessun bloccante identificato.
- Aperti P1 (Fase 5): aggiornare `equipment/compatibility.py` per ragionare su `specialization_slug` (non in Fase 2 per minimizzare rischio).
- Aperti P1 (Fase 5): aggiornare `training/catalog.py` per estendere `eligible_classes` mapping.
- Aperti (Fase 3): backfill atomico `race_slug` + `gender` su 90.611 records.
- Aperti (Fase 4): seed dungeon threats/counters schema-only.

---

## 8. Test invariant attesi post-Fase 2

```python
# tests/backend_round160_class_invariants_test.py (creato in Fase 2)
def test_all_active_classes_are_base():
    # 10 classi attive, tutte base, tutte con primary_stat
    pass

def test_deprecated_classes_have_successor():
    # 3 classi deprecate hanno successor_slug + successor_specialization_slug
    pass

def test_no_active_adventurer_in_deprecated_class():
    # 0 avventurieri con class_slug∈{berserker,assassin,necromancer}
    pass

def test_specializations_catalog_30():
    # class_specializations.count = 30
    pass

def test_legacy_items_still_equippable():
    # item con class_tags=["berserker"] → equipaggiabile da warrior+berserker_spec
    pass
```

---

**Piano migrazione chiuso: SI — pronto per esecuzione Fase 2 dopo validazione tester.**
