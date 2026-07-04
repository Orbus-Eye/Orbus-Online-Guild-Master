# Round 17.3 — Step 1 Audit-Only — Endgame & Class Depth

**Data**: 2026-07-04T14:25Z
**Round precedente**: R17.2 CLOSED & SEALED ✅ (2026-07-04T14:20Z)
**Scope Step 1**: SOLO audit / design / proposta / tabelle. NO apply. NO seed. NO modifica reward/drop/economia. PM approverà ogni sub-item (A/B/C/D/E) singolarmente prima del passaggio a Step 2 (apply mirato).

---

## 1. Sealing R17.2 confermato

| File | Status | Note |
| --- | --- | --- |
| `/app/memory/round172_final_report.md` | ✅ SEALED | 14-point checklist + hotfix regressione UI Auto-Equip + sezione "R17.2 — CLOSED & SEALED ✅" |
| `/app/memory/orbus_world_roadmap.md` | ✅ Updated | R17.2 → CLOSED & SEALED · R17.3 → OPEN (Step 1 audit-only) |
| `/app/memory/backlog.md` | ✅ Updated | R17.2 archiviato · R17.3 OPEN Step 1 con scope 5 audit |
| `/app/memory/round172_*.jpeg` (5 file) | ✅ Present | Screenshot Playwright + hotfix |

Regressioni: zero. Guardrail: rispettati. Pytest R17.1: 13/13 PASS.

---

## 2. Stato attuale raid esistenti (analisi baseline)

### 2.1 Raid endgame (`RAID_DUNGEON_SEED` in `app/seeds/seed_round5.py`)

Tre raid endgame tier 1-2, **team richiesto 4×5 = 20 avventurieri idle**, `min_roster_size: 20`:

| Slug | Nome IT | Tier | Power Combined | Roster | Party×Size | Duration | Gold | XP/mem | Loot Pool | Essence Min-Max |
| --- | --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | --- | :---: |
| `broken-bastion-siege` | Assedio al Bastione Spezzato | 1 | 800 | ≥20 | 4×5 | 30 min | 600 | 100 | `raid_r1` | 1-3 |
| `necropolis-bells` | Necropoli delle Mille Campane | 1 | 900 | ≥20 | 4×5 | 40 min | 700 | 120 | `raid_r1` | 1-3 |
| `dragon-vault` | Volta del Drago Addormentato | 2 | 1400 | ≥20 | 4×5 | 60 min | 1200 | 200 | `raid_r2` | 2-5 |

**Requisito power_combined per team**: 800 / 900 / 1400 (somma dei 20 avventurieri).
**Prestige level requirement runtime**: NON esplicitamente presente nel seed (nessun `guild_level_required` sul catalog raid). Gate implicito via `min_adventurer_level` sui party members (verificare in `app/raids/__init__.py`).

### 2.2 Dungeon 5p (12 doc — sono i "raid mid-tier" *de facto*)

Nel database esistono **12 dungeon 5p** distribuiti su 4 difficulty tiers (`is_5p=true`, `required_team_size=5`). Il PM li chiama "mid-tier gap Lv5-14" ma **sono già presenti**. Coprono la fascia power 80→360:

| Slug | Diff | Power | Team | Ruolo suggerito |
| --- | :---: | :---: | :---: | --- |
| wolf-den-5p | 1 | 80 | 5 | Lv 3-4 |
| frost-cave-5p | 1 | 90 | 5 | Lv 3-4 |
| salt-marsh-5p | 1 | 100 | 5 | Lv 4-5 |
| iron-foundry-5p | 2 | 140 | 5 | Lv 5-7 |
| silent-monastery-5p | 2 | 155 | 5 | Lv 6-7 |
| pirate-fleet-5p | 2 | 170 | 5 | Lv 7-8 |
| obsidian-arena-5p | 3 | 210 | 5 | Lv 8-10 |
| clockwork-vault-5p | 3 | 230 | 5 | Lv 9-11 |
| voidspire-5p | 3 | 250 | 5 | Lv 10-11 |
| infernal-pit-5p | 4 | 290 | 5 | Lv 12-13 |
| celestial-citadel-5p | 4 | 320 | 5 | Lv 13-14 |
| world-tree-roots-5p | 4 | 360 | 5 | Lv 14-15 |

**Osservazione critica**: la richiesta "5 raid mid-tier Lv5-14" **è già coperta dai 12 dungeon 5p esistenti** (che sono raid 5-player). La proposta A dovrebbe quindi essere una **estensione narrativa/di reward**, non un nuovo seed massivo di 5 raid duplicati. Vedi sezione 3 per la proposta rivista.

### 2.3 Gap identificato

