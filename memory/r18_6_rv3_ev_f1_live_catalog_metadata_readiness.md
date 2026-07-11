# R18.6.RV3-EV-F1 · Live Catalog Reconciliation & Additive Metadata Readiness

**Documento**: `r18_6_rv3_ev_f1_live_catalog_metadata_readiness.md`
**Regime**: READ-ONLY DISCOVERY · DOCUMENTAL ONLY · ITALIANO ONLY · **NOT FIELD ADDITION GATE**
**Parent**: R18.6.RV3-EV (CONDITIONAL HOLD) · R18.6.3 Cacciatore del Vuoto (ACTIVE-DESIGN-READY invariato)
**Governance**: `apply_authorized=false` · `no_field_addition=true` · `no_backfill=true` · `no_item_mutation=true`
**Sealed integrity**: 36/36 attesa · `lore_meta.py` = `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`

---

## 1 · Executive summary

EV-F1 determina se il catalogo live può supportare una validazione affidabile del pilot Cacciatore del Vuoto e definisce i metadati necessari SENZA modificare dati. Trigger: RV3-EV = VALIDATION PARTIAL · CONDITIONAL HOLD. Findings di RV3-EV accepted as current evidence. Pilot ACTIVE-DESIGN-READY invariato. Modifica solo: implementation dependency assessment · item reuse confidence · Registry v3 workload · metadata prerequisites.

## 2 · Governance

- **PM-locked**: EV-F1 draft in attesa PM.
- **NO field addition** · **NO backfill** · **NO item mutation** · **NO schema change** · **NO Registry apply**.
- Read-only enrichment simulation ammessa (design_only, `apply_authorized=false`).
- Sealed integrity 36/36 · `lore_meta.py` invariato · Pilot Cert + Manifest immutabili.

## 3 · Distinzione catalogo canonico vs live

**Separazione formale (LOCK)**:

| Layer | Descrizione | Count | Status |
|---|---|---|---|
| **R18.5 canonical design catalog** | Catalogo pianificato documentale (R18.5 phase A/B/C) | **1500 target** | **PRESERVED** (numero pianificato) |
| **Live materialized runtime catalog** | Collection `items` in Mongo | **178** | **INCOMPLETE OR PARTIAL** |
| **catalog_layer_mismatch** | Confermato | | **CONFIRMED** |

**LOCK**: **NON assumere** che `1500 - 178 = 1322 item mancanti` prima di riconciliazione per ID/versione/source. Il 1500 è baseline pianificato numerico. Il live 178 è materializzazione indipendente.

## 4 · Lineage del catalogo 1500

- Origine: documenti R18.5 Phase A/B/C (~40 file `/app/memory/r18_5_phase_*.md/.json`)
- Riferimento a "1500" ricorre **284 volte** nei file r18_5.
- Il `1500` rappresenta il **catalog target complessivo** in G5 EQUIP_DESIGN + Phase C item table drafting.
- **NON esiste** un file r18_5*.json che elenca 1500 item con id/slug fissi (verificato via scan JSON).
- Il canonical catalog `1500` è **numerico target design-lock**, non un manifest ID-to-item.

## 5 · Lineage del catalogo 178

- Origine: collection Mongo `items` (namespace `orbus_r16`).
- Popolamento: legacy da round R16 + reset1b + R18.reset1b hotfix + drafting Phase C parziale.
- **Nessun manifest sealed** collega direttamente i 178 live agli 1500 documentali.
- Item live hanno `id` UUID4 stabile + `slug` machine-name univoco (178 slug distinti).
- Timestamp `created_at`/`updated_at` mostrano popolamento incrementale nel tempo.

## 6 · Item ID overlap analysis

Scansione r18_5*.json per liste item con `id`/`slug`:
- **canonical_ids collected**: **0**
- **canonical_slugs collected**: **0**
- **live ids**: **178**
- **live slugs**: **178**
- **Overlap ids (live ∩ canonical)**: **0**
- **Overlap slugs (live ∩ canonical)**: **0**

**Conclusione**: nessun file R18.5 espone un item registry ID-based comparabile. La discrepanza 1500 vs 178 **non è quantificabile a livello ID** con la documentazione attuale. È una discrepanza **numerica pianificata**, non una lista di "item missing" con ID.

## 7 · Version/source analysis

- **Live** = versione runtime (Mongo `items` collection).
- **R18.5** = versione design planning (r18_5 files).
- **R18.5 Phase C0** (`r18_5_phase_c0_item_table_drafting_support.json` etc.) = contiene tabelle draft ma non ID list finale.
- **R18.5 Phase B1 design_lock** = lock design intent (non implementation).
- **R18.5 Phase E1 balance_remediation_patch** = balance patch documentale.
- **Nessun master registry** con versioning esplicito tra 1500 canonical e 178 live.

