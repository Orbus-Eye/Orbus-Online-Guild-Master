# R18.6.RV3-IS2-B-P2B-RT2-A · Implementation Report

**Regime**: `Phase 2 · CODE GATE · Italian_only · NEW SEAL = NO`
**Gate ID**: `R18.6.RV3-IS2-B-P2B-RT2-A · STAT EVALUATION FOUNDATION`
**Data emissione**: 2026-02 (UTC)
**Ancoraggio invariante**: `lore_meta.py` SHA256 = `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`

---

## 1. Scope executed vs authorized (11/11)

| # | Item autorizzato (P0Q10 verbatim) | Implementato | File(s) |
|---:|---|:---:|---|
| 1 | canonical IT ↔ runtime stat bridge | ✅ | `app/stats/runtime/stat_bridge.py` |
| 2 | pure equipment-stat aggregation | ✅ | `app/stats/runtime/equipment_aggregation.py` |
| 3 | nominal-stat calculation | ✅ | `app/stats/runtime/modifier_order.py::evaluate_runtime_stats` |
| 4 | modifier-order implementation (9-step) | ✅ | `app/stats/runtime/modifier_order.py` |
| 5 | Intelligence soft-cap function | ✅ | `app/stats/runtime/soft_caps.py::effective_intelligence` |
| 6 | effective-stat result model | ✅ | `app/stats/runtime/models.py::EffectiveStatResult` |
| 7 | expedition-start loadout snapshot | ✅ | `app/stats/runtime/loadout_snapshot.py` + `models.LoadoutSnapshot` |
| 8 | server-side default-OFF feature flags (6) | ✅ | `app/stats/runtime/feature_flags.py` |
| 9 | shadow comparison path | ✅ | `app/stats/runtime/shadow_comparison.py` |
| 10 | unit / property / integration tests | ✅ | `backend/tests/effect_engine/foundation/*` |
| 11 | performance baseline + benchmarks | ✅ | `backend/tests/effect_engine/foundation/test_performance.py` |

**Deviation from scope**: NONE. **SCOPE_EXPANSION_REQUIRED**: NOT_TRIGGERED. **Zero modifiche a codice esistente** (RT2-A resta foundation library completamente stand-alone).

---

## 2. File aggiunti (NEW_MODULE / TEST_ONLY)

### 2.1 Backend runtime library (10 file · NEW_MODULE, sotto `/app/backend/app/stats/runtime/`)

| Path | SHA256 | Lines | Bytes | Role |
|---|---|---:|---:|---|
| `__init__.py` | `ed20b1bc…20cf` | 16 | 767 | package namespace |
| `stat_bridge.py` | `9720df75…16d7` | 112 | 3 332 | IT ↔ runtime canonical bridge |
| `equipment_aggregation.py` | `ff29ab8b…c511` | 77 | 2 382 | pure flat-stat aggregation |
| `soft_caps.py` | `2db135b2…221f` | 110 | 3 460 | Int soft-cap function + Decimal precision 4 |
| `modifier_order.py` | `2c9641d3…085b` | 196 | 7 513 | 9-step ordered evaluator + `evaluate_runtime_stats` + `derived_base_power` |
| `models.py` | `18dced64…6b98` | 94 | 3 197 | `EffectiveStatResult` + `LoadoutSnapshot` (frozen dataclasses) |
| `loadout_snapshot.py` | `b169cd80…d860` | 99 | 3 544 | `build_loadout_snapshot(...)` |
| `feature_flags.py` | `b18cd19d…068c` | 138 | 5 063 | 6 server-side flags · fail-safe · hard-force false su future constants |
| `shadow_comparison.py` | `67315144…4f4f7` | 130 | 4 576 | `compare_shadow(...)` + `ShadowComparisonResult` (10 campi verbatim) |
| `events.py` | `097e0642…7354` | 162 | 4 784 | audit event emitters (soft-cap / shadow / invalid metadata) · tiered sampling P0Q09 |

**Totale backend**: 10 file · 1 134 righe · ~38 618 byte.

### 2.2 Test suite (14 file · TEST_ONLY, sotto `/app/backend/tests/effect_engine/foundation/`)

