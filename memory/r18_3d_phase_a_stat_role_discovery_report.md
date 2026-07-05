# R18.3d — Fase A · Stat/Role Discovery Report (READ-ONLY)

**Round**: `R18.3d` (Stat/Role Mapping Registry)
**Fase**: **A — Discovery / Analisi statica read-only**
**Data**: 2026-07-05T16:40:00Z UTC
**Autore**: e1_dev (su GO PM)
**Stato**: 📋 **REPORT COMPLETO — attende revisione PM**

**Vincoli LOCKED rispettati**:
- ✅ Nessuna implementazione applicata
- ✅ Nessun DB write (audit_log baseline: 11896 → post-Fase A: 11896, invariato)
- ✅ Nessuna schema migration
- ✅ Nessuna modifica agli 8 sigilli R18.Reset.1b
- ✅ Nessuna route/endpoint nuovo
- ✅ Nessuna modifica frontend player-facing
- ✅ Nessuna modifica class catalog / adventurers

---

## Sezione 1 — Executive Summary

**Cosa è stato trovato (high-level)**:

1. **Catalog attuale ha 18 classi** in `adventurer_classes` (**NON 27** come indicato nel brief PM), di cui:
   - **11 safe/playable-ready** con `primary_stat` + `secondary_stats` + `base_*` completi (allineate al reset R18.Reset.1b.v1_3)
   - **2 canoniche "hidden"** (`cacciatore_di_mostri`, `cacciatore_del_vuoto`) con `role="TBD"`, senza `primary_stat`, `is_playable=False`, `migration_target_only=True`
   - **5 legacy/inactive/test** (`assassin`, `berserker`, `necromancer`, `recruit_unassigned`, `test-class-5e0064`)

2. **Zero uso runtime dei termini 6-stat legacy** (`dexterity`, `constitution`, `intelligence`, `wisdom`, `charisma`) — questi appaiono SOLO in:
   - Player-facing IT guide (`frontend/src/pages/guide/ClassesAndStatsSection.jsx`) come naming IT flavor (Forza/Destrezza/Costituzione/Intelletto/Fede)
   - Design docs / script comment
   - Un singolo `affected_stat="wisdom"` in `backend_phase4_test.py:195` (test data legacy, non runtime)
   - Il DB **NON contiene** field a nome 6-stat legacy sui documenti runtime.

3. **VALID_ROLES runtime** = `("Tank", "DPS", "Healer")` (`backend/app/admin/services.py:19`). Drift storico: `bard.role="Support"` nel DB non allineato al set VALID_ROLES; è precedente a R18.Reset.1b e non-blocking (bard non fa parte delle 11 safe passate al reset).

4. **Player-facing IT guide (`ClassesAndStatsSection.jsx`)** contiene già mapping IT→5-stat runtime hard-coded per **12 classi** in italiano ("Destrezza", "Costituzione", "Fede") ma i valori runtime sotto sono 5-stat live. Il mapping player-facing è **coerente col design 6→5 PM** (Destrezza→agility, Costituzione→endurance) MA è statico nel codice React, non alimentato da un registry.

5. **Divergenza tra design PM ipotizzato (brief R18.3d) e stato live per Paladin**:
   - Brief ipotizza: `paladin` → primary=strength, secondary=[endurance, faith]
   - DB live (post-R18.Reset.1b.v1_3): `paladin` → **primary=faith**, secondary=[strength, endurance]
   - Fonte di truth attuale: `round15_seed_class_identity.py:71` (script sealed R15). Priorità catalog live > brief.

---

## Sezione 2 — Codebase Usage Map

Tabella (token stat/role → file:line → kind → contesto).

### 2.1 · Runtime canonical 5-stat (`strength|agility|intellect|endurance|faith`)

| Token | File:line | Kind | Contesto |
|:---|:---|:---|:---|
| `strength/agility/intellect/endurance/faith` | `backend/app/admin/services.py:20` | definition | `VALID_AFFECTED_STAT` tuple |
| `strength/…/faith` | `backend/app/expeditions/formulas.py:98-102, 124-128` | runtime-combat | Calcolo `compute_team_power` per membro |
| `strength_bonus/…/faith_bonus` | `backend/app/equipment/auto_equip.py:112-113, 139-141` | runtime-equip | `_stat_delta` + `_format_stat_delta` (auto-equip fitness) |
| `base_strength/…/base_faith` | `backend/app/seeds/seed_data.py:16-62` | seed | Base stats catalog per 12 classi (seed originale) |
| `base_strength/…/base_faith` | `backend/app/seeds/seed_runner.py:181-185` | seed | Loader delle base stats verso adventurer_classes |
| `base_strength` | `backend/app/scripts/round18_reset1b_apply_v1_3.py` | sealed-script | Applica base_* da catalog → adventurers (post-reset) |
| `base_strength` | `backend/app/scripts/round183a2_recruitment_filter_hotfix.py:12, 57, 61, 111` | script-hotfix | Recruitment KeyError previous fix + hidden-class guard |
| `strength_bonus/…/faith_bonus` | `backend/app/admin/services.py:56-57, 66-68` | admin-crud | Item bonus fields |
| `primary_stat` | `backend/app/expeditions/xp_modifier.py:59, 101, 107, 122, 145` | runtime-xp | XP modifier basato su primary_stat vs level (Round 15+) |
| `secondary_stats` | `backend/app/scripts/round15_seed_class_identity.py:49, 72, 94, 114, 134, 154, 174, 196, 215, 236, 255, 276` | sealed-seed | Seed R15 per 12 classi |
| `primary_stat/secondary_stats` | `backend/app/equipment/auto_equip.py:80, 149, 151-152` | runtime-equip | Loader classe → weighting fitness |
| `xp_primary_stat_policy` | `backend/app/expeditions/xp_modifier.py:96` | runtime-xp | Policy override optional |

