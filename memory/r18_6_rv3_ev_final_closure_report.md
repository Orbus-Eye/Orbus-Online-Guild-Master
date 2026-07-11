# R18.6.RV3-EV · Final Closure Report

**Documento**: `r18_6_rv3_ev_final_closure_report.md`
**Parent gate**: R18.6.RV3-EV (Eligibility Validation)
**Chain**: RV3-EV (baseline) → EV-F1 (corrective/additive audit) → EV-F2 (final adjudication) → **RV3-EV CLOSED**
**Regime**: DOCUMENTAL ONLY · READ-ONLY · Italian · Zero write · Zero code · Zero DB mutation
**Sealed integrity**: 36/36 · `lore_meta.py` = `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`
**Cacciatore del Vuoto**: ACTIVE-DESIGN-READY · NOT LIVE · NOT SELECTABLE · NOT IMPLEMENTED

---

## 1 · PM verdict

**R18.6.RV3-EV · Eligibility Validation** è **CHIUSO** con verdict PM finale del dispatch corrente.

Verdict PM sommario:
- **EV-F1**: PM APPROVED (corrective/additive audit accepted)
- **EV-F2**: PM APPROVED (con accounting micro-fix già applicato) — ledger 178/178 RATIFICATO
- **RV3-EV**: FORMAL CLOSURE autorizzata, PM_REVIEW = 0, unresolved item adjudication = 0
- **AFX1**: HOLD (kickoff solo POST closure formale RV3-EV + successivo verdict PM dedicato)
- **Registry v3 apply**: NOT AUTHORIZED
- **Item creation**: NOT AUTHORIZED
- **Gate 11 / Wave 1 / Monaco**: HOLD

Nessuna materializzazione runtime autorizzata da questa closure. RV3-EV chiude come **eligibility & baseline audit** — non come apply gate.

---

## 2 · RV3-EV CLOSED

**Stato finale gate**:
- `gate_id`: R18.6.RV3-EV
- `status`: **CLOSED**
- `sub-gates`:
  - EV-F1 Live Catalog Metadata Readiness → **CLOSED**
  - EV-F2 Candidate Adjudication & Coverage Reconciliation → **CLOSED**
- `pm_locked`: true
- `apply_authorized`: false
- `mutation_forbidden`: true
- `next_gate_pending_pm_directive`: yes (nessun auto-start)

---

## 3 · RV3-EV originale preservato

Il documento originale `r18_6_rv3_ev_eligibility_validation.md` + JSON è **IMMUTABILE**.

**SHA IMMUTABILITY LOCK**:
- MD: `41450c4fa770efd57a15c302958c20e2826f33ac668aba5eaeb2e6743f9fd09e` (preservato)
- JSON: `c4ed0af9bedd7ad343c038b9520cf9aa3c0fcfc4d32779edff9364dfcf1e0f35` (preservato)

Il documento resta come **baseline storica** del gate. Nessuna riscrittura, nessun update, nessuna correzione retroattiva.

Le divergenze rilevate in fase EV-F1/EV-F2 (rarity distribution stimata, finding L12=T5 errato, distinzione catalog canonico vs live, ecc.) sono state tracciate come **corrective/additive audit** nei documenti figli, senza mai modificare il baseline.

---

## 4 · EV-F1 acquisito come corrective/additive audit

`R18.6.RV3-EV-F1 · Live Catalog Metadata Readiness`:
- MD SHA: `2031be1abda2aa5eea00822e68d6d1aa17cd8be7f35ce211b10e2f0d354961fe`
- JSON SHA: `44f6ec686eb6a59ecaaba938d86bbe10a73c34bb4d7626cb0235c92dce29a5bb`
- Ruolo: **corrective/additive audit** su RV3-EV baseline
- Contributi chiave:
  - Distinzione formale **canonical design catalog 1500 (planning-numeric)** vs **live materialized catalog 178**
  - Correzione critica **L12 = T1 Aspirante** (NON T5, come erroneamente affermato in RV3-EV)
  - Metadata field readiness 5-field (armor_type/weapon_family/tier/ilvl/affix_pool_tag) con 7 verdict enum
  - Slot canonici 14 + 4 alias documentati (nessun 15° slot)
  - 6 lore Vuoto/Oblio initial audit (0 REUSE, 4 IDENTITY_CONFLICT, 2 PM_REVIEW)
  - 42 sezioni MD + 19 root keys JSON
