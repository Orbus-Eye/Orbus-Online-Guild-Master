# R18.6.3-G4 RESOURCE_MECHANIC · Cacciatore del Vuoto

**Gate**: R18.6.3-G4 · **Scope**: RESOURCE_MECHANIC · **Class Pilot**: Cacciatore del Vuoto (`cacciatore_del_vuoto`)
**Generated**: 2026-07-08T19:15:00Z · **Status**: DRAFT · pending PM review
**Governance**: DOCUMENTAL ONLY · no code · no DB · no migrations · no Registry v3 · no drop tables · no loot
**Seals anchor**: `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`
**Predecessor gates LOCKED**: R18.5 · R18.6 · R18.6.1 · R18.6.2 · G1 · G2 · G3
**Successor gate**: R18.6.3-G5 EQUIP_DESIGN (HOLD · attende G4 CLOSED)
**Canonical validation**: PASS · zero non-canonical class references
**Terminology anchor**: `resource generation rate` · Frammenti NON sono loot (nessun uso di termini loot-related tipo `d.rop r.ate` · anti-drift guard)

---

## Sezione 1 · Identità della risorsa

- **Nome**: **Frammenti di Onirade**
- **Proprietario**: `cacciatore_del_vuoto` (class-exclusive)
- **Tipo**: class_resource
- **NON loot · NON inventory-persistent · NON tradeable · NON sellable · NON materiale · NON valuta**
- **Scope**: encounter-local
- **Lore**: frammenti di sostanza onirica arcana estratti da target marchiati durante il Drain · rappresentano il progresso rituale del Cacciatore contro l'anomalia
- **Chiarimento anti-drift**: Frammenti NON droppano · NON si vendono · NON persistono come currency

## Sezione 2 · Cap finale proposto

- **Cap proposto**: **5** · **REVIEW OUTCOME: VALIDATED**
- **Rationale**: (a) scelta reale tra Payoff 3F intermedio e Payoff 5F max · (b) evita accumulo cheese · (c) evita collasso opzioni su singolo Payoff · (d) coerente con G3 hard cap V-Q4 LOCK
- **Alternatives**:
  - cap 3 → REJECTED (collassa 3F e 5F)
  - cap 4 → REJECTED (gap troppo stretto)
  - cap 6 → REJECTED (stall + payoff frequency troppo diluita)
  - cap 7+ → REJECTED (burst potential eccessivo)
- **Cap indipendente da Int**: **CONFIRMED** · anti-power-creep · Int scala su generation/reliability/durata, non su containment

## Sezione 3 · Regole di generazione

- **Trigger primario**: colpo su target Marchiato
- **Base**: 1F per colpo (target marchiato · hit valido)
- **Unmarked target**: 0F (Drain funziona SOLO su target Marchiato · anti-cheese)
- **Int proc bonus scale**:

| Int Range | Proc chance +1F | Note |
|---|---|---|
| <30 | 0% | base 1F flat |
| 30-49 | 10% | +1F bonus proc → totale 2F sul colpo |
| 50-69 | 20% | +1F bonus |
| 70-89 | 30% | +1F bonus |
| 90-99 | 40% | +1F bonus |
| 100+ | 45% cap | soft cap linear-flattening · diminishing returns |

- **Max gen per hit**: 2F (base 1 + proc bonus 1)
- **Silenziamento gen bonus**: 0 (anti-double-dipping · silence = utility Marchio, non gen)
- **Critical hit gen bonus**: 0 (Frammenti = rituale, non danno)

## Sezione 4 · Regole di consumo

- **Payoff 3F cost**: 3 Frammenti (dispel area)
- **Payoff 5F cost**: 5 Frammenti (annullamento boss summon · banish incorporeo · self-buff fallback)
- **Consumo atomico e indivisibile**: nessun consumo parziale · anti-cheese frazionale · scelta netta 3F vs 5F
- **Consumo out-of-encounter**: vietato (scope encounter-local)

## Sezione 5 · Condizioni di reset

- end_of_encounter · end_of_dungeon_room · end_of_raid_phase · player_death · party_wipe · logout · disconnect
- **Cross-encounter persistence**: **NO**
- **Manual reset player**: NO
- **Manual reset admin**: YES (governance)

## Sezione 6-8 · Weapon generation matrix

