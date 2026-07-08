# R18.5 — Phase C2 · Proficiency Runtime Preparation

**Round**: R18.5 · **Phase**: C2 Proficiency Runtime Preparation
**Locked at UTC**: `2026-07-07T20:45:00Z`
**Governance**: **DOCUMENTAL ONLY — design preparation. NO code/DB/migrations/runtime apply.**
**Status**: ✅ **APPLIED — design layer preparation per PM review**
**Authority**: PM Orchestrator — Phase C2 dispatch
**Lingua output**: 🇮🇹 SOLO ITALIANO

**Deliverables**:
- `/app/memory/r18_5_phase_c2_proficiency_runtime_preparation.md` (questo file)
- `/app/memory/r18_5_phase_c2_proficiency_runtime_preparation.json` (SHA256 `7c7b83ef65d902e43d81d79d5418d198541abbce7a9cb701846d232bc9ce2bba`)

---

## 1. Executive Summary

Preparare il design documentale per il futuro runtime enforcement di proficiency, anti-P2W, class_slug e Legendary utility caps. Nessuna implementazione runtime in questa fase.

**Scope in**:
- Proficiency maps canoniche (5 classi)
- Equip eligibility validator design (pseudo-logica)
- Lock-state matrix 10 stati
- UI state mapping
- class_slug null handling design
- recruit_unassigned handling design
- progressive_marker handling (10 items)
- Legendary runtime cap design (5 MEDIUM cases)
- Risk register
- GO/HOLD recommendation per C3
- PM open questions

**Scope out** (deferito a fasi successive):
- Implementazione runtime engine (deferred)
- class_slug migration apply (C5)
- Anti-P2W runtime validator implementation (C-fase futura)
- Drop table apply (C4)
- Live DB writes / seed / migration

**Key metrics output**:

| Metrica | Valore |
|---|:--:|
| `proficiency_maps_classes` | 5 |
| `validator_decision_flow_steps` | 10 |
| `validator_case_matrix_rows` | 10 |
| `lock_states` | 10 |
| `ui_state_mappings` | 10 |
| `progressive_marker_items` | 10 |
| `legendary_cap_cases` | 5 |
| `risks_tracked` | 10 |
| `pm_open_questions` | 8 |

---

## 2. Proficiency Map · Classe → Armor · Classe → Weapon

_Proficiency maps CANONICHE — verbatim da direttiva PM STEP 2. Nessuna eccezione implicita ammessa._

| Classe | main_stat | armor whitelist | weapon whitelist |
|:--:|---|---|---|
| **Warrior** | Forza (STR) · label IT: Forza | maglia · piastre | spada · ascia · martello · scudo · lancia · arma_in_asta |
| **Rogue** | Destrezza (AGI) · label IT: Destrezza | cuoio | pugnale · spada · balestra |
| **Mage** | Intelligenza (INT) · label IT: Intelligenza | stoffa | bastone · tomo · focus · pugnale |
| **Priest** | Saggezza (WIS) · label IT: Saggezza | stoffa | bastone · martello · focus · reliquia |
| **Ranger** | Destrezza (AGI) · label IT: Destrezza | cuoio · maglia | arco · balestra · spada · pugnale · lancia |

### Invarianti proficiency

- Priest NO scudo · NO piastre · NO cuoio · NO maglia (solo stoffa)
- Rogue NO arco · NO piastre · NO maglia · NO stoffa (solo cuoio)
- Warrior NO stoffa · NO cuoio (solo maglia/piastre)
- Mage NO piastre · NO maglia · NO cuoio (solo stoffa)
- Ranger NO piastre · NO stoffa (solo cuoio/maglia); arco esclusivo Ranger
- focus off-hand condiviso Mage+Priest (main_stat filtra ownership)
- spada condivisa Warrior+Rogue+Ranger (armor filtra ownership)
- pugnale condiviso Rogue+Mage+Ranger (main_stat filtra ownership)
- trinket = cross-class (main_stat_target Ranger-oriented per Legendary H4 Halodi)


---

## 3. Equip Eligibility Validator Design (pseudo-logica)

_Pseudo-logica documentale per la validazione equip-eligibility. NON è codice runtime._

