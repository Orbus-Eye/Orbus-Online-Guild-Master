# Round 15 — Final Report (25 punti)

Date: 2026-06-29
Phases delivered: 1 (Audit + Class Identity), 2 (Equip Compat + XP Debuff + Materiali), 3 (Achievement + Guild XP/Level + UI), 4 (Guida + Balance audit + report).

---

### 1. File modificati (consolidato Fase 1-4)

**Backend — nuovi:**
- `app/equipment/compatibility.py`
- `app/expeditions/xp_modifier.py`
- `app/expeditions/material_drop_tables.py`
- `app/achievements/{__init__,engine,levels,services,routes}.py`
- `app/scripts/round15_seed_class_identity.py`
- `app/scripts/round15_seed_item_tags.py`
- `app/scripts/round15_legacy_unequip_incompatible.py`
- `app/scripts/round15_seed_achievements.py`
- `app/scripts/round15_phase2_evidence_{hardblock_equip,xp_debuff,monte_carlo}.py`
- `tests/backend_round15_phase2_test.py` (18 test)
- `tests/backend_round15_phase3_test.py` (10 test)

**Backend — modificati:**
- `app/core/app_factory.py` (registrazione router achievements)
- `app/guilds/services.py` (hook guild_created)
- `app/equipment/services.py` (compat validator + hook item_equipped)
- `app/expeditions/services.py` (xp multiplier + materials roll + hook dungeon_completed)
- `app/expeditions/loot_tables.py` (invariato)
- `app/recruitment/routes.py` (hook adventurer_recruited)
- `app/raids/__init__.py` (hook raid_completed)
- `app/adventurers/services.py` (projection classi estesa)
- `app/leaderboard/{multi_category,seasonal}.py` (filtro score=0 + archived guard rimasti R14)

**Frontend — nuovi:**
- `src/pages/Achievements.jsx`
- `src/pages/guide/ClassesAndStatsSection.jsx`
- `src/pages/guide/R15GuideSections.jsx`
- `src/components/GuildProgressCard.jsx`

**Frontend — modificati:**
- `src/App.js` (route /achievements)
- `src/pages/Dashboard.jsx` (mount GuildProgressCard)
- `src/pages/ExpeditionReport.jsx` (sezioni OGGETTI + MATERIALI + XP debuff badge)
- `src/pages/Guide.jsx` (include R15GuideSections)
- `src/pages/guide/_shared.jsx` (TOC + 5 entry: 34–38)

**Docs:**
- `/app/memory/round15_audit.md`
- `/app/memory/round15_material_drop_diff.md`
- `/app/memory/round15_balance_audit.md`
- `/app/memory/round15_final_report.md` (questo file)

### 2. Audit classi/statistiche
`/app/memory/round15_audit.md` — Round 15 Fase 1.

### 3. Classe → primary stat
| Classe        | Primary stat |
|---------------|--------------|
| Guerriero     | Forza        |
| Berserker     | Forza        |
| Paladino      | Forza/Fede   |
| Ladro         | Destrezza    |
| Assassino     | Destrezza    |
| Ranger        | Destrezza    |
| Monaco        | Destrezza    |
| Mago          | Intelletto   |
| Negromante    | Intelletto   |
| Bardo         | Intelletto   |
| Sacerdote     | Fede         |
| Druido        | Fede         |

Live: `GET /api/adventurer-classes` espone `primary_stat` per tutte e 12.

### 4. Classe → equip consigliato/compatibile
- Heavy armour: Warrior / Paladin / Berserker (block per mage/necromancer/priest/druid/bard).
- Arcane weapons (staff/wand/grimoire): Mage / Necromancer / Druid / Priest / Bard (block per warrior/paladin/berserker/rogue/ranger/assassin/monk).
- Bow/Ranged: Ranger.
- Dagger/Finesse: Rogue / Assassin / Ranger.
- Sacred mace/scepter: Priest / Paladin.
- Universal accessories: equipaggiabili da chiunque.
Vedi Guida §34 in `R15GuideSections.jsx` per il dettaglio completo.