## 8 · Live materialization status

- Live 178 items = **~11.87% del target canonical 1500** (aritmetica pianificata, non ID-verified).
- Distribuzione live per rarity: Common ~63 · Uncommon ~49 · Rare ~49 · Epic ~14 · Legendary 3 (approssimazione dai count RV3-EV).
- Item con `lore_reviewed=True` = **178 / 178** (100% lore-reviewed).
- Item `is_active=True` = **178 / 178** (100% active).
- `affix_pool_tag` popolato = **0 / 178** (feature non materializzata a DB).

## 9 · Missing materialization analysis

- **Missing item count** = **NON QUANTIFICABILE PER ID** (nessuna lista canonical ID-based).
- **Missing item count numerico pianificato** ≈ 1500 - 178 = **1322** (SOLO se si assume che 1500 sia il target planning-lock).
- **Regola PM LOCK**: NON usare 1322 come "item mancanti" senza qualifier "planning-numeric-only". La discrepanza è a layer di planning target, non a layer di manifest.

## 10 · Schema live item

**Field union osservati su 50 samples items**:

`_id`, `affects_combat`, `affects_economy`, `affects_ranking`, `affix_pool_tag`, `agility_bonus`, `armor_tags`, `can_be_sold_for_gold`, `can_be_sold_for_real_money`, `class_tags`, `created_at`, `description`, `display_name_en`, `display_name_it`, `enchant_slots`, `endurance_bonus`, `faith_bonus`, `flavor_text_it`, `id`, `intellect_bonus`, `is_active`, `is_cosmetic`, `is_tradeable`, `item_binding_policy`, `item_type`, `level_required`, `lore_reviewed`, `lore_reviewed_at`, `lore_source`, `lore_tags`, `max_refinement`, `min_level`, `name`, `power_score`, `rarity`, `recommended_classes`, `required_adventurer_level`, `required_class_optional`, `role_tags`, `set_id`, `slot`, `slot_type`, `slug`, `spoiler_level`, `stat_tags`, `strength_bonus`, `updated_at`, `weapon_tags`

**Totale field distinct osservati: ~47** (union su 50 sample).

## 11 · Campi esistenti

**Field presenti in tutti/quasi tutti i 178**:
- Identity: `id`, `slug`, `name`, `display_name_en`, `display_name_it`, `description`, `flavor_text_it`
- Classification: `item_type`, `slot_type`, `rarity`, `item_binding_policy`
- Class binding: `class_tags` (list), `recommended_classes` (list), `required_class_optional`
- Level: `required_adventurer_level`, `level_required`, `min_level` (tripla ridondanza)
- Stats: `stat_tags` (list), `role_tags` (list), `power_score`
- Stat bonus: `intellect_bonus`, `strength_bonus`, `agility_bonus`, `endurance_bonus`, `faith_bonus`
- Armor family: `armor_tags` (list) ← ALIAS di `armor_type`
- Weapon family: `weapon_tags` (list) ← ALIAS di `weapon_family`
- Slot: `slot` E `slot_type` (duplicati)
- Set/enchant/refine: `set_id`, `enchant_slots`, `max_refinement`
- Lore: `lore_tags`, `lore_source`, `lore_reviewed`, `lore_reviewed_at`, `spoiler_level`
- Economy: `is_tradeable`, `can_be_sold_for_gold`, `can_be_sold_for_real_money`, `affects_economy`, `affects_ranking`, `affects_combat`
- Cosmetic: `is_cosmetic`
- Affix: `affix_pool_tag` (presente ma tutti None)
- Timestamps: `created_at`, `updated_at`

## 12 · Campi mancanti

**Field EV-Q6 hint (armor_type, weapon_family, tier, ilvl, affix_pool_tag) status**:

| Campo target | Presente | Alias esistente | Note |
|---|---|---|---|
| `armor_type` | ❌ | ✅ `armor_tags` | already available |
| `weapon_family` | ❌ | ✅ `weapon_tags` | already available |
| `tier` | ❌ | ⚠️ derivabile via `required_adventurer_level` + G5 mapping | non-field, derivable |
| `ilvl` | ❌ | ⚠️ proxy `power_score` + `rarity` + `level_required` | non-field, derivable conditional |
| `affix_pool_tag` | ✅ | (self) | field ESISTE ma vuoto (all None) → REQUIRES_FUTURE_BACKFILL |

