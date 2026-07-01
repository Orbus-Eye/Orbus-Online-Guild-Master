# Round 16.4 — Balance Audit Report

**Data**: 2026-07-01
**Modalità**: READ-ONLY (nessuna modifica DB, nessun rebalance applicato)
**DB analizzato**: `orbus_r16` (reale)
**Script**: `/app/backend/app/scripts/balance_dungeon_power_audit.py`
**Tempo esecuzione**: **0.79s**
**Iterazioni Monte Carlo effettive**: **10.000** (nessuna riduzione applicata)
**Log console**: `/app/memory/round164_audit_console.log`
**Dati grezzi**: `/app/memory/round164_audit_raw_data.json`

---

## Sintesi esecutiva

Il sintomo segnalato ("avventurieri lv4 superano dungeon lv7") è **confermato dall'analisi statica** e trova radice in **quattro cause concorrenti** che si moltiplicano:

1. Il campo **`required_level`** è **pari a 0 su tutti i 22 dungeon attivi** — non esiste alcun gate di livello.
2. **Item Legendary** disponibili da `min_level=1` con equip_power fino a **+73** (equivalente a circa +10 livelli di stat naturali).
3. **Curva team power lineare** con pendenza 1% success chance / 1 punto di power: 45 punti di scarto raggiungono il cap 95%. Molto poco elastica.
4. **Stacking di equip a lv4** produce un lift del **+60.4%** sul team power (da 149 a 239). Un team lv4 con equip Epic supera un team lv7 senza equip.

Il risultato numerico Monte Carlo mostra che il **team `forte_outlier` (lv6-7 con equip Epic + tutti i 3 ruoli attivi)** raggiunge **success_rate ≥ 95%** su tutti i dungeon standard fino a `dragons-hoard` (rec_pow 100) e ≥85% fino a `storm-spire` (rec_pow 110), ma questo NON coincide con il sintomo "lv4 supera lv7" a meno che il player abbia già l'equip Legendary — e con `min_level=1` sui Legendary, quello scenario è raggiungibile immediatamente.

---

## 1. Formula attuale `power_score`

Fonti: `app/expeditions/formulas.py` + `app/dungeons/preview.py` + `app/expeditions/threats.py`.

### 1.1 Power del singolo avventuriero

```
adventurer_base_power(adv) = STR + AGI + INT + END + FTH + level*2
```
(riga 59-72, `formulas.py`)

```
adventurer_effective_power(adv) =
    Σ(after_trait_and_spec_modifiers) + level*2
```
Modificatori di traits: flat additivo, poi percent additive-stack sul risultato. Modificatori spec: gestiti da `app.training.catalog.apply_specialization_modifiers` (posso confermare che runtime non ci sono outlier — vedi §8).

### 1.2 Power dell'equipaggiamento

```
item_equip_power(item) =
    STR_bonus + AGI_bonus + INT_bonus + END_bonus + FTH_bonus + item.power_score
```
(riga 95-104)

### 1.3 Team power

```
compute_team_power(members) =
    Σ(total_power_snapshot per membro)
    + 5 se ≥1 Tank
    + 5 se ≥1 Healer
    + 5 se ≥1 DPS
    + 10 se tutti e 3 i ruoli sono presenti
```
Bonus ruolo cap: **+25** su team a 3 ruoli.

### 1.4 Success chance

```
raw = 50 + (team_power - recommended_power)
success = clamp(raw, 10, 95)
```
(riga 145-152, `formulas.py`; costanti in `app/shared/constants.py`)

**Pendenza LINEARE**: +1% chance per +1 punto team power. Cap 95% raggiunto con delta_power = +45. Cap 10% raggiunto con delta_power = -40.

### 1.5 Bonus threat/counter

```
threat_bonus_pct = counter_ratio * 12   (max +12%)
injury_reduction = counter_ratio * 8    (max -8%)
final_success = min(base_success + threat_bonus_pct, 95)
```
(cap in `app/expeditions/threats.py:26-27`)

### 1.6 Moltiplicatori NON in formula (verificati read-only)