### Input contract

**Adventurer**: `adventurer_id · class_slug (nullable) · class_proficiency (canonical W/R/M/P/Ranger, nullable if recruit_unassigned) · level`

**Item**: `item_id · class_proficiency · armor_type · weapon_family · slot · required_level · rarity · registry_status · progressive_marker · runtime_apply_ready · can_be_sold_for_real_money · is_cosmetic`

### Decision flow (10 step ordered)

| # | Check | Action / lock_state |
|:--:|---|---|
| **1** | `runtime_apply_ready == false` | return lock_state=`locked_runtime_not_ready` — item is design layer only, blocca in dry-run. |
| **2** | `registry_status == 'reserved'` | return lock_state=`locked_reserved_placeholder` — Progressive Discovery P1-P4 non equipaggiabili. |
| **3** | `adventurer.class_slug is None AND adventurer.class_proficiency is None` | return lock_state=`locked_recruit_unassigned` — recruit senza classe assegnata (Sala di Classe R18.6). |
| **4** | `adventurer.class_slug is None (ma class_proficiency canonical presente)` | return lock_state=`locked_class_slug_null` — bridge C5/R18.3f pending. NO auto-derivazione da class_proficiency. |
| **5** | `item.is_cosmetic == True OR slot in {'trinket-universal','consumable','material'}` | return lock_state=`universal_allowed` — bypass proficiency check (marker `universal_allowed` per registry v2 v_class_bindfree). |
| **6** | `item.armor_type is not None AND item.armor_type not in PROFICIENCY_MAPS[class].armor` | return lock_state=`locked_proficiency_armor` — armor_type non in whitelist classe. |
| **7** | `item.weapon_family is not None AND item.weapon_family not in PROFICIENCY_MAPS[class].weapon_families` | return lock_state=`locked_proficiency_weapon` — weapon_family non in whitelist classe. |
| **8** | `adventurer.level < item.required_level` | return lock_state=`locked_level` — livello insufficiente. |
| **9** | `item.progressive_marker == True` | return lock_state=`equippable` MA con flag `narrative_marker=true` (marker T4 hint verso T5, gear normale Epic — no restrizioni extra). |
| **10** | `all checks passed` | return lock_state=`equippable`. |

### 10-case matrix (verifica esaustiva casi PM)

| case_id | condition | lock_state | severity | note |
|:--:|---|:--:|:--:|---|
| **1** | class_slug null | `locked_class_slug_null` | HIGH-BLOCK | NO auto-derive · bridge C5/R18.3f required |
| **2** | class_slug valido + compatibile | `equippable` | OK | flusso normale |
| **3** | armor_type incompatibile | `locked_proficiency_armor` | HARD | Priest no piastre, Rogue no maglia, ecc. |
| **4** | weapon_family incompatibile | `locked_proficiency_weapon` | HARD | Rogue no arco, Warrior no bastone, ecc. |
| **5** | required_level > adventurer.level | `locked_level` | MEDIUM | sblocco progressione naturale |
| **6** | progressive_marker == true | `equippable (narrative_marker)` | OK | T4 hint items = Epic gear normale, marker cosmetico/narrativo |
| **7** | Legendary reserved placeholder (P1-P4) | `locked_reserved_placeholder` | HARD | NOT in registry finché PM finalizza |
| **8** | runtime_apply_ready == false | `locked_runtime_not_ready` | HARD | STATO CORRENTE 1500/1500 in dry-run |
| **9** | universal / material / consumable | `universal_allowed` | OK | bypass proficiency check |
| **10** | can_be_sold_for_real_money == false | `n/a (invariante anti-P2W)` | INFO | 1500/1500 already compliant; validator anti-P2W runtime separato (out-of-scope C2) |

**No runtime bridge**: NO auto-bridge da class_proficiency a class_slug. NO fallback silente. NO migration on-the-fly. Ogni lock_state richiede risoluzione esplicita da C5/R18.3f/R18.6.

---

## 4. Lock-State Matrix (10 stati)

