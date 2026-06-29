# ROUND 15 — Fase 2 / Task C — Material Drop Rate Diff

Generated: 2026-06-29 (R15.2)

## Scope
Prima del Round 15 fase 2 i **materiali** venivano distribuiti SOLO da:
- Quest giornaliere/settimanali (`app/quests/services.py` + catalog)
- Contratti (`app/contracts/catalog.py`)
- Admin grant (esclusi dai canali pubblici)

Le **spedizioni** non producevano alcun materiale. Round 15 introduce una
tabella dedicata in `app/expeditions/material_drop_tables.py`, con
**roll separato** rispetto agli item, e con rate **+70%** rispetto alla
baseline proposta.

## Rate baseline (pre +70%) vs Rate tunato (post +70%, clip per rarità)

I cap per rarità (mai superati anche con boost):

| Rarità    | Cap massimo |
|-----------|-------------|
| Common    | 85%         |
| Uncommon  | 55%         |
| Rare      | 25%         |
| Epic      | 15%         |
| Legendary | 10%         |

### Tier 1 (dungeon di apertura: goblin-warrens, sewer-nest, bandit-hideout, wolf-den-5p, ...)

| Material slug   | Rarità  | Baseline | +70% boost | Clipped final |
|-----------------|---------|----------|------------|---------------|
| iron_shard      | common  | 20%      | 34.0%      | **34.0%**     |
| raw_leather     | common  | 15%      | 25.5%      | **25.5%**     |
| healing_herb    | common  | 10%      | 17.0%      | **17.0%**     |

### Tier 2 (druid-grove, cursed-mines, shadow-crypts, sunken-library, iron-foundry-5p, ...)

| Material slug   | Rarità    | Baseline | +70% boost | Clipped final |
|-----------------|-----------|----------|------------|---------------|
| iron_shard      | common    | 25%      | 42.5%      | **42.5%**     |
| raw_leather     | common    | 20%      | 34.0%      | **34.0%**     |
| healing_herb    | common    | 15%      | 25.5%      | **25.5%**     |
| arcane_dust     | uncommon  | 15%      | 25.5%      | **25.5%**     |
| dull_gem        | uncommon  | 10%      | 17.0%      | **17.0%**     |

### Tier 3 (lich-sanctum, storm-spire, dragons-hoard, obsidian-arena-5p, voidspire-5p, ...)

| Material slug   | Rarità    | Baseline | +70% boost | Clipped final |
|-----------------|-----------|----------|------------|---------------|
| iron_shard      | common    | 30%      | 51.0%      | **51.0%**     |
| raw_leather     | common    | 20%      | 34.0%      | **34.0%**     |
| arcane_dust     | uncommon  | 20%      | 34.0%      | **34.0%**     |
| dull_gem        | uncommon  | 12%      | 20.4%      | **20.4%**     |
| dragon_essence  | rare      | 6%       | 10.2%      | **10.2%**     |

### Tier 4 — Elite 5p (infernal-pit-5p, celestial-citadel-5p, world-tree-roots-5p)

| Material slug   | Rarità    | Baseline | +70% boost | Clipped final |
|-----------------|-----------|----------|------------|---------------|
| iron_shard      | common    | 30%      | 51.0%      | **51.0%**     |
| arcane_dust     | uncommon  | 25%      | 42.5%      | **42.5%**     |
| dull_gem        | uncommon  | 15%      | 25.5%      | **25.5%**     |
| dragon_essence  | rare      | 12%      | 20.4%      | **20.4%**     |

## Failure penalty
In caso di FAIL della spedizione, ogni materiale tira al **50%** del rate
tunato (consolation drop, mai zero garantito).

## Compliance vs cap
Nessuna entry sfora i cap di rarità anche dopo il boost +70%. Materiali
floor essential (iron_shard / raw_leather / healing_herb) tutti ≥ 17% in
T1 come richiesto.

## Idempotenza & Independence
- Il roll dei materiali è eseguito DOPO il roll item, in `_complete_one_expedition`,
  e SCRIVE su `expedition.materials_found` (snapshot atomico).
- Il claim `status: in_progress → completing` previene double-counting su
  retry.
- Item drop e Material drop sono completamente indipendenti: nessuna
  competizione per uno slot singolo, l'una può tirare 0 e l'altra 1+.

## File modificati
- `app/expeditions/material_drop_tables.py` (NUOVO)
- `app/expeditions/services.py` (aggiunta chiamata + persistenza)
- `app/expeditions/loot_tables.py` (invariata — item roll non cambia)
