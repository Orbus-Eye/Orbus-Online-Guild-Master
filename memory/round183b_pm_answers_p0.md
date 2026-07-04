# R18.3b — PM Answers P0 · SEALED (as design intent, not live DB values)

⚠️ **STATUS**: PM design intent registrato. **Enum conflict con backend live impedisce applicazione diretta al catalog `adventurer_classes`**.

- **Schema live 5-stat** (`strength`, `agility`, `intellect`, `endurance`, `faith`) vs **PM 6-stat** (`charisma`, `strength`, `constitution`, `dexterity`, `intelligence`, `wisdom`)
- **Atomic role enum live** (`VALID_ROLES = ("Tank", "DPS", "Healer")`) vs **PM composite roles** (`"Healer/Tank hybrid"`, `"Martial DPS/Tank"`, `"DPS/Utility"`, `"DPS Caster"`)

**Reconciliation deferrita a R18.3b.1** (mini-round dedicato post-R18.3c).

**Data sealing**: 2026-07-04T20:40Z · **Applied to live DB in R18.3c**: **NO** (mode `adventurer_class_slug_only`, catalog immutable).

---

## P0-1 · Paladino · design intent

- `role_intent`: `"Healer/Tank hybrid"`
- `primary_stat_intent`: `"charisma"`
- `secondary_stats_intent`: `["strength", "constitution"]`
- **Identità**: tank sacro, cura/protezione, armatura pesante, supporto divino, danno radioso secondario. Assorbe continuità gameplay `priest` legacy. **NO** classe `Priest` separata.
- **Live DB values (invariati R18.3c)**: `role="Tank"`, `primary_stat="faith"`, `secondary_stats=["strength", "endurance"]`

## P0-2 · Cacciatore di Mostri · design intent

- `role_intent`: `"DPS/Utility"`
- `primary_stat_intent`: `"dexterity"`
- `secondary_stats_intent`: `["wisdom", "constitution"]`
- **Identità**: tracker, arciere, trappole, debolezze mostri, utility esplorazione, DPS fisico/ranged. Continuità `ranger` legacy, non solo arciere puro.
- **Live DB values (invariati R18.3c)**: `role="TBD"` (R18.3a.1 placeholder), `primary_stat=None`, `secondary_stats=None`

## P0-3 · Differenziazione Guerriero/Paladino/Cavaliere della Morte · design intent

- **Opzione scelta**: **A** (ruoli distinti, no dual-primary)
- `Guerriero`: martial fisico puro (`role_intent="Martial DPS/Tank"`)
- `Paladino`: divine healer/tank hybrid (`role_intent="Healer/Tank hybrid"`)
- `Cavaliere della Morte`: necro melee / dark frontline (`role_intent="Dark Frontline"`)
- NO dual-primary per ora
- **Live DB values (invariati R18.3c)**: warrior=`Tank`, paladin=`Tank`, cavaliere_della_morte (non seedato)

## P0-4 · Differenziazione 3 Cacciatori · design intent

- **Opzione scelta**: **B + C combinati** (archetipo tematico + item-pool separato)
- `Cacciatore di Mostri`: ranged/tracker/trappole/utility
- `Cacciatore del Sangue`: melee/sangue/sustain/self-risk
- `Cacciatore del Vuoto`: caster/void/curse/corruption
- **Live DB values (invariati R18.3c)**: 
  - `cacciatore_di_mostri`: `role="TBD"`, seedato R18.3a
  - `cacciatore_del_vuoto`: `role="TBD"`, seedato R18.3a
  - `cacciatore_del_sangue`: **non ancora seedato** (nessun orphan da migrare, sarà seed R18.3b.1 o R18.4)

## P0-5 · Cacciatore del Vuoto · design intent

- `role_intent`: `"DPS Caster"`
- `primary_stat_intent`: `"intelligence"`
- `secondary_stats_intent`: `["constitution", "dexterity"]`
- **Identità**: void damage, magia oscura, curse/debuff secondari, rischio/corruzione, control leggero. Continuità `warlock` legacy.
- **Live DB values (invariati R18.3c)**: `role="TBD"` (R18.3a.1 placeholder), `primary_stat=None`, `secondary_stats=None`

## P0-6 · Paladino primary stat · design intent

- `primary_stat_intent`: **`"charisma"`** (B)
- `secondary_stats_intent`: `["strength", "constitution"]`
- CHA primary (divine channeling), STR secondaria offensiva, CON secondaria difensiva
- **Live DB values (invariati R18.3c)**: `primary_stat="faith"`, `secondary_stats=["strength", "endurance"]`

## P0-7 · Cacciatore di Mostri primary stat · design intent

- `primary_stat_intent`: **`"dexterity"`** (A)
- `secondary_stats_intent`: `["wisdom", "constitution"]`
- DEX primary, WIS tracking/percezione, CON sopravvivenza
- **Live DB values (invariati R18.3c)**: `primary_stat=None`

---

## Sintesi migration-critical stats (design intent)

| Classe | role_intent | primary_stat_intent | secondary_stats_intent |
|---|---|---|---|
| **Paladino** | `Healer/Tank hybrid` | `charisma` | `[strength, constitution]` |
| **Guerriero** | `Martial DPS/Tank` | `strength` | `[constitution, dexterity]` |
| **Ladro** | `DPS/Utility` | `dexterity` | `[intelligence, charisma]` |
| **Cacciatore di Mostri** | `DPS/Utility` | `dexterity` | `[wisdom, constitution]` |
| **Cacciatore del Vuoto** | `DPS Caster` | `intelligence` | `[constitution, dexterity]` |

---

## Sintesi migration-critical stats (live DB values, invariati post-R18.3c)

| Classe | role live | primary_stat live | secondary_stats live |
|---|---|---|---|
| paladin | `Tank` | `faith` | `[strength, endurance]` |
| warrior | `Tank` | `strength` | `[endurance]` |
| rogue | `DPS` | `agility` | `[strength]` |
| `cacciatore_di_mostri` | `TBD` (placeholder R18.3a.1) | `None` | `None` |
| `cacciatore_del_vuoto` | `TBD` (placeholder R18.3a.1) | `None` | `None` |

---

## Enum conflict list (per R18.3b.1)

1. **Role composite** vs atomic (`Healer/Tank hybrid` non è in `VALID_ROLES`)
2. **Stat 6-stat** (`charisma`, `dexterity`, `constitution`, `intelligence`, `wisdom`) vs 5-stat legacy (`strength`, `agility`, `intellect`, `endurance`, `faith`)
3. **base_stats schema**: catalog ha `base_strength/agility/intellect/endurance/faith` int 0-10, non ha `base_dexterity/constitution/wisdom/charisma`
4. `Utility` non presente in `VALID_ROLES` (usato in `DPS/Utility`)
5. `Support`, `Control`, `Summoner`, `Hybrid`, `Dark Frontline` non in `VALID_ROLES`

**Impact per R18.3b.1**: schema migration + validation update + backfill 15 doc live + regression testing. Deferred a mini-round dedicato con brief PM esplicito.

---

## Sealing

**R18.3b CLOSED & SEALED (design intent only, not live DB values) ✅**

Timestamp: 2026-07-04T20:40Z

Le 7 answers P0 sono **PM design intent registrato** ma **NON applicate al catalog `adventurer_classes`** in R18.3c. R18.3c procede in mode `adventurer_class_slug_only` (solo `adventurers.class_slug` cambia, catalog immutable). Enum conflict deferrito a R18.3b.1 (nuovo mini-round pending).

Non riaprire R18.3b senza brief PM.