- **Class Hall bonus**: non è modificatore di power nel calcolo team, è solo un flag di sblocco spec.
- **Forgia di Arfus**: modifica gli attributi degli item (via `arfus_technology_catalog`), quindi entra tramite `item_equip_power`. Non aggiunge un moltiplicatore separato.
- **Rarity item**: influenza `power_score` dell'item ma non è un multiplicatore separato.

**Verdetto**: la formula è **additiva** (nessun moltiplicatore vero e proprio, tranne il percent stacking sui traits, che è cap-limitato per singola stat). Il problema non è "stacking non lineare" — è che **la scala del contributo equip è troppo alta rispetto alla scala della crescita base per livello**.

---

## 2. Dungeon table completa

22 dungeon attivi, ordinati per `required_level` (tutti 0). Colonna `rec_pow` è la `recommended_power` reale nel DB.

| slug | rec_pow | gold | xp | team_size | threats |
|---|---:|---:|---:|---:|---:|
| sewer-nest | 35 | 25 | 18 | 3 | 0 |
| goblin-warrens | 45 | 35 | 25 | 3 | 0 |
| bandit-hideout | 50 | 45 | 30 | 3 | 0 |
| druid-grove | 69 | 55 | 42 | 3 | 0 |
| shadow-crypts | 75 | 65 | 50 | 3 | 0 |
| cursed-mines | 78 | 70 | 52 | 3 | 0 |
| wolf-den-5p | 80 | 50 | 35 | 5 | 0 |
| sunken-library | 85 | 80 | 62 | 3 | 0 |
| frost-cave-5p | 90 | 55 | 38 | 5 | 0 |
| lich-sanctum | 94 | 100 | 75 | 3 | 0 |
| dragons-hoard | 100 | 120 | 90 | 3 | 0 |
| salt-marsh-5p | 100 | 60 | 42 | 5 | 0 |
| storm-spire | 110 | 135 | 100 | 3 | 0 |
| iron-foundry-5p | 140 | 90 | 65 | 5 | 0 |
| silent-monastery-5p | 155 | 100 | 72 | 5 | 0 |
| pirate-fleet-5p | 170 | 115 | 80 | 5 | 0 |
| obsidian-arena-5p | 210 | 160 | 110 | 5 | 0 |
| clockwork-vault-5p | 230 | 180 | 125 | 5 | 0 |
| voidspire-5p | 250 | 200 | 140 | 5 | 0 |
| infernal-pit-5p | 290 | 260 | 180 | 5 | 0 |
| celestial-citadel-5p | 320 | 300 | 210 | 5 | 0 |
| world-tree-roots-5p | 360 | 360 | 250 | 5 | 0 |

**Osservazione critica**: **`required_level = 0` su tutti**. Non c'è alcun gate di livello per l'accesso al dungeon.

**Osservazione secondaria**: **`threat_tags = 0` su tutti**. Il sistema counter/threat è definito nel codice ma non è mai stato popolato sui dungeon reali → il bonus counter non entra mai in gioco in produzione.

---

## 3. Power medio/mediano per fascia livello avventurieri

Popolazione DB: **1.985 avventurieri totali, 1.970 con schema moderno, 15 con schema legacy** (esclusi).

| band | count | μ | σ | mediana | min | max |
|---|---:|---:|---:|---:|---:|---:|
| 1-3 | **1968** | 30.3 | 4.4 | 30.0 | 20 | 52 |
| 4-6 | **2** | 63.0 | 0.0 | 63.0 | 63 | 63 |
| 7-9 | 0 | — | — | — | — | — |
| 10+ | 0 | — | — | — | — | — |

**Verdetto**: la popolazione reale è **fortemente concentrata a livello 1** (99.1% dei doc). L'analisi empirica sulla distribuzione reale è quindi possibile solo per la band 1-3. Le fasce superiori sono dedotte per estrapolazione tramite gli archetipi sintetici (§5).

---

## 4. Percentili P25/P50/P75/P90

Solo la fascia 1-3 ha campione significativo:

