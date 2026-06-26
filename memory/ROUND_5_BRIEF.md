# ROUND 5 — Expedition Expansion + Team Size 5 + Solo Raids
## Phase 0 — AUDIT BRIEF (no implementation)

> **Status**: AUDIT ONLY. No code in repo. Awaiting user decisions on 7 open
> questions before scaffolding Phase 17.5 → 19.
>
> **Hard constraints (ribaditi)**:
> - ❌ NO raid Consorzio / cooperative / PvP / world boss
> - ❌ NO modifiche ALLOWLIST / cleanup leaderboard / hard delete
> - ❌ NO Mythic / nuove rarità / premium boost / P2W
> - ❌ NO real-money item purchase
> - ✅ Migrazioni additive/idempotenti
> - ✅ Backward-compat expedition storiche da 3
> - ✅ Forge/equip/bound ROUND 4 non regresso
> - ✅ STOP dopo preview, NO deploy prod senza validazione utente

---

## §A — Audit Expedition model

### A.1 Team-size enforcement (DOVE è hardcoded?)
**Risultato sorprendente: il modello attuale è già parametrico.**

Il campo `required_team_size` è una colonna del documento `dungeons` (int 1-10).
Il frontend e il backend leggono SEMPRE da lì. L'unico hardcode di "3" è nei
**seed** e nei **valori di default** quando il documento non lo specifica.

Posizioni esatte:

| File | Riga | Tipo |
|---|---:|---|
| `backend/app/expeditions/preview.py` | 88 | `dungeon.get("required_team_size", 3)` → DEFAULT FALLBACK |
| `backend/app/expeditions/services.py` | 439, 497 | Read da `dungeon["required_team_size"]` — OK |
| `backend/app/expeditions/schemas.py` | 14 | `adventurer_ids: list[str] = Field(min_length=1, max_length=10)` — OK |
| `backend/app/seeds/seed_data.py` | 172, 183, 194, 210, 222, 235, 247, 259, 272 | `"required_team_size": 3` — SEED (10 dungeon) |
| `frontend/src/pages/ExpeditionNew.jsx` | 90 | `dungeon?.required_team_size ?? 3` — DEFAULT FALLBACK |
| `frontend/src/pages/Admin.jsx` | 286 | `required_team_size: 3` (create form default) |

✅ **CONCLUSIONE A.1**: nessuna modifica strutturale necessaria al modello dati
o agli endpoint. Basta seedare i nuovi dungeon con `required_team_size: 5` e
opzionalmente alzare i defaults da 3 a 5 per i NUOVI dungeon (mantenendo i 10
storici a 3 per back-compat).

### A.2 Endpoint expedition esistenti

| Endpoint | Validazione team size | Note |
|---|---|---|
| `GET /api/dungeons` | n/a | Espone `required_team_size` per dungeon |
| `POST /api/expeditions/preview` | Da `required_team_size` | `preview_expedition` |
| `POST /api/expeditions/start` | Da `required_team_size` | `_dispatch_expedition` |
| `POST /api/expeditions/{id}/complete` | n/a (membri già fissati) | |
| `GET /api/expeditions` | n/a | Lista history |
| `GET /api/expeditions/{id}` | n/a | Report con `team_size = len(members)` |
| `GET /api/expeditions/last-completed` | n/a | |

✅ Tutto già pronto a team variabile.

### A.3 Formula success_chance (sources of truth)

```
team_power = Σ(per-member contribution) + role bonuses
  per-member = total_power_snapshot (Phase 6+)
             = sum(stats) + level*2  (fallback)
  role bonuses = +5 Tank/+5 Healer/+5 DPS + 10 se tutti e 3 presenti

success_chance = clamp(50 + (team_power - recommended_power), MIN=5, MAX=95)
```

**Esempio numerico (oggi, team da 3, T1 goblin-warrens rec=45)**:
- 3 adventurer L1 base (stats medie 8/8/8/8/8 → power=42 cad → 126 team)
- + 10 bonus comp completa = 136 → 50 + (136-45) = +91 → **clamped a 95%**.
- Già oggi un team L1 ben formato ottiene 95% in T1. **Soffitto basso.**

**Esempio numerico (oggi, team L5 T3 storm-spire rec=88)**:
- 3 advL5 ben statted (power 70 cad) → 210 team + 25 comp = 235
- 50 + (235-88) = +197 → clamp 95%. **Soffitto facilmente saturato.**

🚨 Conseguenza diretta: la formula attuale è **lineare e clampata stretta**.
Passando a team 5 con power medio cresciuto da Forge/refinement/set, il
ceiling 95% diventa **irraggiungibile-da-perdere**. Servono dungeon T4 elite
con `recommended_power` molto più alto (es. 250-350) per riportare la curva
sotto al massimo.

### A.4 Injury, fatigue, loot
- **Injury risk** (`preview._injury_risk`): basato su delta team/recommended,
  shift +5 per Tank e +5 per Healer. 3 livelli: high/medium/low. Da team 5
  serve probabilmente uno step extra (`extreme`) per i raid.
- **Fatigue**: ATTUALMENTE assente come sistema dedicato. Il "cooldown" è solo
  l'expedition_in_progress flag su `adventurers`. Da team 5+raid serve
  almeno una `last_expedition_completed_at` per evitare di lanciare 4 party
  raid back-to-back con gli stessi 20 advs (ma con 20 unique non serve).
- **Loot table** (`expeditions/loot_tables.py`): 10 entry hardcoded
  (per slug dungeon). Tier 1/2/3 con weights su Common/Uncommon/Rare/Epic.
  Serve estendere a 22 entry totali (10 storici + 12 nuovi) e 3 raid (con
  pool dedicato che valorizza Legendary set pieces).

### A.5 Report explainability
- `report_builder.py:114` ha `_narrative_summary(outcome, dungeon_name, team_size)`
  parametrico — nessun fix needed.
- `team_size` calcolato runtime: `len(members or [])`. ✅