| Weapon | Base gen | Int proc | Bonus | Gen/turn Int 60 (concept) |
|---|---|---|---|---|
| **focus** | 1F/hit | full scale | +1F channel bonus (max 2 canalizzazioni per encounter · anti-spam) | 1.0-1.4 |
| **balestra** | 1F/hit | full scale −0.05 (meno rituale) | no channel · no ranged bonus · 2H = opportunity cost (blocca off_hand) | 0.9-1.3 |
| **pugnale** | 1F/hit | full scale | +1F ritual close (ultimo hit prima Marchio expiry · una tantum per Marchio) | 0.8-1.2 |

- **Loadout focus+pugnale (default PD-Q1)**: 1.5-2.2 F/turno Int 60 combined
- **Loadout balestra 2H**: 0.9-1.3 F/turno Int 60 · opportunity cost accettato per ranged utility

## Sezione 9-13 · Target interactions

### 9 · Target Marchiato
- unica condizione per Drain to generate · base + proc + weapon bonuses

### 10 · Summon
- Marchio applicabile · **silenziamento anti-cast** 3 turni concettuali (impedisce ability · movement libero)
- gen su summon marchiato = 1F base · Payoff 5F effetto: **annullamento definitivo** (unsummon)
- **boss_summon_priority_flag**: TRUE

### 11 · Incorporei
- Marchio applicabile · **dispel-over-time** (3 tick su durata Marchio)
- gen su incorporeo marchiato = 1F base + 5% proc modifier (target rituale primario)
- Payoff 3F: dispel area · Payoff 5F: banish target incorporeo

### 12 · Boss
- Marchio applicabile · **stack cap 1** su boss
- **Dispel immunity parziale**: Marchio DoT ridotto 50% concept · silenziamento SOLO ability non-lethal · MAI enrage/hard-cast
- gen su boss = 1F base · **no proc bonus** (boss safeguard anti-farm) · Int bonus limitato +5% max
- **Payoff 5F su boss target**: MAI annullamento · fallback self-buff arcano (dispel proprio debuff · barriera arcana temp)

### 13 · No special targets (loop degradato)
- Marchio applicabile su target normali · gen 1F base · NO channel bonus · NO ritual close bonus
- **Fallback utility mode**: 3F Payoff = dispel debuff alleati · 5F Payoff = self-heal arcano concept (numeric in Gate 5)
- **Anti-stall LOCK**: loop sempre funzionale · gen ~50% ridotta ma non nulla

## Sezione 14 · Payoff frequency expected

| Encounter | Expected Payoffs | Typical choice |
|---|---|---|
| Breve 5-10 turn | 1 | 1x 3F o skip |
| Medio 15-25 turn | 1-2 | 1x 5F max OR 2x 3F |
| Boss lungo 30-50 turn | 2-3 | mix 3F/5F basato su fasi |
| Raid multi-encounter | 1-2 per encounter | reset tra encounter |

- **Threshold analysis 3F vs 5F**:
  - **3F dispel area**: utility · ROI alto se ≥2 alleati affetti da debuff arcani
  - **5F annullamento boss summon**: burst decisivo · ROI massimo se add-summon = threat critico
  - **Opportunity cost 5F**: preclude 2x 3F distribuiti (6F virtuali > cap 5 = trade-off vero)
  - **Decision matrix**: (a) debuff arcani su ≥2 alleati → 3F · (b) boss-summon critical → 5F · (c) encounter breve senza summon → skip · (d) mix on encounter lungo

## Sezione 15 · Payoff intermedio 3F (dispel area)

- **Cost**: 3F · **Cast**: 1 turno · **Cooldown**: 0 (re-castable appena Frammenti risalgono a 3)
- **Effetto primario**: dispel area · rimuove effetti arcani sospesi in AoE (raggio concept 3m · gate 5 finalizza)
- **Effetto fallback no_special_targets**: dispel debuff arcani su party
- **Int reliability**: 80% (Int<50) → 90% (50-79) → 95% (80-99) → 98% (100+)
- **Boss arcane effect leggendario**: immune a 3F · richiede 5F o mechanic dedicata

## Sezione 16 · Payoff massimo 5F (annullamento boss summon)