**Nessun nuovo field è proposto in EV-F1** (regola EV-Q6).

## 13 · Alias esistenti

**Alias osservati live**:
- `armor_tags` (list) ↔ concept `armor_type` → **EXISTS_ALIAS**
- `weapon_tags` (list) ↔ concept `weapon_family` → **EXISTS_ALIAS**
- `slot` ↔ `slot_type` (duplicati; da normalizzare in gate futuro, non ora)
- `required_adventurer_level` ↔ `level_required` ↔ `min_level` (tripla ridondanza; da normalizzare)
- Class alignment: `class_tags` (list) ↔ `recommended_classes` (list) ↔ `required_class_optional` (single)
- Slot alias globali proposti: `trinket → accessory` · `belt → waist` · `cloak/cape → back`

**LOCK**: nessuna normalizzazione applicata in EV-F1 (design_only).

## 14 · Armor_type readiness

- **Verdict**: **`EXISTS_ALIAS`** via `armor_tags` (list).
- Discovery live: field `armor_tags` esiste in items schema. Contenuto atteso (design G2): `stoffa`, `cuoio`, `metallo` (heavy) etc.
- Verifica popolamento distinct (da eseguire in F1-followup): `db.items.distinct('armor_tags')` (read-only).
- **Nessuna field addition** richiesta. Suggerito documentare mapping alias.

## 15 · Weapon_family readiness

- **Verdict**: **`EXISTS_ALIAS`** via `weapon_tags` (list).
- Contenuto atteso (design G2 Cacciatore del Vuoto): `focus`, `balestra_arcana`, `pugnale_rituale`.
- Verifica popolamento distinct (da eseguire in F1-followup).
- **Nessuna field addition** richiesta. Suggerito documentare mapping alias.

## 16 · Tier readiness

- **Verdict**: **`DERIVABLE_HIGH_CONFIDENCE`**.
- Regola G5 EQUIP_DESIGN (Cacciatore del Vuoto § 1):
  - **T1 Aspirante** = levels 1-15
  - **T2 Cacciatore** = levels 16-30
  - **T3 Iniziato** = levels 31-45
  - **T4 Rituale** = levels 46-55
  - **T5 Vuoto** = levels 56-60
- Derivazione: `tier = f(required_adventurer_level)` con soglie sopra.
- **Confidence HIGH**: mapping deterministico, verificato in G5 sealed.
- **NON auto-apply runtime** (design_only).

## 17 · ILVL readiness

- **Verdict**: **`DERIVABLE_CONDITIONAL`**.
- ILVL non è field distinct live. Proxy via:
  - `power_score` (numeric)
  - `rarity` (5 valori)
  - `required_adventurer_level` (level buckets)
- Derivazione richiede formula esplicita: `ilvl = required_level + rarity_offset` (già suggerita in G5 formula LOCK: `min(max(required_level + rarity_offset, tier_min), 60)`).
- **Confidence CONDITIONAL**: dipende da rarity_offset ratifica PM.

## 18 · Affix_pool_tag readiness

- **Verdict**: **`REQUIRES_FUTURE_BACKFILL`**.
- Field ESISTE nel schema items (verificato: 178/178 items hanno il field).
- Contenuto: **`None` per tutti 178 items** (100% vuoto).
- Backfill richiede:
  - Definizione vocabolario affix_pool tags (design_only in EV-F1)
  - Schema validation rules
  - Compatibility mapping (per class · per tier · per rarity · per slot)
  - Null handling (item pre-affix rimane null · non forzare)
  - Versioning (affix_pool_tag_version field opzionale futuro)
- **NON popolare ora** (EV-Q8 LOCK).

## 19 · Derivabilità deterministica

- **Tier**: derivabile HIGH via G5 mapping level buckets.
- **ILVL**: derivabile CONDITIONAL via formula + PM ratifica.
- **Armor_type**: già presente via alias `armor_tags`.
- **Weapon_family**: già presente via alias `weapon_tags`.
- **Affix_pool_tag**: NON derivabile · richiede backfill design-driven.

## 20 · Valori non derivabili

- `affix_pool_tag` senza design catalog affix definito.
- `ilvl` senza rarity_offset PM-approved.
- `armor_type` sub-classification (heavy vs medium vs light) se `armor_tags` non contiene granularità fine.
- Item con `stat_tags` incompleto non deriva main_stat implicito.
- Item con `class_tags` empty (16 items live) non deriva class-affinity senza altre evidenze.

## 21 · Null handling

