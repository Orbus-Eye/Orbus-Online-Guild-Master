# Round 16.0 — Class Audit (Fase 1)

> Audit read-only del catalog classi corrente in vista del rework "10 classi base + specializzazioni".
> Scope: catalog `adventurer_classes`, riferimenti `class_slug`/`class_name`/`recommended_classes` nel codice e nei dati. Niente scrittura DB in questa fase.

---

## Executive summary (10 righe)

- Catalog attuale: **12 classi attive** in `adventurer_classes`, di cui 9 confermate "base" + 3 da deprecare (`berserker`, `assassin`, `necromancer`) come specializzazioni.
- Migrazione richiesta: **~20.940 avventurieri** in classi deprecate (Berserker 6.963 · Assassin 7.065 · Necromancer 6.912), tutti referenziati via `class_name` capitalized.
- Items da aggiornare (class_tags legacy): **123 records** (62 berserker + 29 assassin + 32 necromancer); tag legacy resta per back-compat, base class aggiunto in modo non distruttivo.
- Achievements: **0 hit testuali** su classi deprecate (`berserker`/`assassin`/`necromancer`/italiani equivalenti). Paladino: 1 achievement (`specialista-paladin`) — resta valido (paladin rimane classe base).
- Test references: **1 file** (`backend_round15_phase2_test.py`) cita "berserker" in 2 righe come `recommended_classes`, non blocker (item-side, retro-compat conservata).
- Code hotspots: `seeds/seed_data.py`, `training/catalog.py`, `equipment/compatibility.py`, `scripts/round15_seed_*` — tutti sostituibili in modo idempotente, nessuna logica gameplay rigida.
- Campo `specialization` su `adventurers` (642/92.102) è un dict snapshot training/respec → **rinominato concettualmente come `training_specialization`**, mai sovrascritto. Nuovo campo `specialization_slug` (string nullable) introdotto per class-level spec.
- Stat catalog: **5 stat** (`strength, agility, intellect, endurance, faith`) — `charisma` NON esiste. Decisione Stregone: `primary_stat=intellect` (con racconto narrativo che lo separa dal Mago "studioso").
- Race/gender: `race` field già esistente con valore unico `"human"` su 84 records; `race_slug`/`gender` mai valorizzati → backfill atomico in Fase 3.
- Test suite stabile R12+R13+R14+R15: 127 passed, 0 fail (non toccata in Fase 1).

---

## 1. Catalog classi attive (12)

| slug | display_name_it | primary_stat | role | secondary_stats | allowed_weapon_tags | allowed_armor_tags |
|---|---|---|---|---|---|---|
| warrior | Guerriero | strength | Tank | endurance | sword, axe, mace, two_handed | heavy, shield, medium |
| rogue | Ladro | agility | DPS | strength | dagger, shortsword, finesse | light, leather |
| mage | Mago | intellect | DPS | endurance | staff, wand, arcane | cloth, robe, light |
| priest | Sacerdote | faith | Healer | intellect | mace, scepter, holy | cloth, robe, holy |
| ranger | Ranger | agility | DPS | endurance | bow, crossbow, ranged | light, medium, leather |
| paladin | Paladino | faith | Tank | strength, endurance | sword, mace, two_handed | heavy, shield, holy |
| druid | Druido | faith | Healer | intellect | staff, club, natural | leather, cloth, natural |
| monk | Monaco | agility | DPS | endurance, faith | unarmed, staff, martial | cloth, light, martial |
| bard | Bardo | intellect | Support | agility, faith | dagger, instrument, sonic | light, leather |
| **berserker** | Berserker | strength | DPS | endurance | two_handed, axe, rage | medium, light | ⚠ DEPRECATE |
| **assassin** | Assassino | agility | DPS | strength | dagger, finesse, poison | light | ⚠ DEPRECATE |
| **necromancer** | Negromante | intellect | DPS | agility | staff, scythe, dark | cloth, bone | ⚠ DEPRECATE |

> XP debuff policy (R15 schema_v2) presente identica su tutte e 12 — verrà preservata.

---

## 2. Distribuzione avventurieri per classe (DB live)

| class_name (capitalized) | count |
|---|---:|
| Warrior | 11.612 |
| Ranger | 7.473 |
| Rogue | 7.410 |
| Priest | 7.402 |
| Mage | 7.374 |
| **Assassin** | **7.065** ⚠ |
| Monk | 6.991 |
| **Berserker** | **6.963** ⚠ |
| Druid | 6.949 |
| **Necromancer** | **6.912** ⚠ |
| Bard | 6.888 |
| Paladin | 6.839 |
| warrior (lowercase legacy) | 2.060 |
| None / Test Class / mage | 164 |

**Totale da migrare**: **20.940** avventurieri (Berserker + Assassin + Necromancer).

