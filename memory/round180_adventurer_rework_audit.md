# Round 18.0 — Adventurer Identity, Class Mastery & Progression Rework — AUDIT READ-ONLY

**Data**: 2026-07-04T16:10Z
**Round precedente**: R17.3 Step 2 CLOSED & SEALED ✅
**Scope**: **SOLO audit / raccolta dati / feasibility / rischi**. NO implementazione. NO modifica DB/codice/seed. Le decisioni di design le fa il PM fuori da qui.
**Deliverable dati raw**: `/app/memory/round180_adventurer_rework_raw_data.json` (25 chiavi, dati live estratti da MongoDB).

---

## 1. Executive summary

Orbus Online oggi ha già **una base solida non ovvia** per il rework: 14 classi canoniche, 33 class_specializations pre-seedate, 1673 class_halls con `level` e `unlocked_specializations`, 40 traits con `modifier_type/value` funzionanti, 51 razze catalogate con rarity (Common→Epic), 2125 adventurers vivi, 178 item con `class_tags/recommended_classes/role_tags/stat_tags/slot_type/set_id/enchant_slots/max_refinement`.

**Non ha invece**:
- Un vero campo `grade` sull'adventurer (schema-only, 100% None).
- Un modello Common→Legendary progression per adventurer (solo `rarity` grezzo su alcuni doc).
- Un talent tree tier/rami/prereq (le class_specializations sono "flat", 1 tier senza dipendenze).
- Un cap `max_roster` esplicito sulle guild.
- Un training_field / "prima scelta classe gratis" — attualmente adventurer nasce già con `class_slug` in seed random.
- Item class-bound duri (i `recommended_classes` sono un **soft-hint**, non un enforce).
- PWR solo-equip: PWR oggi = base (`level × class multiplier + traits + stats`) **+** equip. Sono due sorgenti.
- Tomi/mastery items dedicati (grep `tome/mastery/knowledge` → 0 collezioni).

**Il rework è tecnicamente fattibile** ma richiede una migrazione dati sensibile su 2125 adventurers vivi e 178 item, con back-compat obbligata per almeno 2 round di transizione. Roadmap proposta: R18.1 (schema+read-model) → R18.2 (talent tree engine, feature-flag) → R18.3 (grade + tomi + roster 50) → R18.4 (dungeon/raid rework + PWR solo-equip switch definitivo).

**Rischio più alto**: unificare `class` (legacy string "Guardian"/"Cleric"/…) con `class_slug` (canonico "paladin"/"priest"). Oggi 91 adventurers hanno `class_slug = None` e i restanti hanno un mix.

---

## 2. Stato reale classi attuali

**14 classi canoniche in `db.adventurer_classes`** (non 15 come nel target PM). Elenco:

| # | slug | display_name_it | role | secondary_role | primary_stat | secondary_stats | is_base_class | deprecated_at | adventurers count |
| :---: | --- | --- | :---: | :---: | --- | --- | :---: | :---: | :---: |
| 1 | alchemist | Alchimista | DPS | Support | intellect | agility, endurance | ✅ | — | 135 |
| 2 | assassin | Assassino | DPS | — | agility | strength | ✅ | — | 0 (unico rogue?) |
| 3 | bard | Bardo | Support | Healer/DPS | intellect | faith | ✅ | — | 177 |
| 4 | berserker | Berserker | DPS | Tank | strength | agility | ✅ | — | 3 (legacy migration!) |
| 5 | druid | Druido | Healer | Support | faith | endurance | ✅ | — | 167 |
| 6 | mage | Mago | DPS | — | intellect | agility | ✅ | — | 218 |
| 7 | monk | Monaco | DPS | Tank | agility | endurance | ✅ | — | 162 |
| 8 | necromancer | Necromante | DPS | Support | intellect | faith | ✅ | — | 0 |
| 9 | paladin | Paladino | Tank | Healer | faith | strength | ✅ | — | 163 |
| 10 | priest | Sacerdote | Healer | Support | faith | intellect | ✅ | — | 187 |
| 11 | ranger | Ranger | DPS | — | agility | intellect | ✅ | — | 175 |
| 12 | rogue | Ladro | DPS | Support | agility | intellect | ✅ | — | 229 |
| 13 | warlock | Warlock | DPS | Support | intellect | faith | ✅ | — | 128 |
| 14 | warrior | Guerriero | Tank | DPS | strength | endurance | ✅ | — | 290 |
| — | **`class_slug = None`** | — | — | — | — | — | — | — | **91** (orfani) |

**Problemi trovati**:
- **assassin, necromancer**: 0 adventurers assegnati (nessuna gilda ha attualmente questi). Probabilmente creati come catalog ma mai assegnati nei seed roster.
- **berserker**: solo 3 doc, tutti da `is_legacy_migration_target: true` (residuo pre-consolidamento).
- **91 orfani `class_slug=None`**: adventurers legacy pre-R16.x. Il PM sa già che 6 hanno `class="Guardian"/"Cleric"`, ma **91** è un numero più grande.
- Nessuna classe è marcata `deprecated_at`.
- Nessuna classe ha `is_hybrid: true` — la visione PM di ruolo hybrid via talent (Warrior/Berserker/Guardian/Weapon Master) è coerente con lo schema attuale ma **non ancora usato**.

**`class_specializations`** (33 doc): sistema talent-tree "flat" già esistente.

