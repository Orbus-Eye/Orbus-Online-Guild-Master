# ROUND 18.3c — Orphan Class Migration Apply Report — CLOSED & SEALED ✅ (2026-07-04T20:47Z)

**Round**: R18.3c · **Mode**: `adventurer_class_slug_only` · **Applied**: **496/496** adv (100%)
**Status**: CLOSED & SEALED — apply reale eseguito, backup safe, rollback pronto, banner IT live, audit event emesso.

---

## 1. Sommario esecutivo

Migration reale dei 496 adventurer orphan legacy → 5 target canonici, **senza toccare** il catalog `adventurer_classes` (mode split R18.3b/R18.3b.1 pending per enum reconciliation). Sub-step completati:

1. ✅ **Backup DB completo** in `/app/memory/backups/round183c_prestart/` via `mongodump --gzip`
2. ✅ **Preflight preconditions** (counts, dispatch-valid, item pool, feature flags) tutti PASS
3. ✅ **Zero player-facing leak** pre-apply verificato via `/api/adventurers` shape check
4. ✅ **Apply 496/496** migrations: `class_slug` + `class_name` (IT display) + metadata append-only + `career_history[]` push
5. ✅ **Zero residual** source slug (0 priest/ranger/warlock/berserker/assassin post-apply)
6. ✅ **Idempotenza**: secondo run = 0 nuove modifiche + audit skip
7. ✅ **Banner UI IT** byte-exact live su `/dashboard` con dismiss endpoint persistente
8. ✅ **Audit event** `R18_CLASS_ORPHAN_MIGRATION_APPLIED` emesso (idempotente)
9. ✅ **Rollback script** eseguibile end-to-end su fixture (test 22 PASS)
10. ✅ **Test suite** 23/23 PASS + **regression cross-round 94/94 PASS**

---

## 2. Migration counts (verified live)

| Source slug | Target slug | Expected | Applied | Residual post-apply |
|---|---|---|---|---|
| `priest` | `paladin` | 190 | **190** | **0** |
| `ranger` | `cacciatore_di_mostri` | 175 | **175** | **0** |
| `warlock` | `cacciatore_del_vuoto` | 128 | **128** | **0** |
| `berserker` | `warrior` | 3 | **3** | **0** |
| `assassin` | `rogue` | 0 | **0** | **0** |
| **TOTAL** | | **496** | **496** | **0** |

**Target counts post-apply** (verify):
- paladin: era 166 → 356 (+190)
- warrior: era 290 → 293 (+3)
- rogue: era 148 → 148 (+0)
- cacciatore_di_mostri: era 0 → 175 (+175)
- cacciatore_del_vuoto: era 0 → 128 (+128)

---

## 3. Field aggiunti per ogni adventurer migrato

**$set** operations (per doc):
```
class_slug          = <target>
class_name          = <target.display_name_it>   # one-shot lookup: "Paladino", "Cacciatore di Mostri", ecc.
previous_class_slug = <source>
migration_round     = "R18.3c"
migration_reason    = "orphan_legacy_class_canonicalization"
migration_timestamp = <ISO UTC>
updated_at          = <ISO UTC>
```

**$push** on embedded array `career_history`:
```json
{
  "event": "class_migration",
  "round": "R18.3c",
  "from": "<source_slug>",
  "to": "<target_slug>",
  "timestamp": "<ISO UTC>"
}
```

**Non modificati** (verificato via test 15):
- `role`, `class_role`, `primary_stat`, `secondary_stats` (recruit-frozen o null)
- `level`, `experience`, `xp`, `grade`, `stamina`, `morale`
- `strength`, `agility`, `intellect`, `endurance`, `faith` (5-stat base)
- `equipment`, `inventory`, `traits`, `items`
- `gold`, `dungeon_history`, `raid_history`
- Catalog `adventurer_classes`: **zero write** in questo round

**Sample migrato** (ranger → cacciatore_di_mostri):
```json
{
  "id": "adv-xxx",
  "name": "Adventurer Name",
  "class_slug": "cacciatore_di_mostri",
  "class_name": "Cacciatore di Mostri",
  "class_role": "DPS",  // ← FROZEN dal recruit, non ricalcolato
  "previous_class_slug": "ranger",
  "migration_round": "R18.3c",
  "migration_reason": "orphan_legacy_class_canonicalization",
  "migration_timestamp": "2026-07-04T20:42:45.499752+00:00",
  "career_history": [
    {"event": "class_migration", "round": "R18.3c", "from": "ranger", "to": "cacciatore_di_mostri", "timestamp": "2026-07-04T20:42:45.499752+00:00"}
  ],
  "level": <preserved>,
  "strength": <preserved>, "agility": <preserved>, ...  // 5-stat intact
}
```

