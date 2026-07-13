# R18.6.RV3-IS2-B Phase 1 · Stat Budget & Mechanical Effect Contract

**Gate**: `R18.6.RV3-IS2-B Phase 1 · Stat Budget & Mechanical Effect Contract`
**Regime**: DOCUMENTAL ONLY · READ-ONLY · NO APPLY
**Stato**: **ARTIFACT WRITTEN** · **PM ADJUDICATION REQUIRED** · **FORMAL CLOSURE HOLD**
**Baseline consumata (read-only)**: R18.5 Itemization · CdV G1-G5 · AFX1 · IC1 · IS1 · IS2-A Phase 1 · IS2-A Phase 2 Rev-4 · IS2-A-L1
**Lingua**: Italiano
**Regola cardine**: definire il **contratto** (come assegnare) senza fissare valori numerici item-by-item né effetti finali.

---

## 1. Executive summary

Phase 1 di IS2-B consegna il **contratto di stat budget** e la **taxonomy meccanica** che governeranno l'assegnazione futura di stat, coefficienti, budget e effetti ai 111 nomi attivi del corpus (108 non-Legendary selected + 3 Legendary PM-selected). Il contratto stabilisce **come** allocare, non **quanto**. Ogni valore numerico item-by-item (main stat concreto, coefficient finale, effetto finale, proc, durata) resta `null` in Phase 1. Le scelte residue con impatto sistemico (coefficient balestra/pugnale, slot budget bands, stacking, rounding, direction Legendary) sono raccolte come **PM open questions** nella §55.

## 2. Scope

- **In scope**: main-stat contract · secondary-stat contract · tier budget architecture · rarity budget architecture · affix budget boundary · utility budget boundary · effect budget boundary · anti-double-counting · slot budget proposal · armor budget (stoffa, cuoio) · weapon coefficient architecture (focus, balestra, pugnale) · effect taxonomy (13 famiglie) · effect status vocabulary · AFX1 relationship · Mark/Drain/Fragment/Dispel/anti-Incorporeal/anti-Summon/Channel/Ritual boundaries · boss safeguards · proc caps · hard-cap protections · forbidden mechanics · anti-P2W · Legendary boundary per i 3 PM-selected · schema futuro per-item · validation rules · policy proposals (rounding, stacking, conflict resolution, fallback) · risk register · PM open questions.
- **Out of scope Phase 1**: numeri item-by-item · effetti finali · affix assignment · Legendary effect finali · Registry generation · Registry apply · migration · DB writes · runtime item · sealed test refactor.

## 3. Governance

- DOCUMENTAL ONLY · READ-ONLY · NO APPLY.
- Zero mod backend/frontend/OpenAPI/DB/Registry/test/env/sigilli.
- 36/36 sigilli byte-identical; `lore_meta.py` anchor invariato.
- §31 rispettato: nessun file embed il proprio SHA finale; il SHA dei nuovi artefatti sarà disclosed solo in chat.
- Il ramo IS2-A (Phase 1, Phase 2 Rev-4, L1) è **LOCKED/IMMUTABLE**: nessuna riapertura di vocabolari, cap lessicali, roster Rev-4, audit chain o selezioni Legendary.

## 4. Source of truth (consumata read-only)

| Fonte | Versione | Ruolo |
|---|---|---|
| R18.5 Itemization baseline | ratificata | Budget framework di riferimento |
| CdV G1-G5 | ratificati | Gate design storici Cacciatore del Vuoto |
| AFX1 | ratificato | Affix architecture (families, cap eligibility) |
| IC1 | ratificato | Item contract genesi |
| IS1 | ratificato / IS1-SEALED | Preserved identity locks |
| IS2-A Phase 1 | CLOSED | Naming lock foundations |
| IS2-A Phase 2 Rev-4 | PM_LOCKED | Roster 120 · identity/naming/lore baseline |
| IS2-A-L1 | CLOSED / PM-LOCKED | Legendary PM-selected trio |

## 5. IS2-A dependency

Phase 1 IS2-B eredita **senza riaprire**:
- corpus attivo 111 (108 non-Leg selected + 3 Leg PM-selected)
- 9 Preserved identity locks (IS1-SEALED)
- 3 contingency dormant (0 generated names)
- Legendary trio: «Veste di Onirade» · «Occhio del Faro Rovesciato» · «Balestra della Traiettoria certa»

## 6. Active roster baseline

- Total active new design names: **111**
- Non-Legendary selected: **108**
- Legendary PM-selected: **3**
- Preserved identities: **9**
- Dormant contingency: **3** (0 generated)

## 7. Main-stat contract