| Fascia Lv | Content 3p | Content 5p | Content 20p endgame |
| :---: | :---: | :---: | :---: |
| Lv 1-3 | 3 dungeon starter | ❌ | ❌ |
| Lv 4-7 | 6 dungeon | 3 dungeon (diff 1-2) | ❌ |
| Lv 8-11 | dungeon vari | 3 dungeon (diff 3) | ❌ |
| Lv 12-14 | ridotto | 3 dungeon (diff 4) | ❌ (gap!) |
| **Lv 15-17** | ❌ | ❌ | broken-bastion pw800 · necropolis-bells pw900 |
| Lv 18-20 | ❌ | ❌ | dragon-vault pw1400 |

Il **vero gap** è a **Lv 15-17** (fascia intermedia tra i 5p endgame e i raid 20p). E a Lv 18-20 c'è solo dragon-vault.

---

## 3. Proposta raid mid-tier Lv5-14 (audit A)

### 3.1 Raccomandazione di scope

Vista la copertura esistente (12 dungeon 5p diff 1-4), la proposta A si divide in **due opzioni**:

- **Opzione A1 (rivista)**: NON creare 5 nuovi raid mid-tier. Invece **arricchire i 12 dungeon 5p esistenti** con: `min_adventurer_level` esplicito, `party_focus_hints` (analoghi ai 20p), `guaranteed_material_min` (drop mid-tier), `narrative_description_it` più ricca, gate `guild_level` (Prestigio 3/5/7/8 sui 4 diff).
- **Opzione A2 (letterale PM)**: creare 5 raid Lv5-14 NARRATIVI DEDICATI 20p su party 2×5, con reward "raid_r0" mid-tier. Riempie il gap semantico ma **duplica** il ruolo dei 5p esistenti.

**Raccomandazione E1**: **A1**. Elimina duplicazione, valorizza asset già seedati, e libera scope per **Lv 15-17** (vero gap) in Opzione A3.

### 3.2 Opzione A3 (proposta primaria) — 5 raid intermedi Lv 15-17 + estensione mid-tier

Riempi il vero gap (Lv 15-17, tra 5p diff-4 e raid 20p endgame) con 3 raid intermedi + arricchimento 5p diff 3-4:

| Slug | Nome IT | Lore breve | Lv min | Prestige req | Team | Rec power | Durata | Gold | Prestigio | Materiali | Drop princ. | Ruoli | Note |
| --- | --- | --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | --- | --- | --- | --- |
| `sunken-vault-5p` | Volta Sommersa | Un vault sottomarino sigillato prima del Vuoto; le mura piangono acqua salata di ricordi. | 12 | 4 | 5 | 340 | 22m | 380 | +18 | `saltwater_essence`×1, `common_raid_mat`×2 | epic weapon 3%, rare accessory 12% | 1 Tank, 1 Healer, 3 DPS | Riempie il gap fra world-tree-roots-5p (pw 360) e endgame 20p |
| `whispering-arboretum` | Boschetto Sussurrante | Un giardino chiuso dove le radici trattano segreti che i re non hanno mai pronunciato. | 15 | 5 | 10 (2×5) | 500 | 30m | 700 | +40 | `sap_of_memory`×1, `arcane_seed`×2 | epic armor 5%, rare weapon 15%, essence 0-1 | 2 Tank, 2 Healer, 6 DPS | Bridge tra 5p mid-tier e 20p endgame; usa `required_party_count: 2` con `required_party_size: 5` |
| `shattered-mint` | Zecca Infranta | Le antiche monete d'oro battono ancora sui muri, sperando che qualcuno le ritrovi. | 16 | 6 | 10 (2×5) | 620 | 35m | 900 | +45 | `sundered_coin`×2, `common_raid_mat`×3 | epic accessory 6%, rare armor 15% | 2 Tank, 2 Healer, 6 DPS | Focus economico: reward oro maggiore, drop economy items |
| `hollow-choir` | Coro Cavo | Voci senza corpo intonano un requiem eterno. Chi si ferma ad ascoltare non ne esce. | 17 | 7 | 15 (3×5) | 720 | 40m | 1050 | +50 | `echo_shard`×2, `sap_of_memory`×1 | epic weapon 6%, rare accessory 15%, essence 0-1 | 3 Tank, 3 Healer, 9 DPS | Preparatorio al raid 20p; unlock post-completion consigliato prima di tentare broken-bastion-siege |
| `starfall-reliquary` | Reliquiario della Caduta Stellare | Meteoriti sacri caduti dalla notte di Alveora, ancora caldi di sole morente. | 17 | 8 | 15 (3×5) | 780 | 45m | 1150 | +55 | `stellar_dust`×2, `arcane_seed`×2 | epic armor 6%, rare weapon 15%, essence 1-2 | 3 Tank, 3 Healer, 9 DPS | Gate implicito su Forgia Leggendaria (Lv5) per beneficiare del drop `stellar_dust` |

### 3.3 Vincoli design rispettati