### 2.2 · Role system (`Tank/DPS/Healer`, `VALID_ROLES`, `role_tags`, `role_display`, `class_role_tags`)

| Token | File:line | Kind | Contesto |
|:---|:---|:---|:---|
| `VALID_ROLES` | `backend/app/admin/services.py:19` | definition | Tuple canonica runtime |
| `VALID_ROLES` | `backend/app/admin/routes.py:19, 70, 109` | runtime-admin | Validation endpoint admin (Tank/DPS/Healer only) |
| `"Tank"/"DPS"/"Healer"` | `backend/app/expeditions/formulas.py:134-140` | runtime-combat | Bonus role composition (+5 each, +10 all-three) |
| `"Tank"/"DPS"/"Healer"` | `backend/app/pvp/simulator.py:21, 51, 84-94` | runtime-pvp | `ROLE_BONUS` + tie-break PvP |
| `"Tank"/"DPS"/"Healer"` | `backend/app/expeditions/report_builder.py:56-60, 299-311` | runtime-narrative | Report IT + display class per role |
| `role_snapshot` | `backend/tests/backend_round1611_raid_recovery_test.py:90`, `backend/app/expeditions/report_builder.py:311` | runtime-snapshot | Snapshot role al raid/expedition |
| `class_role` | `backend/app/expeditions/formulas.py:131` + molti frontend | runtime-frontend | Snapshot role sul doc adventurer |
| `role_tags` | `backend/app/scripts/round15_seed_class_identity.py:53-280` | sealed-seed | 12 classi, es. `["tank","frontline"]`, `["dps_melee","stealth"]` |
| `role_tags` | `backend/app/adventurers/services.py:161` | runtime-frontend | Espone `role_tags` per adventurers list |
| `role_tags` | `backend/app/scripts/round15_seed_item_tags.py:226-228` | sealed-seed | Deriva role_tags da stat_tags per items |
| `role_placeholder` | `backend/app/scripts/round18_reset1a_dry_run.py:504, 515` | script-audit | Filter adventurers non-placeholder |
| `role_display` | **NESSUN uso runtime nel codice** | — | Solo menzionato nel brief R18.3d, mai definito nel codebase |
| `class_role_tags` | **NESSUN uso runtime nel codice** | — | Solo menzionato nel brief R18.3d, mai definito nel codebase |
| `secondary_role` | Presente come field DB su alcune classi (union keys) | schema | Field opzionale, non usato dal runtime attivo |
| `role_pm_decision_pending` | Presente come field DB | schema | Flag PM decision (cacciatori) |

### 2.3 · Frontend UI role/stat usage

| File | Uso | Note |
|:---|:---|:---|
| `frontend/src/components/RoleMarker.jsx:11-18` | ASCII markers Tank/[T], Healer/[+], DPS/[D], Ranger/[R], Mage/[M], Support/[S] | Player-facing, decorative-only |
| `frontend/src/pages/Adventurers.jsx:390, 494` | Legge `a.class_role` | Player-facing list |
| `frontend/src/pages/Recruitment.jsx:75` | `<RoleBadge role={candidate.class_role} />` | Player-facing recruitment |
| `frontend/src/pages/RosterManage.jsx:76, 99, 358` | Filtra roster per `class_role` | Player-facing |
| `frontend/src/pages/RaidBuilder.jsx:190, 210, 253, 679` | Filtra/ordina/mostra `class_role` | Player-facing raid |
| `frontend/src/pages/SquadBuilder.jsx:54, 83, 179` | Marker + filter role | Player-facing squad |
| `frontend/src/pages/ExpeditionNew.jsx:49, 339, 517` | Composition role counter | Player-facing expedition |
| `frontend/src/pages/guide/ClassesAndStatsSection.jsx:113-222, 297, 301` | Hard-coded IT stats mapping per 12 classi (`primary_stat: "Forza"`, `secondary_stats: ["Costituzione"]`) | Player-facing STATIC (non da API) |
| `frontend/src/components/AdventurerDetailModal.jsx:168`, `AdventurerRenameModal.jsx:83`, `InventoryEquipModal.jsx:166` | Mostra `class_role` in modali | Player-facing |

### 2.4 · 6-stat legacy tokens (`dexterity/constitution/intelligence/wisdom/charisma`)

| Token | File:line | Kind | Impatto |
|:---|:---|:---|:---|
| `wisdom` | `backend/tests/backend_phase4_test.py:195` | test-data-legacy | Test data `"affected_stat": "wisdom"` — unico occorrenza, verosimilmente obsoleto vs `VALID_AFFECTED_STAT` |
| `constitution` | `backend/app/seeds/seed_traits_it.py:92`, `frontend/src/i18n/lang/en.json:848`, `backend/app/seeds/seed_data.py:73` | flavor-text | Descrizione trait "Frail" (flavor) |
| `charisma` | `backend/app/scripts/round160_seed_classes_v2.py:21` (commento), `round183b_class_design_matrix_gen.py:173` (design note) | design-doc | Solo commenti + matrice design |
| `dexterity/intelligence` | **NESSUNA occorrenza** in codice | — | Puliti |

