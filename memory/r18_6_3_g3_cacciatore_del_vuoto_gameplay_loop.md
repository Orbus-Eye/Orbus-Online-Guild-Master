# R18.6.3 · Gate 3 · GAMEPLAY_LOOP · Cacciatore del Vuoto

**Locked (UTC)**: 2026-07-08T18:15:00Z · **Regime**: DOCUMENTAL ONLY · Gate 3 SOLO gameplay loop · NO resource numeric (G4) · NO damage coefficient (G5) · NO affix (G5) · NO Gate 4 auto-start · NO modifica R18.5/R18.6/R18.6.1/R18.6.2/G1/G2 (all LOCKED).

**Input from G1+G2**: main_stat=**Intelligenza** (soft cap 100) · armor cuoio+stoffa · weapon focus+pugnale+balestra · scaling Focus ALTO · Balestra MEDIO-ALTO · Pugnale RIDOTTO · focus max 1 · balestra 2H blocca off_hand · class_proficiency=`cacciatore_del_vuoto` (lowercase snake_case).

---

## Sezione 1 · Fantasy Gameplay Centrale

Il Cacciatore del Vuoto è un caster-ranged anti-incorporei che caccia ciò che non ha peso. Il suo mestiere è marchiare ciò che non dovrebbe esistere, drenarne l'essenza in Frammenti di Onirade, e scaricare quei Frammenti in un colpo definitivo (dispel di area o annullamento di boss summon). Non è un mago che scaglia esplosioni · non è un cacciatore fisico che insegue prede · è un anti-arcano di precisione che identifica, marca, drena e chiude. La fantasy è quella del ricercatore-cacciatore che porta luce nella nebbia del Faro Rovesciato, non con la spada, ma con focus, dardo arcano e pugnale rituale.

## Sezione 2 · Ruolo PvE

- **Primary role**: DPS anti-arcano · specializzazione dispel/anti-summon
- **Secondary role**: Utility (silenziamento summon · annullamento boss summon · rivelazione incorporei · debuff via Marchi)
- **Team position**: Ranged-mid range · si tiene distante dai melee heavy · vicino ai target incorporei/summon
- **Encounter priority**: target incorporeo > summon nemico > caster arcano > melee generico
- **Not tank / Not healer**: ✅

## Sezione 3 · Flusso Single-Target (loop 4-step)

| # | Phase | Action |
|:--:|---|---|
| 1 | **Identify** | Individuare target incorporeo/summon nel campo · priorità target (incorporeo > summon > caster > melee) |
| 2 | **Mark** | Applicare Marchio del Vuoto (dispel-over-time + silenziamento summon) · focus canaliza il Marchio |
| 3 | **Drain** | Colpire target marchiato con focus/balestra/pugnale · ogni colpo genera Frammenti di Onirade · accumulo verso il cap encounter |
| 4 | **Payoff** | Spendere Frammenti per Payoff: dispel di area (3F) o annullamento boss summon (5F) |

**Optimal weapon**: focus (Int ALTO) · massimizza applicazione Marchio e Drain · **Secondary**: balestra (se target ranged/inaccessibile in melee)

## Sezione 4 · Flusso Multi-Target

Contro più target incorporei/summon simultanei · Cacciatore del Vuoto NON è AoE caster puro · gestisce Marchi multipli e sceglie priorità

- Step 1: Marchiare 1 target principale (highest-value: boss summon > summon minore > incorporeo > caster)
- Step 2: Se soglie Int permettono (design gate futuro), applicare Marchio secondario
- Step 3: Drenare bersaglio con più HP marchiato · accumulare Frammenti
- Step 4: Payoff dispel area 3F: colpisce zona con più target marchiati · massimizza valore Frammenti spesi

**No infinite AoE**: Cacciatore del Vuoto NON ha AoE illimitato · Payoff area = 3 Frammenti (encounter-local cap 5) · una-tantum per encounter
**Cap reference**: cap Frammenti 5 (V-Q4 LOCKED) · Int NON aumenta cap

## Sezione 5 · Apertura Encounter

Design layer only · rotation base concettuale · sequenze numeriche NON progettate in G3

