# Round 16.5 P0 — Balance Gates & Legendary Level (DRY-RUN)

**Data**: 2026-07-01 20:01:39
**Modalità**: `--dry-run` (nessuna modifica applicata al DB `orbus_r16`)
**Tempo esecuzione**: 0.098s
**Script**: `/app/backend/app/scripts/round165_balance_p0_gates_and_legendary_levels.py`

---

## Riepilogo

- **Dungeon totali analizzati**: 22
- **Dungeon con modifica proposta**: **22**
- **Legendary items totali analizzati**: 5
- **Legendary con modifica proposta**: **5**
- **Unresolved** (non toccati): **0**
- **Epic scannati (informativo, no modifica)**: 23

---

## Tabella A — `required_level` dungeon

Legenda bucket: `tutorial` (lv 1-2), `early` (lv 3-4), `mid` (lv 5-7), `high` (lv 8+). Il suffisso `*` indica `story_catchup` (contenuto narrativo bypassabile a basso livello, valutato caso per caso).

| slug | nome | tier | rec_pow | gold | xp | team | req_lvl attuale | req_lvl proposto | Δ | bucket | motivazione |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| `sewer-nest` | Nido nelle Fogne | 1 | 35 | 25 | 18 | 3 | 0 | **1** | +1 | tutorial | Difficoltà 1, rec_pow 35 (lowest), team 3p, tema 'baseline'. Primo dungeon dell'onboarding player. |
| `goblin-warrens` | Tane dei Goblin | 1 | 45 | 35 | 25 | 3 | 0 | **2** | +2 | tutorial | Difficoltà 1, rec_pow 45, team 3p, tema 'baseline'. Secondo dungeon tutorial, gap +1 su sewer-nest. |
| `bandit-hideout` | Covo dei Banditi | 1 | 50 | 45 | 30 | 3 | 0 | **2** | +2 | tutorial | Difficoltà 1, rec_pow 50, team 3p, tema 'baseline'. Ultimo tutorial 3p prima del salto early. |
| `druid-grove` | Bosco dei Druidi Corrotti | 2 | 69 | 55 | 42 | 3 | 0 | **3** | +3 | early | Difficoltà 2, rec_pow 69, team 3p, tema 'nature'. Primo early: gap +1 su tutorial, coerente con crescita naturale. |
| `shadow-crypts` | Cripte d'Ombra | 2 | 75 | 65 | 50 | 3 | 0 | **3** | +3 | early | Difficoltà 2, rec_pow 75, team 3p, tema 'void_undead'. Early, stesso livello del druid-grove per parità narrativa. |
| `cursed-mines` | Miniere Maledette | 2 | 78 | 70 | 52 | 3 | 0 | **4** | +4 | early | Difficoltà 2, rec_pow 78, team 3p, tema 'arcane'. Early avanzato, ponte verso mid tier. |
| `wolf-den-5p` | Tana dei Lupi | 1 | 80 | 50 | 35 | 5 | 0 | **3** | +3 | early* | Difficoltà 1, rec_pow 80, team 5p, tema 'nature'. Primo co-op 5p: rec_pow più alto assorbito dal group size, livello richiesto allineato all'early solo. |
| `sunken-library` | Biblioteca Sommersa | 2 | 85 | 80 | 62 | 3 | 0 | **4** | +4 | early | Difficoltà 2, rec_pow 85, team 3p, tema 'memory'. Early avanzato, gap allineato con cursed-mines. |
| `frost-cave-5p` | Caverna del Gelo | 1 | 90 | 55 | 38 | 5 | 0 | **4** | +4 | early* | Difficoltà 1, rec_pow 90, team 5p, tema 'nature'. Co-op early avanzato, gap +1 su wolf-den. |
| `lich-sanctum` | Santuario del Lich | 3 | 94 | 100 | 75 | 3 | 0 | **5** | +5 | mid | Difficoltà 3, rec_pow 94, team 3p, tema 'void_undead'. Primo mid tier 3p, sblocca contenuto epic. |
| `dragons-hoard` | Tesoro del Drago | 3 | 100 | 120 | 90 | 3 | 0 | **6** | +6 | mid | Difficoltà 3, rec_pow 100, team 3p, tema 'arcane'. Mid centrale 3p, richiede team con equip Rare consolidato. |
| `salt-marsh-5p` | Palude Salata | 1 | 100 | 60 | 42 | 5 | 0 | **5** | +5 | early* | Difficoltà 1, rec_pow 100, team 5p, tema 'memory'. Co-op ponte verso mid, gate leggermente più stretto per content_family memory (contenuto narrativo). |
| `storm-spire` | Guglia della Tempesta | 3 | 110 | 135 | 100 | 3 | 0 | **6** | +6 | mid | Difficoltà 3, rec_pow 110, team 3p, tema 'arcane'. Top mid 3p, ultimo dungeon della main line 3-player. |
| `iron-foundry-5p` | Fonderia di Ferro | 2 | 140 | 90 | 65 | 5 | 0 | **6** | +6 | mid | Difficoltà 2, rec_pow 140, team 5p, tema 'arcane'. Primo mid 5p, allineato a dragons-hoard 3p per parità. |
| `silent-monastery-5p` | Monastero del Silenzio | 2 | 155 | 100 | 72 | 5 | 0 | **7** | +7 | mid | Difficoltà 2, rec_pow 155, team 5p, tema 'memory'. Mid 5p, contenuto narrativo, +1 su iron-foundry. |
| `pirate-fleet-5p` | Flotta dei Corsari | 2 | 170 | 115 | 80 | 5 | 0 | **8** | +8 | high | Difficoltà 2, rec_pow 170, team 5p, tema 'baseline'. Top mid / soglia high, prima esperienza di 'grande scala'. |
| `obsidian-arena-5p` | Arena d'Ossidiana | 3 | 210 | 160 | 110 | 5 | 0 | **9** | +9 | high | Difficoltà 3, rec_pow 210, team 5p, tema 'arcane'. Primo high tier 5p, richiede team con equip Epic consolidato. |
| `clockwork-vault-5p` | Camera degli Ingranaggi | 3 | 230 | 180 | 125 | 5 | 0 | **10** | +10 | high | Difficoltà 3, rec_pow 230, team 5p, tema 'arcane'. High tier, salto vero rispetto obsidian per delta rec_pow +20. |
| `voidspire-5p` | Pinnacolo del Vuoto | 3 | 250 | 200 | 140 | 5 | 0 | **11** | +11 | high | Difficoltà 3, rec_pow 250, team 5p, tema 'void_undead'. Top high, ultimo prima dell'endgame. |
| `infernal-pit-5p` | Fossa Infernale | 4 | 290 | 260 | 180 | 5 | 0 | **12** | +12 | high | Difficoltà 4, rec_pow 290, team 5p, tema 'arcane'. Primo endgame, gate 12 come minimum viable ma richiede equip Legendary in pratica. |
| `celestial-citadel-5p` | Cittadella Celeste | 4 | 320 | 300 | 210 | 5 | 0 | **13** | +13 | high | Difficoltà 4, rec_pow 320, team 5p, tema 'divine'. Endgame narrative peak, gate +1 su infernal-pit. |
| `world-tree-roots-5p` | Radici dell'Albero del Mondo | 4 | 360 | 360 | 250 | 5 | 0 | **14** | +14 | high | Difficoltà 4, rec_pow 360, team 5p, tema 'nature'. Ultimo endgame, gate 14 come cap del contenuto attuale. |