- Status: **CLOSED** (acquisito nel corpus RV3-EV chain)

---

## 5 · EV-F2 acquisito come final adjudication

`R18.6.RV3-EV-F2 · Candidate Adjudication & Coverage Reconciliation`:
- MD SHA: `37a4963a10515a6cee9726e680e7dc70731bfbca4b9a5f4aa7206f2c5148fcf9`
- JSON SHA: `093061698600880e5833a9a3387631fda2c3beab3dae2f97877eb42cae32389a`
- Ruolo: **final adjudication** del ledger live 178 items
- Contributi chiave:
  - Ledger canonico 178/178 (12/32/134/0) — mutuamente esclusivo, esaustivo, no double count
  - Adjudication record-by-record 18 REUSE_VALID candidates → 12 VALIDATED + 6 declassed (weapon G2 strict)
  - Adjudication record-by-record 49 PM_REVIEW → 32 REUSE_CONDITIONAL + 15 declassed + 2 assegnati ai 6 lore
  - 6 lore items final adjudication (0 REUSE, 5 IDENTITY_CONFLICT, 1 arcane_adept_orb → NOT_COMPATIBLE preserved Opzione A)
  - voidpiercer-bow FINAL exclusion (retro-branding VIETATO)
  - Rarity distribution live misurata authoritative (correzione RV3-EV Epic/Legendary stima)
  - Anti-P2W audit (0 true, 128 false, 50 missing data quality gap)
  - ILVL formula LOCK canonica (+0/+2/+3/+4/+5, Legendary=60 anchor)
  - Coverage T2-T5 = 0 items live confermato
  - F2-Q1..F2-Q12 verbatim extraction + PM verdict finali
  - 47 sezioni MD + 39 root keys JSON post accounting micro-fix
- Status: **CLOSED** (final adjudication ratified)

---

## 6 · Regola di precedenza documentale

Ordine di precedenza per lettura/interpretazione del corpus RV3-EV chain:

| Aspetto | Documento authoritative |
|---|---|
| Ledger 178 / adjudication finale | **EV-F2** (ratified) |
| Metadata readiness + L12=T1 lock + catalog lineage separation | **EV-F1** (corrective/additive) |
| Baseline storica gate + sezioni non corrette (verdicts_admitted, target_profile, ecc.) | **RV3-EV originale** (baseline) |
| Formula ILVL + rarity distribution live | **EV-F2** |
| Governance locks + immutability | **RV3-EV originale + EV-F1 + EV-F2** (concordanti) |

**Regola**: in caso di divergenza documentale, il documento più recente nella chain (EV-F2 > EV-F1 > RV3-EV originale) prevale per l'aspetto contestato. Il baseline non viene mai riscritto.

---

## 7 · Live universe 178

**Live materialized runtime catalog**:
- Collection: `items` (MongoDB `orbus_r16.items`)
- Count: **178 record unici**
- Adjudicati: 178/178
- Non-adjudicated residui: **0**

**Distinzione preservata**:
- **Canonical design catalog 1500** (planning-numeric, R18.5 documentale) — separato, non toccato
- **Live materialized 178** (universe di questo audit)
- Nessuna quantificazione "1500 − 178 = 1322 missing" ammessa (discrepanza non è per-ID)

---

## 8 · Ledger 12/32/134/0

**Live Item Adjudication Ledger (canonical, disjoint, exhaustive)**:

```
╔══════════════════════════════════════════════════════════════════╗
║       LIVE ITEM ADJUDICATION LEDGER (universe = 178 items)       ║
╠══════════════════════════════════════════════════════════════════╣
║   REUSE_VALID          =  12                                     ║
║   REUSE_CONDITIONAL    =  32                                     ║
║   NOT_COMPATIBLE       = 134                                     ║
║   PM_REVIEW            =   0                                     ║
║   TOTAL                = 178  ✅ DISJOINT PASS · EXHAUSTIVE PASS ║
╚══════════════════════════════════════════════════════════════════╝
```

