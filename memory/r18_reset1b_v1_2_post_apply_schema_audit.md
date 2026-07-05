# R18.Reset.1b.hotfix.v1_2 — POST-APPLY SCHEMA AUDIT (READ-ONLY)

**Data**: 2026-07-05T13:52:00Z UTC
**Autore**: e1_dev
**Tipo**: Deep Audit Read-Only (Opzione C autorizzata dal PM)
**Vincoli rispettati**: ✅ Zero DB write · ✅ Zero rollback · ✅ Zero hotfix · ✅ Zero patch · ✅ Zero freeze-off · ✅ Zero apply-retry
**Freeze status**: `orbus_maintenance.flag` = ACTIVE · `orbus_internal_job_freeze.flag` = ACTIVE
**apply_id v1.2**: `5815c73c-dae7-447c-ac3c-70455d3099a3`

---

## 1. Executive Summary

- **1 campo runtime-critical** mancante su 3360/3360 adventurers post-apply: `adventurer_class_id` — causa il `KeyError` in `adventurer_public()` e HTTP 500 su `GET /api/adventurers`.
- 41 campi mancanti **non-critical** (soft access via `.get()` o non usati dagli endpoint attualmente attivi).
- **Mapping deterministico `class_slug → adventurer_class_id` disponibile per 11/11 classi safe** con id univoco su ognuna (nessun duplicato).
- Catalog `adventurer_classes` contiene 18 doc totali; le 11 classi safe usate dallo starter roster hanno tutte `base_strength/agility/intellect/endurance/faith` popolati (coerente con la logica v1.2).
- **Fresh backup pre-apply INTATTO**: 33/33 file jsonl con sha256 line-by-line PASS. Rollback deterministico.
- **Raccomandazione tecnica e1_dev**: **B — HOTFIX v1.3** (con caveat esplicitati in §10).

## 2. Root Cause Confermata

### 2.1 Errore runtime
```
File "/app/backend/app/adventurers/services.py", line 195, in adventurer_public
    "adventurer_class_id": doc["adventurer_class_id"],
KeyError: 'adventurer_class_id'
```

### 2.2 Sample doc PRE-APPLY (backup jsonl `20260705T134230Z`)
Adventurer `Vera` (id `0c0dd04b-cac4-4c1c-b284-641271d8c11f`), 31 campi:
```json
{
  "id": "0c0dd04b-cac4-4c1c-b284-641271d8c11f",
  "guild_id": "9a48d6ef-51fc-4183-a0bd-803ce4f5e781",
  "name": "Vera",
  "adventurer_class_id": "47f07561-2e93-4149-936f-2260f117836b",  ← FK OK
  "class_name": "Cacciatore di Mostri",
  "class_role": "DPS",
  "rarity": "Common",
  "level": 1, "experience": 0,
  "strength": 7, "agility": 7, "intellect": 3, "endurance": 4, "faith": 4,
  "stamina": 100, "morale": 100,
  "traits": [ { …Quick Learner… } ],
  "is_available": true, "is_starter": true,
  "created_at": "2026-07-01…", "updated_at": "2026-07-04…",
  "phase13_unbaked": true,
  "class_slug": "cacciatore_di_mostri",
  "grade": "common",
  "r18_grade_backfilled_at": "…", "r18_grade_note": "…",
  "career_history": […],
  "migration_reason": "…", "migration_round": "…", "migration_timestamp": "…"
}
```

