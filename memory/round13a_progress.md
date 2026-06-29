# ROUND 13a — Recovery + Lore Pack — Progress Log (FINAL)

> 6 fasi DONE + 4 mini-fix richiesti dall'utente DONE. Pronto per E2E tester.

## Mini-fix finali (Messaggio post-report 30 punti)

### Fix 1 — TC1 Dungeon `Lv min` badge SEMPRE visibile (DONE)
- `Dungeons.jsx`: badge `dungeon-min-level-badge-{slug}` ora visibile su tutti i 32 dungeon (anche `min_adventurer_level=1`).
- Stile mutato (`border-border/50 text-muted-foreground`) sui Tier 1 per ridurre rumore visivo; stile amber acceso solo per `lvl > 1`.
- `Raids.jsx`: stesso pattern (badge `raid-min-level-badge-{slug}` su tutti gli 8).

### Fix 2 — TC8 Leaderboard default category (DONE)
- `Leaderboard.jsx`:
  - Guard difensivo in `fetchCategory(slug, ...)`: se `slug` è falsy → skip + warn, niente chiamata API.
  - URL sync al primo mount: se `?category=` mancante, il default risolto (`peak_power` global / `arena_rating` season) è scritto in URL via `setSearchParams({replace:true})`.
- Verifica curl: `/api/leaderboard?category=peak_power&limit=3` → HTTP 200 con `entries=3`. `/api/leaderboard?limit=3` (senza category) → HTTP 422 (BE rifiuta correttamente).

### Fix 3 — TC3 Indagine 2 item delta (DONE)
- Query motor su `db.items` filtro `is_active != False` + `required_adventurer_level` mancante o None:
  ```
  Found 0 items WITHOUT required_adventurer_level (active).
  ```
- L'unico item escluso è `banner-of-glory` (rarity=Epic, `is_active=False`) — escluso per design.
- **Conta finale corretta**: 121 totali, 120 attivi (Common 42 + Uncommon 28 + Rare 22 + Epic 23 + Legendary 5), 1 inactive escluso. **Tutti i 120 attivi hanno `required_adventurer_level >= 1` esplicito e `lore_reviewed=True`**.
- Il "delta 118/120" segnalato dall'utente era un fraintendimento numerico: gli item attivi sono 120 (Epic=23, non 24, perché 1 Epic è inactive). Nessun gap reale.

### Fix 4 — Evidenza badge equip UI (DONE)
- `tests/backend_round13a_test.py::test_r13a_07_underleveled_cannot_equip_legendary_real`:
  - Identifica avs Lv1 del tester (non-retired, non in spedizione).
  - Auto-provisiona Legendary `drake_slayer_helm` via `POST /api/admin/guilds/{guild_id}/grant-item` se inventory non ne contiene.
  - Chiama `POST /api/adventurers/{adv_id}/equip` con `{item_id, slot}`.
  - Asserzione: HTTP **423** con detail strutturato `equipment.level_requirement_not_met`.
  - **Output evidenza**: `adv lv1 on Legendary drake_slayer_helm → HTTP 423 detail={'code':'equipment.level_requirement_not_met',...}`.
  - **PASSED** in 1.37s.

## Test BE finali

```
backend_round13a_test.py::test_r13a_01_dungeons_count_and_lore_reviewed       PASSED
backend_round13a_test.py::test_r13a_02_dungeons_expose_lore_fields            PASSED
backend_round13a_test.py::test_r13a_03_raids_count_and_lore_reviewed          PASSED
backend_round13a_test.py::test_r13a_04_raids_expose_lore_fields               PASSED
backend_round13a_test.py::test_r13a_05_items_required_level_and_reviewed      PASSED
backend_round13a_test.py::test_r13a_06_items_display_name_it_and_lore_tags    PASSED
backend_round13a_test.py::test_r13a_07_underleveled_cannot_equip_legendary_real PASSED
backend_round13a_test.py::test_r13a_08_slug_count_invariants                  PASSED
backend_round13a_test.py::test_r13a_09_no_pii_in_inventory                    PASSED

9 passed in 0.72s
```

## Smoke regression (curl)

| Endpoint | Status | Nota |
|---|---|---|
| `GET /api/recruitment/candidates` | 200 | `candidates=4, frozen=0` |
| `GET /api/recruitment/frozen` | 200 | OK |
| `POST /api/admin/ops/release-stuck-adventurers` (dry) | 200 | `released=0 dry_run=True` |
| `GET /api/leaderboard?category=peak_power` | 200 | `entries=3` |
| `GET /api/leaderboard?limit=3` (no cat) | 422 | BE rifiuta correttamente |
| `GET /api/dungeons` | 200 | 32 total, 10 is_new (R11.3), 13 is_void_undead (10 nuovi + 3 baseline tematici), 32/32 min_level |
| `GET /api/raids/catalog` | 200 | 8 total, 8/8 boss_name |
| `GET /api/inventory` | 200 | no PII leak |

## Stato Round 13a

✅ 6 fasi originali DONE  
✅ 4 mini-fix DONE  
✅ 9/9 test BE PASSED  
✅ Lint pulito (Dungeons/Raids/Leaderboard)  
✅ Webpack "Compiled successfully"  
✅ Smoke regression OK su Recruitment / Admin / Leaderboard / Dungeons / Raids  

**Pronto per il tester E2E utente.**