### A.6 Weekly quest hooks attivi
Da `quests/services.py:74-114`:
- `expeditions_completed`
- `items_crafted`
- `market_purchases`
- `items_equipped`
- `expedition_loot_items`
- `market_listings_created`

🟡 Da ROUND 5: aggiungerne 2-3 (`raid_completed`, `t4_expedition_completed`,
`5man_expedition_completed`) per dare scelta a chi spinge ROUND 5 ma
**solo se l'utente conferma**.

---

## §B — Impatto ROUND 4 sul power medio

### B.1 Contributi power per adventurer oggi

| Sorgente | Range tipico |
|---|---|
| Stats base (5 stat × 8-15) | 40-75 |
| Level bonus (level × 2) | 2-30 |
| Equipment Common (3 slot) | 0-6 |
| Equipment Rare/Epic (3 slot) | 9-21 |
| Refinement +1..+5 (ROUND 4) | +(1-3)*slot |
| Enchant slot (ROUND 4) | +(1-5)/slot |
| Affix prefix+suffix (ROUND 4) | +(2-6)/slot |
| Set bonus 3-piece (ROUND 4) | +5..+15 fisso/team |
| Set bonus 5-piece (ROUND 4) | +10..+30 fisso/team |

**Team power tipico oggi (post-ROUND 4)**:
- Team da 3 L5 ben equipaggiato unbound: ~220-260
- Team da 3 L5 con refine+enchant+set 3pz: ~280-350
- Team da 5 L5 base equip: ~330-400 (estrapolato)
- Team da 5 L5 full forge/set 5pz: ~450-560 (estrapolato)

### B.2 `max_team_power_ever` (leaderboard peak)

Attuale: `max(team_power)` su tutte le expedition completate (anche failed).
Dopo ROUND 5 + team 5 → peak salirà naturalmente da ~250 a ~400-550. **NON
serve modificare la formula**, sale per costruzione. ✅

🚨 **Rischio leaderboard**: i giocatori che fanno raid (team_power 4-party
× 5 = 20 advs sommati?) potrebbero saturare il ceiling. **OPEN QUESTION 5**:
i raid contano per il `max_team_power_ever` o sono una metrica separata?

### B.3 Dungeon `recommended_power` attuali (post-ROUND 4 sembrano obsoleti?)

Confronto rec_power vs team power tipico ROUND 4:

| Dungeon | rec_power | team tipico L5 (3p) | success_chance |
|---|---:|---:|---:|
| goblin-warrens (T1) | 45 | 220 | 95% (clamp) |
| shadow-crypts (T2) | 60 | 220 | 95% (clamp) |
| storm-spire (T3) | 88 | 250 | 95% (clamp) |
| dragons-hoard (T3) | 80 | 280 | 95% (clamp) |

🚨 **Sì, già oggi T3 è banale per team L5 forgiato**. ROUND 5 deve introdurre
T4 con rec_power 180-280, e i raid con rec_power 400+ per il 4×5 sommato.

---

## §C — UI attuale

| File | Stato per ROUND 5 |
|---|---|
| `pages/ExpeditionNew.jsx` | ✅ Già parametrico su `requiredSize`. Solo da aggiornare il copy "3 heroes". |
| `pages/Expeditions.jsx` | ✅ Generic list. |
| `pages/ExpeditionReport.jsx` | ✅ Renderizza N membri. |
| `pages/Dungeons.jsx` | ✅ Mostra `d.required_team_size` dinamicamente (riga 111). |
| `pages/Admin.jsx` | 🟡 Default 3 nel create form (riga 286) → bumpare a 5 + `min=1 max=10`. |
| `components/ExpeditionExplainer.jsx` | 🟡 Da audit, probabilmente parametrico. |
| `mobile/` (Expo) | 🟡 Non auditato. Out-of-scope ROUND 5 per Phase 0. |

🟡 Da aggiungere per RAID:
- `pages/RaidNew.jsx` (party-picker per 20 = 4×5)
- `pages/Raids.jsx` (lista) o tab dentro Expeditions.jsx
- `pages/RaidReport.jsx` (multi-party-report)

---

## §D — Dungeon data attuali (10 totali)

(Già stampati in §A.1.) Tier 1 (3), T2 (4), T3 (3). Tutti `required_team_size=3`.

### D.1 Proposta 12 nuovi dungeon ROUND 5

> **8 LOCKED DECISIONS PROVVISORIE** (da confermare).
> Tutti i 12 nuovi dungeon hanno `required_team_size: 5`. Tier 1 nuovo è
> distinto da Tier 1 storico (rec_power più alto per matchare team da 5).

| # | Slug | Tier | rec_power | gold | xp | dur_s | difficulty | tags |
|---:|---|:---:|---:|---:|---:|---:|---:|---|
| 1 | `wolf-den-5p` | T1 Novizio | 80 | 50 | 35 | 60 | 1 | beast, pack |
| 2 | `frost-cave-5p` | T1 Novizio | 90 | 55 | 38 | 75 | 1 | cold, ambush |
| 3 | `salt-marsh-5p` | T1 Novizio | 100 | 60 | 42 | 90 | 1 | swamp, slow |
| 4 | `iron-foundry-5p` | T2 Avventuriero | 140 | 90 | 65 | 120 | 2 | construct, fire |
| 5 | `silent-monastery-5p` | T2 Avventuriero | 155 | 100 | 72 | 150 | 2 | undead, sustain |
| 6 | `pirate-fleet-5p` | T2 Avventuriero | 170 | 115 | 80 | 180 | 2 | human, water |
| 7 | `obsidian-arena-5p` | T3 Veterano | 210 | 160 | 110 | 240 | 3 | gladiator, agility |
| 8 | `clockwork-vault-5p` | T3 Veterano | 230 | 180 | 125 | 300 | 3 | construct, intellect |
| 9 | `voidspire-5p` | T3 Veterano | 250 | 200 | 140 | 360 | 3 | void, magic |
| 10 | `infernal-pit-5p` | T4 Elite | 290 | 260 | 180 | 420 | 4 | demon, fire |
| 11 | `celestial-citadel-5p` | T4 Elite | 320 | 300 | 210 | 540 | 4 | angel, holy |
| 12 | `world-tree-roots-5p` | T4 Elite | 360 | 360 | 250 | 720 | 4 | nature, endurance |

