# Round 16.5.4e — Territory KeyError Hotfix — CLOSED & SEALED ✅

**Data**: 2026-07-04T07:37:00Z (UTC).
**Tipo**: micro-hotfix difensivo, no refactor territory.

## Root cause (2 righe)

`get_structure_max_level(slug)` in `app/territory/structures.py:174` faceva un lookup diretto `STRUCTURE_CATALOG[slug]` senza guard. Documenti `guild_structures` legacy contengono slug (es. `library`) rimossi dal catalog in un refactor storico → ogni `GET /api/territory/my` per gilde affette lanciava `KeyError: 'library'` in `_public_doc`.

## Fix applicato (diff sintetico)

**File**: `app/territory/structures.py`, funzione `get_structure_max_level`.

```diff
 def get_structure_max_level(slug: str, *, allow_legacy: bool = False) -> int:
     """Return max upgrade level..."""
-    meta = STRUCTURE_CATALOG[slug]
+    meta = STRUCTURE_CATALOG.get(slug)
+    if meta is None:
+        import logging
+        logging.getLogger("orbus.territory").warning(
+            "get_structure_max_level: unknown structure slug %r "
+            "(likely legacy doc referencing a dropped catalog slug). "
+            "Returning 0 as sentinel.", slug,
+        )
+        return 0
     if allow_legacy and "max_legacy_level" in meta:
         return int(meta["max_legacy_level"])
     return int(meta["max_level"])
```

**Comportamento post-fix**:
- Slug conosciuti → invariato (nessuna regressione).
- Slug sconosciuti → `0` (sentinel "no upgrade path") + WARN log una-tantum.
- `_public_doc`: itera comunque su tutti gli slug del doc (anche orfani), ma per slug con `max_lv=0` la condizione `cur_level < max_lv` è sempre False → `next_level_cost` resta `None`. Nessuna struttura fantasma diventa upgradabile via user.

## Test (nuovo file dedicato)

**File**: `backend/tests/backend_round1654e_territory_hotfix_test.py`

6 test dedicati:
- `test_get_structure_max_level_known_slug_returns_catalog_value` — sanity check no regressione.
- `test_get_structure_max_level_unknown_slug_no_keyerror` — verifica `library` non lancia più KeyError.
- `test_get_structure_max_level_unknown_slug_with_legacy_flag_no_keyerror` — copre `allow_legacy=True` path.
- `test_get_structure_max_level_unknown_slug_emits_warning` — verifica WARN log.
- `test_public_doc_survives_legacy_orphan_slug` — integrazione con doc misto (guild_hall + library).
- `test_public_doc_no_crash_when_all_slugs_are_orphan` — edge case tutti orfani.

**Esito**: **6/6 PASSED** in 0.54s (pytest xdist 2 workers).

## Vincoli rispettati

- ✅ Nessuna modifica gameplay/economia/PvP/premium/drop/reward.
- ✅ Nessun refactor territory (scope stretto).
- ✅ Nessun hard delete di doc `guild_structures`.
- ✅ Fix difensivo, nessuna nuova feature.
- ✅ Doc legacy con slug orfani continuano a essere serviti — client vede lo slug (per non alterare la shape) ma non può upgradarlo.

## Follow-up (opzionale, non R16.5.4e)

Un round futuro dedicato di data cleanup potrà emettere una migration idempotente per rimuovere gli slug orfani dai doc `guild_structures` legacy, usando il WARN log come input per identificarli. Non urgente.

**Sigillo**: R16.5.4e chiuso.