- **Cost**: 5F · **Cast**: 1 turno · **Cooldown**: 0 logico (rate-limited da fill cap 5)
- **Effetto primario**: annullamento boss summon · banish add-summon (unsummon permanente)
- **Effetto secondario incorporei**: banish target incorporeo single-target
- **Effetto fallback no_special_targets**: self-heal arcano (concept · numeric Gate 5)
- **Int nullification chance**: 80/90/95/98% scala Int
- **Boss immune ad annullamento diretto**: TRUE · 5F su boss = self-buff arcano (dispel debuff propri · barriera temp)
- **Add-summon boss extra resist**: −10% (Int 100+ = 88% effective su boss add-summon)

## Sezione 17 · Immediate vs stockpile decision

- **Immediate 3F**: debuff arcani party attivi · utility immediata · alleati in threat
- **Stockpile 5F**: boss add-summon phase noto · risparmio per fase critica · burst decisivo
- **Skip Payoff**: encounter breve senza summon · reset a fine encounter accettato · skill window: skip=risparmio ma spreco
- **Cheese prevention**: cap 5 hard · no overcap · no cross-encounter · no hoarding · skip = perdita netta

## Sezione 18 · Overcap handling

- **Hard cap**: 5 · overcap generation IGNORED
- **UI display**: `5/5` fisso · indicator `cap`
- **Tooltip**: "Frammenti al massimo · spendi un Payoff per continuare a generare"
- **Wasted counter**: non tracked · anti-anxiety design
- **Signal chiaro**: overcap = 'usa Payoff' · no punizione hidden

## Sezione 19 · Failure state

- **Marchio expiry wasted**: Frammenti fino a expiry preservati · reapply Marchio richiesto
- **Marchio overwritten early**: durata reset · no overlap stacking (anti-cheese)
- **Target death pre-Payoff**: Frammenti restano nel pool encounter · shift target
- **Payoff missed encounter end**: reset · Frammenti persi · skip = spreco
- **Cast interrupt on Payoff**: Frammenti NON spesi · pool preservato · retry dopo CC clear

## Sezione 20 · Recovery state

- **After Marchio expiry**: reapply focus cast 1 turno · Drain resume · pool preservato
- **After wipe/death**: reset totale · next encounter start-fresh
- **After Payoff wasted**: no recovery · reset porta pool 0 · lesson learned
- **After cast interrupt**: Frammenti preservati · retry appena CC clear · no cooldown extra

## Sezione 21 · Anti-stall

- Loop degradato ma funzionale in no-summon/no-incorporei encounter
- Min gen encounter medio ≥3F → soglia Payoff 3F sempre raggiungibile
- Boss Marchio immunity edge case impossibile per design (tutti boss marchiabili)
- Empty combat prevention: LOCK · loop always funzionale

## Sezione 22 · Anti-spam

- Marchio max attivi: 3 (base) · +1 a Int 50 · +1 a Int 90 · hard cap 5
- Marchio overlap stacking: FALSE
- Channel bonus focus max per encounter: 2
- Ritual close pugnale bonus: 1 per Marchio
- Proc bonus hard ceiling: 45% da Int 100+ (linear-flattening)
- No burst gen chain focus channel + ritual close consecutivi su stesso target

## Sezione 23 · Anti-burst

- Cap 5 hard · indipendente da Int
- Payoff 5F boss immune ad annullamento
- Payoff 5F cast 1 turno (non instant)
- No stockpile cross-encounter
- No burst chain 5F+3F immediato (5F consuma tutto)
- Boss add-summon priority flag → 5F prioritario su add-summon vs generic targets

## Sezione 24 · Interazione con Intelligenza (5 assi)

1. **Probability generation**: 0→10→20→30→40→45% cap · linear-flattening Int 100+
2. **Payoff reliability**: 80→90→95→98% (3F e 5F entrambi) · linear-flattening
3. **Marchio duration**: 3→4→5→6→7→8 turni base · +0.5 turn per 50 Int oltre 100 · hard cap 10
4. **Dispel efficacy**: rank comune-non_comune → raro → epico → leggendario (Int 100+ soft cap)
5. **Summon nullification chance**: 80→90→95→98% · boss add-summon extra −10% (88% effective Int 100+)

- **5 assi tutti linear-flattening oltre Int 100** · anti-power-creep coerente con G1 SD-Q1 LOCK
- **Cap Frammenti resta indipendente da Int** · anchor LOCK

## Sezione 25 · Soft cap Int 100 linear-flattening