---

## 4. Backup pre-apply

- **Tool**: `mongodump` (version 100.17.0)
- **Format**: BSON gzipped
- **Path**: `/app/memory/backups/round183c_prestart/orbus_r16/`
- **Manifest**: `/app/memory/backups/round183c_prestart/manifest.json`
- **Restore recipe**: `mongorestore --uri=$MONGO_URL --gzip --nsInclude='orbus_r16.adventurers' /app/memory/backups/round183c_prestart/`

---

## 5. Audit event

**Event type**: `R18_CLASS_ORPHAN_MIGRATION_APPLIED` · **Idempotent**: sì (skip su re-run)

Metadata inserita:
```json
{
  "round": "R18.3c",
  "mode": "adventurer_class_slug_only",
  "dry_run_count": 496,
  "applied_count": 496,
  "skipped_count": 0,
  "catalog_role_stat_updates": false,
  "mapping": {
    "priest": "paladin",
    "ranger": "cacciatore_di_mostri",
    "warlock": "cacciatore_del_vuoto",
    "berserker": "warrior",
    "assassin": "rogue"
  },
  "rollback_ready": true,
  "rollback_script_path": "app.scripts.round183c_migration_rollback",
  "player_banner_enabled": true,
  "backup_path": "/app/memory/backups/round183c_prestart/",
  "enum_conflict_deferred_to": "R18.3b.1",
  "residual_check": {"priest": 0, "ranger": 0, "warlock": 0, "berserker": 0, "assassin": 0},
  "target_counts_post_apply": {"paladin": 356, "cacciatore_di_mostri": 175, "cacciatore_del_vuoto": 128, "warrior": 293, "rogue": 148},
  "feature_flag_R18_REWORK_ENABLED": "false"
}
```

Whitelist admin `AUDIT_EVENT_WHITELIST` esteso a includere:
- `R18_CLASS_ORPHAN_MIGRATION_APPLIED`
- `R18_CLASS_ORPHAN_MIGRATION_ROLLED_BACK`

---

## 6. Banner UI IT — endpoints + shape response

**Backend endpoints** in `/app/backend/app/guilds/routes.py`:

### GET `/api/guilds/me/migration-banner` (JWT-authenticated)

```json
{
  "show": true,
  "dismissed": false,
  "migrated_count": 2,
  "message_it": "Alcuni tuoi avventurieri sono stati riallineati alle classi canoniche di Orbus. Nessun livello, oggetto o progresso è stato perso.",
  "mappings": [
    {"from_it": "Ranger", "to_it": "Cacciatore di Mostri"},
    {"from_it": "Warlock", "to_it": "Cacciatore del Vuoto"}
  ]
}
```

**Zero leak metadata tecnici**: no `role`, `role_placeholder`, `role_pm_decision_pending`, `migration_target_only`, `is_playable`, `source_round`, `migration_round`, `previous_class_slug`, `career_history`, `migration_history`, `migration_timestamp`, `migration_reason` nella response (verificato via test 16 + curl scan).

### POST `/api/guilds/me/migration-banner/dismiss` (JWT-authenticated)

Setta `guilds.migration_banner_r18_3c_dismissed=true` (persistenza server-side, guild-level). Response:
```json
{"ok": true, "dismissed": true}
```

**Guild-scoped**: banner mostra `show=true` SOLO se `migrated_count > 0 AND !dismissed`. Se dismiss è persistente, refresh non lo ripropone. Se guild ha 0 adv migrati, `show=false` sempre.

**IT byte-exact preservato** (test 17):
> "Alcuni tuoi avventurieri sono stati riallineati alle classi canoniche di Orbus. Nessun livello, oggetto o progresso è stato perso."

### Frontend

- **Component**: `/app/frontend/src/components/MigrationBannerR183c.jsx` (100 righe)
- **Integrazione**: `/app/frontend/src/pages/Dashboard.jsx` line 199 (sopra `OnboardingChecklistV2`)
- **data-testid**: `migration-banner-r18-3c`, `migration-banner-message-it`, `migration-banner-toggle-details`, `migration-banner-mapping-list`, `migration-banner-mapping-<idx>`, `migration-banner-dismiss-btn`
- **UX**: Dismissible con X in alto a destra. "Dettagli" toggle mostra elenco mapping (Ranger → Cacciatore di Mostri, ecc.) filtrato per guild.

Log backend live conferma:
```
GET /api/guilds/me/migration-banner HTTP/1.1 200 OK
POST /api/guilds/me/migration-banner/dismiss HTTP/1.1 200 OK
```

---

## 7. Test suite (23/23 PASS + regression 94/94)