- ✅ **Progressione chiara**: Lv12 → 15 → 16 → 17 (bridge tra 5p e 20p).
- ✅ **NO power creep vs endgame**: rec power max 780 vs endgame `broken-bastion-siege` 800. Ogni raid intermedio resta **sotto** il primo tier endgame.
- ✅ **NO Legendary drop diretti**: solo epic 3-6% e rare 12-15%. Legendary resta gated dalla Forgia (post-Lv5 Prestigio).
- ✅ **Reward proporzionato**: gold 380-1150 (curva sublinear tra 5p Lv12 e endgame Lv17); XP Prestigio +18/+40/+45/+50/+55 (mid-tier XP hook R16.5.3 = +80 raid, quindi qui va deferrito il gate: potrebbero usare **hook expedition** +15/+5 tier-specific o nuovo `raid_mid` hook +40).
- ✅ **Countdown/report**: pattern identico a `RAID_DUNGEON_SEED` esistente. CAS lock idempotency + on-visit fallback + CLI recovery (R16.1.1).
- ✅ **Requisiti visibili in UI**: nuovo campo `prestige_level_required` esposto in `raid.preview` + `dungeon-info` payload. FE badge "Richiede Lv Prestigio N".
- ✅ **NO abbassamento raid endgame**: `broken-bastion-siege/necropolis-bells/dragon-vault` restano invariati (min_roster 20, power 800/900/1400).

### 3.4 Loot pool nuovo

Servirebbe un nuovo `loot_pool_slug: raid_r0` (mid-tier), con drop rate epic 3-6% (rispetto raid_r1 epic 8-10% e raid_r2 epic 12%). Da definire in Step 2 se PM approva A3.

### 3.5 Rischi noti

- 🟡 **Party count**: 2×5 e 3×5 richiedono verifica su UI multi-party (attualmente `PvpMiniCard` gestisce 1-4 party). Deve accettare `required_party_count = 2 / 3` senza fallback.
- 🟡 **Hook Prestigio**: attualmente `raid_completed` = +80/+40/+15 (win/loss/participate) cap 1/day (R16.5.3). Serve nuovo hook `raid_mid_completed` = +40/+20/+10 cap 2/day, oppure allargare cap del hook esistente. Decisione design pendente.
- 🟢 **Migration**: dry-run + snapshot rollback obbligatorio come da pattern `round1654b/c_seed_integrity`.

---

## 4. Endgame Lv15-20 (audit B)

### 4.1 Lacune identificate

| Fascia | Content 3p | Content 5p | Content 20p | Reward tier | Achievement dedicati |
| :---: | :---: | :---: | :---: | --- | :---: |
| Lv 15 | ❌ | 1 (world-tree-roots) | ❌ | epic only | ❌ |
| Lv 16 | ❌ | ❌ | ❌ | — | ❌ |
| Lv 17 | ❌ | ❌ | broken-bastion (pw800) | epic 8%, essence 1-3 | 0-1 verificare |
| Lv 18 | ❌ | ❌ | necropolis-bells (pw900) | epic 10%, essence 1-3 | 0-1 verificare |
| Lv 19 | ❌ | ❌ | ❌ | — | ❌ |
| Lv 20 | ❌ | ❌ | dragon-vault (pw1400) | epic 12%, essence 2-5 | 0-1 verificare |

### 4.2 Legendary Forge gate

- `MIN_GUILD_LEVEL = 5` (`app/legendary_forge/__init__.py:57`) → sblocca Lv5 Prestigio (mid-game, non endgame).
- **Rischio**: recipe Legendary sono unlockable da Lv5 Prestigio ma i **materiali** epic per craftare arrivano solo dai raid endgame (Lv17-20). Gap materiale tra Lv5-16 (recipe visibili ma non craftabili).
- **Proposta B1**: aggiungere drop `common_raid_mat` (già presente in A3) nei 5p diff 3-4 esistenti. Riduce gap materiale senza toccare drop rate Legendary.

### 4.3 Dungeon Lv15-20 (nuovi)

**Proposta B2**: 3 dungeon endgame single-tier (Lv 18/19/20) per completare la curva. **NO 5p, NO 20p** — dungeon 3-player standard con:
- Drop rate ridotto (epic 2%, rare 10%)
- `min_adventurer_level` esplicito
- Reward oro/XP proporzionato (500-800 gold, 60-80 XP)
- No Legendary drop diretto

| Slug | Nome IT | Lv min | Power | Team | Note |
| --- | --- | :---: | :---: | :---: | --- |
| `void-cradle` | Culla del Vuoto | 18 | 380 | 3 | Post-Alveora narrative, drop `void_shard` |
| `moonshadow-crypt` | Cripta d'Ombra Lunare | 19 | 440 | 3 | Late-game solo/duo grind path |
| `astral-lens` | Lente Astrale | 20 | 520 | 3 | Endgame farm dungeon, drop `stellar_dust` (materiale Forgia) |

