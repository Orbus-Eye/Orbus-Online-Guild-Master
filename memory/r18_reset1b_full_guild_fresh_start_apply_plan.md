# ROUND 18.Reset.1b — Full Guild Fresh Start Apply Plan

**Round**: R18.Reset.1b
**Data preparazione**: 2026-07-05T07:10Z
**Autore**: e1 main agent (autorizzato PM decision GO A)
**Status**: PLAN READY — **APPLY BLOCCATO** in attesa di sign-off PM esplicito

⚠️ Questo documento descrive il piano di apply. L'esecuzione reale richiede un nuovo brief PM con OK esplicito. Gli script apply/rollback sono presenti nel repo ma **default dry-run**, con doppia safety gate (§15).

---

## 1. Executive Summary

R18.Reset.1b applica un **fresh start globale** di tutte le 672 guild dell'ambiente Orbus preservando `guild.name` + `guild.owner_user_id` + `users.*` e resettando tutto il resto. Zero real users in produzione (verificato R18.Reset.1a). Zero collezioni premium/billing. Storage archive stimato ~5 MB.

### Decisioni PM sigillate riflesse nel piano

| Decision | Valore | Impact |
|---|---|---|
| **P0-a** | **S1** — reset totale tutte le guild (0 eccezioni) | 672 guild processate |
| **P0-b** | **A.b** — archive + regen 5 starter | 3314 adv archiviati, 3360 adv regen |
| **P0-c** | 100 gold + 3 pozioni base + 0 XP booster | Deterministico |
| **P0-d** | Archive tutti i cosmetici (no preserve live, no founder badge) | pvp+mount+narrative archived |
| **P0-e** | seed_round5 **NON patchato pre-reset** | Verifica post-apply → eventuale R18.3a.3 |
| **P0-f** | Banner R18.3c **suppress** (`migration_banner_r18_3c_dismissed=True`) | No re-show |
| **P1-a** | Retention 90gg minimi, **NO purge automatico** | `_r18_archive` restano intatti |
| **P1-b** | Trigger **CLI script one-shot** | `round18_reset1b_apply.py` con doppio flag |
| **P2-a** | Banner post-reset dismissibile, testo fisso | vedi §10 |

### Numeri attesi post-apply

- Guild preservate: **672** (name + owner + user binding intatti)
- Adventurers archiviati: **3314** in `adventurers_r18_archive`
- Adventurers regen: **672 × 5 = 3360**
- Gold totale post: **672 × 100 = 67.200** (era 4.083.608 pre-apply)
- Inventory items regen: **672 × 3 = 2016** (starter potions)
- Cosmetici live post-apply: **0** (5 PvP + 2 mount + 1 narrative archiviati)
- Audit event: **1** `R18_FULL_GUILD_FRESH_START_APPLIED`

---

## 2. Backup Strategy

### Path

Ogni run di apply crea una directory dedicata:
```
/app/backend/backups/r18_reset1b_<UTC_ISO_timestamp>/
```

Esempio: `/app/backend/backups/r18_reset1b_20260710T130000Z/`

### Formato

**JSONL per collection** (JSON Lines: 1 doc per riga). Motivazione: `mongodump` non è garantito nell'env container; JSONL è indipendente da tool esterni, human-readable, restore trivial via `insert_many` in un round dedicato.

File attesi (34 collections: 33 archive + `guilds`):
```
manifest.json                          — indice + checksum
adventurers.jsonl
inventory_items.jsonl
equipped_items.jsonl
class_halls.jsonl
achievement_progress.jsonl
expeditions.jsonl
expedition_members.jsonl
...
guilds.jsonl                           — importante per restore identity
```

### Manifest schema

```json
{
  "round": "R18.Reset.1b",
  "created_at": "2026-07-XX",
  "backup_path": "...",
  "collections": [
    {"name": "adventurers", "doc_count": 3314,
     "file": ".../adventurers.jsonl", "sha256": "..."},
    ...
  ]
}
```

Ogni file JSONL ha un SHA-256 nel manifest per integrity check pre-restore.

### Retention

- **Minimum**: 90 giorni (P1-a)
- **Cleanup**: **manuale**, richiede nuovo OK PM. NO cron job. NO auto-purge.
- **Nota**: il backup JSONL è indipendente dalle sibling collections `_r18_archive`. Il rollback può usare entrambi (archive è primario, JSONL è fallback se archive è stato droppato).

---

## 3. Archive Collections Mapping

Ogni collection viene copiata (via `aggregate $out`) in una sibling con suffisso `_r18_archive`. Zero hard delete sull'archive.

