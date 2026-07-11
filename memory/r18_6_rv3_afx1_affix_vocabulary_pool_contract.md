# R18.6.RV3-AFX1 · Affix Vocabulary & Pool Contract

**Documento**: `r18_6_rv3_afx1_affix_vocabulary_pool_contract.md`
**Parent gates**: R18.6.RV3-EV (CLOSED) · EV-F1 (CLOSED) · EV-F2 (CLOSED)
**Regime**: DOCUMENTAL ONLY · READ-ONLY DISCOVERY · Italian · Zero write · Zero code · Zero DB mutation
**Natura**: CONTRACT DESIGN GATE (NO item generation · NO affix backfill · NO Registry v3 apply)
**Sealed integrity**: 36/36 · `lore_meta.py` = `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`
**Cacciatore del Vuoto**: ACTIVE-DESIGN-READY · NOT LIVE · NOT SELECTABLE · NOT IMPLEMENTED

---

## 1 · Executive summary

AFX1 è il **contract design gate** che definisce il vocabolario canonico, i namespace, i pool e le regole di eleggibilità degli affix del **Cacciatore del Vuoto** (`class_slug = cacciatore_del_vuoto`) destinati al futuro modulo Registry v3.

**Deliverable AFX1**:
- Vocabolario canonico affix (10 famiglie ratificate)
- Namespace + internal tag + player-facing label per famiglia
- Eligibility item/tier/rarity per famiglia
- Vincoli meccanici LOCK (Fragment cap=5, marks=5, duration=10, proc 45%)
- Contratto `affix_pool_tag` (data type, multi/single, namespace, version, null handling)
- Regole anti-P2W
- Boss safeguard preservation

**Deliverable AFX1 NON contiene**:
- item creation · item_id · item names finali · CSV
- affix backfill · Registry v3 apply · module generation
- OpenAPI · backend · frontend · DB write · schema change
- riapertura EV-F2 ledger 178 (12/32/134/0 immutable)

---

## 2 · Governance

**Locks attivi**:
- `apply_authorized = false`
- `item_creation_authorized = false`
- `registry_v3_apply_authorized = false`
- `field_addition_authorized = false`
- `backfill_authorized = false`
- `affix_population_authorized = false`
- `db_write_count = 0`
- `mutation_forbidden = true`
- `sealed_files_immutability = true`

**Sealed integrity check**:
- Pre-work: pytest 6/6 PASS · lore_meta.py SHA `a18f708b...965b8f` invariato
- Post-work: rieseguire seal check in validazione finale

**AFX1 NON introduce nuovi sigilli**. Nessun file applicativo toccato.

---

## 3 · Regime documental only

**Regime AFX1**:
- Solo `/app/memory/` scritto (2 nuovi file: `.md` + `.json`)
- Nessuna esecuzione codice o migration
- Nessuna query MongoDB con effetti collaterali (solo read se necessario per baseline discovery)
- Nessun file backend/frontend/scripts/tests toccato
- Lingua: italiano only
- Formato: markdown + JSON strutturato

**Nessun impulso a scrivere codice React/FastAPI/route/test/seed/MVP** — anti-drift lock permanente.

---

## 4 · Precedenza documentale (RV3-EV / EV-F1 / EV-F2 / AFX1)

Ordine di precedenza per lettura/interpretazione:

| Aspetto | Documento authoritative |
|---|---|
| Ledger 178 / adjudication finale | **EV-F2** (immutable, ratified) |
| Metadata readiness + L12=T1 + catalog lineage | **EV-F1** (closed) |
| Baseline storica gate + target profile | **RV3-EV originale** (immutable) |
| Formula ILVL + rarity distribution live | **EV-F2** |
| Contratto affix vocabulary + pool | **AFX1** (this document, draft) |
| Governance locks + immutability | **concordanti su tutti i gate** |

**Regola**: in caso di divergenza, AFX1 NON riapre nessun aspetto EV-F2/EV-F1/RV3-EV. AFX1 aggiunge esclusivamente contratti affix; non modifica ledger, non riclassifica item, non altera adjudication.

---

## 5 · Source of Truth consumption (G1-G5, RV3 planning, EV closures)

**Consumati (NON riaperti)**:
- **G1 STAT_DESIGN**: Int → Con → Dex stat priority
- **G2 PROFICIENCY_DESIGN**: focus · balestra · pugnale (literal LOCK)
- **G3 GAMEPLAY_LOOP**: Identify → Mark → Drain → Payoff
- **G4 RESOURCE_MECHANIC**: Frammenti di Onirade, hard cap = 5
- **G5 EQUIP_DESIGN**: stoffa · cuoio (armor proficiency); tier T1-T5 mapping
- **RV3 ADDITIVE PLANNING**: additive-only, no field addition, no rename, no backfill
- **RV3-EV CLOSED**: baseline audit
- **EV-F1 CLOSED**: metadata readiness + L12=T1 lock + catalog lineage separation
- **EV-F2 CLOSED**: ledger 12/32/134/0 immutable

**AFX1 non modifica nessuno di questi documenti**.

---

## 6 · Sealed integrity baseline

**Pre-AFX1 baseline** (verificato):
- pytest `backend/tests/backend_r18_4_sealed_integrity_test.py`: 6 passed
- 36/36 sealed artifacts byte-identical
- `lore_meta.py` SHA anchor: `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`
- backend/frontend/scripts/tests/OpenAPI/PRD: 0 modifiche in questo dispatch

**Durante AFX1**: nessun file applicativo toccato. Nessun nuovo sigillo aggiunto. 36/36 sigilli byte-identical mantenuti.

---

## 7 · Non-authorization inventory (cosa AFX1 NON fa)

AFX1 **NON**:
- crea item · assegna item_id · propone item names finali · esporta CSV
- modifica i 178 item live
- modifica Registry v2
- popola `affix_pool_tag` sui 178 item
- esegue backfill
- applica Registry v3
- crea moduli backend
- modifica OpenAPI
- attiva Hall
- attiva Trial
- migra class_slug
- avvia Gate 11
- avvia Wave 1 (Monaco/Druido/Alchimista/Bardo/Negromante)
- avvia R18.3f-NC1
- riapre EV-F1/EV-F2/RV3-EV
- modifica G1-G5
- amplia G2 proficiency (focus/balestra/pugnale resta LOCK)
- introduce nuove stat scaling
- introduce nuove armor family

---

## 8 · AFX1 scope declaration