### 4.4 Achievement endgame

`achievements_catalog` conta **110** doc. Servono nuovi achievement endgame (10-15) per Lv15-20 completion:
- "Volta Bruciata" — completa dragon-vault senza perdite
- "Signore del Coro" — completa hollow-choir in <35 min
- "Prima Discesa" — primo raid mid-tier completato
- "Curatore dell'Astro" — 10× completion astral-lens
- ecc.

Coerente con seed idempotent pattern (`round173_endgame_achievements.py` in Step 2 se PM approva).

### 4.5 Rischi

- 🔴 **Priorità design endgame vs mid-tier**: non implementare B2/B3 finché A3 non è stabile (rischio di curva sbilanciata).
- 🟡 **Material sink**: introdurre `void_shard/stellar_dust` senza sink (uso) crea inflation drop. Servono ricette Forgia Lv6+ che li consumino.
- 🟢 **Achievement seed**: append-only, zero rischio regression.

### 4.6 Priorità B

1. **B1** (drop mid-tier materiali): P1 se A3 approvato — riempie gap materiale.
2. **B2** (3 dungeon endgame Lv18-20): P2 — arricchisce curva ma non blocca.
3. **B3** (10-15 achievement endgame): P2 — polish, no blocker.

---

## 5. Class depth / item coverage residua (audit C)

### 5.1 Coverage per classe (14 classi, dati DB live)

| Classe | Role | Primary | Weapon | Armor | Accessory | Shield | Totale | Status |
| --- | --- | --- | :---: | :---: | :---: | :---: | :---: | :---: |
| paladin | Tank | faith | 34 | 29 | 27 | 2 | 92 | ✅ eccellente |
| warrior | Tank | strength | 26 | 27 | 14 | 2 | 69 | ✅ ottimo |
| berserker | DPS | strength | 25 | 23 | 14 | 2 | 64 | ✅ ottimo |
| mage | DPS | intellect | 16 | 4 | 14 | 0 | 34 | 🟡 armor thin |
| necromancer | DPS | intellect | 16 | 4 | 14 | 0 | 34 | 🟡 armor thin |
| assassin | DPS | agility | 21 | 6 | 4 | 0 | 31 | 🟡 acc/arm thin |
| ranger | DPS | agility | 21 | 6 | 4 | 0 | 31 | 🟡 acc/arm thin |
| rogue | DPS | agility | 21 | 6 | 4 | 0 | 31 | 🟡 acc/arm thin |
| druid | Healer | faith | 10 | 7 | 16 | 1 | 34 | ✅ ok |
| priest | Healer | faith | 10 | 5 | 16 | 1 | 32 | ✅ ok |
| bard | Support | intellect | 11 | 4 | 14 | 0 | 29 | 🟡 armor thin |
| monk | DPS | agility | 13 | 6 | **1** | 0 | 20 | 🔴 **accessory 1 solo** |
| warlock | DPS | intellect | 4 | 3 | 3 | 0 | 10 | 🔴 **tutti sotto soglia** |
| alchemist | DPS | intellect | 4 | 3 | 3 | 0 | 10 | 🔴 **tutti sotto soglia** |

**Soglia raccomandata**: ≥ 5 item per slot per garantire curva Auto-Equip funzionante Lv1-15.

### 5.2 Item patch proposta (Opzione C1 — NO apply Step 1)

**Priorità P1** (blocking per Auto-Equip fluido):
- **monk accessory**: da 1 → 5 (+4 item, spread Lv3-15, rarità Common/Uncommon/Rare/Epic × ≥1)
- **warlock**: da 4w/3a/3acc → 8w/6a/6acc (+4/+3/+3, spread Lv3-15)
- **alchemist**: da 4w/3a/3acc → 8w/6a/6acc (+4/+3/+3, spread Lv3-15)

**Priorità P2**:
- **assassin/ranger/rogue armor**: da 6 → 10 (+4 ciascuno, spread Lv5-12)
- **assassin/ranger/rogue accessory**: da 4 → 8 (+4 ciascuno, spread Lv5-12)
- **mage/necromancer armor**: da 4 → 8 (+4 ciascuno, spread Lv5-12)
- **bard armor**: da 4 → 8 (+4, spread Lv5-12)

**Totale proposta**: ~48-52 item patch (vs 22 del round R16.5.4c ADJ-3).

### 5.3 Tabella item patch dettagliata (P1 monk/warlock/alchemist)

