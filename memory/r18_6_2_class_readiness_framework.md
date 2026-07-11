# R18.6.2 · Class Readiness Framework (with Cacciatore del Vuoto Pilot)

**Round**: R18.6.2 · **Locked at (UTC)**: 2026-07-08T16:45:00Z
**Authority**: PM Orchestrator — R18.6.2 GO esplicito con pilot Cacciatore del Vuoto
**Regime**: **DOCUMENTAL ONLY** — NO code · NO DB · NO migrations · NO class_slug apply · NO auto-derive · NO live activation · NO Cacciatore del Vuoto unlock · NO 22 PLANNED unlock · NO R18.5/R18.6/R18.6.1 modification (all LOCKED).

---

## Sezione 1 · Executive Summary

Definire il **processo tecnico + gameplay** con cui una classe PLANNED può diventare **ACTIVE-DESIGN-READY**. Framework universale applicabile a tutte le 22 PLANNED · applicato subito al **primo pilota Cacciatore del Vuoto** (Wave 1 · #1).

**R18.6.2 NON attiva Cacciatore del Vuoto live** — propone solo il piano. L'unlock richiederà gate PM successivi (STAT_DESIGN → PROFICIENCY_DESIGN → ... → PM_REVIEW).

**Wave 1 scope (verbatim PM Q2)**: Cacciatore del Vuoto · Monaco · Druido · Alchimista · Bardo · Negromante.

## Sezione 2 · Readiness Checklist Universale (13 items)

| ID | Check |
|:--:|---|
| **R-01** | main_stat definitivo (uno di Forza/Destrezza/Intelligenza/Saggezza · con rationale narrativo/gameplay) |
| **R-02** | armor_proficiency whitelist (subset di stoffa/cuoio/maglia/piastre · con rationale) |
| **R-03** | weapon_proficiency whitelist (subset di famiglie R18.5 · eventuali RESERVED families flagged) |
| **R-04** | gameplay loop base (identificazione target → azione → payoff → cooldown/tempo) |
| **R-05** | risorsa/meccanica di classe (nome canonico · generazione · consumo · scope) |
| **R-06** | equip dedicato sufficiente (n. items base · gap analysis su Registry v2) |
| **R-07** | guida player-facing completa (tooltip · descrizione · forze/debolezze · stile · ruolo · anteprima Sala) |
| **R-08** | Sala completa (20 campi R18.6.1 filled + hall_master LOCKED) |
| **R-09** | prova safe-mode tecnicamente definita (obiettivi didattici · restrizioni · fallback · esiti attesi) |
| **R-10** | readiness tecnica (schema DB · validator equip · lock_state integration · migration path) |
| **R-11** | bridge legacy analysis (se esiste class_proficiency legacy corrispondente · o dichiarazione canonical-new) |
| **R-12** | anti-P2W validation (no premium items · no real-money shortcut · no gated behind paywall) |
| **R-13** | PM review + explicit GO per Sala |

## Sezione 3 · Gate Sequence Obbligatoria (10 gate)

Nessun bypass · nessuna approvazione tacita · ogni gate è PM gate esplicito.

| # | Gate ID | Input | Output |
|:--:|---|---|---|
| 1 | **STAT_DESIGN** | hall lore + ruolo indicativo R18.6.1 | main_stat definitivo + rationale |
| 2 | **PROFICIENCY_DESIGN** | main_stat + gameplay concept | armor_proficiency + weapon_proficiency whitelist |
| 3 | **GAMEPLAY_LOOP** | proficiency + resource concept | loop base 4-step (identify/act/payoff/cooldown) |
| 4 | **RESOURCE_MECHANIC** | gameplay loop + lore | risorsa classe nome canonico + generazione/consumo/scope |
| 5 | **EQUIP_DESIGN** | proficiency + gameplay + Registry v2 gap analysis | equip dedicato base + gap items count |
| 6 | **PLAYER_GUIDE** | tutti i gate precedenti | guida player-facing italiana (tooltip · descrizione · forze/debolezze) |
| 7 | **HALL_COMPLETION** | R18.6.1 hall profile (20 campi) | verifica 20 campi filled + hall_master LOCKED + hall_id canonical |
| 8 | **SAFE_MODE_TRIAL** | concept R18.6.1 + gameplay loop | prova safe-mode tecnica (obiettivi/restrizioni/fallback/esiti) |
| 9 | **TECH_READINESS** | tutti i gate precedenti | schema DB delta · validator equip · lock_state integration · migration path (READINESS ONLY · NO APPLY) |
| 10 | **PM_REVIEW** | output di tutti i 9 gate precedenti | explicit GO PM per PLANNED → ACTIVE-DESIGN-READY transition |

## Sezione 4 · Dependency Matrix

### 4.1 · Registry v2 interaction
- **Current state**: Registry v2 LOCKED · 1500 items · 5 classi × 300 items · runtime_apply_ready=false 1500/1500
- **Planned class impact**: una nuova classe ACTIVE richiede: N item dedicati (stima 50-100 per set base) · new class_proficiency label · slot_canonical mapping (nessuno slot nuovo) · anti-P2W check
- **NO R18.5 modification** ✅
- **Future**: Registry v3 (o extension additive) · gate futuro post-R18.5 lockdown · fuori scope R18.6.2

### 4.2 · Drop table interaction
- **Current state**: Drop table dry-run (C4) · 60 dungeon canonical + 12 raid canonical · HYBRID 0.5% · loot-lock H3/H4 weekly
- **Planned impact**: nuovi item classe richiedono drop table extension · dungeon assignment · anti-P2W preserved

### 4.3 · Lock_state C2 relevant (6 stati riusati · nessuno nuovo)
- `#3_locked_recruit_unassigned` → Recluta senza classe · blocca equip specializzato · CTA 'Assegna Sala'
- `#4_locked_class_slug_null` → adventurer con class_proficiency ma class_slug=null · bridge C5/R18.3f
- `#5_universal_allowed` → consumable/material/cosmetic · bypass proficiency
- `#6_locked_proficiency_armor` → armor_type not in class whitelist → blocca
- `#7_locked_proficiency_weapon` → weapon_family not in class whitelist → blocca
- `#10_equippable` → tutti i check passed

## Sezione 5 · Hall Completion Criteria

20 campi R18.6.1 required (hall_id · nome · slug · classe · regione · lore · architettura · atmosfera · simbolo · colori · hall_master · prova · rituale · main_stat · armor · weapon · stile · ruolo · tratto · stato).

- **hall_master status**: must be LOCKED (PM APPROVED · no PENDING)
- **Consistency with R18.6.1**: tutti i 20 campi devono restare coerenti con hall profile R18.6.1 (immutable) · main_stat + proficiency vengono da gate STAT_DESIGN + PROFICIENCY_DESIGN
- **Language**: tutti i campi in italiano canonico Orbus

## Sezione 6 · Safe-Mode Trial Criteria

**Concept source**: R18.6.1 baseline · **Technical definition required**:
- obiettivi didattici espliciti
- meccaniche da insegnare (subset del gameplay loop)
- restrizioni safe-mode (NO death · NO rare resource consumption · NO endgame drop · NO farmabile)
- esiti attesi (pass/fail conditions · retry policy)
- fallback design (cosa succede se il Recluta fallisce ripetutamente)

**Rules**: non replace general tutorial · one-time per Recluta · dismissal liberates slot · no premium shortcut.

## Sezione 7 · Player-Facing Guide Criteria

**Sezioni richieste (guida italiana canonical)**:
- tooltip breve (1-2 righe · presentazione classe)
- descrizione estesa (paragrafo · lore + gameplay hint)
- punti forti (bullet list 3-5)
- punti deboli (bullet list 2-4)
- stile gameplay (frase sintetica ruolo/ritmo)
- equip tipico (armor + weapon families)
- ruolo indicativo (Tank/DPS/Healer/Support/Utility/Hybrid)
- anteprima UI Sala (screenshot/mockup testuale)
- avvertimento reversibilità (Rite of Rebirth costo elevato una tantum)

## Sezione 8 · Registry / Class_slug Criteria

- class_slug immutable mapping ✅ · da R18.6.1 canonical
- class_proficiency new label required per ogni classe planned
- Runtime apply: DEFERRED to R18.3f + Apply Phase
- Anti-P2W: no premium items · no real-money shortcut · `can_be_sold_for_real_money=false` **forever**
- Slot canonical: no new slot · trinket RESERVED status invariato

## Sezione 9 · Piano Pilota Cacciatore del Vuoto

**Class slug**: `cacciatore_del_vuoto` · **Sala**: Faro Rovesciato di Onirade · **Hall Master**: Nael di Onirade · **Wave**: 1 #1 · **Status**: PROPOSAL · design layer only · NO live activation

### 9.1 · Stat Design Proposal
- **main_stat proposed**: **Intelligenza**
- **Rationale**: Il Cacciatore del Vuoto opera su bersagli incorporei/summon tramite dispel e marchi arcani. La sua efficacia deriva dalla precisione della conoscenza arcana (Intelligenza), non dalla forza bruta né dalla saggezza sacra (già occupata dal Paladino). Coerente con l'atmosfera del Faro Rovesciato (lanterna, silenzio arcano) e con Nael di Onirade (visione oltre l'acqua).
- **Alternatives considered**: {"Saggezza": "rifiutato: overlap con Paladino/futuri healer sacri", "Destrezza": "rifiutato: overlap con Cacciatore di Mostri (ranged agile)", "Forza": "rifiutato: incoerente con lore anti-incorporeo"}