**In-scope**:
- Vocabolario canonico affix (10 famiglie)
- Namespace + internal tag + player-facing label
- Eligibility item type × tier × rarity per famiglia
- Effect scope, stacking rule, hard/soft caps
- Conflict group, validation rule, localization readiness
- Contratto `affix_pool_tag` (design-only)
- Regole anti-P2W
- Boss safeguard preservation
- EV-F2 ledger consumption (immutable)
- Condition code catalog per i 32 REUSE_CONDITIONAL
- Risk register + PM open questions
- GO/HOLD recommendation

**Out-of-scope**: tutto ciò elencato in §7.

---

## 9 · class_slug = cacciatore_del_vuoto

**Class identity anchor**:
- `class_slug`: **`cacciatore_del_vuoto`**
- Bridge legacy: `warlock` (accepted via R18.3e sealed)
- Cross-class rivali (strict separation): `mago`, `negromante`, `bardo`, `cacciatore_di_mostri`
- Retro-branding: **VIETATO** (regola PM ratified in EV-F2)
- Status: ACTIVE-DESIGN-READY · NOT LIVE · NOT SELECTABLE · NOT IMPLEMENTED

**Nessuna modifica a `class_slug` in AFX1**. NC1 dependency preservata per migrazione futura.

---

## 10 · Gameplay loop lock

**Loop identità (G3 immutable)**:
1. **Identify** — targeting condition + bersaglio marchiabile
2. **Mark** — applicazione Marchio del Vuoto sul bersaglio
3. **Drain** — canalizzazione + generazione Frammenti di Onirade
4. **Payoff** — consumo Frammenti + effetto risolutivo (dispel/burst/ritual)

**Regole loop**:
- Refresh dello stesso Marchio NON resetta eligibility Frammenti
- Bersaglio non Marchiato NON genera Frammenti
- Frammenti sono resource class-specific (no cross-class)
- Nessun Frammento passivo gratuito

**AFX1 preserva loop**. Nessuna alterazione ordine/step.

---

## 11 · Resource mechanic lock (Frammenti di Onirade, cap=5)

**Frammenti di Onirade (G4 immutable)**:
- **Hard cap**: 5 Frammenti
- **Generation**: solo da bersaglio Marchiato (Drain step)
- **Consumption**: Payoff step (dispel/burst/ritual)
- **Persistence**: entro combat (no cross-phase, no cross-instance)
- **Overcap**: waste (non stack oltre 5)

**Divieti resource**:
- Fragment cap > 5 · VIETATO
- Passive gratis · VIETATO
- Cross-phase persistence · VIETATO
- Random full-resource waste · VIETATO
- Generazione da non-Marchiato · VIETATO

**AFX1 preserva Frammenti cap=5 lock**.

---

## 12 · Stat priority lock (Int → Con → Dex)

**Stat scaling identità (G1 immutable)**:
- **Primary**: Intelligenza (Int)
- **Secondary**: Costituzione (Con) — resistenza rituali
- **Tertiary**: Destrezza (Dex) — mobilità durante canalizzazione

**Regole scaling**:
- Damage scaling: **SOLO Intelligenza**
- Dex damage scaling · **VIETATO**
- Forza damage scaling · **VIETATO**
- Dual Int/Dex scaling · **VIETATO** (regola anti-retro-branding voidpiercer-bow)

**AFX1 preserva stat priority**. Nessuna nuova stat scaling introdotta.

---

## 13 · Armor lock (stoffa, cuoio)

**Armor proficiency (G5 immutable)**:
- **Stoffa** (cloth/robe/light): full proficiency
- **Cuoio** (leather/medium): full proficiency
- **Metallo pesante** (heavy/plate/mail/scale): **VIETATO**
- **Shield**: NOT applicable (weapon-hand slot conflict con focus/balestra/pugnale)

**AFX1 non aggiunge nuove armor family**.

---

## 14 · Weapon proficiency lock (focus, balestra, pugnale)

**G2 proficiency literal LOCK**:
- **Focus** (arcane implement, tag `focus`)
- **Balestra** (crossbow — mapping DB: `crossbow` — complete gap live)
- **Pugnale** (dagger, tag `dagger`)

**G2 LOCK immutabile durante AFX1**:
- AFX1 **CONSUMA** G2
- AFX1 **NON RIAPRE** G2
- AFX1 **NON RATIFICA** nuove weapon family
- AFX1 **NON PROMUOVE** semantic overlap (tome/wand/staff/grimoire/rod/bow/instrument/flask NON diventano proficiency Vuoto)

---

## 15 · Proficiency exclusion list

**Famiglie weapon esplicitamente escluse da Vuoto proficiency** (EV-F2 ratified):

| Famiglia | DB tag | Motivo |
|---|---|---|
| Tome | `tome` | Caster tool literal, ≠ focus |
| Staff | `staff` | Caster tool literal, ≠ focus |
| Wand | `wand` | Caster tool literal, ≠ focus |
| Rod | `rod` | Caster tool literal, ≠ focus |
| Grimoire | `grimoire` | Book variant, ≠ focus |
| Bow | `bow` | Ranged non-magic, ≠ balestra |
| Instrument | `instrument` | Bard weapon, ≠ Vuoto |
| Sonic | `sonic` | Bard weapon variant, ≠ Vuoto |
| Alchemical_flask | `alchemical_flask` | Alchemist weapon, ≠ Vuoto |
| Sword | `sword` | Melee non-dagger, ≠ pugnale |
| Axe | `axe` | Melee heavy, ≠ pugnale |
| Mace | `mace` | Melee blunt, ≠ pugnale |
| Spear | `spear` | Reach, ≠ pugnale |
| Two_handed | `two_handed` | Modifier, incompatibile |

**Nessuna promozione futura ammessa via AFX1**. Regola FINAL.

---

## 16 · AFX1 non-expansion policy

**Policy invariante**:
- AFX1 **NON amplia** G2 proficiency
- AFX1 **NON introduce** nuove weapon family per Vuoto
- AFX1 **NON promuove** tome/staff/wand/grimoire/etc a "focus semantico"
- AFX1 **NON crea** nuove armor family
- AFX1 **NON crea** nuove stat scaling
- AFX1 **NON riapre** loop, resource, class_slug, boss safeguard, EV-F2 ledger

Ogni pressione a espansione richiede **nuovo verdict PM dedicato** (fuori AFX1).

---

## 17 · Famiglia 1 · Potenza Marchio · namespace/tag/label

| Field | Value |
|---|---|
| Canonical namespace | `void.mark.power` |
| Internal tag | `AFX_MARK_POWER` |
| Player-facing label (IT) | "Potenza del Marchio" |
| Player-facing label (EN) | "Mark Power" |
| Version | `v1.0` |

---