- **Main stat classe pilota (Cacciatore del Vuoto)**: **Intelligenza**.
- **Priority order**: Intelligenza → Costituzione → Destrezza.
- **Soft cap Intelligenza**: 100.
- **Item-level assignment**: `null` in Phase 1 (il contratto stabilisce come, non quanto).
- Ogni item della classe pilota deve poter dichiarare `main_stat = Intelligenza` come default; deviazioni richiedono giustificazione contract-level, non item-level in Phase 1.

## 8. Secondary-stat contract

- **Costituzione**: secondary defensive priority.
- **Destrezza**: tertiary utility/opportunistic priority.
- **Vietati**:
  - Destrezza come main stat CdV
  - dual-primary Int/Dex
  - conversione retroattiva Dex→Int su build esistenti
  - qualunque build CdV Dex-primary
- Il profilo secondary è dichiarato a livello di slot/armor-type, non ancora numero.

## 9. Tier budget architecture

Bande di Intelligenza per tier (proposal, non ancora item-by-item):

| Tier | Intelligenza band |
|---|---|
| T1 | 10–25 |
| T2 | 25–45 |
| T3 | 45–70 |
| T4 | 70–90 |
| T5 | 90–115 |

Le bande definiscono l'**intervallo target** per la main stat all'interno del tier. Il numero finale per singolo item resta `null` in Phase 1; verrà determinato in Phase 2 tramite regola di allocazione contract-derived.

## 10. Rarity budget architecture

**Rarity multiplier** = **TOTAL BUDGET MULTIPLIER** (comprensivo di utility uniche):

| Rarity | Multiplier |
|---|---:|
| Common | 1.00 |
| Uncommon | 1.15 |
| Rare | 1.35 |
| Epic | 1.60 |
| Legendary | 1.85 |

- Il multiplier si applica sul budget totale, **non** come bonus additivo sopra effetti già completi.
- **Non** è moltiplicatore separato per sotto-budget (utility, effect, affix): è cifra di riferimento globale.
- Anti-double-counting: vedi §14.

## 11. Affix budget boundary

**Affix slots per tier**:

| Tier | Affix slots |
|---|---:|
| T1 | 1 |
| T2 | 2 |
| T3 | 3 |
| T4 | 4 |
| T5 | 5 |

- Overlay: **140 affix family occurrences** eleggibili su **120 blueprint units**.
- Questo è **contratto di eleggibilità** (chi PUÒ prendere quale famiglia), **non assegnazione** (chi la prende, con che valore).
- L'assegnazione affix per item resta in Phase 2 con PM_REVIEW.

## 12. Utility budget boundary

- Utility budget è **sotto-porzione** del budget totale post-multiplier.
- Include: effetti PAYOFF_UTILITY, DISPEL_UTILITY, CHANNEL_MOBILITY, RITUAL_PROTECTION.
- **Non** cumulabile in doppio conteggio con effect budget (§14).
- Ogni utility unique deve rispettare hard-cap protections §36 e proc cap §35.

## 13. Effect budget boundary

- Effect budget copre: PASSIVE_STAT, CONDITIONAL_STAT, MARK_INTERACTION, DRAIN_INTERACTION, FRAGMENT_INTERACTION, ANTI_INCORPOREAL, ANTI_SUMMON, WEAPON_IDENTITY_EFFECT, LEGENDARY_UNIQUE_EFFECT.
- Ogni effect ha `status ∈ {DIRECTION_ONLY, BUDGET_CLASSIFIED, DRAFT_REQUIRED, PM_REVIEW, PM_APPROVED, DESIGN_LOCKED}`.
- Item-level `effect value = null` in Phase 1.

## 14. Anti-double-counting rule

- Il rarity multiplier è **globale sul budget totale**.
- Utility budget, effect budget e affix budget sono **sotto-porzioni non additive**: non si moltiplicano di nuovo per il rarity multiplier separatamente.
- Nessun effetto può essere contato sia come utility sia come effect (categoria unica per effetto).
- Nessun affix può essere replicato tra due family diverse.

## 15. Slot budget proposal (PM_REVIEW)

Bande proposte per classificazione slot budget (**non auto-locked**, PM adjudication required):

| Slot | Classificazione proposta |
|---|---|
| head | high-budget armor |
| neck | medium-budget accessory |
| shoulders | medium-budget armor |
| chest | high-budget armor |
| back | medium-budget armor |
| hands | medium-budget armor |
| wrist | low-budget utility |
| waist | medium-budget accessory |
| legs | high-budget armor |
| feet | medium-budget armor |
| main_hand | high-budget weapon |
| off_hand | medium-budget utility |
| ring | low-budget utility |
| accessory | low-budget utility |

Le bande esatte (budget max/min per classificazione) restano PM_REVIEW → `IS2B_P1_Q03`.

## 16. Armor budget