| lock_state | causa | ui_message_it | equip_behavior | severità | future_phase |
|---|---|---|---|:--:|:--:|
| `equippable` | tutti i check passati | Equipaggiabile. | consenti equip | OK | — |
| `locked_class_slug_null` | adventurer.class_slug è null (ma class_proficiency presente) | Classe non ancora migrata. Attendi aggiornamento sistema classi (R18.3f). | blocca; disabilita bottone Equipaggia | HIGH-BLOCK | C5 · R18.3f |
| `locked_recruit_unassigned` | adventurer senza classe (Recluta / Senza Classe) | Assegna una Sala di Classe per poter equipaggiare questo oggetto. | blocca; propone tutorial R18.6 Class Halls | HIGH-BLOCK | R18.6 |
| `locked_proficiency_armor` | armor_type non in whitelist classe | La tua classe non può indossare questa tipologia di armatura. | blocca hard | HARD | — |
| `locked_proficiency_weapon` | weapon_family non in whitelist classe | La tua classe non può impugnare quest'arma. | blocca hard | HARD | — |
| `locked_level` | adventurer.level < item.required_level | Livello richiesto: {required_level}. Sali di livello per equipaggiare. | blocca; tooltip mostra gap | MEDIUM | — |
| `locked_reserved_placeholder` | Progressive Discovery placeholder (P1-P4) — registry_reserved | Oggetto ancora in fase di scoperta. Contenuto futuro. | invisibile in inventario runtime (o mostrato come `?????` narrativo) | HARD | C0.L progressive finalization / post-review |
| `locked_runtime_not_ready` | runtime_apply_ready=false (design layer) | N/A (invisibile all'utente in questa fase; è invariante di sistema mentre l'engine runtime non è abilitato) | l'item non viene proposto in inventario finché runtime non è enabled | HARD (invariante di fase) | C2/C3/C4 runtime enablement pipeline |
| `locked_unknown_item_type` | item_id non nel registry o campi obbligatori mancanti | Oggetto non riconosciuto. Riporta il problema al Supporto. | blocca; log warning telemetry (design) | MEDIUM (safety net) | — |
| `universal_allowed` | is_cosmetic=true OR slot=universal/material/consumable | Equipaggiabile / utilizzabile da qualsiasi classe. | consenti; bypass proficiency check | OK | — |


---

## 5. UI State Mapping

| lock_state | ui_badge | cta_visible | tooltip_it |
|---|---|:--:|---|
| `equippable` | verde · icona check | ✅ | Equipaggiabile |
| `locked_class_slug_null` | grigio · icona ingranaggio | ❌ | In attesa di migrazione sistema classi |
| `locked_recruit_unassigned` | ambra · icona porta | ❌ | Assegna Sala di Classe |
| `locked_proficiency_armor` | rosso · icona scudo barrato | ❌ | Armatura non compatibile |
| `locked_proficiency_weapon` | rosso · icona spada barrata | ❌ | Arma non compatibile |
| `locked_level` | giallo · icona livello | ❌ | Livello richiesto: {required_level} |
| `locked_reserved_placeholder` | viola · icona ????? | ❌ | Contenuto futuro |
| `locked_runtime_not_ready` | (nascosto in questa fase) | ❌ | N/A (invariante dry-run) |
| `locked_unknown_item_type` | grigio · icona warning | ❌ | Oggetto non riconosciuto |
| `universal_allowed` | blu · icona globo | ✅ | Utilizzabile da qualsiasi classe |


---

## 6. class_slug null handling / Recruit Unassigned

**Regola PM verbatim**: class_slug = null NON deve essere auto-derivato.

**Divieti (nessuna eccezione)**:
- ❌ nessuna auto-derivazione da class_proficiency
- ❌ nessun runtime bridge
- ❌ nessuna migration on-the-fly
- ❌ nessun apply (né documentale né live)


### Design "Senza Classe / Recluta"

Avventurieri senza classe nel design 'Senza Classe / Recluta' (recruit_unassigned):

**Permessi**:
- ✅ può esistere nel roster
- ✅ può essere visualizzato
- ✅ può ricevere prompt/tutorial
- ✅ può ricevere onboarding narrativo