## 18 · Famiglia 1 · Descrizione

**Descrizione**: Incrementa la potenza applicativa del Marchio del Vuoto sul bersaglio Identificato. Aumenta la magnitudo dell'impronta rituale ma **NON** modifica la durata (§22-26 famiglia dedicata) né la generazione Frammenti (§37-41).

**Scope narrativo**: rappresenta il grado di penetrazione oniroide del Marchio nella coscienza del bersaglio.

---

## 19 · Famiglia 1 · Eligibility item + tier + rarity

| Dimension | Eligibility |
|---|---|
| Item family | focus · pugnale · accessory (neck/ring/back) · armor chest (proc-slot) |
| Tier eligibility | T1 · T2 · T3 · T4 · T5 |
| Rarity eligibility | Common · Uncommon · Rare · Epic · Legendary |
| Class-specific | true (cacciatore_del_vuoto only) |
| Shared | false |
| Universal | false |

---

## 20 · Famiglia 1 · Effect scope + stacking + caps

| Field | Value |
|---|---|
| Effect scope | Marchio del Vuoto (Mark step) |
| Stacking rule | additive intra-slot, max 1 affix mark_power per item |
| Hard cap | +30% mark_power totale (somma multi-slot) |
| Soft cap | +20% mark_power |
| Diminishing returns | ×0.5 oltre soft cap |
| Combined proc cap | 45% (globale, §70) |

---

## 21 · Famiglia 1 · Conflict + validation + localization

| Field | Value |
|---|---|
| Conflict group | `MARK_MAGNITUDE_GROUP` (exclusive con eventuali "reduce mark power" futuri) |
| Validation rule | bersaglio deve essere Identified prima di Mark; se non Identified → affix idle |
| Localization readiness | IT/EN pronte; slot per FR/DE/ES/JP/BR in Registry v3 futuro |
| PvP validation | require explicit PM validation gate (VIETATO senza validation) |
| Anti-P2W | `can_be_sold_for_real_money = false` obbligatorio |

---

## 22 · Famiglia 2 · Durata Marchio · namespace/tag/label

| Field | Value |
|---|---|
| Canonical namespace | `void.mark.duration` |
| Internal tag | `AFX_MARK_DURATION` |
| Player-facing label (IT) | "Durata del Marchio" |
| Player-facing label (EN) | "Mark Duration" |
| Version | `v1.0` |

---

## 23 · Famiglia 2 · Descrizione

Estende la durata del Marchio del Vuoto sul bersaglio (in turni combat). Non aumenta potenza (§17-21) né Drain efficacy (§27-31).

**Vincolo**: durata Marchio **non può superare 10 turni** (§69). Refresh Marchio non resetta eligibility Frammenti.

---

## 24 · Famiglia 2 · Eligibility item + tier + rarity

| Dimension | Eligibility |
|---|---|
| Item family | focus · accessory (neck/back) · armor chest · pugnale |
| Tier eligibility | T1 · T2 · T3 · T4 · T5 |
| Rarity eligibility | Uncommon · Rare · Epic · Legendary (NO Common — mark duration è secondary stat) |
| Class-specific | true |
| Shared | false |
| Universal | false |

---

## 25 · Famiglia 2 · Effect scope + stacking + caps

| Field | Value |
|---|---|
| Effect scope | Mark duration (in combat turns) |
| Stacking rule | additive intra-slot, max 1 affix mark_duration per item |
| Hard cap | 10 turni totali (§69, mai superabile) |
| Soft cap | 8 turni |
| Diminishing returns | ×0.3 oltre soft cap (≥8 turni) |
| Combined proc cap | 45% (§70) |

---

## 26 · Famiglia 2 · Conflict + validation + localization

| Field | Value |
|---|---|
| Conflict group | `MARK_TEMPORAL_GROUP` (exclusive con futuri "shorten mark") |
| Validation rule | durata calcolata al Mark application; refresh non estende oltre 10 |
| Localization readiness | IT/EN pronte |
| PvP validation | require explicit PM validation |
| Anti-P2W | `can_be_sold_for_real_money = false` |

---

## 27 · Famiglia 3 · Efficacia Drain · namespace/tag/label

| Field | Value |
|---|---|
| Canonical namespace | `void.drain.efficacy` |
| Internal tag | `AFX_DRAIN_EFFICACY` |
| Player-facing label (IT) | "Efficacia del Drenaggio" |
| Player-facing label (EN) | "Drain Efficacy" |
| Version | `v1.0` |

---

## 28 · Famiglia 3 · Descrizione

Aumenta l'efficacia del passo Drain (canalizzazione post-Mark). Modula: danno del channel, tick rate, chance di generazione Frammenti bonus (soggetto a §37-41 e cap §67 e segment cap §71).

---

## 29 · Famiglia 3 · Eligibility item + tier + rarity

| Dimension | Eligibility |
|---|---|
| Item family | focus (channel primary) · balestra · pugnale · accessory (ring/back) |
| Tier eligibility | T1 · T2 · T3 · T4 · T5 |
| Rarity eligibility | Common · Uncommon · Rare · Epic · Legendary |
| Class-specific | true |
| Shared | false |
| Universal | false |

---

## 30 · Famiglia 3 · Effect scope + stacking + caps

| Field | Value |
|---|---|
| Effect scope | Drain channel (damage tick + fragment gen) |
| Stacking rule | additive intra-slot, max 1 affix drain_efficacy per item |
| Hard cap | +40% drain efficacy totale |
| Soft cap | +25% |
| Diminishing returns | ×0.5 oltre soft cap |
| Combined proc cap | 45% (§70) |
| Segment cap | max 2 Frammenti per resource segment (§71 focus channel bonus) |

---

## 31 · Famiglia 3 · Conflict + validation + localization

| Field | Value |
|---|---|
| Conflict group | `DRAIN_EFFICACY_GROUP` |
| Validation rule | bersaglio deve essere Marchiato attivo; Drain su bersaglio Non-Marchiato → idle |
| Localization readiness | IT/EN pronte |
| PvP validation | require explicit PM validation |
| Anti-P2W | `can_be_sold_for_real_money = false` |

---

## 32 · Famiglia 4 · Qualità Dispel · namespace/tag/label

| Field | Value |
|---|---|
| Canonical namespace | `void.payoff.dispel` |
| Internal tag | `AFX_DISPEL_QUALITY` |
| Player-facing label (IT) | "Qualità del Dispel" |
| Player-facing label (EN) | "Dispel Quality" |
| Version | `v1.0` |

---

## 33 · Famiglia 4 · Descrizione