| Live collection | Archive sibling |
|---|---|
| `adventurers` | `adventurers_r18_archive` |
| `inventory_items` | `inventory_items_r18_archive` |
| `equipped_items` | `equipped_items_r18_archive` |
| `class_halls` | `class_halls_r18_archive` |
| `achievement_progress` | `achievement_progress_r18_archive` |
| `expeditions` | `expeditions_r18_archive` |
| `expedition_members` | `expedition_members_r18_archive` |
| `raids` | `raids_r18_archive` |
| `raid_participants` | `raid_participants_r18_archive` |
| `chat_messages` | `chat_messages_r18_archive` |
| `squads` | `squads_r18_archive` |
| `guild_structures` | `guild_structures_r18_archive` |
| `guild_specialization_choice` | `guild_specialization_choice_r18_archive` |
| `guild_trade_pacts` | `guild_trade_pacts_r18_archive` |
| `guild_site_income_ledger` | `guild_site_income_ledger_r18_archive` |
| `guild_world_presence` | `guild_world_presence_r18_archive` |
| `guild_xp_daily_cap_tracker` | `guild_xp_daily_cap_tracker_r18_archive` |
| `pvp_seasons` | `pvp_seasons_r18_archive` |
| `pvp_season_leaderboards` | `pvp_season_leaderboards_r18_archive` |
| `pvp_defense_teams` | `pvp_defense_teams_r18_archive` |
| `pvp_cosmetics_unlocked` | `pvp_cosmetics_unlocked_r18_archive` |
| `guild_mount_ownership` | `guild_mount_ownership_r18_archive` |
| `narrative_rewards_unlocked` | `narrative_rewards_unlocked_r18_archive` |
| `continent_leaderboard_snapshots` | `continent_leaderboard_snapshots_r18_archive` |
| `continent_event_instances` | `continent_event_instances_r18_archive` |
| `seasons` | `seasons_r18_archive` |
| `season_participations` | `season_participations_r18_archive` |
| `season_rewards` | `season_rewards_r18_archive` |
| `world_boss_events` | `world_boss_events_r18_archive` |
| `recruitment_offers` | `recruitment_offers_r18_archive` |
| `shop_daily_offers` | `shop_daily_offers_r18_archive` |
| `tester_tool_snapshots` | `tester_tool_snapshots_r18_archive` |

**Totale**: 32 collections archiviate. `guilds` NON è archiviata via sibling (identità preservata in-place; è comunque nel backup JSONL).

---

## 4. Apply Steps (step-by-step)

Ogni step ha **pre-condition** e **post-condition** verificabile.

| # | Step | Pre-condition | Post-condition |
|---|---|---|---|
| S0 | Parse args + safety gate | `--apply` + `--i-understand-...` presenti | `mode = APPLY` |
| S1 | Idempotency check | `audit_log.event_type = R18_FULL_GUILD_FRESH_START_APPLIED` count = 0 | Ok procedere. Altrimenti exit=2 |
| S2 | Backup snapshot | Directory `backups/r18_reset1b_<ts>/` scrivibile | 33 file JSONL + manifest.json creati, SHA-256 registrato |
| S3 | Archive step | Le collections live esistono | 32 sibling `_r18_archive` create con count == live pre-count |
| S4 | Wipe live step | Archive OK (S3 assertion) | Le 32 collections live hanno count = 0 |
| S5 | Reset guild fields | 672 guild presenti | Tutte le 672 hanno `level=1, gold=100, reputation=0, r18_reset1b_applied=True, ...` |
| S6 | Regen starter roster | Guild reset OK; safe pool = 11 classi | `adventurers` count = 3360 (672 × 5); ogni adv con `class_slug ∈ SAFE_STARTER_SLUGS`, `r18_reset1b_starter=True` |
| S7 | Regen starter kit | Item `minor_healing_potion` presente nel catalog | `inventory_items` count = 2016 (672 × 3 potions), tutti con `r18_reset1b_starter_kit=True` |
| S8 | Emit audit event | Precedenti step OK | Audit log include 1 evento `R18_FULL_GUILD_FRESH_START_APPLIED` con metadata full |
| S9 | Log summary | — | Stdout riporta JSON summary completo |

### Assertion nel codice

- S3 verifica `pre_count == post_count` per ogni collection archiviata → `AssertionError` se mismatch
- S6 usa `_deterministic_rng_for_guild(guild_id)` per riproducibilità del rollback: stesso seed = stessi 5 slug

### Ordine strict