- `class_tags` empty (list vuota): 16 items live → categoria potenziale universal/PM_REVIEW.
- `affix_pool_tag = None`: 178/178 (100%).
- `set_id = None`: probabile per la maggioranza dei 178 (non-set items).
- `spoiler_level`: presente ma non contato distinct.
- **Regola LOCK**: `null` **NON auto-convertire** a default class/tier/slot. Rispetta regola R18.3f no-auto-derive.

## 22 · Conflict handling

**Conflitti schema live osservati**:
- `slot` E `slot_type` coesistono → possibile inconsistenza (source of truth non definita)
- `required_adventurer_level` + `level_required` + `min_level` → 3 field per level: quale è authoritative?
- `class_tags` vs `recommended_classes`: possibili valori diversi tra loro
- `class_tags` vs `required_class_optional`: possibili conflitti

**Handling**: no auto-resolution. Ogni conflict = verdict `PM_REVIEW`.

## 23 · Metadata source of truth

Proposta LOCK (design_only, ratifica PM richiesta in F1-Q):
- Slot canonico = `slot_type` (deprecare `slot`)
- Level canonico = `required_adventurer_level` (deprecare `level_required`, `min_level`)
- Class alignment source of truth = `class_tags` (list) · `recommended_classes` = suggerimento UX · `required_class_optional` = fallback constraint
- Armor family SoT = `armor_tags` (list)
- Weapon family SoT = `weapon_tags` (list)
- Affix pool SoT = `affix_pool_tag` (single string, versioned in futuro)
- **Nessuna migrazione applicata** in EV-F1.

## 24 · Additive schema proposal

Design_only · no application:

- Nessun nuovo campo necessario per: armor_type, weapon_family (alias esistenti).
- Nessun nuovo campo necessario per: tier, ilvl (derivabili).
- Necessari (futuri, non ora):
  - Popolamento `affix_pool_tag` post-vocabulary lock
  - Normalizzazione slot/level (deprecation graceful)
  - Opzionale: field `tier_snapshot` cache-only (deriving expensive), design_only
- **Zero apply · zero backfill · zero write**.

## 25 · Backward compatibility

- Alias esistenti (`armor_tags`, `weapon_tags`) preservano BC totale.
- Deprecation `slot` / `level_required` / `min_level`: gate futuro dedicato (BC-preserving dual-read).
- `affix_pool_tag` = None è baseline attuale → BC preserved.
- Nessun consumer legacy break durante EV-F1 (documento).

## 26 · Registry v2 preservation

- Collection `items` docs pre-EV-F1: **178**
- Collection `items` docs post-EV-F1: **178** ✅
- Documents modified/created/deleted: **0**
- Field added/modified: **0**
- **Catalog INVARIATO**.

## 27 · R18.5 preservation

- File R18.5 Phase A/B/C1/C2/C3/... = **NON TOCCATI**.
- Design catalog documentale 1500 (planning-lock) = **INVARIATO**.
- Nessuna scrittura su file `/app/memory/r18_5_*.json/.md` in EV-F1.

## 28 · Item identity preservation

- `id` UUID4 di ogni item live = **immutabile**.
- `slug` machine-name = **immutabile**.
- `name` / `display_name_it` / `display_name_en` = **immutabili**.
- Anti-P2W flag `can_be_sold_for_real_money = false` (design LOCK · verificare per-item in gate futuro).

## 29 · Read-only enrichment simulation

Metadata view **simulata** (design_only · `apply_authorized=false`):

Per un item live esempio, il metadata view proposto contiene:
```
{
  "item_id": "<uuid>",
  "slug": "<slug>",
  "derived_tier": { "value": "T1", "source": "G5_mapping", "confidence": "HIGH", "derivation_rule": "required_adventurer_level in [1,15]", "conflict_status": "none", "apply_authorized": false },
  "derived_ilvl": { "value": <int>, "source": "formula_g5", "confidence": "CONDITIONAL", "derivation_rule": "min(max(required_level + rarity_offset, tier_min), 60)", "conflict_status": "rarity_offset_pm_ratify_required", "apply_authorized": false },
  "armor_type_alias": { "value": "<from armor_tags>", "source": "existing_alias", "confidence": "HIGH", "derivation_rule": "read armor_tags list", "conflict_status": "none", "apply_authorized": false },
  "weapon_family_alias": { "value": "<from weapon_tags>", "source": "existing_alias", "confidence": "HIGH", "derivation_rule": "read weapon_tags list", "conflict_status": "none", "apply_authorized": false },
  "affix_pool_tag_status": { "value": null, "source": "field_present_null", "confidence": "N/A", "derivation_rule": "not_derivable", "conflict_status": "empty_all_items", "apply_authorized": false }
}
```