**Note metodologiche**:
- Il mapping è derivato dall'ordine crescente di `recommended_power`, incrociato con `difficulty` e `required_team_size` (3p vs 5p).
- I dungeon 5p introduttivi (wolf-den-5p, frost-cave-5p, salt-marsh-5p) hanno `required_level` più basso del `recommended_power` suggerirebbe perché il rec_pow è assorbito dalla dimensione del team (5 avv → più power totale disponibile). Sono marcati `story_catchup` per chiarezza.
- Nessun dungeon ha `difficulty` = 0 o `recommended_power` = 0, quindi tutti sono classificabili.

---

## Tabella B — `min_level` Legendary items

| slug | nome | rarity | equip_power | min_lvl attuale | min_lvl proposto | Δ | motivazione |
|---|---|---|---:|---:|---:|---:|---|
| `arcane_adept_orb` | Arcane Adept Orb | Legendary | 67 | 1 | **9** | +8 | Legendary con equip_power=67 ≥ 60 (outlier top-tier del range Legendary): min_level 9. |
| `drake_slayer_blade` | Drake Slayer Blade | Legendary | 73 | 1 | **9** | +8 | Legendary con equip_power=73 ≥ 60 (outlier top-tier del range Legendary): min_level 9. |
| `drake_slayer_chest` | Drake Slayer Cuirass | Legendary | 57 | 1 | **8** | +7 | Legendary con equip_power=57 < 60: min_level baseline 8. |
| `drake_slayer_helm` | Drake Slayer Helm | Legendary | 43 | 1 | **8** | +7 | Legendary con equip_power=43 < 60: min_level baseline 8. |
| `goblin_hunter_ring` | Goblin Hunter Ring | Legendary | 50 | 1 | **8** | +7 | Legendary con equip_power=50 < 60: min_level baseline 8. |