Aumenta la qualità del Payoff dispel (rimozione buff nemici, cleanse debuff alleati) durante la fase Payoff. **Non** annulla boss diretto (boss safeguard §75).

**Area dispel**: valido su ambiente 3F (safeguard §75) — annullamento summon valido su 5F.

---

## 34 · Famiglia 4 · Eligibility item + tier + rarity

| Dimension | Eligibility |
|---|---|
| Item family | focus · accessory (neck) · armor (chest, back) |
| Tier eligibility | T2 · T3 · T4 · T5 (NO T1 — dispel è mid-game affix) |
| Rarity eligibility | Rare · Epic · Legendary |
| Class-specific | true |
| Shared | false |
| Universal | false |

---

## 35 · Famiglia 4 · Effect scope + stacking + caps

| Field | Value |
|---|---|
| Effect scope | Payoff dispel step |
| Stacking rule | additive intra-slot, max 1 affix dispel_quality per item |
| Hard cap | +50% dispel efficacy (limitato per non trivializzare boss add) |
| Soft cap | +30% |
| Diminishing returns | ×0.4 oltre soft cap |
| Combined proc cap | 45% (§70) |
| Boss safeguard | NO direct boss cleanse (§75) |

---

## 36 · Famiglia 4 · Conflict + validation + localization

| Field | Value |
|---|---|
| Conflict group | `PAYOFF_DISPEL_GROUP` |
| Validation rule | Payoff step richiede >=1 Frammento consumato; NO dispel su boss diretto |
| Localization readiness | IT/EN pronte |
| PvP validation | require explicit PM validation |
| Anti-P2W | `can_be_sold_for_real_money = false` |

---

## 37 · Famiglia 5 · Interazione Frammenti · namespace/tag/label

| Field | Value |
|---|---|
| Canonical namespace | `void.fragment.interaction` |
| Internal tag | `AFX_FRAGMENT_INTERACTION` |
| Player-facing label (IT) | "Sinergia Frammenti" |
| Player-facing label (EN) | "Fragment Synergy" |
| Version | `v1.0` |

---

## 38 · Famiglia 5 · Descrizione

Modula generazione, retention e chain bonus dei Frammenti di Onirade. Cap totale Frammenti **5 (§67, immutabile)**. Sotto-effetti:
- +1 Frammento bonus (focus channel §71)
- +1 Frammento bonus ritual-close (pugnale §72, max una volta per applicazione Marchio)
- Chain bonus multi-Frammento (Payoff efficacy bonus per >=3 Frammenti al consumo)

---

## 39 · Famiglia 5 · Eligibility item + tier + rarity

| Dimension | Eligibility |
|---|---|
| Item family | focus (channel bonus) · pugnale (ritual-close bonus) · accessory (back/neck) · armor (chest, waist alias) |
| Tier eligibility | T2 · T3 · T4 · T5 |
| Rarity eligibility | Uncommon · Rare · Epic · Legendary |
| Class-specific | true |
| Shared | false |
| Universal | false |

---

## 40 · Famiglia 5 · Effect scope + stacking + caps

| Field | Value |
|---|---|
| Effect scope | Fragment generation + retention + chain bonus |
| Stacking rule | additive intra-slot, max 1 affix fragment_interaction per item |
| Hard cap Fragment total | **5** (mai superabile, §67) |
| Segment cap per resource | max 2 Frammenti (§71 focus channel bonus) |
| Ritual-close bonus | max 1 per applicazione Marchio (§72 pugnale) |
| Combined proc cap | 45% (§70) |

**Divieto**: generazione Frammenti da bersaglio non-Marchiato → **VIETATO**.

---

## 41 · Famiglia 5 · Conflict + validation + localization

| Field | Value |
|---|---|
| Conflict group | `FRAGMENT_INTERACTION_GROUP` |
| Validation rule | Frammenti solo da Marchiato attivo; cap=5 hard-limit; overcap = waste (no bonus) |
| Localization readiness | IT/EN pronte |
| PvP validation | require explicit PM validation |
| Anti-P2W | `can_be_sold_for_real_money = false` |

---

## 42 · Famiglia 6 · Efficacia Payoff · namespace/tag/label

| Field | Value |
|---|---|
| Canonical namespace | `void.payoff.efficacy` |
| Internal tag | `AFX_PAYOFF_EFFICACY` |
| Player-facing label (IT) | "Efficacia del Risolvente" |
| Player-facing label (EN) | "Payoff Efficacy" |
| Version | `v1.0` |

---

## 43 · Famiglia 6 · Descrizione

Modula magnitudo del Payoff (danno burst / dispel magnitude / ritual outcome) in funzione dei Frammenti consumati.

**Regola**: efficacia scala lineare con Frammenti consumati (1→5). NO trivializzazione boss (safeguard §75).

---

## 44 · Famiglia 6 · Eligibility item + tier + rarity

| Dimension | Eligibility |
|---|---|
| Item family | focus · pugnale · accessory (neck/ring) · armor chest |
| Tier eligibility | T1 · T2 · T3 · T4 · T5 |
| Rarity eligibility | Common · Uncommon · Rare · Epic · Legendary |
| Class-specific | true |
| Shared | false |
| Universal | false |

---

## 45 · Famiglia 6 · Effect scope + stacking + caps

| Field | Value |
|---|---|
| Effect scope | Payoff step (burst/dispel/ritual outcome) |
| Stacking rule | additive intra-slot, max 1 affix payoff_efficacy per item |
| Hard cap | +45% payoff efficacy (allineato combined proc §70) |
| Soft cap | +30% |
| Diminishing returns | ×0.5 oltre soft cap |
| Combined proc cap | 45% (§70) |
| Boss safeguard | NO direct boss nullification (§75) |

---

## 46 · Famiglia 6 · Conflict + validation + localization

| Field | Value |
|---|---|
| Conflict group | `PAYOFF_EFFICACY_GROUP` |
| Validation rule | Payoff richiede >=1 Frammento; efficacia scale (1x/2x/3x/4x/5x soft) |
| Localization readiness | IT/EN pronte |
| PvP validation | require explicit PM validation |
| Anti-P2W | `can_be_sold_for_real_money = false` |

---

## 47 · Famiglia 7 · Anti-incorporeo · namespace/tag/label

| Field | Value |
|---|---|
| Canonical namespace | `void.antitype.incorporeal` |
| Internal tag | `AFX_ANTI_INCORPOREAL` |
| Player-facing label (IT) | "Contro Incorporei" |
| Player-facing label (EN) | "Anti-Incorporeal" |
| Version | `v1.0` |

---

## 48 · Famiglia 7 · Descrizione

