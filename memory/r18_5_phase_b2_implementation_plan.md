# R18.5 Phase B.2 — Implementation Plan (DOCUMENTAL ONLY)

- **Round**: `R18.5`
- **Fase**: B.2 — Implementation Plan (documentale, dopo B.1 Design Lock)
- **Locked at UTC**: `2026-07-06T17:20:00Z`
- **Governance**: **DOCUMENTAL ONLY** — 36 sigilli byte-identical, zero DB writes, zero code changes.
- **Predecessore**: `r18_5_phase_b1_design_lock.md/.json`

## 1. Migration / dry-run plan

Ogni nuovo campo DB seguirà il **pattern R18.4 B3** (dry-run report → PM GO → apply → post-apply report).

### 1.1 Nuovo campo `items.tier` (int 1..5)
- **Dry-run script**: `app/scripts/round18_5_backfill_tier_dryrun.py` — mappa `rarity → tier` per 173 items attivi + eventuali stale, produce `r18_5_backfill_tier_dryrun_report.md/.json` con conteggi (T1..T5) + drift detection.
- **Apply**: `app/scripts/round18_5_backfill_tier_apply.py` — solo dopo GO PM. Idempotency: `no_change_skip` counter esplicito.
- **Rollback**: `unset $items.tier` script se necessario.

### 1.2 Nuovo constant `MAX_VISIBLE_LEVEL=60`
- **File**: `app/shared/constants.py` (non-sealed) → aggiunta constant.
- **Serializer patch**: `adventurer_public()` clampa `level = min(level, MAX_VISIBLE_LEVEL)`.
- **NO migration DB** (nessun campo nuovo, solo constant + serializer).

### 1.3 Nuovi campi `adventurers.equipment_pwr` + `gear_pwr` (computed, non stored)
- **Non stored**: calcolati on-the-fly nel serializer.
- **NO migration**.

### 1.4 Nuovo campo `items.is_signature` (bool, default false)
- **Dry-run**: identifica gli attuali signature items (drake_slayer_* set) → propone `is_signature=true` per ~14 items.
- **Apply**: script backfill idempotente. Restanti items → `is_signature=false`.

### 1.5 Nuovi slot endgame (`helm`/`chest`/`legs`)
- **NO migration items esistenti** (retro-compat: items `slot_type=armor` restano equipabili come armor generico).
- **Nuovi items batch** (Phase C) useranno slot_type granulare direttamente.
- **Frontend**: `inventoryBySlot` map estesa per gestire i nuovi slot.

### 1.6 min_level cross-check dry-run
- **Script**: `app/scripts/round18_5_min_level_cross_check_dryrun.py` — identifica items con divergenza `min_level != required_adventurer_level`, produce report.
- **NO auto-fix**: manuale item-by-item se <5% divergenza, migration se >5%.

## 2. Registry plan

Nuove registry documentali (in `/app/memory/`):

1. `r18_5_item_family_registry.md/.json` — mapping famiglia → primary/secondary stat, class compatibility, item_type/slot_type.
2. `r18_5_signature_registry.md/.json` — list signature items post-migration (~14 esistenti + eventuali nuovi) con effetti/lore.
3. `r18_5_drop_matrix_registry.md/.json` — drop table per dungeon (24 esistenti + 1 endgame nuovo).
4. `r18_5_naming_registry.md/.json` — elenco prefix/suffix approvati PM + naming batch item.

## 3. Test plan

### 3.1 Unit test (min 12)
- Tier backfill mapping (Common→T1, ...) → 5 test.
- `equipment_pwr` formula (esempi Lv50 endgame, Lv10 starter) → 3 test.
- `MAX_VISIBLE_LEVEL` clamp serializer → 2 test.
- Signature `is_signature=true` uniqueness constraint (equip refuse se già 1 signature) → 2 test.