> Nota: 592 records hanno anche `class_slug` valorizzato, il resto si appoggia su `class_name`. Lo script di migrazione gestisce entrambi i casi.

---

## 3. Impact sulle 3 classi deprecate

| Voce | berserker | assassin | necromancer |
|---|---:|---:|---:|
| `adventurers.class_name` capitalized | 6.963 | 7.065 | 6.912 |
| `adventurers.class_slug` lowercase | 0 | 0 | 0 |
| `items.class_tags` contiene | 62 | 29 | 32 |
| `items.recommended_classes` contiene | 62 | 29 | 32 |
| `achievements_catalog.name_it` match (case-i) | 0 | 0 | 0 |
| `achievements_catalog.description_it` match | 0 | 0 | 0 |
| `training/catalog.py` `eligible_classes` reference | 3 entries | 1 entry | 2 entries |
| `equipment/compatibility.py` blacklist reference | 0 (Tank list) | 1 (arcane block) | 1 (heavy block) |
| `tests/*` reference | 2 righe (`backend_round15_phase2_test.py`, item-side) | 0 | 0 |

---

## 4. Code hotspots con slug hard-coded

File con riferimenti diretti a slug classe (incluse le 9 da preservare + 3 da deprecare):

```
backend/app/equipment/compatibility.py    → NO_HEAVY_ARMOR_CLASSES, NO_ARCANE_WEAPON_CLASSES (frozenset di slug)
backend/app/training/catalog.py            → 6 specializzazioni con eligible_classes
backend/app/training/services.py           → no slug literal (usa class_name)
backend/app/adventurers/generator.py       → seeds di lore
backend/app/adventurers/common.py          → mapping class_name → class_slug
backend/app/auth/services.py               → guard register flow
backend/app/onboarding/services.py         → starter roster
backend/app/content/lore_meta.py           → lore mapping
backend/app/core/email_templates.py        → welcome email lore
backend/app/seeds/seed_data.py             → 12 classi base seed
backend/app/seeds/seed_items_it.py         → items seed
backend/app/seeds/seed_round5.py           → starter roster
backend/app/expeditions/loot_tables.py     → loot mapping
backend/app/expeditions/material_drop_tables.py → tier mapping
backend/app/stats/public_catalog.py        → no slug literal
backend/app/scripts/round15_seed_class_identity.py  → 12 classi seed identità
backend/app/scripts/round15_seed_item_tags.py       → items class_tags mapping
backend/app/scripts/round15_seed_achievements.py    → achievement seed
backend/app/scripts/round15_phase2_evidence_*.py    → 2 file di evidence
backend/app/scripts/seed_preview_tester_round6c.py  → tester roster
backend/app/scripts/seed_preview_tester_round6e.py  → tester roster R6E
```

Tutti questi file restano **invariati in Fase 1**. La migrazione su catalog è non-distruttiva (deprecate-flag + successor-pointer); la migrazione sugli items è additiva (aggiunge base class a `class_tags` senza rimuovere il tag legacy).

---

## 5. Reference nei test

```
backend/tests/backend_round15_phase2_test.py:78    "recommended_classes": ["warrior", "berserker"]
backend/tests/backend_round15_phase2_test.py:96    item = {"item_type": "weapon", "required_class_optional": "berserker"}
```

Entrambi gli usi sono **item-side**, non avventuriere-side. Resteranno validi anche dopo la deprecate: il tag legacy `berserker` viene preservato come specialization tag.

---

## 6. Campo `specialization` legacy (training/respec)

- Records con `specialization` valorizzato: **642 / 92.102** (~0.7%).
- Struttura: **dict snapshot** (slug + name + modifiers + applied_at + signature_item_id) prodotto dal flusso R6C `apply_specialization`.
- **Decisione**: rinominato concettualmente in `training_specialization` nei doc e UI. Nessun rename effettivo nel DB (rompe troppi accessi). Si introduce campo nuovo separato `specialization_slug: str | None` per la spec di CLASSE (non training-grounds), default `None`.

Mapping campi sul doc `adventurers`:
- `class_slug`: classe base (warrior, rogue, …, warlock)
- `specialization_slug`: spec di classe (berserker_spec, assassin_spec, …) opzionale
- `specialization`: snapshot training-grounds (R6C), invariato, solo lettura
- `race_slug`, `gender`: nuovi campi Fase 3
- `class_name`: legacy capitalized display, mantenuto per back-compat

---

## 7. Stato race/gender (preview Fase 3)

| Voce | Records valorizzati |
|---|---:|
| `adventurers.race` (legacy free-string) | 84 (tutti `"human"`) |
| `adventurers.race_slug` (nuovo Fase 3) | 0 |
| `adventurers.gender` (nuovo Fase 3) | 0 |