Aumenta efficacia contro bersagli tipo `incorporeal` (spectre, shade, wraith, ombra). Vuoto è tematicamente void-caster, allineato ad anti-void-adjacent creature.

**Scope**: applicabile solo su bersagli con tag `type: incorporeal` (validation Registry v3).

---

## 49 · Famiglia 7 · Eligibility item + tier + rarity

| Dimension | Eligibility |
|---|---|
| Item family | focus · balestra · pugnale · accessory (ring/back) |
| Tier eligibility | T2 · T3 · T4 · T5 (mid-late game affix) |
| Rarity eligibility | Rare · Epic · Legendary |
| Class-specific | true |
| Shared | false |
| Universal | false |

---

## 50 · Famiglia 7 · Effect scope + stacking + caps

| Field | Value |
|---|---|
| Effect scope | Damage vs `incorporeal` type only |
| Stacking rule | additive intra-slot, max 1 affix anti_incorporeal per item |
| Hard cap | +60% damage vs incorporeal |
| Soft cap | +40% |
| Diminishing returns | ×0.5 oltre soft cap |
| Combined proc cap | 45% (§70) |
| Type validation | required (`type: incorporeal` present) |

---

## 51 · Famiglia 7 · Conflict + validation + localization

| Field | Value |
|---|---|
| Conflict group | `ANTITYPE_INCORPOREAL_GROUP` |
| Validation rule | bersaglio validated con tag incorporeal; idle su altri type |
| Localization readiness | IT/EN pronte |
| PvP validation | require explicit PM validation |
| Anti-P2W | `can_be_sold_for_real_money = false` |

---

## 52 · Famiglia 8 · Anti-summon · namespace/tag/label

| Field | Value |
|---|---|
| Canonical namespace | `void.antitype.summon` |
| Internal tag | `AFX_ANTI_SUMMON` |
| Player-facing label (IT) | "Contro Evocazioni" |
| Player-facing label (EN) | "Anti-Summon" |
| Version | `v1.0` |

---

## 53 · Famiglia 8 · Descrizione

Aumenta efficacia contro bersagli `type: summon` (evocazioni, imp, familiar, boss-summoned adds validati).

**Boss safeguard §75**: valido su boss-summoned adds validati. **NON** valido su boss diretto.

---

## 54 · Famiglia 8 · Eligibility item + tier + rarity

| Dimension | Eligibility |
|---|---|
| Item family | focus · pugnale · accessory (ring/back) |
| Tier eligibility | T2 · T3 · T4 · T5 |
| Rarity eligibility | Rare · Epic · Legendary |
| Class-specific | true |
| Shared | false |
| Universal | false |

---

## 55 · Famiglia 8 · Effect scope + stacking + caps

| Field | Value |
|---|---|
| Effect scope | Damage / dispel vs `summon` type; boss-summoned valid add ok, boss diretto NO |
| Stacking rule | additive intra-slot, max 1 affix anti_summon per item |
| Hard cap | +55% damage vs summon |
| Soft cap | +35% |
| Diminishing returns | ×0.5 oltre soft cap |
| Combined proc cap | 45% (§70) |
| Boss safeguard | NO direct boss nullification (§75) |

---

## 56 · Famiglia 8 · Conflict + validation + localization

| Field | Value |
|---|---|
| Conflict group | `ANTITYPE_SUMMON_GROUP` |
| Validation rule | bersaglio validated con tag summon; boss diretto immune; boss add valid ok |
| Localization readiness | IT/EN pronte |
| PvP validation | require explicit PM validation |
| Anti-P2W | `can_be_sold_for_real_money = false` |

---

## 57 · Famiglia 9 · Mobilità durante canalizzazione · namespace/tag/label

| Field | Value |
|---|---|
| Canonical namespace | `void.channel.mobility` |
| Internal tag | `AFX_CHANNEL_MOBILITY` |
| Player-facing label (IT) | "Mobilità in Canalizzazione" |
| Player-facing label (EN) | "Channel Mobility" |
| Version | `v1.0` |

---

## 58 · Famiglia 9 · Descrizione

Consente movimento parziale/completo durante il Drain channel step. Utility affix (Dex tertiary stat priority §12).

**Non aumenta** damage. **Non aumenta** Fragment generation. **Solo** mobilità.

---

## 59 · Famiglia 9 · Eligibility item + tier + rarity

| Dimension | Eligibility |
|---|---|
| Item family | armor (feet aggregato, legs aggregato, waist alias) · accessory (back) · pugnale |
| Tier eligibility | T1 · T2 · T3 · T4 · T5 |
| Rarity eligibility | Uncommon · Rare · Epic · Legendary (NO Common — utility premium) |
| Class-specific | true |
| Shared | false |
| Universal | false |

---

## 60 · Famiglia 9 · Effect scope + stacking + caps

| Field | Value |
|---|---|
| Effect scope | Movement during Drain channel step |
| Stacking rule | additive intra-slot, max 1 affix channel_mobility per item |
| Hard cap | 100% movement retention during channel (max: canalizzazione mobile completa Legendary T5) |
| Soft cap | 60% |
| Diminishing returns | flat cap oltre 60% richiede Epic+ + T3+ |
| Combined proc cap | N/A (utility, no proc) |
| Damage impact | 0 (mobility only) |

---

## 61 · Famiglia 9 · Conflict + validation + localization

| Field | Value |
|---|---|
| Conflict group | `CHANNEL_MOBILITY_GROUP` |
| Validation rule | applies during Drain channel only; no effect on Mark/Payoff |
| Localization readiness | IT/EN pronte |
| PvP validation | require explicit PM validation |
| Anti-P2W | `can_be_sold_for_real_money = false` |

---

## 62 · Famiglia 10 · Protezione durante rituali · namespace/tag/label

| Field | Value |
|---|---|
| Canonical namespace | `void.ritual.protection` |
| Internal tag | `AFX_RITUAL_PROTECTION` |
| Player-facing label (IT) | "Protezione Rituale" |
| Player-facing label (EN) | "Ritual Protection" |
| Version | `v1.0` |

---

## 63 · Famiglia 10 · Descrizione

Aumenta damage reduction / crowd-control resistance durante il Payoff ritual step. Utilizza Costituzione (secondary stat §12).

**Non** aumenta HP totale. **Solo** riduzione danno + CC resistance transient durante ritual step.

---

## 64 · Famiglia 10 · Eligibility item + tier + rarity

