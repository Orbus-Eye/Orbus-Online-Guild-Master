# Round 15 — Audit Classi & Statistiche (Fase 1)

**Author**: E1
**Date**: 2026-06-29
**Scope**: Read-only inventory di classi, specializzazioni e statistiche per
preparare il refactor "Class Identity" del Round 15.

---

## 1) Classi base presenti nel DB

Collection: `adventurer_classes`. Totale documenti: **111**. Attivi
(`is_active=True`): **12**. Restanti **99** sono artefatti
`test-class-*` con `is_active=false` (lascia stare: già fuori da ogni view).

| slug          | name        | role    | base STR | base AGI | base INT | base END | base FAI |
|---------------|-------------|---------|---------:|---------:|---------:|---------:|---------:|
| warrior       | Warrior     | Tank    |        8 |        4 |        2 |        9 |        2 |
| paladin       | Paladin     | Tank    |        7 |        3 |        2 |        7 |        6 |
| rogue         | Rogue       | DPS     |        5 |        9 |        3 |        4 |        2 |
| ranger        | Ranger      | DPS     |        5 |        8 |        4 |        5 |        3 |
| assassin      | Assassin    | DPS     |        6 |       10 |        4 |        3 |        1 |
| monk          | Monk        | DPS     |        5 |        9 |        3 |        6 |        5 |
| berserker     | Berserker   | DPS     |       10 |        5 |        1 |        6 |        1 |
| mage          | Mage        | DPS     |        2 |        4 |       10 |        3 |        3 |
| necromancer   | Necromancer | DPS     |        2 |        4 |       10 |        4 |        1 |
| priest        | Priest      | Healer  |        2 |        3 |        6 |        4 |       10 |
| druid         | Druid       | Healer  |        3 |        5 |        7 |        5 |        7 |
| bard          | Bard        | Support |        3 |        6 |        7 |        4 |        5 |

## 2) Specializzazioni

**Non esiste una collection dedicata** (`specs/specializations` assenti).
Le spec sono inlined sul documento avventuriero come sotto-oggetto
`specialization: {slug, name_it, name_en, tier, applied_*}`.

Spec attualmente presenti su avventurieri reali (estratte via aggregate):

| spec slug              | name_it         | tier   | classi che la usano |
|------------------------|-----------------|--------|---------------------|
| `spec_difensore`       | Difensore       | starter| Warrior             |
| `spec_furia`           | Furia           | starter| Warrior             |
| `spec_cecchino`        | Cecchino        | (n/d)  | Ranger              |
| `spec_maestro_di_armi` | Maestro d'Armi  | (n/d)  | Warrior             |
| `spec_stratega`        | Stratega        | (n/d)  | Bard                |
| `spec_restauratore`    | Restauratore    | (n/d)  | Priest              |

Le definizioni canoniche delle spec vivono in `app/training/catalog.py`
(`SPECIALIZATIONS_CATALOG`). Per Fase 1 non tocchiamo la spec catalog —
target Fase 2/3.

## 3) Statistiche reali

Le statistiche **core** sono cinque, salvate come campi top-level del
documento avventuriero (NON nested in `stats.*`):

| stat name (DB field) | label IT     | label EN  | range tipico Tier-1 |
|----------------------|--------------|-----------|---------------------|
| `strength`           | Forza        | Strength  | 2–10                |
| `agility`            | Agilità      | Agility   | 2–10                |
| `intellect`          | Intelletto   | Intellect | 2–10                |
| `endurance`          | Resistenza   | Endurance | 2–10                |
| `faith`              | Fede         | Faith     | 2–10                |

Campi *non-core* presenti sul doc avventuriero (di stato, non
combat-relevant nella formula del power):
- `morale` (0–100) — usato per buff temporanei roster-health
- `stamina` (0–100) — disponibilità per spedizioni
- `experience`, `level`, `class_role`, `class_name`, `specialization`,
  `rarity`, `is_available`, `expedition_in_progress` (status/identity)

## 4) Dove le stats sono salvate

| campo                 | collection         | path                                  |
|-----------------------|--------------------|---------------------------------------|
| strength              | `adventurers`      | top-level `adventurers.strength`      |
| agility               | `adventurers`      | top-level `adventurers.agility`       |
| intellect             | `adventurers`      | top-level `adventurers.intellect`     |
| endurance             | `adventurers`      | top-level `adventurers.endurance`     |
| faith                 | `adventurers`      | top-level `adventurers.faith`         |
| base_strength (class) | `adventurer_classes`| `adventurer_classes.base_strength`   |
| (idem per le altre 4) | `adventurer_classes`| `adventurer_classes.base_<stat>`     |
| strength_bonus (item) | `items`            | top-level `items.strength_bonus`      |
| (idem per le altre 4) | `items`            | `items.<stat>_bonus`                  |
| stat snapshot squadra | `expeditions`      | `expeditions.party[].*_snapshot`      |
| trait stat modifier   | `traits`           | `traits.modifier_type='stat'`         |

## 5) Influenza attuale delle stat sul gameplay

Tabella concreta (sorgente: `app/expeditions/formulas.py`,
`app/forge/services.py`, `app/equipment/services.py`,
`app/adventurers/services.py`, `app/expeditions/services.py`).