**Curve loot proposte (allineate a rarity dei drop)**:
- T1 5p: Common 70% · Uncommon 25% · Rare 5%
- T2 5p: Common 30% · Uncommon 50% · Rare 18% · Epic 2%
- T3 5p: Uncommon 25% · Rare 50% · Epic 25%
- T4 5p: Rare 30% · Epic 60% · Legendary 10% (Legendary già esistente da ROUND 4)

**Gate (sticky-peak `max_team_power_ever`)**:
- T1 5p: nessun gate (entry-level)
- T2 5p: `max_team_power_ever ≥ 120`
- T3 5p: `max_team_power_ever ≥ 200`
- T4 5p: `max_team_power_ever ≥ 280`

---

## §E — Roster auditing

### E.1 Limiti roster attuali
- **Nessun `max_roster`** nei modelli. I giocatori possono reclutare illimitato.
- Recruiting flow: `/api/recruitment/candidates` → 3 candidati pseudo-rand,
  `/api/recruitment/recruit` con cost gold scalato per rarity.
- Onboarding: `/api/auth/register` non crea adventurer starter (l'utente
  recluta manualmente dopo aver creato la guild).

### E.2 Numero adventurer medio per player

🚨 Non auditabile senza accesso prod DB. **OPEN QUESTION 1**: ottenere
statistica reale da prod? Stima: la maggior parte dei players ha 5-15 advs
(basato su feedback Phase 14.8 dove abbiamo visto 1 player con 14 advs).

### E.3 Messaggi "ti servono più avventurieri"

NON esiste oggi. ROUND 5 lo richiede per i raid (20 advs unique). Da aggiungere:
- Toast "Servono almeno 5 avventurieri attivi per questa spedizione"
- Toast "Servono almeno 20 avventurieri unici e disponibili per questo raid"
- Banner persistente in `/raids` se roster < 20

---

## §F — Raid model proposto

### F.1 Vincoli (locked, ribaditi)
- **Single-player only**: 1 player solo, NO Consortium, NO PvP, NO co-op.
- **20 advs unique** spalmati su **4 party × 5**.
- Solo l'owner della guild può lanciare un raid.

### F.2 Schema dati proposto

**Nuova collection `raids`**:
```
{
  id: uuid4,
  guild_id: ref,
  raid_slug: "broken-bastion-siege" | "necropolis-bells" | "dragon-vault",
  status: "in_progress" | "completed" | "failed",
  started_at, completed_at,
  parties: [
    { party_idx: 1, adventurer_ids: [5], focus_role: "tank", outcome: "...", loot: [...] },
    { party_idx: 2, adventurer_ids: [5], focus_role: "healer", ... },
    { party_idx: 3, adventurer_ids: [5], focus_role: "dps", ... },
    { party_idx: 4, adventurer_ids: [5], focus_role: "sustain", ... }
  ],
  team_power_combined: int,
  recommended_power_combined: int,
  success_chance: int,
  outcome: "victory" | "partial" | "wipe",
  rewards: { gold, xp_per_member, loot: [...] },
}
```

**Nuova collection `raid_dungeons` (3 seed)**:

| Slug | Tier | rec_power_combined | gold | xp/member | dur_s | focus required |
|---|:---:|---:|---:|---:|---:|---|
| `broken-bastion-siege` | R1 | 800 | 600 | 100 | 1800 (30min) | ≥1 Tank + ≥1 Healer in 2/4 party |
| `necropolis-bells` | R1 | 900 | 700 | 120 | 2400 (40min) | ≥1 Healer in 3/4 party, sustain |
| `dragon-vault` | R2 | 1400 | 1200 | 200 | 3600 (60min) | team_power_combined > 1200 |

### F.3 Endpoint proposti

| Method | Path | Notes |
|---|---|---|
| GET | `/api/raids/catalog` | Lista 3 raid disponibili + gate |
| POST | `/api/raids/preview` | `{raid_slug, parties: [[5 ids]×4]}` → success_chance per party + combined |
| POST | `/api/raids/start` | crea record, marca 20 advs `expedition_in_progress=True` |
| POST | `/api/raids/{id}/complete` | server-driven, calcola outcome per party + combined |
| GET | `/api/raids` | history |
| GET | `/api/raids/{id}` | report dettagliato |

### F.4 Formula raid (proposta)
```
party_power[i] = compute_team_power(party[i])  # riusa formula esistente
team_power_combined = Σ party_power[i]
success_chance_combined = clamp(40 + (team_power_combined - rec_combined)/4, 5, 95)
party_outcome[i] = roll(party_success_chance[i])
raid_outcome =
    "victory" if all 4 success,
    "partial" if 2-3 success,
    "wipe" if 0-1 success.
```
Reward partial: 60% gold, 40% xp/member, no Legendary drop.

---

## §G — Rischi tecnici (RAS)

| # | Rischio | Mitigation |
|---|---|---|
| R1 | Player con <5 advs vede "team size 5 dungeon" loccato → frustrazione | T1 5p è entry-level, sbloccabile dopo 5 reclutamenti. Mantenere i 3 dungeon storici a team 3 sempre disponibili. |
| R2 | Player con <20 advs prova ad aprire `/raids` → banner | Banner "Roster troppo piccolo: 14/20" + link a recruitment. |
| R3 | Migration retrocompat: vecchi report con `team_size=3` non rompono | Nessuna migration necessaria: `report_builder._narrative_summary` accetta team_size dinamico. |
| R4 | Leaderboard `max_team_power_ever` esplode con raid (4×5 sommato) | **OPEN Q5**: raid esclude o include? Default proposto: ESCLUDE (raid avrebbe metrica separata `max_raid_power_ever`). |
| R5 | `expedition_in_progress` su 20 advs simultanei | Bulk update atomico in `raids.start`. Test specifico. |
| R6 | Bilanciamento drop Legendary in raid prosciuga loot tier prima della prossima patch | Gate Legendary in T4 5p (10%) + raid (15%). Stimato 1-2 Legendary/settimana per player attivo. |
| R7 | UI mobile (Expo) non sa di team 5/raid | Esplicitamente out-of-scope Phase 17.5 (mobile parity slittato a Phase 21). |
| R8 | Forge ROUND 4 `dragon_essence` material drop solo da raid? | OPEN Q4: rendere drop dragon_essence da T4 + raid? Oggi assente. |