### 2.3 Sample doc POST-APPLY (live DB)
Adventurer `Starter 1` (id `b2d44a2e-53c3-4493-97b1-a3832af4d0b5`), 22 campi:
```json
{
  "id": "b2d44a2e-53c3-4493-97b1-a3832af4d0b5",
  "guild_id": "57ae4e07-7fbe-44f2-b297-f5c0f42f6540",
  "class_slug": "rogue",                          ← presente
  "name": "Starter 1",
  "level": 1, "xp": 0,                            ← nota: "xp" non "experience"
  "grade": "F",
  "strength": 5, "agility": 9, "intellect": 3, "endurance": 4, "faith": 2,
  "hp_current": 100, "hp_max": 100,
  "status": "idle",
  "created_at": "2026-07-05…", "updated_at": "2026-07-05…",
  "r18_reset1b_starter": true,
  "r18_reset1b_hotfix_v1_2": true,
  "r18_reset1b_seed_source": "sha256(r18_reset1b:57ae4e07-…)",
  "r18_reset1b_stat_source": "adventurer_classes.base_*_catalog_lookup",
  "phase13_unbaked": true
}
```
**Differenza chiave**: assenza di `adventurer_class_id`, `experience`,
`is_available`, `class_name`, `class_role`, `rarity`, `stamina`,
`morale`, `traits`, `is_starter` (semantico → sostituito da
`r18_reset1b_starter`), `grade` = `F` invece di `common`, e uso di
`xp` invece di `experience`. Extra fields v1.2: `hp_current`, `hp_max`,
`status`.

## 3. Schema Diff Pre/Post — Campi Rilevanti

| Field | pre exists % | pre non-null % | post exists % | post non-null % | type_pre | type_post | Status |
|:---|---:|---:|---:|---:|:---|:---|:---:|
| `adventurer_class_id` | 99.06 | 99.06 | **0.00** | 0.00 | str | — | 🔴 MISSING_POST |
| `class_slug` | 100 | 100 | 100 | 100 | str | str | OK |
| `guild_id` / `id` / `name` | 100 | 100 | 100 | 100 | str | str | OK |
| `level` | 100 | 100 | 100 | 100 | int | int | OK |
| `experience` | 99.06 | 99.06 | **0.00** | 0.00 | int | — | ⚠️ MISSING_POST (soft access in `adventurer_public`) |
| `xp` | 0.00 | 0.00 | 100 | 100 | — | int | ⚠️ NEW_POST (v1.2 field) |
| `grade` | 99.06 | 99.06 | 100 | 100 | str | str | ⚠️ VALUES CHANGED (`common/F/A…` → `F` uniform) |
| `rarity` | 99.06 | 99.06 | 0 | 0 | str | — | non-critical |
| `class_name` / `class_role` | 99.06 | 99.06 | 0 | 0 | str | — | non-critical (soft) |
| `strength/agility/intellect/endurance/faith` | 99.06 | 99.06 | 100 | 100 | int | int | OK |
| `hp_current` / `hp_max` | 0 | 0 | 100 | 100 | — | int | NEW_POST |
| `status` | 0 | 0 | 100 | 100 | — | str | NEW_POST (`idle`) |
| `is_available` | 99.06 | 99.06 | 0 | 0 | bool | — | ⚠️ MISSING_POST (soft in `adventurer_public`, hard in `expeditions/services.py:421`) |
| `stamina` / `morale` | 99.06 | 99.06 | 0 | 0 | int | — | non-critical (soft) |
| `traits` | 99.06 | 99.06 | 0 | 0 | list | — | non-critical |
| `is_starter` | 99.06 | 99.06 | 0 | 0 | bool | — | sostituito da `r18_reset1b_starter` |
| `class` / `class_name` / `role` | 99.06 | 99.06 | 0 | 0 | str | — | non-critical (legacy) |
| `career_history` / `migration_*` | var | var | 0 | 0 | list/str | — | drift storico, atteso post-reset |
| `created_at` / `updated_at` | 100 | 100 | 100 | 100 | str | str | OK |
| `phase13_unbaked` | 100 | 100 | 100 | 100 | bool | bool | OK |

Dettaglio completo di tutti i 42 campi missing_universally: vedi
`/app/memory/r18_reset1b_v1_2_post_apply_schema_audit.json`
(sezione `schema_diff`).

## 4. Campi Mancanti Runtime-Critical

Definizione: usati con **hard access** `doc["<field>"]` da funzioni
raggiungibili in flussi attualmente attivi.