**Composition REUSE_CONDITIONAL (32)**:
- 2 weapon literal G2 (focus/dagger)
- 11 armor stoffa/cuoio proficient
- 19 accessory universal
- Condition: Registry v3 additive `rec_classes` atomic append (non-mutation)

**Composition NOT_COMPATIBLE (134)**:
- 6 warlock weapon tome/arcane (famiglia_esclusa_da_G2)
- 5 lore items IDENTITY_CONFLICT
- 1 arcane_adept_orb PRESERVED (Opzione A)
- 15 dei 47 declassati (famiglia_esclusa_da_G2)
- 107 out-of-scope (81 stat mismatch + 21 stat missing + 5 hard binding)

---

## 9 · Primary verdict uniqueness

**Regola invariante RATIFICATA**:
- Ogni record live ha **UN SOLO primary verdict** ∈ {REUSE_VALID, REUSE_CONDITIONAL, NOT_COMPATIBLE, PM_REVIEW}
- Attributi secondari (non double-count nel totale):
  - `out_of_scope=true`
  - `lore_reviewed=true`
  - `identity_conflict=true`
  - `mutation_required=true`
  - `triggers_future_void_native_item=true`
  - `retro_branding_forbidden=true`
- `double_count = 0` ✅
- `unadjudicated = 0` ✅
- Totale disjoint = 178 ✅

`REQUIRES_NEW_ITEM_FUTURE` **NON è primary verdict** applicabile al ledger 178 — è separato in Future Coverage Gap.

---

## 10 · 18 initial REUSE_VALID reconciliation

**Population RV3-EV originale**: 18 items · criterio `class_tags:warlock ∩ stat_tags:intellect`.

**Reconciliation post EV-F2**:
| Sub-verdict | Count |
|---|---|
| VALIDATED_REUSE_VALID | **12** (5 armor stoffa/cuoio + 7 accessory universal) |
| DOWNGRADED / NOT_COMPATIBLE (weapon tome/arcane famiglia_esclusa_da_G2) | **6** |
| REJECTED baseline (nessun rejected) | 0 |
| PM_REVIEW residuo | 0 |
| **Total** | **18** |

**Motivazione declassamento 6 weapon**: `tome` univocamente determinata, ∉ {focus, balestra, pugnale}. G2 non ampliata. `arcane` è modifier, non famiglia. PM ratifica declassamento come **FINAL**.

---

## 11 · 49 PM_REVIEW reconciliation

**Population EV-F1/EV-F2**: 49 items · criterio `item_binding_policy:soft ∩ stat_tags:intellect ∩ class_tags∉warlock`.

**Reconciliation post EV-F2**:
| Sub-verdict | Count |
|---|---|
| REUSE_CONDITIONAL confirmed (2 weapon G2 + 11 armor + 19 accessory) | **32** |
| NOT_COMPATIBLE declassati (famiglia_esclusa_da_G2) | **15** |
| Overlap con 6 lore items (arcane_adept_orb + voidpiercer-bow) | **2** |
| **Total** | **49** |

**Overlap 2 items** con 6 lore già adjudicati singolarmente:
- `arcane_adept_orb` → NOT_COMPATIBLE (Opzione A, preserved)
- `voidpiercer-bow` → NOT_COMPATIBLE (retro-branding VIETATO)

**PM_REVIEW residuo post EV-F2**: **0**.

---

## 12 · Weapon proficiency literal lock

**G2 proficiency LOCK** (Cacciatore del Vuoto):
- **Uniche famiglie ammesse**: **focus · balestra · pugnale**
- Mapping DB weapon_tags: `focus`, `dagger` (balestra/crossbow: **complete gap live**)

**Famiglie escluse determinate univocamente** (declassed in EV-F2):
- `staff`, `grimoire`, `wand`, `rod`, `tome`, `bow`, `instrument`, `sonic`, `alchemical_flask`

**Regole finali**:
- `arcane` è modifier (non famiglia)
- Semantic caster overlap (tome/grimoire/wand/staff) **NON** ammette REUSE_CONDITIONAL
- **AFX1 CONSUMA G2**, **NON RIAPRE**, **NON RATIFICA** nuove proficiency
- G2 literal ratificata FINAL da questo closure gate

---

## 13 · 6 warlock tome rejected

**Population**: 6 items warlock+intellect con weapon_tags `[tome, arcane]`.