### 9.2 · Proficiency Design Proposal
- **armor_proficiency proposed**: cuoio · stoffa
- **Armor rationale**: Ibrido tra mobilità (cuoio · vicinanza al Faro, movimento sull'acqua) e canalizzazione arcana (stoffa · dispel/marchi). Esclude maglia/piastre (troppo Guerriero/marziale · incoerente con lore Onirade). Cuoio+stoffa = whitelist unica tra le 27 · differenzia da tutte le 5 live.
- **weapon_proficiency proposed**: focus · pugnale · balestra
- **Weapon rationale**: focus (canalizzazione dispel/marchi · condivisa con Mago/Paladino ma diverso stat driver) · pugnale (melee opportunistico · condiviso con Ladro/Mago/Cacciatore di Mostri) · balestra (ranged silenzioso · condiviso con Ladro/Cacciatore di Mostri). Esclude arco (troppo Cacciatore di Mostri) · esclude bastone/tomo (troppo Mago) · esclude reliquia (troppo Paladino).
- **Weapon family RESERVED future**: lanterna (candidata come weapon_family PENDING PM · non attiva in R18.6.2 · possibile aggiunta al gate EQUIP_DESIGN)

### 9.3 · Gameplay Loop
| # | Phase | Action |
|:--:|---|---|
| 1 | **Identify** | Cacciatore individua target incorporeo/summon/anti-summon nel campo visivo del Faro |
| 2 | **Mark** | Applica Marchio del Vuoto sul target (dispel-over-time · silenzia summon) |
| 3 | **Drain** | Focus/balestra colpiscono il target marchiato · ogni colpo drena un Frammento di Vuoto dal target |
| 4 | **Payoff** | Frammenti accumulati permettono burst (spendi X Frammenti → dispel massivo di area o annullamento summon boss) |

**Target priority**: incorporei > summon nemici > caster > melee (order di preferenza narrativa e gameplay)

### 9.4 · Resource Mechanic Proposal
- **Candidates (PM directive)**: Marchi del Vuoto, Void Essence, Onirade Fragments
- **Recommended canonical name**: **Frammenti di Onirade**
- **Rationale**: Coerente con Hall lore (Faro Rovesciato di Onirade · Nael di Onirade) · italiano canonico Orbus · differenzia da 'essence' (troppo generico) e 'marchi' (già usati come sub-mechanic del loop step 2). I Marchi del Vuoto restano come sub-mechanic (debuff applicato al target) · i Frammenti di Onirade sono la risorsa accumulata dal Cacciatore.
- **Generation**: 1 Frammento per ogni colpo su target Marchiato · +1 bonus per dispel di summon nemico · +2 bonus per annullamento boss summon
- **Cap**: cap iniziale proposto 5 · scalabile con progressione classe (gate futuro)
- **Consumption**: spesa 3 Frammenti = dispel di area · spesa 5 Frammenti = annullamento boss summon (una-tantum per encounter)
- **Scope**: encounter-local · reset a fine dungeon/raid · non accumulabile fuori combattimento

### 9.5 · Bridge Legacy Analysis
- **Legacy class_proficiency existing**: NONE (nessun 'warlock' o 'void-hunter' esistente in R18.5 · 5 legacy live sono Warrior/Rogue/Mage/Priest/Ranger)
- **Canonical-new status**: cacciatore_del_vuoto è canonical-new · nessun bridge legacy · NO auto-derive · NO migration retroattiva
- **class_proficiency new label required**: 'VoidHunter' (proposta) o 'CacciatoreDelVuoto' (proposta alternativa) · decisione PM al gate PROFICIENCY_DESIGN
- **class_slug immutable from R18.6.1**: `cacciatore_del_vuoto (invariato)`

### 9.6 · Safe-Mode Trial Detailed
**Concept R18.6.1**: La Prova del Riflesso Vuoto — riconoscere il proprio riflesso nella lanterna rovesciata e non distoglierlo

**Obiettivi didattici**:
- insegnare focus (mantenere ambito · concentrazione)
- riconoscere target incorporeo (il riflesso è la prima 'preda' vuota)
- resistenza a effetti distraction (specchi ingannevoli del Faro)

**Meccaniche insegnate**: identificazione target · marchio base · resistenza distraction

**Restrizioni safe-mode**: NO death · NO consumo risorse rare · NO endgame drop · NO farmabile (una tantum per Recluta) · NO sostituisce tutorial generale

**Esiti attesi**:
- **Success**: Recluta riconosce il riflesso · Nael conferma prontezza · sblocca conferma classe
- **Fail-soft**: Recluta distoglie lo sguardo · Nael offre secondo tentativo (retry illimitato)

**Fallback design**: se il Recluta fallisce N volte, Nael racconta la lore per garantire comprensione senza penalty · nessun dismissal forzato

### 9.7 · Impact Registry v2
- **Current registry state**: Registry v2 LOCKED · 5 classi × 300 items = 1500 · nessun item per cacciatore_del_vuoto
- **Estimated new items needed**:
  - `armor_cuoio_stoffa_dedicated`: ~40 items (8 slot × 5 tier)
  - `weapon_focus_dedicated`: ~25 items (5 tier × 5 rarity)
  - `weapon_pugnale_dedicated`: ~15 items (shared con altre classi · gap analysis)
  - `weapon_balestra_dedicated`: ~15 items (shared con altre classi · gap analysis)
  - `trinket_void_focused`: ~10 items (nuova sub-categoria · flag)
  - `total_estimated_gap`: ~80-100 new items per set base Cacciatore del Vuoto
- **Future registry extension**: Registry v3 (additive) o extension modulare · gate futuro post-R18.5 lockdown · fuori scope R18.6.2
- **NO R18.5 modification** ✅ · **Anti-P2W preserved** ✅

### 9.8 · Risks Specific to Pilot Vuoto
| ID | Rischio | Severity | Mitigation |
|:--:|---|:--:|---|
| **VP-R1** | Sovrapposizione weapon proficiency con Ladro/Mago (pugnale/focus/balestra) genera confusione player | MEDIUM | differentiation via main_stat (Intelligenza) + resource mechanic unica (Frammenti di Onirade) + gameplay loop distintivo (Mark → Drain) |
| **VP-R2** | Armor 'cuoio + stoffa' è whitelist unica · potenziale complessità implementativa validator | LOW | validator C2 #6 supporta whitelist multi-armor · already designed |
| **VP-R3** | Risorsa 'Frammenti di Onirade' collide narrativamente con eventuale futuro sistema Onirade (world lore) | LOW-MEDIUM | Frammenti sono meccanica classe-locale · Onirade come regione narrativa resta separata · PM può rinominare in gate RESOURCE_MECHANIC review |
| **VP-R4** | 80-100 new items richiedono Registry v3 · possibile ritardo Wave 1 completion | MEDIUM | gate EQUIP_DESIGN produce gap analysis · Registry v3 può essere additivo modulare (non blocca R18.5 lockdown) |
| **VP-R5** | Prova del Riflesso Vuoto richiede asset UI 'specchio/riflesso' non presente nel toolkit Orbus testuale | LOW | design testuale MMO gestionale · prova narrata + micro-encounter descrittivo · nessun asset grafico |
| **VP-R6** | Bridge legacy assente · possibile percezione 'classe orfana' dai player Round 16.x | LOW | communication: classe canonical-new post-R18.6.1 · lore narrativo dedicato (Nael di Onirade · Ombra di Onirade lore hook) |
| **VP-R7** | Faro Rovesciato è off-site (isolotto lago Gilda) · accesso via Atrio Vocazioni (Q8 architecture) richiede portale/percorso · impact UX | LOW-MEDIUM | Q8 architettura HUB approvata · portale/percorso dedicato in design layer · implementazione tecnica gate futuro |
| **VP-R8** | Interazione con Progressive Discovery Legendary P1-P4 (attualmente HOLD) · possibile overlap con futuri set legendary void | LOW | Progressive Discovery separato · gate PM dedicato post-C6 · no cross-contamination |

### 9.9 · PM Open Questions Pilot Vuoto (V-Q1..V-Q8)
- **V-Q1** · *main_stat Intelligenza confermato o alternativo (Saggezza · rebalancing con Paladino)?*
  - a) confermo Intelligenza
  - b) Saggezza con rebalancing Paladino
  - c) proponi altra