- **Knee point**: Int 100
- **Post-knee slope**: ≈0.15-0.25x pre-knee slope (variable per axis)
- **Reference**: G1 SD-Q1 · R18.6.3-G1 CLOSED
- **Legendary ILVL semantic**: `Legendary ILVL = 60 (non +60 Int)` · utility_unique senza overrides scaling · G1 semantic correction preservata

## Sezione 26 · UI resource display concept

- **Widget**: counter/barrino segmentato · sotto barra HP · sopra weapon quickbar
- **Stati**: `0/5` (empty grigio) · `1-4/5` (parziale viola-arcano) · `3/5` (glow segmento 3 · Payoff pronto) · `5/5` (full pulse · cap) · overcap (`5/5` fisso `cap`) · cast (dimmed 1 turno)
- **No flying number spam** (anti-clutter)
- **Colorblind safe** (shape + tint)

## Sezione 27 · Tooltip italiani (player-facing · zero code)

| Contesto | Tooltip |
|---|---|
| Counter | "Frammenti di Onirade: {n}/5 · usa i Frammenti per attivare rituali del Vuoto" |
| At 3F | "Payoff pronto: dispel area (spesa 3 Frammenti)" |
| At 5F | "Payoff massimo pronto: annullamento evocazione (spesa 5 Frammenti)" |
| Cap | "Frammenti al massimo · spendi un Payoff per continuare a generare" |
| Gen confirm | "Frammento di Onirade catturato" |
| 3F confirm | "Dispel area attivato · effetti arcani rimossi" |
| 5F boss summon | "Evocazione annullata · bersaglio bandito dal campo" |
| 5F incorporeo | "Bersaglio incorporeo bandito" |
| 5F no_special | "Barriera arcana attivata · autoprotezione temporanea" |
| Interrupt | "Rituale interrotto · Frammenti conservati" |
| No target | "Nessun bersaglio marchiabile · applica prima un Marchio del Vuoto" |
| Marchio expired | "Marchio del Vuoto svanito · nuovo Marchio richiesto per il Drain" |

- **Italiano puro** · **zero token `[Gx#y]`** · **zero slug visibili al player**

## Sezione 28 · Feedback concept

- **Visual gen**: flash viola-arcano segmento riempito · particella sopra target Marchiato
- **Visual 3F**: onda arcana AoE viola tenue · no screen shake
- **Visual 5F**: flash intenso + swirl banish 0.5s · tint 0.2s
- **Audio gen**: click arcano 40ms · non intrusivo
- **Audio 3F**: chord dispel breve dolce
- **Audio 5F**: sussurro arcano + banish sfx drammatico
- **Audio cap**: chime discreto una tantum
- **Accessibility**: toggle reduce_motion · toggle reduce_audio · no epilepsy triggers
- **Haptic**: N/A web-first (mobile futuro potrebbe usare vibrazione leggera 5F)

## Sezione 29 · Party 3p dungeon compat

- Loop resource funzionale
- Synergy Paladino heal · Vuoto libera slot dispel party via 3F
- Synergy Guerriero tank · Vuoto genera in mid-range senza rubare threat
- Synergy Cacciatore di Mostri anti-fisico · Vuoto anti-arcano · zero contesa risorse (Frammenti class-exclusive)

## Sezione 30 · Raid 5p compat

- Role: DPS anti-summon
- Payoff 5F prioritario su add-summon boss critical phase
- Synergy Mago burst target primario · Vuoto elimina add-summon → burst Mago non interrotto
- Phase awareness: player conosce timing add-summon · stockpile 5F in preparation phase
- Zero resource contention cross-class

## Sezione 31 · Boss safeguards

- Boss Marchio stack cap: 1
- Boss dispel immunity parziale · DoT ridotto 50% · silenziamento SOLO ability non-lethal · MAI enrage/hard-cast
- Boss 5F annullamento: IMMUNE · fallback self-buff arcano
- Boss generation proc bonus: 0% (anti-farm)
- Boss Int bonus cap: +5% max su dispel/silence/durata
- Boss add-summon priority flag: 5F opera SOLO su add-summon boss-invocati · MAI su boss target
- Boss arcane effect rank leggendario: immune a 3F (richiede 5F o mechanic dedicata)
- **No boss softlock** · **No boss perma-stun** (silence cap 1 turno) · **No dispel-spam** (cooldown implicito via generation)

## Sezione 32 · Risk register (15 rischi tracciati)