**Conclusione**: nessun uso runtime del 6-stat naming — il player-facing IT usa `Destrezza`/`Costituzione`/`Fede` come **etichette localizzate** ma il runtime backend usa `agility`/`endurance`/`faith` verbatim.

---

## Sezione 3 — DB Schema Snapshot (read-only)

### 3.1 · Collection `adventurer_classes` (18 documenti)

**Union completa dei field** (46 chiavi osservate):
```
_id, allowed_armor_tags, allowed_weapon_tags,
base_agility, base_endurance, base_faith, base_intellect, base_strength,
created_at, deprecated_at, description, description_it,
display_name_en, display_name_it, drops_items,
guide_description_en, guide_description_it,
id, is_active, is_base_class, is_canonical, is_playable,
is_specialization, is_talent_tree_eligible, is_test,
migration_target_only, name, name_en, pm_decision,
preferred_item_tags, primary_stat, role, role_placeholder,
role_pm_decision_pending, role_tags, round_intro,
secondary_role, secondary_stats,
seed_source, slug, source_round, source_slug_bridge,
successor_slug, successor_specialization_slug,
updated_at, xp_primary_stat_policy
```

**Sample (`warrior`)**:
```json
{
  "slug": "warrior", "name": "Warrior", "role": "Tank",
  "base_strength": 8, "base_agility": 4, "base_intellect": 2,
  "base_endurance": 9, "base_faith": 2,
  "display_name_it": "Guerriero",
  "is_active": true,
  "allowed_armor_tags": ["heavy","shield","medium"],
  "allowed_weapon_tags": ["sword","axe","mace","two_handed"],
  "guide_description_it": "Il Guerriero è la spina dorsale…"
}
```

### 3.2 · Collection `adventurers` — snapshot post-reset v1.3

**Union field (200 sample)**:
```
_id, adventurer_class_id, agility, class_name, class_role, class_slug,
created_at, endurance, experience, faith, grade, guild_id,
hp_current, hp_max, id, intellect, is_available, is_retired,
is_starter, level, morale, name, phase13_unbaked,
r18_reset1b_hotfix_v1_2, r18_reset1b_hotfix_v1_3,
r18_reset1b_hotfix_v1_3_apply_id, r18_reset1b_hotfix_v1_3_at,
r18_reset1b_seed_source, r18_reset1b_starter, r18_reset1b_stat_source,
rarity, rename_count, stamina, status, strength, traits, updated_at, xp
```

**Sample (adventurer starter Warrior post-v1.3)**:
```json
{
  "class_slug": "warrior", "class_name": "Warrior", "class_role": "Tank",
  "adventurer_class_id": "a0ea32ac-…",
  "strength": 8, "agility": 4, "intellect": 2, "endurance": 9, "faith": 2,
  "level": 1, "status": "idle",
  "r18_reset1b_stat_source": "adventurer_classes.base_*_catalog_lookup"
}
```

**Total counts**:
- `adventurers` totale live: **3373**
- `adventurers` con marker `r18_reset1b_hotfix_v1_2=True`: **3360** (starter roster post-reset)
- `adventurers_r18_archive`: soft-archive storici (non contati qui, read-only skip)

### 3.3 · Altre collezioni rilevanti (113 totali)

Collezioni con potenziale accoppiamento role/stat (non ispezionate in dettaglio in Fase A):
- `items`, `inventory_items`, `equipped_items` — hanno `*_bonus` fields (già canonical 5-stat)
- `guild_specialization_catalog`, `guild_specialization_choice` — usa `preferred_role` (`Tank`, `DPS`, `Healer`)
- `season_participations`, `pvp_battles`, `pvp_matches` — potenziale `role_snapshot`

---

## Sezione 4 — Runtime-critical fields

Ordinati per severity (HIGH → LOW):

| Field | Locazione runtime | Impatto se modificato |
|:---|:---|:---|
| `adventurer_classes.primary_stat` | `expeditions/xp_modifier.py` (XP mod), `equipment/auto_equip.py` (fitness) | 🔴 **HIGH** — XP gain % + auto-equip result cambiano immediatamente per 3360 adventurers |
| `adventurer_classes.role` | `admin/routes.py` validation, snapshot su `class_role` degli adventurers | 🔴 **HIGH** — bloccato da VALID_ROLES; snapshot su adventurers è "denormalizzato" e non si aggiorna retroattivamente |
| `adventurer_classes.secondary_stats` | `equipment/auto_equip.py._compute_fitness` (SECONDARY_WEIGHT=1.5) | 🟠 **MEDIUM** — auto-equip fitness cambia; nessuna crash, ma output differente |
| `adventurers.class_role` | `expeditions/formulas.py.compute_team_power` (role bonus +5) | 🟠 **MEDIUM** — team power cambia, expedition success chance calcolabile diversa |
| `adventurers.strength/agility/intellect/endurance/faith` | `expeditions/formulas.py.compute_team_power` fallback | 🟠 **MEDIUM** — se `total_power_snapshot` è None, questi sono usati |
| `adventurer_classes.role_tags` | `adventurers/services.py:161` (espone al FE) + `round15_seed_item_tags.py` derivation | 🟡 **LOW** — informativo/derivato |
| `adventurer_classes.xp_primary_stat_policy` | `expeditions/xp_modifier.py:96` (override optional) | 🟡 **LOW** — se assente usa default, comportamento invariato |
| `adventurers.class_slug` | `equipment/auto_equip._resolve_class_slug` + espeditions | 🔴 **HIGH** — chiave di lookup verso catalog; corrompendola si perde tutto il weighting |

---