---

## §H — Piano patch minimo (proposta, da approvare)

**Phase 17.5 — Team Size 5 Foundation (≈2-3h)**
1. Seed 12 nuovi dungeon `*-5p` con `required_team_size=5`, gate sticky-peak.
2. Estendere `DUNGEON_LOOT_TABLES` con 12 entry nuove + curve T4.
3. Bump rec_power formula? **NO** (lineare resta, ma dungeon nuovi hanno
   rec_power calibrato per team da 5).
4. Update `Admin.jsx` create-form default 3→5 + range UI.
5. Copy update in `ExpeditionNew.jsx` (`{N}/{requiredSize}` già parametrico).
6. Tests: 6 nuovi (seed presence, gate dei 4 tier, success_chance scaling
   con team 5, loot table T4 returns Legendary, dungeon T4 success-only,
   no-regression team 3).

**Phase 18 — Solo Raid MVP (≈4-5h)**
1. Collection `raid_dungeons` + 3 seed.
2. Collection `raids` + indici.
3. 6 endpoint `/api/raids/*`.
4. `compute_raid_outcome` server-driven con per-party rolls.
5. Frontend: `pages/RaidNew.jsx` (party builder 4×5), `pages/Raids.jsx` (list),
   `pages/RaidReport.jsx` (multi-party).
6. i18n keys + nav link "RAID" / "RAIDS".
7. Tests: 15 nuovi (preview shape, 20 unique check, gate roster, party
   composition, outcome scenarios victory/partial/wipe, loot, audit log).
8. Audit event `raid_completed`, `raid_started`.

**Phase 19 — Polishing (opt)**
1. Weekly quest hooks `raid_completed_weekly`, `t4_5p_completed_weekly`.
2. UI: Forge link "Materiali Raid" + drop dragon_essence solo da T4/raid.
3. Tooltip `extreme` injury_risk level.

---

## §I — 7 LOCKED DECISIONS (risposte utente del 2026-06-26)

> Pattern utente: **1:a 2:a 3:b 4:b 5:a 6:c 7:b**

### I.1 — Starter roster: AUTO-POP 5 (`a`) ✅
- All'evento `POST /api/auth/register` (o al primo `POST /api/guilds`), il sistema genera
  **3 base Common + 2 extra Common procedurali** così il player ha **subito 5 advs disponibili**.
- **IDEMPOTENT**: la routine controlla `count(adventurers where guild_id=X) < 5` PRIMA di seedare.
  Se il player ha già ≥5 (es. registrato pre-ROUND 5), NON viene toccato nulla.
- I 2 extra non sono guaranteed pity rolls: usano la stessa distribuzione del recruitment Common pool.
- **Audit event**: `starter_roster_seeded` (per ogni adv generato, con flag `is_starter=True`).
- **Implicazione tecnica**: nuova funzione `app/onboarding/services.py::ensure_starter_roster(db, guild_id)`,
  chiamata dal lifespan migration al boot per back-fill, e dal `POST /api/guilds` per nuove guild.
- **Edge case**: guild esistente con 0 advs (test rig fresco) → seeda 5 al boot.
  Guild con 3 advs (player partito ma non recluta) → seeda 2 extra. Guild con 7 advs → no-op.

### I.2 — Dungeon storici Legacy: KEEP team=3 (`a`) ✅
- I 10 dungeon storici restano `required_team_size=3`. NESSUN bump.
- Aggiungiamo **tag UI "LEGACY"** + **badge T1L/T2L/T3L** nella `Dungeons.jsx`.
- **Implicazione tecnica**:
  - Nuova colonna `dungeons.is_legacy: bool` (default `False` per i nuovi; backfill `True` per i 10 storici).
  - Pubblico in `dungeon_public()` come `is_legacy: bool`.
  - Frontend filtra per default "Mostra Legacy" toggle ON (così non perdono visibilità).
- Player con <5 advs può comunque giocare i Legacy → onboarding smooth.
- **Visibilità leaderboard**: i Legacy contribuiscono ancora a `max_team_power_ever` (no break).

### I.3 — T4 Legendary drop rate: 5% (`b`) ✅
- Curva T4 5p loot table aggiornata:
  - **Common 5% · Uncommon 25% · Rare 35% · Epic 30% · Legendary 5%**
- Più scarce di quanto inizialmente proposto (10%) → valorizza Forge crafting e set seed di ROUND 4.
- **Failure drop**: solo Common/Uncommon (regola Phase 10 invariata).
- **Implicazione tecnica**:
  - `loot_tables.py` 12 nuove entry per `*-5p` dungeon, T4 con weights aggiornati.
  - Sentinel di test `test_t4_legendary_drop_rate_<=_8pct_over_1000_rolls` per evitare drift.

### I.4 — `dragon_essence` source: T4 + RAID (`b`) ✅
- Drop sources:
  - **T4 5p run**: 5-10% chance success drop di 1× `dragon_essence`
  - **Raid completion**: guaranteed 1× per party survivor + bonus 1-3 random per raid victory
- **NO disenchant**: rimuovere la guaranteed Legendary→dragon_essence dalla tabella disenchant
  (oggi nel seed è incluso) — **MIGRAZIONE NECESSARIA** in `seed_forge.py::disenchant_returns`.
- **Implicazione tecnica**:
  - Update `forge/services.py::disenchant_instance` per leggere dalla nuova tabella che esclude dragon_essence.
  - `loot_tables.py` aggiungere `bonus_material_drop` per T4 dungeons.
  - `raids/services.py::compute_raid_rewards` ha pool dedicato.