- **V-Q2** · *armor whitelist [cuoio + stoffa] · confermata o restringere a solo cuoio (più cacciatore-like)?*
  - a) confermo cuoio+stoffa
  - b) solo cuoio
  - c) solo stoffa
- **V-Q3** · *weapon whitelist [focus, pugnale, balestra] · aggiungo 'lanterna' come RESERVED family (canonizzata al gate EQUIP_DESIGN)?*
  - a) confermo 3 attuali
  - b) aggiungi lanterna RESERVED (implementazione futura)
  - c) rimuovi pugnale (troppo overlap)
- **V-Q4** · *Nome risorsa: 'Frammenti di Onirade' vs 'Marchi del Vuoto' vs 'Void Essence'?*
  - a) confermo 'Frammenti di Onirade'
  - b) 'Marchi del Vuoto' (deprezza sub-mechanic)
  - c) 'Void Essence' (troppo inglese)
  - d) proponi altro nome canonico
- **V-Q5** · *Registry v3 (extension additiva) per 80-100 new items · GO planning ora o gate futuro dedicato?*
  - a) planning ora in R18.6.2 sub-doc
  - b) gate futuro dedicato (Registry v3 dispatch separato)
  - c) reuse items shared da 5 classi live (compromesso)
- **V-Q6** · *Faro Rovesciato accesso via Atrio Vocazioni · portale magico vs percorso navigabile (barca/ponte)?*
  - a) portale magico (istantaneo · lore arcano)
  - b) percorso navigabile (barca sul lago)
  - c) mix (portale al primo ingresso · barca successivi)