## Sezione 5 — Combat/Auto-Equip Dependency Graph

```
[adventurer_classes.primary_stat] ─→ [equipment/auto_equip._load_class_meta] ─→ [_compute_fitness (PRIMARY_WEIGHT=3.0)]
                                 └→ [expeditions/xp_modifier.expected_primary_stat] ─→ [compute_xp_multiplier]

[adventurer_classes.secondary_stats] ─→ [equipment/auto_equip._compute_fitness (SECONDARY_WEIGHT=1.5)]

[adventurer_classes.role] ─→ [admin/routes validation]
                          └→ [snapshot al momento della creazione adventurer → adventurers.class_role]

[adventurers.class_role] ─→ [expeditions/formulas.compute_team_power (+5 per role)]
                         └→ [pvp/simulator.ROLE_BONUS (Tank=0.05, Healer=0.05, DPS=0.03)]
                         └→ [expeditions/report_builder — narrative IT/EN]

[adventurers.{strength,agility,intellect,endurance,faith}] ─→ [expeditions/formulas.compute_team_power fallback]
                                                          └→ [items.{stat}_bonus + equipped_items]

[adventurer_classes.role_tags] ─→ [adventurers/services expose to FE]
                              └→ [equipment/compatibility.check_equip_compatibility] (round15_seed_item_tags derivation chain)
```

**Nota**: `total_power_snapshot` (post-Phase 6) è la primary path; le stat root sono fallback. Il break di stat root ha impatto LIMITATO nel caso "happy path" ma la corruption dei `primary_stat`/`role` sul catalog impatta TUTTI i futuri lookup.

---

## Sezione 6 — API / Admin / Frontend Dependencies

### Endpoint pubblici (player-facing)

| Endpoint | Espone stat/role | Impatto |
|:---|:---|:---|
| `GET /api/adventurers` | `strength, agility, intellect, endurance, faith, class_role, class_slug, class_name, role_tags` | HIGH — tutti i pageviewer di roster/dashboard |
| `GET /api/recruitment/candidates` | Come sopra + `class_slug` | MEDIUM |
| `POST /api/expeditions` | Team composition role check | HIGH |
| `POST /api/adventurers/{id}/auto-equip` | Legge `primary_stat` / `secondary_stats` dal catalog | HIGH |
| `GET /api/dungeons` | Non tocca stat, ma `recommended_power` interagisce con team_power | LOW indiretto |
| `GET /api/guild-specialization/mine` | `preferred_role` (Tank/DPS/Healer) | LOW |

### Endpoint admin

| Endpoint | Uso | Impatto |
|:---|:---|:---|
| `POST /api/admin/classes` (via `admin/routes.py`) | Validation su `VALID_ROLES` | HIGH — se modifichiamo VALID_ROLES, admin bloccherà classi con role non-canonico |
| `POST /api/admin/traits` (via `admin/routes.py`) | `VALID_AFFECTED_STAT` = strength/agility/intellect/endurance/faith/xp_gain | MEDIUM |
| `POST /api/admin/items` | 5 field `*_bonus` int | MEDIUM |

### Frontend components player-facing

**Consumatori diretti di `class_role` (11 componenti/pages)**: Adventurers, Recruitment, RosterManage, RaidBuilder, SquadBuilder, ExpeditionNew, AdventurerDetailModal, AdventurerRenameModal, InventoryEquipModal, ClassesAndStatsSection (guide), AdventurerEquipment.

**Componente decorativo `RoleMarker.jsx`**: gestisce anche `Support`, `Ranger`, `Mage` come marker set (superset di VALID_ROLES runtime, per compatibilità legacy display).

**Guide statica IT (`ClassesAndStatsSection.jsx`)**: espone HARD-CODED per 12 classi in italiano:
- primary_stat IT: Forza, Destrezza, Intelletto, Fede
- secondary_stats IT: Costituzione, Forza, Destrezza, Fede, Intelletto
- **Nota**: qui c'è già un mapping IT→5-stat DE FACTO (Destrezza→agility, Costituzione→endurance), ma è statico e non alimentato da un registry.

---

## Sezione 7 — Class Catalog Field Inventory (18 classi, memory-only registry candidato)

Tabella completa (⭐ = priority=critical per il PM). Colonne: slug, IT-name, role, primary_stat, secondary_stats, base_*, is_active, is_playable, is_canonical, migration_target_only, priority.