- Il budget armor è funzione di: `slot_budget_class × rarity_multiplier × tier_band_reference`.
- L'output è un **range di riferimento**, non un valore singolo per Phase 1.
- Ogni armor slot deve dichiarare compliant `armor_type ∈ {stoffa, cuoio}` per la classe pilota; deviazioni fuori scope Phase 1.

## 17. Stoffa budget

- Direzione budget: **potenza rituale · canalizzazione · Marchio · Drenaggio · dissipazione**.
- Costituzione: profilo secondario **basso/medio** (non defensive-primary).
- Nessuna direzione verso mobilità principale.
- Nessuna sovrapposizione con identità Ladro / Cacciatore di Mostri (§44).

## 18. Cuoio budget

- Direzione budget: **mobilità · Costituzione · protezione rituale · opportunità · controllo distanza**.
- Costituzione: profilo secondario **medio/alto**.
- **Vietato** profilo Dex-primary sul cuoio della classe pilota.
- **Vietato** identità Ladro sul cuoio (weapon-family lock preserved).
- **Vietato** identità Cacciatore di Mostri sul cuoio.

## 19. Weapon coefficient architecture

Bande weapon coefficient (moltiplicatore su budget weapon):

| Weapon family | Coefficient (banda) | Status |
|---|:---:|---|
| focus | **1.00** | DESIGN_LOCKED |
| balestra | **0.85 – 0.90** | PM_REVIEW → `IS2B_P1_Q01` |
| pugnale | **0.70 – 0.80** | PM_REVIEW → `IS2B_P1_Q02` |

- Il coefficient si applica al budget weapon (dopo tier/rarity), non alla main stat.
- Il valore esatto entro la banda balestra/pugnale è PM open question.

## 20. Focus contract

- Focus = **primary class weapon** per Cacciatore del Vuoto.
- Coefficient = **1.00** (baseline).
- Il contratto **PUÒ** autorizzare:
  - maggiore potenza diretta
  - migliore efficienza di canalizzazione
  - migliore coerenza con Marchio / Drenaggio
- Il contratto **NON PUÒ** autorizzare:
  - resource cap increase
  - Frammenti oltre 5 (hard cap)
  - focus bonus oltre 2 per resource segment
  - boss safeguard bypass

## 21. Balestra contract

- Balestra = **ranged ritual signature** della classe.
- Coefficient = **0.85 – 0.90** (PM_REVIEW).
- Il budget riflette: precisione · distanza · proiezione · dissipazione mirata.
- **Vietato** trasformare la balestra in:
  - arma Dex primaria
  - arco (weapon-family lock)
  - weapon family generica

## 22. Pugnale contract

- Pugnale = **ritual/opportunistic weapon**.
- Coefficient = **0.70 – 0.80** (PM_REVIEW).
- Il budget riflette: prossimità · incisione · opportunità · rischio maggiore.
- **Ritual close bonus**: **≤ 1 per applicazione Marchio**, refresh **non resetta** il limite (hard cap).
- Preservare identity ritual/opportunistic; **vietato** identità Ladro.

## 23. Effect taxonomy (13 famiglie)

Le 13 famiglie di effetto ammesse in IS2-B:

1. `PASSIVE_STAT` — bonus statico non condizionato
2. `CONDITIONAL_STAT` — bonus statico con precondizione
3. `MARK_INTERACTION` — interazione con Marchio del Vuoto
4. `DRAIN_INTERACTION` — interazione con Drenaggio del Vuoto
5. `FRAGMENT_INTERACTION` — interazione con Frammenti (cap 5)
6. `PAYOFF_UTILITY` — categoria tecnica interna (**NON** player-facing "Payoff")
7. `DISPEL_UTILITY` — utilità di dissipazione
8. `ANTI_INCORPOREAL` — vs incorporeal targets
9. `ANTI_SUMMON` — vs summoned targets (con safeguard §34)
10. `CHANNEL_MOBILITY` — mobilità durante canalizzazione
11. `RITUAL_PROTECTION` — protezione difensiva rituale
12. `WEAPON_IDENTITY_EFFECT` — effetto legato al weapon-family
13. `LEGENDARY_UNIQUE_EFFECT` — effetto Legendary unique-per-item

## 24. Effect status taxonomy

Ogni effetto ha uno status nel ciclo di vita:

| Status | Semantica |
|---|---|
| `DIRECTION_ONLY` | Solo direzione descrittiva, nessun valore |
| `BUDGET_CLASSIFIED` | Assegnato a un budget category |
| `DRAFT_REQUIRED` | Necessita draft numerico Phase 2 |
| `PM_REVIEW` | In review PM |
| `PM_APPROVED` | Approvato PM (pre-lock) |
| `DESIGN_LOCKED` | Locked, immutabile senza Gate correttivo |

In Phase 1: **item-level effect = null** · **effect value = null** per l'intero corpus 111.

## 25. AFX1 relationship

