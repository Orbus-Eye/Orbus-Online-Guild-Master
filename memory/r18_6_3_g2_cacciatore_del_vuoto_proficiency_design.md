# R18.6.3 · Gate 2 · PROFICIENCY_DESIGN · Cacciatore del Vuoto

**Pilot**: Cacciatore del Vuoto (Wave 1 · #1) · **Hall**: `hall_cacciatore_del_vuoto` · **Locked at (UTC)**: 2026-07-08T17:45:00Z

**Authority**: PM Orchestrator — G2 PROFICIENCY_DESIGN GO esplicito post-G1 ACK

**Regime**: **DOCUMENTAL ONLY** · Gate 2 SOLO proficiency · NO gameplay loop (G3) · NO resource (G4) · NO equip base (G5) · **NO Gate 3 auto-start** · NO code · NO DB · NO Registry v3 · NO nuovi item · NO class unlock · NO Hall activation · NO modifica R18.5/R18.6/R18.6.1/R18.6.2/G1 (all LOCKED).

**Input from G1 (locked reference)**: main_stat=**Intelligenza** · soft cap 100 linear-flattening · priority Int→Cos→Dex · damage profile Focus ALTO · Balestra MEDIO-ALTO · Pugnale RIDOTTO · **Legendary ILVL = 60** (NON +60 Int) · bridge warlock→cacciatore_del_vuoto (mapped_design_only · R18.3f handling).

---

## Sezione 1 · Executive Summary

Gate 2 PROFICIENCY_DESIGN definisce le whitelist obbligatorie di armor e weapon per la classe Cacciatore del Vuoto e le regole di eligibility associate. **Armor**: cuoio + stoffa (entrambe Int-focus, no doppia identità stat). **Weapon**: focus (PRIMARIA, scaling Int ALTO) · balestra (RANGED ARCANA, scaling Int MEDIO-ALTO) · pugnale (RITUALE/opportunistica, scaling Int RIDOTTO). **Lanterna** = RESERVED FUTURE (no unlock, no item, no registry entry). Esclusi: maglia · piastre · arco · spada · bastone · tomo · martello · reliquia. Il gate non progetta gameplay loop, resource, o equip base (deferiti a Gate 3-5).

## Sezione 2 · Armor Whitelist Definitiva

**Allowed**: `cuoio` + `stoffa`

**Rationale**:
- **Cuoio**: mobility narrativa nel Faro Rovesciato (accesso via barca, movimento tra riflessi) · consistente con hall lore 'si caccia ciò che non ha peso' · Int-focus enforced (no Dex-cuoio Rogue-style)
- **Stoffa**: canalizzazione arcana per Marchi/dispel · condivisa con Mago ma con identità diversa (Vuoto anti-arcano, Mago caster puro) · Int-focus enforced

**No dual stat identity**: Entrambi armor DEVONO privilegiare Intelligenza · NO cuoio Dex-focused (Rogue/CdM style) · NO stoffa Wis-focused
**Coverage**: cuoio + stoffa copre tutti gli slot armor (head/chest/legs/feet/hands/wrist/waist · off-hand quando applicabile · back)

## Sezione 3 · Weapon Whitelist Definitiva

**Allowed**: `focus` · `pugnale` · `balestra`

**Rationale**:
- **Focus**: weapon PRIMARIA arcana · scaling Int ALTO (canalizzazione/controllo) · main-hand principale
- **Pugnale**: weapon RITUALE/opportunistica · scaling Int RIDOTTO (rituale/payoff ravvicinato) · main-hand secondaria o off-hand
- **Balestra**: weapon RANGED ARCANA · scaling Int MEDIO-ALTO (applicazione precisa Marchi a distanza) · NON weapon fisica Ranger/Rogue

**No scaling alternative stat**: TUTTI e 3 scalano su Intelligenza · NO Dex scaling per pugnale/balestra · NO Str scaling
**PM verbatim**: Balestra Vuoto = strumento canalizzazione arcana a distanza · NON weapon Ranger/Rogue · nessun requisito Dex nascosto

## Sezione 4 · Compatibilità Stoffa (Int-focus)

canalizzazione arcana per Marchi/dispel · condivisa con Mago ma con identità diversa (Vuoto anti-arcano, Mago caster puro) · Int-focus enforced

## Sezione 5 · Compatibilità Cuoio (Int-focus)

mobility narrativa nel Faro Rovesciato (accesso via barca, movimento tra riflessi) · consistente con hall lore 'si caccia ciò che non ha peso' · Int-focus enforced (no Dex-cuoio Rogue-style)

## Sezione 6 · Esclusione Maglia/Piastre

**Armor excluded**: `maglia` · `piastre`

**Rationale**: maglia/piastre incoerenti con identità caster-arcana · incompatibili con canalizzazione focus/balestra · overlap indesiderato con Guerriero (piastre) e CdM (maglia)

**Impatto**: Vuoto non compete per maglia (CdM) né piastre (Guerriero) · zero overlap gear heavy.

## Sezione 7-9 · Identità Weapon

### Focus
- **Role**: **PRIMARIA**
- **Stat scaling**: Int ALTO
- **Narrative identity**: canalizzatore arcano · epicentro dei Marchi del Vuoto · strumento principale del Cacciatore
- **Typical slot**: main_hand
- **Material hint (design gate futuro)**: cristallo scuro · specchio piccolo · reliquiario rovesciato (design gate futuro)

### Balestra
- **Role**: **RANGED ARCANA**
- **Stat scaling**: Int MEDIO-ALTO
- **Narrative identity**: applicazione precisa Marchi a distanza · dardi come veicoli arcani · NON strumento fisico agile
- **Typical slot**: main_hand (ranged) o off-hand (accessorio) · design regola main-hand/off-hand sotto
- **Material hint (design gate futuro)**: legno annerito · corda argentea · dardo con rune (design gate futuro)

### Pugnale
- **Role**: **RITUALE / OPPORTUNISTICA**
- **Stat scaling**: Int RIDOTTO
- **Narrative identity**: chiude i rituali · applica payoff ravvicinato · momento intimo di caccia · NON specializzazione primaria melee
- **Typical slot**: off_hand o main_hand secondaria
- **Material hint (design gate futuro)**: lama nera opaca · impugnatura in stoffa · rune leggere (design gate futuro)

## Sezione 10 · Regole Main-Hand / Off-Hand

- **Main-hand primary**: focus (raccomandato · Int ALTO scaling)
- **Main-hand alternatives**: balestra (ranged), pugnale (opzione ravvicinata)
- **Off-hand primary**: pugnale (ritual/payoff)
- **Off-hand alternative**: focus variant secondaria (dual-cast concept futuro)
- **Dual-wield policy**: dual-wield NON obbligatorio · design layer per player choice · focus main-hand + pugnale off-hand = combo canonica raccomandata · focus main-hand + focus off-hand = dual-cast (design gate futuro se emerge meccanica)
- **No shield**: scudo NON in weapon whitelist Vuoto · off-hand è arma o accessorio, mai scudo
- **Ranged/melee swap**: player può switchare tra balestra ranged e focus/pugnale melee · design gate GAMEPLAY_LOOP futuro valuta cooldown swap

## Sezione 11 · Compatibilità Slot

| Slot | Armor compatible | Weapon compatible |
|---|---|---|
| `main_hand` | N/A | focus · balestra · pugnale |
| `off_hand` | N/A | pugnale · focus (variant secondaria) |
| `chest` | cuoio · stoffa | N/A |
| `legs` | cuoio · stoffa | N/A |
| `head` | cuoio · stoffa | N/A |
| `hands` | cuoio · stoffa | N/A |
| `feet` | cuoio · stoffa | N/A |
| `wrist` | cuoio · stoffa | N/A |
| `waist` | cuoio · stoffa | N/A |
| `neck` | universal (accessory) | N/A |
| `ring` | universal (accessory) | N/A |
| `accessory` | universal | N/A |
| `back` | cuoio · stoffa | N/A |

## Sezione 12 · Equip Eligibility Matrix (sample)

| Slot | Item family | class_proficiency | Equipable | Reason |
|---|---|---|:--:|---|
| main_hand | focus | CacciatoreDelVuoto (or VoidHunter · gate PROFICIENCY_DESIGN future decision) | ✅ | focus in weapon whitelist · Int scaling |
| main_hand | arco | CacciatoreDelVuoto | ❌ | locked_proficiency_weapon (C2 #7) · arco NOT in whitelist Vuoto |
| chest | armor_type=cuoio, main_stat_target=Intelligenza | CacciatoreDelVuoto | ✅ | cuoio in armor whitelist · Int-focus preservato |
| chest | armor_type=cuoio, main_stat_target=Destrezza | CacciatoreDelVuoto | ✅ | cuoio in whitelist · MA XP penalty tiered soft (main_stat != Int) · SD-Q5 policy globale |
| chest | armor_type=maglia | CacciatoreDelVuoto | ❌ | locked_proficiency_armor (C2 #6) · maglia NOT in whitelist Vuoto |
| chest | armor_type=piastre | CacciatoreDelVuoto | ❌ | locked_proficiency_armor (C2 #6) · piastre NOT in whitelist Vuoto |
| off_hand | pugnale | CacciatoreDelVuoto | ✅ | pugnale in weapon whitelist · off-hand allowed |
| off_hand | scudo | CacciatoreDelVuoto | ❌ | locked_proficiency_weapon · scudo NOT in whitelist · off-hand = arma o accessorio |
| main_hand | balestra | CacciatoreDelVuoto | ✅ | balestra in whitelist · Int scaling medio-alto |
| consumable | any | any | ✅ | universal_allowed (C2 #5) |
| material | any | any | ✅ | universal_allowed (C2 #5) |

## Sezione 13 · Lock-State Matrix Estensione (riuso 10 stati C2 · NO nuovi)

| C2 # | State | When (Vuoto-specific) |
|:--:|---|---|
| #3 | `#3 locked_recruit_unassigned` | Recluta senza classe assegnata · gear Vuoto specializzato bloccato · CTA Assegna Sala |
| #4 | `#4 locked_class_slug_null` | adventurer con class_proficiency=CacciatoreDelVuoto ma class_slug=null · bridge C5/R18.3f · warning UI |
| #5 | `#5 universal_allowed` | consumable/material/cosmetic · bypass proficiency · Vuoto può equipaggiare universal come qualsiasi altra classe |
| #6 | `#6 locked_proficiency_armor` | armor_type in {maglia, piastre} + class_proficiency=CacciatoreDelVuoto → blocca |
| #7 | `#7 locked_proficiency_weapon` | weapon_family in {arco, spada, bastone, tomo, martello, reliquia, ascia, scudo, lancia, arma_in_asta} + class_proficiency=CacciatoreDelVuoto → blocca |
| #8 | `#8 locked_level` | level < required_level · applica come per tutte le classi |
| #10 | `#10 equippable` | tutti i check passed · item Vuoto-compatible equipaggiabile |

**No new lock_state introduced** ✅
**XP penalty hook**: XP penalty tiered soft (SD-Q5) NON è un lock_state · è policy XP separata · applicata post-equip · potenziale badge UI 'main_stat_below_recommended' senza blocco

## Sezione 14 · Messaggi UI Italiano Canonical

- **block_armor_maglia_piastre**: **Armatura non compatibile** — Il Cacciatore del Vuoto non veste maglia né piastre. Preferisce cuoio o stoffa per non ostacolare la canalizzazione del Vuoto.
- **block_weapon_arco**: **Arma non compatibile** — L'arco è strumento del Cacciatore di Mostri. Il Cacciatore del Vuoto usa focus, balestra o pugnale.
- **block_weapon_bastone_tomo**: **Arma non compatibile** — Bastoni e tomi appartengono al Mago. Il Cacciatore del Vuoto canalizza con focus arcani e balestre di canalizzazione.
- **block_weapon_spada_ascia_martello_lancia**: **Arma non compatibile** — Le armi marziali pesanti sono estranee al Cacciatore del Vuoto. Preferisce strumenti di canalizzazione.
- **block_weapon_reliquia**: **Arma non compatibile** — Le reliquie appartengono al Paladino. Il Cacciatore del Vuoto cerca ciò che non ha peso, non ciò che pesa nella luce.
- **block_shield_off_hand**: **Off-hand non compatibile** — Il Cacciatore del Vuoto non impugna scudo. Preferisce un pugnale rituale o un focus secondario in off-hand.
- **warning_recruit_unassigned**: **Assegna una Sala di Classe** — Questo avventuriero è un Recluta senza classe. Portalo al Faro Rovesciato di Onirade per farne un Cacciatore del Vuoto.
- **warning_class_slug_null**: **Identità in aggiornamento** — Il sistema di identità è in fase di aggiornamento (bridge canonico). Puoi equipaggiare questo oggetto, ma alcune funzionalità saranno disponibili dopo la migrazione.
- **warning_main_stat_below_recommended**: **Statistica principale sotto la soglia raccomandata** — Questo Cacciatore del Vuoto trarrebbe più esperienza con equipaggiamento incentrato sull'Intelligenza. XP corrente ridotta (mai sotto 50%).

## Sezione 15 · Interazione `class_slug=null`

Se `adventurer.class_slug=null` (Recluta), l'avventuriero NON può equipaggiare gear Vuoto specializzato (armor cuoio/stoffa Int-focus · weapon focus/pugnale/balestra) tramite normale flusso equip.

- **Lock state**: `#3 locked_recruit_unassigned`
- **CTA**: Assegna Sala di Classe (Faro Rovesciato di Onirade)
- **No auto assignment** ✅ · **No bridge from warlock** ✅

## Sezione 16 · Interazione `recruit_unassigned`

- Lock state #3 preserved ✅
- Gear specialized equip: BLOCKED ✅
- Universal allowed: OK ✅
- Dismissal ammesso · Sell/transfer bloccato
- Cap per Gilda: 3 · Idle XP: 0%

## Sezione 17 · `lanterna` RESERVED Valuation

- **Status**: RESERVED FUTURE
- **Identity future**: candidate weapon family unica del Cacciatore del Vuoto · strumento di rivelazione + canalizzazione · alternativa/completamento al focus
- **Main/Off-hand candidate**: potenziale main-hand OR off-hand (design gate futuro decide)
- **Difference from focus**: canalizzazione arcana pura · Marchi + dispel + payoff vs rivelazione (illumina incorporei/nascosti) + canalizzazione secondaria · non replica focus
- **Requires Registry v3**: ✅
- **Risks new weapon type**:
  - Registry v3 required (nuovi item · nuovo weapon family in slot_canonical map)
  - class_proficiency validator update (C2 #7)
  - affix design dedicato (main_stat_target=Intelligenza · illumination-based utility)
  - possibile confusione player 'perché due weapon primarie?' · design gate valuterà se lanterna sostituisce focus o coesiste

**Operations forbidden now**: unlock ❌ · item_generation=0 · registry_entry=0 · implementation=0 · runtime NOT available · NOT in R18.5 catalog

**Conclusione**: Design layer only ora · valutare al gate EQUIP_DESIGN (G5) se lanterna diventa canonical weapon family o resta narrative-only. Nessuna decisione forzata in G2.

## Sezione 18 · Differenze da Mago

- **Shared armor**: ['stoffa']
- **Vuoto unique armor**: ['cuoio']
- **Shared weapon**: ['focus', 'pugnale']
- **Vuoto unique weapon**: ['balestra']
- **Mago unique weapon**: ['bastone', 'tomo']
- **Slot competition**: stoffa items condivisi · MA affix `main_stat_target=Intelligenza` uguale · possibile competizione item generico stoffa-Int · mitigazione: item Mago spesso avrà affix caster-burst (spell power/mana), item Vuoto affix dispel/mark efficacy (design gate EQUIP_DESIGN)
- **Focus shared, role diff**: focus è weapon condivisa · Int scaling condiviso · MA item focus può avere affix class-specific (Marchi effectiveness per Vuoto vs Spell burst per Mago) · design gate futuro
- **Pugnale shared, role diff**: Mago: pugnale opzione secondaria caster · Vuoto: pugnale ritual/payoff · same weapon, different role

## Sezione 19 · Differenze da Rogue (Ladro)

- **Shared armor**: ['cuoio']
- **Shared weapon**: ['pugnale']
- **Critical diff main_stat**: Rogue: Destrezza · Vuoto: Intelligenza · cuoio+pugnale Rogue è Dex-focused, Vuoto è Int-focused
- **Cuoio split**: cuoio con main_stat_target=Destrezza → Rogue/CdM primario · cuoio con main_stat_target=Intelligenza → Vuoto primario · SD-Q5 policy XP penalty enforce
- **Pugnale split**: pugnale scaling è determinato da class_proficiency · same item, different scaling behavior per class
- **Vuoto no Rogue weapons**: Vuoto NON usa spada (Rogue whitelist) né balestra Dex-style · balestra Vuoto è arcana

## Sezione 20 · Differenze da Ranger (Cacciatore di Mostri)

- **Shared armor**: ['cuoio']
- **Shared weapon**: ['balestra', 'pugnale']
- **Critical diff main_stat**: Ranger (Cacciatore di Mostri): Destrezza · Vuoto: Intelligenza
- **Balestra semantic split**: Ranger balestra = weapon fisica Dex (ranged agile) · Vuoto balestra = strumento canalizzazione arcana Int · same item family, opposite scaling
- **Cuoio split**: cuoio Ranger main_stat_target=Destrezza vs cuoio Vuoto main_stat_target=Intelligenza · split by affix
- **Vuoto no Ranger weapons**: Vuoto NON usa arco (Ranger primary) · NO lancia · NO spada
- **No maglia Vuoto**: Ranger cuoio+maglia · Vuoto cuoio+stoffa · maglia esclusivo Ranger
- **Narrative diff**: Ranger caccia bestie fisiche del bosco · Vuoto caccia incorporei/summon del Faro Rovesciato · zero overlap target

## Sezione 21 · Rischio Gear Sharing

**Summary**: Cuoio e pugnale condivisi con Rogue/Ranger · stoffa/focus condivisi con Mago · item generici potrebbero apparire compatibili con più classi

**Mitigations**:
1. class_proficiency è il primary discriminator · validator C2 #7 verifica esattamente questo
2. affix `main_stat_target` (già in Registry v2 schema C1 · 23 fields) discrimina ulteriormente · main_stat_target=Intelligenza favorisce Vuoto/Mago vs Destrezza favorisce Rogue/Ranger
3. gate EQUIP_DESIGN (G5) può introdurre affix class-specific · es. `mark_effectiveness` (Vuoto-only) · `spell_burst` (Mago-only) · design layer futuro
4. XP penalty tiered soft (SD-Q5) segnala al player 'questo item non è ottimale per la tua classe' senza bloccare

**No hard block**: item shared armor_type + weapon_family sono EQUIPABILI da più classi (se class_proficiency e whitelist match) · la stat scaling e XP penalty gestiscono il resto
**Residual risk**: MEDIUM · gestibile via mitigation stack · gate EQUIP_DESIGN + PLAYER_GUIDE completeranno UX

## Sezione 22 · Rischio Doppia Armor Proficiency

**Summary**: cuoio + stoffa doppia armor proficiency potrebbe creare 'due identità stat' se stoffa fosse Wis-focus e cuoio Dex-focus (come tradizionale MMO)

**PM verbatim mitigation**: V-Q2 PM LOCK: entrambi armor DEVONO privilegiare Intelligenza · NO doppia identità stat

**Enforcement affix**: affix `main_stat_target=Intelligenza` obbligatorio su tutti gli item armor Vuoto (cuoio + stoffa) · gate EQUIP_DESIGN (G5) enforcement
**No hybrid**: NO cuoio Dex-secondary hybrid · NO stoffa Wis-secondary hybrid · Int primary con Cos/Dex come secondary/tertiary via affix minor
**No dual build paths**: no build 'cuoio Vuoto' vs 'stoffa Vuoto' distinta · entrambi supportano lo stesso design
**Residual risk**: LOW · enforcement design + gate EQUIP_DESIGN

## Sezione 23 · Readiness Checklist R-02 + R-03

- **R-02** (armor_proficiency whitelist + rationale): **COMPLETED ✅**
  - whitelist: ['cuoio', 'stoffa']
  - exclusions: ['maglia', 'piastre']
- **R-03** (weapon_proficiency whitelist + RESERVED families flagged): **COMPLETED ✅**
  - whitelist: ['focus', 'pugnale', 'balestra']
  - RESERVED future: ['lanterna']

**Overall**: R-02 + R-03 COMPLETED · altre R-01 (G1 done) · R-04..R-13 PENDING gate successivi

## Sezione 24 · Risk Register (10 rischi PD-R1..PD-R10)

| ID | Rischio | Severity | Status |
|:--:|---|:--:|:--:|
| **PD-R1** | Cuoio Vuoto (Int-focus) confusion con cuoio Rogue/CdM (Dex-focus) | MEDIUM | DESIGNED |
| **PD-R2** | Stoffa Vuoto (Int-focus) competition con stoffa Mago | MEDIUM | DEFERRED to EQUIP_DESIGN |
| **PD-R3** | Focus shared weapon Mago/Vuoto genera 'stesso item stesso ruolo' feeling | MEDIUM | DEFERRED to EQUIP_DESIGN |
| **PD-R4** | Pugnale shared con Rogue crea overlap gameplay confuso | LOW-MEDIUM | DESIGNED |
| **PD-R5** | Balestra Vuoto confusa con balestra Ranger fisica | MEDIUM | DESIGNED |
| **PD-R6** | Dual armor proficiency (cuoio+stoffa) genera 'due identità stat' | LOW | ENFORCED |
| **PD-R7** | Player crede lanterna sia già weapon Vuoto (RESERVED confusion) | LOW | DOCUMENTED |
| **PD-R8** | Off-hand policy (pugnale/focus/no scudo) confusa dai player abituati a scudo off-hand | LOW | DOCUMENTED |
| **PD-R9** | Weapon whitelist 3-family (focus+pugnale+balestra) percepita come 'stretta' rispetto a Guerriero (6 weapon) | LOW | DESIGNED |
| **PD-R10** | Modifica accidentale R18.6.3-G1 (LOCKED) durante G2 writing | HIGH-BLOCK | ENFORCED |

## Sezione 25 · PM Open Questions + GO/HOLD Recommendation Gate 3

### 25.1 · PM Open Questions (PD-Q1..PD-Q6)

- **PD-Q1** · *Focus in off-hand (dual-cast concept) confermato come design gate futuro o rimuovere possibilità?*
  - a) confermo dual focus off-hand come opzione gate futuro (design layer)
  - b) rimuovere · off-hand solo pugnale
  - c) valutare con Gate 3 GAMEPLAY_LOOP
- **PD-Q2** · *Balestra Vuoto scaling Int MEDIO-ALTO conferma soglia numerica in Gate 3 o Gate 5?*
  - a) Gate 3 GAMEPLAY_LOOP (contesto gameplay)
  - b) Gate 5 EQUIP_DESIGN (contesto item stat)
  - c) sub-doc dedicato scaling numerico
- **PD-Q3** · *Lanterna RESERVED · timeline gate valutazione (Gate 5 EQUIP_DESIGN o sub-gate dedicato R18.6.LTN)?*
  - a) Gate 5 EQUIP_DESIGN (integrato)
  - b) sub-gate R18.6.LTN dedicato
  - c) documental-only forever · no future implementation