### 3.2 Integration test (min 8)
- `GET /api/items` espone `tier`+`tier_label` → 2 test.
- `GET /api/adventurers` espone `equipment_pwr`+`gear_pwr` → 2 test.
- `GET /api/dungeons/{slug}` mostra endgame nuovo dungeon → 1 test.
- Endpoint `/api/adventurers/{id}/eligible-items` continua a rispondere byte-identical (R18.4 seal preserve) → 1 test.
- Equipment flow con nuovi slot endgame per Adv Lv>=30 → 2 test.

### 3.3 Regression test (min 6)
- R18.4.followup UI 4-state suite: 13/13 PASS invariato.
- R18.4 class_bound: 16/16 PASS invariato.
- Sealed integrity: **36/36 byte-identical**.
- phase19_2_rename: 6/1 skipped invariato.
- Auto-equip fitness: nuove famiglie non degradano fitness ranking esistente.
- Adventurer_base_power backward compat: `total_power = base + equipment_power` invariato.

### 3.4 Deterministic 4-state coverage (post R18.4.followup)
Rerun t01-t13 test suite `backend_r18_4_followup_ui_4state_test.py` invariato.

## 4. Rollback plan

Per ogni migration:
- **Snapshot pre-apply**: `mongodump --db=orbus_r16 --collection=items --out=/tmp/backup_pre_r18_5_<step>_<utc>.bson`.
- **Rollback script**: dedicated `round18_5_rollback_<step>.py` per unset del campo.
- **Verification**: post-rollback SHA256 fields target = pre-migration snapshot.
- **Rollback per constant `MAX_VISIBLE_LEVEL`**: rimozione line dal constants.py + revert serializer patch.

## 5. DB impact estimate

| Collection | Count est. | Impact |
|---|---|---|
| `items` | 173 active + 80-120 new = 253-293 | tier backfill + is_signature backfill + eventuali slot_type update per new batch |
| `adventurers` | 5 live + fresh users starter | zero write (equipment_pwr computed non stored) |
| `dungeons` | 24 + 1 new endgame | additive: 1 new doc `endgame-void-crucible` |
| `recipes` | 6 legendary + 10 arfus + T3/T4 workshop recipes futuri | additive per Phase C |
| `materials` | esistenti + T3-T5 nuovi | additive per Phase C |
| **Total records touched** | ~200 update + ~100 insert | Idempotency mandatory su tutti apply |

## 6. Frontend impact estimate

| Component / Page | Change | Estimated lines |
|---|---|---|
| `pages/Inventory.jsx` | display tier + dual-label + nuovi slot | ~15 lines |
| `pages/AdventurerEquipment.jsx` | slot endgame dinamici (Lv>=30) + equipment_pwr display | ~25 lines |
| `components/InventoryEquipModal.jsx` | slot filter esteso a helm/chest/legs | ~10 lines |
| `components/TierBadge.jsx` (NEW) | badge tier secondario | ~50 lines |
| `utils/displayLabels.js` | tierLabel helper IT | ~10 lines |
| `components/ItemCompatibilityBadge.jsx` | **NO CHANGE** (SEALED R18.4.followup) | 0 |
| `utils/compatibilityLabels.js` | **NO CHANGE** (SEALED R18.4.followup) | 0 |
| Componenti inline RarityBadge | audit + eventuale patch dual-label | ~20 lines |

## 7. Backend/API impact estimate

| Endpoint | Serializer | Change |
|---|---|---|
| `GET /api/items` | `item_public()` | expose `tier`+`tier_label` |
| `GET /api/items/{slug}` | idem | idem |
| `GET /api/inventory` | idem | idem |
| `GET /api/adventurers` | `adventurer_public()` | expose `equipment_pwr`+`gear_pwr`, clamp `level=min(level,60)` |
| `GET /api/adventurers/{id}/equipment` | `equipment_public()` | idem PWR |
| `GET /api/adventurers/{id}/eligible-items` | `derive_ui_4state (SEALED)` | **NO CHANGE** |
| `GET /api/dungeons` | dungeon_public | expose endgame nuovo dungeon |
| `POST /api/expeditions/complete` | loot + xp | soft cap Lv60 clamp UI only |
| `GET /api/gear-ranking` (NEW opzionale) | new endpoint | leaderboard equipment_pwr top 10 |