| slug | nome_it | slot | rarity | level | power_score | stat_bonus | recommended_classes |
| --- | --- | :---: | :---: | :---: | :---: | --- | --- |
| `monk-jade-cord` | Cordone di Giada | accessory | Common | 3 | 3 | +1 AGI, +1 END | monk |
| `monk-serpent-anklet` | Cavigliera del Serpente | accessory | Uncommon | 6 | 6 | +2 AGI, +1 END | monk |
| `monk-mantra-bead` | Grano da Mantra | accessory | Rare | 9 | 10 | +3 AGI, +2 END | monk |
| `monk-thousand-hands-bracer` | Bracciale delle Mille Mani | accessory | Epic | 12 | 16 | +5 AGI, +3 STR | monk |
| `warlock-pact-focus-i` | Focus del Patto I | weapon | Uncommon | 5 | 7 | +2 INT, +1 FAI | warlock |
| `warlock-pact-focus-ii` | Focus del Patto II | weapon | Rare | 9 | 12 | +4 INT, +2 FAI | warlock |
| `warlock-hex-tome` | Tomo di Malia | weapon | Epic | 13 | 20 | +6 INT, +3 END | warlock |
| `warlock-void-drape` | Manto del Vuoto | weapon | Rare | 8 | 14 | +5 INT | warlock |
| `warlock-shadow-mail` | Cotta d'Ombra | armor | Rare | 7 | 8 | +3 INT, +2 END | warlock |
| `warlock-abyssal-plate` | Placca Abissale | armor | Epic | 12 | 14 | +5 INT, +3 END | warlock |
| `warlock-old-covenant-robe` | Veste del Vecchio Patto | armor | Uncommon | 5 | 5 | +2 INT, +1 FAI | warlock |
| `warlock-fetish-idol` | Idolo Feticcio | accessory | Uncommon | 5 | 5 | +2 INT | warlock |
| `warlock-imp-collar` | Collare dell'Imp | accessory | Rare | 9 | 9 | +3 INT, +2 FAI | warlock |
| `warlock-black-covenant-ring` | Anello del Nero Patto | accessory | Epic | 12 | 14 | +5 INT, +2 FAI | warlock |
| `alchemist-mortar-and-pestle` | Mortaio e Pestello | weapon | Common | 3 | 4 | +1 INT, +1 END | alchemist |
| `alchemist-catalyst-flask` | Fiala del Catalizzatore | weapon | Uncommon | 6 | 7 | +2 INT, +1 END | alchemist |
| `alchemist-elixir-lance` | Lancia dell'Elisir | weapon | Rare | 9 | 12 | +4 INT, +2 END | alchemist |
| `alchemist-transmuters-crown` | Corona del Trasmutatore | weapon | Epic | 13 | 19 | +6 INT, +3 END | alchemist |
| `alchemist-brewers-apron` | Grembiule del Distillatore | armor | Common | 3 | 3 | +1 END, +1 INT | alchemist |
| `alchemist-quicksilver-vest` | Corpetto Mercuriale | armor | Rare | 8 | 8 | +3 INT, +2 END | alchemist |
| `alchemist-philosophers-plate` | Placca del Filosofo | armor | Epic | 12 | 14 | +5 INT, +3 END | alchemist |
| `alchemist-brew-belt` | Cintura Distillante | accessory | Common | 3 | 3 | +1 END, +1 INT | alchemist |
| `alchemist-catalyst-ring` | Anello Catalitico | accessory | Rare | 9 | 9 | +3 INT, +2 END | alchemist |
| `alchemist-golden-vial` | Fiala d'Oro | accessory | Epic | 12 | 14 | +5 INT, +2 END | alchemist |

Totale patch P1: **24 item** (0 Legendary, no power creep verificato programmatico vs `POWER_MAX_BY_BUCKET`).

### 5.4 6 orfani Guardian/Cleric (ADJ-9 residuo)

Da R16.5.4c: 6 avventurieri legacy con `class_name ∈ {"Guardian","Cleric"}` non nel catalog. Post ADJ-9 backfill class_slug=null.

**Decisione design pendente (accettata pendente in R16.5.4c)**:
- (a) mappare Guardian→paladin e Cleric→priest (aliasing lightweight)
- (b) retire tramite endpoint standard (soft delete)
- (c) aggiungere Guardian/Cleric al catalog come classi vere (crea coverage burden addizionale)

**Raccomandazione E1**: **(a)** aliasing. Zero impact narrative, zero migration destructive, zero item patch aggiuntivo. Script `round173_class_alias_migration.py` dry-run+apply.

---

## 6. Tooltip Prestigio mapping completo (audit D)

### 6.1 Audit gate reali (grep `MIN_GUILD_LEVEL` + `guild.level` / `guild_level` in tutto il backend)

