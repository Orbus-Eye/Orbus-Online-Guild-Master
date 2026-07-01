# Round 16.5 P0 — Balance Gates & Legendary Level (APPLY)

**Data**: 2026-07-01 20:26:27
**Modalità**: `--apply` (modifiche effettive al DB `orbus_r16`)
**Tempo esecuzione**: 0.102s
**Script**: `/app/backend/app/scripts/round165_balance_p0_gates_and_legendary_levels.py`

## Snapshot
- Path: `/app/memory/round165_p0_prechange_snapshot.json`
- SHA256: `28a1e085fd743cfb7ce407168bdc88961817a3ddd76239a4f12bbc62a89fc537`
- Size: 4814 bytes

## Diff Preview (audit trail)
- Path: `/app/memory/round165_p0_apply_preview.txt`

## Risultati
- Dungeon **modificati** (22), no-op (0)
- Legendary **modificati** (5), no-op (0)
- Whitelist violations: 0 (deve essere 0)
- Unresolved (non toccati): 0

## Tabella A — required_level dungeon (applicati)

| slug | nome | tier | rec_pow | gold | xp | team | req_lvl attuale | req_lvl proposto | Δ | bucket | motivazione |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| `sewer-nest` | Nido nelle Fogne | 1 | 35 | 25 | 18 | 3 | 1 | **1** | 0 | tutorial | Difficoltà 1, rec_pow 35 (lowest), team 3p, tema 'baseline'. Primo dungeon dell'onboarding player. |
| `goblin-warrens` | Tane dei Goblin | 1 | 45 | 35 | 25 | 3 | 2 | **2** | 0 | tutorial | Difficoltà 1, rec_pow 45, team 3p, tema 'baseline'. Secondo dungeon tutorial, gap +1 su sewer-nest. |
| `bandit-hideout` | Covo dei Banditi | 1 | 50 | 45 | 30 | 3 | 2 | **2** | 0 | tutorial | Difficoltà 1, rec_pow 50, team 3p, tema 'baseline'. Ultimo tutorial 3p prima del salto early. |
| `druid-grove` | Bosco dei Druidi Corrotti | 2 | 69 | 55 | 42 | 3 | 3 | **3** | 0 | early | Difficoltà 2, rec_pow 69, team 3p, tema 'nature'. Primo early: gap +1 su tutorial, coerente con crescita naturale. |
| `shadow-crypts` | Cripte d'Ombra | 2 | 75 | 65 | 50 | 3 | 3 | **3** | 0 | early | Difficoltà 2, rec_pow 75, team 3p, tema 'void_undead'. Early, stesso livello del druid-grove per parità narrativa. |
| `cursed-mines` | Miniere Maledette | 2 | 78 | 70 | 52 | 3 | 4 | **4** | 0 | early | Difficoltà 2, rec_pow 78, team 3p, tema 'arcane'. Early avanzato, ponte verso mid tier. |
| `wolf-den-5p` | Tana dei Lupi | 1 | 80 | 50 | 35 | 5 | 3 | **3** | 0 | early* | Difficoltà 1, rec_pow 80, team 5p, tema 'nature'. Primo co-op 5p: rec_pow più alto assorbito dal group size, livello richiesto allineato all'early solo. |
| `sunken-library` | Biblioteca Sommersa | 2 | 85 | 80 | 62 | 3 | 4 | **4** | 0 | early | Difficoltà 2, rec_pow 85, team 3p, tema 'memory'. Early avanzato, gap allineato con cursed-mines. |
| `frost-cave-5p` | Caverna del Gelo | 1 | 90 | 55 | 38 | 5 | 4 | **4** | 0 | early* | Difficoltà 1, rec_pow 90, team 5p, tema 'nature'. Co-op early avanzato, gap +1 su wolf-den. |
| `lich-sanctum` | Santuario del Lich | 3 | 94 | 100 | 75 | 3 | 5 | **5** | 0 | mid | Difficoltà 3, rec_pow 94, team 3p, tema 'void_undead'. Primo mid tier 3p, sblocca contenuto epic. |
| `dragons-hoard` | Tesoro del Drago | 3 | 100 | 120 | 90 | 3 | 6 | **6** | 0 | mid | Difficoltà 3, rec_pow 100, team 3p, tema 'arcane'. Mid centrale 3p, richiede team con equip Rare consolidato. |
| `salt-marsh-5p` | Palude Salata | 1 | 100 | 60 | 42 | 5 | 5 | **5** | 0 | early* | Difficoltà 1, rec_pow 100, team 5p, tema 'memory'. Co-op ponte verso mid, gate leggermente più stretto per content_family memory (contenuto narrativo). |
| `storm-spire` | Guglia della Tempesta | 3 | 110 | 135 | 100 | 3 | 6 | **6** | 0 | mid | Difficoltà 3, rec_pow 110, team 3p, tema 'arcane'. Top mid 3p, ultimo dungeon della main line 3-player. |
| `iron-foundry-5p` | Fonderia di Ferro | 2 | 140 | 90 | 65 | 5 | 6 | **6** | 0 | mid | Difficoltà 2, rec_pow 140, team 5p, tema 'arcane'. Primo mid 5p, allineato a dragons-hoard 3p per parità. |
| `silent-monastery-5p` | Monastero del Silenzio | 2 | 155 | 100 | 72 | 5 | 7 | **7** | 0 | mid | Difficoltà 2, rec_pow 155, team 5p, tema 'memory'. Mid 5p, contenuto narrativo, +1 su iron-foundry. |
| `pirate-fleet-5p` | Flotta dei Corsari | 2 | 170 | 115 | 80 | 5 | 8 | **8** | 0 | high | Difficoltà 2, rec_pow 170, team 5p, tema 'baseline'. Top mid / soglia high, prima esperienza di 'grande scala'. |
| `obsidian-arena-5p` | Arena d'Ossidiana | 3 | 210 | 160 | 110 | 5 | 9 | **9** | 0 | high | Difficoltà 3, rec_pow 210, team 5p, tema 'arcane'. Primo high tier 5p, richiede team con equip Epic consolidato. |
| `clockwork-vault-5p` | Camera degli Ingranaggi | 3 | 230 | 180 | 125 | 5 | 10 | **10** | 0 | high | Difficoltà 3, rec_pow 230, team 5p, tema 'arcane'. High tier, salto vero rispetto obsidian per delta rec_pow +20. |
| `voidspire-5p` | Pinnacolo del Vuoto | 3 | 250 | 200 | 140 | 5 | 11 | **11** | 0 | high | Difficoltà 3, rec_pow 250, team 5p, tema 'void_undead'. Top high, ultimo prima dell'endgame. |
| `infernal-pit-5p` | Fossa Infernale | 4 | 290 | 260 | 180 | 5 | 12 | **12** | 0 | high | Difficoltà 4, rec_pow 290, team 5p, tema 'arcane'. Primo endgame, gate 12 come minimum viable ma richiede equip Legendary in pratica. |
| `celestial-citadel-5p` | Cittadella Celeste | 4 | 320 | 300 | 210 | 5 | 13 | **13** | 0 | high | Difficoltà 4, rec_pow 320, team 5p, tema 'divine'. Endgame narrative peak, gate +1 su infernal-pit. |
| `world-tree-roots-5p` | Radici dell'Albero del Mondo | 4 | 360 | 360 | 250 | 5 | 14 | **14** | 0 | high | Difficoltà 4, rec_pow 360, team 5p, tema 'nature'. Ultimo endgame, gate 14 come cap del contenuto attuale. |

## Tabella B — min_level Legendary (applicati)

| slug | nome | rarity | equip_power | min_lvl attuale | min_lvl proposto | Δ | motivazione |
|---|---|---|---:|---:|---:|---:|---|
| `arcane_adept_orb` | Arcane Adept Orb | Legendary | 67 | 9 | **9** | 0 | Legendary con equip_power=67 ≥ 60 (outlier top-tier del range Legendary): min_level 9. |
| `drake_slayer_blade` | Drake Slayer Blade | Legendary | 73 | 9 | **9** | 0 | Legendary con equip_power=73 ≥ 60 (outlier top-tier del range Legendary): min_level 9. |
| `drake_slayer_chest` | Drake Slayer Cuirass | Legendary | 57 | 8 | **8** | 0 | Legendary con equip_power=57 < 60: min_level baseline 8. |
| `drake_slayer_helm` | Drake Slayer Helm | Legendary | 43 | 8 | **8** | 0 | Legendary con equip_power=43 < 60: min_level baseline 8. |
| `goblin_hunter_ring` | Goblin Hunter Ring | Legendary | 50 | 8 | **8** | 0 | Legendary con equip_power=50 < 60: min_level baseline 8. |