- **PD-Q4** · *Class_proficiency label finale: 'CacciatoreDelVuoto' vs 'VoidHunter' vs altro?*
  - a) CacciatoreDelVuoto (canonical IT · consistent con canonical_class_slug)
  - b) VoidHunter (English label · consistent con legacy Warrior/Rogue/etc)
  - c) proponi terza opzione (es. cacciatore_del_vuoto direct slug)
- **PD-Q5** · *UI tooltip lock reason: italiano puro (come da G2 copy) o hybrid con codici lock_state visibili per debug?*
  - a) italiano puro (player-facing)
  - b) italiano + tooltip debug per QA/PM
  - c) italiano + optional advanced info toggle
- **PD-Q6** · *Affix class-specific (mark_effectiveness · spell_burst · etc) · dispatch al gate EQUIP_DESIGN o sub-doc affix dedicato?*
  - a) integrato in Gate 5 EQUIP_DESIGN
  - b) sub-doc R18.6.AFX (affix system dedicato)
  - c) parte di Registry v3 dispatch

### 25.2 · GO/HOLD Gate 3

- **Gate 2 status**: COMPLETED · pending PM review + risposte PD-Q1..PD-Q6
- **Gate 3 status**: 🔒 HOLD · attende PM ACK Gate 2 + GO esplicito Gate 3
- **Gate 3 input from G2**: armor whitelist + weapon whitelist + slot compatibility + main_hand/off_hand rules + lock_states extension → input per GAMEPLAY_LOOP
- **Gate 3 scope preview**: loop 4-step (Identify → Mark → Drain → Payoff) · cooldown swap main/ranged · target priority · integration con Marchi + Frammenti pool (Gate 4 finalizza risorsa) · NO resource design output in G3