| Field | Impatto | File:Line | Severità |
|:---|:---|:---|:---:|
| `adventurer_class_id` | `GET /api/adventurers` (500), `adventurer_public()` serialization | `adventurers/services.py:195` | **P0 — bloccante** |
| `experience` | Expedition resolve async (XP calc, level-up) | `expeditions/services.py:203,205,419,427` | **P1** (raggiungibile solo dopo POST /expeditions, ora bloccato dal freeze) |
| `is_available` | Expedition resolve async (mark available) | `expeditions/services.py:421` | **P1** (idem) |

**Nota P1**: `expeditions/services.py` hard-accede a `adv["experience"]`
e `adv["is_available"]`. Ma il codepath è invocato SOLO dopo che una
expedition è stata creata e sta per essere risolta. Con freeze attivo
nessuna expedition è creabile, e nessuna è in-flight (backup wipe ha
azzerato `expeditions`). Al momento del rilascio della manutenzione,
se non popolati, il primo POST `/api/expeditions` produrrà 500 alla
risoluzione.

## 5. Campi Mancanti Non-Critical

41 campi, accesso solo via `.get()` in `adventurer_public()` o non usati
dagli endpoint core. Elencati integralmente:
`archived, archived_by_tester_tool, career_history, class, class_name,
class_role, expedition_in_progress, frozen, is_available (soft in
adventurer_public), is_retired, is_starter, is_test_artifact,
is_test_seed, legacy_class_original, migration_reason, migration_round,
migration_timestamp, morale, needs_reassignment, previous_class_slug,
r18_alias_migrated_at, r18_grade_backfilled_at, r18_grade_note,
r18_orphan_migrated_at, rarity, rename_count, retire_via, retired,
retired_at, retired_by, retirement_reason, role, specialization,
specialization_applied_at, specialization_slug, stamina, stats,
team_power, test_seed_source, traits`.

Impatto: nessun 500 diretto. Dashboard mostrerà valori `null/None`
per campi come `class_name`, `rarity`, `stamina`, `morale`, `traits`.
Ai fini gameplay iniziale (starter roster fresco), semanticamente
accettabile per un reset "F/idle/no-traits".

## 6. Mapping `class_slug → adventurer_class_id` (11/11 classi safe)

Catalog usato: `adventurer_classes` (18 doc totali). Nessun duplicato per
le 11 slug safe. Tutti gli id univoci. Tutti i `base_*` popolati.

| Slug | adventurer_class_id | Unique | base_stats OK |
|:---|:---|:---:|:---:|
| alchemist | `ba0362b6-e69f-4136-9600-1d95ea6fbe05` | ✓ | ✓ |
| bard | `17e0abb7-aab2-453b-8416-49597630e815` | ✓ | ✓ |
| druid | `94e5da79-17b6-42be-8d71-b39a7400cf36` | ✓ | ✓ |
| mage | `a6267904-a813-45b0-94e0-d537db356286` | ✓ | ✓ |
| monk | `26c61b46-0dd6-4cd9-ad50-e3d38e5dfcbe` | ✓ | ✓ |
| paladin | `002f2308-af9e-4419-8e05-2bd663db6015` | ✓ | ✓ |
| priest | `cdc69941-be44-4e4b-bc4c-be8e36c811d8` | ✓ | ✓ |
| ranger | `47f07561-2e93-4149-936f-2260f117836b` | ✓ | ✓ |
| rogue | `48c8160d-c0e1-47b2-bb74-ac7bbf2b229d` | ✓ | ✓ |
| warlock | `395cc067-f278-4f1a-bb5c-9eb76ae58940` | ✓ | ✓ |
| warrior | `a0ea32ac-e912-4733-bebb-2a314cf9cc19` | ✓ | ✓ |

Verifica coerenza: gli stats dei sample generati dal v1.2 coincidono con
i `base_*` del catalog (es. rogue: sample `str=5, agi=9, int=3, end=4,
faith=2` matcha esattamente `base_stats` catalog). Prova che la strategia
"base_stats_exact_no_variance" ha correttamente letto il catalog — solo
NON ha copiato l'`id`.

## 7. Endpoint / Functions Impattati

