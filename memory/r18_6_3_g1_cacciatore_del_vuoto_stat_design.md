# R18.6.3 · Gate 1 · STAT_DESIGN · Cacciatore del Vuoto

**Pilot**: Cacciatore del Vuoto (Wave 1 · #1) · **Hall**: `hall_cacciatore_del_vuoto` (Faro Rovesciato di Onirade · Nael di Onirade) · **Locked at (UTC)**: 2026-07-08T17:15:00Z

**Authority**: PM Orchestrator — R18.6.3-G1 STAT_DESIGN GO esplicito · **Intelligenza LOCKED** verbatim

**Regime**: **DOCUMENTAL ONLY** · Gate 1 definisce SOLO stat design · NO proficiency (Gate 2) · NO gameplay loop (Gate 3) · NO resource (Gate 4) · **NO Gate 2 auto-start** · NO code · NO DB · NO Registry v3 · NO nuovi item · NO class unlock · NO Hall activation · NO class_slug apply · NO legacy bridge apply · NO auto-derive · NO modifica R18.5/R18.6/R18.6.1/R18.6.2 (LOCKED).

### ⚠️ Legacy Bridge Correction (verbatim PM)

```yaml
legacy_bridge_source: warlock
canonical_target_slug: cacciatore_del_vuoto
bridge_status: mapped_design_only
migration_status: not_applied
runtime_bridge_status: disabled
```

Il bridge serve per readiness/migrazione futura · NO auto-derive · NO migration apply · NO runtime bridge · nuovi avventurieri continuano a nascere `class_slug=null · recruit_unassigned`.

---

## Sezione 1 · Identità Statistica della Classe

Il Cacciatore del Vuoto è una classe caster-ranged anti-incorporei che si distingue per l'uso arcano di focus, pugnale e balestra come strumenti di canalizzazione. La sua identità statistica poggia interamente su Intelligenza come stat driver unico: precisione arcana, marchi dispel, drenaggio di essenza (Frammenti di Onirade). Non è un cacciatore agile (Cacciatore di Mostri · Destrezza) né un caster puro (Mago · Intelligenza ma con arsenale diverso) né un supporter sacro (Paladino · Saggezza). La sua identità statistica è l'anti-arcano di precisione contro summon e incorporei.

**Hall context**: Faro Rovesciato di Onirade · Nael di Onirade · lore 'si caccia ciò che non ha peso'
**Ruolo indicativo (R18.6.1)**: DPS ranged/melee ibrido con specializzazione dispel/anti-summon

## Sezione 2 · Intelligenza come Main Stat (LOCK verbatim PM)

- **main_stat**: **Intelligenza** 🔒 LOCKED (verbatim V-Q1 PM · PRD append R18.6.2 APPROVED)
- **No dual main stat** ✅ · **No hybrid scaling** ✅

**Rationale PM verbatim**:
- Unica primaria · non condivisa scaling con Destrezza/Saggezza/Costituzione per il ruolo primario
- Balestra = canalizzazione arcana · NON gear Rogue/Ranger riciclato
- Penalità XP main stat insufficiente si applica al Cacciatore del Vuoto senza eccezioni

**Alternatives rejected**:
- **Saggezza**: REJECTED · overlap con Paladino · Vuoto non è sacro né healer/support
- **Destrezza**: REJECTED · overlap con Cacciatore di Mostri e Ladro · Vuoto non è agile fisico
- **Forza**: REJECTED · incoerente con lore anti-incorporeo e canalizzazione arcana

## Sezione 3 · Relazione con Altre Stat

- **Intelligenza**: Scaling driver PRIMARIO su damage focus/pugnale/balestra · potenza Marchio del Vuoto · generazione Frammenti di Onirade · payoff dispel/annullamento
- **Destrezza**: Contribuisce ad accuracy balestra secondaria (design gate PROFICIENCY_DESIGN futuro) · MAI scaling di danno primario
- **Costituzione**: Survivability base · resistenze dispel-backlash narrativo (concept design futuro) · NO scaling danno
- **Saggezza**: Nessun ruolo diretto · possibile utility su interazioni sacre/anti-Vuoto (design gate futuro se emergono meccaniche)
- **Forza**: Nessun ruolo · dump stat raccomandato

**No hybrid scaling**: Il Cacciatore del Vuoto NON ha hybrid scaling (Int+Wis o Int+Dex) sulla base danno. Il main_stat è unico e locked.

## Sezione 4 · Priorità Statistiche

1. **Primary**: Intelligenza (main_stat · scaling driver principale)
2. **Secondary recommended**: Costituzione (survivability minima in melee opportunistico con pugnale · resistenza dispel-backlash narrativo)
3. **Tertiary recommended**: Destrezza (mobilità nel Faro Rovesciato + accuracy balestra secondaria · NON scaling di danno)
4. **Dump stats**: Forza (nessun ruolo per Cacciatore del Vuoto) · Saggezza (nessun ruolo scaling · può essere dump con eccezione di eventuali resistenze specifiche gate futuro)

**Notes**: Priorità Int → Cos → Dex → dump(Str, Wis) è raccomandazione design · non hard-lock oltre a main_stat=Intelligenza · gate futuro EQUIP_DESIGN valuterà secondari via item affix

## Sezione 5 · Scaling Previsto Lv1-60

Curva design layer · numeri finali locked nel gate TECH_READINESS · questa sezione documenta principi

| Level | Tier | Int expected | Gear context |
|---|:--:|:--:|---|
| 1-15 | T1 | 10-25 | starter · Common/Uncommon prevalente |
| 16-30 | T2 | 25-45 | Uncommon/Rare prevalente |
| 31-45 | T3 | 45-70 | Rare/Epic prevalente |
| 46-55 | T4 | 70-90 | Epic (T4 progressive_marker 10 items) |
| 56-60 | T5 | 90-115 | Epic/Legendary (Legendary flat +60 R18.5 C3 Q7) |

- **Rarity offsets (R18.5 C3 reference)**: Common:0 · Uncommon:2 · Rare:3 · Epic:4 · Legendary:5
- **Legendary flat bonus**: +60 (C3 Q7 lockato) · applicato su Int scaling per item Legendary Cacciatore del Vuoto (futuri)
- **Curve type**: linear con soft cap oltre tier T4-T5 · anti-power-creep
- **Gating**: ILVL formula C3 approvata · Cacciatore del Vuoto gear scaling Int deve rispettare rarity offsets · no overshoot

## Sezione 6 · Rapporto Stat → Danno (formula design)

Formula design layer · valori numerici in TECH_READINESS gate futuro

- **Focus damage**: `base_focus_dmg × (1 + int_scaling_focus × Int) · int_scaling_focus alto (weapon primaria arcana)`
- **Pugnale damage**: `base_pugnale_dmg × (1 + int_scaling_pugnale × Int) · int_scaling_pugnale ridotto (melee opportunistico · NON specializzazione primaria)`
- **Balestra damage**: `base_balestra_dmg × (1 + int_scaling_balestra × Int) · int_scaling_balestra medio-alto (canalizzazione arcana a distanza)`

**No Dex/Str scaling di danno** ✅ · **No hybrid scaling** ✅

**Diminishing returns**: oltre Int ≈ 90 (T4-T5 boundary) scaling multiplier si riduce · previene power creep

## Sezione 7 · Rapporto Stat → Marchio del Vuoto

Meccanica Marchio è design output gate GAMEPLAY_LOOP (Gate 3) · questa sezione documenta SOLO come Int scala la meccanica futura

- **Durata dispel-over-time**: durata Marchio scala con Int (linear · soft cap Int ≈ 100)
- **Potenza silenziamento summon**: potenza silence su summon nemici scala con Int (linear · soft cap Int ≈ 100)
- **Max marchi attivi simultanei**: cap iniziale design raccomandato = 3 · scalabile con Int a soglie (es. +1 marchio a Int 50, +1 a Int 90) · numeri finali gate futuro
- **Resistance check scaling**: target con resistenze arcane richiedono soglia Int minima per applicare Marchio · design gate futuro

## Sezione 8 · Rapporto Stat → Drain

Meccanica Drain è output gate GAMEPLAY_LOOP + RESOURCE_MECHANIC · G1 documenta scaling Int

- **Frammenti per colpo su marchiato**: 1 Frammento base · +1 bonus a soglia Int (es. Int ≥ 60) · gate RESOURCE_MECHANIC finalizza numeri
- **Bonus dispel summon**: +1 · non scala direttamente con Int (evita farming Int-heavy)
- **Bonus annullamento boss summon**: +2 · non scala direttamente con Int (evita farming boss)
- **Anti-abuse cap**: cap Frammenti per encounter = 5 (V-Q4 LOCKED R18.6.2) · Int NON aumenta cap

## Sezione 9 · Rapporto Stat → Payoff

Meccanica Payoff è output gate GAMEPLAY_LOOP + RESOURCE_MECHANIC · G1 documenta scaling Int

- **Dispel area 3 Frammenti**: raggio dispel area scala con Int (linear con soft cap Int ≈ 100) · potenza dispel scala con Int
- **Annullamento boss summon 5 Frammenti**: chance di successo scala con Int fino a soft cap Int ≈ 100 (es. 50% Int 30, 90% Int 100) · una-tantum per encounter
- **Duration of dispel effect**: durata effetto post-dispel scala con Int (design layer · numeri finali gate futuro)
- **No Int beyond soft cap reward**: oltre Int 100 nessun beneficio significativo su Payoff · anti-power-creep

## Sezione 10 · Rischi Power Creep (7 protezioni documentate)

- **risk_1_int_stacking_via_items**: Int stacking via multi-item Int-boost potrebbe rompere scaling · mitigazione: soft cap Int ≈ 100 su tutte le meccaniche · rarity offset R18.5 (0/2/3/4/5) enforced · anti-P2W preserved (no premium boost Int)
- **risk_2_legendary_flat_60_bonus**: Legendary flat +60 (C3 Q7) può portare Int a 115+ · mitigazione: soft cap 100 su scaling · Legendary offre solo utility_unique + affix rari, NON overrides scaling design
- **risk_3_diminishing_returns_absence**: assenza diminishing returns porterebbe a scaling lineare unbounded · mitigazione: soft cap 100 · linear con curve flattening
- **risk_4_synergy_with_progressive_discovery**: 4 Progressive Discovery Legendary (P1-P4 attualmente HOLD) potrebbero includere effetti class-locked per Vuoto · mitigazione: PG1 tracked · Progressive Discovery gate dedicato · no anticipazione design G1
- **risk_5_secondary_stat_bleed**: Costituzione/Destrezza secondari via item affix potrebbero creare hybrid inaspettato · mitigazione: gate EQUIP_DESIGN limita affix multi-stat · Int primary preserved
- **risk_6_soft_cap_evasion_via_buff_stack**: buff temporanei potrebbero superare soft cap · mitigazione: soft cap si applica anche a buff temporanei · gate TECH_READINESS enforcement
- **risk_7_anti_p2w_preservation**: premium items o real-money boost potrebbero rompere design · mitigazione: R18.5 anti-P2W lockato (can_be_sold_for_real_money=false 1500/1500) · nessuna eccezione per Vuoto

## Sezione 11 · Differenza Statistica da Mago

- **Shared main stat**: Intelligenza (condivisa · unico caso tra 5 live + Vuoto)
- **Diff 1 · weapon family**: Mago: bastone · tomo · focus · pugnale · Vuoto: focus · pugnale · balestra · NO bastone · NO tomo. Overlap solo su focus (canalizzazione arcana generica) + pugnale (opportunistico). Balestra è unica del Vuoto.
- **Diff 2 · gameplay style**: Mago = burst caster puro con AoE elemental · Vuoto = anti-summon/dispel con Marchi + Frammenti pool + drain-based payoff. Ruoli DPS distinti.
- **Diff 3 · armor**: Mago: solo stoffa · Vuoto: cuoio + stoffa. Cuoio è unica del Vuoto (mobility nel Faro).
- **Diff 4 · resource**: Mago: mana/spell system (design R18.5 non specificato in G1) · Vuoto: Frammenti di Onirade (encounter-local · cap 5). Risorse ortogonali · no competition item.
- **Diff 5 · target priority**: Mago: bersagli generici arcani/elementali · Vuoto: incorporei > summon nemici > caster > melee (specializzazione anti-arcano)
- **Diff 6 · role**: Mago R18.6: DPS puro · Vuoto R18.6.1: DPS con specializzazione dispel/anti-summon (utility hybrid)
- **No item competition expected**: Progressive Discovery Legendary Vuoto (futuri) sono distinti da Mago's · gate PG1 tracked

## Sezione 12 · Differenza Statistica da Cacciatore di Mostri

- **Shared main stat**: NONE (CdM=Destrezza · Vuoto=Intelligenza)
- **Diff 1**: CdM scala su Dex (precisione fisica · accuracy · dodge) · Vuoto scala su Int (precisione arcana · dispel · Marchi). Non c'è competizione statistica.
- **Diff 2 · weapon family**: CdM: arco · balestra · spada · pugnale · lancia · Vuoto: focus · pugnale · balestra. Overlap: balestra + pugnale. Ma balestra CdM=ranged fisico agile · balestra Vuoto=canalizzazione arcana (design divergente EQUIP_DESIGN gate futuro).
- **Diff 3 · gameplay style**: CdM: ranged agile · trappole · knowledge bestie · Vuoto: ranged arcano · Marchi · anti-incorporei. Ruoli DPS distinti (bestie fisiche vs incorporei/summon).
- **Diff 4 · target priority**: CdM: bestie · mostri fisici · Vuoto: incorporei · summon · anti-arcano. Zero overlap target.
- **Diff 5 · armor**: CdM: cuoio + maglia · Vuoto: cuoio + stoffa. Overlap solo cuoio. Maglia CdM unica · stoffa Vuoto unica.
- **Diff 6 · resource**: CdM: nessuna risorsa unica documentata R18.6 · Vuoto: Frammenti di Onirade
- **Narrative diff**: CdM: 'La bestia è vecchia, il cacciatore di più' · Vuoto: 'Si caccia ciò che non ha peso'. Semantica cacciatore condivisa · sostanza cacciata fondamentalmente diversa.

## Sezione 13 · Differenza Statistica da Paladino

- **Shared main stat**: NONE (Paladino=Saggezza · Vuoto=Intelligenza)
- **Diff 1 · role**: Paladino: Healer/Support sacro · Vuoto: DPS anti-arcano. Ruoli opposti nel team.
- **Diff 2 · thematic axis**: Paladino: 'La luce non chiede, la luce impone' (sacro affermativo) · Vuoto: 'Si caccia ciò che non ha peso' (arcano negativo/dispel). Assi opposti.
- **Diff 3 · weapon family**: Paladino: bastone · martello · focus · reliquia · Vuoto: focus · pugnale · balestra. Overlap solo focus (weapon condivisa tra caster/anti-caster). Reliquia Paladino unica · balestra + pugnale Vuoto unici.
- **Diff 4 · armor**: Paladino: solo stoffa · Vuoto: cuoio + stoffa. Cuoio Vuoto unico.
- **Diff 5 · gameplay focus**: Paladino: protezione + resurrezione + heal · Vuoto: Marchi + drain + dispel. Nessuna sovrapposizione meccanica.
- **Diff 6 · target priority**: Paladino: alleati (heal) + nemici sacri (light burst) · Vuoto: incorporei/summon (dispel/annullamento). Zero overlap.
- **No cross-class bleed**: Paladino e Vuoto potrebbero coesistere nello stesso raid come healer + anti-summon DPS · complementari · no competition item/role

## Sezione 14 · Compatibilità Futura con Stoffa e Cuoio

SOLO note di compatibilità stat-armor · design proficiency è output Gate 2 PROFICIENCY_DESIGN

- **Stoffa Int-focus**: stoffa items dovrebbero privilegiare Int come stat primaria (coerente con caster tradition) · gate EQUIP_DESIGN futuro conferma affix Int-heavy
- **Cuoio Int-focus**: cuoio items del Cacciatore del Vuoto dovrebbero privilegiare Int (NO doppia identità Dex-focus tipica cuoio Ladro/CdM) · gate EQUIP_DESIGN valida design distinto
- **No double stat identity**: V-Q2 PM lock: entrambi armor devono privilegiare Intelligenza · no hybrid Int+Dex o Int+Cos
- **Future set bonus hint**: set bonus 2/4/6 pezzi (design gate EQUIP_DESIGN futuro) può includere Int scaling amplification · design layer only ora

## Sezione 15 · Compatibilità Futura con Focus, Pugnale e Balestra

SOLO note di compatibilità stat-weapon · design proficiency è output Gate 2

- **Focus Int scaling**: focus è weapon primaria arcana · scaling Int alto (int_scaling_focus alto)
- **Pugnale Int scaling**: pugnale è weapon opportunistica melee · scaling Int ridotto rispetto a focus (int_scaling_pugnale ridotto) · NO Dex scaling di danno
- **Balestra Int scaling**: balestra è weapon canalizzazione ranged · scaling Int medio-alto (int_scaling_balestra medio-alto) · NO Dex scaling di danno · Dex può contribuire ad accuracy ma NON al danno base
- **Lanterna RESERVED FUTURE**: weapon family lanterna RESERVED · valutabile in EQUIP_DESIGN · potenziale scaling Int primary · NO in catalogo R18.5
- **Esclusioni verbatim**: esclusioni verbatim V-Q3 PM lock · design proficiency Gate 2 enforcerà

## Sezione 16 · Interazione con Penalità XP per Main Stat Insufficiente

**Regola PM verbatim**: *Penalità XP per main stat insufficiente si applica al Cacciatore del Vuoto senza eccezioni.*

- Applies to Cacciatore del Vuoto: ✅
- No exceptions: ✅
- **Trigger**: adventurer con class_slug=cacciatore_del_vuoto che equipaggia gear il cui main_stat_target != Intelligenza subisce XP penalty (design layer · valori numerici gate futuro)
- **Purpose**: enforcement dell'identità statistica · previene reroll silente stat-focus via gear · anti-cheese
- **Lock_state interaction**: possibile nuovo lock_state warning (design gate TECH_READINESS) o riuso lock_state esistenti C2 con badge XP-penalty
- **No soft bypass** ✅ · **No premium bypass** ✅

## Sezione 17 · Readiness Checklist R-01

- **Item ID**: R-01
- **Check**: main_stat definitivo (uno di Forza/Destrezza/Intelligenza/Saggezza · con rationale narrativo/gameplay)
- **Result**:
  - `main_stat_defined`: Intelligenza
  - `rationale_documented`: True
  - `pm_lock_verified`: True
  - `no_dual_main_stat`: True
  - `no_hybrid_scaling`: True
  - `differentiation_from_5_live_classes_documented`: True
  - `power_creep_protections_documented`: True

**Checklist status**: COMPLETED ✅ (per R-01 · altre R-02..R-13 restano PENDING gate successivi)

## Sezione 18 · Risk Register (10 rischi)

| ID | Rischio | Severity | Status |
|:--:|---|:--:|:--:|
| **SD-R1** | Int stacking via multi-item Int-boost rompe scaling | MEDIUM | DESIGNED |
| **SD-R2** | Legendary flat +60 porta Int oltre 115 · scaling break | MEDIUM | DESIGNED |
| **SD-R3** | Assenza diminishing returns · scaling lineare unbounded | MEDIUM | DESIGNED |
| **SD-R4** | Progressive Discovery Legendary Vuoto (futuri) rompe design G1 | LOW-MEDIUM | TRACKED PG1 |
| **SD-R5** | Secondary stat affix (Cos/Dex) creano hybrid inaspettato | MEDIUM | DEFERRED to EQUIP_DESIGN |
| **SD-R6** | Buff temporanei superano soft cap Int | LOW | DESIGNED |
| **SD-R7** | Player interpreta 'Int shared con Mago' come 'stessa classe diversa skin' | MEDIUM | DOCUMENTED |
| **SD-R8** | Penalità XP main stat insufficiente confonde player nuovi | LOW-MEDIUM | DOCUMENTED |
| **SD-R9** | Bridge legacy warlock → cacciatore_del_vuoto crea confusione per player Round 16.x che avevano 'warlock' concept | LOW | DOCUMENTED |
| **SD-R10** | Int-only scaling considerato 'noioso' rispetto a hybrid systems altri MMO | LOW | DESIGNED |

## Sezione 19 · PM Open Questions (SD-Q1..SD-Q7)

- **SD-Q1** · *Soft cap Int ≈ 100 confermato o alternativo (es. 90, 110, adaptive per tier)?*
  - a) confermo 100 fisso
  - b) 90 (più stretto)
  - c) 110 (più permissivo)
  - d) adaptive per tier T1-T5 (curve tier-based)