- Turn 1: Identify target primario · applicare Marchio del Vuoto (focus main_hand)
- Turn 2-3: Drain con focus (colpi generano 1F ciascuno · +1F soglia Int se ≥60 · design gate futuro)
- Turn 4-5: continuare Drain · accumulare verso cap 5F
- Turn 6+: decidere Payoff (3F dispel area vs 5F annullamento boss summon) in base al contesto encounter

**Target priority**: incorporeo · summon boss · summon minore · caster · melee (in ordine)

## Sezione 6-9 · Mantenimento/Drain/Payoff

### Mark maintenance
- Refresh: Marchio si riapplica sopra un Marchio esistente sullo stesso target · durata reset · NO overlap stacking (evita farm cheese)
- Overlap: 1 Marchio per target · anti-cheese
- Anti-waste: reapply Marchio troppo presto = spreco casting time · troppo tardi = Drain interrotto · skill window
- Max Marchi concept: cap iniziale 3 (G1 · design gate futuro finalizza soglie Int per +1 marchio a Int 50, Int 90)

### Drain windows
- When to drain: target marchiato attivo · Frammenti sotto cap 5 · encounter in corso · payoff non ancora deciso
- When to conserve: target boss in fase critica · Payoff imminente (accumulare 5F per annullamento) · switch target imminente (Frammenti persi se encounter cambia? design gate 4)
- Priority: focus > balestra > pugnale (in base a scaling Int)

### Payoff decision
- **3F dispel area**: dispel di area · potenza scala Int (G1) · raggio scala Int · quando: gruppo di summon/incorporei · encounter multi-target · Payoff efficiente
- **5F annullamento boss summon**: annullamento boss summon · chance successo scala Int fino soft cap 100 (G1) · quando: boss encounter con summon evocata · single high-value target · Payoff decisivo
- **Trade-off**: 3F = maggiore utility area · più flessibilità · 5F = kill-lock su boss summon · più decisivo ma costoso
- **One-time per encounter** ✅ · **No double payoff** ✅

## Sezione 10-13 · Behavior vs Targets

- **vs Summons** (primary kit target): Cacciatore del Vuoto è progettato PRIMA di tutto contro summon nemici · Marchio silenzia summon · Payoff annulla summon boss · uptime: alto (summon frequenti in encounter dungeon/raid Onirade-themed)
- **vs Incorporei** (primary kit target): Incorporei (spettri, riflessi ostili, ombre del Vuoto) sono target ideale · Marchio + Drain particolarmente efficaci · uptime: alto (incorporei frequenti in encounter Onirade-themed · anche in altri dungeon)
- **vs Boss**: Boss senza summon: Vuoto usa Marchio + Drain + Payoff 3F area (utility) o 5F single-target (se boss è Vuoto-themed)
  - Boss con summons: Marchio sul summon boss primario · Payoff 5F annullamento decisivo · utility massima
  - Boss incorporeo: boss incorporeo = target ideale · Marchi + Drain + Payoff = kill-lock parziale
- **No special targets**: Encounter senza incorporei/summon → Cacciatore del Vuoto in ruolo DEGRADATO ma FUNZIONALE · focus colpisce target generico · Marchi applicati a caster/melee ma con efficacia ridotta (design gate futuro) · Frammenti generati più lentamente

## Sezione 13 · Weapon Role in Loop

- **Focus**: PRIMARIA main_hand · applicazione Marchio · Drain principale · Payoff channeling · quando: quasi sempre · standard rotation · max 1 focus (PD-Q1 LOCK) · no dual-focus
- **Balestra**: RANGED ARCANA · 2H · applicazione Marchio a distanza · Drain ranged · quando: target inaccessibile in melee · encounter ranged-focused · switch da focus quando serve distanza · 2H · blocca off_hand · switch da focus+pugnale a balestra 2H costa 1 turno concettuale (design gate futuro)
- **Pugnale**: RITUALE/opportunistica off_hand · chiude rituali · Payoff ravvicinato · quando: in melee opportunistico · rituale post-Marchio · off_hand con focus main · off_hand default · main secondaria in build alternative (PD-Q1 loadout Pugnale+Focus inversione futura)

**Rotation switch**: player può switchare weapon durante encounter · design gate 4/5 valuterà cooldown switch

## Sezione 14-15 · Mobilità e Rischio/Posizionamento