| slug | display_name_it | role | primary_stat | secondary_stats | base(S/A/I/E/F) | is_active | is_playable | is_canonical | migration_target_only | 🏷 priority |
|:---|:---|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **alchemist** | (Alchemist) | DPS | intellect | agility, endurance | 3/6/9/6/4 | ✓ | — | — | — | normal |
| **assassin** | (Assassin) | DPS | agility | strength | 6/10/4/3/1 | ✗ | — | — | — | legacy-inactive |
| **bard** | Bardo (Bard) | **Support** ⚠ | intellect | agility, faith | 3/6/7/4/5 | ✓ | — | — | — | normal (role drift) |
| **berserker** | (Berserker) | DPS | strength | endurance | 10/5/1/6/1 | ✗ | — | — | — | legacy-inactive |
| **cacciatore_del_vuoto** ⭐ | Cacciatore del Vuoto | **TBD** | — | — | — | ✓ | ✗ | ✓ | ✓ | **critical (hidden)** |
| **cacciatore_di_mostri** ⭐ | Cacciatore di Mostri | **TBD** | — | — | — | ✓ | ✗ | ✓ | ✓ | **critical (hidden)** |
| **druid** | (Druid) | Healer | faith | intellect | 3/5/7/5/7 | ✓ | — | — | — | normal |
| **mage** | (Mage) | DPS | intellect | endurance | 2/4/10/3/3 | ✓ | — | — | — | normal |
| **monk** | (Monk) | DPS | agility | endurance, faith | 5/9/3/6/5 | ✓ | — | — | — | normal |
| **necromancer** | (Necromancer) | DPS | intellect | agility | 2/4/10/4/1 | ✗ | — | — | — | legacy-inactive |
| **paladin** ⭐ | Paladino (Paladin) | Tank | **faith** ⚠ | strength, endurance | 7/3/2/7/6 | ✓ | — | — | — | **critical (design divergence)** |
| **priest** | (Priest) | Healer | faith | intellect | 2/3/6/4/10 | ✓ | — | — | — | normal |
| **ranger** | (Ranger) | DPS | agility | endurance | 5/8/4/5/3 | ✓ | — | — | — | normal |
| **recruit_unassigned** | — | — | — | — | — | ✗ | ✗ | — | — | placeholder |
| **rogue** ⭐ | Ladro (Rogue) | DPS | agility | strength | 5/9/3/4/2 | ✓ | — | — | — | **critical (fresh-start)** |
| **test-class-5e0064** | Updated Test Class | Tank | — | — | 10/5/4/9/3 | ✗ | — | — | — | test-doc |
| **warlock** | (Warlock) | DPS | intellect | faith, agility | 4/6/10/6/6 | ✓ | — | — | — | normal |
| **warrior** ⭐ | Guerriero (Warrior) | Tank | strength | endurance | 8/4/2/9/2 | ✓ | — | — | — | **critical (fresh-start)** |

### Registry candidato per stat mapping IT ↔ 5-stat live (memory-only)

```json
[
  {"design_stat_it": "Forza",        "design_stat_en": "strength",     "live_stat": "strength",  "notes": "Mapping identity 6→5"},
  {"design_stat_it": "Destrezza",    "design_stat_en": "dexterity",    "live_stat": "agility",   "notes": "Design 6-stat aveva dexterity separata; PM 6→5: dexterity → agility"},
  {"design_stat_it": "Costituzione", "design_stat_en": "constitution", "live_stat": "endurance", "notes": "Design 6-stat aveva constitution separata; PM 6→5: constitution → endurance"},
  {"design_stat_it": "Intelletto",   "design_stat_en": "intelligence", "live_stat": "intellect", "notes": "Mapping identity semantic 6→5"},
  {"design_stat_it": "Saggezza",     "design_stat_en": "wisdom",       "live_stat": "intellect", "notes": "Design 6-stat aveva wisdom separata; PM 6→5: wisdom → intellect (collisione con Intelletto — vedi Open Q#5)"},
  {"design_stat_it": "Carisma",      "design_stat_en": "charisma",     "live_stat": "faith",     "notes": "Design 6-stat aveva charisma; PM 6→5: charisma → faith. NB: nel catalog live 'faith' è già primary di Paladin/Priest/Druid — vedi Open Q#5"}
]
```

### Registry candidato per classi (memory-only, esempio safe subset)

Esempio per 3 classi critical:

```json
[
  {
    "class_slug": "paladin",
    "class_name_it": "Paladino",
    "design_primary_stat_it": "Fede",
    "design_secondary_stats_it": ["Forza", "Costituzione"],
    "mapped_primary_stat_live": "faith",
    "mapped_secondary_stats_live": ["strength", "endurance"],
    "role_atomic_candidate": "Tank",
    "role_display_it_candidate": "Paladino (Tank/Support Divino)",
    "class_role_tags_candidate": ["tank", "support", "holy"],
    "confidence": "high",
    "needs_PM_review": true,
    "PM_review_reason": "Design divergence: brief R18.3d supponeva primary=strength; catalog live (R15 sealed) è primary=faith. Confermare source-of-truth."
  },
  {
    "class_slug": "warrior",
    "class_name_it": "Guerriero",
    "design_primary_stat_it": "Forza",
    "design_secondary_stats_it": ["Costituzione"],
    "mapped_primary_stat_live": "strength",
    "mapped_secondary_stats_live": ["endurance"],
    "role_atomic_candidate": "Tank",
    "role_display_it_candidate": "Guerriero (Tank)",
    "class_role_tags_candidate": ["tank", "frontline"],
    "confidence": "high",
    "needs_PM_review": false
  },
  {
    "class_slug": "rogue",
    "class_name_it": "Ladro",
    "design_primary_stat_it": "Destrezza",
    "design_secondary_stats_it": ["Forza"],
    "mapped_primary_stat_live": "agility",
    "mapped_secondary_stats_live": ["strength"],
    "role_atomic_candidate": "DPS",
    "role_display_it_candidate": "Ladro (DPS Melee/Stealth)",
    "class_role_tags_candidate": ["dps_melee", "stealth"],
    "confidence": "high",
    "needs_PM_review": false
  }
]
```

(La versione completa per tutte le 18 classi è in `r18_3d_phase_a_stat_role_discovery_report.json` sezione `class_registry_candidate_memory_only`.)

---

## Sezione 8 — Adventurer Field Inventory Post-Reset (3-5 sample live)

Sample 1 (starter Rogue, post-v1.3):
```
class_slug=rogue, class_name=Rogue, class_role=DPS,
adventurer_class_id=48c8160d-c0e1-47b2-bb74-ac7bbf2b229d,
strength=5, agility=9, intellect=3, endurance=4, faith=2,
level=1, status=idle, xp=0, experience=0, is_available=true,
r18_reset1b_stat_source=adventurer_classes.base_*_catalog_lookup
```