- **SD-Q2** · *Secondary stat priority Cos → Dex confermata o Dex → Cos (mobilità prima di survivability)?*
  - a) confermo Cos → Dex
  - b) Dex → Cos
  - c) tie (Cos ≡ Dex · player choice)
- **SD-Q3** · *Diminishing returns curve type: linear-flattening vs logarithmic vs step-function?*
  - a) linear con soft cap 100 (design raccomandato)
  - b) logarithmic (smoother)
  - c) step-function (stat breakpoints a soglie 30/60/90)
- **SD-Q4** · *Bridge legacy warlock → cacciatore_del_vuoto · gate futuro dedicato o gestione in R18.3f (Class Slug Migration Readiness)?*
  - a) R18.3f handling (integrato con class_slug migration)
  - b) gate dedicato R18.6.LB1 (Legacy Bridge Design)
  - c) documental only forever (nessun apply · nessuna migration)
- **SD-Q5** · *Penalità XP main stat: hard-block (XP=0) o soft (XP ridotta)?*
  - a) soft (XP ridotta · es. -50%)
  - b) hard (XP=0)
  - c) tiered (soft T1-T3 · hard T4-T5)
- **SD-Q6** · *Stat Saggezza dump vs preserve per future utility (es. anti-Vuoto resistenze)?*
  - a) dump raccomandato (design attuale)
  - b) preserve utility bassa (per resistenze future)
  - c) preserve utility media (design gate futuro rivalutazione)
