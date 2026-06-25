# ROUND 1.5 — Phase 14.4 Playtest Notes

Date: 2026-06-25 (cont. session)

## What changed (frontend-only, no new endpoints)

### Task 1 — Password show/hide toggle
- `src/components/PasswordInput.jsx`: reusable input with eye icon, accessible
  (aria-label, aria-pressed), preserves `autoComplete`/`name`, default hidden.
- Wired into `Login.jsx`, `Register.jsx`, `PasswordResetConfirm.jsx`.
- i18n keys: `password_input.show_label`, `password_input.hide_label` (EN+IT).
- data-testids: `*-password-input`, `*-password-input-toggle`.

### Task 2 — Confirm password on Register
- Client-side validation only (no OpenAPI change).
- Field id `confirm_password`, testid `register-confirm-password-input`.
- Error message via i18n `auth.errors.password_mismatch`
  (EN: "Passwords do not match" / IT: "Le password non coincidono").

### Task 3 — Adventurer detail modal
- `src/components/AdventurerDetailModal.jsx`: shows level, XP bar, raw stats,
  total power, traits with descriptions, equipment per slot.
- Closes on X / ESC / backdrop click. Focus moves to close button on open.
- Hooked into `Adventurers.jsx` from both the desktop table (row click +
  dedicated `adventurer-name-${id}` button) and the mobile card (whole-card
  role=button + keyboard activation).
- Existing actions (Trait preview, Manage equipment link, traits area) stop
  event propagation so they keep working without opening the sheet.
- Pre-existing bug fix bonus: `Empty` component in `Adventurers.jsx` was
  calling `t()` from outside the component scope (would crash on an empty
  roster). Now receives `t` as a prop.

### Task 4 — Item requirements (Inventory)
- Each card now exposes a **REQUIREMENTS** row showing
  `Lvl ≥ N` (from `item.level_required`) and `Slot: WEAPON/ARMOR/ACCESSORY`
  (derived from `item.item_type`).
- A muted line communicates the cohort impact:
  "Usable by N adventurer(s)" / "Utilizzabile da N avventuriero/i".
- When stock is available but no adventurer matches, the card displays the
  reason: either the required level (e.g. "Requires level 3") or the generic
  "No compatible adventurer" (slots full / all on expedition).

### Task 5 — Equip clarity (Inventory)
- **STATUS** row shows two parallel badges:
  - green "Available × N" when `available_quantity > 0`
  - amber "Equipped by: <names>" listing each adventurer that wears a copy
    (we cross-reference `/api/adventurers` to surface names client-side).
- **ACTIONS** row:
  - per-equipped-adventurer "Manage on <name>" link → `/adventurers/{id}/equipment`
  - per-eligible-adventurer "▶ <name>" equip button (max 6 shown + "+N" overflow)
  - eligibility = available stock + adventurer level ≥ requirement + slot empty + not on expedition.
- Inventory model is explicit at the top of the page (`inventory-model-note`)
  and documented in the file header: stacks with per-equip reservations.

## Backend invariants

- **No new endpoints** in ROUND 1.5.
- OpenAPI path count stays at 43.
- `/api/adventurers` already exposes `traits` + per-slot `equipment` →
  AdventurerDetailModal and Inventory "Equipped by" rely on that data, no
  schema change.
- Equip endpoint is unchanged; cross-adventurer reservation guard
  (Phase 9.3.1) keeps protecting against double-equip races.

## Trade-offs documented

- **"Replace" button not exposed**: requires backend unequip+equip combo
  (two atomic ops). Surfacing it would need either a new swap endpoint or a
  two-step UI that can leave a slot empty between calls. We deferred and kept
  "Manage" deep-link instead.
- **Equip from Inventory page**: limited to **empty** slots. To replace an
  existing equipped item the user goes through the per-adventurer page where
  Unequip is available.
- **Inventory ↔ Adventurers join is client-side**: two parallel GETs on page
  load; refresh after each equip. Same pattern already in
  `AdventurerEquipment.jsx`.

## Test status (pytest)

- `backend_phase14_4_round15_test.py` (NEW, 5/5) — inventory shape,
  adventurers shape, OpenAPI count==43, register validation guards.
- `backend_phase14_3_traits_preview_test.py` — 9/9 PASS (trait leak + dungeon
  preview ROUND 1 invariants).
- `backend_phase931_security_test.py::TestPhase931OpenAPI` — 11/11 PASS
  (the off-by-one assertion was aligned to 43, as documented in the file).
- `backend_phase9_leaderboard_test.py` — 5/5 PASS (Step A2 invariant intact).
- Frontend `yarn build` PASS (190 kB gz main).
- ESLint PASS on Adventurers / Inventory / PasswordInput / AdventurerDetailModal.

## Out of scope (will land later)

- Phase 3 report explainability.
- Phase 4 loot/equip scaffolding.
- Backend swap endpoint (would unblock the "Sostituisci" button).
- True class restrictions on items (current schema has only `level_required`).
