# R18.6 · POST-SYNC-INTEGRITY-P1 · UI4STATE Controlled Sealed-Break Addendum

> **Gate**: `POST-SYNC-INTEGRITY-P1 · UI4STATE CONTROLLED SEALED-BREAK FOR 10-SLOT REVAMP`
> **Regime**: Controlled successor seal · targeted single-hash update · no PRD append · no closure manifest · baseline unchanged.

---

## 0 · Identity

| Field | Value |
|---|---|
| gate_id | `POST-SYNC-INTEGRITY-P1` |
| gate_title | UI4State Controlled Sealed-Break for 10-Slot Revamp |
| repository | `Orbus-Eye/Orbus-Online-Guild-Master` |
| branch | `main-260728` |
| pre_remediation_head | `34546b40c3e2fae12bec739ce8bc7524639ff7cf` |
| pm_authority | PM dispatch `POST-SYNC-INTEGRITY-P1 · UI4STATE CONTROLLED SEALED-BREAK FOR 10-SLOT REVAMP` |
| baseline_pre | `17/17` |
| baseline_post | `17/17` (unchanged · no increment) |

---

## 1 · Status declaration

```
UI4STATE_SEALED_HASH = SUCCESSOR RATIFIED
functional content            = UNCHANGED (already at canonical target at HEAD)
sealed integrity test contract = UPDATED (single hash constant only)
sealed artifact count          = 36 (unchanged)
baseline chain                 = 17/17 (unchanged)
closure manifest               = NOT CREATED (PM regime)
PRD append                     = NONE
database writes                = 0
deployment                     = UNCHANGED
```

**This is a controlled successor seal. It does not rewrite or invalidate the historical R18.4 closure.**

---

## 2 · Hash transition

| Field | Value |
|---|---|
| sealed_file_path | `backend/app/equipment/ui_4state.py` |
| original_sealed_sha256 | `7054ec65d19066074f6cdb646f472f08213533ab0683e6dcfbeefa01a1e74aa7` |
| new_canonical_sha256 | `0b19287a48e8506006285d4460d3ffdd0235a44062b1132379616fd1404570a9` |
| updated_constant | `R18_4_FOLLOWUP_NEW_6_SEALED_HASHES` |
| updated_file | `backend/tests/backend_r18_4_sealed_integrity_test.py` |
| line_touched | one (value line for `ui_4state.py` entry) |
| adjacent_hashes_touched | 0 |
| test_logic_touched | 0 |
| assert_lines_touched | 0 |
| sealed_count_touched | 0 (36 preserved) |

---

## 3 · Exact functional diff (canonical closure `c0d8150c…` → HEAD `34546b40…`)

```diff
diff --git a/backend/app/equipment/ui_4state.py b/backend/app/equipment/ui_4state.py
index 9889701..07d8646 100644
--- a/backend/app/equipment/ui_4state.py
+++ b/backend/app/equipment/ui_4state.py
@@ -80,7 +80,10 @@ def derive_ui_4state(adventurer: dict[str, Any], item: dict[str, Any]) -> dict[s
     policy = (item.get("item_binding_policy") or "").strip().lower()
     slot_type = item.get("slot_type")
     item_type = (item.get("item_type") or "").strip().lower()
-    equipable_types = {"weapon", "armor", "accessory", "shield"}
+    equipable_types = {
+        "weapon", "armor", "legs", "helmet", "accessory",
+        "back", "ring", "trinket", "shield",
+    }

     is_universal_derived = (policy == "universal")
```

**Blob-level attribution** (from `git blame -L 80,92 34546b40 …`):
- Lines 83–86 (the drift): commit `34546b40` · author `Andrea Gualmini` · date `2026-07-30 16:18:03 +0200` · message `Complete item-first roadmap through T8 tester release`
- Adjacent lines 80–82, 87–92: commit `c4b097bb` (2026-07-06) · `emergent-agent-e1` · sealed baseline invariant

---

## 4 · Reason for sealed-break

**10-slot equipment revamp** (item-first roadmap, T0-T8 documented in `memory/ROADMAP_CURRENT.md` and `memory/HANDOFF_CURRENT.md`):

- Original set (R18.4.followup Phase C canonical baseline): `{weapon, armor, accessory, shield}` — 4 legacy slot categories.
- New canonical set (`main-260728` @ `34546b40`): `{weapon, armor, legs, helmet, accessory, back, ring, trinket, shield}` — 9 canonical item_type categories mapping to the 10 physical equipment slots (`arma, corazza, gambe, elmo, accessorio, schiena, due anelli, due monili`).

The `equipable_types` set is used at line 105 of `ui_4state.py` to detect the `slot_missing` edge case (equipable `item_type` with absent `slot_type` → `blocked` with `reason_code = "slot_missing"`). Without the extension, the new item categories would fall through the "non-equipable" branch and lose the diagnostic semantics.

---

## 5 · Affected slot types (5 additions)

| item_type | Italian noun | Slot physical mapping |
|---|---|---|
| `legs` | Gambe | leg armour |
| `helmet` | Elmo | head armour (canonical rename of legacy `head`) |
| `back` | Schiena | cloak / cape |
| `ring` | Anello | ring slots 1 & 2 |
| `trinket` | Monile | trinket slots 1 & 2 |

Corresponding canonical catalog entries confirmed in `backend/app/items/final_catalog.py` (lines 55-62, 680) and grammatical mappings in `backend/app/equipment/auto_equip.py` (lines 186-302).