- **V-Q7** · *Prova del Riflesso Vuoto · retry policy illimitato o cap (evita farming safe-mode)?*
  - a) retry illimitato (no farming perché no reward)
  - b) cap 3 tentativi + cooldown 24h reali
  - c) cap 5 tentativi senza cooldown
- **V-Q8** · *Cacciatore del Vuoto come first pilot conferma anche schema di readiness per Wave 1 successivo (Monaco)?*
  - a) sì · framework universale confermato dopo pilot
  - b) rivedere framework dopo pilot Vuoto
  - c) framework case-by-case

## Sezione 10 · Risk Register Framework (10)

| ID | Rischio | Severity | Mitigation |
|:--:|---|:--:|---|
| **F-R1** | Framework universale troppo rigido · alcune classi PLANNED (creative/systemic) non fittano il pattern | MEDIUM | framework è baseline · ogni gate può avere sub-varianti case-by-case · Wave 4 (creative) può richiedere gate aggiuntivi |
| **F-R2** | 22 classi × 10 gate = 220 gate PM · overhead review | MEDIUM | wave-based batching · alcuni gate parallelizzabili · PM può delegare sub-review |
| **F-R3** | Registry v3 (extension additiva) inevitabile · possibile drift da R18.5 lockdown | HIGH-INFO | R18.5 lockdown preservato · Registry v3 additivo modulare · non riscrive R18.5 |
| **F-R4** | Bridge legacy assente per 22/22 classi PLANNED · richiede canonical-new labels | LOW-MEDIUM | translation layer R18.3f estende immutable lookup 5→27 · design coerente |
| **F-R5** | Anti-P2W preservation su 22 classi × 100 items = 2200 nuovi items · audit complesso | MEDIUM | gate EQUIP_DESIGN include anti-P2W check obbligatorio · can_be_sold_for_real_money=false enforced 100% |
| **F-R6** | Rite of Rebirth verso classe non ancora ACTIVE → design constraint | MEDIUM | Rite of Rebirth constraint Q3 R18.6.1: solo target ACTIVE-DESIGN-READY · no PLANNED |
| **F-R7** | Class_slug immutable mapping potrebbe cambiare durante readiness (es. rename) | LOW | R18.6.1 slug canonical LOCKED · rename Hall Master già gestito via PRD errata (Ambrose→Orien · Sylas→Marek) |
| **F-R8** | Pilot Vuoto proposta stat/prof non convincente PM · rework necessario | MEDIUM | V-Q1-Q8 questions permettono iterazione · gate STAT_DESIGN + PROFICIENCY_DESIGN sono PM gate espliciti |
| **F-R9** | Cavaliere di Draghi readiness (Wave 3 #15) richiederà integration Stables · complessità elevata | HIGH-INFO | framework include tech_readiness gate · Cavaliere di Draghi avrà sub-gate integrazione Stables dedicato |
| **F-R10** | R18.6.2 documento accidentalmente modifica R18.6.1 LOCKED | HIGH-BLOCK | R18.6.2 legge R18.6.1 read-only · file R18.6.1 non toccati · sealed integrity test copre |

## Sezione 11 · PM Open Questions Framework (F-Q1..F-Q5)

- **F-Q1** · *Framework 10-gate confermato o proposta di semplificazione?*
  - a) confermo 10 gate
  - b) merge alcuni gate (proponi quali)
  - c) 10 gate + sub-gate per Wave 4 creative