| File:Line | Funzione | Field mancante | Impatto immediato |
|:---|:---|:---|:---|
| `adventurers/services.py:195` | `adventurer_public()` | `adventurer_class_id` | **500 su `GET /api/adventurers`** (verificato via curl) |
| `expeditions/services.py:203,205,419,427` | `_resolve_expedition_member()` | `experience` | Latent — 500 al prossimo expedition resolve |
| `expeditions/services.py:421` | idem | `is_available` | Latent — idem |
| `recruitment/services.py:110-124` | `_offer_to_public()` (candidati mercato) | `adventurer_class_id`, `class_name`, `class_role`, `rarity`, `experience`, `stamina`, `morale` | **NON impatta**: `recruitment_offers` collezione post-apply = 0 (wipeata). Ma se ricreata (job seeder), impatterà. |
| `squads/services.py` | squad ops | — | Nessun accesso adventurer diretto |
| `pvp/services.py` | pvp ops | — | Nessun accesso adventurer diretto |

## 8. Rischio HOTFIX v1.3 (nuovo sibling, sigilli intatti)

### Pro
- Mapping catalog **deterministico 11/11**.
- Mantiene il beneficio del reset v1.2 (roster stats corretti, no drift).
- Idempotency guard esistente su v1.2 non impatta v1.3 (nuovo audit event).
- Nessun tocco ai 7 sigilli attuali.
- Backup fresh esiste come safety per double-rollback.

### Contro / Attenzioni
- Bisogna decidere se popolare **solo** `adventurer_class_id` o **anche** `experience=0`, `is_available=true`, `is_starter=true`, ed eventualmente `class_name`, `class_role`, `rarity` per la parità semantica.
- Il codebase legge `experience` HARD in expedition resolve → **obbligatorio popolare `experience`** per evitare 500 futuro.
- Il codebase legge `is_available` HARD in expedition resolve → **obbligatorio popolare `is_available`**.
- Il valore di `experience` per starter è chiaramente `0` (già visto nel sample pre `Vera`).
- Il valore di `is_available` per starter è `true` (idle, disponibile).

### Prerequisiti (per un futuro v1.3)
- Nuovo script sibling `round18_reset1b_apply_v1_3.py` (o meglio `round18_reset1b_hotfix_v1_3_field_backfill.py`).
- Idempotency guard su nuovo audit event `R18_FULL_GUILD_FRESH_START_HOTFIX_V1_3_APPLIED`.
- Update solo dei doc con `r18_reset1b_hotfix_v1_2 == true` (targeting sicuro sui 3360 rigenerati).
- `update_many({r18_reset1b_hotfix_v1_2: true}, {$set: {experience: 0, is_available: true}})` + per singola classe con lookup catalog `$set: {adventurer_class_id: <catalog_id>}`.
- Test suite dedicato (sibling test file, non i sigilli).

### Invarianti da verificare in v1.3
- `guild_count` invariato (672).
- `adventurers_live` invariato (3360).
- Nessun altro campo modificato oltre a `adventurer_class_id`, `experience`, `is_available` (+ eventualmente `is_starter=true`).
- Total gold invariato (67 200).
- Audit event count v1.2 invariato (1); nuovo event v1.3 = 1.
- Post-v1.3: `GET /api/adventurers` = 200 (test HTTP live obbligatorio).