**NO DB write · NO item mutation · NO Registry write · NO CSV apply · NO generated item rows.**

## 30 · 49 PM_REVIEW preparation

**Metadata gap analysis** per i 49 items PM_REVIEW (soft binding + intellect stat + not warlock class_tag):

Priority tier per review (design_only):
1. **Priority 1**: items con `class_tags` overlap con classi caster (mage/necromancer/priest/bard/druid) → review overlap identità
2. **Priority 2**: items con `role_tags: dps_caster` o `support` → funzionalità Vuoto-adjacent
3. **Priority 3**: items con `lore_tags` alignment (vuoto/oblio/veglie/memoria/filo-spezzato) → identità classe
4. **Priority 4**: items rimanenti → verifica per-item stat_tags secondary

Nessun review record-by-record ora (deferred fino EV-F1 completion → EV-F2 dedicato futuro).

## 31 · 6 lore-item audit

**Per-item verdict (5 verdict ammessi)**:

| # | slug | display_it | slot/type | rarity | L | class_tags | stat_tags | lore | binding | **Verdict** |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `drake_slayer_helm` | Elmo Cacciadrago | helm/armor | Legendary | 12 | warrior/paladin/berserker | STR, END | oblio, vuoto | hard | **IDENTITY_CONFLICT** (STR class, non caster) |
| 2 | `drake_slayer_chest` | Corazza Cacciadrago | chest/armor | Legendary | 12 | warrior/paladin/berserker | STR, END | oblio, vuoto | hard | **IDENTITY_CONFLICT** |
| 3 | `drake_slayer_blade` | Lama Cacciadrago | weapon_main/weapon | Legendary | 12 | warrior/paladin/berserker/rogue/ranger/assassin | STR, AGI | oblio, vuoto | hard | **IDENTITY_CONFLICT** (melee STR/AGI, no int) |
| 4 | `arcane_adept_orb` | Orbe del Maestro Arcano | amulet/accessory | Legendary | 12 | mage/necromancer/bard | **intellect** | oblio, vuoto | soft | **PM_REVIEW** (int caster ma no warlock) |
| 5 | `goblin_hunter_ring` | Anello del Cacciatore di Goblin | ring/accessory | Legendary | 12 | warrior/paladin/berserker/rogue/ranger/assassin | STR, AGI | oblio, vuoto | soft | **IDENTITY_CONFLICT** |
| 6 | `voidpiercer-bow` | Arco Trafittore del Vuoto | weapon/weapon | Epic | 8 | rogue/ranger/assassin/monk/mage/necromancer | AGI, **intellect** | vuoto, filo-spezzato | soft | **PM_REVIEW** (nome "Vuoto" ma weapon ranger/assassin dominant) |

**Sintesi**:
- `LORE_COMPATIBLE_REUSE_CANDIDATE`: **0**
- `LORE_ONLY_NOT_EQUIP_COMPATIBLE`: 0 (tutti equip)
- `IDENTITY_CONFLICT`: **4** (drake_slayer_helm/chest/blade + goblin_hunter_ring)
- `INSUFFICIENT_METADATA`: 0 (tutti hanno metadata sufficienti)
- `PM_REVIEW`: **2** (arcane_adept_orb + voidpiercer-bow)

**Conclusione EV-Q9**: la presenza di lore_tags `vuoto` o `oblio` **NON garantisce** compatibilità Vuoto. Su 6 items: 0 REUSE_VALID, 4 IDENTITY_CONFLICT, 2 PM_REVIEW. Identity Vuoto sotto-materializzata live (confermato RV3-EV finding).

## 32 · T5 live coverage assessment

**LEVEL/TIER MAPPING VERIFICATO da G5**:
- T5 Vuoto = **levels 56-60** (NON L12)
- L12 = **T1 Aspirante** (levels 1-15)

**Correzione finding RV3-EV precedente**: "1 item Int L12 in T5" era ERRATO. L12 è T1.

**Live coverage per tier reale**:

| Tier G5 | Level range | Items live tot | Items intellect live | Items warlock+intellect live |
|---|---|---|---|---|
| **T1 Aspirante** | 1-15 | 178 (100%) | 72 (100%) | 18 (100%) |
| **T2 Cacciatore** | 16-30 | **0** | **0** | **0** |
| **T3 Iniziato** | 31-45 | **0** | **0** | **0** |
| **T4 Rituale** | 46-55 | **0** | **0** | **0** |
| **T5 Vuoto** | 56-60 | **0** | **0** | **0** |

