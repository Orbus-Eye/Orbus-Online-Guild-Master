# ROUND 13a — Recovery + Lore Pack — Progress Log

> COMPLETATO. Tutte le 6 fasi DONE. Pronto per E2E utente.

## FASE 0 — Baseline (DONE)

Snapshot DB pre-recovery:
- `db.dungeons` = **32** (22 baseline + 10 R11.3 Void)
- `db.raid_dungeons` = **8** (3 baseline + 5 R11.3 Void)
- `db.items` = **121** (120 attivi + 1 inactive)
- Rarity: Common=42, Uncommon=28, Rare=22, Epic=24, Legendary=5
- `required_adventurer_level > 1`: 0 (gap)
- `lore_reviewed`: 0 (gap)

## FASE 1 — Additività R11.3 (DONE)

Verificato: 22 baseline dungeon + 10 nuovi R11.3 = 32 → additivi.
- Slug nuovi: echoes-of-the-broken-thread, shattered-seal-of-ergolat,
  obelisks-of-the-void, plague-warrens-of-irthe, moonlit-strings-of-alevora,
  ashkaroth-crypt-court, eclipthra-veiled-sanctum, gralca-tide-of-the-deep,
  xal-zoraax-throat-of-silence, tip-of-oblivion-trial.
- Raid additivi: 5 nuovi R11.3 + 3 baseline = 8.

**Decisione**: NON seed altri +10/+5. Uso i 10+5 R11.3 come "i nuovi".

## FASE 2 — Dungeon/Raid lore rework (DONE)

### Files creati
- `app/content/lore_meta.py` — SoT slug → {name_it, lore_theme, content_family, emotional_tone, narrative_hook, enemy_families, boss_name, spoiler_level} + sets `NEW_DUNGEON_SLUGS_R113` / `NEW_RAID_SLUGS_R113`.
- `app/scripts/seed_round13a_dungeon_raid_lore.py` — Seed idempotente registered nel lifespan.

### Bug fix
`find_one(..., {"_id":0, "lore_reviewed":1})` ritornava `{}` (falsy) per docs senza `lore_reviewed`. Fix: include `slug:1` nella projection e check esplicito `existing is None`.

### Risultati post-run
- `db.dungeons` reviewed: **32/32** + `name_it` set su 32/32.
- `db.raid_dungeons` reviewed: **8/8** + `name_it` set su 8/8 + `boss_name` su 8/8.
- Sample `echoes-of-the-broken-thread` → `{content_family: void_undead, name_it: "Echi del Filo Spezzato"}`
- Sample `valys-mordivac-final-whisper` → `{name_it: "L'Ultimo Sussurro di Valys Mordivac", boss_name: "Valys Mordivac", spoiler_level: "hidden"}`

### Serializer estesi
- `dungeon_public` (`app/dungeons/services.py`) ora espone `name_it`, `description_it`, `lore_theme`, `content_family`, `emotional_tone`, `location_hint`, `narrative_hook`, `enemy_families`, `spoiler_level`, `is_new`, `is_void_undead`, `lore_reviewed`, `min_adventurer_level`.
- `raid_dungeon_public` (`app/raids/__init__.py`) stesso pattern + `boss_name`.

## FASE 3+4 — Item lore + required_level (DONE)

### Files
- `app/scripts/seed_round13a_items_lore.py` — Seed idempotente registrato nel lifespan.

### Risultati post-run
- Items reviewed: **120/121** (1 inactive `banner-of-glory` skippato volutamente).
- `required_adventurer_level` set su 120 items:
  - Common (42) → Lv 1
  - Uncommon (28) → Lv 3
  - Rare (22) → Lv 5
  - Epic (23) → Lv 8 (1 Epic inactive)
  - Legendary (5) → Lv 12
- `display_name_it`: 120/121
- `flavor_text_it`: 78/121 (Common = NULL by design)
- 4 hand-written display name Epic/Legendary: voidpiercer-bow, oracle-pendant, phoenix-relic, dragon-mask
- `lore_tags` su tutti, `spoiler_level` (mystery per Legendary)

### Serializer esteso
- `item_public` (`app/items/services.py`) ora espone `display_name_it`, `display_name_en`, `flavor_text_it`, `flavor_text_en`, `lore_tags`, `spoiler_level`, `lore_reviewed`, `required_adventurer_level` (già presente da R11.3).

### Level audit eseguito (dry_run=false)
- File: `/app/memory/round13a_level_audit_diff_20260629T100848Z.json`
- Scanned: **568 equipped_items rows**
- Invalid: **15**
- Auto-unequipped: **15** (soft, items restano in inventory)
- Guilds touched: **5**
- By slug: drake_slayer_helm=5, drake_slayer_chest=5, drake_slayer_blade=5
- < 50 unequipped: nessun warning operativo.

## FASE 5 — API + UI visibility (DONE)