| slug | weapon_family | primary verdict | condizione |
|---|---|---|---|
| warlock_apprentice_tome | tome | NOT_COMPATIBLE | famiglia_esclusa_da_G2 |
| warlock_hex_grimoire | tome | NOT_COMPATIBLE | famiglia_esclusa_da_G2 |
| warlock_shadowbound_grimoire | tome | NOT_COMPATIBLE | famiglia_esclusa_da_G2 |
| warlock_witchking_codex | tome | NOT_COMPATIBLE | famiglia_esclusa_da_G2 |
| warlock_apprentice_grimoire | tome | NOT_COMPATIBLE | famiglia_esclusa_da_G2 |
| warlock_pact_binder | tome | NOT_COMPATIBLE | famiglia_esclusa_da_G2 |

**Rejection RATIFIED FINAL**: tome ∉ G2 → NOT_COMPATIBLE. Nessuna promozione futura ammessa via AFX1 semantic overlap.

---

## 14 · arcane_adept_orb final disposition

**Item preserved (Opzione A applicata)**:

| Attributo | Valore |
|---|---|
| slug | `arcane_adept_orb` |
| primary verdict | **NOT_COMPATIBLE** |
| item PRESERVED | true |
| class_tags mutation | false |
| rec_classes mutation | false |
| retro-branding | forbidden |
| reassignment a Cacciatore del Vuoto | none |
| secondary `lore_reviewed` | true |
| secondary `identity_conflict` | false (lore compatible ma no mutation) |
| secondary `mutation_required` | true |
| secondary `triggers_future_void_native_item` | true |
| Future Coverage Gap entry | `arcane_adept_orb_void_native_successor` |

**Successor futuro**: nuovo item Vuoto-native con nuovo `item_id`, proficiency focus/balestra/pugnale, stat Intelligenza, weapon family valida. **NO copia nome · NO duplicazione diretta · NO creazione ora**.

---

## 15 · voidpiercer-bow final disposition

**Item preserved · exclusion FINAL**:

| Attributo | Valore |
|---|---|
| slug | `voidpiercer-bow` |
| primary verdict | **NOT_COMPATIBLE** (FINAL) |
| item preserved | true |
| identity_conflict | true |
| mutation_required | true |
| retro_branding_forbidden | true |
| warlock retro-tag | forbidden |
| cacciatore_del_vuoto tag | forbidden |
| stat mutation | forbidden |
| identity rewrite | forbidden |
| weapon_tags | `[bow, ranged]` (bow ∉ G2) |
| rec_classes | assegnato a `cacciatore_di_mostri` (rival class) — strict separation |

**Rejection RATIFIED FINAL**: nome/lore "voidpiercer" non giustifica riuso Vuoto. Regola retro-branding VIETATO applicata.

---

## 16 · Anti-P2W findings

**Audit `can_be_sold_for_real_money`** su 178 items:

| Metrica | Valore |
|---|---|
| Field present | 128/178 (71.9%) |
| Field missing | 50/178 (28.1%) |
| Count `true` | **0** |
| Count `false` | 128 |
| Truthy / non-boolean ambiguo | 0 |
| Anti-P2W verdict | ✅ **PASS documentale** (0 marketable items) |

**Fallback**: se il codice backend applica `default=false` per missing field, i 50 missing sono trattati come `false` runtime. Il fallback è **comportamento code/config** — non valore materializzato. Verifica read-only pre-item-creation / pre-apply / post-apply obbligatoria.

**PM verdict**: PASS con nota **data quality gap OPEN** su 50 missing (§17).

---

## 17 · 50 missing field data-quality gap

**Data Quality Gap RATIFIED**:
- **50 items** senza field `can_be_sold_for_real_money` esplicito
- **NO backfill ora** (mutation vietata)
- **NO auto-derive** (nessuna assunzione runtime che sostituisca il valore mancante con `true`)
- Fallback `missing → false` è **codice/config**, non "valore materializzato"
- Data quality gap deferrito a **gate dedicato futuro** (post-EV chain, post-AFX1)

**Verifica obbligatoria** (PM ratified):
- Pre-item creation → verificare fallback effettivo del codice
- Pre-registry apply → verificare che nessun item nuovo/mutato bypassi fallback
- Post-apply → snapshot per audit anti-P2W preservazione