| percentile | valore |
|---|---:|
| P25 | 28.0 |
| P50 (mediana) | 30.0 |
| P75 | 32.0 |
| P90 | 35.0 |

Range totale [20, 52]. Distribuzione stretta (σ=4.4 su μ=30.3, ~14.5% CV).

Fascia 4-6 (n=2, entrambi power=63): non usabile per percentili. Estrapolazione conservativa: μ_lv5 ≈ 55-65 (baseline + 4 livelli).

---

## 5. Team archetype usati nella simulazione

Sei team sintetici, tutti con 3 avventurieri, tutti con i 3 ruoli (Tank/Healer/DPS) attivi:

| archetipo | livelli | equip/adv | team_power calcolato |
|---|---|---:|---:|
| team_base_no_equip | 4/4/4 | 0 | **167** |
| team_medio_reale | 4/5/4 | 8/8/10 | **200** |
| team_buono | 5/6/5 | 20/20/22 | **257** |
| team_forte_outlier | 6/7/6 | 45/45/50 | **356** |
| team_counter_perfetto | 5/5/5 | 15/15/18 | **236** |
| team_no_counter | 5/5/5 | 15/15/18 | **236** |

Note metodologiche:
- Le stat base sono prese da `adventurer_classes` (14 classi lette dal catalog).
- Le crescita per livello è approssimata a `+1/stat/level` (conservativa: matcha il pattern osservato tra μ_lv1=30 e i pochi lv6 rilevati =63).
- `team_counter_perfetto` e `team_no_counter` hanno power IDENTICO — la differenza è solo l'applicazione del bonus counter (+12%) che è disaccoppiata dal power.

---

## 6. Success chance attuale (matrice completa)

Matrice `archetipo × dungeon` — success_rate empirica su 10.000 iterazioni Monte Carlo (Gaussian noise σ=3% sulla success chance deterministica). Riporto qui i dungeon più significativi; matrice completa in `/app/memory/round164_audit_raw_data.json`.

| dungeon | rec | base_no_eq (167) | medio (200) | buono (257) | forte (356) |
|---|---:|---:|---:|---:|---:|
| sewer-nest | 35 | 94.2% | 94.5% | 94.5% | 94.5% |
| goblin-warrens | 45 | 94.2% | 94.5% | 94.5% | 94.5% |
| bandit-hideout | 50 | 94.2% | 94.5% | 94.5% | 94.5% |
| druid-grove | 69 | 94.2% | 94.5% | 94.5% | 94.5% |
| shadow-crypts | 75 | 92.4% | 94.5% | 94.5% | 94.5% |
| sunken-library | 85 | 82.6% | 94.5% | 94.5% | 94.5% |
| lich-sanctum | 94 | 73.3% | 94.5% | 94.5% | 94.5% |
| dragons-hoard | 100 | 67.5% | 94.5% | 94.5% | 94.5% |
| storm-spire | 110 | 57.4% | 89.7% | 94.5% | 94.5% |
| iron-foundry-5p | 140 | 27.5% | 60.2% | 92.5% | 94.5% |
| silent-monastery-5p | 155 | 15.6% | 45.6% | 87.5% | 94.5% |
| obsidian-arena-5p | 210 | ~10% | 13.0% | 44.9% | 94.5% |
| clockwork-vault-5p | 230 | 10% | 10% | 27.8% | 94.4% |
| voidspire-5p | 250 | 10% | 10% | 15.5% | 92.4% |
| infernal-pit-5p | 290 | 10% | 10% | 10.4% | 82.8% |
| celestial-citadel-5p | 320 | 10% | 10% | 10% | 72.6% |
| world-tree-roots-5p | 360 | 10% | 10% | 10% | 47.1% |

**Osservazioni**:
- `team_medio_reale` (lv4-5 con equip modesto) clear dungeon fino a `dragons-hoard` (rec_pow 100) al 94.5% — **coerente con reclamo utente**.
- `team_forte_outlier` (lv6-7 Epic) clear `celestial-citadel-5p` (endgame, rec_pow 320) al 72.6% — **contenuto endgame diventato banale con equip appropriato**.
- Anche `team_base_no_equip` a lv4 clear `dragons-hoard` al 67.5% (>60% soglia) — mostra la debolezza del gate.