- **SD-Q7** · *Balestra Vuoto scaling: int_scaling_balestra medio-alto vs alto (parificato a focus)?*
  - a) medio-alto (design attuale · differenzia focus come primaria)
  - b) alto (parificato a focus)
  - c) alto ma con penalty accuracy senza Dex secondario

## Sezione 20 · GO/HOLD Recommendation per Gate 2 PROFICIENCY_DESIGN

- **Gate 1 STAT_DESIGN status**: COMPLETED · pending PM review + risposte SD-Q1..SD-Q7
- **Gate 2 PROFICIENCY_DESIGN status**: 🔒 HOLD · attende PM ACK Gate 1 + GO esplicito Gate 2

**Recommendation**:
- APPROVE Gate 1 STAT_DESIGN (Intelligenza LOCKED · scaling design Lv1-60 · power creep protections · differentiation matrix)
- HOLD Gate 2 PROFICIENCY_DESIGN in attesa PM ACK
- Rispondere a SD-Q1..SD-Q7 in round dedicato prima di Gate 2 dispatch
- NO auto-transition · NO gate skip · NO parallel gate execution

**Post-Gate-1-ACK next steps**:
- Input Gate 2 from Gate 1: Intelligenza main_stat + soft cap 100 + priority order Cos/Dex → input per PROFICIENCY_DESIGN Gate 2
- Gate 2 scope: armor whitelist (cuoio + stoffa) + weapon whitelist (focus + pugnale + balestra) + lanterna RESERVED valuation · SOLO proficiency, no gameplay/resource