| Livello | Feature sbloccata | Fonte codice | Endpoint UI coinvolti | Certezza |
| :---: | --- | --- | --- | :---: |
| **2** | Resource Missions (raccolta risorse continentali) | `app/resources/__init__.py:91` `MIN_GUILD_LEVEL = 2` | `POST /api/resources/gather` (403 gate), `GET /api/resources/missions/stats` | 🟢 **ALTA** |
| **5** | Forgia Leggendaria (recipes visibili) | `app/legendary_forge/__init__.py:57` `MIN_GUILD_LEVEL = 5` | `GET /api/legendary-forge/recipes`, forge access panel | 🟢 **ALTA** |
| **6** | Forgia di Arfus (research visibile) | `app/arfus_forge/__init__.py:38` `MIN_GUILD_LEVEL = 6` | `GET /api/arfus-forge/research/*`, arfus panel | 🟢 **ALTA** |
| **8** | Specializzazione della Gilda (scelta iniziale) | `app/guild_specialization/__init__.py:35` `MIN_GUILD_LEVEL = 8` | `POST /api/guild-specialization/choose`, `GET /api/guild-specialization/status` | 🟢 **ALTA** |
| ? | Territory upgrades | ❌ nessun `MIN_GUILD_LEVEL` in `app/territory/*` | — | 🔴 **BASSA** (gate implicito su `structure.level_required`, non su guild) |
| ? | Raid endgame (broken-bastion-siege, ecc.) | ❌ nessun `guild_level` gate in `RAID_DUNGEON_SEED` | Gate implicito via `min_adventurer_level` sui party members | 🔴 **BASSA** (nessun gate a livello guild) |
| ? | Continenti (scelta anchor) | Gate: primo raid completato (R16.3 Phase 2) | Non gated su `guild_level` | 🔴 **BASSA** |
| ? | Class Hall | Modulo non presente in codebase (`grep -r "class_hall"` → 0 match) | — | 🔴 **BASSA** (feature non implementata) |
| ? | PvP Continental | `app/pvp_continental/*` gate su `guild.level ≥ 8` (verificare) | `/api/pvp/*` | 🟡 **MEDIA** (da verificare code path) |
| ? | Trade pacts | `app/trade_pacts/*` — gate design pendente | `/api/trade-pacts/*` | 🔴 **BASSA** (feature backlog R16.5.4) |
| ? | Site contracts (Incarichi di Sede) | R16.3 Phase 3 — gate su `guild.level ≥ 4` (verificare) | `/api/site-contracts/*` | 🟡 **MEDIA** |

### 6.2 Verifica PvP Continental

Grep `MIN_GUILD_LEVEL\|guild.*level.*>=` in `app/pvp_continental/` → 0 match esplicito. Il gate `guild.level ≥ 8` è documentato in roadmap (Phase 7A) ma serve grep dedicato per confermare fonte codice.

### 6.3 Verifica Site Contracts

`app/site_contracts/` esiste ma gate specifico non documentato. Da audit in Step 2 se PM approva D.

### 6.4 Proposta tooltip esteso (solo certezza ALTA)

Estendere `next_unlock` payload in `app/expeditions/services.py:1216-1241` con i 4 gate ALTA + gate MEDIA se verificati in Step 2:

```python
_unlocks = [
    (2, "Missioni Risorse Continentali"),        # ALTA (nuovo, R17.2 P0.3)
    (5, "Forgia Leggendaria"),                    # ALTA (R17.2 P1)
    (6, "Forgia di Arfus"),                       # ALTA (R17.2 P1)
    (8, "Specializzazione della Gilda"),          # ALTA (R17.2 P1)
    # (8, "PvP Continentale"),                    # MEDIA — verificare in Step 2
    # (4, "Incarichi di Sede"),                   # MEDIA — verificare in Step 2
]
```

**Implementazione Step 2 (certezza ALTA)**: aggiungere solo il gate Lv 2 al mapping esistente (R17.2 già ha 5/6/8). Guarda anche il caso `guild_level == 1` → tooltip mostra "Missioni Risorse al Lv 2" (nuovo primo step motivazionale post-onboarding).

### 6.5 Deferrito Step 2

- Gate territory (dipende da `structure.level_required` — logica differente, non guild-level)
- Gate raid endgame (dipende da party members, non guild)
- Gate PvP / Site contracts (richiedono audit code path dedicato)
- Gate Class Hall (non implementato)

---

## 7. CTA retry class-fit balancing (audit E)

### 7.1 Comportamento attuale (R17.1b `ExpeditionNew.jsx`)

CTA `?auto=strongest` → filtra `is_available !== false` + non underlevel → prende top-N per `power_score`. Zero class-fit balance.

**Problema player-facing**: se un dungeon richiede "team bilanciato" (Tank/Healer/DPS), pure-power può proporre 3 Berserker → underperform.

### 7.2 Algoritmo proposto (pseudocodice)