| Dimension | Eligibility |
|---|---|
| Item family | armor (chest, cloth/medium/leather) · accessory (neck/back) · shield NOT applicable (§13) |
| Tier eligibility | T1 · T2 · T3 · T4 · T5 |
| Rarity eligibility | Common · Uncommon · Rare · Epic · Legendary |
| Class-specific | true |
| Shared | false |
| Universal | false |

---

## 65 · Famiglia 10 · Effect scope + stacking + caps

| Field | Value |
|---|---|
| Effect scope | Damage reduction + CC resist during Payoff ritual step |
| Stacking rule | additive intra-slot, max 1 affix ritual_protection per item |
| Hard cap | -50% damage taken during ritual · +40% CC resist |
| Soft cap | -30% damage · +25% CC resist |
| Diminishing returns | ×0.5 oltre soft cap |
| Combined proc cap | N/A (defensive utility) |

---

## 66 · Famiglia 10 · Conflict + validation + localization

| Field | Value |
|---|---|
| Conflict group | `RITUAL_PROTECTION_GROUP` |
| Validation rule | attivo solo durante ritual Payoff step; idle altrove |
| Localization readiness | IT/EN pronte |
| PvP validation | require explicit PM validation |
| Anti-P2W | `can_be_sold_for_real_money = false` |

---

## 67 · Fragment cap LOCK

**Hard invariant**: **`Fragments_current <= 5`** in ogni istante.

- Overcap Frammenti generati oltre 5 → waste (non stack)
- Nessun affix può alterare `fragment_hard_cap`
- Frammenti persistono entro combat; **NO** cross-phase persistence (§77)
- Nessun random full-resource waste ammesso (divieto §73)

---

## 68 · Active marks hard cap

**Hard invariant**: **`active_marks_by_player <= 5`** in ogni istante.

- Applicare Marchio quando active_marks >= 5 → **fallisce silenziosamente** (no bonus)
- Refresh Marchio esistente non incrementa counter
- Marchi expired liberano slot al tick successivo
- Divieto: active_marks > 5 → **VIETATO**

---

## 69 · Mark duration hard cap

**Hard invariant**: **`Mark_duration_turni <= 10`** turni combat.

- Affix `AFX_MARK_DURATION` (§22-26) può estendere fino a 10, MAI oltre
- Refresh Marchio non estende oltre 10
- Refresh dello stesso Marchio **NON** resetta eligibility Frammenti (regola loop §10)

---

## 70 · Combined proc hard cap 45%

**Hard invariant**: **`combined_proc_chance <= 45%`** su somma multi-slot affix con proc trigger.

- Somma tutte le proc chance stackate su slot equipaggiati
- Clamped a 45% (hard ceiling)
- Diminishing returns oltre soft cap ×0.5
- **Divieto**: combined proc > 45% → **VIETATO**

---

## 71 · Focus channel bonus + segment cap

**Focus weapon channel bonus**:
- Bonus: **+1 Frammento** per canalizzazione focus attiva
- Segment cap: **max 2 Frammenti per resource segment**
- Applicabile solo se weapon equipped è tag `focus`
- Non stackabile con multiple focus (unico bonus per canalizzazione)

**Segment definizione**: sub-window della canalizzazione (Drain step) con proprio cap Frammenti.

---

## 72 · Pugnale ritual-close bonus + refresh eligibility

**Pugnale ritual-close bonus**:
- Bonus: **+1 Frammento** al ritual-close (Payoff step chiusura)
- **Max 1 volta per applicazione Marchio** (refresh Marchio non riabilita il bonus)
- Applicabile solo se weapon equipped è tag `dagger`
- Non stackabile con multiple pugnali (unico bonus per Marchio)

**Regola eligibility**: refresh dello stesso Marchio NON resetta eligibility del bonus pugnale (già consumato per quel Marchio).

---

## 73 · Divieti affix enumeration

**Divieti esplicitamente ratificati** (nessun affix futuro può violarli):

| # | Divieto |
|---|---|
| 1 | Fragment cap > 5 |
| 2 | active_marks > 5 |
| 3 | Mark duration > 10 turni |
| 4 | Generazione Frammenti da bersaglio non-Marchiato |
| 5 | Frammenti passivi gratuiti |
| 6 | Direct boss nullification |
| 7 | Boss safeguard bypass |
| 8 | Cross-phase Fragment persistence |
| 9 | Random full-resource waste (senza player agency) |
| 10 | Dual Int/Dex scaling (dmg scaling ibrido) |
| 11 | Dex damage scaling |
| 12 | Forza damage scaling |
| 13 | PvP effect non validato |
| 14 | P2W (`can_be_sold_for_real_money = true`) |
| 15 | Retro-branding di item esistenti |
| 16 | Amplificazione G2 proficiency (tome/staff/wand/etc a "focus") |
| 17 | Mutazione dei 178 item live |
| 18 | Modifica ledger EV-F2 |

**Total divieti**: 18 hard rules.

---

## 74 · Anti-P2W contract

**Contratto anti-P2W obbligatorio** per ogni affix futuro:

- `can_be_sold_for_real_money = false` **obbligatorio**
- Applicabile a: T1-T5 · Common-Legendary · class-specific · shared · universal · utility unique
- Nessuna eccezione ammessa
- Fallback default `false` se field missing (§17 EV-F2 closure report)
- Pre-item creation verification obbligatoria
- Pre-registry apply verification obbligatoria
- Post-apply snapshot obbligatorio

**Rejected any affix con potenziale P2W bypass**.

---

## 75 · Boss safeguard

**Boss safeguard immutabile** (G3 + EV closures):

| Contesto | Safeguard |
|---|---|
| **3F (area dispel)** | Valido — dispel su ambiente ammesso |
| **5F (annullamento summon valida)** | Valido — anti_summon efficace su boss-summoned adds validati |
| **Boss diretto** | **IMMUNE** — nessun affix può annullare direttamente boss diretto |
| **Boss-summoned valid add** | Ammesso con safeguard (add validato con `type: summon`) |

**Divieti**:
- Direct boss nullification → **VIETATO**
- Boss phase / enrage cancellation → **VIETATO**
- Bypass validazione bersaglio → **VIETATO**

---

## 76 · Retro-branding forbidden

**Regola PM ratified** (EV-F2 closure):

- Retro-branding item esistenti al Cacciatore del Vuoto → **VIETATO**
- Nessun affix futuro può giustificare riuso item preserved (voidpiercer-bow / arcane_adept_orb / 6 warlock tome) sulla base di:
  - Nome contenente "Vuoto" / "Void" / "Oblio"
  - Lore vuoto/oblio
  - Warlock legacy association senza compatibility mecanica
- Retro-branding pressure → escalation PM
- **Voidpiercer-bow**: NOT_COMPATIBLE FINAL preservato
- **arcane_adept_orb**: NOT_COMPATIBLE preserved (Opzione A)