**Recommendation**:
- APPROVE Gate 2 PROFICIENCY_DESIGN (armor cuoio+stoffa · weapon focus/pugnale/balestra · lanterna RESERVED · exclusions locked · differentiation matrix vs Mago/Rogue/Ranger)
- HOLD Gate 3 GAMEPLAY_LOOP in attesa PM ACK
- Rispondere a PD-Q1..PD-Q6 in round dedicato prima di Gate 3 dispatch
- NO auto-transition · NO gate skip · NO parallel gate

---

## Governance Snapshot G2

| Voce | Stato |
|---|:--:|
| Documental only · Italian · sealed 6/6 · `lore_meta.py` invariato | ENFORCED ✅ |
| DB / code / migrations | 0 / 0 / 0 ✅ |
| R18.5 / R18.6 / R18.6.1 / R18.6.2 / G1 modification | 0 / 0 / 0 / 0 / 0 ✅ (all LOCKED) |
| Legacy bridge apply · Registry v3 dispatch | 0 · ❌ ✅ |
| Cacciatore del Vuoto live activation · Lanterna unlock | BLOCKED · BLOCKED ✅ |
| Gate 3/4/5 auto-start | BLOCKED ✅ |
| Gate isolation enforced (SOLO proficiency in G2) | ✅ |
| File deliverable G2 | 2 (.md + .json) · Sezioni: **25 / 25** ✅ |

---

## 🛑 STOP before Gate 3 GAMEPLAY_LOOP

**Non procedere a Gate 3 senza nuovo GO PM.**

Attendo PM review Gate 2 + risposte a **PD-Q1..PD-Q6** prima di dispatch Gate 3. Nessun auto-start · nessuna modifica R18.5/R18.6/R18.6.1/R18.6.2/G1 (tutti LOCKED).