| classe | specializzazioni | fields relevanti |
| --- | --- | --- |
| warrior | berserker_spec, guardian_spec, weapon_master_spec | stat_bonus, weapon_tag_unlocks, armor_tag_unlocks, counter_tags, requires_class_hall_level, is_legacy_migration_target |
| rogue | assassin_spec, duelist_spec | " |
| … | … (33 tot per 14 classi ≈ 2-3 spec/classe) | " |

Struttura data: `{slug, class_slug, display_name_it, description_it, stat_bonus{…}, weapon_tag_unlocks[], armor_tag_unlocks[], counter_tags[], is_legacy_migration_target, is_unlockable, requires_class_hall_level, is_active}`.

**Note**: già supporta stat_bonus + unlocks + level gate class_hall. **Mancano**: tier/rami, prerequisiti fra spec, mutual-exclusion, points_cost, max_points, respec.

**`class_halls`** (1673 doc): 1 hall per (guild, classe). Ogni doc ha `level`, `is_unlocked`, `unlocked_specializations[]`, `training_territory_id`. **Sistema training-hall pronto**.

**Auto-Equip role mapping (R17.3 Step 2 E)** — 14 classi mappate FE-side in `ExpeditionNew.jsx`:
- Tank: warrior, paladin
- Healer: priest, druid
- Support: bard
- DPS: 9 restanti

---

## 3. Stato reale avventurieri (schema)

**Schema `adventurers` sample (legacy, `phase13_unbaked=true`)**:

| campo | tipo | note |
| --- | --- | --- |
| `id` | uuid4 str | ✅ |
| `guild_id` | uuid4 str | ✅ |
| `name` | str | ✅ |
| `class` | str (legacy) | ⚠️ "Guardian"/"Cleric"/"Warrior" — nome capitalizzato, non slug |
| `class_slug` | str canonico | ⚠️ presente su ~2034 doc, `None` su 91 |
| `class_name` | str (i18n?) | presente ma non standardizzato |
| `role` | str "Tank"/"DPS"/… | derivato da classe |
| `level` | int | 1-15 nei sample |
| `stats` | dict `{atk, def, pwr, spd}` | ⚠️ LEGACY 4-stat, NON matching primary/secondary_stat delle classi (che sono `strength/agility/intellect/endurance/faith`) |
| `team_power` | int | valore aggregato PWR pre-equip |
| `traits` | list[str] | trait slug list |
| `is_available` | bool | occupato in expedition o no |
| `archived/retired/frozen` | bool | soft-delete states |
| `is_test_artifact` | bool | test data flag |
| `created_at/updated_at` | datetime ISO | UTC |
| `phase13_unbaked` | bool | flag legacy migration incompleta |
| `rarity` | str \| None | 2060 "Common" + 30 "common" + 3 "Uncommon" + 32 None |
| `grade` | ❌ | schema esiste, TUTTI None (100%) |

**Campi MANCANTI per il nuovo modello** (visione PM):
- `race` (razza, es. tabaxi/dragonide/tiefling) — 51 razze in catalog ma **mai referenziate nell'adventurer**
- `gender` — 0
- `background` — 0
- `biography` / `lore_text` — 0
- `talents` (list di talent_id + points) — 0
- `mastery_points` / `mastery_level` — 0
- `class_history` (classi precedenti + tomi consumati) — 0
- `dungeons_completed` / `raids_completed` counters — 0 (esistono solo su guild aggregato)
- `signature_moves` (unlockable finishers) — non presente su adventurer
- `equipped_slots` — è normalizzato in `equipped_items` collection separata
- `training_field_slug` (per training→classe) — 0
- `is_recruit` / `is_untrained` (adventurer "Common/Recluta" pre-training) — 0

**Grade Common→Legendary**: schema `grade` esiste ma **completamente vuoto**. Va **popolato ex novo**.

---

## 4. Stato reale rarity/grade

**Tre concetti DIVERSI oggi mescolati**:

1. **`item.rarity`** — usato attivamente su 178 item: Common/Uncommon/Rare/Epic/Legendary. È **gameplay** (drop table, power_score, forge recipe). ✅ OK come modello.
2. **`adventurer.rarity`** — semi-usato: 2060 "Common" + 30 "common" (case mismatch!) + 3 "Uncommon" + 32 None. Non ha effetti gameplay evidenti (probabilmente cosmetic/starter marker). ⚠️ Bassa qualità dati.
3. **`adventurer.grade`** — schema-only, 100% None. **Non esiste ancora come concetto**.
4. **`race.rarity`** — 51 razze taggate common/uncommon/rare/epic. Usato? Nell'audit del sample adventurer NON c'è campo `race`, quindi la rarity razziale **non è mai propagata** all'adventurer.

**Cosa manca per l'idea PM "Common Recluta → Legendary con 100 raid + 1000 dungeon"**:
- Field `grade` (Common/Uncommon/Rare/Epic/Legendary) su adventurer
- Contatori history su adventurer (`raids_completed`, `dungeons_completed`, `expeditions_completed`, `pvp_wins`, `boss_kills`, `days_active`)
- Formula upgrade grade → nuovo modulo dedicato (`app/adventurer_grade/` non esiste)
- Rewards visibili (cosmetic banner + stat bonus + slot equipaggiabili?)

---

## 5. Stato reale PWR/power