- **Bilanciamento**: stima 2-5 dragon_essence/settimana per player attivo che fa T4 + 1 raid/settimana.

### I.5 — `max_team_power_ever` esclude raid (`a`) ✅
- Il `max_team_power_ever` del leaderboard guild **resta basato SOLO su expedition**.
- Nuova metrica separata `guilds.max_raid_score: int` (default 0).
- `raid_score = team_power_combined × outcome_multiplier`
  dove `outcome_multiplier = 1.0 victory / 0.5 partial / 0.1 wipe`.
- **NUOVO endpoint pubblico** (proposto, opzionale ROUND 5):
  `GET /api/leaderboard/raids` ordinato per `max_raid_score`.
- **Implicazione tecnica**:
  - Aggiungere `max_raid_score` a `guilds_public()` (additive, no break).
  - Aggiornare `guilds.max_raid_score` solo al `complete_raid` con `max(current, new_score)`.
  - Nessun cross-contamination tra expedition e raid metrics.
- Leaderboard guild esistente: **invariato**. Frontend toggle "Top guilds / Top raiders".

### I.6 — `rec_power` bump storici: SOLO +25% T2-T3 (`c`) ✅
- Migration **idempotente** con flag `dungeons.power_bumped: bool`:
  - Se `power_bumped == True` → no-op (già fatto, non ribumpare)
  - Se `power_bumped` assente o `False` AND `difficulty in [2, 3]` AND `is_legacy=True`
    → `recommended_power = ceil(recommended_power * 1.25)`, set `power_bumped=True`.
  - T1 storici: NESSUN bump (entry-level intoccato).
  - T4 nuovi: nessun bump necessario (sono calibrati nativi per team 5).
- **Nuovi recommended_power post-bump** (delta T2-T3):
  - druid-grove: 55 → 69 (+14)
  - cursed-mines: 62 → 78 (+16)
  - sunken-library: 68 → 85 (+17)
  - shadow-crypts: 60 → 75 (+15)
  - dragons-hoard: 80 → 100 (+20)
  - lich-sanctum: 75 → 94 (+19)
  - storm-spire: 88 → 110 (+22)
- **Implicazione tecnica**:
  - Migration in `seed_data.py::run_dungeons_power_bump()` chiamata al lifespan boot.
  - Test `test_power_bump_idempotent_no_double` (run 2 volte, verify rec_power unchanged after first).
- **Player UX**: dungeon storici T2-T3 ora richiedono leggermente più power, ma con team 3 + ROUND 4 forge resta gestibile.

### I.7 — Raid cooldown: 15 min per GUILD (`b`) ✅
- Dopo `complete_raid` la guild non può lanciare un altro raid per **15 minuti** (900 secondi).
- **Storage**: nuovo field `guilds.last_raid_completed_at: datetime UTC` (additive).
- **Validation** in `POST /api/raids/start`:
  ```
  cooldown_remaining = 900 - (now() - guild.last_raid_completed_at).total_seconds()
  if cooldown_remaining > 0:
      raise HTTPException(422, detail="raids.cooldown_active", extra={"seconds_remaining": int(cooldown_remaining)})
  ```
- I 20 advs partecipanti **NON** hanno cooldown extra (i flags `expedition_in_progress`
  vengono rilasciati al complete_raid come per le expedition normali).
- **Frontend**: countdown live "Prossimo raid disponibile tra: 12:34" nella `Raids.jsx`.
- **i18n key**: `raids.error.cooldown_active`, `raids.cooldown_countdown` con placeholder `{seconds}`.
- **Audit**: nessun nuovo event (il timer è derivato dal `raid_completed`).

---

## §K — File coinvolti per Phase 17.5 + 18 (lista preventiva)

**Backend**:
- `app/seeds/seed_data.py` (+ 12 nuovi dungeon)
- `app/seeds/seed_raids.py` (NEW: 3 raid)
- `app/expeditions/loot_tables.py` (+ 12 entry)
- `app/expeditions/formulas.py` (no change atteso)
- `app/raids/__init__.py` (NEW)
- `app/raids/routes.py` (NEW)
- `app/raids/services.py` (NEW)
- `app/raids/formulas.py` (NEW)
- `app/raids/schemas.py` (NEW)
- `app/raids/report_builder.py` (NEW)
- `server.py` (mount raids router)

**Frontend**:
- `pages/Dungeons.jsx` (filter T4 + 5p tags)
- `pages/Admin.jsx` (default + range form)
- `pages/RaidNew.jsx` (NEW)
- `pages/Raids.jsx` (NEW)
- `pages/RaidReport.jsx` (NEW)
- `components/AppHeader.jsx` (nav link "RAID")
- `i18n/lang/{it,en}.json` (+ raid.*, dungeon.t4.*, expedition.team5.*)
- `App.js` (3 nuove route)

**Tests**:
- `tests/backend_phase17_5_team5_test.py` (NEW, ~12 test)
- `tests/backend_phase18_raids_test.py` (NEW, ~15 test)

**Memory**:
- `ROUND_5_BRIEF.md` (this file, expanded with locked decisions)
- `PRD.md` (aggiornamento Phase 17.5 + 18)
- `test_credentials.md` (sezione raid se applicabile)

---

## §L — Stima totale

- **Phase 17.5**: ~2-3h implementazione + 1h test
- **Phase 18**: ~4-5h implementazione + 1.5h test
- **Phase 19 polishing**: ~1.5h
- **Path count atteso**: 69 → ~75 (+6 raid endpoints)

---

## §M — Data model finale (post-lock)

### M.1 Nuova collection `raid_dungeons`