### Casi di fallimento
- Se un doc con `class_slug` NON in catalog (edge case impossibile qui: preload v1.2 ha già validato 11/11 al momento dell'apply), l'update fallisce → guard preventivo con `$in: [11_safe_slugs]`.
- Se l'update non è idempotente e viene rieseguito, `experience` potrebbe essere reset a 0 su adventurers che nel frattempo hanno acquisito xp → mitigazione via check `experience: {$exists: false}` OR `is_available: {$exists: false}`.

## 9. Rischio ROLLBACK

### Pro
- Backup fresh **INTATTO**:
  - Path: `/app/backend/backups/r18_reset1b_v1_2_20260705T134230Z/`
  - Manifest sha256 line-by-line **PASS 33/33** file (validato ora).
  - Contiene lo stato esatto pre-apply v1.2 (creato dall'apply stesso).
- Script rollback dedicato SEALED: `round18_reset1c_restore_from_jsonl_manifest.py` (sha256 `453b87c8…`).
- Ritorna a stato completamente conosciuto (3415 adventurers originali).

### Contro / Attenzioni
- **Ritorna al problema originale**: 15 adventurers con stats null nell'archive drift storico (ricorda: v1.2 esisteva PROPRIO per risolvere questo).
- Reintroduce 32 adventurers pre-apply che non avevano `adventurer_class_id` (0.94%), che rimarranno rotti sull'endpoint.
- Perde il roster reset fresco (che era il desiderata PM).
- Audit event `R18_FULL_GUILD_FRESH_START_APPLIED_V1_2` resterà nel log (audit append-only) → futura rieseguzione v1.2 continuerà a essere bloccata dall'idempotency guard: serve un nuovo apply_id o un ulteriore hotfix.

### Prerequisiti
- Comando (NON eseguito):
  ```
  cd /app/backend && python -m app.scripts.round18_reset1c_restore_from_jsonl_manifest \
    --backup-root /app/backend/backups/r18_reset1b_v1_2_20260705T134230Z \
    --apply --i-understand-this-will-restore-full-guild-fresh-start
  ```
- Freeze deve rimanere ATTIVO durante il restore.
- Verifica post-rollback: `GET /api/adventurers` = 200 (verifica se i 32 doc problematici causano ancora 500 su alcune guild — dipende dai guild_id specifici).

### Invarianti attesi post-rollback
- `adventurers_live` = 3415 (o meno se il restore filtra).
- `guilds` = 672 con gold pre-apply (`gold_total ≈ 4 083 643`).
- 100% doc originari con `_id`/`id` invariati.

## 10. Raccomandazione Tecnica e1_dev

### **Preferenza: B — HOTFIX v1.3**

Motivazione:
1. **Chirurgico**: un solo campo hard-critical (`adventurer_class_id`), mapping catalog deterministico 11/11.
2. **Preserva l'obiettivo PM**: il reset v1.2 ha risolto correttamente il problema stats (verificato: 3360/3360 con stats esatti da catalog). Non ha senso perdere questo risultato per un FK mancante.
3. **Include gli altri 2 campi latent-P1**: popolare anche `experience=0` e `is_available=true` per evitare 500 futuri su expedition resolve.
4. **Idempotency safe**: nuovo audit event, targeting mirato su `{r18_reset1b_hotfix_v1_2: true}`.
5. **Backup fresh conservato**: se v1.3 fallisse, il rollback è ancora disponibile.

### Caveat
- Servirà scrivere/SEAL un nuovo script sibling `round18_reset1b_hotfix_v1_3_field_backfill.py` (o nome equivalente).
- Test file dedicato, coverage ≥ 12 punti (mapping, coverage post-fix, HTTP verify live pre-freeze-off).
- Il PM Q5 ("GET /api/adventurers = 200") **DEVE essere HTTP live** questa volta, non proxy DB.

### Se rollback preferito (B non accettato)
Motivazioni valide per rollback:
- Se il PM vuole zero rischio scrittura addizionale.
- Se il PM preferisce riprogettare v1.2 da capo con FK popolato (v1.2b sealed sostitutivo).

## 11. Decisione PM Richiesta

Attendo scelta esplicita tra:

| Opzione | Descrizione | Preferenza e1_dev |
|:---:|:---|:---:|
| **A** | Rollback via `round18_reset1c_restore_from_jsonl_manifest.py` su backup `20260705T134230Z` | — |
| **B** | Hotfix v1.3 — nuovo sibling che popola `adventurer_class_id` + `experience=0` + `is_available=true` sui 3360 doc con `r18_reset1b_hotfix_v1_2: true` | ✓ **preferito** |
| A+B | Rollback poi v1.2b sealed sostitutivo (path lungo) | — |

**Nessuna azione autonoma. Freeze restano attivi. Attendo direttiva.**