Sample 2 (starter Mage):
```
class_slug=mage, class_role=DPS, strength=2, agility=4,
intellect=10, endurance=3, faith=3, level=1
```

Sample 3 (starter Warrior):
```
class_slug=warrior, class_role=Tank, strength=8, agility=4,
intellect=2, endurance=9, faith=2, level=1
```

**Schema completo adventurer post-reset** (union 200 sample): 37 field, tutti stat runtime = 5-stat canonici, `class_role` snapshot denormalizzato, marker reset `r18_reset1b_*` presenti.

**Nessun 6-stat legacy field** nei documenti adventurers.

---

## Sezione 9 — Risk Matrix

| Field | Runtime-critical? | Modifiable? | Blocker? | Note |
|:---|:---:|:---:|:---:|:---|
| `adventurer_classes.role` | Y | **BLOCKED** | ✓ PM | Snapshot su adventurers.class_role — cambio catalog non retroattivo |
| `adventurer_classes.primary_stat` | Y | **BLOCKED** | ✓ PM | XP mod + auto-equip fitness dipendono direttamente |
| `adventurer_classes.secondary_stats` | Y | **RISKY** | Consultare PM | Cambio pesa auto-equip 1.5x per secondary |
| `adventurer_classes.base_*` | Y | **BLOCKED** | ✓ PM | Reset R18.Reset.1b appena applicato — mai toccare senza rerun scripts sealed |
| `adventurer_classes.role_tags` | N (informativo) | RISKY | consultare PM | Non runtime combat, ma influenza item derivation R15 |
| `adventurer_classes.display_name_it` | N | **SAFE** | — | Append-only metadata IT-locale |
| `adventurer_classes.guide_description_it/en` | N | **SAFE** | — | Player-facing flavor |
| `adventurer_classes.xp_primary_stat_policy` | Y (opz.) | RISKY | consultare PM | Override XP calc; default sicuro |
| `adventurer_classes.is_playable/is_canonical/is_active` | Y | **BLOCKED** | ✓ PM | Governance recruitment + guard whitelist |
| `adventurer_classes.role_display_it` (nuovo) | N | **SAFE** | — | Non esiste ancora; append-only pure metadata |
| `adventurer_classes.class_role_tags` (nuovo) | N | **SAFE** | — | Non esiste ancora; append-only pure metadata |
| `adventurer_classes.notes/source_round` (nuovi) | N | **SAFE** | — | Documentale, non runtime |
| `adventurers.class_role` (denorm) | Y | **BLOCKED** | ✓ PM | Snapshot storico, mai riscrivere retroattivamente |
| `adventurers.{stat}` runtime | Y | **BLOCKED** | ✓ PM | Runtime combat |
| `VALID_ROLES` tuple (admin/services.py) | Y | **BLOCKED** | ✓ PM | Espandere = allargare la validation admin — impact esteso |

---

## Sezione 10 — Proposed Registry Shape (memory-only, NO seed, NO DB write)

**File proposto**: `/app/memory/r18_3d_stat_role_mapping_registry.json` (letto in Phase B, mai in Phase A).

### Schema top-level

```json
{
  "registry_version": "R18.3d.v1",
  "generated_at": "<ISO UTC>",
  "seal_authority": "PM Orchestrator",
  "stat_system": {
    "live_stats": ["strength", "agility", "intellect", "endurance", "faith"],
    "design_stat_mapping_6_to_5": [
      {"design_it": "Forza",        "design_en": "strength",     "live": "strength"},
      {"design_it": "Destrezza",    "design_en": "dexterity",    "live": "agility"},
      {"design_it": "Costituzione", "design_en": "constitution", "live": "endurance"},
      {"design_it": "Intelletto",   "design_en": "intelligence", "live": "intellect"},
      {"design_it": "Saggezza",     "design_en": "wisdom",       "live": "intellect"},
      {"design_it": "Carisma",      "design_en": "charisma",     "live": "faith"}
    ]
  },
  "role_system": {
    "live_roles_atomic": ["Tank", "DPS", "Healer"],
    "candidate_role_display_it": {
      "Tank":   "Difensore",
      "DPS":    "Danneggiante",
      "Healer": "Curatore"
    },
    "candidate_class_role_tags_taxonomy": [
      "tank", "frontline", "off_healer",
      "dps_melee", "dps_ranged", "dps_burst", "dps_caster",
      "healer_dedicated", "healer_aoe",
      "support", "buffer", "debuffer",
      "stealth", "scout", "summoner", "control", "self_sustain",
      "holy"
    ]
  },
  "classes": [ /* 18 doc — 11 safe + 2 hidden + 5 legacy */ ]
}
```

**Nota importante**: PROPOSTA — NON APPLICATA. In Fase A ci limitiamo a salvare la struttura nel report JSON (`r18_3d_phase_a_stat_role_discovery_report.json`), non nel registry attivo.

---

## Sezione 11 — Safe / Unsafe Fields for Future Apply

### 🟢 SAFE (append-only metadata, apply candidate in Phase B senza GO extra)