---

## 77 · Cross-phase persistence forbidden

**Regola resource lifecycle**:

- Frammenti di Onirade: **combat-scoped** (reset a fine combat)
- Cross-phase persistence → **VIETATO**
- Cross-instance persistence → **VIETATO**
- Persistence tra encounter → **VIETATO**
- Reset via wipe/logout → applicato (no stacking abuse)

Nessun affix può alterare lifecycle Frammenti.

---

## 78 · affix_pool_tag data contract (type/multi/namespace/version)

**Contratto documentale `affix_pool_tag`** (design-only, **NO POPULATION · NO BACKFILL · NO DB WRITE**):

| Field | Value |
|---|---|
| Data type | `string` (or `list[string]` for multi-value future) |
| Single vs multi | Design: **single-value primary** con extension multi-value in v2 futuro |
| Namespace | `void.<family>.<sub>` (es. `void.mark.power`, `void.drain.efficacy`) |
| Version | `v1.0` (locked per AFX1 draft) |
| Enum vocabulary | Chiuso a 10 namespace canonical (§17-66) |
| Format | lowercase · dot-separator · no spaces · ascii only |
| Length limits | min 8 char · max 64 char |

**No population 178 items**: campo `affix_pool_tag` resta null per tutti i 178 items live. Backfill futuro solo con nuovo gate dedicato post-AFX1 (PM verdict richiesto).

---

## 79 · null/unknown/invalid handling

**Contratto handling `affix_pool_tag`** valore anomalo:

| Case | Behavior |
|---|---|
| `null` | Meaning: "no affix pool assigned yet" · Runtime: item ha nessun affix · Design: default per T1 baseline · **Not P2W trigger** |
| `unknown` (valore non nel vocabolario canonico) | Runtime: log warning + treat as `null` · Validation: fail item creation attempt · Post-apply: audit alert |
| `invalid` (schema violation, formato errato) | Runtime: log error + treat as `null` · Validation: fail apply · Test: rejected |
| Missing field | Fallback: `null` (design-only fallback via config, no materialized default) |

**Nessun auto-derive**: `affix_pool_tag` non è mai derivato automaticamente da nome/lore/keyword item.

---

## 80 · class-specific/shared/universal semantics

**Semantica ownership affix**:

| Ownership tier | Semantics | Vuoto affix count (contract) |
|---|---|---|
| **Class-specific** | Solo `class_slug = cacciatore_del_vuoto` può equipaggiare/beneficiare | 10 famiglie AFX1 (all class-specific per Vuoto) |
| **Shared** | Multi-class (subset compatibili, es. `caster_group`) | 0 in AFX1 (design-only; futuro gate condiviso) |
| **Universal** | Qualsiasi class può equipaggiare (utility neutro) | 0 in AFX1 (design-only; futuro gate universal) |

**Rule**:
- Class-specific affix richiede `class_slug` match runtime
- Shared/Universal affix richiedono validation gate dedicato (fuori AFX1)
- 10 famiglie AFX1 sono **tutte class-specific per Vuoto** in questa versione contract

---

## 81 · EV-F2 ledger consumption (12/32/134/0 immutable)

**Ledger EV-F2 CONSUMATO (immutable, NON riaperto)**:

```
REUSE_VALID       =  12
REUSE_CONDITIONAL =  32
NOT_COMPATIBLE   = 134
PM_REVIEW        =   0
TOTAL            = 178
```

**AFX1 può definire**:
- affix eligibility (per famiglia, per item family, per tier, per rarity)
- condition code (per i 32 REUSE_CONDITIONAL) — vedi §83
- pool compatibility (namespace-level)
- future Registry v3 behavior (design-only)

**AFX1 NON può**:
- cambiare primary verdict di qualunque item nel ledger
- riaprire EV-F2
- promuovere item da NOT_COMPATIBLE a REUSE_CONDITIONAL/VALID
- declassare item da REUSE_VALID a NOT_COMPATIBLE
- introdurre nuovi verdict enum

**Qualunque modifica al ledger richiede riapertura PM esplicita di EV-F2** (VIETATO in AFX1).

---

## 82 · arcane_adept_orb & voidpiercer-bow preservation

**Preservation FINAL** (EV-F2 closure ratified):

| Item | Verdict | Mutation | Successor futuro | Retro-branding |
|---|---|---|---|---|
| `arcane_adept_orb` | NOT_COMPATIBLE | forbidden | `arcane_adept_orb_void_native_successor` (future coverage gap) | forbidden |
| `voidpiercer-bow` | NOT_COMPATIBLE FINAL | forbidden | none (bow ≠ Vuoto proficiency) | forbidden |

**AFX1 preserva entrambi**:
- Nessun affix futuro può giustificare riuso di questi item per Vuoto
- Nessun name-based / lore-based promotion ammesso
- Successor arcane_adept_orb: nuovo item Vuoto-native con nuovo item_id, proficiency focus/balestra/pugnale, stat Int, weapon family valida. **NO creation in AFX1**.

---

## 83 · Condition code catalog per i 32 REUSE_CONDITIONAL

**Catalog condition codes** (design-only, per Registry v3 additive futuro):

| Code | Descrizione | Item count nei 32 |
|---|---|---|
| `weapon_family_literal_G2_via_rec_classes_additive` | Weapon focus/dagger literal G2 | 2 |
| `armor_proficiency_stoffa_cuoio_via_rec_classes_additive` | Armor stoffa/cuoio proficient | 11 |
| `universal_accessory_slot_via_rec_classes_additive` | Accessory universal slot | 19 |
| **Total** | | **32** |

**Condition unlock prerequisite** (per tutti):
- Registry v3 additive apply `rec_classes: cacciatore_del_vuoto` (array append atomic, non-mutation)
- AFX1 vocabulary lock (this document + PM approval)
- Explicit item allowlist + per-item verdict + dry-run + snapshot + PM GO esplicito (F2-Q2 constraints)
- NO dynamic keyword selection
- NO bulk apply senza allowlist

**AFX1 NON esegue apply**. Definisce solo il contratto.

---

## 84 · Risk register + PM open questions AFX1

**Risk register AFX1**:

| ID | Risk | Severity | Mitigation | Status |
|---|---|---|---|---|
| AFX1-R1 | Pressure to expand G2 proficiency via AFX1 | HIGH governance | LOCK G2 §14-16, AFX1 non-expansion policy | MITIGATED |
| AFX1-R2 | Retro-branding pressure (voidpiercer/arcane_adept_orb) | HIGH | Regola PM §76 forbidden | MITIGATED |
| AFX1-R3 | Cross-class contamination (mago/negromante/bardo) | MEDIUM | Class-specific ownership §80 | ACCEPTED |
| AFX1-R4 | Combined proc > 45% via multi-slot stacking | HIGH mechanical | Hard cap §70 clamped | MITIGATED |
| AFX1-R5 | Fragment overcap via affix synergy | HIGH mechanical | Hard cap §67 immutable | MITIGATED |
| AFX1-R6 | Mark duration > 10 turni | MEDIUM | Hard cap §69 | MITIGATED |
| AFX1-R7 | Boss safeguard bypass | HIGH gameplay | §75 safeguard preserved | MITIGATED |
| AFX1-R8 | Anti-P2W bypass on affix | HIGH governance | Contract §74 obbligatorio | MITIGATED |
| AFX1-R9 | PvP unvalidated effect | MEDIUM | Require explicit PM validation gate | HOLD |
| AFX1-R10 | AFX1 vocabulary drift in Registry v3 apply | MEDIUM | Contract lock §78-80 | ACCEPTED |
| AFX1-R11 | Item creation impulse via AFX1 | HIGH governance | §7 non-authorization inventory | MITIGATED |
| AFX1-R12 | NC1 dependency bypass attempt | HIGH governance | NC1 = HOLD mandatory pre-migration §5 | ACCEPTED |

**PM Open Questions AFX1**:

| # | Question | Recommendation |
|---|---|---|
| AFX1-Q1 | Approvare i 10 canonical namespace `void.<family>.<sub>`? | APPROVE (nomi coerenti con G3/G4 loop) |
| AFX1-Q2 | Confermare combined proc hard cap = 45%? | CONFIRM (§70 mechanical safety) |
| AFX1-Q3 | Confermare Fragment cap = 5, active marks = 5, duration = 10? | CONFIRM (G4 + G3 loop) |
| AFX1-Q4 | Approvare Focus channel bonus +1 Frammento + segment cap 2? | APPROVE (§71 G2 focus lock) |
| AFX1-Q5 | Approvare Pugnale ritual-close bonus +1 Frammento max 1x per Marchio? | APPROVE (§72 G2 pugnale lock) |
| AFX1-Q6 | Boss safeguard 3F/5F/immune/valid add come attuale? | CONFIRM (§75) |
| AFX1-Q7 | `affix_pool_tag` single-value con estensione multi-value in v2? | APPROVE (§78) |
| AFX1-Q8 | Class-specific ownership all 10 famiglie AFX1? Shared/Universal in gate futuri? | APPROVE (§80) |
| AFX1-Q9 | Registry v3 additive `rec_classes: cacciatore_del_vuoto` come mechanism unlock 32 REUSE_CONDITIONAL? | APPROVE (§83, F2-Q2 constraints) |
| AFX1-Q10 | Localization readiness IT/EN in AFX1, altri lingue in Registry v3 futuro? | APPROVE |
| AFX1-Q11 | AFX1 → NC1 → Gate 11 sequence ratified? | CONFIRM (§85) |
| AFX1-Q12 | AFX1 closure gate follow-up (AFX2 vocabulary v2 vs Registry v3 architecture)? | HOLD PM directive futura |

---

## 85 · GO/HOLD recommendation + Registry v3 dependency + NC1 dependency + explicit STOP state

**GO/HOLD recommendation al PM**:

| Componente | Verdict |
|---|---|
| **AFX1 draft** | ✅ **DRAFT_GENERATED** (this document) |
| **AFX1 PM review** | 🕐 **PENDING** |
| **AFX1 closure** | 🔒 **HOLD** (draft only, PM must validate before CLOSED) |
| **Registry v3 module generation** | 🔒 **NOT AUTHORIZED** |
| **Registry v3 apply** | 🔒 **NOT AUTHORIZED** |
| **Affix backfill** | 🔒 **NOT AUTHORIZED** |
| **`affix_pool_tag` population** | 🔒 **NOT AUTHORIZED** |
| **Item creation** | 🔒 **NOT AUTHORIZED** |
| **arcane_adept_orb successor creation** | 🔒 **NOT AUTHORIZED** |
| **Focus/balestra weapon materialization** | 🔒 **NOT AUTHORIZED** |
| **T2-T5 Vuoto item materialization** | 🔒 **NOT AUTHORIZED** |
| **R18.3f-NC1** | 🔒 **HOLD** (mandatory pre-migration; not required for AFX1) |
| **Gate 11** | 🔒 **HOLD** |
| **Wave 1 (Monaco/Druido/Alchimista/Bardo/Negromante)** | 🔒 **HOLD** |
| **Cacciatore del Vuoto: LIVE / SELECTABLE** | 🔒 **NOT LIVE · NOT SELECTABLE** |

**Registry v3 dependency chain**:
1. AFX1 draft → PM verdict → AFX1 CLOSED
2. Registry v3 architecture gate (design-only, NOT AUTHORIZED ora)
3. `rec_classes` additive apply gate (con constraints F2-Q2)
4. `affix_pool_tag` backfill gate (con AFX1 vocabulary lock)
5. Item creation gate (T2-T5 Vuoto + successor)
6. Registry v3 apply gate

**NC1 dependency chain** (per class_slug migration + Hall runtime + Gate 11):
1. R18.3f-NC1 kickoff (post PM verdict dedicato)
2. Null cohort remediation planning
3. class_slug apply gate
4. Hall/Trial activation gate
5. Gate 11 kickoff

**Sequenza corretta**:
- AFX1 draft (this dispatch) → PM verdict → AFX1 CLOSED
- Successivi gate: nessun auto-start · nessun kickoff senza PM directive dedicata

---

## 🛑 EXPLICIT STOP FINALE · AFX1 DRAFT GENERATED · PENDING PM VALIDATION

Governance locks:
- `apply_authorized = false`
- `item_creation_authorized = false`
- `registry_v3_apply_authorized = false`
- `field_addition_authorized = false`
- `backfill_authorized = false`
- `affix_population_authorized = false`
- `db_write_count = 0`
- Sealed integrity 36/36 mantenuta durante AFX1
- lore_meta.py invariato
- Nessuna modifica backend/frontend/scripts/tests/OpenAPI/PRD
- RV3-EV/EV-F1/EV-F2 closure IMMUTATI
- Nessun nuovo sigillo aggiunto
- Nessun auto-start su NC1, Gate 11, Wave 1, Registry v3 apply, item creation

**Attendo verdict PM su AFX1 draft prima di qualsiasi ulteriore azione.**