**Regola applicata**:
- Legendary con `equip_power < 60` → `min_level = 8` (baseline)
- Legendary con `equip_power ≥ 60` → `min_level = 9` (outlier top-tier)
- Soglia `60` scelta in modo CONSERVATIVO rispetto al top-40% matematico (che sarebbe 55). Motivazione: solo gli item chiaramente outlier vengono spinti a 9; il resto resta a 8 per non essere troppo aggressivi.

---

## Unresolved (guard-rail: NON modificati)

Nessuno.


---

## Epic outlier scan (informativo, no modifica in R16.5 P0)

Scannati **23** item Epic. Range `equip_power` osservato: 10-14.

Nessun Epic supera la soglia di outlier (`equip_power ≥ 25`). Sono tutti entro il range atteso Epic [10-14]. **Nessuna modifica proposta sugli Epic in questo round P0.**

Il campo `min_level` sugli Epic è attualmente non impostato (default 1 implicito). Un round P1 potrebbe voler impostare `min_level = 5-7` per gli Epic, ma richiede analisi separata (fuori scope R16.5 P0).

---

## Cosa NON viene toccato (ricordato esplicitamente)

- ❌ `recommended_power` (dungeon)
- ❌ `base_gold_reward`, `base_xp_reward` (dungeon)
- ❌ `threat_tags`, `counter_tags` (dungeon)
- ❌ `equip_power`, `rarity`, `strength_bonus`, `agility_bonus`, ecc. (items)
- ❌ Prezzi, drop, crafting, ricette
- ❌ Formula `compute_success_chance` o qualsiasi altra formula
- ❌ Sistema PvP, Stalla, economia, tutti gli altri sistemi

---

## Prossimi passi

1. **Approvazione utente** su Tabella A + Tabella B → richiesta esplicita prima di STEP 2.
2. **STEP 2** (se approvato): esecuzione `--apply` con:
   - Snapshot pre-change (`/app/memory/round165_p0_prechange_snapshot.json`)
   - Applicazione `update_one` per ogni riga proposta
   - Test post-apply (verifica idempotenza + guard-rail)
   - Audit rapido R16.4 rieseguito per validare che la nuova curva sia effettivamente più coerente
   - Aggiornamento §19 del report R16.4 con dati mancanti disponibili post-fix
   - Report finale `/app/memory/round165_p0_apply_report.md`