| stat       | power | dungeon  | raid     | PvP      | equip                  | XP        | traits | spec |
|------------|:-----:|:--------:|:--------:|:--------:|------------------------|:---------:|:------:|:----:|
| strength   | ✅    | ✅       | ✅       | ✅       | molti weapon (STR bonus)| ⚪︎       | ✅     | ✅   |
| agility    | ✅    | ✅       | ✅       | ✅       | leggera/finesse        | ⚪︎       | ✅     | ✅   |
| intellect  | ✅    | ✅       | ✅       | ✅       | grimoires, sigil       | ⚪︎       | ✅     | ✅   |
| endurance  | ✅    | ✅       | ✅       | ✅       | corazze pesanti        | ⚪︎       | ✅     | ✅   |
| faith      | ✅    | ✅       | ✅       | ✅       | reliquie, talismani    | ⚪︎       | ✅     | ✅   |

**Note attuali**:
- Power: `total_power = STR + AGI + INT + END + FAI + (level × 2) + equip_bonus`.
- Dungeon/raid `success_chance = 50 + (team_power − recommended_power)` (clamped 5..95).
- PvP usa lo stesso `total_power_snapshot` del PvE → tutte e 5 le stat
  contribuiscono allo stesso peso. Nessuna stat è "PvE-only" o "PvP-only".
- Equip: ogni rarità/slot mappa preferenzialmente a 1-2 stat (es. `iron_sword` → STR;
  `apprentice_robe` → INT). I bonus si sommano linearmente.
- XP: **oggi le stat NON influenzano l'XP** (sarà la novità del 15.2).
- Traits: 4 trait su 5 toccano direttamente uno dei `TRAIT_AFFECTABLE_STATS`
  (`("strength","agility","intellect","endurance","faith")`).
- Spec: 6 spec attive vincolate a `class_base` specifico.

## 6) Classi attualmente "troppo simili"

Tre coppie con range/policy quasi sovrapposti — il refactor di Fase 1
formalizzerà `primary_stat` per disambiguare l'identità.

| Coppia            | Sovrapposizione                                            | Mitigazione Fase 1 |
|-------------------|------------------------------------------------------------|---------------------|
| Mage ↔ Necromancer| Entrambi INT=10, DPS, basso END/FAI                        | secondary_stats divergenti (Mage=END, Necro=AGI) + preferred_item_tags |
| Rogue ↔ Ranger    | Entrambi AGI 8-9, DPS                                      | secondary_stats divergenti (Rogue=STR-stealth, Ranger=END-ranged) + role_tags |
| Priest ↔ Druid    | Entrambi Healer, FAI alta                                  | Druid mid-INT (caster ibrido) vs Priest pure-FAI (single-target) |
| Warrior ↔ Paladin | Entrambi Tank STR/END                                       | Paladin FAI=6 mid (utility healer) vs Warrior pure STR/END        |

## 7) Statistiche poco/non spiegate nella Guida attuale

Stato corrente di `Guide.jsx`:
- Sezione `stats-catalog` (#10) → presente, **data-driven** (lazy fetch
  da `/api/traits/stats-catalog` o simile) ma puramente tecnica.
- Nessuna sezione narrativa che spieghi: cosa fa Forza vs Resistenza,
  perché Fede non è solo "mana" ma anche damage holy, ecc.
- Nessuna sezione classi: nemmeno una tabella con i 12 archetipi.

Il task 3 di questa fase chiude entrambe le gap.

## 8) Statistiche poco usate / vestigial

Nessuna stat è realmente vestigial: tutte e 5 contribuiscono al power
e tutte vengono moddate da almeno qualche item/trait. Tuttavia:
- `faith` ha distribuzione **bimodale** sui roster reali: o ≥ 6
  (paladin/priest/druid) o ≤ 3 (le altre 9 classi). I player non-healer
  la trattano come "stat morta".
- `endurance` è la stat con bonus item più frequente (corazze) ma il
  suo contributo al power è 1:1 → poco "interessante" rispetto a STR
  che apre più item tier.

Niente da rimuovere/refactor in Fase 1, solo da spiegare meglio nella
Guida (Task 3).

---

## Executive summary (10 righe)

1. **12 classi attive**, 5 ruoli pesati: 2 Tank, 7 DPS (di cui 4 phys + 3 magic), 2 Healer, 1 Support.
2. **5 statistiche core** (STR/AGI/INT/END/FAI), salvate top-level su `adventurers`.
3. Tutte e 5 le stat alimentano l'unica formula del power → nessuna è vestigial, ma `faith` è "binaria" sui roster reali.
4. **Nessuna collection di specializzazione**: spec inlined sull'avventuriero. 6 spec live, catalogo definito in codice (`training/catalog.py`).
5. **4 coppie classi-quasi-cloni** identificate (Mage/Necro, Rogue/Ranger, Priest/Druid, Warrior/Paladin) → disambiguate via secondary_stats + tags.
6. **Equip già stat-aware**: ogni item porta 1-2 `<stat>_bonus`. Nessuna modifica al sistema item richiesta in Fase 1.
7. **XP attualmente non guarda le stat** → ganci pronti per la meccanica di Fase 2 (debuff su primary_stat bassa).
8. **Trait** già impattano tutte e 5 le stat via `TRAIT_AFFECTABLE_STATS`.
9. **Guide.jsx**: ha già `stats-catalog` data-driven ma manca tutta la parte narrativa per stats e l'intera sezione classi → Task 3 la introduce.
10. **Nessun rischio runtime**: il refactor di Fase 1 aggiunge solo campi descrittivi (`primary_stat`, `secondary_stats`, `*_tags`, `guide_description_*`). Zero impatto su power/PvP/economy.