Gli step S3 → S4 → S5 → S6 → S7 → S8 sono **sequenziali**. Se uno fallisce, gli step successivi sono skippati e serve rollback esplicito.

---

## 5. Identity Preservation Contract

### Preservato per ogni guild (immutato)

| Field | Semantica |
|---|---|
| `_id` (ObjectId) | Identity DB |
| `id` (UUID) | Identity applicativa |
| `public_id` | Public reference |
| `owner_user_id` | Binding user (login) |
| `name` | **Player-facing identity** — MAI toccato |
| `created_at` | Storicità (data creazione originale) |
| `email` (se presente) | Backref owner |
| `is_test`, `is_test_artifact`, `is_grandfathered`, `is_demo_opponent` | Tag semantici |

### Preservato a livello collection

- `users` — INTERA collection intatta (340 doc)
- `refresh_tokens` — intatta (1722 doc)
- `login_attempts`, `password_reset_tokens` — intatte
- `audit_log`, `audit_logs`, `audit_events` — **APPEND-ONLY invariante** (11884 doc)
- Tutti i catalogs (30 collections, ~1500 doc) — vedi `CATALOG_INVARIANT` nel codice

### Cosa va (archiviato in `_r18_archive` + rimosso dal live)

- Adventurers (3314), inventory (111), equipped (20)
- Achievement progress (1686)
- Cosmetici earned (8: 5 pvp + 2 mount + 1 narrative)
- Expeditions/raids/season history
- Structures, trade pacts, income ledger, ecc.

### Cosa viene rigenerato

- 5 adventurers starter per guild (deterministico via RNG seed)
- 3 minor healing potions per guild in inventory
- Guild fields reset a starter values (level=1, gold=100, reputation=0, max_roster_cap=10, ecc.)

---

## 6. Starter Roster Regen Algorithm

### Pool safe (11 classi legacy)

```
alchemist, bard, druid, mage, monk,
paladin, priest, ranger, rogue, warlock, warrior
```

**Blacklist esplicita** (safety net):
```
cacciatore_di_mostri, cacciatore_del_vuoto
```

Verificato in R18.Reset.1a: `filter_safe_class_pool` post-R18.3a.2 restituisce esattamente questo pool.

### RNG deterministico

Ogni guild ha il proprio seed **derivato dal `guild_id`**:

```python
digest = hashlib.sha256(f"r18_reset1b:{guild_id}".encode()).hexdigest()
seed = int(digest[:16], 16)   # 64 bit
rng = random.Random(seed)
picks = [rng.choice(SAFE_STARTER_SLUGS) for _ in range(5)]
```

### Motivazione

- **Riproducibilità del rollback**: se serve ricalcolare, stesso guild_id → stessi 5 slug. Utile per testing/QA.
- **Zero dipendenza da DB live pool**: usiamo whitelist hardcoded (11 slug) invece di `filter_safe_class_pool` runtime. Se domani il catalog cambia, il regen resta stabile.
- **Zero uso di `seed_round5`** (P0-e): il regen è totalmente in-round, non passa dalla routine legacy.

### Documento adventurer starter

Ogni adv creato ha:
```json
{
  "id": "<uuid4>",
  "guild_id": "<guild.id>",
  "class_slug": "<safe_slug>",
  "name": "Starter 1..5",
  "level": 1,
  "xp": 0,
  "grade": "F",
  "hp_current": 100,
  "hp_max": 100,
  "status": "idle",
  "created_at": "<ISO>",
  "r18_reset1b_starter": true,
  "r18_reset1b_seed_source": "sha256(r18_reset1b:<guild_id>)"
}
```

**Nota**: `base_strength/base_agility/base_intellect/base_endurance/base_faith` NON vengono impostati dal regen (rimangono al valore default MongoDB, cioè assenti). Il combat runtime li leggerà dal catalog `adventurer_classes` via lookup (pattern esistente).

---

## 7. Starter Kit Regen Payload

### Per ogni guild

| Item | Quantità | Note |
|---|---|---|
| **Gold** | **100** | Già impostato in `_reset_guild_fields` (`guilds.gold=100`) |
| **Minor Healing Potion** | **3** | 3 doc in `inventory_items` con `item_slug=minor_healing_potion, quantity=1` |
| **XP Booster** | **0** | P0-c esplicito: no XP payload |

### Slug canonico item verificato

⚠️ **Nota importante**: il brief PM diceva "3 pozioni base". Il catalog live (verificato 2026-07-05 read-only) contiene:
- `minor_healing_potion` (nome UI: "Minor Healing Potion") ✅ presente
- `healing_herb` (herb, non potion) — non usato
- `basic_healing_potion` — **non esiste**