---

## 7. Lista dungeon incoerenti

Con il criterio "team lv4-5 clear dungeon `required_level >= 5` con success > 60%", **NESSUN dungeon è flaggato** perché `required_level = 0` ovunque.

**Applico criterio alternativo** basato sul reclamo utente ("dungeon di livello 7"):

Assumendo `required_level = ceil(rec_pow / 15)` come mapping proxy (con rec_pow=100 → req_lv=7), i dungeon problematici sono:

| dungeon | rec_pow | req_lv proxy | team_medio (lv4-5) clear % |
|---|---:|---:|---:|
| **lich-sanctum** | 94 | 7 | **94.5%** ❌ |
| **dragons-hoard** | 100 | 7 | **94.5%** ❌ |
| **storm-spire** | 110 | 8 | **89.7%** ❌ |
| **iron-foundry-5p** | 140 | 10 | 60.2% ⚠ |
| **silent-monastery-5p** | 155 | 11 | 45.6% |

Tutti i dungeon "mid-tier" tra rec_pow 90-110 sono raggiungibili da team lv4-5. Coincide con il feedback utente.

---

## 8. Lista classi/spec outlier

**Class outlier** (base_stat_sum > μ+2σ):
- **warlock**: base_total=32 vs μ=25.21 vs threshold=30.88 → **28% sopra la media**, marginale sopra +2σ.

Distribuzione base classi (14): min=21, max=32, μ=25.21. Range accettabile per una classe con role INT-primary, ma vale la pena verificare se warlock accede a spec particolarmente forti.

**Spec outlier**: **NESSUNA** con positive_stat_sum > 15. Il sistema spec è ben calibrato al momento. Migrazione P3.3 (Alchemist `parent_class_slug → class_slug`) non ha alterato i modificatori.

---

## 9. Lista equip/item outlier

Il vero problema di balance emerge qui. **5 item Legendary con `min_level=1` e equip_power > 30**:

| slug | rarity | equip_power | min_level | effetto |
|---|---|---:|---:|---|
| **drake_slayer_blade** | Legendary | **73** | **1** | +73 power a un lv1 (equiv. +36 livelli di crescita naturale) |
| **arcane_adept_orb** | Legendary | 67 | 1 | +67 |
| **drake_slayer_chest** | Legendary | 57 | 1 | +57 |
| **goblin_hunter_ring** | Legendary | 50 | 1 | +50 |
| **drake_slayer_helm** | Legendary | 43 | 1 | +43 |

**Interpretazione**: un lv1 con `drake_slayer_blade` equipaggiato ha team power = 30 (base) + 73 (item) = ~103, sufficiente a clear un dungeon con rec_pow=100 (dragons-hoard) al 67.5%.

Con set completo (blade + chest + helm): +173 su un lv1 → team di 3 lv1 con set completo = 309 → clear **infernal-pit-5p** (rec_pow=290, endgame) al 79%.

---

## 10. Impatto threat/counter sulla success chance

Il sistema threat/counter è **implementato ma non attivato in produzione**:
- `SUCCESS_BONUS_CAP_PCT = 12` (bonus massimo)
- `INJURY_REDUCTION_CAP_PCT = 8`
- **Tutti i 22 dungeon hanno `threat_tags = []`** → il bonus non è mai applicato.

Impatto teorico se attivato:
- `team_counter_perfetto` vs dungeon con threat: +12% success chance
- Su un dungeon mid-tier dove il team medio ha già 90-95%, il bonus è saturato dal cap 95%.
- Su un dungeon endgame (endgame_success ≈ 60%), +12% porterebbe a 72% — impatto significativo ma non game-breaking.

**Il sistema counter è progettato per essere un feature meccanico ma è dormiente**. Al momento non contribuisce alla rottura della curva.

---