- **F-Q2** · *Wave 1 sequence dopo Vuoto: Monaco next o riordinare?*
  - a) Monaco next (verbatim PM Q2)
  - b) riordinare Wave 1 in base a feedback pilot Vuoto
  - c) parallelizzare 2-3 classi Wave 1 dopo Vuoto
- **F-Q3** · *Registry v3 dispatch: attesa fine Wave 1 (6 classi ready) o kickoff subito dopo Vuoto?*
  - a) attesa fine Wave 1 (batch efficiente)
  - b) kickoff subito dopo Vuoto (early integration)
  - c) parallel dispatch (Registry v3 in parallelo a Wave 1 progression)
- **F-Q4** · *Sigillo di Rinascita (Q3 R18.6.1): design gameplay dedicato in R18.6.3?*
  - a) sì · R18.6.3 dispatch dedicato
  - b) integrare in R18.3f
  - c) gate futuro post-Wave 1
- **F-Q5** · *Player-facing guide per 27 classi (una volta tutte ACTIVE): lingua solo italiana o preparazione i18n?*
  - a) solo italiana (canonical)
  - b) prepare i18n structure (deferred fill)
  - c) hybrid (italiano canonical · UI-only i18n key hooks)

## Sezione 12 · Wave 1 Recommendation

**Ordine verbatim PM**: cacciatore_del_vuoto → monaco → druido → alchimista → bardo → negromante