**Vietati**:
- ❌ non può equipaggiare gear specializzato
- ❌ non può essere considerato pienamente pronto per dungeon/raid
- ❌ deve scegliere una Sala di Classe in R18.6 prima di full-progression

**Phase di risoluzione tecnica**:
- 🔒 C5 — Class Slug Migration Prep / R18.3f Readiness
- 🔒 R18.6 — Class Halls · Classless Start · Adventurer Identity


**Current state snapshot**:
- `class_slug null count`: 1500/1500 ✅
- `class_slug_resolution_status`: `deferred_to_C5_R18_3f` 1500/1500 ✅
- `adventurer recruit_unassigned handling`: documentato in C2, risoluzione live in R18.6

---

## 7. progressive_marker handling (10 items)

- **Count approvato**: **10** (Q4=B risolto in C1 CLOSED review: `progressive_marker` count corrected/approved at **10** (source-of-truth C0.L Sezione 3.6, pattern `*-t4-legendary-*-hint`).)

### Regole C2 (nessuna promozione, nessuna esclusione, no runtime)
- NON trasformare i marker in Legendary — restano rarity=Epic invariata
- NON promuovere a T5 — restano tier=T4
- NON escluderli dal registry dry-run — sono `registry_status=progressive_marker`
- NON renderli runtime_apply_ready — restano `runtime_apply_ready=false`
- Trattarli come marker narrativi/meccanici verso T5 Legendary corrispondente (teaser design intent)
- In validator: `equippable` con flag `narrative_marker=true` (Epic gear normale, no restrizioni extra proficiency)
- UI: tooltip narrativo 'Anticipa un oggetto leggendario futuro' opzionale (design solo, no implementazione)

### 10 items flaggati (`progressive_marker=true`)

- `warrior-t4-legendary-emberking-crown-hint`
- `warrior-t4-legendary-void-touched-hint`
- `rogue-t4-legendary-void-touched-hint`
- `rogue-t4-legendary-soul-abyss-hint`
- `mage-t4-legendary-celestial-halo-hint`
- `mage-t4-legendary-void-warlock-hint`
- `priest-t4-legendary-celestial-halo-hint`
- `priest-t4-legendary-resurrect-hint`
- `ranger-t4-legendary-worldroot-hint`
- `ranger-t4-legendary-emberking-crown-hint`


---

## 8. Legendary Runtime Cap Design (5 casi MEDIUM)

**Principio governance PM**: Gli effetti Legendary sono APPROVATI come design ma NON sono runtime-ready. NESSUN cap deve essere applicato ora. C2 documenta il cap design per PM review e futura Phase runtime enablement.

### #1 — Void-Pierce · `rogue-t5-legendary-void-touched-blade` (APPROVED-7 (L2))

