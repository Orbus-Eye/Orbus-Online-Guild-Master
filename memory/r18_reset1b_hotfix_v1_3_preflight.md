# R18.Reset.1b.hotfix.v1_3 — Preflight (Schema Compatibility Fix)

**Generated at**: 2026-07-05T14:40:15Z UTC
**Purpose**: Preflight read-only PRE-DRY_RUN dell'hotfix v1.3.
**Freeze status**: `orbus_maintenance.flag` ACTIVE · `orbus_internal_job_freeze.flag` ACTIVE

---

## 1. Target Set

- Marker: `r18_reset1b_hotfix_v1_2 = true`
- Target count: **3360 / 3360** ✅ (expected: 3360)
- Slug conformance: **3360 / 3360** in whitelist safe (nessun non-conformant)

Distribuzione per class_slug:

| slug | count |
|:---|---:|
| alchemist | 299 |
| bard | 324 |
| druid | 311 |
| mage | 281 |
| monk | 327 |
| paladin | 303 |
| priest | 278 |
| ranger | 299 |
| rogue | 302 |
| warlock | 305 |
| warrior | 331 |
| **totale** | **3360** |

## 2. Catalog Mapping (11/11)

Vedi tabella in §6 del report post-apply schema audit.

## 3. Fields To Patch

### Hard-critical (obbligatori)
- `adventurer_class_id` ← catalog `id` via `class_slug`
- `experience` = 0
- `is_available` = true

### Semantic parity (evitano None/valori non canonici)
- `class_name` ← catalog `name` (es. "Rogue", "Warrior")
- `class_role` ← catalog `role` (∈ {DPS, Tank, Healer, Support})
- `rarity` = "Common"
- `stamina` = 100
- `morale` = 100
- `status` = "idle"
- `is_starter` = true
- `traits` = []
- `rename_count` = 0
- `is_retired` = false
- `grade` = "common" (sostituisce "F" v1.2 con valore canonico live)

### Tracking marker
- `r18_reset1b_hotfix_v1_3` = true
- `r18_reset1b_hotfix_v1_3_at` = ISO UTC di apply
- `r18_reset1b_hotfix_v1_3_apply_id` = UUID4

### NON toccati (preservati)
`id`, `guild_id`, `name`, `class_slug`, `strength/agility/intellect/endurance/faith`,
`level`, `xp` (legacy v1.2), `hp_current`, `hp_max`, `created_at`,
`r18_reset1b_starter`, `r18_reset1b_hotfix_v1_2`,
`r18_reset1b_seed_source`, `r18_reset1b_stat_source`, `phase13_unbaked`.

## 4. Static Analysis Referenza

Fonti live per determinare enum canonici:

| Enum | Value | Fonte |
|:---|:---|:---|
| `rarity` | `Common` | `onboarding/services.py:49` — starter default |
| `grade` | `common` | `round181_schema_foundation.py:14/180` — backfill default |
| `status` | `idle` | `adventurers/services.py:223` — default se is_available=True |
| `is_available` | `true` | `adventurers/services.py:217,223` — default runtime |
| `class_role` ∈ | `DPS/Tank/Healer/Support` | `adventurer_classes` catalog (11/11) |

## 5. xp vs experience — Decisione

**Decisione**: `xp` v1.2 (valore `0` per starter) resta invariato come
metadata legacy documentato. `experience` viene creato ex-novo con
valore `0` (canonico). Motivazione:
- Il runtime (`adventurer_public`, `_resolve_expedition_member`) usa
  `experience` come chiave hard/soft. `xp` non è mai referenziato
  dai serializer / resolver core.
- Rimuovere `xp` implicherebbe un `$unset` extra su 3360 doc, non
  necessario. Mantenerlo è idempotency-safe (nessun consumer lo legge).
- Documentato nel report per tracciabilità (§5 di
  `r18_reset1b_v1_2_post_apply_schema_audit.md`).

## 6. Guards (hard stop conditions)

Lo script v1.3 si rifiuta di scrivere se:
1. `target count != 3360`
2. `class mapping < 11/11`
3. freeze non attivo in `--apply`
4. audit `APPLIED_V1_3` già presente e non rollbackato
5. trova `class_slug` non-safe nel target
6. mapping non deterministico

## 7. Backup Reference

Backup fresh v1.2 (fonte rollback in caso di fail v1.3):
- Path: `/app/backend/backups/r18_reset1b_v1_2_20260705T134230Z/`
- Manifest sha256: **PASS 33/33** file (verificato nell'audit precedente)

## 8. Audit Events da emettere (solo dopo APPLY riuscito)

- `R18_STARTER_ROSTER_HOTFIX_APPLIED`
- `R18_STARTER_ROSTER_HOTFIX_APPLIED_V1_3`

Con metadata condiviso:
```
round=R18.Reset.1b.hotfix.v1_3
apply_script=round18_reset1b_apply_v1_3.py
apply_version=v1.3
target_count=3360
fields_patched=[14 fields]
class_mapping_count=11
schema_compatibility_fix=true
http_maintenance_required=true
internal_job_freeze_required=true
apply_id=<uuid>
completed_at=<iso>
backup_reference=/app/backend/backups/r18_reset1b_v1_2_20260705T134230Z
supersedes_versions=[v1.2]
patch_stats={…}
```

## 9. Verdetto preflight: **PROCEED**

Nessun blocker. DRY_RUN eseguito con esito exit=0.
Test suite dedicata da eseguire prima del gate PM per Fase B.