**Finding CRITICO**: il catalog live è **completamente in T1 (levels 1-15)**. Tutti i tier T2-T5 sono **0 items live**. Il game è materialmente in early progression (max level live L12).

**Valid T5 live candidates**: **0**
**Conditional T5 candidates**: **0**
**Missing T5 armor**: intero set (7 slot × 2+ rarity + Legendary)
**Missing T5 weapon**: focus + balestra_arcana + pugnale_rituale + Legendary utility_unique
**Missing T5 universal slots**: back, ring, amulet (universal T5)
**Future T5 item estimate**: ~26 items (T5 budget baseline da G5 §Item Budget)

## 33 · Missing-slot assessment

**Slot canonici globali (14 + 3 alias)** confermati da EV-Q7:

Slot canonici (14): `head`, `neck`, `shoulders`, `chest`, `back`, `hands`, `wrist`, `waist`, `legs`, `feet`, `main_hand`, `off_hand`, `ring`, `accessory`.
Alias (3): `trinket → accessory`, `belt → waist`, `cloak/cape → back`.
**Nessun 15° slot.**

**Live slot coverage vs canonical 14**:

| Slot canonico | Live count | Status |
|---|---|---|
| `head` | 1 (helm) | UNDERPOPULATED |
| `neck` | 5 (amulet) | LOW |
| `shoulders` | 0 | **MISSING** |
| `chest` | 3 (chest) + 42 (armor generic) | AGGREGATED_NON_DISTINCT |
| `back` | 0 | **MISSING** |
| `hands` | 0 | **MISSING** |
| `wrist` | 0 | **MISSING** |
| `waist` | 0 | **MISSING** |
| `legs` | 0 | **MISSING** |
| `feet` | 0 | **MISSING** |
| `main_hand` | 7 (weapon_main) | LOW |
| `off_hand` | 0 (nessuno distinct) | **MISSING** |
| `ring` | 1 | UNDERPOPULATED |
| `accessory` | 42 | ADEQUATE_CATCH_ALL |

**Missing/underpopulated**: 9 slot su 14 (64%).

## 34 · Armor coverage assessment

Live armor items (item_type=armor):
- slot_type distribution: `armor` (42) · `chest` (3) · `helm` (1)
- Missing: shoulders, back, hands, wrist, waist, legs, feet
- Il slot generico `armor` (42 items) è un **catch-all** non granulare (probabile che alcuni siano di fatto chest/legs/etc ma non tagged)
- Armor coverage granulare: **inadeguata per Vuoto endgame**

## 35 · Weapon coverage assessment

Live weapon items:
- slot_type distribution: `weapon` (54) · `weapon_main` (7)
- Missing: `off_hand` distinct
- `weapon_family` alias (`weapon_tags`) non ancora analizzato per contenuto distinct
- Weapon coverage Vuoto (focus/balestra_arcana/pugnale_rituale): non discriminabile live senza analisi `weapon_tags`

## 36 · Future item gap estimate

**Rivisto con priorità EV-Q4 rivista**:

Priority 1 (T5 endgame minimum viability): **~26 items** (armor 14 + weapon 6 + accessory 6 + Legendary 2 utility_unique)
Priority 2 (armor core stoffa+cuoio T1-T4): **~28 items** (7 slot × 4 tier × ~1 armor_type = 28)
Priority 3 (weapon core focus+balestra+pugnale T1-T4): **~18 items** (3 famiglie × 4 tier × ~1.5 rarity)
Priority 4 (slot mancanti head/back/ring/shoulders/hands/wrist/waist/legs/feet/off_hand): **~50-70 items** (9 slot × T1-T5 × rarity)
Priority 5 (T1-T4 progression complete): **~40-50 items**
Priority 6 (affix e identità specifica Vuoto): **~15-25 items** identità Vuoto

**Totale futuro stimato (design_only, NOT AUTHORIZED)**: **~180-220 items nuovi** per raggiungere pieno catalog design R18.5 (1500 target).

Envelope Vuoto-specifico 110-130 rimane confermato come subset del totale futuro.

## 37 · Implementation dependency matrix

Sequenza (design_only · nomi tentativi · no auto-authorization):