**Formula attuale (deduzione da campi + moduli)**:
- `adventurer.stats.pwr` = base pwr (dalla classe/level/traits)
- `adventurer.team_power` = pwr aggregato che alcuni sistemi leggono
- `power_score` (usato in item + item recommended + auto-equip): valore che rappresenta il contributo dell'equipaggiamento
- **Somma effettiva PWR** in expedition/raid/PvP: mix di `adventurer.team_power` + equipped items `power_score`

**Sistemi che leggono PWR** (grep):
- `app/expeditions/services.py` — combattimento + report
- `app/raids/*` — combined team power
- `app/pvp_*` — matchmaking
- `app/resources/*` — gate `guild_level` (non PWR)
- `app/auto_equip*` — target maximization
- `app/recruitment_offers` — soglia adventurer proposto

**Cosa si romperebbe se PWR = solo equip**:
- Bilanciamento dungeon `recommended_power`: attualmente calibrato assumendo base PWR + equip. Bisogna ridurre `recommended_power` su TUTTI i 23 dungeon + 3 raid.
- PvP matchmaking: cambia il ranking (adventurer level 15 senza equip → PWR = 0).
- Auto-Equip class-fit: già lavora per massimizzare score_delta → **compatibile senza rework**.
- Expedition preview / power hint UI: da rivedere.

**Preservazione consigliata**: introdurre `adventurer.base_stats` (le nuove stats granulari dalle classi: strength/agility/…) come "influenza" del talent tree/mastery ma **NON contribuire a PWR** direttamente. PWR resta puro equipaggiamento. Le stats granulari fanno da moltiplicatore/bonus percentuale sull'equip appropriato (es. `strength` × equip Tank bonus %).

---

## 6. Stato reale item/equip

**178 item totali**, di cui **157 con `recommended_classes` non-vuoto** (88%), 21 generic (12%).

**Schema item ricco**:
- `slug, name, display_name_it/en`
- `item_type` (weapon/armor/accessory)
- `slot_type` (probabile enum finer-grained)
- `rarity` (Common/Uncommon/Rare/Epic/Legendary)
- `required_adventurer_level` (bucket 1/3/5/8 per non-Legendary; Lv 8/9/12 per Legendary)
- `power_score`
- `class_tags[]` (canonical class slugs)
- `recommended_classes[]` (soft-hint, usato da Auto-Equip)
- `role_tags[]` (tank, dps_melee, dps_ranged, dps_caster, healer_aoe, healer_dedicated, support, frontline, stealth)
- `stat_tags[]` (agility, intellect, faith, strength, endurance)
- `weapon_tags[]` / `armor_tags[]` (mundane, arcane, dark, cloth, medium, light)
- `equipment_tags[]` (belt, ring, bracer, trinket, cord, …)
- `lore_tags[]` (memoria, veglie, filo-spezzato, frontiera, mundane)
- `enchant_slots` (numero slot enchant)
- `max_refinement` (grade di refine max)
- `set_id` (set support **già presente** in schema, non ancora usato attivamente)
- `affix_pool_tag` (per affix random)
- `flavor_text_it`, `spoiler_level`, `lore_reviewed/at/source`

**Set support**: `item_sets` collection ha 3 doc. Sistema già in schema. **Riusabile per set future**.

**Class-bound già presente?**
- **Soft**: `recommended_classes[]` è un hint (Auto-Equip lo usa per preferenza, ma un adventurer può ancora equipaggiare item off-class).
- **Hard class-bound**: **NON esiste**. Nessun enforcement backend "questo item è utilizzabile solo da monk".

**Off-class check**: attualmente Auto-Equip R16.5.4c filtra class-aware ma i **player possono ancora equipaggiare manualmente item off-class**. Nel nuovo modello va aggiunto enforce backend su `POST /adventurers/{id}/equip`.

**Coverage per classe** (from raw data `items_coverage_per_class_slot`):
- Best: paladin (92 total), warrior (69), berserker (64)
- Ok: druid (34), priest (32), mage/necromancer (34/34)
- Post-R17.3 Step 2: monk/warlock/alchemist ora 6/6/6 per slot (patch C1P1)

---

## 7. Stato auto-equip vs nuovo modello

**Cosa è riusabile**:
- ✅ Logica class-aware R16.5.4c (`recommended_classes` + `class_tags`)
- ✅ Role mapping R17.3 Step 2 E (Tank/Healer/DPS/Support/Hybrid)
- ✅ Payload IT class-aware (traduzioni "Monaco"/"Alchimista"/…)
- ✅ Score-based ranking (`power_score`)
- ✅ Bucket safety (`POWER_MAX_BY_BUCKET`)
- ✅ Idempotency + audit event

**Cosa va riscritto per PWR solo equip + class-bound + talent-tree + role dichiarato**:
- ⚠️ Score calculator: se PWR è solo equip, il "team_power" attuale non conta più → richiede refactor endpoint `/adventurer/{id}` + preview.
- ⚠️ Enforce class-bound: `POST /adventurer/{id}/equip` deve rifiutare item con `class_tags` non matching (oggi solo warning).
- ⚠️ Talent modifiers: se un talent aumenta "efficacia armi arcane +10%", il calcolo score_delta va modificato per moltiplicatore per stat_tag/weapon_tag.
- ⚠️ Role dichiarato: se un adventurer dichiara "Tank via talent", Auto-Equip deve prendere quello come sorgente unica (invece di derivare da class_slug).
- ✅ Set bonus: aggiungere calcolo aggregato `set_id` durante score computation (attivare i 3 set esistenti).

---