| ID | Rischio | Severity | Status |
|---|---|---|---|
| RM-R1 | Cap 5 percepito 'troppo lento' casual | MEDIUM | DESIGNED |
| RM-R2 | Int 45% cap percepito 'stat check hard' | LOW | DESIGNED |
| RM-R3 | 5F su boss = disappointment (immune) | MEDIUM | DESIGNED |
| RM-R4 | Marchio expiry frequente = frustration | MEDIUM | DESIGNED |
| RM-R5 | Overcap wasted percepito hidden punishment | LOW | DESIGNED |
| RM-R6 | No-summon/no-incorporei = loop degradato disorientante | MEDIUM | DESIGNED |
| RM-R7 | Boss add-summon priority flag confusa multi-source | MEDIUM | TRACKED PG1 |
| RM-R8 | Balestra 2H opportunity cost mal percepito | LOW | DESIGNED |
| RM-R9 | Focus channel 2/encounter cap = artificial gate | LOW | DESIGNED |
| RM-R10 | Reset encounter-local → hoarding-then-reset frustration | LOW | DESIGNED |
| RM-R11 | Legendary P1-P4 può rompere cap 5 | LOW-MEDIUM | TRACKED PG1 |
| RM-R12 | Bridge legacy warlock resource | LOW | DESIGNED |
| RM-R13 | Silence summon 3T percepito broken vs summon builders | MEDIUM | TRACKED PG2 |
| RM-R14 | Payoff cast 1T interrompibile CC-heavy | MEDIUM | DESIGNED |
| RM-R15 | Cross-class balance vs Mago/CdMostri DPS | MEDIUM | TRACKED PG3 |

## Sezione 33 · PM Open Questions (RM-Q1..RM-Q7)

- **RM-Q1** · *Cap 5 hard indipendente da Int LOCK definitivo?* → recommendation: **a) LOCK**
- **RM-Q2** · *Focus channel bonus max 2/encounter conferma?* → recommendation: **a) LOCK 2/encounter**
- **RM-Q3** · *Pugnale ritual close bonus una tantum per Marchio conferma?* → recommendation: **a) LOCK**
- **RM-Q4** · *Boss add-summon priority flag su 5F conferma?* → recommendation: **a) LOCK · 5F solo su add-summon boss-invocati**
- **RM-Q5** · *Marchio durata scaling Int 3→8 hard cap 10 conferma?* → recommendation: **a) LOCK**
- **RM-Q6** · *Reset per phase vs cross-phase-persistence boss multi-phase?* → recommendation: **a) reset per phase**
- **RM-Q7** · *Silenziamento summon 3T PvE-only o PvP diff da subito?* → recommendation: **c) HOLD questione PvP fino a gate PvP dedicato**

## Sezione 34 · GO/HOLD Recommendation Gate 5 EQUIP_DESIGN

- **Gate 4 status**: DRAFT · pending PM review + risposte RM-Q1..RM-Q7
- **Gate 5 status**: 🔒 HOLD · attende PM ACK Gate 4 + GO esplicito Gate 5
- **Gate 5 input from G4**: cap 5 LOCK · generation matrix weapon · Int 5-axis scaling · Marchio durata + max cap · Payoff 3F/5F reliability · boss safeguards · reset policy → input per EQUIP_DESIGN (weapon coefficients · affix · budget statistico · ILVL)
- **Gate 5 scope preview**: weapon damage coefficients · weapon affix design · armor budget statistico · ILVL scaling · Legendary utility_unique overrides · slot allocation · rarity distribution · SOLO equip · NO gameplay implementation · NO Registry v3 · NO drop tables

---

## 🛑 STOP before Gate 5 EQUIP_DESIGN

**Non procedere a Gate 5 senza nuovo GO PM.**

Attendo PM review Gate 4 + risposte a **RM-Q1..RM-Q7**. Nessun auto-start · nessuna modifica R18.5/R18.6/R18.6.1/R18.6.2/G1/G2/G3 (tutti LOCKED).

---

## Operational compaction guard (session snapshot · NOT in PRD)

Prima di segnalare canonical drift al PM verificare separatamente: (1) contenuto effettivo dei file · (2) contenuto del summary chat · (3) discrepanza tra i due.
**Regola**: chat summary ≠ source of truth · file deliverable + SHA256 + validation = source of truth.
