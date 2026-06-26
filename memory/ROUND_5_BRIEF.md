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

## §I — 7 OPEN QUESTIONS — risposte locked richieste prima di scrivere codice

1. **Starter roster auto-pop**: quando il player crea la guild, **vuoi
   auto-popolare 5 advs starter** (così team-size-5 funziona subito) o
   continuare con il flow manuale di recruiting candidate-by-candidate?
   - a. Auto-pop 5 Common starter al login (idempotent)
   - b. Auto-pop solo 3 starter (back-compat) e player deve reclutarne 2
   - c. Nessun auto-pop (status quo): player vede gate "ti servono 5 advs"

2. **Dungeon T1-T3 storici**: i 10 dungeon a `required_team_size=3`
   esistenti li **manteniamo intatti** o **bumpiamo anche loro a team 5**?
   - a. Tieni intatti (back-compat 100%, players con poche reclute giocano T1-T3)
   - b. Bump tutti a 5 (clean break, ma reclute necessarie)
   - c. Bump i T3 storici a 5 (matching nuovi T3), T1-T2 restano a 3

3. **Tier curve drop Legendary**: T4 5p deve droppare Legendary?
   - a. Sì 10% (proposta sopra)
   - b. Sì 5% (più scarce, valorizza Forge crafting da set seed)
   - c. NO — solo da raid

4. **dragon_essence material**: dove deve droppare?
   - a. Solo Raid (incentivo raid)
   - b. T4 5p (5-10% per run) + Raid (garantito 1+)
   - c. Anche da disenchant Legendary (oggi è il caso). Tutto invariato.

5. **`max_team_power_ever` e raid**: il raid contribuisce al peak leaderboard?
   - a. NO, raid ha metrica separata `max_raid_power_ever` (proposta)
   - b. Sì, sommato come 4-party power
   - c. Sì, ma solo il party migliore del raid

6. **Recommended_power dungeon storici obsoleti**:
   - a. Lasciamo invariati (player low-level li trova facili — fine)
   - b. Bumpiamo +50% rec_power per matchare ROUND 4 power inflation
   - c. Bumpiamo +25% solo T2-T3 storici, T1 invariati

7. **Fatigue/cooldown post-raid**: dopo un raid i 20 advs hanno cooldown
   extra rispetto a expedition normale?
   - a. NO cooldown extra (status quo `expedition_in_progress` rilasciato al complete)
   - b. Cooldown 15min sui 20 advs post-raid (no expedition fino allo scadere)
   - c. Cooldown 1h sui 20 advs post-raid (gating più stretto)

> Quando rispondi con il pattern `1:a 2:c 3:a 4:b 5:a 6:a 7:a` (o varianti),
> aggiorno questo brief in `§J — LOCKED DECISIONS` e Phase 17.5 implementation
> può partire.

---

## §J — LOCKED DECISIONS

_(empty — awaiting user response to §I)_

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

🛑 **STATUS**: Audit completo. **Aspetto risposte alle 7 domande in §I**.
Nessun codice in repo finora. Phase 17.5 non parte fino a `LOCKED DECISIONS` in §J.