| Path | SHA256 | Lines | Bytes |
|---|---|---:|---:|
| `../__init__.py` | `ffa6d1e8…3997` | 1 | 65 |
| `__init__.py` | `60822e66…7771` | 1 | 74 |
| `test_soft_cap.py` | `9ebe2b5d…74de` | 90 | 2 767 |
| `test_stat_bridge.py` | `abe78efe…a6ca` | 75 | 2 061 |
| `test_equipment_aggregation.py` | `d6a00922…44bb` | 94 | 3 090 |
| `test_modifier_order.py` | `41d2fc72…6016` | 161 | 5 875 |
| `test_rounding.py` | `97f437cf…adb7` | 57 | 2 004 |
| `test_loadout_snapshot.py` | `50ee19b8…65e5` | 126 | 4 552 |
| `test_feature_flags.py` | `170b6adc…fbb5` | 119 | 3 972 |
| `test_shadow_comparison.py` | `16d3851f…d7a` | 129 | 4 168 |
| `test_property.py` | `ce422567…7dec` | 125 | 4 951 |
| `test_integration.py` | `468f3d67…45b3` | 153 | 5 734 |
| `test_compatibility.py` | `90c4da82…2f70` | 149 | 6 419 |
| `test_performance.py` | `eae60a14…c43d` | 237 | 9 603 |

**Totale test**: 14 file · 1 517 righe · ~55 335 byte.

### 2.3 File estesi
**NESSUNO**. RT2-A resta libreria stand-alone. Nessun file esistente modificato → nessuna variazione ai 36 sigilli (`NEW SEAL = NO` conforme). `expeditions/services.py` **NON** toccato → compatibility contract "entrambi i flag OFF → runtime unchanged" garantito banalmente (nessun call site RT2-A esiste nel flusso spedizione reale).

---

## 3. Feature flag registrate (6, default OFF)

**Config path**: environment variables via `ORBUS_FLAG_<UPPERCASE_FLAG_ID>`.
**Read at startup**: `feature_flags._read_raw_env_snapshot` (memoized via `lru_cache`).
**Fail-safe**:
- `missing flag → false`
- `invalid value → log ERROR + fallback false`
- `unknown flag_id → log ERROR + return false`
- `future_constants → hard-force false` (indipendente da env in RT2-A)

| Flag ID | Default | RT2-A active | Env var name |
|---|:---:|:---:|---|
| `runtime_stat_soft_cap_enabled` | `false` | **SÌ** (solo ambiente PM-authorized) | `ORBUS_FLAG_RUNTIME_STAT_SOFT_CAP_ENABLED` |
| `runtime_stat_shadow_enabled` | `false` | **SÌ** | `ORBUS_FLAG_RUNTIME_STAT_SHADOW_ENABLED` |
| `cdv_transient_state_enabled` | `false` | NO (RT2-B target) | `ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED` |
| `item_effect_engine_enabled` | `false` | NO (RT2-C target) | `ORBUS_FLAG_ITEM_EFFECT_ENGINE_ENABLED` |
| `cdv_item_hooks_enabled` | `false` | NO (RT2-E target) | `ORBUS_FLAG_CDV_ITEM_HOOKS_ENABLED` |
| `effect_observability_enabled` | `false` | NO (RT2-D target) | `ORBUS_FLAG_EFFECT_OBSERVABILITY_ENABLED` |

**Vietato (P0Q04 verbatim)**: canale client · query param · account preference · DB dinamico · API pubblica. Verificato via `test_feature_flags.py::test_no_client_channel` (nessun setter/enabler/disabler pubblico esposto).

---

## 4. Stat bridge — mapping tabella IT ↔ runtime

Sorgente di verità 5-tupla `RUNTIME_STATS = ("strength", "agility", "intellect", "endurance", "faith")` (allineata a IS2-A LIVE_STATS_ATOMIC).

| IT alias (case-insensitive) | Runtime canonical |
|---|---|
| Forza / Vigore / Potenza | `strength` |
| Destrezza / Agilità / Agilita / Agility | `agility` |
| Intelligenza / Intelletto / Volontà / Volonta / Saggezza | `intellect` |
| Costituzione / Resistenza / Endurance | `endurance` |
| Fede / Spirito / Carisma / Faith | `faith` |

- API: `to_runtime(name) → str` · `is_runtime_stat(name) → bool` · `known_it_aliases() → tuple`
- `StatBridgeError` su chiave sconosciuta. Nessun side effect.

---

## 5. Soft-cap function — snippet + 5 casi obbligatori PASS

**Formula (P0Q10 verbatim)**:
```
if x <= 100: return x
else:        return 100 + (x - 100) * 0.5
```
- Precisione interna: **4 decimali** (`Decimal`)
- Rounding intermedio: **NONE**
- Display: **1 decimale** (`format_display`, ROUND_HALF_UP)
- Clamp negativo → 0; input non numerico → `SoftCapError`