```
1. R18.3f CLOSED ✅ (done)
2. R18.3f-NC1 Null Conflict Remediation Planning (HOLD)
3. R18.6.RV3-EV CONDITIONAL HOLD (this dispatch context)
4. R18.6.RV3-EV-F1 (this document · pending PM)
5. [tentative name] R18.6.RV3-EV-F2 "PM_REVIEW record-by-record" (HOLD)
6. [tentative name] R18.6.RV3-Additive-Metadata gate (armor_type/weapon_family alias documentation + tier/ilvl derivation ratification + affix_pool_tag vocabulary) (HOLD)
7. [tentative name] R18.6.RV3-Field-Deprecation gate (slot vs slot_type · level tripla ridondanza normalization) (HOLD)
8. R18.6.RV3 Registry v3 apply (HOLD)
9. R18.6.RV3-EV close (HOLD)
10. R18.3f-NC1 close (HOLD)
11. R18.6.RB1 Rite of Rebirth (HOLD)
12. Gate 11 (HOLD · 14 P residue)
13. Wave 1 kickoff (HOLD)
```

**Nessuna auto-authorization tra gate successivi**.

## 38 · Migration/backfill prerequisites

Prerequisiti futuri (design_only · non applicati):
- Dry-run readiness (già ratificato in R18.3f)
- Snapshot pre-apply (R18.3f closure)
- Idempotency (R18.3f)
- Rollback strategy (R18.3f)
- Audit trail (R18.3f)
- Feature flag 2-level (R18.3f R3f-Q6)
- Anti-P2W audit pre + post (EV-Q10)
- Metadata vocabulary lock (affix_pool_tag) · **prerequisito EV-F1 successor**

## 39 · Test requirements

Test futuri richiesti (design_only, NOT AUTHORIZED):
- Sealed integrity 36/36 pre e post ogni apply
- Item ID uniqueness check
- Item slug uniqueness check
- Class_tags ↔ recommended_classes coherence check
- Level (required_adventurer_level) tier mapping validation
- Anti-P2W `can_be_sold_for_real_money=false` enforcement check
- Affix_pool_tag vocabulary validation post-backfill
- **NON creare test file ora** (regola vincoli EV-F1).

## 40 · Risk register EV-F1

| ID | Severity | Rischio | Mitigation |
|---|---|---|---|
| **F1-R1** | HIGH | Assunzione "1322 item mancanti" errata (nessun manifest ID) | Separazione formale canonical planning vs live materialized · LOCK "non quantificabile per ID" |
| **F1-R2** | HIGH | Tier mapping erroneo (L12 ≠ T5, è T1) · propagation errore RV3-EV precedente | Correzione documentale in §32 · G5 mapping ratificato |
| **F1-R3** | HIGH | Live catalog completamente in T1 (0 items T2-T5) · classe non giocabile mid/end-game | Requires ~180-220 items nuovi per full catalog · design_only |
| **F1-R4** | MEDIUM | Tripla ridondanza level field (required_adventurer_level/level_required/min_level) | Normalization gate futuro dedicato |
| **F1-R5** | MEDIUM | Duplicazione slot/slot_type · SoT ambiguo | Deprecation `slot` in gate futuro · BC preserved |
| **F1-R6** | MEDIUM | `affix_pool_tag` = None 178/178 · feature non materializzata | Backfill dopo vocabulary lock design_only |
| **F1-R7** | LOW | 6 lore-vuoto items: 4 IDENTITY_CONFLICT, 2 PM_REVIEW · identity Vuoto ~zero live | Registry v3 additive item generation futuro |
| **F1-R8** | MEDIUM | `class_tags` vs `recommended_classes` potenzialmente inconsistente per item | Verifica per-item in F2 futuro |
| **F1-R9** | HIGH | Assumption che alias esistenti (armor_tags, weapon_tags) siano popolati con vocabolario G2-coerente | Verifica distinct values in F1 follow-up |
| **F1-R10** | LOW | Registry v3 apply potrebbe introdurre duplicati slug se nome conflict | Slug uniqueness enforcement pre-apply |

## 41 · PM open questions F1-Q1..F1-Q10