- AFX1 fornisce le affix families e la loro eligibility architecture.
- IS2-B Phase 1 **consuma** AFX1 read-only per definire l'affix budget boundary (§11) e la matrice di eleggibilità 140/120.
- Nessuna modifica ad AFX1. Nessuna nuova family introdotta in Phase 1.

## 26. Mark boundaries

- **Active marks hard cap = 5** (immutabile).
- **Mark duration hard cap = 10** (immutabile).
- Ogni MARK_INTERACTION effect deve rispettare i cap sopra.
- Nessun effetto può aggiungere mark oltre 5 attivi né estendere duration oltre 10.

## 27. Drain boundaries

- DRAIN_INTERACTION effects sono ammessi solo per target con Marchio attivo (unmarked resource generation vietata, §37).
- Nessun drain permanente cross-phase (§37).
- Ogni drain deve rispettare boss safeguard (§34).

## 28. Fragment boundaries

- **Frammenti cap = 5** (immutabile).
- FRAGMENT_INTERACTION effects non possono aumentare il cap.
- Focus bonus ≤ 2 per resource segment (§20).

## 29. Dispel boundaries

- DISPEL_UTILITY effects devono avere target definito (buff/debuff/altro).
- Nessuna dispel unconditional su boss buff (§34).
- Rispetta boss safeguard.

## 30. Anti-incorporeal boundaries

- ANTI_INCORPOREAL effects sono ammessi per valid incorporeal targets.
- Budget classificato come utility o weapon_identity_effect a seconda dell'ancoraggio.
- Nessuna combinazione anti-incorporeal + boss safeguard bypass.

## 31. Anti-summon boundaries

- ANTI_SUMMON effects sono ammessi **solo** per valid boss-summoned add con safeguard/condition/budget dichiarato.
- **Vietata** unconditional summon deletion (§37).
- **Vietata** boss immunity bypass (§34).

## 32. Channel-mobility boundaries

- CHANNEL_MOBILITY effects concedono mobilità durante canalizzazione.
- Non devono trasformare la classe in mobility-primary (identity coerenza).
- Devono restare compatibili con focus/balestra/pugnale identity.

## 33. Ritual-protection boundaries

- RITUAL_PROTECTION effects sono defensive rituali.
- Non devono sovrapporsi al ruolo tank/healer.
- Cap combined proc rispettato (§35).

## 34. Boss safeguards

**Vietato**:
- direct boss nullification
- boss immunity bypass
- unconditional summon deletion
- ignore boss safeguard

Le direzioni future consentite **solo** per: **valid boss-summoned add** con safeguard/condition/budget dichiarati. Ogni ANTI_SUMMON, DISPEL_UTILITY, ANTI_INCORPOREAL effect deve dichiarare `boss_safeguard_required = true` a livello di schema (§45).

## 35. Proc cap rules

- **Combined proc cap = 45%** su qualsiasi combinazione multi-effect proc.
- Nessun singolo effetto può eccedere 45% di proc rate.
- Multi-effect stacking (§48) è policy PM_REVIEW.

## 36. Hard-cap protections (immutabili)

| Voce | Valore | Note |
|---|:---:|---|
| Frammenti cap | **5** | Nessun item può aumentarlo |
| Marchio duration hard cap | **10** | Immutabile |
| Active marks hard cap | **5** | Immutabile |
| Combined proc cap | **45%** | Combined multi-effect |
| Focus bonus per resource segment | **≤ 2** | Focus contract |
| Pugnale ritual-close bonus per Mark application | **≤ 1** | Refresh non resetta |

**Nessun item, nessuna combinazione, nessun affix, nessun Legendary unique può violare questi cap.**

## 37. Forbidden mechanics

Vietato definire item con queste meccaniche (elenco non esaustivo):

- resource cap increase
- active marks > 5
- Mark duration > 10
- unmarked resource generation
- direct boss nullification
- boss safeguard bypass
- P2W (§38)
- dual Int/Dex primary
- cross-class optimal item
- focus bonus > 2 per segment
- ritual-close bonus > 1 per Mark
- untested PvP effects
- cross-phase persistence
- random full-resource waste

## 38. Anti-P2W

- `can_be_sold_for_real_money = false` per:
  - combat item
  - progression item
  - ranking item
  - economy-impacting item
- La potenza NON può derivare da acquisto real-money.
- Qualunque conflict con la monetizzazione va risolto in favore dell'integrità gameplay.

## 39. Legendary chest boundary — «Veste di Onirade»