```json
{
  "_id": ObjectId,
  "id": "uuid4",
  "slug": "broken-bastion-siege" | "necropolis-bells" | "dragon-vault",
  "name": { "it": "Assedio al Bastione Spezzato", "en": "Siege of the Broken Bastion" },
  "description": { "it": "...", "en": "..." },
  "tier": 1 | 2,
  "recommended_power_combined": 800 | 900 | 1400,
  "min_roster_size": 20,
  "required_party_count": 4,
  "required_party_size": 5,
  "party_focus_hints": [
    { "party_idx": 1, "preferred_role": "Tank", "label_it": "Vanguardia", "label_en": "Vanguard" },
    { "party_idx": 2, "preferred_role": "Healer", "label_it": "Sostegno", "label_en": "Sustain" },
    { "party_idx": 3, "preferred_role": "DPS", "label_it": "Assalto", "label_en": "Assault" },
    { "party_idx": 4, "preferred_role": null, "label_it": "Riserva", "label_en": "Reserve" }
  ],
  "base_duration_seconds": 1800 | 2400 | 3600,
  "base_gold_reward": 600 | 700 | 1200,
  "base_xp_per_member": 100 | 120 | 200,
  "loot_pool_slug": "raid_r1" | "raid_r2",
  "guaranteed_dragon_essence_min": 1,
  "guaranteed_dragon_essence_max": 3,
  "is_active": true,
  "created_at": ISODate
}
```

INDICI: `slug` UNIQUE, `is_active`.

### M.2 Nuova collection `raids` (istanze in corso/completate)

```json
{
  "_id": ObjectId,
  "id": "uuid4",
  "guild_id": "uuid4",
  "raid_dungeon_id": "uuid4",
  "raid_dungeon_slug": "broken-bastion-siege",
  "status": "in_progress" | "completed",
  "outcome": "victory" | "partial" | "wipe" | null,
  "team_power_combined": 1234,
  "recommended_power_combined": 800,
  "success_chance_per_party": [78, 82, 65, 71],
  "success_chance_combined": 75,
  "raid_score": 1234,
  "started_at": ISODate,
  "ends_at": ISODate,
  "completed_at": ISODate | null,
  "duration_seconds": 1800,
  "rewards": {
    "gold_total": 600,
    "xp_per_member": 100,
    "loot_items": [{ "item_id": "...", "rarity": "Epic", "to_party_idx": 2 }, ...],
    "dragon_essence_count": 2
  },
  "audit_event_ids": [...],
  "created_at": ISODate,
  "updated_at": ISODate
}
```

INDICI:
- `id` UNIQUE
- `guild_id, status` (lookup raid attivo)
- `guild_id, completed_at DESC` (history)

### M.3 Nuova collection `raid_participants` (4 party × 5 advs, 20 rows per raid)

> Modellati come row separate (1 per adv) invece di array embedded — permette
> indici/query per adventurer e audit retention indipendente dal raid doc.

```json
{
  "_id": ObjectId,
  "id": "uuid4",
  "raid_id": "uuid4",       // FK -> raids.id
  "guild_id": "uuid4",
  "adventurer_id": "uuid4",
  "party_idx": 1 | 2 | 3 | 4,
  "role_snapshot": "Tank" | "Healer" | "DPS" | null,
  "class_snapshot": "Paladin" | ...,
  "level_snapshot": 5,
  "total_power_snapshot": 87,
  "equipment_power_snapshot": 12,
  "outcome": "survived" | "fainted" | null,   // post-complete
  "xp_gained": 100,
  "created_at": ISODate
}
```

INDICI:
- `raid_id` (lookup tutti i 20 partecipanti)
- `adventurer_id` (history per adv)
- UNIQUE compound `(raid_id, adventurer_id)` (no doppia partecipazione)
- UNIQUE compound `(raid_id, party_idx, adventurer_id)` (party assignment)
- Pre-check applicativo: `(adventurer_id, status='in_progress')` deve essere unique
  across raid + expedition combined (riusiamo `adventurers.expedition_in_progress` boolean).

### M.4 Estensioni a `guilds` (additive, idempotenti)

```diff
+ "max_raid_score": int (default 0)
+ "last_raid_completed_at": ISODate | null (default null)
+ "raids_completed_count": int (default 0)
+ "raids_victory_count": int (default 0)
```

Esposti in `guild_public()` solo se >0 (sennò chiavi assenti, no breaking change).

### M.5 Estensioni a `dungeons` (additive, idempotenti)

```diff
+ "is_legacy": bool (default False per nuovi 5p, True backfill per i 10 storici)
+ "power_bumped": bool (default False, sentinel migration §I.6)
+ "tier_label": "T1" | "T2" | "T3" | "T4" | "T1L" | "T2L" | "T3L"  (derivato runtime, no storage)
```

### M.6 Estensioni a `adventurers` (additive)

```diff
+ "is_starter": bool (default False, True per i 5 generati da §I.1)
```

Nessuna nuova logica gameplay sui starter — solo audit/telemetria.

### M.7 Audit events nuovi

| Event type | Payload | Trigger |
|---|---|---|
| `starter_roster_seeded` | `{adventurer_id, is_starter: True, source: "register|backfill"}` | §I.1 |
| `raid_started` | `{raid_id, raid_dungeon_slug, party_count: 4, adventurer_count: 20}` | POST /api/raids/start |
| `raid_completed` | `{raid_id, outcome, raid_score, gold, xp_per_member, dragon_essence}` | POST /api/raids/{id}/complete |
| `dungeon_power_bumped` | `{dungeon_slug, old_rec_power, new_rec_power}` | §I.6 migration (one-shot) |

---

## §N — UI mockup (raid builder + cooldown display)

### N.1 Lista raid (`/raids` — page Raids.jsx)