Il gap resta **OPEN** ma **non blocca** la closure RV3-EV.

---

## 18 · T1 materialized catalog

**Live materialization T1 Aspirante (L1-15)**:
- **178 items** (100% del catalog live)
- Level distinct: `[1, 3, 5, 8, 9, 12]`
- Max live level: **12**

**Vuoto-eligibile T1** (post EV-F2 adjudication):
- REUSE_VALID: 12
- REUSE_CONDITIONAL: 32
- Baseline usable Vuoto T1: **44 items** (12 valid + 32 conditional post additive apply)

**Note critica**: T1 coverage è **partial** — slot canonical incomplete, focus literal sub-materializzato.

---

## 19 · T2–T5 zero live materialization

**Coverage live tier**:
| Tier | Level range | Live items | Vuoto usable |
|---|---|---|---|
| T2 Cacciatore | 16-30 | **0** | 0 |
| T3 Iniziato | 31-45 | **0** | 0 |
| T4 Rituale | 46-55 | **0** | 0 |
| T5 Vuoto endgame | 56-60 | **0** | 0 |

**INCOMPLETE progression T2-T5 CONFIRMED** (PM verdict).

Correzione critica preservata: **L12 = T1 Aspirante**, NON T5. Il finding RV3-EV originale "1 item Int L12 in T5" è **REJECTED** e archiviato come errore superato.

**Cacciatore del Vuoto = ACTIVE-DESIGN-READY · NOT LIVE**: non selezionabile in-game, non implementato runtime, materializzazione progressive prevista T1→T5 in gate futuri (post-AFX1).

---

## 20 · Slot gaps

**Slot canonici target** (14 canonical, PM ratified):
head · neck · shoulders · chest · back · hands · wrist · waist · legs · feet · main_hand · off_hand · ring · accessory

**Alias standard** (PM ratified):
- `belt → waist`
- `cloak / cape → back`
- `trinket → accessory`
- `weapon_main → main_hand`
- `weapon_off → off_hand`
- `main-hand → main_hand`
- `off-hand → off_hand`
- `amulet → neck`

**NO ring1/ring2 · NO trinket come 15° slot · NO DB remapping ora**.

**Slot gaps live**:
- `back` slot missing dal live schema (0 items con `slot_type=back`)
- `slot_type = None` in 21 items (data quality gap, keep as-is)
- Slot taxonomy live coarse (weapon/armor/accessory aggregati) vs canonical 14 granulari

**Gaps → Future Coverage Gap** (§30).

---

## 21 · Armor gaps

**Armor proficiency Vuoto (G2)**: stoffa + cuoio (cloth/robe/light + leather/medium).

**Live coverage armor Vuoto-usable T1**: **16 items** (5 armor warlock REUSE_VALID + 11 armor 47-subset REUSE_CONDITIONAL).

**Armor gaps**:
- Armor T1 canonical slot completeness: partial (aggregate `armor` type non granulare per canonical slot)
- Armor T2-T5 Vuoto: **0 items live** → complete gap
- Armor tags coverage parziale (46/178 items con armor_tags, alias-first partial)

**Future need**: ~48-72 armor Vuoto items T2-T5 (6 canonical slot × 4 tier × 1-3 rarity + Legendary).

---

## 22 · Weapon gaps

**Weapon proficiency Vuoto (G2 literal LOCK)**: focus · balestra · pugnale.

**Live coverage weapon Vuoto-usable**: **2 items** (focus/dagger literal REUSE_CONDITIONAL).

**Weapon gaps**:
- `focus` literal sub-materializzato (0-2 items T1)
- `crossbow / balestra`: **0 items live** — famiglia complete gap
- `pugnale / dagger` warlock/vuoto identity: minimale
- Weapon T2-T5 Vuoto: 0 items → complete gap

**Future need**: ~24-36 weapon Vuoto items T1-T5 (3 famiglie × 4-5 tier × 1-2 rarity).

---

## 23 · Accessory gaps

**Accessory slot** (universal, no proficiency constraint).

**Live coverage accessory Vuoto-usable T1**: **26 items** (7 accessory warlock REUSE_VALID + 19 accessory 47-subset REUSE_CONDITIONAL).