---

## 6 · Impact analysis of hypothetical revert (Option B — rejected)

Reverting `ui_4state.py` to the original sealed content would:

1. Break the `slot_missing` diagnostic for 5 canonical item categories (legs / helmet / back / ring / trinket).
2. Force introduction of a duplicated `equipable_types` set in an external wrapper (violating DRY; the caller `adventurers/routes.py:304` already has an 11-type local list including `chest` and `head`).
3. Fragment the semantic meaning of "equipable" across sealed helper and unsealed caller.
4. Fail the item-first tester journey (11 item categories in production catalog + 5 unrecognised in the helper's edge-case detection).
5. Constitute a regression against the ratified 10-slot revamp architecture documented in `HANDOFF_CURRENT.md` and `ROADMAP_CURRENT.md`.

**PM Option A (this addendum)** preserves the canonical helper as single source of truth and formally ratifies the new hash as successor seal.

---

## 7 · Callers inventory

| Caller | Location | Nature |
|---|---|---|
| `derive_ui_4state` | `backend/app/adventurers/routes.py:319` (production endpoint items-compatibility) | 1 production caller |
| `derive_ui_4state` | `backend/tests/backend_r18_4_followup_ui_4state_test.py` (Group 1 + Group 3) | Unit + integration tests |
| `VALID_COMPATIBILITY_STATES` | `backend/tests/backend_r18_4_followup_ui_4state_test.py:252,281,406,436,462,485` | Contract validation |
| `slot_missing` reason code | `frontend/src/utils/compatibilityLabels.js:43` | UI label |

No orphan callers found. No other callers rely on the pre-extension set.

---

## 8 · Test evidence

### 8.1 · Targeted UI4State tests (functional invariance)

Executed:
```bash
PYTHONDONTWRITEBYTECODE=1 pytest -p no:cacheprovider \
  backend/tests/backend_r18_4_followup_ui_4state_test.py -q
```

Result (during P0 read-only discovery, canonical evidence): **`13 passed in 2.42s`**.
Post-remediation identical (see §9 · Verification block).

### 8.2 · Sealed integrity test (governance)

Executed:
```bash
PYTHONDONTWRITEBYTECODE=1 pytest -p no:cacheprovider \
  backend/tests/backend_r18_4_sealed_integrity_test.py -q
```

Pre-remediation result: **1 failed / 5 passed** (SHA drift on `ui_4state.py`).
Post-remediation expected: **6 passed / 36 byte-identical** (see §9).

---

## 9 · Verification block (post-remediation)

Filled at STEP 4 execution:

| Check | Expected | Command |
|---|---|---|
| `ui_4state.py` SHA256 | `0b19287a48e8506006285d4460d3ffdd0235a44062b1132379616fd1404570a9` (unchanged) | `sha256sum backend/app/equipment/ui_4state.py` |
| `lore_meta.py` SHA256 | `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` (canonical invariant) | `sha256sum backend/app/content/lore_meta.py` |
| UI4State targeted tests | `13 passed / 0 failed` | `pytest backend/tests/backend_r18_4_followup_ui_4state_test.py -q` |
| Sealed integrity tests | `6 passed / 36 byte-identical` | `pytest backend/tests/backend_r18_4_sealed_integrity_test.py -q` |
| OpenAPI paths | `283` (measured P0 · doc says 284 · P2 responsibility) | in-process `server.app.openapi()` |
| Tracked working tree | Only `M backend/tests/backend_r18_4_sealed_integrity_test.py` + 2 new files in `memory/` | `git status --short` |

---

## 10 · Scope compliance

- ✅ ONE file modified: `backend/tests/backend_r18_4_sealed_integrity_test.py` (single hash value line)
- ✅ TWO files created: this addendum (MD + JSON)
- ✅ `backend/app/equipment/ui_4state.py` NOT modified (already at canonical target)
- ✅ `memory/PRD.md` NOT modified (regime forbids PRD append)
- ✅ Closure manifest NOT created (regime forbids)
- ✅ Sealed artifact count = 36 (unchanged)
- ✅ Baseline = 17/17 (no increment)
- ✅ `lore_meta.py` SHA canonical invariant preserved
- ✅ No `.env` / dependency / deployment / DB / feature-flag changes
- ✅ No commit / push / merge / PR / rollback / branch switch
- ✅ No new test file
- ✅ No `testing_agent` / `e1_tester` invocation
- ✅ 11 untracked pre-gate preserved intact

---

## 11 · Successor seal declaration

**This is a controlled successor seal. It does not rewrite or invalidate the historical R18.4 closure.**

The original hash `7054ec65…4aa7` remains the authoritative seal of the R18.4.followup Phase C closure snapshot (baseline chain 13/13 → 14/14 era). The new hash `0b19287a…70a9` is the authoritative sealed reference for the `main-260728` branch item-first canonical state at HEAD `34546b40…`. Both hashes are historically valid; only the new one is enforced by the current sealed integrity test contract.

---

## 12 · Next authorized step

PM adjudication awaited. On PM ratification, `POST-SYNC-INTEGRITY-P2 · OPENAPI_DOC_STALE_FIX_284_TO_283` is the proposed successor gate (documentation-only correction of `HANDOFF_CURRENT.md:61` and `r18_6_classless_27_item_first_report.md:37` to align the "284 paths" claim to the measured `283` paths).

**P2 is NOT AUTHORIZED yet. STRICT STOP after P1 verification block.**