| Nuovo field | Target collection | Kind | Note |
|:---|:---|:---|:---|
| `role_display_it` | `adventurer_classes` | append pure metadata | Non runtime, solo player-facing (Guide/Modali future) |
| `class_role_tags` | `adventurer_classes` | append pure metadata | Documentale, superset di `role_tags` R15 esistente |
| `design_primary_stat_it` | `adventurer_classes` | append pure metadata | IT-label documentale |
| `design_secondary_stats_it` | `adventurer_classes` | append pure metadata | IT-label documentale |
| `stat_role_registry_source_round` | `adventurer_classes` | append pure metadata | Tracciabilità |

### 🟠 RISKY (runtime field, apply richiede GO PM + dry-run + regression)

| Field | Perché risky |
|:---|:---|
| `secondary_stats` modifica ordine/contenuto | Auto-equip fitness cambia (SECONDARY_WEIGHT 1.5x) |
| `role_tags` modifica | Item derivation R15 chain |
| `xp_primary_stat_policy` overrides | XP mod runtime |

### 🔴 BLOCKED WITHOUT PM (runtime-critical, mai in Phase B senza GO esplicito)

| Field | Perché blocked |
|:---|:---|
| `primary_stat` | XP mod + auto-equip dipendono direttamente. Cambio = rebalance immediato dei 3360 adventurers live. |
| `role` | VALID_ROLES admin check + snapshot su adventurers.class_role. Non retroattivo. |
| `base_strength/…/base_faith` | R18.Reset.1b appena applicato con questi valori exact. Modifica senza rerun scripts sealed = drift. |
| `VALID_ROLES` tuple in code | Cambia semantica admin + validation catena — impatto trasversale |
| `is_playable/is_canonical/is_active` | Governance recruitment guard whitelist |

---

## Sezione 12 — Open Questions PM (10 domande, minimo 7 richiesti)

### Q1 · Quali metadata append-only possiamo aggiungere al catalog senza toccare runtime?

**Proposta**: `role_display_it`, `class_role_tags`, `design_primary_stat_it`, `design_secondary_stats_it`, `stat_role_registry_source_round`.
**Runtime touch**: ZERO.
**Chiedo PM**: ok ad append di questi 5 field su `adventurer_classes` in Phase B **staged apply**?

### Q2 · `role_display_it` deve essere player-facing subito o admin-only?

Il brief menziona `role_display` come "candidato futuro". Se player-facing subito, tocca almeno:
- `frontend/src/pages/Adventurers.jsx`
- `frontend/src/components/AdventurerDetailModal.jsx`
- `frontend/src/components/InventoryEquipModal.jsx`
- (Potenzialmente) `RoleMarker.jsx` per label extended

**Chiedo PM**: player-facing dal Phase B (frontend refactor incluso) **o** solo admin-panel/API introspection?

### Q3 · `class_role_tags` devono essere usati solo come guida (documentale) o anche per matchmaking futuro?

Il seed R15 (`round15_seed_class_identity.py`) ha già `role_tags` con taxonomy 15+ tag. Se `class_role_tags` è un **superset consolidato** letto dal registry, va sincronizzato con `role_tags` esistente.

**Chiedo PM**: `class_role_tags` = alias di `role_tags` (unificazione) **o** field separato specifico (doppia sorgente)?

### Q4 · `mapped_primary_stat_live` deve restare memory-only o andare nel catalog?

Attualmente è ridondante con `primary_stat` già presente sul catalog. Nel registry JSON serve per tracciabilità 6→5 mapping.

**Chiedo PM**: registry JSON è **source-of-truth** (backend legge da lì) **oppure** `adventurer_classes` resta source-of-truth (registry è documentale)?

### Q5 · Mapping `Saggezza → intellect` e `Carisma → faith` — definitivo?

Sono le 2 collisioni del mapping 6→5:
- Saggezza + Intelletto → entrambi `intellect` runtime
- Carisma → `faith` (ma nel catalog live "faith" è primary di Paladin/Priest/Druid → il player-facing "Carisma" non appare mai come primary_stat visible)

**Chiedo PM**: mapping OK per **tutte** le 11 classi safe **o** ci sono classi specifiche (es. Druido/Sciamano futuri) dove "Saggezza"→`intellect` è ambiguo semanticamente?

### Q6 · Quando riaprire le 2 classi hidden al recruitment?

`cacciatore_di_mostri` e `cacciatore_del_vuoto` sono `is_playable=False`, `migration_target_only=True`, senza `primary_stat`, `role=TBD`. Il registry R18.3d è l'occasione naturale per definirle.

**Chiedo PM**: (a) tenerle hidden ancora, (b) definire primary_stat + role in Phase C e riaprirle al recruitment, oppure (c) round separato dedicato?

### Q7 · R18.4 (item class-bound) può partire senza `role_display` player-facing?

Se R18.4 è la prossima priorità dopo R18.3d, dipende dal registry?

**Chiedo PM**: R18.3d ships in modalità "**documental-only** (metadata append)" per non bloccare R18.4? La versione con `role_display` player-facing può slittare a un R18.3d.v2?

### Q8 · Drift `bard.role="Support"` — sanare in Phase B?

`bard.role="Support"` non è in `VALID_ROLES=(Tank,DPS,Healer)`. Se lasciato così, resta un drift silente. Storicamente bard è caduto fuori dalle 11 safe passate al reset.

**Chiedo PM**: (a) sanare in Phase B (portare bard.role="Healer" o "DPS"), (b) espandere VALID_ROLES ad includere "Support" (impact esteso), (c) lasciare drift e documentare.

### Q9 · Divergenza design Paladin — brief vs catalog live

Brief R18.3d ipotizzava `paladin.primary_stat=strength`; catalog live è `paladin.primary_stat=faith`. Fonte di truth attuale = seed R15 sealed.