`/app/backend/tests/backend_round183c_migration_test.py`

| # | Test | Status |
|---|---|---|
| 01 | Backup manifest valid | ✅ |
| 02 | Migration count = 496 esatti | ✅ |
| 03 | Zero residual source slugs | ✅ |
| 04 | Target counts migrated correctly | ✅ |
| 05 | previous_class_slug preservato | ✅ |
| 06 | career_history embedded append-only | ✅ |
| 07 | Migration idempotent (re-run 0 modifiche) | ✅ |
| 08 | Audit event `R18_CLASS_ORPHAN_MIGRATION_APPLIED` emesso | ✅ |
| 09 | Audit whitelist admin extended | ✅ |
| 10 | Zero touch catalog `adventurer_classes` | ✅ |
| 11 | Guard R18.1.2 accetta 5 target slugs | ✅ |
| 12 | Item pool bridge preservato (31 + 18) | ✅ |
| 13 | Player API `/api/adventurers` zero leak | ✅ |
| 14 | class_name aggiornato ai display IT canonici | ✅ |
| 15 | Level/grade untouched + 5-stat intact | ✅ |
| 16 | Banner endpoint shape + zero leak | ✅ |
| 17 | Banner message IT byte-exact | ✅ |
| 18 | Banner shows only for guilds with migrated_count>0 | ✅ |
| 19 | Banner dismiss endpoint persistence | ✅ |
| 20 | Admin audit endpoint returns 200 for new event | ✅ |
| 21 | Regression prior rounds importable | ✅ |
| 22 | Rollback script eseguibile end-to-end su fixture | ✅ |
| 23 | Feature flag R18_REWORK_ENABLED off preservato | ✅ |

**Regression cross-round**:
```
R18.1     migration:      18/18 PASS
R18.2     talent pilot:   15/15 PASS
R18.1.2   guard whitelist: 12/12 PASS
R18.3a    class prereq:   16/16 PASS
R18.3a.1  hotfix:         10/10 PASS
R18.3c    migration apply: 23/23 PASS
──────────────────────────────────────
TOTAL:                    94/94 PASS in 2.81s
```

---

## 8. Rollback

**Script**: `/app/backend/app/scripts/round183c_migration_rollback.py`

**Uso**:
```bash
python -m app.scripts.round183c_migration_rollback --dry-run
python -m app.scripts.round183c_migration_rollback --apply
```

**Operazioni**:
1. Ripristina `class_slug = previous_class_slug` per ogni doc con `migration_round=R18.3c`
2. Ripristina `class_name` al display IT del source (best-effort da catalog)
3. `$unset` di `previous_class_slug`, `migration_round`, `migration_reason`, `migration_timestamp`
4. `$pull` dell'evento `career_history` con round=R18.3c
5. Emit audit event `R18_CLASS_ORPHAN_MIGRATION_ROLLED_BACK` con count

**Safety pre-rollback**: verifica adventurer non in expedition/raid attivi. Idempotent (secondo run 0 modifiche).

**Backup safety net**: se rollback script fallisce, `mongorestore` dal backup pre-apply è disponibile.

---

## 9. Vincoli rispettati

| Vincolo | Status |
|---|---|
| Zero schema migration (stat system resta 5-stat) | ✅ |
| Zero modifica role enum | ✅ |
| Zero modifica combat math | ✅ |
| Zero modifica catalog `adventurer_classes` | ✅ (test 10) |
| Zero nuovi item / talenti reali / Trait / Fatigue / Cucina | ✅ |
| Zero modifiche drop/reward/economia/PvP/premium | ✅ |
| Zero hard delete | ✅ |
| Feature flag `R18_REWORK_ENABLED=false` invariato | ✅ (test 23) |
| Backup + dry-run + apply + rollback safe | ✅ |
| Banner IT byte-exact | ✅ (test 17) |
| Zero player-facing leak metadata migration | ✅ (test 13, 16) |
| Idempotenza apply + audit | ✅ (test 7, 8) |
| Test coverage ≥ 20 | ✅ (23 tests) |
| Regression cross-round | ✅ (94/94) |

---

## 10. Sealing

**R18.3c CLOSED & SEALED ✅ (2026-07-04T20:47Z)**

496/496 apply completo. Regression 94/94 PASS. Zero touch catalog. Banner live. Rollback pronto. Audit event emesso. Feature flag OFF preservato.

**Next**: R18.3b.1 (Stat/Role Enum Reconciliation Matrix) OPEN PENDING — attendere brief PM esplicito per procedere con decisione enum.

*Firma: e1 main agent · 2026-07-04T20:47Z · R18.3c APPLY COMPLETE*