| Campo | Valore |
|---|---|
| **utility_summary** | passive proc on-hit 15% chance di ignorare armor del target |
| **cap_tecnico_proposto** | max 1 proc per round (anche se più attacchi vengono effettuati nel round) |
| **cooldown_proposto** | N/A (passive) — cap round-based è il gate |
| **stack_limit** | 1 stack unico (nessun refresh se già proc'd nel round) |
| **limitazione_pve** | attiva solo su target con `armor > 0` (bypass no-op su mob armor=0) |
| **comportamento_boss** | attiva; boss raid endgame con armor >= threshold prendono damage bypass. NON overturned in tuning perché 15% chance già bilanciata. |
| **failure_case** | attacchi off-hand / DoT non triggano proc (only main-hand hit) |
| **ui_note_it** | Notifica 'Perforazione del Vuoto attiva' su proc; nessuna barra CD (passive). |
| **rischio_exploit** | **MEDIUM — potenziale con attack-speed boost + Focus Fire → cappato da round-based** |
| **recommendation_pm** | OK con cap 1 proc/round. Valutare telemetria proc rate nei primi raid endgame. |

### #2 — Divine Resurrect · `priest-t5-legendary-seraph-halo-crown` (APPROVED-7 (L3))

| Campo | Valore |
|---|---|
| **utility_summary** | 1x/encounter resurrect di 1 fallen ally con 50% max HP, 3s cast time |
| **cap_tecnico_proposto** | 1 utilizzo per encounter · target = 1 fallen ally (last_death_ts within encounter window) |
| **cooldown_proposto** | 1x/encounter (rebirth cooldown ~3s cast time, no interrupt-safe) |
| **stack_limit** | N/A (unique effect) |
| **limitazione_pve** | solo party members within same encounter tag; NO cross-encounter (es. raid → dungeon 3p) revives |
| **comportamento_boss** | attivo · nessuna restriction su boss raid; però meta-impact su encounter recovery — PM review meta obbligatoria |
| **failure_case** | target fallen ma reset da wipe > 30s post-encounter-end = no target valido; NO auto-cast on self |
| **ui_note_it** | Bottone 'Divina Resurrezione' visibile solo se >=1 fallen ally nel party; barra 3s cast con interrupt indicator. |
| **rischio_exploit** | **HIGH (design) — permette 'raid saves' e riduce wipe pressure endgame. PM può decidere gate su top-tier raid.** |
| **recommendation_pm** | MEDIUM RISK · consenti in encounter attivi PER ORA. Considerare in R18.6+ un ranking `raid_leaderboard` che tracci `divine_resurrect_used` per fairness competitive. |

### #3 — Reforge weapon slot mid-encounter · `warrior-t5-legendary-ambash-forge-hammer` (APPROVED-7 (L5))

| Campo | Valore |
|---|---|
| **utility_summary** | 1x/encounter cambia damage type dell'arma di un alleato (physical↔elemental) per 3 turni |
| **cap_tecnico_proposto** | 1 utilizzo per encounter · target = 1 ally in party (raid o dungeon 3p) · target consent runtime opt-in |
| **cooldown_proposto** | 1x/encounter · durata effetto 3 turni |
| **stack_limit** | 1 stack unico su target (no double-reforge) |
| **limitazione_pve** | target ally deve essere in same encounter; NO cross-target NPC/pet |
| **comportamento_boss** | cambia damage type su weapon ally; utile contro boss con resistenza specifica. Nessun bypass elemental cap boss (resistance elemental sub-max) |
| **failure_case** | target rifiuta consent (runtime opt-in flag) → utility fallita, cooldown consumato? OPEN QUESTION |
| **ui_note_it** | Bottone 'Riforgia Arma Alleato' con target picker; tooltip 'l'alleato deve accettare'. |
| **rischio_exploit** | **MEDIUM — cross-target buff manipolabile (troll consent-deny). Cap consent-based è il gate.** |
| **recommendation_pm** | CONSENT REQUIRED. In runtime: se target rifiuta, cooldown NON consumato (design fair). PM review per default consent behavior (opt-in vs auto-accept in guild members). |

### #4 — Absence Distortion · `mage-t5-legendary-ergolat-obelisk-focus-hybrid` (HYBRID-4 (H3))

| Campo | Valore |
|---|---|
| **utility_summary** | 1x/encounter AoE silence area 8m per 2 turni |
| **cap_tecnico_proposto** | 1 utilizzo per encounter · durata 2 turni · target ground area 8m radius · boss/elite immune (silence-resistance) |
| **cooldown_proposto** | 1x/encounter · 2 turni durata |
| **stack_limit** | N/A (unique AoE) |
| **limitazione_pve** | trash mob = silence full; elite = silence 50% durata; boss = silence resistance flag = true (no-op) |
| **comportamento_boss** | no-op su raid boss (silence resistance). Su dungeon 3p mini-boss = silence 50% durata (bilanciamento). |
| **failure_case** | target ground senza mob in radius = utility fallita, cooldown consumato |
| **ui_note_it** | Bottone 'Distorsione dell'Assenza' con AoE targeter 8m; tooltip 'inefficace su boss'. |
| **rischio_exploit** | **LOW dopo cap boss/elite immune (silence-resistance).** |
| **recommendation_pm** | OK con cap boss immune. PM decide se elite=50% durata o full immune. Preferenza design: 50% durata (utility ancora rilevante). |

### #5 — Fate Deflection · `ranger-t5-legendary-halodi-fate-quiver-hybrid` (HYBRID-4 (H4))

| Campo | Valore |
|---|---|
| **utility_summary** | 1x/encounter auto-reactive: next lethal hit deviato su bersaglio nemico casuale |
| **cap_tecnico_proposto** | 1 utilizzo per encounter · auto-triggered on damage that would reduce HP<=0 · target = random alive enemy in encounter |
| **cooldown_proposto** | 1x/encounter · auto-reactive next lethal hit |
| **stack_limit** | N/A (auto-reactive single-shot) |
| **limitazione_pve** | richiede almeno 1 alive enemy in encounter; se lethal source = boss single-target senza add → deflection no-op (auto-consumed but no effect on boss) |
| **comportamento_boss** | raid boss single-target no-add: deflection auto-consumed, damage NON absorbed (Ranger muore). Con add presenti: deflect su random add. Alt design: deflect su boss self = 0 damage (immunity design intent). |
| **failure_case** | encounter senza altre entità = deflection consumata ma nessun effetto; Ranger muore comunque |
| **ui_note_it** | Barra 'Deviazione del Fato: pronta' → 'Deviazione del Fato: consumata' post-trigger; log encounter '{damage} deviato su {target}'. |
| **rischio_exploit** | **MEDIUM — permette 'survival save' endgame. Cap auto-reactive è naturale. Governance: no-op boss single-target è il gate contro exploit.** |
| **recommendation_pm** | CHOOSE: (A) deflection no-op se solo boss = Ranger muore; (B) deflection su boss self assorbita = immunity endgame (overturned?). Raccomandazione design: **A** (fair, non overturned). |



---

## 9. Risk Register

| ID | Rischio | Severità | Mitigazione | Status |
|:--:|---|:--:|---|:--:|
| **R1** | class_slug null auto-derivation temptation | HIGH-BLOCK | regola PM verbatim NO auto-derive; risoluzione C5/R18.3f | MITIGATED (documental) |
| **R2** | recruit_unassigned adventurers senza classe possono equipaggiare gear specializzato | HIGH-BLOCK | lock_state=locked_recruit_unassigned + R18.6 Class Halls gate | DESIGNED |
| **R3** | 5 Legendary MEDIUM utility runtime senza cap causerebbero exploit/overturned | MEDIUM | cap tecnici proposti in `legendary_runtime_caps` (documental only, non applicati) | DESIGNED per review PM |
| **R4** | progressive_marker items scambiati per Legendary T5 dagli utenti | LOW | UI badge distinto + tooltip narrativo 'Anticipa un oggetto leggendario futuro'; registry_status=progressive_marker chiaro | DESIGNED |
| **R5** | runtime_apply_ready=false su 1500/1500 potrebbe confondere QA in dry-run | INFO | documentazione C2 chiarisce invariante di fase; QA in dry-run non tocca l'engine live | DOCUMENTED |
| **R6** | HYBRID drop_rate 0.5% direzionale non definitivo potrebbe essere applicato prematuramente in C4 | MEDIUM | C4 Drop Table richiederà PM final decision su HYBRID drop_rate; C2 mantiene visibilità del pending | TRACKED |
| **R7** | Reforge (L5) cross-target consent-deny troll | MEDIUM | design: consent-deny → cooldown NON consumato (fair) | DESIGNED (PM review consent default) |
| **R8** | Divine Resurrect (L3) altera meta raid competitive | MEDIUM | raid_leaderboard tracking `divine_resurrect_used` (R18.6+) | TRACKED |
| **R9** | Fate Deflection (H4) su boss single-target no-add = feels bad | LOW-MEDIUM | design chiaro (no-op fair) + UI log encounter | DESIGNED (PM confirm A/B) |
| **R10** | class_proficiency canonical (Warrior/Rogue/Mage/Priest/Ranger) NON allineato con eventuali runtime slugs esistenti (es. 'warrior' lowercase) | MEDIUM | C5 Class Slug Migration Prep gestirà la normalizzazione; C2 usa canonical form documentale | DEFERRED to C5 |


---

## 10. GO/HOLD Recommendation

### Phase C3 ILVL + Backfill
- **Recommendation**: **GO — soggetto a PM approval esplicito post-C2 review**
- **Rationale**: C2 fornisce validator design + lock states + proficiency maps stabili. C3 ILVL backfill non richiede runtime enablement (rimane design layer). class_slug null non è blocker per ILVL (invariante indipendente).

**Conditions richieste**:
- PM approval C2 (Q1-Q8)
- 5 Legendary utility caps approvati o soft-lock (design only, no apply)
- progressive_marker=10 mantenuto
- HYBRID drop_rate 0.5% direzionale confermato/differenziato pre-C4

**Risks se GO**:
- R10 (class_proficiency canonical vs runtime slugs) rimane in DEFERRED — nessun impatto C3
- R6 (HYBRID drop_rate) non impatta C3 ILVL (drop_rate è C4-scope)


### Fasi successive (HOLD)

- **C4 Drop Table** — HOLD post-C3 · HYBRID drop_rate PM final decision richiesto qui
- **C5 Class Slug Migration Prep** — HOLD post-C4 · class_slug null resolution formalizzata qui
- **C6 Final Closure** — HOLD post-C5
- **R18.6 Class Halls / Classless Start** — PLANNED post-Phase C · recruit_unassigned + Class Halls implementation

---

## 11. PM Open Questions post-C2

| ID | Topic |
|:--:|---|
| **Q1** | Approvare C2 Proficiency Runtime Preparation design (validator + lock states + maps + Legendary caps) come design layer input per runtime enablement futuro? |
| **Q2** | 5 Legendary MEDIUM utility caps proposti: accettare ora come design baseline (5/5) o affinare specifici (indicare quali e come)? |
| **Q3** | Divine Resurrect (L3): permettere in encounter attivi (design attuale) o gate su top-tier raid? Se gate, quale threshold? |
| **Q4** | Reforge (L5) cross-target consent: default = opt-in (target deve accettare) o auto-accept per guild members? |
| **Q5** | Absence Distortion (H3) su elite dungeon 3p: silence 50% durata (raccomandato) o full immune? |
| **Q6** | Fate Deflection (H4) su boss single-target no-add: (A) no-op fair (raccomandato) o (B) deflect su boss self = immunity? |
| **Q7** | class_slug null handling C2 documentato: confermare NO auto-derive + risoluzione differita a C5/R18.3f + recruit_unassigned differito a R18.6? |
| **Q8** | Autorizzare Phase C3 ILVL + Backfill con condizioni GO documentate in `go_hold_recommendation.phase_c3_ilvl_backfill`? |


---

## 12. Governance Check C2

| Voce | Stato |
|---|:--:|
| `sealed` | VERIFIED pytest 6/6 (post STEP 1 PRD append + STEP 2 C2 draft) |
| `db_writes` | ZERO |
| `code_changes` | ZERO |
| `migrations` | ZERO |
| `item_creation_live` | ZERO |
| `registry_apply` | ZERO |
| `registry_generation_live` | ZERO |
| `drop_table_apply` | ZERO |
| `economy_changes` | ZERO |
| `lore_meta_py_touch` | ZERO (invariato) |
| `sealed_file_modification` | ZERO |
| `hard_delete` | ZERO |
| `runtime_bridge` | ZERO |
| `class_slug_migration_apply` | ZERO |
| `class_slug_auto_derivation` | ZERO (rule PM verbatim) |
| `proficiency_runtime_enforcement_implementation` | ZERO (design only) |
| `anti_p2w_runtime_validator_implementation` | ZERO (design only) |
| `c3_auto_start` | BLOCKED (STOP after C2 per direttiva PM) |
| `r18_6_kickoff` | BLOCKED (PLANNED) |
| `marketing_brief` | BLOCKED (DEFERRED) |
| `classi_canoniche` | Warrior/Rogue/Mage/Priest/Ranger — NO drift |
| `italian_language_output` | ENFORCED |
| `documental_only_regime` | ENFORCED |
| `files_deliverable` | 2 (.md + .json) |


---

## Stop after C2

- **`auto_transition_c3`**: `false`
- **Nota**: **STOP dopo C2. Attendo PM review Q1-Q8 + GO esplicito prima di C3 ILVL + Backfill.**