- **Blueprint**: `cdv_t5_chest_stoffa_002` · slot chest · subtype stoffa
- **Mechanical identity pillar**: canalizzazione + dissipazione rituale (direction, non valore)
- **Budget class**: high-budget armor · rarity Legendary (multiplier 1.85)
- **Unique-effect boundary**: `LEGENDARY_UNIQUE_EFFECT` con status `DIRECTION_ONLY` in Phase 1
- **Forbidden overlap**:
  - no boss safeguard bypass
  - no active marks > 5
  - no Mark duration > 10
  - no Dex-primary drift
- **Future validation requirements**: PM_REVIEW per direction meccanica definitiva (§55 → `IS2B_P1_Q06a`)
- **Effetto finale**: `null` in Phase 1

## 40. Legendary focus boundary — «Occhio del Faro Rovesciato»

- **Blueprint**: `cdv_t5_main_hand_focus_001` · slot main_hand · subtype focus
- **Mechanical identity pillar**: coerenza con loop Identify → Mark → Drain → Payoff (direction, non promessa meccanica quantificabile)
- **Budget class**: high-budget weapon · rarity Legendary · coefficient 1.00
- **Unique-effect boundary**: `LEGENDARY_UNIQUE_EFFECT` + `WEAPON_IDENTITY_EFFECT` con status `DIRECTION_ONLY` in Phase 1
- **Forbidden overlap**:
  - no resource cap increase
  - no Frammenti > 5
  - no focus bonus > 2 per segment
  - no boss safeguard bypass
- **Future validation requirements**: PM_REVIEW per direction meccanica definitiva (§55 → `IS2B_P1_Q06b`)
- **Effetto finale**: `null` in Phase 1

## 41. Legendary balestra boundary — «Balestra della Traiettoria certa»

- **Blueprint**: `cdv_t5_main_hand_balestra_001` · slot main_hand · subtype balestra
- **Mechanical identity pillar**: precisione narrativa aspirazionale (**non** garanzia hit / crit / accuracy quantificata)
- **Budget class**: high-budget weapon · rarity Legendary · coefficient 0.85-0.90 (PM_REVIEW → `IS2B_P1_Q01`)
- **Unique-effect boundary**: `LEGENDARY_UNIQUE_EFFECT` + `WEAPON_IDENTITY_EFFECT` con status `DIRECTION_ONLY` in Phase 1
- **Forbidden overlap**:
  - no Dex-primary drift
  - no trasformazione in arco
  - no boss safeguard bypass
  - no ranged safeguard bypass
- **Future validation requirements**: PM_REVIEW per direction meccanica definitiva (§55 → `IS2B_P1_Q06c`)
- **Effetto finale**: `null` in Phase 1

## 42. Shared-family limits

- Effetti WEAPON_IDENTITY_EFFECT non possono replicarsi identici tra weapon-family diverse.
- Affix families condivise (§25) restano coerenti con AFX1 architecture.
- Nessun cross-family stacking oltre il proc cap combinato (§35).

## 43. Universal-neutral limits

- Effetti neutrali universali (senza class-specific hook) non possono superare il baseline utility budget.
- Nessun neutral effect può superare in potenza un class-specific equivalente.
- Balance rimane biased verso class-specific per preservare identità.

## 44. Class-specific limits

- Effetti class-specific CdV: consentiti solo se coerenti con Marchio/Drenaggio/Frammenti loop.
- **Vietata** deriva Negromante (§39-40 rationale IS2-A-L1).
- **Vietata** identità Ladro / Cacciatore di Mostri sul cuoio (§18).
- **Vietata** conversione retroattiva Dex→Int su build esistenti (§8).

## 45. Future per-item schema (campi contract-level)

Schema campi previsti per ogni item nel corpus 111. In Phase 1: tutti i campi numerici = `null`, campi categoriali popolati con classificazione contract-derived.