**Chiedo PM**: (a) accettare live `faith` come definitivo, (b) rivedere il brief e cambiare il catalog (BLOCKED — richiede unseal R15), (c) documentare Paladin come "tank hybrid" nel registry `class_role_tags=[tank, support, holy]`.

### Q10 · Le 27 classi "canoniche" del brief vs 18 in DB — coerenza design docs

Il brief menziona 27 classi canoniche. Il DB ne ha 18. Presumo che le rimanenti 9 siano nel design roadmap ma non seedate. Sono elencate nel roadmap docs?

**Chiedo PM**: fornire la lista delle 27 canoniche (o confermare che 18 è il numero effettivo del "canonical set attuale"). Se ci sono 9 classi solo-design (non-seed), vanno registrate nel registry come `design_only=true`?

---

## Sezione 13 — Recommendation for Phase B

### Raccomandazione tecnica (mia analisi, PM decide)

**Approccio consigliato: "DESIGN-FIRST STAGED APPLY"**

1. **Sotto-fase B0 (2h, no code)**: PM review delle 10 Open Questions sopra. Convergenza su:
   - Ambito Phase B (documental-only vs partial player-facing)
   - Q9 Paladin design (accettare `faith` primary o unseal R15)
   - Q10 lista 27 canoniche completa

2. **Sotto-fase B1 (staged, no DB write)**: draft del registry JSON completo `/app/memory/r18_3d_stat_role_mapping_registry.json` con **tutte le 18 classi** (o 27 se PM include design-only). Include:
   - Stat mapping 6→5 (LOCKED da PM)
   - Role atomic per ogni classe (LOCKED)
   - Metadati SAFE append-candidate
   - Flags `needs_PM_review` per divergenze
   - SHA256 self-hash per contract lock

3. **Sotto-fase B2 (loader read-only)**: creare modulo Python `app/core/stat_role_registry.py`:
   - **Solo LOAD**, no mutation
   - Validation fail-fast a startup (schema check)
   - Espone helper `get_stat_role_mapping(class_slug)` per consumo runtime FUTURO (non wire ancora nei consumer)

4. **Sotto-fase B3 (append-only DB, opzionale, richiede GO PM esplicito)**: se PM autorizza (Q1 + Q2), aggiungere i 5 field SAFE alle 18 classi via script sealed `round18_3d_apply_metadata.py`:
   - Solo append: `role_display_it`, `class_role_tags`, `design_primary_stat_it`, `design_secondary_stats_it`, `stat_role_registry_source_round`
   - **NO tocco a**: primary_stat, secondary_stats, role, base_*
   - Dry-run gate + double flag `--i-understand-this-will-write-metadata`

5. **Sotto-fase B4 (test suite)**: 
   - Registry schema contract test
   - Loader fail-fast test
   - Snapshot regression: pre/post metadata (verificare che nessun field runtime sia toccato)

6. **Sotto-fase B5 (SEAL)**: sealed script + registry JSON + test suite. Update PRD + closure report R18.3d.

### Motivazione del "design-first"

- **Sicurezza**: 3360 adventurers live post-reset — qualsiasi modifica runtime = potenziale drift + necessità di rerun R18.Reset scripts sealed.
- **Reversibilità**: append-only è naturalmente reversibile ($unset), mentre mutation su primary_stat/role non lo è (snapshot su class_role degli adventurers non si aggiorna).
- **Modularità**: Phase B1 può girare in isolation senza impatto live. Se PM decide di non procedere, il registry JSON resta materiale documentale.

### Alternativa "runtime-first" (SCONSIGLIATA per Phase B)

Se PM vuole subito consumare il registry dal runtime (auto_equip, xp_modifier), servirebbe:
- Wire di `app/core/stat_role_registry.py` in `_load_class_meta` di auto_equip
- Wire in `expected_primary_stat` di xp_modifier
- Regression massiva su 3360 adventurers × 27+ dungeon test
- Rischio drift alto se registry JSON e catalog divergono anche solo per un byte

Non raccomandato in Phase B — meglio un R18.3d.v2 dedicato.

---

## Self-Check 10 Punti (Fase A)

| # | Check | Esito |
|:---:|:---|:---:|
| 1 | Report MD creato | ✅ `/app/memory/r18_3d_phase_a_stat_role_discovery_report.md` |
| 2 | Report JSON creato e parsabile | ✅ `/app/memory/r18_3d_phase_a_stat_role_discovery_report.json` (parsing esplicito sotto) |
| 3 | Zero DB write (audit_log baseline invariato) | ✅ 11896 → 11896 (verificato a fine Fase A) |
| 4 | Zero schema migration | ✅ nessun `update_many/insert_many/create_index` eseguito |
| 5 | Zero route nuova | ✅ nessun file `.py` in `backend/app/*/routes.py` modificato |
| 6 | Zero UI player-facing modificata | ✅ nessun file `frontend/src/**/*.jsx` modificato |
| 7 | Zero modifica sealed scripts Reset | ✅ pytest `test_t01_sealed_scripts_untouched` PASS a fine Fase A |
| 8 | Discovery copre backend/frontend/tests/memory | ✅ grep esaustivo sui 4 domini + DB dump read-only |
| 9 | Runtime-critical usage documentato | ✅ Sezioni 4-5 (dependency graph + risk matrix) |
| 10 | Recommendation Phase B presente | ✅ Sezione 13 (staged apply design-first) |

---

**FASE A R18.3D CHIUSA — attende revisione PM e GO/NO-GO per Fase B.**