- **Mobility**: MEDIA-BASSA · Cacciatore del Vuoto NON è agile fisico (CdM/Rogue) · richiede posizionamento pensato · movimento tra fasi encounter · non teleport, non dash
- **Positioning**: ranged mid-range · vicino a target incorporei/summon ma fuori da AoE nemiche · Faro Rovesciato = ambiente con visibilità limitata (design gate futuro considera penalità/bonus terreno)
- **No teleport · no dash** ✅
- **Armor fragility**: cuoio+stoffa · low armor · fragile burst · richiede awareness
- **Anti-brainless**: player NON può ignorare posizionamento · encounter difficili puniscono cattivo posizionamento

## Sezione 16-17 · Failure States + Recovery

**Failure states**:
- **mark_lost**: Marchio scade prima di Drain sufficiente · Frammenti non generati · loop interrotto
- **fragments_wasted**: Payoff attivato senza target ottimale · effetto sub-ottimale · encounter loss
- **drain_interrupted**: target eliminato da altro DPS prima che Vuoto completi Drain · Frammenti persi (se encounter cambia · design gate 4)
- **payoff_off_target**: Payoff 3F area senza target multiple · Payoff 5F annullamento su summon non-boss · risorse sprecate

**Recovery loop**:
- **mark_lost_recovery**: riapplicare Marchio · costo casting time · loop ritorna a Drain fase
- **fragments_wasted_recovery**: no full recovery in-encounter · attendere Payoff reset a fine encounter · design accetta cost of learning
- **drain_interrupted_recovery**: switch target · nuovo Marchio · accumulare Frammenti da capo
- **payoff_off_target_recovery**: impossibile · Payoff one-time · learning experience per encounter successivi

## Sezione 18-19 · Skill Floor + Ceiling

- **Skill floor**: loop 4-step Identify → Mark → Drain → Payoff è COMPRENSIBILE al nuovo player · player nuovo può eseguire loop base con focus + Marchio + Drain lineare + Payoff 3F area quando comodo
- **Tutorial**: safe-mode trial (Faro Rovesciato) insegna: identificazione target · Marchio base · distraction resistance
- **Skill ceiling**: rotation ottimale · target prioritization avanzata · Payoff timing decisivo · switch weapon dinamico · Marchio management multi-target
- **High skill reward**: player esperto massimizza Frammenti · usa 5F Payoff su boss summon in fase critica · gestisce Marchi multipli in raid
- **No infinite ceiling**: soft cap Int 100 e Frammenti cap 5 limitano cheese esperto · anti-power-creep

## Sezione 20-22 · Differenziazione

- **vs Mago**: Vuoto = Mark-based drain-payoff (accumulo → burst decisivo) · Mago = burst caster AoE elemental (spell puro · no accumulo). Ruoli DPS distinti · non competition-ready sugli stessi encounter (Mago meglio in AoE puro · Vuoto meglio in anti-summon/incorporei).
- **vs Cacciatore di Mostri**: Vuoto = anti-arcano ranged/rituale (Int · caccia incorporei/summon) · CdM = anti-fisico ranged/melee agile (Dex · caccia bestie fisiche). Zero overlap target · complementari in raid.
- **vs Paladino**: Vuoto = DPS anti-Vuoto (offensivo) · Paladino = Healer/Support sacro (difensivo/curativo). Ruoli opposti · coesistono in raid (Paladino cura, Vuoto elimina summon).

## Sezione 23-25 · Anti-Power-Creep + Anti-Stall + Party/Raid

**Anti-power-creep**:
- **payoff_cap_5f**: Payoff hard cap 5 Frammenti (V-Q4 LOCKED) · Int NON aumenta cap
- **marchi_max_3_plus_2**: cap iniziale 3 · +1 a soglia Int 50 · +1 a soglia Int 90 · max 5 marchi simultanei · design gate futuro finalizza soglie
- **scaling_soft_cap_int_100**: linear-flattening oltre Int 100 · diminishing returns · anti-scaling infinito (G1 SD-Q1 LOCK)
- **no_overrides_from_legendary**: Legendary ILVL=60 (non +60 Int) · Legendary offre utility_unique senza overrides scaling design (G1 semantic correction)
- **no_premium_boost**: anti-P2W · can_be_sold_for_real_money=false 1500/1500 (R18.5 lockato) · nessuna eccezione Vuoto