- **F1-Q1** — Alias `armor_tags` è authoritative source per `armor_type` o serve rename graceful? *Recommendation*: alias-first no-rename (design_only, mapping documentato).
- **F1-Q2** — Alias `weapon_tags` authoritative source per `weapon_family`? *Recommendation*: alias-first no-rename.
- **F1-Q3** — Deprecation `slot` vs `slot_type` timing? *Recommendation*: gate futuro dedicato dopo affix_pool_tag lock.
- **F1-Q4** — Normalization triplo level field (`required_adventurer_level` / `level_required` / `min_level`) SoT? *Recommendation*: SoT = `required_adventurer_level` · deprecate altri in gate dedicato.
- **F1-Q5** — `rarity_offset` per ILVL formula: valori PM-ratified? *Recommendation*: Common=0 · Uncommon=+1 · Rare=+2 · Epic=+3 · Legendary=+5 (proposta design G5 · PM ratify richiesto).
- **F1-Q6** — Affix pool tag vocabulary: quale set base per T1-T5? *Recommendation*: vocabulary lock in gate dedicato (design_only) prima di backfill.
- **F1-Q7** — Live catalog T1-only (0 items T2-T5): confermare che roadmap dev è materializzazione progressive per tier? *Recommendation*: yes, materialization progressive T1→T5.
- **F1-Q8** — `voidpiercer-bow` PM_REVIEW: warlock class_tag mancante ma nome/lore "Vuoto": aggiungere warlock a class_tags o keep out? *Recommendation*: keep out (item design pre-Vuoto pilot, evitare retro-branding).
- **F1-Q9** — `arcane_adept_orb` PM_REVIEW: aggiungere warlock/cacciatore_del_vuoto a class_tags? *Recommendation*: valutare in F2 gate dedicato dopo Registry v3 field additive.
- **F1-Q10** — `can_be_sold_for_real_money=false` audit per-item: 178 items live tutti compliant? *Recommendation*: verificare distinct in F1 follow-up (probabile 100% false, ma da confermare).

## 42 · GO/HOLD recommendation RV3-EV

| Componente | Verdict |
|---|---|
| RV3-EV closure | 🔒 **HOLD** (attende PM review EV-F1) |
| EV-F1 draft documentale | ✅ **DRAFT_GENERATED** (this document) |
| EV-F1 PM review | 🕐 **PENDING** |
| Registry v3 additive metadata gate | 🔒 **HOLD** (post EV-F1) |
| Registry v3 apply | 🔒 **HOLD** |
| Field addition (nuovi campi) | 🔒 **NOT AUTHORIZED** (alias sufficienti) |
| Field deprecation (slot/level) | 🔒 **HOLD** (gate dedicato futuro) |
| Affix pool tag backfill | 🔒 **HOLD** (vocabulary lock prerequisito) |
| Item creation Registry v3 (~180-220 items futuri) | 🔒 **HOLD** (NOT AUTHORIZED) |
| PM_REVIEW 49 items record-by-record | 🔒 **HOLD** (F2 gate dedicato futuro) |
| 6 lore Vuoto/Oblio review | ✅ **COMPLETED** in this document (0 REUSE, 4 IDENTITY_CONFLICT, 2 PM_REVIEW) |
| Gate 11 | 🔒 **NOT AUTHORIZED** |
| Wave 1 kickoff | 🔒 **HOLD** |

**Recommendation al PM**: acquisire EV-F1 come corrective/additive audit di RV3-EV · confermare separazione canonical vs live · confermare tier mapping L12=T1 (non T5) · confermare 0 REUSE tra 6 lore Vuoto items · autorizzare (in gate dedicato futuro) additive metadata documentation + vocabulary lock affix_pool_tag come pre-requisiti Registry v3.

---

## 🛑 STOP FINALE · EV-F1 DRAFT GENERATO · PENDING PM

- Catalog lineage separato: canonical 1500 (planning-numeric) vs live 178 (materialized) · **NON quantificabile per ID**
- Field readiness verdict: armor_type EXISTS_ALIAS · weapon_family EXISTS_ALIAS · tier DERIVABLE_HIGH · ilvl DERIVABLE_CONDITIONAL · affix_pool_tag REQUIRES_FUTURE_BACKFILL
- Slot canonici 14+3 alias confermati (nessun 15° slot)
- 6 lore Vuoto/Oblio audit: 0 REUSE · 4 IDENTITY_CONFLICT · 2 PM_REVIEW
- **Correzione critica**: L12 ≠ T5. L12 = T1 (G5 mapping ratificato)
- Live catalog completamente in T1 (0 items T2-T5) · gap ~180-220 items futuri
- Registry v2 R18.5 catalog **INVARIATO** · 178 items live 0 modificati
- Sealed integrity 36/36 attesa · lore_meta invariato · Pilot Certificate + Manifest immutati
- R18.3f originali + R1 audit + Closure Report + Closure Manifest + RV3-EV = IMMUTATI

**Attendo PM directive su EV-F1 (CLOSE integrativo / REWORK / HOLD) prima di ogni ulteriore azione.**

- `apply_authorized = false`
- `no_field_addition = true`
- `no_backfill = true`
- `no_item_creation = true`
- `no_registry_apply = true`
- `class_slug write count = 0`
- `db writes = 0`
- Nessuna migration · nessun Gate 11 · nessun Wave 1 kickoff senza PM directive esplicita
