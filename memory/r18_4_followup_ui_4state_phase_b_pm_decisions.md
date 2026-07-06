# R18.4.followup — UI 4-State Item Compatibility Activation — Phase B PM Decision Lock

- **Round**: `R18.4.followup — UI 4-State Item Compatibility Activation`
- **Phase**: B — Implementation Decision Lock
- **Locked at UTC**: `2026-07-06T08:15:00Z`
- **Seal Authority**: PM Orchestrator
- **Perimetro**: read-side API updates + UI 4-state activation. Zero DB write. Zero runtime enforcement change.
- **Fonti**: Phase A Discovery (`/app/memory/r18_4_followup_ui_4state_phase_a_discovery.md/json`) + risposte PM verbatim B.SQ1..B.SQ8.

---

## 1. Decisioni PM verbatim (B.SQ1..B.SQ8)

### B.SQ1 — Enum values naming: **(c) Entrambi — raw enum + derived flags**
Serializer espone: `item_binding_policy` (raw `"hard"/"soft"/"universal"`) + `slot_type` + `is_universal` (derived) + `recommended_for_class` + `compatibility_state` (dove esiste contesto adventurer).
- **Impatto**: `item_public()` estende output con 3 campi raw + derived. Endpoint context-aware espone anche `recommended_for_class` + `compatibility_state`.

### B.SQ2 — Computed vs raw exposure: **(a) Server-side context-aware**
`recommended_for_class` calcolato SOLO negli endpoint che conoscono adventurer context (es. `/api/adventurers/{id}/eligible-items`). Endpoint generici (es. `/api/items`) → campo `null` o assente, no computed.
- **Impatto**: `item_public()` NON calcola `recommended_for_class`. Solo endpoint `/api/adventurers/{id}/eligible-items` lo popola.

### B.SQ3 — Localization scope: **(a) Solo enum tecnico backend**
Valori enum backend: `hard`, `soft`, `universal`, `blocked`, `recommended`, `not_recommended`. **NO** `compatibility_label_it` o `compatibility_reason_it` server-side.
- **Impatto**: label localizzata IT è **responsabilità frontend** (helper `compatibilityLabels.js`).

### B.SQ4 — Mobile display strategy: **(b) Icona + badge testuale mobile**
UI 4-state: icona lucide-react + short IT text badge. NO tooltip espansa mobile.
- **Impatto**: `ItemCompatibilityBadge.jsx` rende icona + testo IT sempre; no popover complesso.

### B.SQ5 — Backward compat slot: **(a) Fallback obbligatorio**
Frontend usa `item.slot_type ?? item.item_type` **OVUNQUE** viene risolto lo slot. Risolve Risk 10.1 (shield mismatch).
- **Impatto**: modifiche a `InventoryEquipModal.jsx` (line 46) + eventuali altri consumer.

### B.SQ6 — Endpoint contract: **(c) Endpoint dedicato**
Nuovo endpoint: `GET /api/adventurers/{id}/eligible-items`. Payload per item: `item_id, name, item_type, slot_type, item_binding_policy, can_equip, compatibility_state, recommended_for_class, is_universal, reason_code`.
- **Impatto**: nuovo endpoint READ-ONLY, ownership guard via `get_current_user`, query inventory della guild dell'adventurer.

### B.SQ7 — Shield fix scope: **(a) Incluso in Phase B**
Shield fix (item_type=shield, slot_type=armor) verificato nel flow UI/equipment nella stessa Phase B.
- **Impatto**: test dedicato `test_eligible_items_shield_mapping` verifica end-to-end.

### B.SQ8 — Test coverage: **(a) 12 test minimi**
8 backend + 4 frontend/E2E + regression smoke.

---

## 2. Contract enum `compatibility_state`

```yaml
compatibility_state enum:
  - blocked:          equip vietato (hard policy + class mismatch)
  - not_recommended:  equip permesso ma warning (soft policy + class mismatch)
  - recommended:      equip permesso + consigliato (recommended_for_class=true)
  - universal:        equip permesso + universale (item_binding_policy=universal)

can_equip mapping:
  - blocked          → can_equip = false
  - not_recommended  → can_equip = true
  - recommended      → can_equip = true
  - universal        → can_equip = true

recommended_for_class mapping:
  - recommended      → true
  - universal        → true (universale conta come recommended per UX)
  - not_recommended  → false
  - blocked          → false
  - endpoint senza context → null (assente)

reason_code enum:
  - universal_item          — item universale
  - class_recommended       — classe adventurer tra recommended
  - class_mismatch_soft     — soft policy, classe non consigliata (equip permesso)
  - class_mismatch_hard     — hard policy, classe non compatibile (equip bloccato)
  - slot_missing            — item senza slot_type valido (edge case)
```

---

## 3. Impatto tecnico consolidato

### Backend
- `/app/backend/app/items/services.py::item_public()` → 3 nuovi field: `slot_type`, `item_binding_policy`, `is_universal`
- `/app/backend/app/adventurers/routes.py` → nuovo endpoint `GET /api/adventurers/{adventurer_id}/eligible-items`
- Nuovo modulo helper: `/app/backend/app/equipment/ui_4state.py` (derivazione `compatibility_state` + `reason_code`)

### Frontend
- Nuovo componente: `/app/frontend/src/components/ItemCompatibilityBadge.jsx`
- Nuovo helper: `/app/frontend/src/utils/compatibilityLabels.js`
- Modifica: `/app/frontend/src/components/InventoryEquipModal.jsx` (slot fallback + badge integration)

### Test
- Nuovo file backend: `/app/backend/tests/backend_r18_4_followup_ui_4state_test.py` (8 test)
- Test frontend/E2E: coperti via smoke playwright (4 test)

### Governance
- Zero DB writes ✅
- Zero runtime enforcement change ✅ (endpoint eligible-items è pure read + serializzazione)
- Zero migration ✅
- Zero touch a 30 sigilli ✅

---

## Self-check B PM decision lock 9/9
1. ✅ B.SQ1 lock enum raw + derived
2. ✅ B.SQ2 lock context-aware only
3. ✅ B.SQ3 lock enum tecnico (no label backend)
4. ✅ B.SQ4 lock icona + badge testuale
5. ✅ B.SQ5 lock slot_type fallback
6. ✅ B.SQ6 lock endpoint dedicato `/api/adventurers/{id}/eligible-items`
7. ✅ B.SQ7 lock shield fix inclusion
8. ✅ B.SQ8 lock 12 test minimi
9. ✅ Impatto tecnico consolidato + governance zero-DB-write