### 5. XP debuff
**SÌ.** Formula 4-step in `app/expeditions/xp_modifier.py`:
- deficit ≤ 0%: 1.00
- 0% < deficit < 10%: 1.00 (tolleranza)
- 10% ≤ deficit < 20%: 0.90
- 20% ≤ deficit < 30%: 0.80
- ≥ 30%: 0.70 (cap floor)

### 6. Material drop rate
`/app/memory/round15_material_drop_diff.md` (baseline → +70% boost, cap rarità).

### 7. Material roll separato
**Confermato.** `roll_loot_for_dungeon()` (item) e `roll_materials_for_dungeon()` (materiale) chiamate separate in `_complete_one_expedition`. Test `test_r15p2_16_item_and_material_rolls_independent` su 1000 simulazioni.

### 8. Achievement catalog count
**110 / 100 richiesti** — verificato live: `GET /api/achievements/catalog` → `count: 110`.

### 9. Lista 14 categorie achievement
`primi_passi (8), roster (10), dungeon (12), raid (8), equipaggiamento (10), classi_stats (12), territorio (8), crafting (8), economia (6), pvp_stagioni (8), leaderboard (5), consorzi (3), lore (8), meta_beta (4 hidden)`.

### 10. Guild XP/Level
**Implementato.** Curva monotona (vedi `app/achievements/levels.py`):
- Lv1=0, Lv2=100, Lv5=900, Lv10=5.000, Lv20≈25k, Lv30≈79k, Lv50≈300k.
- Tests: `test_r15p3_01_*`, `test_r15p3_02_*`.

### 11. UI `/achievements`
**Implementata.** `src/pages/Achievements.jsx` — header con KPI guild_level/guild_xp/achievement_points + barra XP + filtri `Tutti/In corso/Completati` + dropdown categoria + lista raggruppata per categoria. 16 data-testid.

### 12. Dashboard "Progresso Gilda"
**Implementata.** `src/components/GuildProgressCard.jsx` montata in `Dashboard.jsx` (sopra DailyQuests). 8 data-testid + link `/achievements`.

### 13. Guida aggiornata (7 sezioni)
- §9b. Classi e statistiche (Fase 1, già live)
- §10. Statistiche (esistente, completata)
- §34. Equipaggiamento per classe (NUOVA Fase 4)
- §35. XP e statistica primaria (NUOVA)
- §36. Drop materiali in spedizione (NUOVA)
- §37. Livello Gilda (NUOVA)
- §38. Imprese di Gilda (NUOVA)

### 14. Backend tests count finale
**97 passed, 1 skipped** in 3.89s (R13a + R13b + R13c + R14 + R15p2 + R15p3).

### 15. Frontend tests / lint / build
- Lint Achievements/GuildProgressCard/Guide/R15Sections: 0 errors, 1 warning non-bloccante.
- Build: `Compiled successfully!` ripetuto in `frontend.out.log`.

### 16. E2E tester result cumulativo (Fase 1+2+3)
- Fase 1: 12/12 PASS (post-fix EN→IT).
- Fase 2: 6/6 + 3 evidence script (hardblock 400, xp_debuff 3-tier, Monte Carlo 5000).
- Fase 3: 7/7 PASS.

### 17. OpenAPI path count
- Pre-R15: ~143 path.
- Post-R15: **146 path** (delta +3: `/api/achievements/{catalog,progress,summary}`).

### 18. PII sweep finale
0 leak su tutti i nuovi endpoint (catalog, summary, progress, adventurer-classes, items, expeditions/last-completed): no `@orbus.test`, no `$oid`, no `password_hash`, no `owner_user_id`.

### 19. localStorage/token sweep
0 occorrenze di `localStorage` in `Achievements.jsx`, `GuildProgressCard.jsx`, `R15GuideSections.jsx`, `ExpeditionReport.jsx`. Auth via cookie + axios Bearer.

### 20. NO hard delete
Conferma: `grep -rn "deleteOne\|delete_one" app/scripts/round15_*.py` → solo `equipped_items.delete_one` (riassegnazione, item è già stato spostato in `inventory_items` con quantity++ prima). Inventory conservation count invariato.