**Post-Vuoto progression plan**:
- `step_1_pilot_vuoto`: R18.6.2 propose · PM review · GO gate STAT_DESIGN → PROFICIENCY_DESIGN → ... → PM_REVIEW · attivazione ACTIVE-DESIGN-READY
- `step_2_monaco`: R18.6.3? (dispatch separato dopo Vuoto ACTIVE) · framework applicato · main_stat probabilmente Destrezza · armor stoffa/cuoio · weapon unarmed/bastone
- `step_3_druido`: R18.6.4? · main_stat Saggezza (probabile) · armor cuoio · weapon bastone/naturale · shapeshift design richiede integrazione tecnica
- `step_4_alchimista`: R18.6.5? · main_stat Intelligenza · armor stoffa · weapon bastone/focus/consumable-throwable · crafting integration
- `step_5_bardo`: R18.6.6? · main_stat Saggezza/Intelligenza · armor cuoio/stoffa · weapon strumento (RESERVED family Q7 R18.6.1) · performance mechanic
- `step_6_negromante`: R18.6.7? · main_stat Intelligenza · armor stoffa · weapon bastone/tomo · summon undead mechanic · integration con evocazioni dark

**Parallelization option**: Wave 1 può essere parallelizzata dopo pilot Vuoto (2-3 classi in review simultanea) · gate PM può gestire multipli · risk: sovrapposizione review