```
┌──────────────────────────────────────────────────────────────┐
│  ORBUS // RAID                                       👤 ⚙   │
├──────────────────────────────────────────────────────────────┤
│  ▶  RAID DISPONIBILI                                          │
│                                                                │
│  ⏳ Prossimo raid disponibile tra: 12:34                       │
│  └─ data-testid="raids-cooldown-banner"                       │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ ASSEDIO AL BASTIONE SPEZZATO                  [T1] [R1]│   │
│  │ ───────────────────────────────────────────────────────│   │
│  │ Potenza consigliata: 800 (combinata)                   │   │
│  │ Roster richiesto: 20 unique                            │   │
│  │ Durata: 30:00                                          │   │
│  │ Reward: 600g + 100 XP/adv + 1-3 dragon_essence        │   │
│  │                                                        │   │
│  │ Roster: 14/20 ⚠ servono altri 6 avventurieri          │   │
│  │ [ data-testid="raid-card-roster-warn-broken-bastion" ]│   │
│  │ ────────────────────────────────────────────────────  │   │
│  │ [ ENTRA A PIANIFICARE ]    ← greyed if roster < 20    │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ NECROPOLI DELLE MILLE CAMPANE                 [T1] [R1]│   │
│  │ ...                                                    │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ VOLTA DEL DRAGO ADDORMENTATO                  [T2] [R2]│   │
│  │ 🔒 BLOCCATO — Richiede max_team_power_ever ≥ 280       │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  ───────────────────────────────────────────                  │
│  STORIA RAID                                                   │
│  • 24 giu — Bastione Spezzato — ✅ Vittoria — 600g            │
│  • 22 giu — Bastione Spezzato — ⚠ Parziale — 360g             │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

### N.2 Raid builder (`/raids/new/:slug` — page RaidNew.jsx)

```
┌──────────────────────────────────────────────────────────────┐
│  ORBUS // RAID :: ASSEDIO AL BASTIONE SPEZZATO                │
├──────────────────────────────────────────────────────────────┤
│  ⚠ I 20 avventurieri saranno impegnati per ~30 minuti.        │
│  Dopo il raid, devi aspettare 15 min prima del prossimo.      │
│                                                                │
│  ┌──────────────── PARTY 1 — VANGUARDIA (Tank prefer.) ────┐  │
│  │ data-testid="raid-party-1"                              │  │
│  │ [Slot 1] (vuoto)  → trascina o seleziona               │  │
│  │ [Slot 2] (vuoto)                                        │  │
│  │ [Slot 3] (vuoto)                                        │  │
│  │ [Slot 4] (vuoto)                                        │  │
│  │ [Slot 5] (vuoto)                                        │  │
│  │ Party power: 0  ·  Success chance: —                   │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌──────────────── PARTY 2 — SOSTEGNO (Healer prefer.) ────┐  │
│  │ data-testid="raid-party-2"   ...                        │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌──────────────── PARTY 3 — ASSALTO (DPS prefer.) ────────┐  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌──────────────── PARTY 4 — RISERVA (flessibile) ─────────┐  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ──────────────────────────────────────────────────────────   │
│  AVVENTURIERI DISPONIBILI (14)                                │
│  data-testid="raid-roster-pool"                               │
│  • [Tank] Gwyn Ashwood L5  pwr 87   [+ AGGIUNGI ▾]            │
│  • [Healer] Brom L4  pwr 72   [+ AGGIUNGI ▾]                  │
│  ...                                                          │
│                                                                │
│  ──────────────────────────────────────────────────────────   │
│  RIEPILOGO                                                     │
│  Team power totale: 0/4 party                                 │
│  Success chance combinata: —                                  │
│  data-testid="raid-summary-power" / "raid-summary-success"    │
│                                                                │
│  [ ANTEPRIMA RAID ] (disabled se non 20 advs)                 │
│  data-testid="raid-preview-btn"                               │
│                                                                │
│  [ LANCIA RAID ]    (disabled finché preview non OK)          │
│  data-testid="raid-launch-btn"                                │
└──────────────────────────────────────────────────────────────┘
```

### N.3 Cooldown display globale

- Inserito in `AppHeader.jsx` come piccola pill in alto a destra solo se cooldown attivo:
  ```
  ⏳ Raid: 12:34   data-testid="header-raid-cooldown"
  ```
- Aggiornato con timer JS lato client (no polling backend, derivato da `guild.last_raid_completed_at`).

### N.4 Report raid (`/raids/:id` — page RaidReport.jsx)

```
┌──────────────────────────────────────────────────────────────┐
│  RAPPORTO RAID :: ASSEDIO AL BASTIONE SPEZZATO                │
│  Outcome: ✅ VITTORIA  ·  Raid score: 1234                    │
│  Durata effettiva: 28 min                                     │
├──────────────────────────────────────────────────────────────┤
│  PARTY 1 — Vanguardia    ✅ Successo (78%)                   │
│    • Gwyn Ashwood — survived — +100 XP                       │
│    • Brom — survived — +100 XP                                │
│    • ... (3 altri)                                            │
│  PARTY 2 — Sostegno      ✅ Successo (82%)                   │
│    ...                                                        │
│  PARTY 3 — Assalto       ⚠ Fallimento (65%)                  │
│    • Tibel — fainted — 0 XP                                   │
│    ...                                                        │
│  PARTY 4 — Riserva       ✅ Successo (71%)                   │
│                                                                │
│  ──────────────────────────────────────────────────────────   │
│  REWARDS                                                      │
│  • 600 gold → guild treasury                                  │
│  • 100 XP per avventuriere sopravvissuto (16 advs)            │
│  • Loot:                                                      │
│    • [Epic] Helm of the Bastion → party 1                     │
│    • [Rare] Drake-fang Pendant → party 2                      │
│  • 2× dragon_essence → inventory guild                        │
└──────────────────────────────────────────────────────────────┘
```

---

## §O — Piano patch finale (Phase 17.5 → 18 → 19)

### Phase 17.5 — Team Size 5 Foundation (~3h impl + 1h test)

**Backend** (in ordine di esecuzione):
1. `app/onboarding/__init__.py` + `app/onboarding/services.py::ensure_starter_roster(db, guild_id)` (§I.1).
2. Modifica `app/guilds/routes.py::create_guild` per chiamare `ensure_starter_roster` post-creazione.
3. Lifespan back-fill: chiamata one-shot a `ensure_starter_roster` per ogni guild esistente con <5 advs.
4. `seed_data.py`:
   - Aggiungere 12 nuovi dungeon T1-T4 5p con `is_legacy: False`, `power_bumped: True` (skip migration).
   - Migration `mark_legacy_dungeons()` (idempotent: set `is_legacy=True` ai 10 storici se assente).
   - Migration `bump_legacy_power()` (idempotent §I.6 con flag `power_bumped`).
5. `loot_tables.py`: 12 nuove entry `*-5p` con curve §I.3.
6. `dungeons/services.py::dungeon_public()`: aggiungere campi `is_legacy`, `power_bumped` allo schema pubblico.
7. `guilds/services.py::guild_public()`: aggiungere `max_raid_score`, `last_raid_completed_at`, `raids_completed_count`, `raids_victory_count` (solo se >0/non-null).

**Frontend**:
1. `Dungeons.jsx`: badge "LEGACY" + filtro "Mostra Legacy" (default ON).
2. `Admin.jsx`: bump default `required_team_size: 5` nel create form, range `min=1 max=10`.
3. `ExpeditionNew.jsx`: copy "{N}/{requiredSize} heroes" (già parametrico).
4. i18n keys nuove: `dungeon.legacy_badge`, `dungeon.t4_badge`, `expedition.team5_intro`, `onboarding.starter_seeded`.

**Tests** (`tests/backend_phase17_5_team5_test.py`, ~12 test):
- `test_starter_roster_seeded_5_on_new_guild`
- `test_starter_roster_idempotent_no_dup` (run 2x → still 5 advs)
- `test_starter_roster_backfill_for_legacy_guild_with_3` (3→5)
- `test_legacy_dungeons_marked_is_legacy_true`
- `test_new_5p_dungeons_marked_is_legacy_false`
- `test_power_bump_T2_T3_only` (verify rec_power deltas exact)
- `test_power_bump_idempotent_no_double` (run migration 2x, no change)
- `test_T1_legacy_not_bumped`
- `test_T4_loot_table_returns_legendary_5pct_over_1000_rolls`
- `test_T4_failure_drops_only_common_uncommon` (regola Phase 10)
- `test_inventory_has_no_dragon_essence_from_disenchant_post_round5` (§I.4)
- `test_no_regression_team_3_dungeons_still_dispatchable`

### Phase 18 — Solo Raid MVP (~5h impl + 1.5h test)

**Backend**:
1. `app/raids/__init__.py`, `routes.py`, `services.py`, `formulas.py`, `schemas.py`, `report_builder.py`.
2. `seed_raids.py`: 3 raid dungeon (Bastione/Necropoli/Drago) con stat §M.1.
3. Migration `mark_raid_collections_indexes()` su `raids`, `raid_participants`, `raid_dungeons`.
4. 6 endpoint:
   - `GET /api/raids/catalog` (lista + gate)
   - `POST /api/raids/preview` (combined power + per-party success chance)
   - `POST /api/raids/start` (validate roster 20 unique, cooldown 15min, atomic flag bulk update)
   - `POST /api/raids/{id}/complete` (server-driven outcome + rewards + audit)
   - `GET /api/raids` (history guild)
   - `GET /api/raids/{id}` (report)
5. `compute_raid_outcome` con formula §F.4.
6. `compute_raid_rewards` con loot pool dedicato + dragon_essence guaranteed.
7. server.py: mount router `raids.router`.

**Frontend**:
1. `pages/Raids.jsx` (lista + cooldown banner + history).
2. `pages/RaidNew.jsx` (party builder 4×5, drag-or-pick, preview live).
3. `pages/RaidReport.jsx` (multi-party-report con per-adv outcome).
4. `components/AppHeader.jsx`: cooldown pill (§N.3) + nav link "RAID".
5. `App.js`: 3 nuove route protette + `requireGuild`.
6. i18n: ~30 chiavi `raid.*`.

**Tests** (`tests/backend_phase18_raids_test.py`, ~15 test):
- `test_raid_catalog_returns_3_seeds`
- `test_raid_preview_shape`
- `test_raid_start_requires_20_unique_advs`
- `test_raid_start_rejects_dup_adventurer_across_parties`
- `test_raid_start_marks_20_advs_expedition_in_progress`
- `test_raid_cooldown_15min_after_complete` (lock + retry → 422 sentinel)
- `test_raid_outcome_victory_all_parties_success`
- `test_raid_outcome_partial_2_of_4`
- `test_raid_outcome_wipe_0_of_4`
- `test_raid_score_uses_outcome_multiplier`
- `test_raid_dragon_essence_guaranteed_min_1`
- `test_raid_max_raid_score_updates_on_completion`
- `test_max_team_power_ever_NOT_affected_by_raid` (§I.5)
- `test_raid_audit_events_logged`
- `test_raid_with_lt_20_advs_returns_422_clear_msg`

### Phase 19 — Polishing (~1.5h, opt)

1. Weekly quest hooks: `raid_completed_weekly`, `t4_5p_completed_weekly`.
2. UI: tooltip `extreme` injury_risk per T4 + raid.
3. Leaderboard toggle "Top Raiders" (nuovo endpoint `GET /api/leaderboard/raids`).
4. (Solo se utente lo chiede esplicitamente) — Mobile Expo parity Raid.

### Path count atteso post-implementazione

- Phase 17.5: +0 endpoint nuovi (solo seed/migration) → **69**
- Phase 18: +6 endpoint raid → **75**
- Phase 19: +1 endpoint leaderboard raid → **76** (se attivato)

---

## §P — Pre-implementation checklist (da spuntare prima di "GO ROUND 5 IMPLEMENTATION")

- [x] ROUND 4 mergiato e deployato in prod  ← **BLOCCANTE**
- [x] Smoke test prod paths=69 verde   ← **BLOCCANTE**
- [x] User esplicito "GO ROUND 5 IMPLEMENTATION"   ← **BLOCCANTE**
- [x] Decisioni §I tutte locked (questa versione del brief)   ✅
- [x] PRD.md aggiornato con Phase 17.5/18/19 backlog   (al kickoff)
- [x] Memory ROUND_5_BRIEF.md condiviso col testing agent al prossimo ciclo