## 8. Auto-equip impact estimate

- **`app/equipment/auto_equip.py`** (non-sealed): fitness formula estesa per considerare `tier_bonus` come tie-break secondario. Backward-compat totale.
- **`app/equipment/compatibility.py`** (SEALED R18.3e): **NO CHANGE**. R18.5 non modifica policy hard/soft/universal.
- **`app/equipment/bindings.py`** (SEALED R18.4 B4): **NO CHANGE**.
- **`app/equipment/level_gate.py`** (non-sealed): estende validation per rispettare policy precedenza `required_adventurer_level` (SQ6 lock).
- **`app/equipment/ui_4state.py`** (SEALED R18.4.followup C): **NO CHANGE**.

Signature uniqueness constraint (max 1 signature equipped): nuovo check runtime in `equipment/services.py::equip_item` (non-sealed). Return 400 IT se violation.

## 9. Phase C/D/E proposal (breakdown implementativo)

### Phase C — Migration dry-run (documentale + script)
- Script dry-run per tutti i backfill (tier, is_signature, min_level cross-check).
- Deliverable: `r18_5_phase_c_migration_dry_run_report.md/.json`.
- **GO PM required** prima di Phase D.

### Phase D — Code changes + apply
- **D.1**: constant + serializer patch (`MAX_VISIBLE_LEVEL`, `equipment_pwr`, `tier` exposure).
- **D.2**: apply script backfill (post-GO PM dry-run report).
- **D.3**: nuovi 80-120 items seed (post-GO PM naming registry).
- **D.4**: endgame dungeon `endgame-void-crucible` seed.
- **D.5**: Frontend: `TierBadge`, dual-label, slot endgame Lv30+.
- **D.6**: Test suite: 26+ nuovi test.

### Phase E — SEAL
- Selezione file nuovi da sigillare (target: PM decision perimetro).
- Banner apposition + SHA256 registry.
- Update `backend_r18_4_sealed_integrity_test.py` → aggregate 36 + N.
- Deliverable: `r18_5_phase_e_seal_report.md/.json`.

## 10. Exact PM gates required

Lista gate obbligatori (in ordine sequenziale):

1. **Gate 1**: PM review Phase B.1 + risposta a 8 new sub-questions (R18.5.SQ11..SQ18) → GO Phase C.
2. **Gate 2**: PM review dry-run report Phase C → GO backfill apply Phase D.2.
3. **Gate 3**: PM approval naming registry (batch 80-120 items) → GO seed Phase D.3.
4. **Gate 4**: PM approval endgame dungeon naming + drop rate → GO seed Phase D.4.
5. **Gate 5**: PM review Phase D end-to-end (test PASS + sealed 36/36 invariato + integration smoke) → GO Phase E.
6. **Gate 6**: PM approval SEAL perimeter (N file per Phase E) → GO SEAL apposition.
7. **Gate 7**: PM approval post-SEAL report → CLOSED R18.5.

**Stop conditions preserved**:
- Sealed drift → STOP critical
- DB write senza GO → STOP critical
- Batch > 120 items → STOP + report al PM
- Auto-decision su bilanciamento/naming/class identity/stat priority → STOP + segnala

## Self-check Phase B.2 10/10
1. ✅ Migration/dry-run plan (6 sub-plan)
2. ✅ Registry plan (4 registry doc)
3. ✅ Test plan (12 unit + 8 integration + 6 regression + 4-state)
4. ✅ Rollback plan (snapshot + script + verification)
5. ✅ DB impact (5 collezioni + count est.)
6. ✅ Frontend impact (7 componenti)
7. ✅ Backend/API impact (9 endpoint)
8. ✅ Auto-equip impact (compatibility SEALED preserved)
9. ✅ Phase C/D/E proposal (breakdown 12 sub-step)
10. ✅ PM gates (7 gate ordinati)

**Ready for PM review** → Phase B.2 CLOSED, attesa PM Gate 1 (risposta 8 SQ + GO Phase C).
