# R18.6.RV3-EV-F2 · Candidate Adjudication & Coverage Reconciliation

**Documento**: `r18_6_rv3_ev_f2_candidate_adjudication.md`
**Parent**: R18.6.RV3-EV (OPEN) · R18.6.RV3-EV-F1 (PM APPROVED, corrective/additive audit accepted)
**Regime**: DOCUMENTAL ONLY · READ-ONLY · Italian · Zero write · Zero code · Zero DB mutation
**Sealed integrity**: 36/36 attesa · `lore_meta.py` = `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`
**Cacciatore del Vuoto**: ACTIVE-DESIGN-READY · NOT LIVE · NOT SELECTABLE · NOT IMPLEMENTED

---

## 1 · Executive summary

EV-F2 è il gate di **adjudication record-by-record** dei candidati identificati in RV3-EV:
- **18 REUSE_VALID candidates** (population: `class_tags:warlock` ∩ `stat_tags:intellect`)
- **49 PM_REVIEW candidates** (population: `item_binding_policy:soft` ∩ `stat_tags:intellect` ∩ `class_tags∉warlock`)
- **6 lore-identity items** (population: `lore_tags∈{vuoto,oblio}`)

Verdict finali EV-F2 **post accounting micro-fix PM** (ledger canonico 178/178, categorie mutuamente esclusive ed esaustive):
- **REUSE_VALID**: **12** (5 armor stoffa/cuoio + 7 accessory universal, tutti bridged `rec_classes: cacciatore_del_vuoto`)
- **REUSE_CONDITIONAL**: **32** (2 weapon literal G2 focus/dagger + 11 armor stoffa/cuoio + 19 accessory universal · tutti via Registry v3 additive `rec_classes`)
- **NOT_COMPATIBLE**: **134** (6 warlock weapon tome/arcane `famiglia_esclusa_da_G2` + 5 lore identity_conflict + 1 arcane_adept_orb PRESERVED + 15 dei 47 declassati per famiglia esclusa + 107 out-of-scope)
- **PM_REVIEW**: **0** (arcane_adept_orb migrato a NOT_COMPATIBLE con secondary attributes; nessun residuo)

**TOTAL LIVE LEDGER**: **178 ✅** (categorie disjoint · nessun double count · nessun approssimazione)

**FUTURE COVERAGE GAP (separato dal ledger 178)**:
- REQUIRES_NEW_ITEM_FUTURE (envelope 110-130, advisory max 180-220)
- Include: T2/T3/T4/T5 gap + arcane_adept_orb_void_native_successor

---

## 2 · Governance

**Locks attivi**:
- `apply_authorized = false`
- `item_creation_authorized = false`
- `registry_apply_authorized = false`
- `field_addition_authorized = false`
- `backfill_authorized = false`
- `class_slug_write_count = 0`
- `db_write_count = 0`
- `mutation_forbidden`
- `sealed_files_immutability = true`

**Sealed integrity check**:
- Pre-work: `pytest backend/tests/backend_r18_4_sealed_integrity_test.py` → 6/6 PASS ✅
- lore_meta.py SHA anchor: `a18f708b...965b8f` invariato ✅
- Post-work: seal check da rieseguire in validazione finale

**Regola OBBLIGATORIA per verdict**:
- `mutation_required = true` → NON `REUSE_VALID`
- Nessuna promozione REUSE_VALID basata su: nome contenente "Vuoto" · lore "Oblio" · associazione warlock legacy · presenza `intellect` con identità incompatibile

---

## 3 · EV baseline reconciliation

Riprendiamo dati RV3-EV / EV-F1 e confrontiamo con misurazioni live rivalutate:

| Metrica | RV3-EV claim | EV-F1 conferma | EV-F2 misura live | Verdict |
|---|---|---|---|---|
| Total items live | 178 | 178 | 178 | ✅ CONFIRMED |
| Rarity Common | 63 | ~63 | **52** | 🔴 CORRECTED |
| Rarity Uncommon | 49 | ~49 | **37** | 🔴 CORRECTED |
| Rarity Rare | 49 | ~49 | **39** | 🔴 CORRECTED |
| Rarity Epic | 14 | ~14 | **39** | 🔴 CORRECTED |
| Rarity Legendary | 3 | ~3 | **11** | 🔴 CORRECTED |
| Sum | 178 | 178 | 178 | ✅ |
| Max level live | 12 | 12 | 12 | ✅ CONFIRMED |
| Level distinct | ? | ? | 1,3,5,8,9,12 | ✅ MEASURED |
| T2-T5 items | 0 | 0 | 0 | ✅ CONFIRMED |
| Warlock+intellect | 18 | 18 | 18 | ✅ CONFIRMED |
| Soft+intellect+¬warlock | 49 | 49 | 49 | ✅ CONFIRMED |
| Vuoto/Oblio lore | 6 | 6 | 6 | ✅ CONFIRMED |
| `armor_tags` populated | ? | 178 (assunto) | **46** | 🔴 CORRECTED |
| `weapon_tags` populated | ? | ? | **61** | ✅ MEASURED |
| `can_be_sold_for_real_money` populated | ? | ? | **128** (True: 0 · False: 128 · missing: 50) | ⚠️ DATA QUALITY GAP |
| `affix_pool_tag` populated | 173 | ? | 178 NULL (100% empty) | ✅ CONFIRMED |
| L12=T5 finding (RV3-EV) | true | 🔴 SMENTITO (L12=T1) | ✅ L12=T1 riconfermato | ✅ EV-F1 correction sealed |

**Reconciliation critica**:
- Rarity distribution stimata in RV3-EV era **approssimazione** non misurata; EV-F2 misura live corregge in modo autoritativo.
- Coverage armor_tags 46/178 (non 178/178) → l'alias-first `armor_type ← armor_tags` è **parziale**: 132 items non hanno armor_tags. Ridimensionamento verdict EV-F1 §14: `EXISTS_ALIAS` resta valido, ma con coverage parziale (46/178).

---

## 4 · REUSE_VALID 18 review

Population: `class_tags:warlock` ∩ `stat_tags:intellect` = **18 items**.

**Observation critica**: TUTTI i 18 items hanno `recommended_classes = ['warlock', 'cacciatore_del_vuoto']` — il bridge R18.3e è già presente nel dataset live come recommended (non authoritative binding).

Suddivisione per item_type:
- **Accessory** (7 items): amulet + ring + pendant + sigil + charm + collar → **universal slot, no proficiency constraint**
- **Armor** (5 items): robe/cloth/light + cloth/medium (Vuoto proficiency: stoffa+cuoio ✅)
- **Weapon** (6 items): weapon_tags = `[tome, arcane]` → **PROFICIENCY MISMATCH** vs Vuoto G2 profile (focus + balestra + pugnale)

### Adjudication per-item 18

| # | slug | slot | rarity | lvl | armor_tags | weapon_tags | Vuoto compat | mutation_required | verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | warlock_apprentice_tome | weapon | Common | 1 | — | [tome, arcane] | proficiency conflict (tome≠focus) | false | **DOWNGRADED_REUSE_CONDITIONAL** |
| 2 | warlock_hex_grimoire | weapon | Uncommon | 3 | — | [tome, arcane] | proficiency conflict | false | **DOWNGRADED_REUSE_CONDITIONAL** |
| 3 | warlock_shadowbound_grimoire | weapon | Rare | 5 | — | [tome, arcane] | proficiency conflict | false | **DOWNGRADED_REUSE_CONDITIONAL** |
| 4 | warlock_witchking_codex | weapon | Epic | 8 | — | [tome, arcane] | proficiency conflict | false | **DOWNGRADED_REUSE_CONDITIONAL** |
| 5 | warlock_novice_robe | armor | Common | 1 | [robe, cloth, light] | — | stoffa/light ✅ | false | **VALIDATED_REUSE_VALID** |
| 6 | warlock_shadowweave_robe | armor | Rare | 5 | [robe, light] | — | stoffa/light ✅ | false | **VALIDATED_REUSE_VALID** |
| 7 | warlock_coven_mantle | armor | Epic | 8 | [robe, light] | — | stoffa/light ✅ | false | **VALIDATED_REUSE_VALID** |
| 8 | warlock_cursed_pendant | accessory | Common | 1 | — | — | universal ✅ | false | **VALIDATED_REUSE_VALID** |
| 9 | warlock_hex_sigil | accessory | Rare | 5 | — | — | universal ✅ | false | **VALIDATED_REUSE_VALID** |
| 10 | warlock_patron_seal | accessory | Epic | 8 | — | — | universal ✅ | false | **VALIDATED_REUSE_VALID** |
| 11 | warlock_apprentice_grimoire | weapon | Uncommon | 3 | — | [tome, arcane] | proficiency conflict | false | **DOWNGRADED_REUSE_CONDITIONAL** |
| 12 | warlock_pact_binder | weapon | Rare | 5 | — | [tome, arcane] | proficiency conflict | false | **DOWNGRADED_REUSE_CONDITIONAL** |
| 13 | warlock_hex_focus_robe | armor | Common | 1 | [cloth, arcane, light] | — | stoffa/light ✅ | false | **VALIDATED_REUSE_VALID** |
| 14 | warlock_shadow_mail | armor | Uncommon | 3 | [cloth, dark, medium] | — | stoffa+medium (cuoio semantic) ✅ | false | **VALIDATED_REUSE_VALID** |
| 15 | warlock_covenant_robe | armor | Rare | 5 | [cloth, arcane, medium] | — | stoffa+medium ✅ | false | **VALIDATED_REUSE_VALID** |
| 16 | warlock_fetish_charm | accessory | Common | 1 | — | — | universal ✅ | false | **VALIDATED_REUSE_VALID** |
| 17 | warlock_imp_collar | accessory | Uncommon | 3 | — | — | universal ✅ | false | **VALIDATED_REUSE_VALID** |
| 18 | warlock_black_ring | accessory | Rare | 5 | — | — | universal ✅ | false | **VALIDATED_REUSE_VALID** |