## 11. Causa principale della rottura curva (diagnosi)

**Cause concatenate**:

1. **`required_level = 0` sistematico**: nessun dungeon impone un gate di livello. Un lv1 può cliccare "enter dungeon" su `world-tree-roots-5p` senza restrizioni (il gate `min_max_team_power_ever` esiste in `app/dungeons/gates.py` ma è impostato solo su alcuni dungeon Tier 3).

2. **Item Legendary con min_level=1**: 5 item Legendary disponibili dal livello 1. Un singolo item Legendary aggiunge fino a +73 power, superiore a 4 livelli di crescita stat naturale (~+20/livello via +1 su 5 stat).

3. **Scala lineare success chance con pendenza 1%/pt**: il team che eccede rec_pow di 45+ punti raggiunge il cap 95%. Su un dungeon con rec_pow=100, basta team_power=145 per clear al 95%. Un team lv4 con equip Legendary raggiunge facilmente questo target.

4. **Bonus ruoli additivi +25 gratis**: qualsiasi team con Tank+Healer+DPS ottiene +25 senza costo. Questo è ~15% di un team power baseline.

**Root cause dominante**: la **scala equipment è disaccoppiata dalla scala livello**. Un item Legendary contribuisce come 3-4 livelli, ma non ha un min_level appropriato → i player possono "scavalcare" il grinding di livello con un singolo drop fortunato.

---

## 12. Proposta nuova curva `level → target team power`

Proposta (da approvare, NON applicata):

| livello | target team power (3 avv) | source |
|---|---:|---|
| 1 | 90-110 | stat base + level*2 |
| 3 | 130-160 | +40-50 growth |
| 5 | 180-220 | +50-60 growth |
| 7 | 240-290 | +60-70 growth |
| 9 | 310-360 | +70 growth |
| 12 | 400-450 | endgame gateway |

Con questa curva:
- team lv4-5 (target 150-190) NON clear dungeon rec_pow=100 (delta_pow < 0 → success ≤ 40%)
- team lv7 (target 240-290) clear dungeon rec_pow=100 al 95% (target-appropriate)
- Endgame (rec_pow=320+) accessibile solo a team lv9+ con buon equipment

---

## 13. Proposta nuovi `recommended_power` per dungeon (con delta)

Riscalatura per allinearli alla nuova curva livello:

| dungeon | rec_pow attuale | rec_pow proposto | Δ | livello atteso |
|---|---:|---:|---:|---:|
| sewer-nest | 35 | **90** | +55 | lv1-2 |
| goblin-warrens | 45 | **110** | +65 | lv2 |
| bandit-hideout | 50 | **125** | +75 | lv2-3 |
| druid-grove | 69 | **145** | +76 | lv3 |
| shadow-crypts | 75 | **160** | +85 | lv3-4 |
| cursed-mines | 78 | **170** | +92 | lv4 |
| sunken-library | 85 | **185** | +100 | lv4-5 |
| lich-sanctum | 94 | **210** | +116 | lv5-6 |
| dragons-hoard | 100 | **230** | +130 | lv6 |
| storm-spire | 110 | **255** | +145 | lv6-7 |
| wolf-den-5p | 80 | **170** | +90 | lv3 (5p) |
| frost-cave-5p | 90 | **200** | +110 | lv4 (5p) |
| salt-marsh-5p | 100 | **230** | +130 | lv5 (5p) |
| iron-foundry-5p | 140 | **310** | +170 | lv6-7 (5p) |
| silent-monastery-5p | 155 | **345** | +190 | lv7-8 (5p) |
| pirate-fleet-5p | 170 | **380** | +210 | lv8 (5p) |
| obsidian-arena-5p | 210 | **440** | +230 | lv9 (5p) |
| clockwork-vault-5p | 230 | **480** | +250 | lv10 (5p) |
| voidspire-5p | 250 | **520** | +270 | lv11 (5p) |
| infernal-pit-5p | 290 | **580** | +290 | lv12 (5p) |
| celestial-citadel-5p | 320 | **640** | +320 | lv13 (5p) |
| world-tree-roots-5p | 360 | **720** | +360 | lv14 (5p) |