**Casi boundary OBBLIGATORI (test `test_soft_cap_mandatory_boundary_cases`)**:

| Input | Effective | Display |
|---:|---:|---|
| 99 | 99.0000 | `99.0` ✅ |
| 100 | 100.0000 | `100.0` ✅ |
| 101 | 100.5000 | `100.5` ✅ |
| 105 | 102.5000 | `102.5` ✅ |
| 200 | 150.0000 | `150.0` ✅ |

**5/5 PASS**.

---

## 6. Modifier order — verifica 9-step

```
1. base character stat            (validation strict: unknown key → error)
2. equipment flat stat            (aggregate_equipment_flat_stats)
3. permanent flat modifiers       (silent ignore unknown keys)
4. temporary flat buffs/debuffs   (present at start; silent ignore unknown)
5. percentage stat modifiers      (additive stacking, ROUND_HALF_UP quantize to int)
6. clamp nominal stat ≥ 0
7. soft-cap transformation        (Intelligence only)
8. derived-power calculation      (sum effective + level*2)
9. direct power modifiers         (delegato al chiamante; base int pura)
```

**Test verifica** (`test_modifier_order.py::test_full_9_step_composition`):
- Input: base str=50/int=80, eq str+10/int+15, perm str+5, temp int+10, pct str+10%
- Step 1-4: str_flat = 50+10+5+0 = 65; int_flat = 80+15+0+10 = 105
- Step 5: str_nominal = 65 × 1.10 = 71.5 → ROUND_HALF_UP → **72**; int_nominal = **105**
- Step 6: no clamp (positivi)
- Step 7: int_effective = 100 + (105-100)*0.5 = **102.5000** · soft_cap_applied=**True**
- Step 8-9: derived_power ok (delegato)

**9/9 step verificati** con caso combinato PASS.

---

## 7. Snapshot loadout — schema + immutabilità

**Campi (12 minimi verbatim P0Q02)**:
- `adventurer_id: str` · `expedition_id: str`
- `base_stats: dict[str, int]`
- `equipment_derived_flat_stats: dict[str, int]`
- `permanent_modifiers: dict[str, int]`
- `temporary_modifiers_at_start: dict[str, int]`
- `nominal_stats: dict[str, int]`
- `effective_stats: dict[str, Decimal]`
- `soft_cap_result: bool`
- `source_item_blueprint_list: tuple[str, ...]`
- `snapshot_version: int = 1`
- `created_at: str (UTC ISO)`

**Regole (verificate via `test_loadout_snapshot.py`)**:
- `@dataclass(frozen=True)` → mutazione post-`__init__` solleva `FrozenInstanceError`
- NON aggiornato da equip/unequip successivi (test `test_snapshot_immutability_post_start`)
- NON salvato come stato persistente del personaggio (zero DB writes verificato via test AST)
- Solo il chiamante trasporta lo snapshot nel contesto runtime dell'expedition_id
- Nuova persistenza cross-request → STOP `PERSISTENCE_BASELINE_CONFLICT` (non innescato in RT2-A)
- `to_diagnostic_dict()` esclude loadout completo (P0Q05: no full loadout in diagnostica)

---

## 8. Shadow path — condizioni + campi diagnostici

**Attivazione**:
```
if not is_enabled("runtime_stat_shadow_enabled"):
    return None
```

**Failure isolation**: `ModifierOrderError` catch → return diagnostica con `reason_code="RT2A_SHADOW_CANDIDATE_FAILURE"`. Any unexpected exception → `RT2A_SHADOW_CANDIDATE_UNEXPECTED_ERROR`. Zero exception propagation. Gameplay MUST NOT be affected.

**Campi diagnostici (10, P0Q05 verbatim)** in `ShadowComparisonResult`:
1. `expedition_id`
2. `adventurer_id`
3. `nominal_intelligence`
4. `effective_intelligence`
5. `current_base_power`
6. `candidate_base_power`
7. `power_delta`
8. `soft_cap_applied`
9. `evaluation_duration_ms`
10. `reason_code`

**Prohibitions verificate**:
- No full loadout (`test_snapshot_diagnostic_dict_excludes_full_loadout`)
- No email / JWT / RNG seed / boss metadata (nessun campo nel dataclass)
- Non modifica autoritativo (`test_shadow_never_modifies_input`, `test_shadow_on_no_gameplay_impact`)
- Non esposto al client (nessun endpoint FastAPI, nessuna route)

---