| Campo | Tipo | Fase di popolamento |
|---|---|---|
| `blueprint_code` | string | IS2-A |
| `tier` | int (1-5) | IS2-A |
| `rarity` | enum {Common, Uncommon, Rare, Epic, Legendary} | IS2-A |
| `slot` | enum (14 slot §15) | IS2-A |
| `equipment_category` | enum {weapon, armor, accessory} | IS2-A |
| `armor_type` | enum {stoffa, cuoio, null} | IS2-A |
| `weapon_family` | enum {focus, balestra, pugnale, null} | IS2-A |
| `identity_class` | string | IS2-A |
| `stat_budget_class` | enum {high, medium, low} | **IS2-B Phase 1** (contract-derived) |
| `main_stat` | enum {Intelligenza, Costituzione, Destrezza} | IS2-B Phase 1 (default Intelligenza per CdV) |
| `main_stat_band` | enum tier band §9 | IS2-B Phase 1 (contract-derived) |
| `main_stat_value` | int | **null in Phase 1** → Phase 2 |
| `secondary_stat_profile` | dict | IS2-B Phase 1 (contract-derived) |
| `weapon_coefficient_status` | enum {locked, PM_REVIEW} | IS2-B Phase 1 |
| `weapon_coefficient_value` | float | **null in Phase 1** → Phase 2 |
| `base_budget` | float | **null in Phase 1** → Phase 2 |
| `rarity_multiplier` | float | IS2-B Phase 1 (from §10) |
| `utility_budget` | float | **null in Phase 1** → Phase 2 |
| `effect_budget` | float | **null in Phase 1** → Phase 2 |
| `affix_budget` | int (slots) | IS2-B Phase 1 (from §11) |
| `eligible_effect_families` | list[enum] | IS2-B Phase 1 (from §23) |
| `effect_direction` | list[string] | IS2-B Phase 1 (Legendary direction pillar) |
| `effect_status` | enum §24 | IS2-B Phase 1 (default `DIRECTION_ONLY`) |
| `effect_value` | numeric | **null in Phase 1** → Phase 2 |
| `mechanic_boundary_flags` | dict | IS2-B Phase 1 (from §26-33, §36-37) |
| `boss_safeguard_required` | bool | IS2-B Phase 1 (from §34) |
| `anti_p2w` | bool (true) | IS2-B Phase 1 |
| `validation_status` | enum {contract_pending, contract_ok, item_pending, item_ok} | IS2-B Phase 1 |
| `PM_status` | enum {open, PM_REVIEW, PM_APPROVED, LOCKED} | IS2-B Phase 1 |

## 46. Validation rules

Regole di validazione contract-level (item validation resta Phase 2):

- `main_stat` deve essere Intelligenza per item CdV, o giustificato.
- `main_stat_band` deve appartenere a tier band §9.
- `rarity_multiplier` = valore atteso da §10 per la rarity dichiarata.
- `affix_budget` = valore atteso da §11 per il tier.
- Ogni effect deve dichiarare `effect_status` (§24) e appartenere a una delle 13 famiglie (§23).
- Ogni effect ANTI_SUMMON/DISPEL_UTILITY/ANTI_INCORPOREAL deve avere `boss_safeguard_required = true`.
- `anti_p2w = true` per ogni combat/progression/ranking/economy item.
- Nessun item può violare hard-cap protections (§36).
- Nessuna dual Int/Dex primary (§8).

## 47. Rounding policy proposal

Proposta baseline (PM_REVIEW → `IS2B_P1_Q04`):

- Main stat: round-half-to-even sul valore contract-derived, boundary rispettata dal tier band §9.
- Coefficient weapon: 2 decimali, round-half-to-even.
- Budget totale: 1 decimale, round-half-to-even.
- Proc cap: intero percentuale, round-down conservativo.

PM open question: **up / down / nearest** per stat, tier, budget (§55).

## 48. Stacking policy proposal

Proposta baseline (PM_REVIEW → `IS2B_P1_Q05`):

- Multi-item effect stacking: sub-additive per stessa famiglia effect (§23).
- Combined proc cap §35 non bypassabile via stacking.
- Nessuno stacking cross-phase (durate non si sommano tra pull).
- Two-piece / four-piece set bonuses: fuori scope Phase 1.

## 49. Conflict-resolution policy

- Conflict tra due effect stessa family: prevale il più restrictive (safeguard-oriented).
- Conflict tra item-level e class-level: prevale class-level (identity lock).
- Conflict tra Phase 1 contract e IS2-A output: prevale IS2-A (LOCKED/IMMUTABLE §5).
- Conflict tra contract e sealed scripts: **prevale sealed scripts** (§3, 36/36 byte-identical).

## 50. Fallback policy

- Se PM non decide una PM open question entro Phase 2 opening: applicare la `default proposal` dichiarata (§55).
- Se la fallback introduce violazione hard-cap (§36): STOP, re-escalation PM, no autonomous decision.
- Se la fallback introduce forbidden mechanic (§37): STOP, re-escalation PM, no autonomous decision.

## 51. Migration boundary

- **Zero migration** in Phase 1.
- Nessuna riscrittura DB, nessuna alterazione schema, nessun runtime data mutation.
- Migration di stat/budget/effect ai 111 nomi → **Phase 2 con Registry v3 apply autorizzato separatamente** (attualmente NOT AUTHORIZED).

## 52. Registry boundary

- **Registry_status per l'intero corpus 111**: `NOT_GENERATED`.
- Registry v3 Item Generation & Apply: `NOT_AUTHORIZED`.
- Nessuna Registry entry, nessun apply, nessun runtime item.

## 53. Implementation boundary

- Backend: **nessuna modifica**.
- Frontend: **nessuna modifica**.
- OpenAPI: **nessuna modifica**.
- Test suite: **nessuna modifica**.
- Sigilli: **36/36 byte-identical, nessun nuovo sigillo**.
- Anchor `lore_meta.py`: SHA `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` INVARIATO.