**Accessory gaps**:
- T1 accessory Vuoto: sufficient (26 items)
- T2-T5 accessory Vuoto: 0 items → complete gap
- Ring / neck / trinket canonical slot: sub-materializzati (1 ring, 5 amulet=neck alias, 0 trinket dedicati)

**Future need**: ~30-45 accessory Vuoto items T2-T5.

---

## 24 · Focus T1 gap

**PM CONFIRMED gap literal**:
- Weapon proficiency `focus` è **gap literal T1** (0-2 items focus tag literal)
- G2 non modificabile (locked)
- Retro-branding forbidden (nessuna promozione tome/wand/staff/grimoire a "focus")
- Item creation `focus` T1-T5 tracciato in **Future Coverage Gap** (§30)

**Nessuna autorizzazione item creation** da questo gate. Materializzazione focus rinviata a gate dedicato futuro **post AFX1 closure**.

---

## 25 · Canonical 110–130 envelope

**Coverage envelope PM baseline** (Cacciatore del Vuoto full identity):
- **Range**: 110-130 items
- **Planning center**: ~120 items
- **Status**: **LOCK design baseline** (PM ratified)

**Interpretazione**:
- Baseline "playable Vuoto" = single-rarity per canonical slot per tier
- Envelope include: 14 slot canonical × 5 tier × ~1.5 rarity avg + shared caster items + universal

**Envelope resta LOCK anche post-closure RV3-EV**. Nessun aggiornamento envelope autorizzato senza PM directive dedicata.

---

## 26 · Advisory 180–220 interpretation

**Advisory max scenario**:
- **Range**: 180-220 items
- **Status**: **NON-BINDING · NOT LOCKED · NOT TARGET PM**

**Interpretazione**:
- Scenario massimo per full Vuoto identity (multi-rarity + shared caster + universal + Legendary depth)
- +50-100 items rispetto envelope baseline
- **Non è target di planning** — è advisory scenario per orientamento gate futuri

**Non autorizza**:
- Item creation
- Registry v3 apply
- Aggiornamento envelope
- Modifica G2 / proficiency / stat / slot

---

## 27 · Alias-first metadata strategy

**Strategia alias-first RATIFIED** (design-only):

| Field target | Alias source | Coverage live |
|---|---|---|
| `armor_type` | `armor_tags` (list) | 46/178 (partial) |
| `weapon_family` | `weapon_tags` (list) | 61/178 (partial) |
| `tier` | derivato da `required_adventurer_level` | derivable HIGH confidence |
| `ilvl` | derivato da rarity_offset + required_level | derivable HIGH confidence post PM lock |
| `slot_canonical` | mapping alias (§20) | design-only, no DB remapping |

**Nessuna field addition** ora. Nessun rename. Nessun backfill. **AFX1 documenterà alias contratti per futuro Registry v3 additive** (non ora).

---

## 28 · ILVL canonical formula

**LOCK** (PM ratified in EV-F2 + closure):

```
rarity_offset:
  Common    = +0
  Uncommon  = +2
  Rare      = +3
  Epic      = +4
  Legendary = +5

ilvl(item) = min( max( required_level + rarity_offset[rarity], tier_min[tier] ), 60 )

tier_min:
  T1 = 1  · T2 = 16  · T3 = 31  · T4 = 46  · T5 = 56

Legendary anchor: ilvl(Legendary) = 60
```

**Nessuna riapertura C3**. Formula ratificata come standard di derivazione read-only per tutti i gate futuri.

**Applicabilità**: design-only in questa closure. Runtime apply richiede gate dedicato futuro (post AFX1).

---

## 29 · Slot taxonomy

**14 slot canonici LOCK**:
head · neck · shoulders · chest · back · hands · wrist · waist · legs · feet · main_hand · off_hand · ring · accessory

**Alias mapping standard** (§20 dettagliata):
- belt → waist
- cloak / cape → back
- trinket → accessory
- weapon_main → main_hand
- weapon_off → off_hand
- main-hand → main_hand
- off-hand → off_hand
- amulet → neck

**Divieti**:
- NO `ring1` / `ring2` (ring resta single canonical slot)
- NO trinket come 15° slot
- NO DB remapping ora
- NO rename/backfill/migrazione via AFX1
- AFX1 documenterà alias contratti come design-only