Il piano usa `minor_healing_potion` come slug canonico. Se PM vuole slug diverso, sostituire la costante `STARTER_POTION_ITEM_SLUG` nello script prima dell'apply.

### Fallback defensivo

Lo script include un check: se `items.find_one({slug: minor_healing_potion})` restituisce `None` in apply mode, **skippa la creazione delle pozioni** e logga WARN. Non blocca l'apply (le gilde comunque hanno 100 gold e possono comprare pozioni via shop).

---

## 8. Cosmetics Archive Handling

Tutti i cosmetici earned vanno archiviati (P0-d):

| Collection | Doc count | Archive target |
|---|---|---|
| `pvp_cosmetics_unlocked` | 5 | `pvp_cosmetics_unlocked_r18_archive` |
| `guild_mount_ownership` | 2 | `guild_mount_ownership_r18_archive` |
| `narrative_rewards_unlocked` | 1 | `narrative_rewards_unlocked_r18_archive` |
| **Totale** | **8** | 3 archive collections |

### Zero preserve live

Nessun cosmetico resta player-facing dopo il reset. **NO founder badge**, **NO hall of fame**, **NO "prima era" title** in R18.Reset.1b. Se PM vuole compensation cosmetica, richiede round successivo dedicato (R18.Reset.2 candidate).

### Recovery via archive

I cosmetici sono comunque accessibili in read-only tramite le sibling `_r18_archive` per admin/audit debug. Il rollback (§12) li ripristina live se richiesto.

---

## 9. Banner R18.3c Suppression Logic

### Meccanismo

Il campo `guilds.migration_banner_r18_3c_dismissed` viene impostato a `True` in tutte le guild (`_reset_guild_fields` step S5). Questo fa sì che l'endpoint `GET /api/guilds/me/migration-banner` (R18.3c) restituisca banner=null (già-dismisso).

### Verifica post-apply

Il tester brief (§11 del tester brief) include: verifica che `GET /api/guilds/me/migration-banner` per una guild resettata NON mostri il banner R18.3c.

### Motivazione

- R18.3c banner comunicava la migration orphan-classes → paladin/cacciatori
- Post R18.Reset.1b, la storia degli orphan è archiviata (in `adventurers_r18_archive`)
- Il player vedrà solo il nuovo banner R18.Reset.0 (§10) che è il messaggio del fresh start

---

## 10. Post-Reset Banner P2-a Design

### Testo fisso (byte-exact IT)

> **Le gilde sono state riallineate per il nuovo inizio di Orbus. Il nome della tua gilda è stato preservato; progressi, roster e risorse sono ripartiti da zero.**

### Semantica

- Nessun riferimento a bug, test data, reset interno, R18, migration, dry-run
- Zero jargon tecnico
- Messaggio positivo focalizzato su "nuovo inizio" + rassicurazione ("nome preservato")

### Comportamento

- **Dismissibile**: sì (button "Ho capito" / "Inizia")
- **Mostra una sola volta**: flag `guilds.r18_reset1b_banner_dismissed` (default `False` post-reset, `True` dopo dismiss)
- **Endpoint suggeriti** (per apply frontend futuro, NON in scope R18.Reset.1b):
  - `GET /api/guilds/me/reset1b-banner` → `{show: true/false, message: "..."}`
  - `POST /api/guilds/me/reset1b-banner/dismiss` → `{show: false}`
- **Component name suggerito**: `ResetWelcomeBannerR18Reset1b.jsx`

### Scope

⚠️ **Il banner UI NON viene implementato in R18.Reset.1b**. Solo il flag DB è pronto (`r18_reset1b_banner_dismissed=False` in reset). L'implementazione frontend è deferrita a round successivo (R18.Reset.2 candidate).

---

## 11. seed_round5 Post-Reset Verification Plan

### Direttiva PM

**P0-e**: NON patchare `seed_round5` pre-reset. R18.Reset.1b non deve dipendere da `seed_round5`.

### Cosa fa R18.Reset.1b per evitare dipendenza

- `_regen_starter_roster` usa **whitelist statica** `SAFE_STARTER_SLUGS` (11 slug hardcoded), non chiama `filter_safe_class_pool` né `seed_round5.starter_backfill`
- Il regen scrive direttamente in `adventurers` via `insert_many`

### Verifica post-apply