**Anti-stall**: Encounter senza summon/incorporei non blocca il Cacciatore del Vuoto · loop degradato ma non nullo (behavior_no_special_targets) · focus + Marchio ridotto + Drain lento · sostiene partecipazione encounter · no empty combat

**Party/Raid**:
- Team 3p: Vuoto in team 3p con Paladino (heal) + Guerriero/CdM (tank/DPS fisico) · Vuoto copre anti-arcano · sinergia forte in dungeon Onirade-themed
- Team 5p: Vuoto DPS anti-summon in raid 5p · sinergia con Mago (Vuoto elimina summon, Mago fa burst target rimanenti) · Paladino cura · Guerriero tank
- Synergy: Paladino heal · Mago burst target · CdM anti-fisico · Vuoto anti-arcano · quattro ruoli distinti

## Sezione 26-28 · Marchi/Frammenti/Payoff Conceptual Interaction

**⚠️ NO NUMERI FINALI in G3** · Gate 4 finalizzerà.

### Marchi (concept)
- Marchio del Vuoto = dispel-over-time + silenziamento summon · applicato via focus/balestra
- Duration/silence: scala con Int
- Max: 3 base · +1 a Int 50 · +1 a Int 90 · max 5 (design gate futuro finalizza soglie)
- Gate 4 finalizza: durata precisa in secondi/turni, tick damage numerico, silence duration numerico, resistance check formula

### Frammenti (concept)
- Frammenti di Onirade generati on-hit su target marchiato · encounter-local · cap 5 · reset fine dungeon/raid/prova
- Generation concept: 1 Frammento per colpo su marchiato · +1 bonus soglia Int (Int ≥ 60 · design gate 4) · +1 dispel summon · +2 annullamento boss summon (bonus NON scala con Int)
- Scope: encounter-local · non trasferibile · non mana alternativo · non valuta · non crafting · non premium (V-Q4 LOCKED)
- Gate 4 finalizza: generazione numerica esatta, consumo numerico esatto, cap scaling per progressione classe, reset trigger boundaries

### Payoff (concept)
- Payoff = spesa Frammenti per effetto decisivo · 3F dispel area · 5F annullamento boss summon
- Trade-off: 3F più flessibile ma meno decisivo · 5F più decisivo ma costoso
- Scaling Int: raggio dispel area scala Int · chance successo annullamento scala Int fino soft cap 100 (G1)
- Gate 4-5 finalizza: raggio dispel numerico, chance successo percentuale formula, duration effetto post-dispel, interaction con boss summon HP threshold

## Sezione 29 · Readiness Checklist R-04

- **Item ID**: R-04
- **Check**: gameplay loop base (identify → act → payoff → cooldown) definito
- **Status**: COMPLETED ✅
  - `loop_4_step_defined`: True
  - `single_target_flow_documented`: True
  - `multi_target_flow_documented`: True
  - `opening_rotation_concept`: True
  - `mark_maintenance_designed`: True
  - `drain_windows_designed`: True
  - `payoff_decision_designed`: True
  - `behavior_vs_targets_documented`: True
  - `failure_states_and_recovery_documented`: True
  - `skill_floor_and_ceiling_documented`: True
  - `differentiation_matrix_locked`: True
  - `anti_power_creep_documented`: True
  - `anti_stall_documented`: True
  - `party_raid_compatibility_documented`: True
  - `no_numbers_finalization_in_gate_3`: True

## Sezione 30 · Risk Register (12 rischi GL-R1..GL-R12)