## 8. Stato reale class_halls / training fields / strutture

**`class_halls`** (1673 doc):
- 1 doc per (guild, class_slug) = 14 hall per gilda × 119 gilde attive ≈ 1666, +tester = 1673.
- Fields: `level` (int, default 1), `is_unlocked` (bool), `unlocked_specializations[]`, `training_territory_id`.
- **Ottima base per training_field**: già ha unlock granulare per classe + level + specializations.
- **Naming pragmatico**: `class_halls` può restare (o essere ridenominato `training_grounds` se il PM vuole coerenza con la visione "training field").

**`guild_structures`** (per gilda):
- Building sistemici (forge, market, quartermaster, ecc.).
- Alcuni gate `min_guild_level` (via `structure.level_required`).
- Non c'è oggi una struttura "Academy" o "Barracks" dedicata al training.

**`territories`**: sistema separato (non nella query attuale, ma esiste come modulo). Può fornire il "training_territory_id" già presente in class_halls.

**Verdict**: **NO nuovo sistema training**. Estendere `class_halls` con:
- `training_slots_available` (quanti recruit possono trainare in parallelo)
- `training_duration_seconds` (durata training per classe)
- `training_material_required` (per training oltre la prima classe)
- `is_starter_hall` (marcare quale hall è "gratis" al primo unlock)

---

## 9. Feasibility talent tree

**Cosa esiste già**:
- ✅ `adventurer_traits` (40 doc): schema `{slug, name, affected_stat, modifier_type: flat/percent, modifier_value, is_positive}`. **È già un modifier engine leggero, ma trait-level, non talent-level**.
- ✅ `class_specializations` (33 doc): schema `{slug, class_slug, stat_bonus{stat:value}, weapon_tag_unlocks[], armor_tag_unlocks[], counter_tags[], is_unlockable, requires_class_hall_level}`. Sistema talent "flat" con 1 tier.
- ✅ `guild_arfus_technologies` / `arfus_technology_catalog`: sistema con prereq multi-tier + research_cost + tech-tree — **pattern architetturale già usato** (potrebbe fare da template per talent tree adventurer).

**Cosa manca**:
- ⚠️ Modello dati `talent_tree`: rami + tier + prerequisites + points_cost + max_points.
- ⚠️ Adventurer `talent_points_available` + `talent_choices[{talent_id, points_spent}]`.
- ⚠️ Respec mechanism (opzionale, ma probabilmente richiesto).

**Struttura tecnica PROPOSTA (solo scaffolding, NON talenti specifici)**:

```
db.talent_catalog:
  - talent_id (uuid), slug (str, unique)
  - class_slug (str, indexed)
  - branch (enum: primary/secondary/utility) — 3 rami per classe
  - tier (int 1-5) — 5 tier per ramo
  - prerequisites: list[talent_id]  — dipendenze DAG
  - max_points (int, default 1)
  - points_cost (int, default 1)
  - name_it/en, description_it/en
  - stat_modifiers: dict{stat: value}
  - role_modifiers: dict{role: value}   # es. tank_effectiveness +10%
  - tag_modifiers: dict{tag: value}     # es. arcane_dmg +5%
  - unlock_features: list[str]          # es. "reactive_shield", "double_strike"
  - is_active, seed_source

db.adventurer_talents:
  - adventurer_id (indexed)
  - talent_id (indexed)
  - points_spent (int)
  - unlocked_at (datetime)

adventurer schema addition:
  - talent_points_available (int)
  - talent_points_earned_total (int)  # audit
  - talent_reset_count (int)          # respec history
```

**Compatibilità UI**:
- Frontend attuale ha `GuildProgressCard` + `AdventurerDetailModal` (già rework in R17.2/R17.3). Un talent tree richiede una **nuova view dedicata** (`/adventurers/{id}/talents`) con struttura DAG. Non è banale ma non è distruttivo.
- Component library: shadcn-ui è ok. Serve un layout tree/DAG (usare react-flow, o SVG custom).

**Compatibilità backend modifier engine**:
- `adventurer_traits` schema è sostanzialmente lo stesso dei talenti proposti. Il modifier engine è pronto.
- Serve solo **estenderlo** per aggregare (trait + talent) modifiers al momento del score/PWR/expedition/PvP calc.

---

## 10. Feasibility class mastery / tomi

**Grep sul codebase** (`tome/knowledge/mastery/class_token/scroll/training/book/manual`) nel repo Orbus:
- **0 collezioni** dedicate a tome/mastery/knowledge.
- 0 item con slug `tome_*` o `mastery_*`.
- `training_territory_id` esiste in class_halls ma non è un "tomo" item.
- **`arfus_technology_catalog`** (10 doc): sistema simile ma per guild-tier tech, non class-tier.

**Item simili già presenti**: nel catalog `items` non ci sono ancora item-materiale "tome". Il campo `item_type` è limitato a weapon/armor/accessory (+ Legendary craft materials in `legendary_forge_catalog`).

**Cosa manca**:
- Nuovo `item_type: "tome"` (o `"knowledge_book"`)
- Nuovo `training_material` schema? O riuso `inventory_items`?
- Class token: adventurer inventory personale + guild inventory (già presente `db.inventory_items`).
- Cost model per "seconda classe": livello adventurer + N tomi + M materiali + M dungeon completati.