**Wave 2 dispatch**: Wave 2 dispatch dopo Wave 1 completamente ACTIVE (6/6) · gate PM per apertura Wave 2 · non prima

**No wave skip**: ✅

---

## Governance Snapshot R18.6.2

| Voce | Stato |
|---|:--:|
| Documental only regime | ENFORCED ✅ |
| Italian output | ENFORCED ✅ |
| 36 sealed files byte-identical | ✅ |
| `lore_meta.py` INVARIATO (`a18f708b…`) | ✅ |
| DB writes / code changes / migrations | 0 / 0 / 0 ✅ |
| R18.5 / R18.6 / R18.6.1 modification | 0 / 0 / 0 ✅ (LOCKED) |
| Cacciatore del Vuoto live activation | BLOCKED ✅ |
| 22 PLANNED unlock | BLOCKED ✅ |
| class_slug auto-derivation | BLOCKED ✅ |
| Anti-P2W preserved | ✅ |
| Deliverable files | 2 (`.md` + `.json`) |
| Sezioni scope | **12 / 12** ✅ |

---

## 🛑 STOP after R18.6.2 design + PRD append R18.6.1 CLOSED

**Non procedere oltre senza nuovo GO PM esplicito.**

Attendo PM review + risposte a **F-Q1..F-Q5** (framework) + **V-Q1..V-Q8** (pilot Vuoto) prima di qualunque handoff verso:
- Cacciatore del Vuoto STAT_DESIGN gate (unlock start)
- Monaco / Druido / Alchimista / Bardo / Negromante (Wave 1 successivo)
- Wave 2/3/4 activation
- R18.3f Class Slug Migration Readiness
- Apply Phase
- Registry v3 dispatch
- Progressive Discovery finalization
- Marketing Brief