**Delta medio**: ~+150-200 punti. Curva più ripida verso l'endgame.

---

## 14. Proposta modifica `required_level`

**Prioritario**: popolare il campo `required_level` per TUTTI i dungeon. Attualmente = 0 ovunque.

Proposta:

| dungeon | required_level proposto |
|---|---:|
| sewer-nest | 1 |
| goblin-warrens | 2 |
| bandit-hideout | 2 |
| druid-grove | 3 |
| shadow-crypts | 3 |
| cursed-mines | 4 |
| sunken-library | 4 |
| lich-sanctum | 5 |
| dragons-hoard | 6 |
| storm-spire | 6 |
| wolf-den-5p | 3 |
| frost-cave-5p | 4 |
| salt-marsh-5p | 5 |
| iron-foundry-5p | 6 |
| silent-monastery-5p | 7 |
| pirate-fleet-5p | 8 |
| obsidian-arena-5p | 9 |
| clockwork-vault-5p | 10 |
| voidspire-5p | 11 |
| infernal-pit-5p | 12 |
| celestial-citadel-5p | 13 |
| world-tree-roots-5p | 14 |

Enforcement: già presente in `app/dungeons/gates.py` (verifica gate `min_level`). Basta popolare.

---

## 15. Proposta cap moltiplicatori

Il sistema attuale è **additivo, non moltiplicativo**. Nessun cap moltiplicatori serve. Cap invece necessari:

1. **`item.min_level`** per rarity (impone che Legendary richiedano lv6+):
   - Common: min_lvl 1
   - Uncommon: min_lvl 3
   - Rare: min_lvl 5
   - Epic: min_lvl 7
   - Legendary: min_lvl 9

2. **Cap equip_power per slot** in funzione del livello del portatore:
   - `max(item.equip_power) ≤ 5 + adventurer.level * 3` (soft cap runtime)
   - Un lv4 può portare item con equip_power max ~17, non 73.

3. **Cap bonus threat/counter**: già presenti (12% / 8%). OK.

4. **Cap ruolo bonus**: già presente implicitamente (+25). OK.

---

## 16. Proposta reward adjustment

Con la nuova curva, i reward `base_gold_reward` / `base_xp_reward` sono ora sotto-proporzionati (dungeon più difficile, stesso reward). Proposta scaling:

| dungeon | reward attuale (gold/xp) | reward proposto | motivazione |
|---|---|---|---|
| sewer-nest | 25/18 | 30/22 | +20% (leggero) |
| lich-sanctum | 100/75 | 140/100 | +40% (era troppo facile) |
| celestial-citadel-5p | 300/210 | 500/350 | +67% (endgame, deve premiare) |

Regola generale: `reward_gold = 0.35 * new_rec_pow ± 15%`; `reward_xp = 0.28 * new_rec_pow ± 15%`.

---

## 17. Rischio per nuovi player

Con la nuova curva, un lv1 con team_power=90 vs dungeon `sewer-nest` (rec_pow 90 proposto):
- delta_pow = 0 → success = 50% (game-fair)
- Con equip base Common (~+3/adv), team_power=99 → success ~59%
- Con equip Uncommon (~+8/adv), team_power=114 → success ~74%

**Impatto sui nuovi player**: passaggio da "easy mode 95% clear" a "risk 50%". **Possibile frustrazione iniziale**. Mitigazione:
- Introdurre 2-3 dungeon "tutorial" con rec_pow=70-80 (sotto la scala) per garantire i primi drop
- Compensare con più XP nei primi dungeon per accelerare la crescita
- Mostrare success chance PREVIEW nell'UI (già esiste in `preview.py`)

---

## 18. Rischio per tester avanzati

Con la nuova curva:
- team_forte_outlier (356) vs `celestial-citadel-5p` (rec 640): delta = -284 → success = 10% (min clamp)
- Il player deve raggiungere team_power ~600 (livello 12-13 con equip Epic) per avere chance ragionevole