Slot taxonomy resta **read-only** fino a gate dedicato canonicalizzazione slot futuro (post AFX1).

---

## 30 · Future coverage gap

**Future Coverage Gap** (separato dal ledger live 178):

| Gap component | Estimate |
|---|---|
| T2 Cacciatore Vuoto items | 22-35 |
| T3 Iniziato Vuoto items | 22-35 |
| T4 Rituale Vuoto items | 22-35 |
| T5 Vuoto endgame items | 22-35 |
| `arcane_adept_orb_void_native_successor` | 1 |
| Slot canonical materialization (back/shoulders/hands/wrist/waist/legs/feet) T1-T5 | 20-30 |
| Focus literal weapon materialization T1-T5 | 8-12 |
| Crossbow/balestra weapon materialization T1-T5 | 8-12 |
| Legendary Vuoto identity items | 5-15 |
| Shared caster items | 15-25 |
| Universal slot expansion | 15-25 |

**Envelope baseline PM lock**: **110-130** (center ~120)
**Advisory max scenario**: **180-220** (NON-BINDING)

**Governance FUTURE COVERAGE GAP**:
- `item_creation_authorized = false`
- `registry_v3_apply_authorized = false`
- `field_addition_authorized = false`
- `no_backfill`
- `no_copy_of_existing_names`

Materializzazione rinviata a gate dedicati futuri **post-AFX1**.

---

## 31 · AFX1 dependency

**R18.6.RV3-AFX1 · Affix Vocabulary & Pool Contract**:
- **Status**: **HOLD** (kickoff solo post-closure RV3-EV formale + nuovo verdict PM dedicato)
- **Prerequisites** documentati in EV-F1 §40 (7 punti):
  1. Vocabulary base T1-T5
  2. Schema validation rules
  3. Compatibility mapping
  4. Null handling policy (no backfill)
  5. Applicability audit read-only su 178 items
  6. PM ratify vocabulary lock
  7. Registry v3 additive design_only (nessuna field addition)
- **AFX1 CONSUMA G2** (non modifica proficiency)
- **AFX1 NON riapre** decisioni EV-F2 (adjudication finale)
- **AFX1 NON ratifica** nuove weapon family
- **AFX1 documenterà alias contratti** per futuro Registry v3 additive

**AFX1 non parte in questo dispatch**. Attende nuovo verdict PM dopo closure formale RV3-EV.

---

## 32 · Registry v3 apply status

**Registry v3 apply**: **NOT AUTHORIZED**.

**Constraints preservati**:
- Nessun apply di field addition
- Nessun apply di `rec_classes` bulk (batch futura solo con explicit allowlist + per-item verdict + condition code + omogeneità + no mutation + no dynamic keyword selection + dry-run + snapshot + PM GO esplicito — vedi F2-Q2)
- Nessun apply di slot canonicalization
- Nessun apply di alias documentation runtime
- Nessun apply di ILVL formula runtime

**Registry v3 architettura** resta documentale (design-only). Apply gate dedicato futuro post AFX1.

---

## 33 · Item creation status

**Item creation**: **NOT AUTHORIZED**.

**Constraints preservati**:
- Nessun item Vuoto-native creato
- Nessun `arcane_adept_orb_void_native_successor` creato
- Nessun focus T1-T5 creato
- Nessun T2-T5 Vuoto creato
- Nessun crossbow/balestra creato
- Nessun universal slot back/shoulders creato

**Item creation** rinviata a gate dedicati futuri **post AFX1 closure**. Nessun impulso di creation ammesso da questa closure.

---

## 34 · Risk register

**Rischi tracciati post-closure RV3-EV**:

| ID | Risk | Severity | Status |
|---|---|---|---|
| CLR-R1 | Retro-branding voidpiercer/arcane_adept_orb | HIGH → mitigated | MITIGATED (rejection FINAL) |
| CLR-R2 | Identity contamination mago/necromante/bardo | MEDIUM | HOLD (Registry v3 additive selectivo) |
| CLR-R3 | Cross-class Cacciatore di Mostri overlap | MEDIUM | MITIGATED (strict separation LOCK) |
| CLR-R4 | Coverage T2-T5 zero live | HIGH design | HOLD (Future Coverage Gap) |
| CLR-R5 | armor_tags coverage parziale (46/178) | LOW | ACCEPTED |
| CLR-R6 | 50 items missing `can_be_sold_for_real_money` | LOW-MEDIUM | ACCEPTED (data quality gap OPEN) |
| CLR-R7 | 21 items `slot_type=None` | LOW | ACCEPTED (keep as-is) |
| CLR-R8 | Slot taxonomy live coarse | MEDIUM | HOLD (gate dedicato futuro) |
| CLR-R9 | Focus literal sub-materialized | HIGH design | HOLD (Future Coverage Gap) |
| CLR-R10 | Legacy warlock bridge (R18.3e) | LOW | ACCEPTED (bridge sealed) |
| CLR-R11 | AFX1 pressure to reopen G2 | HIGH governance | MITIGATED (LOCK G2 literal, AFX1 consuma G2) |
| CLR-R12 | Registry v3 apply pressure | HIGH governance | MITIGATED (NOT AUTHORIZED lock) |

**Nessun rischio blocca la closure RV3-EV**. Rischi HOLD sono tutti tracciati a gate futuri dedicati.

---

## 35 · Governance evidence

**Evidence chain**:

| Check | Result |
|---|---|
| `pytest backend/tests/backend_r18_4_sealed_integrity_test.py` | 6 passed · 36/36 byte-identical |
| `lore_meta.py` SHA anchor | `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` invariato |
| backend changes | **0** |
| frontend changes | **0** |
| scripts changes | **0** |
| tests changes | **0** |
| OpenAPI changes | **0** |
| DB writes | **0** |
| Migration files | **0** |
| Item creation | **0** |
| Registry v3 apply | **0** |
| Field addition | **0** |
| Backfill | **0** |
| Class_slug write | **0** |
| Mutation su 178 items | **0** |

**Immutability preservata**:
- RV3-EV originale MD + JSON: IMMUTABLE
- EV-F1 MD + JSON: IMMUTABLE post-approval
- EV-F2 MD + JSON: IMMUTABLE post-approval (post accounting micro-fix)
- Pilot Certificate + Manifest R18.6.3: IMMUTATI
- R18.3f corpus (originale + R1 audit + closure report + closure manifest): IMMUTATI
- Sealed 36 artifact byte-identical

Governance CLEAN. Zero deviations.

---

## 36 · Final STOP state

```
╔══════════════════════════════════════════════════════════════════╗
║             R18.6.RV3-EV · FINAL CLOSURE STATE                   ║
╠══════════════════════════════════════════════════════════════════╣
║  Cacciatore del Vuoto     = ACTIVE-DESIGN-READY (NOT LIVE)       ║
║  R18.3f                   = CLOSED                               ║
║  R18.6.RV3-EV             = CLOSED                               ║
║  R18.6.RV3-EV-F1          = CLOSED                               ║
║  R18.6.RV3-EV-F2          = CLOSED                               ║
║  R18.6.RV3-AFX1           = HOLD (post-closure PM directive)     ║
║  Registry v3 item gen     = NOT AUTHORIZED                       ║
║  Registry v3 apply        = NOT AUTHORIZED                       ║
║  Field addition           = NOT AUTHORIZED                       ║
║  Field backfill           = NOT AUTHORIZED                       ║
║  Item creation            = NOT AUTHORIZED                       ║
║  Gate 11                  = HOLD                                 ║
║  Monaco (Wave 1)          = HOLD                                 ║
║  Druido/Alchimista/Bardo/Negromante (Wave 1) = HOLD              ║
║  Sealed integrity         = 36/36 PASS                           ║
║  lore_meta.py anchor      = INVARIATO                            ║
║  Backend/Frontend/OpenAPI = 0 modifications                      ║
║  DB writes                = 0                                    ║
║  PRD append               = RV3-EV CLOSED section only           ║
╚══════════════════════════════════════════════════════════════════╝
```

**🛑 EXPLICIT STOP FINALE · RV3-EV CLOSED · ATTENDO NUOVO VERDICT PM PER PROSSIMO GATE**

Non avviare AFX1 in questo dispatch. Non avviare Gate 11. Non avviare Wave 1. Non avviare Registry v3 apply. Nessun auto-start su gate successivi.