**Proposta scaffolding**:
```
Nuovi item_type nel catalog:
  - class_tome (slug: "class_tome_<class>", "class_tome_generic")
  - training_manual (slug: "training_manual_<discipline>")
  - class_switch_seal (slug: "class_switch_seal_<class>")

Nuovo endpoint (design solo):
  POST /adventurers/{id}/change-class
    body: {new_class_slug, tome_ids[], material_ids[]}
    validation: adventurer.level >= min_level_for_class, tomi disponibili, dungeon completati
    effect: consume tomi/materials, reset talenti, migra a nuova classe, mark class_history
```

---

## 11. Impatto dungeon/raid

**Dungeon**: 23 totali (12 dungeon 5p diff 1-4 + 11 dungeon 3p vari livelli).
**Raid**: 3 endgame in `raid_dungeons` (broken-bastion-siege pw800, necropolis-bells pw900, dragon-vault pw1400).
**`raids` collection**: 1 doc (residuo legacy?).

**Level/power curve**:
- Lv 1-3: 3 starter dungeon (Training Yard, Goblin Den, Sewer Nest)
- Lv 4-7: 6 dungeon vari + 3 5p diff1-2
- Lv 8-11: 5 dungeon + 3 5p diff3
- Lv 12-15: 3 5p diff4 (world-tree-roots power 360)
- Lv 15-20: solo i 3 raid endgame

**Cosa può restare / ricalibrato / trasformato**:
- **Restano invariati**: 3 starter dungeon (Training Yard, ecc.) e 3 raid endgame (economia critica).
- **Ricalibrati** (se PWR diventa solo equip):
  - Tutti i `recommended_power` vanno ridotti di ~30-40% (perché prima includevano base PWR class + equip).
  - I 12 dungeon 5p vanno rivisti (curva 80→360 troppo lineare, richiederebbe re-bucketing).