| ID | Rischio | Severity | Status |
|:--:|---|:--:|:--:|
| **GL-R1** | Loop 4-step percepito come 'lento' rispetto a burst caster Mago | MEDIUM | DESIGNED |
| **GL-R2** | Encounter no-summon/no-incorporei rende classe underpowered | MEDIUM | DESIGNED |
| **GL-R3** | Player abbandona Marchi in favore di Drain diretto (skip fase Mark) | MEDIUM | DESIGNED |
| **GL-R4** | Marchio multipli tracking troppo complesso per player casuale | MEDIUM | TRACKED to G6 |
| **GL-R5** | Payoff one-time per encounter frustra player in encounter lunghi | LOW-MEDIUM | TRACKED |
| **GL-R6** | Switch weapon dinamico durante encounter troppo micro per player casuale | MEDIUM | DESIGNED |
| **GL-R7** | Balestra 2H blocca off_hand · confusione player abituati a dual-wield | LOW-MEDIUM | DOCUMENTED |
| **GL-R8** | Overlap gameplay con Cacciatore di Mostri (entrambi 'cacciatori') | LOW | ENFORCED |
| **GL-R9** | Anti-P2W confuso con anti-difficoltà · player pensa gioco troppo grindy | LOW | DESIGNED |
| **GL-R10** | Gate 4 RESOURCE_MECHANIC finalizzerà numeri divergenti da concept G3 | MEDIUM | DESIGNED |
| **GL-R11** | Progressive Discovery Legendary P1-P4 (HOLD) può introdurre meccaniche che rompono loop G3 | LOW-MEDIUM | TRACKED PG1 |
| **GL-R12** | Bridge legacy warlock (R18.3f handling) potrebbe importare gameplay warlock che confligge con Vuoto design | LOW | DESIGNED |

## Sezione 31 · PM Open Questions (GL-Q1..GL-Q6)

- **GL-Q1** · *Marchi multipli cap: 3+1 a Int 50 +1 a Int 90 (max 5) confermato o alternative?*
  - a) confermo 3+1@50+1@90=5
  - b) 2+1@60+1@100=4 (più conservative)
  - c) 3+2@70=5 (soglia singola più alta)
- **GL-Q2** · *Drain interrotto (target eliminato da altro DPS) · Frammenti persi o preservati?*
  - a) Frammenti persi (design cost of encounter chaos)
  - b) Frammenti preservati (skill floor più accessibile)
  - c) 50% preservati (compromesso)
- **GL-Q3** · *Loop degradato no-summon: Marchio applicabile a caster/melee con efficacia ridotta · quanto ridotta?*
  - a) 50% efficacia (loop degradato ma competitivo)
  - b) 25% efficacia (design punitivo · forza player a scegliere encounter Vuoto-friendly)
  - c) 0% (Marchio non applicabile · fallback su balestra ranged puro)
- **GL-Q4** · *Switch weapon durante encounter · cooldown o istantaneo?*
  - a) istantaneo (skill ceiling alto · micro-management)
  - b) cooldown breve (es. 2 turni concettuali)
  - c) cooldown medio (es. 5 turni · switch strategico)
- **GL-Q5** · *Payoff reset fine encounter · Frammenti conservati tra encounter dungeon multipli o reset?*
  - a) reset a fine encounter (V-Q4 LOCK · design attuale)
  - b) preserved tra encounter stesso dungeon (skill floor più accessibile)
  - c) reset a fine dungeon (compromesso)
- **GL-Q6** · *Encounter design (post-Gate 3): dungeon Onirade dovrebbero avere summon/incorporei prevalenti per Vuoto o mix bilanciato?*
  - a) prevalenti (Vuoto specialista Onirade-themed)
  - b) mix bilanciato (Vuoto viable ovunque · no specialization forzata)
  - c) design encounter-per-encounter (gate futuro encounter design)

## Sezione 32 · GO/HOLD Recommendation Gate 4 RESOURCE_MECHANIC

- **Gate 3 status**: COMPLETED · pending PM review + risposte GL-Q1..GL-Q6
- **Gate 4 status**: 🔒 HOLD · attende PM ACK Gate 3 + GO esplicito Gate 4
- **Gate 4 input from G3**: loop 4-step + Marchi/Frammenti/Payoff conceptual interactions + max marchi cap concept + generation/consumption concept → input per RESOURCE_MECHANIC numeric finalization
- **Gate 4 scope preview**: Frammenti di Onirade: generazione numerica esatta · consumo numerico · cap scaling · reset trigger boundaries · Marchi durata secondi/turni · tick damage · silence duration · resistance check formula · Payoff numeric · SOLO resource · NO damage weapon coefficient (Gate 5)

---

## 🛑 STOP before Gate 4 RESOURCE_MECHANIC

**Non procedere a Gate 4 senza nuovo GO PM.**

Attendo PM review Gate 3 + risposte a **GL-Q1..GL-Q6**. Nessun auto-start · nessuna modifica R18.5/R18.6/R18.6.1/R18.6.2/G1/G2 (tutti LOCKED).