### 21. NO cleanup leaderboard
R14 `is_test_artifact + is_archived_pre_launch` filter rimasto attivo in `leaderboard/multi_category.py:*` e `leaderboard/seasonal.py:*`. Verifica live: `GET /api/leaderboard?category=peak_power&limit=50` → 0 entry archiviate, 0 score=0.

### 22. NO P2W / premium boost
Reward whitelist hard-coded `{xp_points, xp_points_title, xp_points_badge, xp_points_frame}` in `app/achievements/engine.py` e validator nel seed script. Zero menzioni di Stripe / acquisti / IAP nel codice Round 15. Guild Level non sblocca potere, drop, boost economici, vantaggi PvP/LB.

### 23. NO deploy production
Tutto preview. Nessun comando di deploy eseguito, nessuna mutazione su database prod.

### 24. Rischi residui (lista trasparente)
- **WARN (semantico, non bloccante)**: `/api/achievements/summary` espone `xp_for_next_level` nested sotto `progress` invece che top-level. Funzionalmente equivalente, UI già usa il campo nested.
- **WARN (UI cosmesi)**: `/admin/game-health` mostra 7 sezioni (6 cards + 1 utility "Riattiva gilda archiviata") — semanticamente OK, intenzionale.
- **Hook coverage**: l'engine ha hook su 5 trigger event (guild_created, adventurer_recruited, item_equipped, dungeon_completed, raid_completed). Restano da agganciare quando i sistemi diventano stabili: `item_crafted`, `item_disenchanted`, `material_purchased`, `territory_upgraded`, `pvp_match_completed`, `season_league_reached`, `leaderboard_rank_reached`, `market_purchase`, `auction_sale`/`auction_purchase`, `consortium_joined`. Quando questi hook saranno aggiunti i relativi achievement (~30) inizieranno a progredire.
- **Mage threshold**: a Lv1 il Mage ha `intellect_base=10`. Il debuff può attivarsi solo se la stat è ≤ 9 (deficit ≥10%). Per altri build con base più alto la finestra si apre prima.

### 25. Come validare manualmente
Script di replay disponibili (tutti idempotenti, no side-effect production):
```bash
cd /app/backend && set -a && source .env && set +a

# Catalog seeds (110 achievement + class identity + item tags)
python3 -m app.scripts.round15_seed_class_identity
python3 -m app.scripts.round15_seed_item_tags
python3 -m app.scripts.round15_seed_achievements

# Legacy migration (no-op se già fatto)
python3 -m app.scripts.round15_legacy_unequip_incompatible --dry-run
python3 -m app.scripts.round15_legacy_unequip_incompatible

# Evidence script (verifica numerica + comportamentale)
python3 -m app.scripts.round15_phase2_evidence_hardblock_equip
python3 -m app.scripts.round15_phase2_evidence_xp_debuff
python3 -m app.scripts.round15_phase2_evidence_monte_carlo

# Pytest completo (atteso: 97 passed, 1 skipped)
pytest tests/backend_round13a_test.py tests/backend_round13b_seasonal_increment_test.py \
       tests/backend_round13c_market_test.py tests/backend_round14_test.py \
       tests/backend_round15_phase2_test.py tests/backend_round15_phase3_test.py --tb=line
```

UI walkthrough:
1. Login `tester@orbus.test` / `password123`.
2. Dashboard → vedi card "PROGRESSO GILDA" (Lv3, 300 XP, 25 pt).
3. Click "Vedi tutte le Imprese →" → pagina `/achievements`.
4. Verifica filtri "Tutti / In corso / Completati" e dropdown categoria.
5. Naviga `/guide` → scroll al TOC, click §34 / §35 / §36 / §37 / §38.
6. Apri qualsiasi expedition completata → vedi sezioni "OGGETTI TROVATI" + "MATERIALI TROVATI" separate.

---

## Verdict
**Round 15 chiudibile DEFINITIVAMENTE: SI** ✅