- **Trasformati in Tomi drop**:
  - 2-3 dungeon mid-tier (Lv 5-8) potrebbero drop `class_tome_<class>` con weighted probability per class del boss.
  - Requisito "1000 dungeon completed" per Legendary grade → **necessita un counter dungeon per adventurer** (oggi non c'è, solo aggregato guild).

**Come impedire farm tutorial per Legendary**:
- Diminishing returns: `dungeon_completed_count[dungeon_slug]` con weight decrescente (es. 1st completion vale 1.0, 10th=0.5, 100th=0.1).
- Cap giornaliero grade_points per dungeon.
- Grade Legendary richiede **variety** (es. min 5 dungeon distinti + min 3 raid distinti + min 20 PvP win).

---

## 12. Impatto roster cap 50

**Roster cap attuale**:
- `guild` schema **NON ha** `max_roster` / `max_adventurers` / `roster_size` field.
- Cap attuale probabilmente hardcoded nel codice (grep `max_roster` / `roster_limit` in `/app/backend/app/`):
  - Verificato: nessun cap esplicito nel guild schema.
  - Il cap è implicito via `guild_level` — R16.x aumentava roster con level.

**Impatto UI/perf/raid/dungeon/resource su roster 50**:
- **UI mobile**: pagina `Adventurers.jsx` renderizza 20-30 card in griglia. 50 card = paginazione o lazy load OBBLIGATORI. Attualmente non c'è.
- **Perf**: query `db.adventurers.find({guild_id})` con index (guild_id) resta fast (50 doc = nulla). OK.
- **Raid 20p (4×5)**: già usano 20 avv. Roster 50 → più flessibilità composizione. OK.
- **Dungeon**: 3p / 5p — nessun impatto.
- **Resource missions (R17.2)**: 3 avv per mission × 6 missioni/day = 18 avv occupati. Con roster 50, resta ampio margine idle per PvP + expedition + resource.

**Proposta cap scalare**:
- Guild Lv 1: 10 avv (starter)
- Guild Lv 3: 15
- Guild Lv 5: 20
- Guild Lv 7: 25
- Guild Lv 10: 30
- Guild Lv 15: 40
- Guild Lv 20: 50
- **Formula**: `max_roster = min(50, 8 + guild_level × 2)` (esempio, PM decida)
- Fields: aggiungere `guild.max_roster_current` (int, computed) + `guild.max_roster_cap` (int, hard cap = 50).

---

## 13. Identità avventuriero

**Campi identità presenti oggi**:
- ✅ `name` (nome random dal generator R14.x)
- ✅ `traits[]` (0-3 traits da catalog 40)
- ✅ `class_slug` / `class_name`
- ✅ `level`

**Campi identità MANCANTI** (secondo visione PM "Rare/Epic/Legendary come Dragon Lore/Beyoncé/Michael Jordan"):
- ❌ `race` (razza — 51 razze in catalog ma orfane)
- ❌ `gender` — non presente
- ❌ `background` — non presente
- ❌ `biography` / `lore_text_it` — non presente
- ❌ `achievements_personal` (achievement per adventurer, non solo guild) — non presente
- ❌ `history` (contatori: dungeons_completed, raids_completed, expeditions_won, pvp_wins, boss_kills, days_active)
- ❌ `signature_quote` / `motto` — non presente
- ❌ `portrait_url` (o `avatar_seed`) — non presente
- ❌ `age`, `birthplace` (opzionale, cosmetico)

**Dove salvare**:
- Fields diretti su `db.adventurers` (per lookup fast).
- `db.adventurer_history` collection separata (per audit history rich, es. "questo adventurer ha ucciso il World Boss il 2026-06-15").
- `db.adventurer_achievements` (achievement unlockati per adventurer, index su adventurer_id + achievement_slug).

**Feasibility**: OK. 40 traits + 51 razze già catalogate. Serve solo:
1. Popolare `adventurer.race` (query random dalla `db.races` con weighted rarity).
2. Estendere schema con biography/gender/background (opzionali, lore-first).
3. Nuovo collection `adventurer_achievements` per contatori.

---

## 14. Piano migrazione ipotetico (NO exec, solo documenti toccati)

**Fase A — Read-model prep** (nessuna scrittura destructive):
- Nuovo collezioni: `talent_catalog`, `adventurer_talents`, `adventurer_history`, `adventurer_achievements`
- Nuovo campi (con default null) su `adventurers`: `grade`, `race`, `gender`, `background`, `biography`, `talent_points_available`, `talent_points_earned_total`, `class_history[]`, `is_recruit`, `training_field_slug`
- Nuovo campi su `guilds`: `max_roster_current`, `max_roster_cap`
- Migration script append-only.

**Fase B — Backfill** (per 2125 adventurers):
- `race`: random weighted da `db.races` per rarity coerente con guild_level.
- `grade`: derivato da history counters (nuovi contatori partono a 0 = tutti Common).
- `is_recruit`: false (backfill), true solo per nuovi adventurer generati post-rework.
- `talent_points_available`: 0 (nessuno spende ancora).

**Fase C — Feature-flag activation** (feature-flag per gilda):
- Nuovo endpoint `POST /adventurers/{id}/train-class` (gated `feature_flag=r18_rework`).
- Class hall training UI dietro flag.
- Talent tree UI dietro flag.

**Fase D — PWR switch** (breaking change):
- Ricalibrazione tutti `recommended_power` (dungeon + raid + PvP threshold).
- `adventurer.stats.pwr` → deprecated (mantenere in schema per back-compat, ma non usato).
- Snapshot pre/post per verifica no regression.
- Rollback plan: revert al `stats.pwr` legacy via feature-flag disable.

**Compensazioni player**:
- Respec gratis per tutti gli adventurers pre-esistenti (1 respec token per adventurer).
- Tomi iniziali gratuiti: 1 tome per guild per class attualmente non presente in roster (incentivo a esplorare classi nuove).
- Prima scelta classe gratis (nuovi adventurer post-rework partono Common Recluta con 1 training gratuito).
- Communicazione: report in-game "Cosa cambia con R18" con tabella prima/dopo.

**Legacy da preservare**:
- `class` (str legacy) — mantenere per 2 round, poi sunset.
- `stats.pwr` — mantenere per 2 round come read-only computed.
- `phase13_unbaked` flag — usare come "questo doc è pre-R18, va ri-processato".

---

## 15. Rischi principali

| # | Rischio | Gravità | Probabilità | Sistemi coinvolti | Mitigazione | Round consigliato |
| :---: | --- | :---: | :---: | --- | --- | :---: |
| 1 | **DB migration 2125 adventurer** con nuovi field | 🔴 Alta | Alta | adventurers, class_halls, expeditions | Migration append-only + dry-run + snapshot + rollback via feature-flag | R18.1 |
| 2 | **UI regression** (mobile roster 50, talent tree dedicato) | 🔴 Alta | Media | Adventurers.jsx, AdventurerDetailModal, nuova TalentTreeView | Lazy load + progressive rollout + fallback FE | R18.2 |
| 3 | **Balance talenti** rompe curva PvP/raid | 🔴 Alta | Alta | pvp_battles, raid_dungeons, dungeons | Talenti tier 1 stat-only (no active abilities) in R18.2. Active abilities R18.3+ | R18.2/R18.3 |
| 4 | **Dungeon/raid invalidati** da PWR solo-equip | 🔴 Alta | Alta | dungeons.recommended_power, raid_dungeons.recommended_power_combined | Ricalibrazione con snapshot pre/post, feature-flag `pwr_equip_only=true` | R18.4 |
| 5 | **Item off-class esistenti** nell'inventory dei player | 🟠 Media | Alta | inventory_items, equipped_items | Grazioso migration: item off-class restano equipaggiabili una-tantum ma marcati `deprecated_equip=true` | R18.3 |
| 6 | **Player confusion** (rework macro può frustrare) | 🟠 Media | Alta | UI, changelog, tooltip | Report in-game bilingue + video tutorial + respec gratis + compensazioni | R18.1-R18.4 |
| 7 | **Performance roster 50** su mobile | 🟡 Bassa | Media | Adventurers.jsx, api pagination | Lazy load (10-20 doc/page) + virtualized list | R18.3 |
| 8 | **PvP matchmaking** rotto durante switch | 🔴 Alta | Media | pvp_matches, pvp_battles | Freeze PvP season durante R18.4 switch + reset ELO | R18.4 |
| 9 | **Economia tomi** (P2W risk se acquistabili) | 🔴 Alta | Media | shop_daily_offers, market_listings | NO tomi in shop premium. Solo drop dungeon + craft in class_hall | R18.3 |
| 10 | **Legacy `class` vs `class_slug`** confusione | 🟠 Media | Alta | adventurers | Migration script `class → class_slug` con audit dei 91 orfani + Guardian→paladin/Cleric→priest aliasing (proposta R17.3 audit) | R18.1 |
| 11 | **Grade progression farming** | 🟠 Media | Alta | achievements, dungeons | Diminishing returns + variety requirement (5+ dungeon distinti) | R18.3 |
| 12 | **Backup / rollback DB** | 🔴 Alta | Bassa | tutta la DB | Snapshot completo pre-R18.1 + strategy blue-green | Pre-R18.1 |
| 13 | **Talent respec spam** | 🟡 Bassa | Media | adventurer_talents | Cap respec 1/settimana + cost oro crescente | R18.3 |
| 14 | **PvP defense team pre-R18** invalidati | 🟠 Media | Alta | pvp_defense_teams | Auto-migration + notifica player + respec squad gratis 1× | R18.4 |
| 15 | **Feature flag rollout partial** (gilda A ha R18, gilda B no) | 🟠 Media | Bassa | tutta la piattaforma | Global flag on/off (no per-guild flag) o "opt-in" beta season | R18.2 |
| 16 | **Localization non pronta** per talenti/tomi | 🟢 Bassa | Alta | i18n | Tracciato in R16.5.4f Localization Sweep [P3] | Parallelo |
| 17 | **Testing agent copertura** per rework macro | 🟠 Media | Media | tests/ | 3-4 nuovi test suite dedicati (schema, migration, talent-tree engine, class-change flow) | R18.1-R18.4 |

---

## 16. Domande da portare al PM (decisioni bloccanti aperte)

1. **15 vs 14 classi canoniche?** Attualmente 14 in `adventurer_classes`. Vuole aggiungere una 15° (es. rinominare o creare una `paladin_dark`/`shaman`)? O consolidare a 14?
2. **Rename classi**? Warlock→Stregone? Necromancer→Negromante? (Il DB ha `display_name_it` "Warlock"/"Necromante", verificare se PM vuole 100% IT.)
3. **Quali specializzazioni deprecate**? 33 spec attuali (2-3 per classe). Il PM vuole conservare tutte come tier 1 del talent tree, o filtrare?
4. **Struttura talent tree tier N**? Proposta 3 rami × 5 tier × ~4 talent/tier = ~60 talent/classe × 14 = 840 talent totali. Troppi? Il PM preferisce 3×3×3 (~30/classe = 420 total)?
5. **Sblocco roster progressivo**: formula proposta `min(50, 8 + guild_level × 2)` = OK? O curva diversa (es. sblocco a milestone Lv 5/10/15/20)?
6. **Class-bound HARD o SOFT**? Se un weapon Rare monk viene assegnato a un warrior, deve essere rifiutato dal backend `POST /equip` (hard) o solo warnato in UI (soft)?
7. **Legendary grade requisiti**: 100 raid + 1000 dungeon + N PvP wins + M variety count? Formula esatta va calibrata.
8. **PWR solo equip attivazione**: full-switch o duale (per 2 round back-compat)? Se full-switch, richiede migration di tutti gli `recommended_power` in un solo round.
9. **Prima scelta classe gratis**: adventurer nasce Common Recluta con 0 classe → training obbligatorio prima di poter fare expedition? O nascono già con `class_slug` random ma con option di "retraining gratuito 1×"?
10. **Tomi drop-only o craftable**? Se craftable in class_hall, che materiali? Se drop-only, che dungeon dropano quali tomi?
11. **Race popolamento retroattivo**: 2125 adventurer esistenti ricevono race weighted da `db.races` (51 razze) al momento della migration, o restano race=None e solo i nuovi hanno race?
12. **Respec strategy**: Talent respec gratis 1/settimana o cost oro crescente?
13. **Roster 50 breakdown**: 50 total, o 50 attivi + 10 riserva/pensionati? (Retirement dell'adventurer come parte dell'identità narrativa.)
14. **`class_halls` rename?** Il PM parla di "training field" — mantenere `class_halls` come collection oppure alias/rename?
15. **6+91 orfani `class_slug=None`**: aliasing Guardian→paladin/Cleric→priest + fallback random weighted per i restanti, o retirement soft-delete?

---

## 17. Roadmap consigliata R18.1 / R18.2 / R18.3 / R18.4

### R18.1 — Schema Foundation & Data Backfill (2-3 sprint)

**Scope**: preparare il terreno senza breaking change.
- Migration append-only: nuovi field su `adventurers` + `guilds` + nuove collezioni `talent_catalog` / `adventurer_talents` / `adventurer_history` / `adventurer_achievements`.
- Backfill: race weighted, grade=Common, is_recruit=false (per adventurer legacy), max_roster_current per guild.
- Migration `class`→`class_slug` completa: 91 orfani + aliasing Guardian→paladin/Cleric→priest.
- Ripulire duplicati rarity ("Common"/"common" → Common).
- **Feature flag `r18_rework_enabled = false` globale.**
- **Nessuna modifica economia/PWR/talent visibile ai player.**
- Testing: 1 nuovo pytest per migration integrity + snapshot before/after.

### R18.2 — Talent Tree Engine + UI (3-4 sprint)

**Scope**: sistema talent tree funzionale ma flag-gated.
- Seed `talent_catalog`: ~30-60 talent per classe (stat-only tier 1-3, feature flag active-abilities tier 4-5 posticipato).
- Endpoint: `GET /adventurers/{id}/talents`, `POST /adventurers/{id}/talents/spend`, `POST /respec`.
- UI: nuova view `/adventurers/{id}/talents` con visualizzazione DAG (react-flow o SVG).
- Aggiornare Auto-Equip: sommare talent modifiers al score computation.
- **Feature flag `r18_talents_enabled = true` per beta gilde** (10-20 gilde volontarie).
- Testing: playbook end-to-end talent spend + respec + persistence.

### R18.3 — Grade + Tomi + Roster 50 + Class-Bound Hard (3-4 sprint)

**Scope**: identity progression e class-lock.
- Nuovo modulo `app/adventurer_grade/` con formula grade upgrade.
- Nuovo item_type `class_tome`, `training_manual`, `class_switch_seal`.
- Endpoint: `POST /adventurers/{id}/change-class` con validation tomi + materials + dungeon count.
- Class-bound HARD enforce su `POST /equip`.
- Roster 50 attivato con curva `min(50, 8 + guild_level × 2)`.
- UI: pannello identity avventuriero (grade badge, race, biography, history counters).
- Achievement personale per adventurer.
- Testing: full E2E grade Common→Uncommon flow + change-class flow + roster cap.

### R18.4 — PWR Solo-Equip + Dungeon/Raid Rework + PvP Reset (3-4 sprint)

**Scope**: switch definitivo economia PWR + ricalibrazione content.
- Snapshot completo pre-switch.
- Ricalibrazione `recommended_power` per 23 dungeon + 3 raid (formula −30-40% media).
- 3-5 dungeon mid-tier ricalibrati per drop `class_tome`.
- Bridge Raids Lv12-17 (originariamente R17.3 Step 3, ora integrato).
- Endgame Lv15-20 (nuovi 3 dungeon).
- Achievement endgame 10-15.
- PvP season freeze + reset ELO.
- Feature flag `r18_pwr_equip_only = true` global.
- Testing: full regression suite + PvP simulation post-reset.

---

## Risposta esplicita alla domanda del PM

> **"Qual è il modo più sicuro per trasformare Orbus Online nel nuovo sistema (adventurers Common iniziali + scelta classe via addestramento + 15 classi canoniche + talent tree + mastery + tomi + PWR solo equip + item class-bound + grado Common→Legendary + roster 50 + rework dungeon/raid) senza rompere il gioco attuale?"**

### Cosa serve sapere (decisioni PM prerequisite)
1. Numero definitivo classi (14 attuali vs 15 target).
2. Struttura talent tree (rami × tier × talent).
3. Class-bound hard o soft.
4. Formula grade Legendary (variety + counters).
5. Roster curve (formula esatta).
6. Prima scelta classe: forced training o class random + retrain gratis.
7. Tomi: drop-only, craftable, o mix.

### Cosa è già pronto (leverage)
- ✅ 14 classi canoniche catalogate (13 delle quali con adventurers attivi)
- ✅ 33 class_specializations pre-seedate (base talent tier 1)
- ✅ 1673 class_halls con `level` + `unlocked_specializations` (base training_fields)
- ✅ 40 traits con modifier engine (pattern riusabile per talenti)
- ✅ 51 razze catalogate con rarity (base identity)
- ✅ 178 item con `class_tags/recommended_classes/role_tags/stat_tags` (base class-bound)
- ✅ Set support in schema (`set_id`, non ancora usato)
- ✅ Auto-Equip class-aware R16.5.4c + role mapping R17.3 Step 2 E
- ✅ Feature flag pattern (già usato in altri round)
- ✅ Migration snapshot+rollback pattern (round1654c) ripetibile

### Cosa manca (nuovo lavoro)
- ❌ `grade` progression (schema-only, va popolato)
- ❌ `race` propagation su adventurer (0 doc)
- ❌ Talent tree modello dati (DAG multi-tier)
- ❌ Tomi item_type + endpoint change-class
- ❌ Class-bound hard enforce
- ❌ Roster cap esplicito su guild
- ❌ Adventurer identity fields (biography, gender, background)
- ❌ Adventurer history counters (dungeons/raids/pvp per adventurer)
- ❌ Achievement personale per adventurer
- ❌ Training field UI + endpoint

### Rischi (in ordine gravità)
1. 🔴 DB migration 2125 adventurer + 178 item → snapshot obbligatorio
2. 🔴 PWR solo-equip rompe curva dungeon/raid → ricalibrazione + snapshot pre/post
3. 🔴 PvP defense team invalidati → freeze season + reset
4. 🔴 Balance talenti → tier 1-3 stat-only, active abilities deferrite
5. 🟠 Item off-class → gracious migration (deprecated_equip=true)
6. 🟠 Player confusion → respec gratis + comunicazione ricca
7. 🟠 Farming Legendary → diminishing returns + variety

### Ordine sicuro
**R18.1 → R18.2 → R18.3 → R18.4** in questo ordine strict, con feature-flag gate su ogni breaking change. Beta gilde volontarie in R18.2 prima del rollout global R18.3. **NO Big Bang release**: ogni round è deployable e rollbackable indipendentemente.

**Prerequisito assoluto**: snapshot DB completo pre-R18.1 + strategia blue-green (o read-replica) per rollback rapido in caso di regression scoperta post-deploy.

---

## STOP audit

**Round R18.0 audit-only completo. Nessuna modifica DB/codice/seed eseguita.** PM ora legge, decide, e apre R18.1 con scope definitivo.

**Bug critici non-scope R18.0 emersi durante l'audit**: nessuno bloccante.

**Ambiguità di scope**: rimandate al PM come 15 domande bloccanti in sezione 16.

**Firma**: E1 Coding Agent · 2026-07-04T16:10Z