Il tester brief include:
1. Grep log backend post-apply per `orbus.seed_round5.*starter backfill failed`
2. Se il warning **persiste**: aprire `R18.3a.3` hotfix separato (patch 1-riga simmetrica a R18.3a.2 in `seed_round5.py`)
3. Se il warning **è sparito** (probabile: nessuna guild ha roster < threshold, seed_round5 non entra nel branch che falliva): warning obsoleto, skip patch

### Rischio residuo

**BASSO**. Il warning è catturato da try/except in `seed_round5`, non causa HTTP 500 né corruzione dati. Nessun impatto player-facing.

---

## 12. Rollback Plan

### Comando

```bash
# 1. Dry-run rollback (safe)
cd /app/backend && python -m app.scripts.round18_reset1b_rollback

# 2. Rollback reale
cd /app/backend && python -m app.scripts.round18_reset1b_rollback --confirm-rollback
```

### Step-by-step

1. **Pre-condition checks**:
   - Audit event `R18_FULL_GUILD_FRESH_START_APPLIED` presente → apply è stato eseguito
   - Audit event `R18_FULL_GUILD_FRESH_START_ROLLED_BACK` **NON** presente → no doppio rollback
   - Almeno una `_r18_archive` con doc > 0

2. **Restore step** (per ogni ARCHIVE_COLLECTIONS):
   - Fetch tutti i doc da `<name>_r18_archive`
   - Wipe live: `delete_many({})` sulla live
   - Reinsert: `insert_many(docs_from_archive)`
   - **`_r18_archive` resta intatta** (idempotenza inversa)

3. **Unset guild reset markers**:
   - `r18_reset1b_applied = False`
   - `r18_reset1b_applied_at = None`
   - `r18_reset1b_banner_dismissed = None`
   - ⚠️ **NOTA HARD BLOCKER**: `gold/level/reputation/prestige/resources/progression fields` originali NON sono ripristinati automaticamente da questo step (guild non è in ARCHIVE_COLLECTIONS). Per restore completo dell'identity serve `restore_from_jsonl_manifest.py` con verifica `sha256 manifest` — round dedicato **R18.Reset.1c**, che è **hard prerequisite blocker** (non opzionale) per l'apply reale di R18.Reset.1b.

4. **Audit event**: emit `R18_FULL_GUILD_FRESH_START_ROLLED_BACK` con summary metadata

### Time-to-rollback

Stimato: **60-120 secondi** per ~7500 doc totali su 32 collections.

### Retention window

**90 giorni minimi** su `_r18_archive` (P1-a). Nessun purge automatico. Cleanup richiede nuovo OK PM.

### Limitazione nota rollback (senza R18.Reset.1c)

Il rollback da `_r18_archive` **NON ripristina automaticamente** i seguenti campi delle guild:

- `gold`
- `level`
- `reputation`
- `prestige`
- `resources`
- `progression fields` (qualsiasi campo state/progress dinamico)

Questi campi sono modificati in-place durante l'apply (step S5 `_reset_guild_fields`) e richiedono restore da backup JSONL + `sha256 manifest` (round dedicato **R18.Reset.1c**).

**R18.Reset.1c è hard prerequisite blocker** — non opzionale, non hotfix, non "se necessario". Nessuna scorciatoia è ammessa: l'apply reale di R18.Reset.1b resta bloccato finché R18.Reset.1c non è PASS e il tool `restore_from_jsonl_manifest.py` non è verificato in dry-run.

---

## 13. Expected Counts Post-Apply

> ⚠️ **Nota importante — reference at plan-time.** I numeri riportati in questa sezione (672 guilds, 3314 adventurers pre-archive, 3360 adv regen, gold totale 4.083.608 → 67.200, 2016 potions) sono **reference at plan-time** derivati dallo snapshot R18.Reset.1a del 2026-07-05. **NON sono autorevoli.** Il count autorevole verrà rilevato al momento dell'apply reale tramite dry-run immediatamente-precedente e `manifest sha256`. Vedi sottosezione **Snapshot-at-Apply Rule** più sotto.

Confronto con snapshot R18.Reset.1a (2026-07-05T06:41Z) — valori **reference at plan-time**, non autorevoli:

| Metrica | Pre-apply (R18.Reset.1a) | Post-apply (atteso) | Delta |
|---|---:|---:|---:|
| Guilds | 672 | **672** | invariato ✓ |
| Users | 340 | **340** | invariato ✓ |
| Adventurers live | 3314 | **3360** | +46 (672×5 regen − 3314 delete + tolleranza test data) |
| Adventurers `_r18_archive` | 0 | **3314** | archive |
| Inventory items live | 111 | **2016** | +1905 (672×3 potions regen − 111 delete) |
| Inventory items `_r18_archive` | 0 | **111** | archive |
| Equipped items live | 20 | **0** | archive |
| Achievement progress live | 1686 | **0** | archive |
| Guild gold sum | 4.083.608 | **67.200** | 672×100 |
| Guild gold avg | 6076.8 | **100** | reset |
| Guild level avg | ~variabile | **1** | reset |
| PvP cosmetics live | 5 | **0** | archive |
| Mount ownership live | 2 | **0** | archive |
| Narrative rewards live | 1 | **0** | archive |
| Audit event `R18_FULL_GUILD_FRESH_START_APPLIED` | 0 | **1** | emit |

### Nota tolleranza test data

Durante il round R18.Reset.1a → 1b, alcuni test agent hanno creato guild sintetiche (`orbus.onboarding - starter roster seeded: guild=... inserted=1..2`). Il conteggio finale può variare di ±20-50 doc rispetto a expected. Documentato per non fare false-positive nel tester brief.

### Snapshot-at-Apply Rule

I numeri qui riportati (672 guilds, 3314 adventurers pre-archive, 3360 adv regen, gold totale 4.083.608 → 67.200, 2016 potions) sono **reference at plan-time** (snapshot R18.Reset.1a del 2026-07-05). Il count autorevole verrà rilevato al momento dell'apply reale tramite dry-run immediatamente-precedente e verifica `manifest sha256`.

**Protocollo obbligatorio pre-apply reale:**

1. Eseguire `round18_reset1b_apply.py` in DRY_RUN immediatamente prima dell'apply reale.
2. Generare snapshot/backup JSONL + `manifest.json` con `sha256` per ogni file.
3. Usare i count del **manifest sha256** come **fonte autorevole** (non i numeri di questo piano, che sono `reference at plan-time`).
4. **Bloccare l'apply** se il manifest non viene generato oppure se la verifica `sha256 manifest` fallisce.
5. Riportare nel report finale post-apply i **count effettivi al momento apply**, non i reference at plan-time.

**NON usare tolerance percentuale come criterio principale.** Il reset globale si basa su **snapshot effettivo** (`manifest sha256` at apply time), non su count statici del piano.

---

## 14. Test Plan Post-Apply

Vedi `/app/memory/r18_reset1b_tester_brief_post_apply.md` (file dedicato).

### Sintesi

Il tester brief post-apply include 12 test cases:
1. Guild identity preservation (name + owner intatti)
2. 5 starter adv per guild, tutti safe classes
3. Kit inventory (3 potions per guild + 100 gold)
4. Gold totale = 67.200
5. `_r18_archive` count integrity (adventurers=3314, ecc.)
6. Zero cosmetici live, tutti archiviati
7. Banner R18.3c non appare per guild resettata
8. Flag banner P2-a `r18_reset1b_banner_dismissed=false`
9. Audit event singolo emesso con metadata corretta
10. Warning seed_round5 verificato (pass o hotfix R18.3a.3 richiesto)
11. Idempotency: secondo run apply → exit=2 con messaggio
12. Rollback script eseguibile in dry-run senza errori

---

## 15. Safety Checks Pre-Apply

### Flag richiesti (obbligatori entrambi)

```bash
--apply
--i-understand-this-will-reset-all-guilds
```

Se uno o entrambi mancano → script rimane in dry-run + WARN log.

### Timestamp check

Ogni run genera un timestamp UTC ISO per la directory di backup. Formato: `%Y%m%dT%H%M%SZ`. Esempio: `20260710T130000Z`.

### Hash sorgente (opzionale, PM può richiedere)

Se il PM vuole assicurarsi che lo script eseguito sia esattamente quello reviewato, aggiungere una post-condition manual check:

```bash
sha256sum /app/backend/app/scripts/round18_reset1b_apply.py
```

Comparare con hash noto dopo review.

### Verifica no-lock

MongoDB non ha lock table-level su collections normali. Il pattern `aggregate $out` è atomico. Nessuna verifica lock necessaria in ambiente attuale.

### Feature flag double-gate

Verificare che `R18_REWORK_ENABLED=false` e `R18_TALENT_ENGINE_ENABLED=false` restino OFF durante e dopo l'apply. Il reset non tocca feature flags.

---

## 16. Human Approval Gate — R18.Reset.1b APPLY

⚠️ **APPLY BLOCKED until ALL of the following are satisfied (HARD BLOCKERS — 7 gates, updated by R18.Reset.1b.hotfix):** ⚠️