## 54. Risk register

| # | Rischio | Impatto | Mitigazione contract-level |
|---|---|:---:|---|
| R1 | Coefficient balestra/pugnale scelta suboptimal | alto | PM_REVIEW `IS2B_P1_Q01`/`Q02` |
| R2 | Slot budget bands sbilanciate | alto | PM_REVIEW `IS2B_P1_Q03` |
| R3 | Stacking policy leaks su proc cap | alto | Policy conservativa §48, cap §35 |
| R4 | Rounding boundary ambigua | medio | Round-half-to-even baseline §47 |
| R5 | Legendary direction troppo forte / troppo debole | alto | PM_REVIEW `IS2B_P1_Q06a-c` |
| R6 | AFX1 family drift durante Phase 2 | medio | AFX1 read-only §25 |
| R7 | Cross-phase persistence unintended | alto | §37 forbidden, §49 conflict resolution |
| R8 | Boss safeguard bypass via combo | alto | §34, `boss_safeguard_required` schema §45 |
| R9 | Dex-primary drift CdV | medio | §8, §18, §37 |
| R10 | Item-by-item numeric leak in Phase 1 | medio | Vincolo hard: item-level numeric = null |

## 55. PM open questions (blocco unificato)

Elenco delle domande aperte con proposta agent, impatto e fallback. Ogni domanda ha `question_id` incrementale.

### `IS2B_P1_Q01` — Balestra weapon coefficient finale
- **Question (verbatim)**: «Il weapon coefficient finale della balestra deve essere 0.85 o 0.90 all'interno della banda contract-level 0.85–0.90?»
- **Agent recommendation**: 0.88 come compromesso tra weapon readability alta e non-overtaking del focus baseline; oppure 0.85 se il PM preferisce preservare gap netto vs focus 1.00.
- **Impact**: alto (influenza budget weapon per tutti gli item balestra del corpus)
- **Default proposal**: 0.85 (conservativo, mantiene gap netto vs focus 1.00)
- **Blocking**: sì (bloccante per Phase 2)

### `IS2B_P1_Q02` — Pugnale weapon coefficient finale
- **Question (verbatim)**: «Il weapon coefficient finale del pugnale deve essere 0.70 o 0.80 all'interno della banda contract-level 0.70–0.80?»
- **Agent recommendation**: 0.75 come punto intermedio che rispetta rischio-opportunità del pugnale ritual/opportunistic; oppure 0.70 se il PM enfatizza il rischio maggiore.
- **Impact**: alto (influenza budget weapon per tutti gli item pugnale del corpus)
- **Default proposal**: 0.75 (intermedio, coerente con identity ritual/opportunistic)
- **Blocking**: sì (bloccante per Phase 2)