---

## Governance Snapshot Gate 1

| Voce | Stato |
|---|:--:|
| Documental only regime · Italian output | ENFORCED ✅ |
| 36 sealed byte-identical · pytest 6/6 | ✅ |
| `lore_meta.py` INVARIATO (`a18f708b…`) | ✅ |
| DB / code / migrations | 0 / 0 / 0 ✅ |
| R18.5 / R18.6 / R18.6.1 / R18.6.2 modification | 0 / 0 / 0 / 0 ✅ (all LOCKED) |
| Registry v3 dispatched | ❌ (HOLD) |
| Cacciatore del Vuoto live activation | BLOCKED ✅ |
| Legacy bridge apply | 0 ✅ (mapped_design_only) |
| Gate 2/3/4 auto-start | BLOCKED ✅ |
| Gate isolation enforced | ✅ (Gate 1 = SOLO stat design) |
| File deliverable G1 | 2 (.md + .json) |
| Sezioni scope coperte | 20 / 20 ✅ |

---

## 🛑 STOP before Gate 2 PROFICIENCY_DESIGN

**Non procedere a Gate 2 senza nuovo GO PM.**

Attendo PM review Gate 1 + risposte a **SD-Q1..SD-Q7** prima di dispatch Gate 2. Nessun auto-start · nessuna modifica R18.5/R18.6/R18.6.1/R18.6.2 (tutti LOCKED).