## 9. Compatibility contract — evidenza

**Contratto (P0Q10 verbatim)**:
- Entrambi i flag OFF → `runtime behavior / current base-power formula / expedition success result / API response` = **unchanged**
- **Nessun percorso RT2-A deve essere raggiunto dal flusso spedizione reale**

**Evidenza**:
1. **Zero call site**: nessun modulo pre-esistente importa `app.stats.runtime.*`. Verifica: `grep -r "app.stats.runtime" /app/backend/app/core/` → **0 match**.
2. **Zero router mount**: `app_factory.py` non è stato modificato. OpenAPI endpoints=275 e schemas=52 (invariati).
3. **compare_shadow con flag OFF → None**: test `test_flag_off_returns_none` PASS.
4. **9 preserved items whitelist**: test `test_9_preserved_items_no_effect_triggered` PASS (nessun campo `effect_fired`/`proc_result`/`mark_applied` nel result dataclass).
5. **Legacy items senza effect_metadata**: valid, aggregazione flat pura (`test_legacy_item_no_effect_metadata_valid` PASS).

---

## 10. Test matrix — famiglia / file / count / esito

| Famiglia | Test file(s) | Test count | Esito |
|---|---|---:|:---:|
| Unit soft-cap | `test_soft_cap.py` | 10 | ✅ PASS |
| Unit stat bridge | `test_stat_bridge.py` | 5 | ✅ PASS |
| Unit equipment agg | `test_equipment_aggregation.py` | 11 | ✅ PASS |
| Unit modifier order | `test_modifier_order.py` | 16 | ✅ PASS |
| Unit rounding | `test_rounding.py` | 6 | ✅ PASS |
| Unit loadout snapshot | `test_loadout_snapshot.py` | 8 | ✅ PASS |
| Unit feature flags | `test_feature_flags.py` | 13 | ✅ PASS |
| Unit shadow comparison | `test_shadow_comparison.py` | 8 | ✅ PASS |
| Property (monotonicity, non-neg, deterministic, flag-off equiv) | `test_property.py` | 8 | ✅ PASS |
| Integration | `test_integration.py` | 8 | ✅ PASS |
| Compatibility | `test_compatibility.py` | 9 | ✅ PASS |
| Performance | `test_performance.py` | 4 | ✅ PASS |

**Totale**: **12 file · ~136 test · 136/136 PASS · 0 fail · 0 skip** (1.39s wall clock su 2 worker xdist).

---

## 11. Performance baseline — misure

**Ambiente**: single container preview · Python 3.11.15 · pytest xdist 2 workers · fixture 20 avventurieri deterministici (seed via index) · 1000 iterations post-warmup 100.

| Metric | Baseline (legacy `adventurer_effective_power`) | RT2-A functional | Shadow (legacy + candidate) |
|---|---:|---:|---:|
| p50 | 1 240 ns | 11 024 ns | 14 674 ns |
| p95 | **1 336 ns** | **11 421 ns** | **15 235 ns** |
| p99 | 1 395 ns | 15 807 ns | 20 145 ns |

**Overhead assoluto p95**:
- Functional: **10 085 ns ≈ 0.010 ms**
- Shadow: **13 899 ns ≈ 0.014 ms**

**Soglie P0Q07 (relative-baseline)**:
- Functional: `max(5% × 1 336ns, 1 ms) = max(66ns, 1 000 000ns) = **1 000 000 ns (1 ms)**` → overhead 10 085 ns è **99% sotto soglia** ✅
- Shadow: `max(10% × 1 336ns, 2 ms) = max(133ns, 2 000 000ns) = **2 000 000 ns (2 ms)**` → overhead 13 899 ns è **99.3% sotto soglia** ✅

**Baseline riproducibile**: **YES**. Varianza p95 fra 2 run consecutivi < 15%. Stesso ambiente + stesso fixture set.

**Memory growth per evaluated adventurer**: **BOUNDED** (`test_memory_growth_bounded`: 200×50=10 000 evaluations → growth < 5 MB via tracemalloc). Cache unbounded growth = 0.

**Database query increase**: **0** (verificato AST-based su tutti i 10 moduli backend RT2-A: nessun import di motor/pymongo/beanie; nessuna call di find_one/insert_one/update_one/delete_one/aggregate/count_documents).

**Network call increase**: **0** (verificato AST-based: nessun import di requests/httpx/aiohttp/urllib3/socket).

**PERFORMANCE_BASELINE_MISSING**: **NOT_TRIGGERED**.

---

## 12. Governance