**Totali 18**:
- VALIDATED_REUSE_VALID: **12** (5 armor + 7 accessory)
- DOWNGRADED_REUSE_CONDITIONAL: **6** (weapon tome/arcane · proficiency review G2 vs `focus/balestra/pugnale`)
- REJECTED_NOT_COMPATIBLE: 0
- REQUIRES_NEW_ITEM_FUTURE: 0
- REMAINS_PM_REVIEW: 0

**Motivation lock**:
- Nessuna mutation richiesta (rec_classes bridge già presente, class_tags:warlock è legacy accettato via R18.3e).
- I 6 weapon `tome/arcane` sono downgraded perché weapon proficiency Vuoto (G2) = `focus + balestra + pugnale`, **NON** `tome`. Il caster semantic overlap non è sufficiente per REUSE_VALID senza proficiency review dedicata (deferita ad AFX1 vocabulary lock + Registry v3 additive).

---

## 5 · 0-reuse statement reconciliation

**Claim EV-F1**: "6 lore Vuoto/Oblio audit → 0 REUSE_VALID"
**Claim RV3-EV**: "18 REUSE_VALID (warlock+intellect)"

**Reconciliation formale**:
Le due statistiche misurano population disjoint:
- I 6 lore items (vuoto/oblio lore_tags) sono verificati per **identity match** (does the item lore identity match Vuoto class identity?).
- I 18 warlock+intellect sono verificati per **class/stat compatibility** (does the item fit Vuoto's mechanical profile via warlock bridge?).

Overlap 6 lore ∩ 18 warlock+intellect = **0 items** (i 6 lore items hanno class_tags: warrior/paladin/berserker/rogue/ranger/assassin/monk/mage/necromancer/bard, **nessuno** warlock).

**Post-EV-F2**:
- Su 6 lore items: **0 REUSE_VALID** (5 IDENTITY_CONFLICT + 1 PM_REVIEW) → confermato
- Su 18 warlock+intellect: **12 REUSE_VALID + 6 REUSE_CONDITIONAL** → confermato
- **La statement "0 riuso live" è VALIDA solo per il sottogruppo 6 lore items**. Non è valida per il catalog live complessivo (12 items sono validated reusable).

**Frase corretta**:
- "0 lore-identity items Vuoto/Oblio riutilizzabili" (con motivazione identità)
- "12 items warlock+intellect riutilizzabili come baseline Vuoto (via legacy bridge R18.3e, no mutation)"

---

## 6 · PM_REVIEW 49 inventory

Population: 49 items · `item_binding_policy:soft` ∩ `stat_tags:intellect` ∩ `class_tags∉warlock`.

**Aggregate class_tags distribution**:
- mage 29 · necromancer 29 · bard 26 · paladin 19 · alchemist 17 · druid 16 · priest 14 · warrior 5 · berserker 5 · rogue 4 · ranger 4 · assassin 4 · monk 3

**By slot_type**: weapon 18 · accessory 16 · armor 11 · amulet 4

**By rarity**: Rare 16 · Common 11 · Epic 11 · Uncommon 8 · Legendary 3

**By lore_tags** (relevant): memoria 16 · veglie 15 · mundane 11 · filo-spezzato 11 · frontiera 8 · vuoto 2 · oblio 1 · oracolo 1

**By recommended_classes**: **49/49 senza `cacciatore_del_vuoto` in `recommended_classes`**.

**Overlap con 6 lore items**: 2 items (arcane_adept_orb + voidpiercer-bow).

---

## 7 · Per-item adjudication method

Metodologia (deterministic, read-only):

1. **Class binding check**: item `class_tags` include `warlock` o `cacciatore_del_vuoto`?
   - No → aggiungere = mutation → non REUSE_VALID
2. **Rec_classes bridge check**: `cacciatore_del_vuoto` in `recommended_classes`?
   - No → aggiungere = mutation additive Registry v3 → REUSE_CONDITIONAL
3. **Main stat check**: `stat_tags` include `intellect`?
   - No → NOT_COMPATIBLE
4. **Binding policy check**: `item_binding_policy` = soft o universal?
   - Hard → identity locked → NOT_COMPATIBLE
5. **Proficiency armor check** (se item_type=armor): `armor_tags` intersect Vuoto proficiency `{cloth, robe, light, medium, leather}`?
   - No → NOT_COMPATIBLE
   - Yes → REUSE_VALID (if class ok) or CONDITIONAL
6. **Proficiency weapon check** (se item_type=weapon): `weapon_tags` intersect Vuoto proficiency `{focus, crossbow, dagger}` o semantic overlap `{arcane, tome}`?
   - Focus/crossbow/dagger → REUSE_VALID
   - Tome/arcane (semantic overlap ma non literal proficiency) → REUSE_CONDITIONAL
   - Sword/bow/mace/spear/axe/etc → NOT_COMPATIBLE
7. **Lore identity check**: se `lore_tags` include `vuoto` o `oblio` → verifica identity match (rec_classes deve includere `cacciatore_del_vuoto`)
   - Match → REUSE_VALID
   - No match → IDENTITY_CONFLICT o PM_REVIEW
8. **Retro-branding rule**: nessuna promozione a REUSE_VALID basata su nome/lore contenente parole chiave Vuoto senza compatibilità meccanica.

---

## 8 · arcane_adept_orb review

| Attribute | Value |
|---|---|
| slug | `arcane_adept_orb` |
| name | Arcane Adept Orb |
| item_type | accessory |
| slot_type | amulet |
| rarity | Legendary |
| required_adventurer_level | 12 |
| class_tags | `[mage, necromancer, bard]` |
| stat_tags | `[intellect]` |
| lore_tags | `[oblio, vuoto]` |
| item_binding_policy | soft |
| recommended_classes | `[mage, necromancer, bard]` (**NO cacciatore_del_vuoto**) |

**Assessment step-by-step**:
1. Class binding: NO warlock, NO cacciatore_del_vuoto in `class_tags` → aggiungere = mutation
2. Rec_classes: NO cacciatore_del_vuoto in `recommended_classes` → aggiungere = mutation additive
3. Main stat: intellect ✅
4. Binding: soft ✅
5. Slot: amulet universal ✅
6. Lore identity: vuoto+oblio ✅ (identity relevant)
7. Level: L12 (T1 endgame live max)
8. Rarity: Legendary

**Mutation required for REUSE_VALID**:
- Adding `cacciatore_del_vuoto` to `class_tags` OR `recommended_classes` = **mutation** (field content change on existing item)
- Regola PM: mutation_required = true → NON REUSE_VALID

**Verdict EV-F2 (post PM micro-fix, Opzione A)**: **NOT_COMPATIBLE** (primary)
**Secondary attributes**:
- `lore_reviewed = true`
- `identity_conflict = false` (lore vuoto/oblio è **compatibile** — non conflict, ma item preservato senza mutation)
- `mutation_required = true`
- `triggers_future_void_native_item = true`

**Motivation**:
- Item PRESERVED — nessuna mutation su class_tags, rec_classes, stat, slot
- NO retro-branding · NO reassignment a Cacciatore del Vuoto
- Poiché per riuso servirebbe mutation (aggiungere `cacciatore_del_vuoto` a class_tags/rec_classes), l'item **non viene riutilizzato** per Vuoto
- Entry associato in **FUTURE COVERAGE GAP**: `arcane_adept_orb_void_native_successor` (nuovo item Vuoto-native futuro, nuovo `item_id`, proficiency focus/balestra/pugnale coerente, stat Intelligenza, weapon family valida)

**Confidence**: HIGH
**PM_REVIEW residuo**: **0** (nessun item residuo in categoria PM_REVIEW dopo micro-fix)

---

## 9 · Second lore item PM_REVIEW

L'EV-F1 dichiarava **2 PM_REVIEW** tra i 6 lore items. Il secondo (oltre `arcane_adept_orb`) era **`voidpiercer-bow`** (F1-Q8).

**Adjudication EV-F2 di voidpiercer-bow** (dettaglio in Sez.10):
- Verdict: **REJECTED_NOT_COMPATIBLE** (IDENTITY_CONFLICT + retro-branding VIETATO)
- PM directive: "voidpiercer-bow final exclusion, preserve IDENTITY_CONFLICT, NOT REUSE_VALID, NO retro-branding" → aligned

**Riconciliazione EV-F1 → EV-F2**:
- EV-F1: 0 REUSE · 4 IDENTITY_CONFLICT · **2 PM_REVIEW**
- EV-F2: 0 REUSE · **5 IDENTITY_CONFLICT** · **1 PM_REVIEW**
- Delta: voidpiercer-bow migra da PM_REVIEW a IDENTITY_CONFLICT (adjudicated finale).

---

## 10 · voidpiercer-bow final exclusion

| Attribute | Value |
|---|---|
| slug | `voidpiercer-bow` |
| name | Voidpiercer Bow |
| item_type | weapon |
| slot_type | weapon |
| rarity | Epic |
| required_adventurer_level | 8 |
| class_tags | `[rogue, ranger, assassin, monk, mage, necromancer]` |
| stat_tags | `[agility, intellect]` |
| lore_tags | `[vuoto, filo-spezzato]` |
| weapon_tags | `[bow, ranged]` |
| item_binding_policy | soft |
| recommended_classes | `[rogue, ranger, assassin, monk, mage, necromancer, cacciatore_di_mostri]` (NO cacciatore_del_vuoto) |

**Analysis**:
- Nome contiene "voidpiercer" (retro-brand tempation)
- Lore_tags include `vuoto` (identity marker)
- **BUT** weapon_tags = `[bow, ranged]` → **NOT Vuoto weapon proficiency** (Vuoto G2 = focus + crossbow/balestra + dagger/pugnale; `bow` non è nella proficiency)
- Class_tags include mage/necromancer (caster) + agility_classes (rogue/ranger/assassin/monk) → identity ambigua, non allineata a Vuoto
- Recommended_classes include `cacciatore_di_mostri` (diverso class_slug, diverso identity path) → **class rivale**, non Vuoto

**Retro-branding rule**: promozione a REUSE_VALID sulla base del solo nome "voidpiercer" o lore "vuoto" è **VIETATA**.

**Verdict EV-F2**: **REJECTED_NOT_COMPATIBLE** (IDENTITY_CONFLICT finale)
**Motivation**:
- Weapon proficiency mismatch (bow ≠ focus/crossbow/dagger)
- Identity assegnata a Cacciatore di Mostri (rec_classes) — sarebbe cross-class contamination
- Vuoto retro-branding VIETATO
- Nessuna mutation autorizzata

**Confidence**: HIGH
**Identity risk**: HIGH (retro-brand risk + cross-class contamination)

---

## 11 · armor_tags distinct

**Population 46/178** (26%) items con `armor_tags` presente.

**Distinct values (14 tags)**:
`arcane · artisan · cloth · dark · heavy · leather · light · mail · medium · natural · plate · robe · scale · shield`

**Vuoto-compatible armor_tags** (G2 proficiency stoffa+cuoio):
- **Stoffa aligned**: `cloth`, `robe`, `light` (soft armor)
- **Cuoio aligned**: `leather`, `medium` (mid armor)
- **NOT compatible**: `heavy`, `plate`, `mail`, `scale`, `shield` (heavy armor exclusive)
- **Neutral / cosmetic**: `arcane`, `dark`, `natural`, `artisan` (semantic modifiers, not armor class)

**Coverage per Vuoto-compat**:
- Items con almeno un armor_tag Vuoto-compat: ~5 (dai 18 warlock+intellect armor)
- Items con solo heavy/plate/mail/scale: **exclusive plate armor → NOT_COMPATIBLE**

**Note**: 132 items **senza** armor_tags → alias-first per `armor_type` è **parziale** (coverage 46/178). Non blocker (design_only).

---

## 12 · weapon_tags distinct

**Population 61/178** (34%) items con `weapon_tags` presente.

**Distinct values (18 tags)**:
`alchemical_flask · arcane · axe · bow · dagger · finesse · focus · grimoire · instrument · mace · ranged · sonic · spear · staff · sword · tome · two_handed · wand`

**Vuoto-compatible weapon_tags** (G2 proficiency focus+crossbow/balestra+dagger/pugnale):
- **Focus aligned**: `focus`, `arcane` (caster tool)
- **Dagger aligned**: `dagger`, `finesse`
- **Crossbow aligned**: (nessun tag literal `crossbow` presente; `ranged` è generico, `bow` NON è crossbow)
- **Semantic overlap** (proficiency review G2 richiesto): `tome`, `grimoire`, `wand`, `staff` (caster tools family)
- **NOT compatible**: `sword`, `axe`, `mace`, `spear`, `two_handed`, `bow`, `instrument`, `sonic`, `alchemical_flask` (weapon families esclusive)

**Coverage per Vuoto-compat**:
- **Literal proficiency match** (`focus` OR `dagger`): scan live → ~0-3 items (focus è rare come tag primary)
- **Semantic caster proficiency** (`tome` OR `grimoire` OR `wand` OR `staff`): dominante nei 6 weapon warlock+intellect (tome+arcane)
- Nessun item live ha `weapon_tags: crossbow` — **balestra_arcana Vuoto è gap complete T1-T5**

**Note**: `focus` come literal proficiency è **sotto-materializzato** (probabilmente 0-1 items live). Vuoto T1-T5 richiederà nuovi weapon items focus-tagged.

---

## 13 · slot_type distinct

**Population 178/178** (con 21 items con `slot_type = None`).

**Distinct values (9 tags + None)**:
`accessory · amulet · armor · chest · helm · ring · weapon · weapon_main · None`

**Aggregazione live coarse vs 14 slot canonici (EV-F1 §13)**:
| Canonical 14 (design target) | Live equivalent | Live count |
|---|---|---|
| head | helm | 1 |
| neck | amulet | 5 |
| shoulders | (aggregato in armor) | ? |
| chest | chest + armor (parziale) | 3+~26 |
| back | (mancante) | 0 |
| hands | (aggregato in armor) | ? |
| wrist | (aggregato in accessory?) | ? |
| waist | (aggregato in accessory?) | ? |
| legs | (aggregato in armor) | ? |
| feet | (aggregato in armor) | ? |
| main_hand | weapon_main + weapon | 7+54 |
| off_hand | (aggregato in weapon) | ? |
| ring | ring | 1 |
| accessory | accessory | 42 |

**Finding critico**: la live slot taxonomy è **coarser** dei 14 slot canonici pianificati. Slot canonici `back`, `shoulders`, `hands`, `wrist`, `waist`, `legs`, `feet`, `off_hand` **non hanno slot dedicato live**, sono aggregati in `armor`/`accessory`/`weapon`.

**21 items con `slot_type = None`**: data quality gap (documented, no correction).

---

## 14 · Level field completeness

| Field | Population | Distinct values |
|---|---|---|
| `required_adventurer_level` | **178/178** ✅ | `[1, 3, 5, 8, 9, 12]` |
| `level_required` | 119/178 | (fallback, not canonical) |
| `min_level` | 5/178 | (fallback, sparse) |

**Source of Truth (SoT)** confermato:
1. `required_adventurer_level` (canonical, always present)
2. `level_required` (fallback if canonical missing)
3. `min_level` (fallback if both above missing)
4. `1` (default fallback if all missing)

**Nessuna deprecazione** di `level_required` o `min_level` in EV-F2 (gate dedicato futuro).

**Tier mapping (G5 EQUIP_DESIGN)**:
- T1 Aspirante: L 1-15
- T2 Cacciatore: L 16-30
- T3 Iniziato: L 31-45
- T4 Rituale: L 46-55
- T5 Vuoto: L 56-60

**Max live level**: 12 → **tutti i 178 items live sono T1** (Aspirante). **T2-T5 = 0 items materializzati**.

**Correzione RV3-EV finding "1 item Int L12 in T5" preservata**: L12 = T1, **NON** T5. Nessuna reintroduzione del finding errato.

---

## 15 · Rarity values

**Distinct**: `Common · Uncommon · Rare · Epic · Legendary` (5 valori)

**Distribuzione live measured**:
| Rarity | Count | % |
|---|---|---|
| Common | 52 | 29.2% |
| Uncommon | 37 | 20.8% |
| Rare | 39 | 21.9% |
| Epic | 39 | 21.9% |
| Legendary | 11 | 6.2% |
| **Total** | 178 | 100% |

**Delta vs RV3-EV stima**:
- Epic: 39 live vs 14 RV3-EV stima → **+25 items** (approssimazione RV3-EV era grossolanamente sottostimata)
- Legendary: 11 live vs 3 RV3-EV stima → **+8 items**
- Common: 52 live vs 63 RV3-EV stima → -11
- Uncommon: 37 vs 49 → -12
- Rare: 39 vs 49 → -10

**Ratifica EV-F2**: la distribuzione RV3-EV per rarity era **approssimazione non misurata**. EV-F2 sostituisce con misurazione live authoritative.

---

## 16 · can_be_sold_for_real_money audit

**Field presence**:
| Status | Count | % |
|---|---|---|
| Present with value | 128 | 71.9% |
| Missing (unset) | 50 | 28.1% |

**Distinct values (per items presenti)**:
| Value | Count |
|---|---|
| `False` | 128 |
| `True` | **0** |
| Truthy / non-boolean ambiguous | **0** |

**Anti-P2W audit result**:
- **PASS documentale**: 0 items marketable (`can_be_sold_for_real_money = true`)
- ⚠️ **Data quality gap**: 50 items **missing** field (28.1%). Non è violation P2W (missing ≠ true), ma è gap di completezza schema.
- Nessuna correction/backfill autorizzata in EV-F2.

**Fallback anti-P2W enforcement**:
- Backend logic (sealed) applica default `can_be_sold_for_real_money = false` se missing/null.
- Documentato in EV-F2 come **data quality followup** (design_only, no apply).

**Verdict**: **ANTI-P2W COMPLIANT** su population presente + fallback logic. Data quality gap tracciata separatamente.

---

## 17 · Tier derivation preview

Formula (design_only, read-only preview, NO apply):

```
tier = f(required_adventurer_level)
  L 1-15  → T1 Aspirante
  L 16-30 → T2 Cacciatore
  L 31-45 → T3 Iniziato
  L 46-55 → T4 Rituale
  L 56-60 → T5 Vuoto
```

**Live preview (read-only enrichment simulation, apply_authorized=false)**:
- Tutti i 178 items → **T1 Aspirante** (max L12)
- T2/T3/T4/T5 → 0 items materializzati

**Verdict tier readiness** (EV-F1 §16 confermato): `DERIVABLE_HIGH_CONFIDENCE`
**Confidence**: HIGH (formula deterministica, boundary lock G5)
**Apply**: NOT AUTHORIZED (design_only)

---

## 18 · ILVL derivation preview

**Formula canonica LOCK** (PM directive EV-F2):
```
rarity_offset:
  Common    = +0
  Uncommon  = +2
  Rare      = +3
  Epic      = +4
  Legendary = +5

ilvl(item) = min( max( required_level + rarity_offset[rarity], tier_min[tier] ), 60 )

tier_min:
  T1 = 1
  T2 = 16
  T3 = 31
  T4 = 46
  T5 = 56
```

**Legendary ILVL LOCK**: `ilvl(Legendary) = 60` (endgame anchor).

**Live preview (read-only enrichment simulation)**:
- Common L1 → ilvl 1
- Uncommon L3 → ilvl 5
- Rare L5 → ilvl 8
- Epic L8 → ilvl 12
- Legendary L12 → ilvl 60 (anchor lock applicato)
- Common L12 → ilvl 12
- Common L1 → ilvl 1

**Verdict ilvl readiness** (EV-F1 §17 aggiornato): `DERIVABLE_HIGH_CONFIDENCE` (era `DERIVABLE_CONDITIONAL` in EV-F1; upgrade a HIGH post PM ratify formula)
**Confidence**: HIGH post lock
**Apply**: NOT AUTHORIZED (design_only)

**Nota**: formula EV-F2 differisce da EV-F1 proposal (Common=0/Unc=+1/Rare=+2/Epic=+3/Leg=+5). PM directive EV-F2 **sostituisce** con offset +0/+2/+3/+4/+5. EV-F1 proposal è deprecata a livello raccomandazione (nessun apply avvenuto in nessun caso).

---

## 19 · T1 actual coverage

**Live materialized**: **178 items** (100% catalog live è T1).

**Breakdown per item_type**:
| item_type | Count |
|---|---|
| weapon | 61 (54 weapon + 7 weapon_main) |
| armor | 48 (44 armor + 3 chest + 1 helm) |
| accessory | 47 (42 accessory + 5 amulet · non conteggia ring/1 nel amulet) |
| ring | 1 |
| consumable | ~10 |
| material / material_continental / material_event | ~10 |
| shield | ~2 |

**Vuoto-eligibile T1 (via warlock bridge + adjudication EV-F2)**:
- Validated REUSE_VALID: 12
- Conditional REUSE: 6 (weapon tome/arcane) + subset 49 REUSE_CONDITIONAL
- Total baseline T1 Vuoto usable: ~65-70 items

**Verdict T1 coverage**: **PARTIAL** (sufficient per T1 baseline, insufficient per full-slot canonical 14 coverage).

---

## 20 · T2 coverage gap

**Live materialized**: **0 items** (L16-30).

**Future item need (estimate G5 §Item Budget)**:
- Vuoto-specific T2: ~15-20 items (5-6 slot × 3 rarity + weapons/accessory)
- Cross-class shared T2: ~5-10 items
- Universal T2: ~2-5 items
- **Total T2 Vuoto need**: ~22-35 items

**Gap**: COMPLETE (0 → 22-35 items future).

---

## 21 · T3 coverage gap

**Live materialized**: **0 items** (L31-45).

**Future item need**:
- Vuoto-specific T3: ~15-20 items
- Cross-class shared T3: ~5-10 items
- Universal T3: ~2-5 items
- **Total T3 Vuoto need**: ~22-35 items

**Gap**: COMPLETE (0 → 22-35 items future).

---

## 22 · T4 coverage gap

**Live materialized**: **0 items** (L46-55).

**Future item need**:
- Vuoto-specific T4: ~15-20 items
- Cross-class shared T4: ~5-10 items
- Universal T4: ~2-5 items
- **Total T4 Vuoto need**: ~22-35 items

**Gap**: COMPLETE (0 → 22-35 items future).

---

## 23 · T5 coverage gap

**Live materialized**: **0 items** (L56-60).

**Correzione critica preservata**: L12 = T1, **NON** T5. Nessun item Int L12 è T5.

**Future item need (G5 T5 Vuoto endgame identity)**:
- Vuoto-specific T5: ~15-20 items (endgame Vuoto identity full gear)
- T5 Legendary Vuoto: ~5-10 items
- Universal T5: ~2-5 items
- **Total T5 Vuoto need**: ~22-35 items

**Gap**: COMPLETE (0 → 22-35 items future).

**Note**: `voidpiercer-bow` NOT count come T5 (è Epic L8 = T1).

---

## 24 · Head gap

**Slot canonical**: head (helm)

**Live coverage**: 1 item (`drake_slayer_helm`, Legendary L12) — ma **IDENTITY_CONFLICT** con Vuoto (strength/endurance, hard binding warrior/paladin/berserker)

**Vuoto-usable head**: **0 items**.

**Gap**: COMPLETE. Serve materializzazione head Vuoto-specific T1-T5 (~5-8 items).

---

## 25 · Back gap

**Slot canonical**: back (cape/cloak/mantle)

**Live coverage**: **0 items live con slot_type `back`** (slot canonico assente dal schema live).

**Sub-observation**: alcuni armor items (es. `warlock_coven_mantle` = "Mantello del Coven") sono **thematically back-slot** ma classificati `slot_type = armor` (schema aggregato).

**Gap**: COMPLETE. Serve slot canonico `back` + items back Vuoto T1-T5 (~4-6 items).

---

## 26 · Ring gap

**Slot canonical**: ring

**Live coverage**: 
- 1 item con `slot_type = ring` (`goblin_hunter_ring`, Legendary L12) — **IDENTITY_CONFLICT**
- 1 item warlock+intellect ring (`warlock_black_ring`, Rare L5) — **REUSE_VALID**

**Vuoto-usable ring**: **1 item** (warlock_black_ring T1)

**Gap per Vuoto full endgame**: ring T2-T5 = 0 → serve ~5-8 items ring Vuoto T2-T5.

---

## 27 · Armor gap

**Slot canonical armor group** (chest, shoulders, hands, waist, legs, feet):
- Live coverage armor Vuoto-usable: 5 items (warlock+intellect armor con cloth/robe/light/medium) tutti **T1**
- Live coverage armor by canonical slot: aggregato in `armor` (coarse)

**Gap**: 
- T1 armor Vuoto: 5 items — insufficient per full 6-slot armor set
- T2-T5 armor Vuoto: 0 → serve ~24-36 items future (6 slot × 4 tier × ~1-2 rarity avg)

---

## 28 · Weapon gap

**Slot canonical weapon** (main_hand + off_hand):
- Live coverage weapon Vuoto: 6 items warlock+intellect (tome/arcane) — **REUSE_CONDITIONAL** proficiency review
- Native `focus` weapon literal: ~0-1 items (sub-materialized)
- Native `crossbow/balestra` weapon: **0 items** — complete gap
- Native `dagger` Vuoto: 0 items warlock (i dagger live sono per rogue/assassin/ranger)

**Gap**:
- T1 weapon Vuoto (focus + balestra + dagger): parziale via tome semantic — ~6 CONDITIONAL
- T2-T5 weapon Vuoto: 0 → serve ~15-24 items future (3 famiglie × 4 tier × 1-2 rarity)

---

## 29 · Accessory gap

**Slot canonical accessory** (neck + ring + amulet + trinket):
- Live coverage accessory Vuoto-usable: 7 items warlock+intellect accessory tutti T1 — **REUSE_VALID**
- Live accessory total: 42 + 5 amulet + 1 ring = 48
- Universal slot coverage: OK per T1

**Gap**:
- T1 accessory Vuoto: 7 — sufficient
- T2-T5 accessory Vuoto: 0 → serve ~15-20 items future

---

## 30 · Class identity risk

**Risk register class identity per Vuoto**:

| Risk | Severity | Mitigation |
|---|---|---|
| Overlap con Mago (mage class_tag 29 items nei 49) | MEDIUM | Rec_classes bridge selectivo; Vuoto-specific lore su nuovi items |
| Overlap con Necromante (necromancer 29 items) | MEDIUM | Distinct lore identity (necromancer = death; Vuoto = void/oblivion — sovrapposizione parziale) |
| Overlap con Bardo (bard 26 items) | LOW | Bardo è caster-support, Vuoto è caster-DPS; identity separata |
| Overlap con Cacciatore di Mostri (rec_classes cross-class su 2 lore items) | LOW-MEDIUM | Class rivale con proprio identity path; escludere rigorosamente da Vuoto (no retro-branding) |
| Retro-branding "voidpiercer" | HIGH (mitigato) | REJECTED_NOT_COMPATIBLE finale su voidpiercer-bow |
| Legacy warlock bridge (R18.3e) | LOW | Bridge accettato via R18.3e sealed; class_tags:warlock è mapping stabile a cacciatore_del_vuoto |

**Verdict identity risk complessivo**: **MEDIUM** (mitigabile con Registry v3 additive design_only + AFX1 vocabulary lock).

---

## 31 · Overlap Mago

**Population 49 con `class_tags: mage`**: **29 items**.

**Sottogruppo Mago-esclusivo** (solo mage in class_tags, no altri caster): ~5-8 items.
**Sottogruppo Mago-multi** (mage + necromancer + bard): ~20 items (caster generici).

**Analisi identity Vuoto vs Mago**:
- Mago = arcane classic caster · Vuoto = void/oblivion caster
- Overlap tematico: entrambi Intelligence-based casters
- Overlap distinct: Mago è "high magic" · Vuoto è "forbidden magic" / "void magic"

**Adjudication overlap Mago**:
- Items Mago-only con lore neutral (mundane/frontiera): REUSE_CONDITIONAL (bridge additive Registry v3)
- Items Mago-only con lore veglie/memoria/filo-spezzato (Vuoto-adjacent): REUSE_CONDITIONAL (identity partial overlap)
- Items Mago-only con lore vuoto/oblio (arcane_adept_orb): REMAINS_PM_REVIEW

---

## 32 · Overlap Rogue

**Population 49 con `class_tags: rogue`**: **4 items** (limited).

**Analysis**:
- Rogue = agility-based melee stealth
- Vuoto = intellect-based caster
- Overlap identity: **LOW** (stat mismatch, role mismatch)
- I 4 items rogue+intellect (soft binding) sono dual-stat multi-class → **REUSE_CONDITIONAL** solo per intellect scaling parziale
- Verdict overlap Rogue: LOW risk, minimal reuse potential

---

## 33 · Overlap Cacciatore di Mostri

**Cacciatore di Mostri** (canonical class_slug, presumibilmente Wave 1 successor).

**Population live con `cacciatore_di_mostri` in recommended_classes**: 
- 2 items lore vuoto/oblio (`voidpiercer-bow`, `goblin_hunter_ring`) — **entrambi IDENTITY_CONFLICT per Vuoto** e già assegnati a Cacciatore di Mostri path

**Analysis**:
- Cacciatore di Mostri e Cacciatore del Vuoto sono **class rivali** (naming convergence, identity distinct)
- Vuoto = intellect caster · Cacciatore di Mostri = agility/strength melee-ranged (presumibile)
- **NO shared items** — separation obbligatoria per identity clarity

**Verdict overlap**: **STRICT SEPARATION** required. Nessun item con `rec_classes: cacciatore_di_mostri` promuovibile a Vuoto.

---

## 34 · Reuse final totals

**Adjudication finale EV-F2 (post PM micro-fix)** — ledger canonico live universe 178:

| Verdict | Count | Population source |
|---|---|---|
| **REUSE_VALID** | **12** | 18 warlock+intellect: 5 armor + 7 accessory (nessuna mutation) |
| **REUSE_CONDITIONAL** | **32** | 2 dei 47 (weapon focus/dagger literal G2) + 11 dei 47 (armor stoffa/cuoio) + 19 dei 47 (accessory universal) — tutti via Registry v3 additive `rec_classes: cacciatore_del_vuoto` (non-mutation atomica) |
| **NOT_COMPATIBLE** | **134** | 6 weapon warlock tome/arcane (famiglia_esclusa_da_G2) + 5 lore identity_conflict + 1 arcane_adept_orb PRESERVED + 15 dei 47 declassati per famiglia_esclusa_da_G2 + 107 out-of-scope |
| **PM_REVIEW** | **0** | (arcane_adept_orb migrato a NOT_COMPATIBLE; nessun residuo) |
| **TOTAL LIVE LEDGER** | **178** | ✅ Categorie mutuamente esclusive ed esaustive |

**REQUIRES_NEW_ITEM_FUTURE**: **SEPARATO dal ledger 178** (design coverage gap T2-T5 + arcane_adept_orb_void_native_successor) — vedi §45 FUTURE COVERAGE GAP.

---

## 35 · Conditional totals

**REUSE_CONDITIONAL breakdown (post PM strict G2 review)** — Total: **32 items**:

| Sub-group | Count | Condition | Non-mutation guarantee |
|---|---|---|---|
| Weapon literal G2 (focus/dagger) | 2 | `weapon_family_literal_G2_via_rec_classes_additive` | Additive `rec_classes: cacciatore_del_vuoto` (array append atomic, no rewrite) |
| Armor stoffa/cuoio proficient | 11 | `armor_proficiency_stoffa_cuoio_via_rec_classes_additive` | Additive `rec_classes` |
| Accessory universal slot | 19 | `universal_accessory_slot_via_rec_classes_additive` | Additive `rec_classes` |
| **Total REUSE_CONDITIONAL** | **32** | Tutti richiedono Registry v3 additive apply futuro | Nessuna mutation su class_tags/stat/slot/proficiency |

**Note strict G2**: la PM directive strict richiede weapon family literal ∈ {focus, balestra, pugnale}. Semantic caster overlap (tome/grimoire/wand/staff) **NON** giustifica REUSE_CONDITIONAL → tutti gli item con weapon_tags `tome/grimoire/wand/staff/instrument/sonic/alchemical_flask/bow/etc` declassati a NOT_COMPATIBLE (famiglia_esclusa_da_G2).

**Condition unlock prerequisite**: Registry v3 additive apply (rec_classes atomic append) + AFX1 Affix Vocabulary lock (entrambi HOLD, apply NOT authorized ora).

---

## 36 · Rejected totals

**NOT_COMPATIBLE breakdown (post PM micro-fix)** — Total: **134 items**:

### 36.1 — 6 weapon warlock tome/arcane (strict G2 review)

| slug | weapon_family | rarity | lvl | Verdict | Condition |
|---|---|---|---|---|---|
| warlock_apprentice_tome | tome | Common | 1 | NOT_COMPATIBLE | famiglia_esclusa_da_G2 |
| warlock_hex_grimoire | tome | Uncommon | 3 | NOT_COMPATIBLE | famiglia_esclusa_da_G2 |
| warlock_shadowbound_grimoire | tome | Rare | 5 | NOT_COMPATIBLE | famiglia_esclusa_da_G2 |
| warlock_witchking_codex | tome | Epic | 8 | NOT_COMPATIBLE | famiglia_esclusa_da_G2 |
| warlock_apprentice_grimoire | tome | Uncommon | 3 | NOT_COMPATIBLE | famiglia_esclusa_da_G2 |
| warlock_pact_binder | tome | Rare | 5 | NOT_COMPATIBLE | famiglia_esclusa_da_G2 |

**PM directive strict**: weapon family `tome` è univocamente determinata, `tome ∉ {focus, balestra, pugnale}` → NOT_COMPATIBLE (primary verdict). `arcane` è modifier, non famiglia. G2 non ampliata.

### 36.2 — 5 lore items IDENTITY_CONFLICT

| slug | Primary verdict | Secondary attributes | Reason |
|---|---|---|---|
| drake_slayer_helm | NOT_COMPATIBLE | identity_conflict=true, mutation_required=true | strength/endurance + hard binding warrior/paladin/berserker |
| drake_slayer_chest | NOT_COMPATIBLE | identity_conflict=true, mutation_required=true | strength/endurance + hard binding |
| drake_slayer_blade | NOT_COMPATIBLE | identity_conflict=true, mutation_required=true | strength/agility + hard + sword proficiency |
| goblin_hunter_ring | NOT_COMPATIBLE | identity_conflict=true, mutation_required=true | strength/agility + rec_classes cacciatore_di_mostri |
| voidpiercer-bow | NOT_COMPATIBLE | identity_conflict=true, mutation_required=true, retro_branding_forbidden=true | bow ≠ focus/crossbow/dagger + cacciatore_di_mostri rec + retro-branding VIETATO |

### 36.3 — 1 arcane_adept_orb PRESERVED

| slug | Primary verdict | Secondary attributes | Reason |
|---|---|---|---|
| arcane_adept_orb | NOT_COMPATIBLE | lore_reviewed=true, identity_conflict=false, mutation_required=true, triggers_future_void_native_item=true | Item preserved (no mutation); trigger successor void-native item in FUTURE COVERAGE GAP |

### 36.4 — 15 dei 47 declassati per famiglia_esclusa_da_G2 (strict weapon review)

| slug | weapon_family | Condition |
|---|---|---|
| cracked-staff | staff | famiglia_esclusa_da_G2 |
| spiritglass-staff | staff | famiglia_esclusa_da_G2 |
| embermind-focus | wand | famiglia_esclusa_da_G2 |
| apprentice-wand | wand | famiglia_esclusa_da_G2 |
| hex-rod | staff | famiglia_esclusa_da_G2 |
| moonsilver-bow | bow | famiglia_esclusa_da_G2 |
| warlocks-grimoire | grimoire | famiglia_esclusa_da_G2 |
| archmagi-staff | staff | famiglia_esclusa_da_G2 |
| songsteel-flute | instrument/sonic | famiglia_esclusa_da_G2 |
| apprentice_staff | staff | famiglia_esclusa_da_G2 |
| legendary_staff_efreto | staff | famiglia_esclusa_da_G2 |
| alchemist_apprentice_flask | alchemical_flask | famiglia_esclusa_da_G2 |
| alchemist_elemental_flask | alchemical_flask | famiglia_esclusa_da_G2 |
| alchemist_transmuters_tome | tome | famiglia_esclusa_da_G2 |
| alchemist_philosophers_flask | alchemical_flask | famiglia_esclusa_da_G2 |

### 36.5 — 107 out-of-scope items (secondary attribute `out_of_scope=true`)

| Sub-reason | Count |
|---|---|
| stat_mismatch_non_intellect (strength/agility/faith/endurance) | 81 |
| stat_missing (materials/consumables/misc) | 21 |
| hard_binding_non_warlock | 5 |
| **Total out-of-scope** | **107** |

Tutti classificati **NOT_COMPATIBLE (primary)** con secondary `out_of_scope=true`. Non double-count nel ledger.

**Grand total NOT_COMPATIBLE**: 6 + 5 + 1 + 15 + 107 = **134** ✅

---

## 37 · Unresolved totals

**REMAINS_PM_REVIEW (post PM micro-fix)**: **0 items** ✅

Il precedente residuo (arcane_adept_orb) è stato adjudicato dalla PM directive (Opzione A):
- Primary verdict: **NOT_COMPATIBLE** (preserved, no mutation)
- Secondary: `lore_reviewed=true`, `mutation_required=true`, `triggers_future_void_native_item=true`
- FUTURE COVERAGE GAP entry: `arcane_adept_orb_void_native_successor`

Nessun altro item residuo ambiguo nel ledger live 178.

---

## 38 · Future item estimate normalized

**Stima 180-220 (EV-F1 §36)** — normalizzazione EV-F2:

**Interpretation (D + E ibrido)**:
- **A** (nuovi item unici): parzialmente vero, ma includerebbe anche shared/universal items
- **B** (tier × slot × rarity coverage): rilevante per T2-T5 gap
- **C** (materializzazione completa T1-T5): sì, questa è la componente principale
- **D** (class-specific + shared + universal): sì, la stima include tutte 3 le tipologie
- **E** (scenario massimo): sì, 180-220 è **scenario massimo full Vuoto identity**

**Decomposizione EV-F2**:
| Component | Count estimate |
|---|---|
| Vuoto-specific T1 completion | 15-25 (headroom + slot completeness) |
| Vuoto-specific T2 | 22-35 |
| Vuoto-specific T3 | 22-35 |
| Vuoto-specific T4 | 22-35 |
| Vuoto-specific T5 endgame | 22-35 |
| Shared caster items | 15-25 |
| Universal slot back/shoulders (new canonical) | 15-25 |
| Legendary Vuoto identity | 5-15 |
| **Total scenario massimo** | **~138-230** (envelope 180-220 confermato) |

**Status**:
- **NON-BINDING**
- **NOT PM-APPROVED**
- **NOT ITEM-CREATION AUTHORIZATION**
- Stima design-only per orientamento planning

---

## 39 · Coverage envelope reconciliation

**Coverage envelope pianificato Vuoto** (da R18.6.RV3):
- **Envelope**: 110-130 items
- **Planning center**: ~120 items

**Relazione envelope vs future estimate 180-220**:

| Metric | Value | Interpretation |
|---|---|---|
| Coverage envelope | 110-130 | Baseline planning: identity full + slot completeness base (single-rarity coverage per slot per tier) |
| Planning center | 120 | Median target |
| Future item estimate | 180-220 | **Scenario massimo** con multi-rarity + shared + universal + Legendary identity items |
| Delta envelope → estimate | +50-100 items | Rappresenta l'expansion multi-rarity + universal slots (back, shoulders) + Legendary depth |

**Reconciliation**:
- **Envelope 120** = baseline "playable Vuoto" (1 item per slot per tier per Common/Rare rarity)
- **Estimate 180-220** = scenario "full Vuoto identity" (multi-rarity per slot per tier + Legendary depth + shared caster items)
- **Envelope resta LOCK design baseline**; l'estimate è expanded scenario NON-binding.

**Verdict**: envelope 110-130 (center 120) preservato come **planning baseline**; estimate 180-220 è **max scenario advisory**.

---

## 40 · Affix Vocabulary Gate prerequisites (R18.6.RV3-AFX1)

**AFX1 = Affix Vocabulary & Pool Contract** (HOLD, not started).

**Prerequisites documentati per AFX1** (design_only):
1. **Affix pool tag vocabulary base**: definire set T1-T5 (arcane/void/oblivion/veglie affixes)
2. **Schema validation rules**: min/max affix count per rarity, stacking rules, exclusion rules
3. **Compatibility mapping**: per class · per tier · per rarity · per slot
4. **Null handling policy**: item pre-affix rimane null · non forzare backfill · versioning field opzionale
5. **AFX applicability audit su 178 items**: verifica quali items sono retrofittabili con affix pool tag (backfill futuro)
6. **Vocabulary lock**: PM ratify vocabulary base prima di backfill/apply
7. **Registry v3 additive design_only**: nessuna field addition, solo alias-first

**AFX1 status EV-F2**:
- **DO NOT START**
- **DO NOT CREATE artifacts AFX1**
- **DO NOT APPEND PRD**
- **HOLD** fino a PM directive dedicata post-EV-F2 approval

---

## 41 · Risk register

| ID | Risk | Severity | Mitigation | Status |
|---|---|---|---|---|
| F2-R1 | Rarity distribution RV3-EV stimata errata (Epic/Legendary sottostima) | HIGH → mitigated | EV-F2 misura live authoritative | RESOLVED |
| F2-R2 | Retro-branding "voidpiercer" temptation | HIGH | Regola PM strict: no name-based reuse | MITIGATED (voidpiercer-bow REJECTED) |
| F2-R3 | Identity_conflict mage/necromancer overlap con Vuoto | MEDIUM | Registry v3 additive selectivo + AFX1 lock | HOLD |
| F2-R4 | Cross-class Cacciatore di Mostri contamination | MEDIUM | Strict separation rec_classes | MITIGATED (documentato) |
| F2-R5 | Coverage T2-T5 zero live | HIGH (design) | Future materialization gate (post AFX1) | HOLD |
| F2-R6 | armor_tags coverage parziale (46/178) | LOW | Alias-first accettato con caveat | ACCEPTED |
| F2-R7 | 50 items missing `can_be_sold_for_real_money` | LOW-MEDIUM | Backend default false; data quality followup | ACCEPTED |
| F2-R8 | 21 items `slot_type = None` | LOW | Data quality followup (design_only) | ACCEPTED |
| F2-R9 | Slot taxonomy live coarse vs canonical 14 | MEDIUM | Design_only remapping in gate futuro | HOLD |
| F2-R10 | `focus` weapon literal sub-materialized (0-1 items) | HIGH (design) | Future weapon materialization Vuoto-specific | HOLD |
| F2-R11 | ILVL formula pre-EV-F1 vs EV-F2 divergence | LOW → mitigated | EV-F2 formula lock sostituisce EV-F1 proposal | RESOLVED |
| F2-R12 | Class_slug bridge R18.3e legacy (warlock → cacciatore_del_vuoto) | LOW | R18.3e sealed, bridge stabile | ACCEPTED |

---

## 42 · PM open questions F2-Q1..F2-Q12

- **F2-Q1** — I 6 REUSE_CONDITIONAL weapon warlock (tome/arcane) sono promuovibili a REUSE_VALID se G2 profile Vuoto include `tome` come semantic proficiency? *Recommendation*: HOLD fino a AFX1 vocabulary lock — decidere in gate dedicato se weapon proficiency Vuoto è literal (`focus + crossbow + dagger`) OR semantic (include `tome/grimoire/wand`).
- **F2-Q2** — I 47 REUSE_CONDITIONAL dei 49 PM_REVIEW richiedono Registry v3 additive `recommended_classes` bulk. Autorizzare in gate dedicato o item-by-item? *Recommendation*: bulk in gate dedicato post AFX1, con exclusion list per items lore-conflicting.
- **F2-Q3** — arcane_adept_orb REMAINS_PM_REVIEW: creare nuovo item Legendary Vuoto-specific similare O autorizzare additive `class_tags` in gate dedicato? *Recommendation*: creare nuovo item Vuoto-specific (evita mutation su item Legendary esistente).
- **F2-Q4** — Rarity distribution RV3-EV corrected: aggiornare RV3-EV.json con misurazioni live? *Recommendation*: NO — RV3-EV.json è IMMUTABLE post approval; correzione tracciata in EV-F1 + EV-F2 come corrective/additive audit.
- **F2-Q5** — ILVL formula EV-F2 (+0/+2/+3/+4/+5) sostituisce EV-F1 proposal: verdict finale? *Recommendation*: EV-F2 formula è ratificata; EV-F1 proposal deprecata a livello suggestion (nessun apply avvenuto).
- **F2-Q6** — Slot taxonomy live coarse (weapon/armor/accessory) vs canonical 14: quando remapping? *Recommendation*: gate dedicato post AFX1 (slot canonical remapping = mutation schema, richiede Registry v3 additive field `slot_canonical` alias).
- **F2-Q7** — Anti-P2W: 50 items missing `can_be_sold_for_real_money` — data quality followup ora o defer? *Recommendation*: defer a gate dedicato data quality (post-EV chain).
- **F2-Q8** — 21 items `slot_type = None`: data quality gap. Backfill o keep as-is? *Recommendation*: keep as-is (no backfill); documentare per audit futuro.
- **F2-Q9** — `focus` weapon literal sub-materialized (0-1 items): T1 Vuoto weapon proficiency ha gap literal? *Recommendation*: **YES**, T1 Vuoto weapon proficiency `focus` è gap → serve materializzazione focus items T1 in Registry v3 (gate futuro).
- **F2-Q10** — Coverage envelope 110-130 (planning center 120) vs future estimate 180-220: quale è "official planning target"? *Recommendation*: envelope 110-130 è **official baseline**; estimate 180-220 è **advisory max scenario** NON-binding.
- **F2-Q11** — Cacciatore di Mostri strict separation: preservare "no shared items"? *Recommendation*: YES, strict separation confermata.
- **F2-Q12** — AFX1 kickoff timing: post-EV chain closure O in parallel? *Recommendation*: post-EV chain (EV → EV-F1 → EV-F2 → EV closure) prima di AFX1 kickoff.

---

## 43 · GO/HOLD recommendation RV3-EV

| Componente | Verdict |
|---|---|
| RV3-EV closure | 🔒 **HOLD** (attende PM review EV-F2) |
| EV-F1 | ✅ PM APPROVED (corrective/additive audit) |
| EV-F2 draft | ✅ **DRAFT_GENERATED** (this document) |
| EV-F2 PM review | 🕐 **PENDING** |
| Registry v3 additive metadata gate | 🔒 HOLD (post-EV closure) |
| Registry v3 apply | 🔒 **NOT AUTHORIZED** |
| Field addition (nuovi campi) | 🔒 **NOT AUTHORIZED** |
| Field deprecation (slot/level) | 🔒 HOLD |
| Affix pool tag backfill | 🔒 HOLD (AFX1 vocabulary lock prerequisito) |
| Item creation Registry v3 (~180-220) | 🔒 **NOT AUTHORIZED** |
| PM_REVIEW 49 items adjudication | ✅ **COMPLETED** in this document |
| PM_REVIEW residuo | 1 (arcane_adept_orb) |
| 6 lore Vuoto/Oblio final adjudication | ✅ **COMPLETED** (0 REUSE · 5 IDENTITY_CONFLICT · 1 PM_REVIEW) |
| voidpiercer-bow | 🔒 **REJECTED_NOT_COMPATIBLE** finale (no retro-branding) |
| arcane_adept_orb | 🕐 **REMAINS_PM_REVIEW** (defer future gate) |
| AFX1 kickoff | 🔒 **HOLD** (DO NOT START) |
| Gate 11 | 🔒 **NOT AUTHORIZED** |
| Wave 1 kickoff (Monaco/Druido/Alchimista/Bardo/Negromante) | 🔒 **HOLD** |
| Cacciatore del Vuoto: LIVE / SELECTABLE | 🔒 **NOT LIVE · NOT SELECTABLE** |

**Recommendation al PM**:
Acquisire EV-F2 come **adjudication finale + coverage reconciliation**. Riconoscere:
- 12 REUSE_VALID (baseline warlock+intellect via legacy bridge R18.3e, no mutation)
- 53 REUSE_CONDITIONAL (con dependency AFX1 + Registry v3 additive)
- 5 IDENTITY_CONFLICT + 1 PM_REVIEW residuo (arcane_adept_orb)
- Rarity distribution RV3-EV corrected (live measurement authoritative)
- ILVL formula finale locked (+0/+2/+3/+4/+5, Legendary = 60 anchor)
- Coverage envelope 110-130 (center 120) planning baseline · 180-220 max scenario advisory
- T2-T5 gap complete (0 items) — future materialization gate post AFX1
- Anti-P2W: PASS documentale con data quality caveat (50 missing)

**Prerequisiti pre-closure RV3-EV**:
- PM approval EV-F2 adjudication
- Nessun altro gate F3+ pianificato (adjudication considered complete)
- Ratifica ILVL formula finale
- Ratifica envelope 110-130 baseline

---

## 🛑 STOP FINALE · EV-F2 DRAFT GENERATO · PENDING PM

---

## 44 · Live Item Adjudication Ledger (post PM accounting micro-fix)

```
╔══════════════════════════════════════════════════════════════════╗
║       LIVE ITEM ADJUDICATION LEDGER (universe = 178 items)       ║
╠══════════════════════════════════════════════════════════════════╣
║   REUSE_VALID          =  12  (7 accessory + 5 armor)            ║
║   REUSE_CONDITIONAL    =  32  (2 weapon G2 + 11 armor + 19 acc) ║
║   NOT_COMPATIBLE       = 134  (6+5+1+15+107 disjoint)            ║
║   PM_REVIEW            =   0                                     ║
║   TOTAL                = 178  ✅ CANONICAL DISJOINT EXHAUSTIVE   ║
╚══════════════════════════════════════════════════════════════════╝
```

**Regole rispettate**:
- Ogni record ha **UN SOLO primary verdict** ∈ {REUSE_VALID, REUSE_CONDITIONAL, NOT_COMPATIBLE, PM_REVIEW}
- Categorie **mutuamente esclusive ed esaustive** su universe 178
- Attributi secondari (non double-count): `out_of_scope`, `lore_reviewed`, `identity_conflict`, `mutation_required`, `triggers_future_void_native_item`, `retro_branding_forbidden`
- `REQUIRES_NEW_ITEM_FUTURE` è **separato** dal ledger 178 (vedi §45)
- Nessuna approssimazione "~110" — conteggio esatto item-by-item
- Nessuna mutation su record R18.5/live

**Composition NOT_COMPATIBLE (134)**:
| Component | Count | Secondary flag |
|---|---|---|
| 6 weapon warlock tome/arcane (famiglia_esclusa_da_G2) | 6 | mutation_required=true |
| 5 lore items IDENTITY_CONFLICT | 5 | identity_conflict=true, mutation_required=true |
| 1 arcane_adept_orb PRESERVED (Opzione A) | 1 | lore_reviewed=true, mutation_required=true, triggers_future_void_native_item=true |
| 15 dei 47 declassati (famiglia_esclusa_da_G2) | 15 | mutation_required=true |
| 107 out-of-scope items | 107 | out_of_scope=true |
| **Total** | **134** | |

**Composition REUSE_CONDITIONAL (32)**:
| Component | Count | Condition |
|---|---|---|
| Weapon literal G2 (focus/dagger) | 2 | weapon_family_literal_G2_via_rec_classes_additive |
| Armor stoffa/cuoio | 11 | armor_proficiency_stoffa_cuoio_via_rec_classes_additive |
| Accessory universal | 19 | universal_accessory_slot_via_rec_classes_additive |
| **Total** | **32** | Registry v3 additive `rec_classes` (atomic array append, non-mutation) |

---

## 45 · Future Coverage Gap (separato dal ledger 178)

**Status**: NON conta nei 178 live · progettuale · design-only

```
REQUIRES_NEW_ITEM_FUTURE (design coverage gap, NOT PM-approved, NOT authorized)
├── T2 Cacciatore (L16-30) Vuoto items                    ~22-35
├── T3 Iniziato (L31-45) Vuoto items                      ~22-35
├── T4 Rituale (L46-55) Vuoto items                       ~22-35
├── T5 Vuoto (L56-60) endgame items                       ~22-35
├── arcane_adept_orb_void_native_successor (new item)      1  (nuovo item_id, proficiency focus/balestra/pugnale, stat Intelligenza, weapon family valida - NO copia nome)
├── Slot canonical materialization (back/shoulders/hands/wrist/waist/legs/feet) T1-T5   ~20-30
├── focus literal weapon materialization (T1-T5)           ~8-12
├── crossbow/balestra weapon materialization (T1-T5)       ~8-12
├── Legendary Vuoto identity items                         ~5-15
├── Shared caster items                                    ~15-25
└── Universal slot expansion                               ~15-25
```

**Envelope PM baseline**: **110-130 items** (planning center ~120) — LOCK design baseline
**Advisory max scenario**: **180-220 items** — NON-BINDING · NOT PM-APPROVED · NOT ITEM-CREATION AUTHORIZATION

**Governance FUTURE COVERAGE GAP**:
- `item_creation_authorized = false`
- `registry_v3_apply_authorized = false`
- `field_addition_authorized = false`
- `no_backfill`
- `no_apply`
- `no_copy_of_existing_names`
- Nessuna materializzazione ora; gate dedicato futuro post-AFX1

---

## 46 · F2-Q1 → F2-Q12 · Verbatim Extraction

Estrazione testuale delle 12 domande PM open questions dal MD §42 e JSON `pm_open_questions_f2`. Format: testo verbatim + recommendation e1_dev + sezione origine + impatto + default proposto.

```
=== F2-Q1 ===
Testo: I 6 REUSE_CONDITIONAL weapon warlock (tome/arcane) sono promuovibili a REUSE_VALID se G2 profile Vuoto include `tome` come semantic proficiency?
Recommendation e1_dev: HOLD fino a AFX1 vocabulary lock — decidere in gate dedicato se weapon proficiency Vuoto è literal (`focus + crossbow + dagger`) OR semantic (include `tome/grimoire/wand`).
Sezione di origine: §42 · PM open questions F2-Q1..F2-Q12 (derivata da §4 REUSE_VALID 18 review e §12 weapon_tags distinct)
Impatto: AFX1 + REUSE_CONDITIONAL classification
Default proposto: literal G2 (post PM micro-fix strict interpretation applicata): 6 warlock weapon tome/arcane → NOT_COMPATIBLE (famiglia_esclusa_da_G2). Domanda resta aperta per validazione formale AFX1.

=== F2-Q2 ===
Testo: I 47 REUSE_CONDITIONAL dei 49 PM_REVIEW richiedono Registry v3 additive `recommended_classes` bulk. Autorizzare in gate dedicato o item-by-item?
Recommendation e1_dev: bulk in gate dedicato post AFX1, con exclusion list per items lore-conflicting.
Sezione di origine: §42 · PM open questions (derivata da §6 PM_REVIEW 49 inventory)
Impatto: registry v3 apply gate futuro
Default proposto: bulk apply in gate dedicato post-AFX1 con exclusion list (drake_slayer trilogy + goblin_hunter_ring + voidpiercer-bow + arcane_adept_orb esclusi).

=== F2-Q3 ===
Testo: arcane_adept_orb REMAINS_PM_REVIEW: creare nuovo item Legendary Vuoto-specific similare O autorizzare additive `class_tags` in gate dedicato?
Recommendation e1_dev: creare nuovo item Vuoto-specific (evita mutation su item Legendary esistente).
Sezione di origine: §42 · PM open questions (derivata da §8 arcane_adept_orb review)
Impatto: item creation futuro
Default proposto: creare nuovo item `arcane_adept_orb_void_native_successor` in FUTURE COVERAGE GAP (PM ha già scelto Opzione A: item preserved + nuovo successor futuro).

=== F2-Q4 ===
Testo: Rarity distribution RV3-EV corrected: aggiornare RV3-EV.json con misurazioni live?
Recommendation e1_dev: NO — RV3-EV.json è IMMUTABLE post approval; correzione tracciata in EV-F1 + EV-F2 come corrective/additive audit.
Sezione di origine: §42 · PM open questions (derivata da §3 EV baseline reconciliation e §15 Rarity values)
Impatto: cosmetico / traceability
Default proposto: NO update RV3-EV.json (immutable); correzione preservata in EV-F1/EV-F2 come corrective/additive audit.

=== F2-Q5 ===
Testo: ILVL formula EV-F2 (+0/+2/+3/+4/+5) sostituisce EV-F1 proposal: verdict finale?
Recommendation e1_dev: EV-F2 formula è ratificata; EV-F1 proposal deprecata a livello suggestion (nessun apply avvenuto).
Sezione di origine: §42 · PM open questions (derivata da §18 ILVL derivation preview)
Impatto: registry apply (ILVL calculation runtime futuro)
Default proposto: PM ha CONFIRMATO EV-F2 formula (+0/+2/+3/+4/+5, Legendary=60 anchor). Nessuna riapertura C3.

=== F2-Q6 ===
Testo: Slot taxonomy live coarse (weapon/armor/accessory) vs canonical 14: quando remapping?
Recommendation e1_dev: gate dedicato post AFX1 (slot canonical remapping = mutation schema, richiede Registry v3 additive field `slot_canonical` alias).
Sezione di origine: §42 · PM open questions (derivata da §13 slot_type distinct)
Impatto: registry v3 additive slot alias
Default proposto: PM ha CONFIRMATO 14 slot canonici + alias standard (belt→waist, cloak/cape→back, trinket→accessory, weapon_main→main_hand, weapon_off→off_hand, main-hand→main_hand, off-hand→off_hand, amulet→neck). NO ring1/ring2. NO trinket come 15° slot. Nessun remapping DB ora. Gate dedicato futuro per alias documentation.

=== F2-Q7 ===
Testo: Anti-P2W: 50 items missing `can_be_sold_for_real_money` — data quality followup ora o defer?
Recommendation e1_dev: defer a gate dedicato data quality (post-EV chain).
Sezione di origine: §42 · PM open questions (derivata da §16 can_be_sold_for_real_money audit)
Impatto: data quality gate futuro
Default proposto: DEFER a data quality gate; PM ha CONFIRMATO fallback missing→false comportamento codice/config effettivo (verifica read-only, senza materializzare). I 50 missing restano DATA QUALITY GAP tracciato.

=== F2-Q8 ===
Testo: 21 items `slot_type = None`: data quality gap. Backfill o keep as-is?
Recommendation e1_dev: keep as-is (no backfill); documentare per audit futuro.
Sezione di origine: §42 · PM open questions (derivata da §13 slot_type distinct)
Impatto: data quality
Default proposto: keep as-is · documentare · nessuna correzione ora.

=== F2-Q9 ===
Testo: `focus` weapon literal sub-materialized (0-1 items): T1 Vuoto weapon proficiency ha gap literal?
Recommendation e1_dev: **YES**, T1 Vuoto weapon proficiency `focus` è gap → serve materializzazione focus items T1 in Registry v3 (gate futuro).
Sezione di origine: §42 · PM open questions (derivata da §12 weapon_tags distinct + §28 weapon gap)
Impatto: FUTURE COVERAGE GAP (item creation futuro post-AFX1)
Default proposto: YES gap literal · materializzazione focus/balestra/pugnale in gate futuro dedicato · tracciato in FUTURE COVERAGE GAP (§45).

=== F2-Q10 ===
Testo: Coverage envelope 110-130 (planning center 120) vs future estimate 180-220: quale è "official planning target"?
Recommendation e1_dev: envelope 110-130 è **official baseline**; estimate 180-220 è **advisory max scenario** NON-binding.
Sezione di origine: §42 · PM open questions (derivata da §38 future item estimate + §39 coverage envelope reconciliation)
Impatto: planning target lock
Default proposto: PM ha CONFIRMATO — envelope 110-130 (center ~120) = baseline PM · estimate 180-220 = ADVISORY MAX SCENARIO NOT LOCKED NOT TARGET PM.

=== F2-Q11 ===
Testo: Cacciatore di Mostri strict separation: preservare "no shared items"?
Recommendation e1_dev: YES, strict separation confermata.
Sezione di origine: §42 · PM open questions (derivata da §33 overlap Cacciatore di Mostri)
Impatto: class identity governance
Default proposto: YES strict separation preservata · nessun item shared tra Vuoto e Cacciatore di Mostri.

=== F2-Q12 ===
Testo: AFX1 kickoff timing: post-EV chain closure O in parallel?
Recommendation e1_dev: post-EV chain (EV → EV-F1 → EV-F2 → EV closure) prima di AFX1 kickoff.
Sezione di origine: §42 · PM open questions (derivata da §40 Affix Vocabulary Gate prerequisites)
Impatto: AFX1 gate timing
Default proposto: post-EV chain closure · AFX1 HOLD fino a RV3-EV chiuso.
```

**Blocco F2-Q verbatim COMPLETATO · 12/12 domande estratte**.

---

## 47 · PM Directive micro-fix acknowledgment

**PM verdict registrato**:
- EV-F2 = **APPROVED WITH MANDATORY ACCOUNTING MICRO-FIX** — applicato in questa revisione
- Technical findings = ACCEPTED
- Candidate adjudication = ACCEPTED
- RV3-EV = STILL OPEN (attende verdict F2-Q1..F2-Q12)
- AFX1 = HOLD

**Conferme PM registrate (nessuna azione richiesta)**:
- ILVL formula CONFERMATA: Common+0 · Uncommon+2 · Rare+3 · Epic+4 · Legendary+5 · Legendary ILVL=60. Nessuna riapertura C3.
- Slot taxonomy CONFERMATA: 14 slot canonici + alias standard (belt→waist, cloak/cape→back, trinket→accessory, weapon_main→main_hand, weapon_off→off_hand, main-hand→main_hand, off-hand→off_hand, amulet→neck). NO ring1/ring2. NO trinket come 15° slot. Nessun remapping DB ora.
- Anti-P2W finding ACCEPTED con nota: verificare read-only se il fallback missing→false è comportamento codice/config effettivo (senza materializzare); i 50 missing restano DATA QUALITY GAP.
- T1-T5 progression materialization = INCOMPLETE (confermato). Cacciatore del Vuoto resta ACTIVE-DESIGN-READY (non live).
- Stima 180-220 = ADVISORY MAX SCENARIO NOT LOCKED NOT TARGET PM. Envelope 110-130 (center ~120) resta baseline PM.

**Micro-fix applicati in EV-F2**:
1. §1 Executive summary → totali canonici 12/32/134/0=178
2. §8 arcane_adept_orb → Opzione A (NOT_COMPATIBLE + secondary attrs + successor entry in §45)
3. §34-37 → ledger canonico 178, no ~110 approssimazione
4. §44 → LIVE ITEM ADJUDICATION LEDGER canonico completo
5. §45 → FUTURE COVERAGE GAP separato dal ledger 178
6. §46 → F2-Q1..F2-Q12 verbatim extraction
7. §47 → PM directive acknowledgment (this section)

---

## 🛑 EXPLICIT STOP FINALE · EV-F2 · ACCOUNTING MICRO-FIX APPLICATO · PENDING F2-Q VERDICTS

- **RV3-EV**: OPEN
- **EV-F2**: DRAFT GENERATED
- **AFX1**: HOLD (DO NOT START)
- **ITEM CREATION**: NOT AUTHORIZED
- **REGISTRY V3 APPLY**: NOT AUTHORIZED
- **FIELD BACKFILL**: NOT AUTHORIZED
- **GATE 11**: HOLD
- **MONACO / WAVE 1**: HOLD
- **CACCIATORE DEL VUOTO**: NOT LIVE · NOT SELECTABLE · NOT IMPLEMENTED

Governance locks:
- `apply_authorized = false`
- `item_creation_authorized = false`
- `registry_apply_authorized = false`
- `field_addition_authorized = false`
- `backfill_authorized = false`
- `class_slug_write_count = 0`
- `db_write_count = 0`
- Sealed integrity 36/36 attesa (validazione finale post-artifact)
- lore_meta.py invariato
- Nessuna modifica su backend/frontend/scripts/tests/OpenAPI
- R18.3f originali + R1 audit + Closure Report + Closure Manifest + RV3-EV + EV-F1 = IMMUTATI
- Nessun append PRD (RV3-EV/EV-F2 restano OPEN)

**Attendo PM directive su EV-F2 (APPROVE / CONDITIONAL / REWORK / HOLD) prima di ogni ulteriore azione.**
