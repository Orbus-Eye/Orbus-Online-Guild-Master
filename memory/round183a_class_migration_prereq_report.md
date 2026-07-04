# ROUND 18.3a — Class Migration Pre-Req Report — CLOSED & SEALED ✅ (2026-07-04T20:08Z)

**Round**: R18.3a · **Data**: 2026-07-04 · **Autore**: e1 main agent
**Status**: PRE-REQ COMPLETO — seed classi + bridge item + dry-run migration corretto. **APPLY reale in R18.3.**

---

## 1. Sommario esecutivo

Prepara il pool tecnico per la futura migration R18.3 (496 orphan adventurer) senza toccare gli adventurer reali. Sub-step completati:

1. ✅ Seed classi `cacciatore_di_mostri` + `cacciatore_del_vuoto` in `adventurer_classes` con `is_playable=false + migration_target_only=true + is_canonical=true + is_active=true + source_round="R18.3a"`.
2. ✅ Bridge item append-only: 31 ranger-tagged items ora accettano `cacciatore_di_mostri`; 18 warlock-tagged items ora accettano `cacciatore_del_vuoto` (49 append totali).
3. ✅ Slug corretti da PM Q6: `cacciatore_di_mostri` + `cacciatore_del_vuoto` (con preposizione articolata). Slug R18.2 (`cacciatore_mostri`, `cacciatore_vuoto`) mai seedati.
4. ✅ Dry-run migration script `round183a_orphan_migration_dry_run.py` generato con slug corretti + `slug_correction_note`. Report JSON in `/app/memory/round183a_orphan_migration_dry_run.json`, plan MD in `/app/memory/round183a_orphan_migration_plan.md`.
5. ✅ Audit event `R18_CLASS_MIGRATION_PREREQ_READY` emesso in `audit_log` con metadata completa (round, classes_seeded, item_bridge_counts, dry_run_only=true, ecc.). Idempotente.
6. ✅ Whitelist admin audit (`app/admin/audit_routes.py`) estesa a includere il nuovo event type.
7. ✅ 16 test in `backend_round183a_prereq_test.py` (target ≥ 13) tutti PASS. Regression totale 61/61 PASS.

---

## 2. Deliverable

| File | Descrizione |
|---|---|
| `/app/memory/round183a_class_migration_prereq_report.md` | questo report |
| `/app/memory/round183a_orphan_migration_plan.md` | plan migration IT-friendly |
| `/app/memory/round183a_orphan_migration_dry_run.json` | dry-run JSON con slug corretti |
| `/app/backend/app/scripts/round183a_class_migration_prereq_seed.py` | seed classi + bridge items + audit emit |
| `/app/backend/app/scripts/round183a_orphan_migration_dry_run.py` | dry-run migration analyzer (successor R18.2) |
| `/app/backend/tests/backend_round183a_prereq_test.py` | 16 test |
| `/app/backend/app/admin/audit_routes.py` (patch) | whitelist esteso |

---

## 3. Classi seedate — verifica live

Post-apply live DB (`orbus_r16`):

```json
[
  {
    "slug": "cacciatore_di_mostri",
    "name": "Cacciatore di Mostri",
    "display_name_it": "Cacciatore di Mostri",
    "is_playable": false,
    "migration_target_only": true,
    "is_canonical": true,
    "is_active": true,
    "source_round": "R18.3a",
    "source_slug_bridge": "ranger",
    "pm_decision": "Q2"
  },
  {
    "slug": "cacciatore_del_vuoto",
    "name": "Cacciatore del Vuoto",
    "display_name_it": "Cacciatore del Vuoto",
    "is_playable": false,
    "migration_target_only": true,
    "is_canonical": true,
    "is_active": true,
    "source_round": "R18.3a",
    "source_slug_bridge": "warlock",
    "pm_decision": "Q3"
  }
]
```

**Player-facing leak check** post-seed:
- `GET /api/adventurer-classes` non espone nessuna delle 2 classi (verificato via test 13).
- Recruitment/onboarding/generator: filtrano su `is_playable` (esistente in codice pre-R18.3a).
- Guard R18.1.2: accetta i 2 slug come dispatch-valid (verificato via test 08).

---

## 4. Bridge item counts

| Target class | Source class | Bridge count | Method |
|---|---|---|---|
| `cacciatore_di_mostri` | `ranger` | **31** | `$addToSet` append-only |
| `cacciatore_del_vuoto` | `warlock` | **18** | `$addToSet` append-only |
| **TOTAL** | | **49** | |

**Vincoli rispettati**:
- ✅ Zero override / delete di source slug (test 04 verifica presenza `$all: [source, target]`).
- ✅ Zero modifica a `stats`, `rarity`, `power_score`, `required_adventurer_level`, `required_level`, `drop_rate`, `is_tradeable`, `is_bound` (test 05).
- ✅ Zero item nuovo creato.
- ✅ Idempotenza: secondo run `--apply` risulta in `already=31 to_append=0` + `already=18 to_append=0`.

---

## 5. Audit event emesso

**Event type**: `R18_CLASS_MIGRATION_PREREQ_READY` · **Idempotent**: sì

Metadata inserita in `audit_log`:

```json
{
  "round": "R18.3a",
  "classes_seeded": ["cacciatore_di_mostri", "cacciatore_del_vuoto"],
  "is_playable": false,
  "migration_target_only": true,
  "item_bridge_strategy": "recommended_classes_append_only",
  "item_bridge_counts": {
    "cacciatore_di_mostri": 31,
    "cacciatore_del_vuoto": 18
  },
  "orphans_impacted_estimated": 303,
  "migration_apply": false,
  "dry_run_only": true,
  "slug_correction_from_R18_2": true,
  "corrected_slugs_from_R18_2": {
    "cacciatore_mostri": "cacciatore_di_mostri",
    "cacciatore_vuoto": "cacciatore_del_vuoto"
  },
  "feature_flag_R18_REWORK_ENABLED": "false",
  "feature_flag_R18_TALENT_ENGINE_ENABLED": "false",
  "seed_results": [...]
}
```

Whitelist admin extended: `R18_CLASS_MIGRATION_PREREQ_READY` + `R18_GUARD_WHITELIST_EXTENDED` (R18.1.2) accettati da `GET /api/admin/audit/events?event_type=...`.

---

## 6. Test suite (16/16 PASS)

`/app/backend/tests/backend_round183a_prereq_test.py`

| # | Test | Scope | Status |
|---|---|---|---|
| 01 | `target_classes_seeded` | Marker seed corretti su 2 slug | ✅ |
| 02 | `exact_slugs_no_short_form` | Slug R18.2 (short form) NON esistono | ✅ |
| 03 | `bridge_item_counts_min_10` | ≥ 10 items per ciascuna classe target | ✅ |
| 04 | `bridge_append_only_preserves_source` | Source slug preservato in every item | ✅ |
| 05 | `bridge_no_stat_modification` | rarity/power_score/level intatti | ✅ |
| 06 | `audit_event_emitted` | Event R18_CLASS_MIGRATION_PREREQ_READY | ✅ |
| 07 | `audit_event_idempotent` | Unico record (idempotenza) | ✅ |
| 08 | `guard_r18_1_2_accepts_target_slugs` | Query guard include target slugs | ✅ |
| 09 | `zero_adv_migrated_in_r18_3a` | 0 adventurer con class_slug target | ✅ |
| 10 | `feature_flags_off` | R18 flags OFF preservati | ✅ |
| 11 | `dry_run_json_valid` | JSON output + slug_correction_note | ✅ |
| 12 | `admin_audit_whitelist_extended` | 2 new event types in whitelist | ✅ |
| 13 | `no_player_facing_leak_target_classes` | is_playable=false enforced | ✅ |
| 14 | `plan_md_deliverable_exists` | Plan MD scritto + slug corretti | ✅ |
| 15 | `regression_prior_rounds_importable` | Moduli test R18.1/R18.2/R18.1.2 importabili | ✅ |
| 16 | `guilds_untouched` | 0 modifiche a guilds | ✅ |

**Regression cross-round**: 61/61 PASS (R18.1 18 + R18.2 15 + R18.1.2 12 + R18.3a 16).

---

## 7. Idempotenza (verificata live)

**Sub-step seed classi**:
- Primo `--apply`: `action=inserted` per entrambi gli slug.
- Secondo `--apply`: `action=skip-idempotent` per entrambi.

**Sub-step bridge items**:
- Primo `--apply`: `to_append=31 + 18 = 49`.
- Secondo `--apply`: `already=31 + 18 = 49`, `to_append=0`.

**Audit event**:
- Primo `--apply`: `inserted`.
- Secondo `--apply`: `skip-idempotent` (unique record in audit_log).

---

## 8. Vincoli rispettati

| Vincolo | Status |
|---|---|
| Zero hard delete (adventurer, classi, items) | ✅ |
| Zero migration reale su adventurer | ✅ |
| Zero modifica a stats/rarity/level/drop/power/reward | ✅ |
| Zero item nuovo | ✅ |
| Zero player-facing UI change | ✅ |
| Zero modifica economia/PvP/premium/combat math | ✅ |
| Feature flag `R18_REWORK_ENABLED=false` OFF preservato | ✅ |
| Feature flag `R18_TALENT_ENGINE_ENABLED=false` OFF preservato | ✅ |
| Append-only su `recommended_classes` (`$addToSet`) | ✅ |
| Idempotency script (2 run consecutivi) | ✅ |
| Audit event emit idempotente | ✅ |
| Whitelist admin audit estesa | ✅ |
| ≥ 13 test creati e PASS | ✅ (16 test) |
| Slug PM-sigillati con preposizione articolata | ✅ |
| Slug R18.2 (short form) NON usati | ✅ |
| Guard R18.1.2 accetta i 2 slug | ✅ |
| Zero adventurers migrati | ✅ |
| Zero modifica a guilds | ✅ |

---

## 9. Prossimo step: R18.3 (apply reale)

Con R18.3a completato, il pool tecnico è pronto per l'apply reale della migration 496 orphan → 5 target. Prerequisiti apply R18.3:

1. ✅ Seed classi target (R18.3a) — DONE
2. ✅ Bridge item pool (R18.3a) — DONE
3. ✅ Guard whitelist ext (R18.1.2) — DONE
4. ⏳ Career_history snapshot policy
5. ⏳ UI banner IT "La classe X è stata rinominata Y"
6. ⏳ Flip `is_playable=false → true` + `migration_target_only=true → false` post apply
7. ⏳ (Opzionale) Guild-level opt-in `r18_beta_opt_in=true`

---

## 10. Firma

**R18.3a CLOSED ✅ (2026-07-04T19:55Z)**

Test 16/16 PASS. Regression 61/61 PASS. Audit event emesso. Slug PM-sigillati corretti. Bridge item append-only. Zero write reali su adventurers. Feature flag OFF preservati.

*Firma: e1 main agent · 2026-07-04T19:55Z*