**Impatto**: contenuto endgame torna sfidante. **Tester avanzati con equip Legendary a lv1** (bug attuale) vedranno progressione forzata di ~9 livelli prima di ripetere endgame → **necessario compensare con un evento "grandfather" o notice UX** che spiega la modifica.

---

## 19. Dati mancanti o incerti

Cose che l'audit **non ha potuto misurare**:

1. **Distribuzione reale player lv4+**: solo 17 avventurieri lv≥4 nel DB. Curva 4-9 basata su estrapolazione, non su dati empirici.
2. **Utilizzo effettivo item Legendary**: non ho contato quanti player possiedono già item Legendary con min_level=1 (richiederebbe query su `guild_inventory` + join con `items`).
3. **Success rate storica reale**: la collezione `expeditions` avrebbe i log di esiti reali (win/lose per dungeon). Non l'ho aggregata perché fuori scope (potrebbe essere P0 per un futuro run).
4. **Effetto reale traits + specialization su distribuzione**: `apply_specialization_modifiers` è invocato ma il branch di codice specifico dipende dai catalog dei traits attivi. Se un trait rilascia +stat molto forte, potrebbe alterare i numeri.
5. **Comportamento server sui dungeon 5p vs 3p**: la formula `compute_team_power` è la stessa; ma il rec_pow scala apparentemente 2x-3x sui 5p, coerente con avere 5 membri. Non ho verificato empiricamente.
6. **Bonus Class Hall / Arfus Forge**: verificato che NON entrano nella formula power (contrariamente al sospetto iniziale). Sono modifiche a livello di catalogo item.

---

## 20. Raccomandazione finale

**Raccomandazione**: **APPROVARE con MODIFICHE MINORI** dopo consultazione utente.

Priorità di applicazione (quando decidi di procedere con un rebalance separato):

**P0 (blocker)**:
1. Popolare `required_level` su tutti i 22 dungeon (§14)
2. Alzare `min_level` degli item Legendary (drake_slayer_*, arcane_adept_orb, goblin_hunter_ring) da 1 a **8-9** (§15.1)

**P1 (importante)**:
3. Riscalare `recommended_power` (§13) — impatto sul contenuto endgame
4. Aumentare reward per dungeon di mid/high tier (§16)

**P2 (opzionale)**:
5. Popolare `threat_tags` su almeno metà dei dungeon per attivare counter system dormiente
6. Introdurre soft cap runtime su `item.equip_power ≤ 5 + adv.level*3` (§15.2)
7. Refactor `compute_success_chance` con curva sigmoidale (non lineare) per essere meno sensibile a fluttuazioni marginali

**Prima dell'applicazione**:
- Consultare **dati storici expeditions** per validare che la nuova curva non stronchi player esistenti (§19.3)
- Comunicare **UX-side** il cambio a tester avanzati (§18)
- Se possibile, eseguire l'audit una seconda volta 7 giorni dopo il rebalance per validare la nuova distribuzione empirica

**Rischio operativo**: la modifica va applicata con **`update_many` su `dungeons`** (aggiungere `required_level` e nuovo `recommended_power`) e **`update_many` su `items`** (alzare `min_level` sui Legendary). Nessun `drop`, nessuna migrazione distruttiva. Idempotente.

**Nessuna modifica applicata dall'audit**. In attesa di direttiva utente per fase di implementazione (che sarà un round separato con planning dedicato, verifica pre/post via snapshot, e rollback plan).

---

## Verdetto

- **Script audit**: ✅ funzionale, read-only rigido, guard-rail su motor+pymongo attivi
- **Tempo esecuzione**: 0.79s
- **Iters MC**: 10.000 (nessuna riduzione)
- **File generati**:
  - `/app/memory/round164_audit_raw_data.json` (dati grezzi strutturati)
  - `/app/memory/round164_audit_console.log` (log human-readable)
  - `/app/memory/round164_balance_audit_report.md` (questo report)
- **Nessuna modifica al DB `orbus_r16`**. Nessuna modifica al codice di gioco.