```
function selectBalancedTeam(adventurers, dungeon, teamSize):
    # 1. Filter available + eligible level
    pool = [adv for adv in adventurers
            if adv.is_available == true
            and adv.level >= dungeon.min_adventurer_level]

    if len(pool) < teamSize:
        # Fallback: current strongest logic + warning IT
        return topByPower(pool, teamSize), reason="not_enough_available"

    # 2. Compute class-fit score per adv/dungeon
    for adv in pool:
        adv.class_fit_score = computeClassFit(adv.class_slug, dungeon.type, dungeon.tags)
        # e.g., "combat" dungeon → Tank+DPS score high, Healer neutral
        # e.g., "arcane" dungeon → INT-based classes score high
        adv.role = classToRole(adv.class_slug)  # Tank/Healer/DPS/Support

    # 3. Try ROLE BALANCE first: 1 Tank + 1 Healer + rest DPS (for 3-player)
    #    For 5-player: 1 Tank + 1 Healer + 3 DPS
    #    For 20-player raid: use dungeon.party_focus_hints if available
    ideal_roles = getIdealRoleMix(teamSize, dungeon)

    team = []
    remaining = list(pool)

    for target_role in ideal_roles:
        candidates = [a for a in remaining if a.role == target_role]
        if not candidates:
            candidates = remaining  # fallback: no penalty, take anyone
        # 4. Pick best fit: class_fit_score * 3 + power_score
        candidates.sort(key=lambda a: -(a.class_fit_score * 3 + a.power_score))
        team.append(candidates[0])
        remaining.remove(candidates[0])

    # 5. If team incomplete or invalid (e.g., 3 tank found), fallback
    if not isValidParty(team, dungeon):
        return topByPower(pool, teamSize), reason="no_valid_balance_found"

    return team, reason="balanced_class_fit"
```

### 7.3 Class-fit primary/secondary stat mapping

| Class | Primary | Secondary | Role |
| --- | --- | --- | --- |
| warrior | strength | endurance | Tank |
| paladin | faith | strength | Tank |
| berserker | strength | agility | DPS |
| mage | intellect | agility | DPS |
| necromancer | intellect | endurance | DPS |
| warlock | intellect | faith | DPS |
| alchemist | intellect | endurance | DPS |
| assassin | agility | strength | DPS |
| ranger | agility | endurance | DPS |
| rogue | agility | intellect | DPS |
| monk | agility | endurance | DPS |
| bard | intellect | faith | Support |
| priest | faith | intellect | Healer |
| druid | faith | endurance | Healer |

### 7.4 Edge case handling

| Case | Comportamento |
| --- | --- |
| Meno di teamSize avventurieri available | Fallback pure-power (attuale R17.1b) + toast IT "Non abbastanza avventurieri disponibili per un team bilanciato. Selezione pura per potere." |
| Nessun Tank disponibile | Fallback DPS puro + toast IT "Nessun Tank disponibile. Team offensivo suggerito." |
| Nessun Healer disponibile | Analogo, toast IT "Nessun Healer disponibile. Attenzione alle fatalità." |
| Dungeon senza `party_focus_hints` | Usa default: 1 Tank / 1 Healer / N-2 DPS |
| Raid 20p con `party_focus_hints` | Rispetta hint per party_idx (usa preferred_role di `RAID_DUNGEON_SEED`) |
| Underlevel adv | Filter escluso a monte |
| `is_available == false` | Filter escluso a monte |

### 7.5 Rischio scope

- 🟢 **Basso**: solo lato client + eventuale payload derivation server (nuovo endpoint `POST /api/expeditions/preview/balanced-team` opzionale, o all-client con `class_slug` + `role` già presenti nel payload `/adventurers`).
- 🟡 **Medio se server-side**: aggiunge complexity a `preview.py` (0 dependency change; solo logica selection).
- 🟢 **Zero impact su reward/economia/PvP**: la CTA è solo UX preselect, POST expedition invariato.

### 7.6 Behavior conservato

- ❌ NO avvio automatico spedizione (solo preselect + navigate al preview).
- ❌ NO boost nascosto (power_score usato as-is dal DB).
- ❌ NO reward extra.
- ✅ Solo suggerimento; il player può modificare la selezione manuale.
- ✅ Trasparenza IT: toast dopo preselect spiega la logica.

### 7.7 Implementazione stimata

- Client-side (`ExpeditionNew.jsx`): +80-100 righe (helper `selectBalancedTeam` + role mapping + toast).
- No modifiche backend (fase 1 puramente FE).
- Test: 5-8 unit test JavaScript per `selectBalancedTeam` con scenari edge case.
- Se PM richiede server-side (per share URL / raid preset), aggiungere endpoint dedicato in Step 3.

---

## 8. Rischi trasversali