1. ✅ **R18.Reset.1c** rollback completeness PASS — **SATISFIED 2026-07-05T08:18:11Z**
2. ✅ `restore_from_jsonl_manifest.py` verified — **SATISFIED** (10/10 tester PASS, dry-run + fake fixture)
3. ✅ `sha256 manifest` verification PASS — **SATISFIED** (HARD STOP runtime verified via test 4 mismatch)
4. ☐ **PM sign-off renewed** — **PENDING** (conditional on R18.Reset.1b.ops PASS + staged pre-apply verify + hotfix acceptance + write_freeze_full PASS)
5. ✅ **Backend maintenance mode / write-freeze** — **SATISFIED 2026-07-05T08:36:37Z** (R18.Reset.1b.ops SEALED, 8/8 tester PASS, middleware `/app/backend/app/core/maintenance.py` wired in `app_factory.py`, playbook `/app/memory/r18_reset1b_ops_write_freeze_playbook.md`)
6. ✅ **R18.Reset.1b.hotfix — Starter Kit Inventory Unique Index Fix** — **SATISFIED 2026-07-05T09:48:57Z** (sibling script `/app/backend/app/scripts/round18_reset1b_apply_v1_1.py` sha256 `43ca97f284b50706cf450bf4a0dc8e6b977aa195547bc69e99a80da55ede3031`, 12/12 tests PASS in `/app/backend/tests/backend_round1b_hotfix_starter_kit_test.py` sha256 `bf26da31dce950256c0ec6e92b180fdfa6e82fdd308004c454b82ff712a755ec`, sealed originale INTATTO — preflight/postflight in `/app/memory/r18_reset1b_hotfix_sealed_preflight.json` + `_postflight.json`)
7. ☐ **R18.Reset.1b.hotfix.write_freeze_full PASS** — **PENDING** (round non ancora avviato; env var `ORBUS_INTERNAL_JOB_FREEZE` letta dai job async interni per bloccare `orbus.onboarding.starter_roster` + seed durante l'apply; HARD PREREQUISITE per real apply post-hotfix — id `r18_reset1b_hotfix_write_freeze_full_pass`)

**Status:** APPLY BLOCKED, **2 of 7 gates pending** (gate 4, gate 7). `APPLY_BLOCKED_2_OF_7_GATES_PENDING`.

**Gate satisfaction summary:** gates satisfied: **5 / 7**.

**Nota hotfix (gate 6):** Il nuovo apply reale DEVE usare
`round18_reset1b_apply_v1_1.py` (NON il sealed originale
`round18_reset1b_apply.py`). Il sealed originale resta preservato per
audit trail. Il rollback via `round18_reset1b_rollback.py` continua a
funzionare invariato (v1.1 emette entrambi gli audit event
`R18_FULL_GUILD_FRESH_START_APPLIED` + `..._V1_1`).

**Nota gate 7 (write_freeze_full):** Il maintenance middleware R18.Reset.1b.ops
copre solo HTTP request. I job async interni (es.
`orbus.onboarding.starter_roster`, seed loops) bypassano il freeze e
possono introdurre drift durante l'apply reale. Il round
`R18.Reset.1b.hotfix.write_freeze_full` chiude questo gap architetturale
prima del real apply post-hotfix.

**While these gates are NOT all satisfied:**

- **NO reset apply**
- **NO archive apply**
- **NO starter regen live**
- **NO guild gold/resources reset**
- **NO DB write**
- **NO banner UI activation**
- **NO audit event `R18_FULL_GUILD_FRESH_START_APPLIED` emission**

**Sign-off request format (for PM):**

> "R18.Reset.1b APPLY APPROVED. R18.Reset.1c PASS confirmed. Execute `--apply --i-understand-this-will-reset-all-guilds` with backup mandatory."

Finché i 4 gate non sono tutti verdi, gli script restano nel repo ma **DEFAULT DRY-RUN**. Nessuna esecuzione automatica. Nessun git commit automatico.

### Blocker check pre-approval (checklist review PM)

- [ ] Slug potion (`minor_healing_potion`) accettabile
- [ ] Retention 90gg minimi accettabile
- [ ] Testo banner P2-a byte-exact accettabile
- [ ] Warning `seed_round5` deferrito post-apply accettabile
- [ ] Guild fields (`gold`, `level`, `reputation`, `prestige`, `resources`, `progression fields`) originali restoreabili SOLO tramite **R18.Reset.1c** (JSONL manifest + `sha256 manifest`) — hard prerequisite blocker confermato, non opzionale
- [ ] Zero UI change deploy in R18.Reset.1b (banner UI = round successivo) accettabile
- [ ] **Snapshot-at-Apply Rule** §13 accettabile (count autorevoli da `manifest sha256` at apply time, non da questo piano)

---

## 17. Scope Exclusions & HOLD/PAUSED Registry

Round e task esplicitamente esclusi da R18.Reset.1b (in HOLD / PAUSED / CANDIDATE / BACKLOG):

- **R18.1.3** — drift backfill (HOLD, obsoleto post-reset)
- **R18.3d** — Stat/Role Mapping Registry (PAUSED, in attesa post-reset)
- **R18.X-Traits** — Traits System Rework (HOLD, backlog P2)
- **R18.X-Fatigue** — Fatigue/Kitchen (HOLD, backlog P2)
- **R17.infra.smtp** — SMTP fix (HOLD, infra deferred)
- **seed_round5** — starter_backfill patch (HOLD, P0-e: no pre-reset patch. Verifica post-apply)
- **R18.3a.3** — seed_round5 symmetric patch (CANDIDATE, solo se warning persiste post-apply)
- **R18.Reset.2** — Banner UI + Compensation cosmetic (CANDIDATE, founder badge / hall of fame se PM decide dopo reset)
- **R18.Tooling** — Generalized Read-Only Live Snapshot Utility (**BACKLOG**, PM approved concept, deferred as "LATER" to avoid scope creep pre-rollback blocker. Candidate after: R18.Reset.1c, R18.Reset.1b apply, R18.Reset.2)
- **R18.Tooling.PreSealContract** — `pre_seal_grep_contract.py` — automated grep contract validator (**BACKLOG**, PM approved concept but deferred; utile per round futuri, non deve bloccare R18.Reset.1c. Candidate after: R18.Reset.1c, R18.Reset.1b apply, R18.Reset.2)
- **R18.Tooling.DryRunReport** — `--dry-run-report` machine-readable summary for CI/CD gating (**BACKLOG**, PM approved concept, deferred: utile per CI/CD ma fuori scope write-freeze. Candidate after: R18.Reset.1b.ops, R18.Reset.1b apply)
- **R18.Reset.1b.ops** — Backend Write-Freeze Maintenance Mode (**CLOSED & SEALED 2026-07-05T08:36:37Z**, gate 5 §16 satisfied, 8/8 tester PASS)
- **R18.Tooling.HealthMaintenanceEndpoint** — `GET /api/health/maintenance` diagnostic endpoint (**BACKLOG**, PM approved concept, deferred: utile per monitoring esterno pre/post-apply ma non blocking. Candidate after: R18.Reset.1b apply, R18.Reset.2)
- **R18.Infra.PreviewApiRoutingCheck** — Preview edge `/api/*` returns 404 while `localhost:8001` works (**BACKLOG**, finding rilevato durante tester 1b.ops verification. Non blocca il reset. Preview edge routing va indagato in un round infra separato. Candidate after: R18.Reset.1b apply)
- **R18.Reset.1c.cleanup** — Rollback Residual Guild Flags Cleanup (**CLOSED & SEALED 2026-07-05T09:31:08Z**, 3 field residui rimossi da 672 guild, CTRL 7 PASS, CTRL 4 delta +2 accepted as benign onboarding drift covered by Snapshot-at-Apply Rule §13. Audit CLEANUP=1, APPLIED=0, ROLLED_BACK=1. Tool 1c sealed integrity: INVARIATA.)
- **R18.Reset.1b.hotfix.write_freeze_full** — Extend MaintenanceMiddleware to internal async jobs (**BACKLOG**, gap architetturale rilevato durante R18.Reset.1c.cleanup CTRL 4: job async interni bypassano il write-freeze middleware. Candidate: env var `ORBUS_INTERNAL_JOB_FREEZE` letta dai job onboarding/seed. Candidate after: R18.Reset.1b.hotfix, R18.Reset.2)
- **R18.Reset.1b.hotfix** — Starter Kit Inventory Unique Index Fix (**IMPLEMENTED 2026-07-05T09:48:57Z**, sibling script `round18_reset1b_apply_v1_1.py` creato, sealed intatto, 12/12 test PASS, gate §16 gate 6 SATISFIED. In attesa PM acceptance per apply reale post-hotfix + `R18.Reset.1b.hotfix.write_freeze_full` hard gate.)

---

## Firma

**R18.Reset.1b PLAN READY — APPLY BLOCCATO.**

*Firma: e1 main agent — 2026-07-05T07:10Z*

Attendo OK esplicito PM per esecuzione.