> Fase 3 farà backfill atomico: `race_slug` casuale tra (human, elf, dwarf, halfling, orc, …TBD) e `gender` casuale (`male|female`) via `secrets.SystemRandom`, audit log per ogni record.

---

## 8. Stato stat catalog (rilevante per Stregone)

| Stat key | Esposta in `public_catalog.py` |
|---|---|
| strength | ✅ |
| agility | ✅ |
| intellect | ✅ |
| endurance | ✅ |
| faith | ✅ |
| **charisma** | ❌ NON esiste |

**Implicazione per Stregone (warlock)**: aggiungere `charisma` come 6ª stat rompe XP debuff R15 (`xp_primary_stat_policy` config + check), UI `Stats`, public catalog, e seed avventurieri. **Decisione sicura**: `warlock.primary_stat = intellect` con narrativa differenziata (Stregone = canalizzatore di patti vs Mago = studioso arcano). Eventuale `charisma` rinviato a Round dedicato post-Round-16.

---

## 9. Conflitti rilevati (Task 1.4)

| # | Conflitto | Severità | Risoluzione proposta |
|---:|---|---|---|
| 1 | Campo `specialization` (dict, 642 records) vs nuovo `specialization_slug` (string) | MEDIA | Tenere `specialization` invariato (training/respec snapshot); usare nuovo nome `specialization_slug` per classe |
| 2 | Items con `class_tags=["berserker"]` esclusivo (62 items) — restano equipaggiabili da `warrior + berserker_spec` | BASSA | Script `round160_update_items_class_tags.py` aggiunge la base class `warrior`/`rogue`/`mage` ai class_tags mantenendo il tag legacy come `specialization_unlocks` |
| 3 | `equipment/compatibility.py` blacklist hard-coded `necromancer` / `berserker` / `assassin` | BASSA | Script di migrazione **non tocca** questo file in Fase 2; verrà rivisto in Fase 5 (`equip validator extension`) per ragionare su `class_slug + specialization_slug` |
| 4 | `training/catalog.py` ha 6 specializzazioni con `eligible_classes` che includono `berserker`, `assassin`, `necromancer` | BASSA | Tradotto in compat-list: dopo migrazione, gli avventurieri eredi (`warrior` + `berserker_spec`) restano eleggibili perché la check del catalog viene estesa a `specialization_slug` matching in Fase 5 |
| 5 | Achievement con trigger basato su `class_slug` deprecato | NULLA | 0 occorrenze testuali. Solo `specialista-paladin` referenzia "Paladino" che resta base class |
| 6 | Item legacy `warlocks-grimoire` (`seed_data.py:457`) | NULLA | Item esistente coerente col nuovo lore Stregone (Warlock) — nessuna azione necessaria |
| 7 | Test `backend_round15_phase2_test.py:78,96` cita `berserker` come item recommended_classes | NULLA | Tag legacy preservato, test resta verde |

---

## 10. Decisione Stregone (warlock) — definizione completa

| Campo | Valore |
|---|---|
| slug | `warlock` |
| display_name_it | `Stregone` |
| primary_stat | `intellect` (motivazione: charisma non esiste, evitiamo cambio 5→6 stat) |
| secondary_stats | `["faith", "agility"]` |
| role | `DPS` |
| secondary_role | `Caster` |
| is_active | `true` |
| is_base_class | `true` |
| allowed_weapon_tags | `["dagger", "staff", "tome"]` |
| allowed_armor_tags | `["robe", "light"]` |
| xp_primary_stat_policy | identica alle altre 9 base (schema_v2) |
| description_it | "Lo Stregone stringe patti con entità del Vuoto o delle Stelle. Sacrifica la chiarezza arcana del Mago per ricevere potere oscuro: scaglia maledizioni, debilita i nemici e canalizza l'energia del patto stretto. Diversamente dal Mago studioso, lo Stregone è un canalizzatore: la magia non gli appartiene, gli è prestata." |

### 3 specializzazioni iniziali
| spec slug | display_name_it | descrizione lore breve |
|---|---|---|
| `demon_pact_spec` | Patto Infernale | DPS sostenuto da maledizioni di fuoco e sangue |
| `void_pact_spec` | Patto del Vuoto | DoT/debuffer, drena vita e abilità |
| `stellar_pact_spec` | Patto Stellare | Burst caster con cure d'urto al gruppo |

---

## 11. Verdict audit

- Migrazione **fattibile** in modo non-distruttivo (additiva su items, deprecate-flag su classi, rinaming logico su campo training-spec).
- Conflitti tutti risolvibili senza modificare logica gameplay R15.
- Stregone introducibile come 10ª base class senza toccare lo stat catalog (5 stat).
- 0 reference achievement testuali a classi deprecate.
- Test suite R12-R15 invariata.

**Audit chiuso: SI** — passare a Fase 2 esecuzione dopo validazione tester.