### `IS2B_P1_Q03` — Slot budget bands finali
- **Question (verbatim)**: «Le classificazioni proposte in §15 (high/medium/low per i 14 slot) sono ratificate? Se sì, quali valori di budget max/min per ciascuna classificazione?»
- **Agent recommendation**: ratificare la classificazione §15 e adottare rapporti budget high:medium:low = 1.00 : 0.70 : 0.45 come baseline.
- **Impact**: alto (influenza budget di ogni slot per l'intero corpus)
- **Default proposal**: adozione classificazione §15 con rapporti 1.00 : 0.70 : 0.45
- **Blocking**: sì (bloccante per Phase 2)

### `IS2B_P1_Q04` — Rounding policy finale
- **Question (verbatim)**: «La policy di rounding per stat, tier, budget deve essere round-half-to-even, round-half-up, o nearest-with-configurable-tiebreak?»
- **Agent recommendation**: round-half-to-even (banker's rounding) per stabilità statistica; round-down conservativo per proc cap.
- **Impact**: medio (edge cases sui valori boundary)
- **Default proposal**: round-half-to-even per stat/tier/budget, round-down per proc cap
- **Blocking**: no (fallback deterministico applicabile)

### `IS2B_P1_Q05` — Stacking policy finale
- **Question (verbatim)**: «La stacking policy multi-item per effect family deve essere additive, sub-additive, oppure diminishing-returns esplicito (formula da PM)?»
- **Agent recommendation**: sub-additive per stessa family, nessuno stacking cross-phase, combined proc cap §35 non bypassabile.
- **Impact**: alto (rischio power-creep se additive)
- **Default proposal**: sub-additive intra-family, proc cap 45% invariato
- **Blocking**: sì (bloccante per Phase 2)

### `IS2B_P1_Q06a` — Legendary direction «Veste di Onirade»
- **Question (verbatim)**: «Qual è il pillar meccanico finale (direction, non valore) per «Veste di Onirade»? Canalizzazione+dissipazione, protezione rituale enhanced, o altro?»
- **Agent recommendation**: canalizzazione + dissipazione rituale come pillar primario, `LEGENDARY_UNIQUE_EFFECT` con effect_status `DIRECTION_ONLY` in Phase 1.
- **Impact**: alto (Legendary identity)
- **Default proposal**: canalizzazione + dissipazione rituale
- **Blocking**: sì (bloccante per Phase 2)

### `IS2B_P1_Q06b` — Legendary direction «Occhio del Faro Rovesciato»
- **Question (verbatim)**: «Qual è il pillar meccanico finale (direction, non valore) per «Occhio del Faro Rovesciato»? Marchio efficiency, identify support, drain synergy, o altro?»
- **Agent recommendation**: coerenza col loop Identify→Mark→Drain→Payoff, `LEGENDARY_UNIQUE_EFFECT` + `WEAPON_IDENTITY_EFFECT`, effect_status `DIRECTION_ONLY` in Phase 1.
- **Impact**: alto (Legendary identity + class signature)
- **Default proposal**: identify/mark/drain synergy come pillar
- **Blocking**: sì (bloccante per Phase 2)

### `IS2B_P1_Q06c` — Legendary direction «Balestra della Traiettoria certa»
- **Question (verbatim)**: «Qual è il pillar meccanico finale (direction, non valore) per «Balestra della Traiettoria certa»? Precisione narrativa senza hit-guarantee, dissipazione mirata, o altro?»
- **Agent recommendation**: precisione narrativa aspirazionale + dissipazione mirata, senza garanzia hit / crit / accuracy quantificata.
- **Impact**: alto (Legendary identity + ranged ritual signature)
- **Default proposal**: precisione narrativa + dissipazione mirata (no mechanic-promise)
- **Blocking**: sì (bloccante per Phase 2)

### `IS2B_P1_Q07` — Utility vs effect budget ratio
- **Question (verbatim)**: «Il rapporto proposto utility_budget : effect_budget dentro il budget totale (post-multiplier) è auto-ratificato dal contratto, o richiede PM adjudication?»
- **Agent recommendation**: PM adjudication su ratio baseline; default 30% utility · 70% effect per weapon, 40% utility · 60% effect per armor.
- **Impact**: medio
- **Default proposal**: 30/70 weapon, 40/60 armor
- **Blocking**: no

### `IS2B_P1_Q08` — Set bonus policy
- **Question (verbatim)**: «Sono ammessi in futuro set bonuses (two-piece / four-piece) per il corpus 111, o restano fuori scope permanente?»
- **Agent recommendation**: fuori scope Phase 1; PM adjudication per Phase 2+ o gate separato.
- **Impact**: medio
- **Default proposal**: fuori scope Phase 1, hold decision per Phase 2+
- **Blocking**: no

## 56. Phase 2 readiness

Phase 2 può aprire **solo dopo** che:

- Le 5 domande `IS2B_P1_Q01`/`Q02`/`Q03`/`Q05`/`Q06a-c` sono ratificate PM (blocking = sì).
- Il contratto §7-§54 è ratificato PM come immutable baseline.
- Nessuna violazione hard-cap emergente in review.
- Registry v3 apply resta separatamente NOT_AUTHORIZED fino a fase successiva.

Phase 2 focus (out of scope Phase 1): assegnazione item-by-item di main stat value, coefficient value, base budget, utility budget, effect budget, effect value, affix assignment; validation full-corpus; draft Legendary unique effect finali; migration boundary review.

## 57. GO/HOLD recommendation

**Agent recommendation**: **HOLD** — Phase 1 draft è completo come **artifact written**, ma richiede PM adjudication sulle open questions §55 prima di poter dichiarare `DESIGN_LOCKED` e aprire Phase 2. Nessuna auto-ratifica su balestra/pugnale coefficient finali, slot budget bands, stacking, rounding, Legendary effect direction: tutte le 5 aree restano PM_REVIEW.

**Stato finale Phase 1**:

```
R18.6.RV3-IS2-B Phase 1        = ARTIFACT WRITTEN
PM adjudication                = REQUIRED (§55 PM open questions)
Formal closure                 = HOLD
R18.6.RV3-IS2-B Phase 2        = HOLD / NOT AUTHORIZED
R18.6.RV3-NC1                  = HOLD / NOT AUTHORIZED
R18.6 Gate 11                  = HOLD / NOT AUTHORIZED
Registry v3 Item Gen & Apply   = NOT AUTHORIZED
Monaco                         = HOLD / NOT AUTHORIZED
AFX2                           = RESERVED FUTURE / NOT AUTHORIZED

IS2-A ramo (Phase 1, Phase 2 Rev-4, L1) = LOCKED / IMMUTABLE
Cacciatore del Vuoto = ACTIVE-DESIGN-READY (design layer only)

ATTENDO VERDICT PM.
```