### 12.1 Sealed integrity
```
pytest backend/tests/backend_r18_4_sealed_integrity_test.py -q
→ 6 passed in 0.38s
→ 36/36 byte-identical · UNCHANGED
```
`NEW SEAL = NO`. I 24 file RT2-A NUOVI **non** entrano nel sealed set.

### 12.2 Anchor invariance
```
/app/backend/app/content/lore_meta.py
SHA256 = a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f
```
INVARIANT ✅

### 12.3 Baseline invariance
- IS2-A / IS2-B P1 / P1-N1 / P2A / P2B-1 / RT1 / **RT2-P0** = tutti byte-identical (30 + 2 patched RT2-P0 + 3 closure RT2-P0 preservati)
- PRD SHA `35d41883…94ad` INVARIATO (nessun append RT2-A in Phase 2)

### 12.4 Application status (all zero as authorized)
| Superficie | Δ |
|---|---:|
| frontend code | **0** (yarn.lock untracked pre-esistente, non toccato) |
| OpenAPI | **0** (275 endpoints · 52 schemas invariati) |
| DB writes | **0** |
| migrations | **0** |
| Registry generation | **0** |
| Registry apply | **0** |
| item generation | **0** |
| new_seals | **0** |
| env | **0** |
| backend routes | **0** (nessun router aggiunto) |
| existing code modifications | **0** |

---

## 13. Audit / observability RT2-A

Eventi (via `events.py`):
- `SOFT_CAP_EVALUATION` (DEBUG)
- `SHADOW_COMPARISON` (INFO)
- `INVALID_STAT_METADATA` (WARNING)

**Sampling tiered (P0Q09 verbatim)**:
| Level | prod | staging | test/dev |
|---|---:|---:|---:|
| DEBUG | 0% | 100% | 100% |
| INFO | 10% future | 100% | 100% |
| WARNING/ERROR | 100% | 100% | 100% |

Sampling determinstic via `hash(event_id) mod 100 < pct`. Reason code obbligatorio per ogni evento (`RT2A_STAT_EVAL_OK` · `RT2A_STAT_EVAL_NO_CAP` · `RT2A_SHADOW_CANDIDATE_FAILURE` · `RT2A_SHADOW_CANDIDATE_UNEXPECTED_ERROR`). **Nessuna scrittura DB** in RT2-A: solo `logger.log(...)` strutturato JSON su `orbus.rt2_a.events`.

---

## 14. Fail-stop detection

**Elenco**: **NONE**.

- `SCOPE_EXPANSION_REQUIRED`: **NOT_TRIGGERED**
- `PERSISTENCE_BASELINE_CONFLICT`: **NOT_TRIGGERED**
- `PERFORMANCE_BASELINE_MISSING`: **NOT_TRIGGERED** (baseline riproducibile con margine ampio)
- `TRANSIENT_STATE_DEPLOYMENT_CONFLICT`: **N/A per RT2-A** (RESOLVED_BY_SCOPE_BOUNDARY)
- `ATOMICITY_PERSISTENCE_CONFLICT`: **NOT_TRIGGERED** (RT2-A side-effect free)

---

## 15. Recommendation per formal closure

**`RT2-A READY-FOR-PM-CLOSURE`**

Motivazione:
- 11/11 scope items implementati (P0Q10 verbatim)
- 136/136 test PASS
- 5/5 soft-cap boundary cases PASS
- 9/9 modifier order steps verificati
- Snapshot immutabile · non persistente · P0Q02 conforme
- Shadow path 10/10 diagnostic fields · P0Q05 conforme
- Compatibility contract verificato programmaticamente (flag OFF → zero percorso RT2-A raggiunto)
- Performance p95 overhead 99% sotto soglia P0Q07 (baseline riproducibile)
- Sealed integrity 6/36 byte-identical · anchor invariant · baseline chain 30/30 invariant
- Application status: tutti zero (nessun frontend / OpenAPI / DB / migration / registry / item-gen delta)
- Zero fail-stop deterministici

---

## 16. STOP esplicito

Phase 2 code completata. NESSUN passaggio a rollout step 4+ (test-user activation, staging, produzione shadow, live activation, GA) autorizzato. NESSUN append PRD RT2-A (deferito a formal closure ratificata PM). NESSUNA anticipazione a RT2-B/C/D/E. In attesa di verdict PM per formal closure e authorization rollout successivi.

---

**Fine documento** · Italian_only · RT2-A CODE GATE · NEW SEAL = NO · SHA Policy §31