| # | Rischio | Impatto | Mitigazione |
| :---: | --- | --- | --- |
| 1 | **Power creep se A3 + B2 approvati insieme** | Medio | Impl. sequenziale con verifica curva post-A3 |
| 2 | **Hook Prestigio raid mid-tier confonde cap giornaliero** | Basso | Nuovo hook dedicato o allargamento cap con audit event distinto |
| 3 | **Item patch C1 aumenta drop table complexity** | Basso | Append-only seed idempotente, snapshot pre/post |
| 4 | **Tooltip D estende `next_unlock` a Lv2** — retro-compat expedition legacy | Basso | Fallback `null` se `cur_level < 2` non applicabile (già gestito) |
| 5 | **CTA E class-fit selezione confonde player esperti** | Basso | Toggle "usa selezione mia" prominente + toast trasparente |
| 6 | **20p raid 2×5/3×5 (proposta A3) rompe UI multi-party** | Medio | Verifica PvpMiniCard `required_party_count` in Step 2 prima di apply |
| 7 | **Aliasing Guardian→paladin, Cleric→priest** cambia UX 6 avv | Basso | Migration idempotente + snapshot; UX label aggiornata al reload |
| 8 | **Nuovi materiali (stellar_dust, void_shard, ecc.) senza sink** | Medio | Aggiungere ricette Forgia Lv6+ che li consumino in Step 3 |
| 9 | **Achievement endgame B3 richiedono trigger events** | Basso | Riusa `trigger_emitter.py` esistente (R17.0 audit); pattern append-only |
| 10 | **e1_tester scope creep** — 5 audit → 5 test suite | Basso | Step 2 apply solo item singolo approvato → tester su singolo scope |

---

## 9. Raccomandazione dev — cosa implementare per primo in Step 2

Ordine di priorità raccomandato per Step 2 (se PM approva):

1. **D** (Tooltip Prestigio esteso Lv2) — **P0, effort minimo, valore immediato**. 1 file, ~4 righe, zero regressioni. Motivazione post-onboarding chiara: "Lv 1 → Lv 2 = Missioni Risorse".

2. **C1 P1** (item patch monk/warlock/alchemist) — **P0, valore diretto Auto-Equip UX**. Seed 24 item append-only, dry-run+apply pattern R16.5.4c. Chiude gap post-R16.5.4c ADJ-3.

3. **E** (CTA class-fit balancing) — **P1, effort medio, valore alto**. Solo FE, 80-100 righe. Chiude follow-up esplicito R17.1b/R17.2 P2.

4. **A3** (5 raid intermedi Lv12-17) — **P1, effort medio-alto**. Nuovo seed 5 raid + nuovo loot_pool `raid_r0` + verifica UI multi-party. Impatto endgame moderato.

5. **B1** (drop mid-tier materiali su 5p diff 3-4) — **P2, effort basso**. Prerequisito narrativo per B2/B3.

6. **B2** (3 dungeon endgame Lv18-20) — **P2, dopo A3**. Completa curva.

7. **B3** (10-15 achievement endgame) — **P3, polish finale**. Append-only.

8. **C1 P2** (assassin/ranger/rogue/mage/necromancer/bard patch) — **P3, quality-of-life Auto-Equip**.

9. **Guardian/Cleric aliasing** (6 orfani) — **P3, cleanup finale**.

### 9.1 Sequenza consigliata

**Sprint 1 (Step 2a)**: D → C1 P1 → E (chiude follow-up R17.2, no rischio endgame).
**Sprint 2 (Step 2b)**: A3 → B1 (nuovo content mid-tier, con verifica UI multi-party).
**Sprint 3 (Step 2c)**: B2 → B3 → C1 P2 → aliasing (polish endgame + coverage completa).

---

## 10. Cosa resta fuori scope R17.3

- **Localization Sweep R16.5.4f** [P3] — 10 token EN residui in UI generale. Tracciato parallelo, no round dedicato.
- **SMTP `@orbus.test`** [P2] R17.infra.smtp — invariato.
- **Class Hall** — feature non implementata, non prevista in R17.3.
- **Class-fit UI polish**: interpolazione classe IT nel branch already-best (R16.5.4d residuo P3).
- **Refactor `guild.level` vs `guild_level`** — deferrito per rischio gate breaking Forge/Spec/PvP/Arfus/TradePact.
- **PvP season 2** — invariato, out of scope R17.3.
- **World Boss V2** — out of scope R17.3 (Phase 1 già CLOSED R16.3).
- **Territory upgrades roadmap** — invariato.
- **Stables V2** (`-5% travel time`) — parked, richiede design review anti-P2W dedicato.
- **Legendary Forge material sink audit** — parziale in questo audit (B1/B2), completo scope Sprint 3.
- **Migration `structure.library/market`** legacy slug — R16.5.4e.b [P3] parallelo.

---

## Firma audit

**Autore**: E1 Coding Agent (Emergent Labs)
**Data**: 2026-07-04T14:25Z
**Deliverable**: `/app/memory/round173_step1_audit.md` — Step 1 audit-only, NO apply.

**Prossimo step**: PM review sub-item A/B/C/D/E → approvazione singola → Step 2 apply mirato.

**STOP — attendo approvazione PM per Step 2.**