### Backend serializer
- ✓ `dungeon_public` espone tutti campi lore additivi.
- ✓ `raid_dungeon_public` espone tutti campi lore additivi + boss_name.
- ✓ `item_public` espone display_name_it/en, flavor_text_it/en, lore_tags, spoiler_level, required_adventurer_level.

### Frontend
- ✓ `Dungeons.jsx` aggiornato: card mostra `name_it` (fallback `name`), badge `NUOVO` / `✦ VUOTO` / `Lv min: X` / `tema lore`, narrative_hook in italics, filtro `lore_family` (Tutti/Void-Nonmorti/Solo Nuovi/Baseline/Natura/Memoria/Arcano/Divino).
- ✓ `Raids.jsx` aggiornato: card mostra `name_it`, badge `NUOVO`/`✦ VUOTO`/`Lv min`/`Boss: <name>`, narrative_hook.
- ✓ `AdventurerEquipment.jsx` (R11.3D.3): già usa `resolve_item_required_level` server-side. Nessuna modifica necessaria.

### data-testid aggiunti
- `dungeon-new-badge-{slug}`, `dungeon-void-badge-{slug}`, `dungeon-min-level-badge-{slug}`, `dungeon-theme-badge-{slug}`, `dungeon-desc-{slug}`, `dungeon-hook-{slug}`, `filter-lore-family`.
- `raid-new-badge-{slug}`, `raid-void-badge-{slug}`, `raid-min-level-badge-{slug}`, `raid-boss-{slug}`, `raid-desc-{slug}`, `raid-hook-{slug}`.

## FASE 6 — Guide + Test + E2E (DONE)

### Guide.jsx (5 nuove sezioni)
- `nuovi-dungeon-void` (14c) — Elenco 10 nuovi Void/Non-Morti con Lv min + tema 1-riga.
- `nuovi-raid-void` (14d) — Elenco 5 nuovi raid Void/Non-Morti con boss_name + Lv min.
- `lore-vuoto-nonmorte` (14e) — 5 paragrafi player-facing su Filo Spezzato, Vuoto, Esiliati, Non-Morti, endgame (Valys Mordivac).
- `equip-level-gate` (16a) — Scala Lv min per rarità + spiegazione 423 + audit menzionato.
- `equip-lore-tematica` (16b) — Pattern naming per rarità + nomi Leggendari cherry-pick.
- `_shared.jsx` SECTIONS aggiornato: 5 voci nuove nel nav sticky.

### Test
- `tests/backend_round13a_test.py` — **8 PASSED + 1 SKIPPED** (Lv1 equip gate skip: tester non ha advs Lv1 + Legendary; gate teorico coperto da R11.3D.3 tests).
- Test coverage:
  - 01 dungeons count=32 + all lore_reviewed
  - 02 dungeons espongono name_it/lore_theme/content_family/is_new/is_void_undead/spoiler_level/min_adventurer_level, e i 10 R11.3 Void sono is_new=is_void_undead=True
  - 03 raids count=8 + all lore_reviewed
  - 04 raids espongono boss_name (non vuoto per ogni raid)
  - 05 items required_adventurer_level>=1 esplicito su tutti, lore_reviewed=true
  - 06 items display_name_it presente; voidpiercer-bow="Arco Trafittore del Vuoto" Lv8 tag vuoto
  - 07 SKIPPED (no Lv1 adv tester)
  - 08 slug distinct invariati (dungeons/raids/items)
  - 09 no PII leak in /api/inventory (no email, no $oid, no owner_user_id)

### Lint
- `yarn lint:strict` su Dungeons.jsx / Raids.jsx / Guide.jsx → 0 warnings.

## STATUS FINALE

| Layer | Check | Result |
|---|---|---|
| DB | 32 dungeon `lore_reviewed=true` | ✓ |
| DB | 8 raid `lore_reviewed=true` | ✓ |
| DB | 120 item `required_adventurer_level>=1` + `lore_reviewed=true` | ✓ |
| DB | 1 inactive item skippato volutamente | ✓ |
| DB | Level audit eseguito: 15 unequip, 5 guilds, 0 hard delete | ✓ |
| Backend | `/api/dungeons` espone name_it + lore meta | ✓ |
| Backend | `/api/raids/catalog` espone name_it + boss_name + lore meta | ✓ |
| Backend | `/api/items`, `/api/inventory` espongono display_name_it/flavor/lore_tags | ✓ |
| Frontend | Dungeons.jsx badge + filtro lore_family | ✓ |
| Frontend | Raids.jsx badge + boss_name + narrative_hook | ✓ |
| Frontend | Equip modal R11.3D.3 — verificato (no change) | ✓ |
| Guide | 5 nuove sezioni R13a | ✓ |
| Tests | 8 PASSED + 1 SKIPPED (gate skip) | ✓ |

Ready per E2E utente.
