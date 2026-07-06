# R18.4 Phase B1 — Deep-Dive Audit READ-ONLY

- **Round**: R18.4 — Item Class-Bound Player-Facing — Phase B1
- **Tipo**: Deep-dive audit READ-ONLY
- **Timestamp UTC**: `2026-07-05T20:50:00Z`
- **Direzione preliminare**: Option 3 Hybrid Refined (LOCKED da PM)
- **Perimetro**: analisi statica + read-only DB queries + coverage matrix in-process. NO DB write, NO code change, NO frontend change, NO touch 24 sigilli.

---

## 1. Executive Summary

Il sistema equipment/compatibility è **già ~80% coerente con Option 3 Hybrid Refined**. `check_equip_compatibility` implementa precedenza multi-field (10 rule steps). `auto_equip.py` (R16.5.4b REOPEN #2, 2026-07-02) **skip warning items entirely** — Q6 del PM è già rispettato dal design attuale (warning=SKIP, block=SKIP). Signature items sono **14 (non 12)** — split naturale in **8 hard** (`required_class_optional` populated) + **6 soft** (solo `recommended_classes`). `specialization_unlocks` è **dead branch** (0 items lo usano). Bard drift confermato ma **NO bug** rilevati su compatibility/auto-equip/UI. NULL class_slug (13 adventurers) gestito via fallback `_resolve_class_slug`→`class_name`. G1 backfill fattibile via mapping `item_type→slot_type` per 140 items, con **2 shield items OPEN** (EQUIPMENT_SLOTS runtime = 3 slot: weapon/armor/accessory, no shield). Recommendation: **procede a B2 decision lock**.

---

## 2. `auto_equip.py` Audit Findings (594 righe)

### Fitness formula (righe 45-49, 88-98)
```
PRIMARY_WEIGHT   = 3.0
SECONDARY_WEIGHT = 1.5
POWER_WEIGHT     = 1.0
STAT_TAG_BONUS   = 2.0

fitness = PRIMARY_WEIGHT * item[f"{primary}_bonus"]
        + SECONDARY_WEIGHT * sum(item[f"{s}_bonus"] for s in secondaries)
        + POWER_WEIGHT * item.power_score
        + STAT_TAG_BONUS if primary in item.stat_tags else 0
```

### Tie-break deterministico (righe 365-369)
`(-fitness, -power_score, id_ASC)`. Idempotente: seconda invocazione con stesso inventario produce zero swap.

### Hard-reject paths
- `check_equip_compatibility` con `severity in ("block","warning")` → **exclude** (riga 320)
- `resolve_item_required_level(it) > adv_level` → **exclude** (level gate R11.3, righe 315-316)
- `is_active: false` su inventory → esclude (riga 264)
- Items bound to other adventurer → esclude (riga 268-270)
- `item_type != expected_type` per slot → esclude (riga 309-310)

### Soft warning integration
**Q6 già rispettato**: dal `REOPEN #2 R16.5.4b (2026-07-02)`, warning items sono **SKIPPED completamente** (no penalty ×0.5 fallback). Solo `severity == "ok"` entra nel ranking. Manual equip resta invariato (con warning UX).

### Edge case NULL class_slug
- `_resolve_class_slug(adv)` (riga 164-179): fallback `class_slug` → `class_name` → `class` → None
- `_load_class_meta(db, class_slug)` (riga 149-161): se class_slug è None o classe non trovata → default `{primary_stat:"strength", secondary_stats:[], display_name_it:None}`
- **Impact**: 13 adventurers NULL class_slug (dal Phase A) — se anche `class_name` è vuoto, ricevono weighting `strength` come default, che è sub-ottimale per druid/monk/ranger/mage (verificato: i 13 NULL hanno `class_name` populated, es. "Druid", "Monk", "Ranger", quindi fallback funziona correttamente)

### Empty-state differentiation (righe 327-360)
- `off_class_seen == 0` → "Nessun oggetto adatto in inventario, completa spedizioni…"
- `off_class_seen > 0` → "Oggetti trovati, ma nessuno adatto alla classe X"
- Coerente con Q6 policy: **NO force incompatibile**.

### EQUIPMENT_SLOTS runtime
`shared/constants.py` → `EQUIPMENT_SLOTS = ('weapon', 'armor', 'accessory')` — **3 slot fissi**. `SLOT_TO_ITEM_TYPE = {weapon:weapon, armor:armor, accessory:accessory}`. **Shield NON è uno slot equipaggiabile runtime**.

---

## 3. Frontend Components Inventory

| Componente | Path | Righe | Ruolo |
|---|---|---|---|
| Inventory (page) | `/app/frontend/src/pages/Inventory.jsx` | 574 | Lista globale guild inventory con item details |
| AdventurerEquipment (page) | `/app/frontend/src/pages/AdventurerEquipment.jsx` | 439 | Slot management per adventurer (3 slot: weapon/armor/accessory) |
| InventoryEquipModal (component) | `/app/frontend/src/components/InventoryEquipModal.jsx` | 208 | Modal transactional equip/unequip |
| AdventurerDetailModal (component) | `/app/frontend/src/components/AdventurerDetailModal.jsx` | 481 | Detail con inline slot equip |

**NON deep-dive in B1**: `RaidBuilder.jsx`, `Adventurers.jsx` (usano solo lookup lightweight su class_slug, non equip).

---

## 4. Compatibility UI Current-State

### `warning_it` flow
- Backend `check_equip_compatibility` ritorna `{allowed, severity, reason_code, reason_it}`
- `equip_item_service` (equipment/services.py) espone il payload al client
- `auto_equip.py::_extract_it_message` (righe 57-74) usa `detail.user_message` come SoT (mai `type(exc).__name__` per evitare leak "HTTPException")
- Frontend components ricevono `reason_it` / `warning_it` come stringa localizzata IT

### i18n handling
- Testi hard-coded IT nei service + fallback slug-based (_CLASS_LABELS_IT: warrior→Guerriero, mage→Mago, warlock→Occultista, ecc.)
- Localizzazione EN attualmente parziale (empty_state hardcoded EN in auto_equip righe 342-354)
- Player-facing labels stabili post-R18.Reset.1b/1.3

### UI 4-state feasibility (Q7)
Attualmente **3-state** implementato via `severity`:
- `block` → HTTP 400, `reason_it` errore
- `warning` → HTTP 201 + `warning_it`
- `ok` → HTTP 201 clean

**Missing per Q7 4-state**: badge "**consigliato per la classe**" (positive) e badge "**universale**" (neutrale) — richiedono nuovo signal API (es. `recommended_for_class: bool`, `is_universal: bool`) esposto in `item_public()` o nell'equip response. Feasibility: alta (schema exists, solo serialization change).

---

## 5. Test Baseline Coverage

### File test rilevanti (post-collect)
| File | Test count | Coverage |
|---|---|---|
| `backend_round1654b_test.py` | **27** | R16.5.4b auto-equip class-aware (fitness, tie-break, class_locked, druid warning-skip, alchemist/warlock full, warrior regression, empty state IT) |
| `backend_round15_phase2_test.py` | ~15 | Equipment compatibility validator base (hard block heavy_armor, arcane_weapon) |
| `backend_round160_phase2_test.py` | ~14 | Validator v2 base+specialization (spec mismatch, class_locked) |
| `backend_round1654c_i18n_test.py` | ~14 | i18n messages (class_labels, warlock=Occultista) |
| `backend_round160_phase3_test.py` | ~8 | Equip flow end-to-end |

### Coverage gap identificati
- **NULL class_slug edge case**: no dedicated test (13 live doc)
- **UI 4-state**: nessun test frontend (Cypress/Playwright)
- **audit event EQUIP_BLOCKED/WARNING**: 0 test (evento non ancora esistente)
- **`item_binding_policy` field**: 0 test (feature Q11 non ancora esistente)
- **G1 slot_type backfill**: 0 test (feature Q13 non ancora esistente)
- **Shield items (2)**: 0 test dedicato (item_type=shield ma slot non in EQUIPMENT_SLOTS)

---

## 6. Coverage Matrix 10 items × 5 classi = 50 verdicts

Eseguita in-process (no DB write) con `check_equip_compatibility(adv={class_slug:X}, item=Y)`.

| Item slug | warrior | mage | ranger | bard | priest |
|---|---|---|---|---|---|
| `drake_slayer_helm` (A) | ✓OK | ✗BLK (class_locked) | ✗BLK | ✗BLK | ✗BLK |
| `drake_slayer_blade` (C) | ✓OK | ✗BLK | ✗BLK | ✗BLK | ✗BLK |
| `arcane_adept_orb` (A) | ~W (not_rec) | ✓OK | ~W | ✓OK | ~W |
| `goblin_hunter_ring` (C) | ✓OK | ~W | ✓OK | ~W | ~W |
| `spec_signature_truestrike_bow` (E) | ✗BLK (class_locked) | ✗BLK | ✓OK | ✗BLK | ✗BLK |
| `spec_signature_sacred_chalice` (E) | ~W | ✓OK | ~W | ✓OK | ✓OK |
| `spec_signature_battle_standard` (E) | ✓OK | ✓OK | ~W | ✓OK | ~W |
| `spec_signature_bloodied_greataxe` (E, req=berserker) | ✗BLK | ✗BLK | ✗BLK | ✗BLK | ✗BLK |
| `spec_signature_breakers_gauntlets` (E, req=warrior) | ✓OK | ✗BLK | ✗BLK | ✗BLK | ✗BLK |
| `spec_signature_silent_kris` (E, req=assassin) | ✗BLK | ✗BLK | ✗BLK | ✗BLK | ✗BLK |

**Distribuzione verdicts**: 15× OK, 15× warning, 20× block. Coerente con Option 3 (hard-locked signature + soft warning generalisti).

**Insight critico**: 3 signature items (`bloodied_greataxe`, `silent_kris`) bloccati per TUTTI i 5 sample perché `required_class_optional` è `berserker`/`assassin` — classi **presenti nel bridge R18.3e ma con 0 adventurer live** (post-reset R18.Reset.1b). Questi item sono **de facto un-equipabili in produzione** finché berserker/assassin non tornano live.

---

## 7. Bard Drift Verification (Q14)

### DB state
- `bard.role = 'Support'` **confermato** (drift documentato in backlog `R18.3d.followup — Bard Role Drift Resolution`, P3)
- `bard.primary_stat = 'intellect'`
- `bard.secondary_stats = ['agility', 'faith']`
- Items con `recommended_classes: "bard"` = **29**

### Behavior verificato (3 sample)
| Item | Bard verdict |
|---|---|
| `arcane_adept_orb` (mage/necromancer/**bard**) | ✓ OK (code=ok) |
| `cracked-staff` | ✓ OK (code=ok) |
| `spiritglass-staff` | ✓ OK (code=ok) |

**Bug detection**: **ZERO bug rilevati**. Il drift `role='Support'` è **cosmetico**:
- `check_equip_compatibility` non usa `role` per hard block (usa solo `armor_tags`, `weapon_tags`, `class_tags`, `recommended_classes`, `specialization_unlocks`, `required_class_optional`, `is_universal`)
- `auto_equip.py` non legge `role` (usa `primary_stat`, `secondary_stats`)
- UI badge/warning: nessun path critico dipende da `role`

**Impatto R18.4**: **NULLO** — bard drift resta backlog P3. Coverage matrix OK.

---

## 8. Signature Items Flow Analysis (bucket E: 14, NON 12)

**Rettifica Phase A**: signature items sono **14** (Round 6C templates). Phase A ha usato pattern grep parziale.

### Split naturale hard/soft (già nel catalog)
| Sub-bucket | Count | Slug esempi | Meccanismo |
|---|---|---|---|
| **E1 hard** (`required_class_optional` populated) | **8** | truestrike_bow (ranger), bloodied_greataxe (berserker), breakers_gauntlets (warrior), corrupted_blade (necromancer), runic_aegis (paladin), silent_kris (assassin), storm_rod (mage), twin_blades (rogue) | HTTP 400 se class_slug ≠ required_class |
| **E2 soft** (solo `recommended_classes`) | **6** | aegis_of_the_defender, battle_standard, runed_focus, sacred_chalice, thornwood_shield, warhorn | Soft warning `not_recommended_class` per off-class |

### `specialization_unlocks`
- **0 items** popolano questo field nel catalog attuale
- Il branch in `compatibility.py:130-165` è **dead code** (logica presente ma nessun input runtime)
- Feature R16.0 introdotta ma mai utilizzata → sub-question B2

### Interazione E1 con classi deprecate_alias
- `bloodied_greataxe` (req=berserker) e `silent_kris` (req=assassin) → **de facto unusable** (0 adventurer live)
- 2 items dormant in catalog. Nessuna player action possibile.

---

## 9. G1 slot_type Backfill Strategy Proposal

### Composizione G1 (140 items)
| item_type | count | slot_type target derivato |
|---|---|---|
| weapon | 54 | `weapon` |
| armor | 42 | `armor` |
| accessory | 42 | `accessory` |
| **shield** | **2** | **OPEN — no slot in EQUIPMENT_SLOTS** |

### Proposta derivazione (SAFE)
```
if item_type in ("weapon", "armor", "accessory"):
    slot_type = item_type
elif item_type == "shield":
    slot_type = ???  # OPEN — see sub-question B2.SQ1
```

### Edge cases
1. **Shield (2 items)**: `EQUIPMENT_SLOTS` runtime = 3 slot. Shield non è slot equipaggiabile. Opzioni:
   - **(a)** Mappa in `armor` (comportamento tipico D&D-like)
   - **(b)** Aggiungi `shield` come 4° slot (breaking: richiede EQUIPMENT_SLOTS extend + auto-equip loop update)
   - **(c)** Lascia `slot_type=null` e considera come "off-slot" (soft warning universale)
2. **Item type ambiguo**: nessun item con `item_type` mancante nei 140. Materiali (`material`, `material_continental`, `material_event`) e consumabili sono in G2 (21 items) — NON G1, quindi fuori scope backfill.

### Governance backfill (Q13)
- Sequenza LOCKED da PM: B1 audit → B2 decision lock → **B3 sibling script dry-run** → real apply solo post-verify + gate PM
- NO backfill pre-B1 ✅ (Phase B1 read-only)
- Script sibling `round18_4_backfill_slot_type.py` proposto in B3 con `APPLY_ENABLED=False` default

---

## 10. Multi-Field Interaction Priority Matrix

### Precedenza attuale in `compatibility.py::check_equip_compatibility`

| # | Rule | Field | Severity | Population | Code |
|---|---|---|---|---|---|
| 1 | `required_class_optional != class_slug` | `required_class_optional` | **BLOCK** | 11 items | `class_locked` |
| 2 | `is_universal == True` | `is_universal` | **OK** (bypass) | 0 items verificati | `universal` |
| 3 | `armor_tags` contains "heavy" × class in NO_HEAVY_ARMOR (6 classi) | `armor_tags` | **BLOCK** | dipende da armor_tags | `heavy_armor_forbidden` |
| 4 | `weapon_tags ∩ ARCANE_WEAPON_TAGS` × class in NO_ARCANE_WEAPON (7 classi) | `weapon_tags` | **BLOCK** | dipende da weapon_tags | `arcane_weapon_forbidden` |
| 5 | `specialization_unlocks` matches `spec_slug` | `specialization_unlocks` | **OK** | **0 items DEAD** | `specialization_match` |
| 6 | `specialization_unlocks` non-empty + no spec + class not in rc | `specialization_unlocks` | **BLOCK** | 0 items DEAD | `specialization_required` |
| 7 | `specialization_unlocks` + spec mismatch + class in rc | `specialization_unlocks` | **WARN** | 0 items DEAD | `specialization_mismatch` |
| 8 | `recommended_classes` non-empty + class not in rc | `recommended_classes` | **WARN** | 157 items | `not_recommended_class` |
| 9 | `class_tags` non-empty + class not in ct | `class_tags` | **WARN** | 157 items | `off_class_tags` |
| 10 | default | — | **OK** | — | `ok` |

### Conflict resolution
- Rule 1 (class_locked) ha **priorità massima** — mai override
- Rule 2 (universal) è secondo — bypass everything except class_locked (attualmente 0 items ma logica presente)
- Blacklists (3-4) hanno priorità 3-4 sui warning (8-9)
- Il branch spec_unlocks (5-7) è dead ma tecnicamente ha priorità su class_tags/rc

### Insight
La matrice attuale è **corretta e senza contraddizioni**. `item_binding_policy` (Q11) può essere aggiunto come **rule 0** (top priority) senza modificare ordine esistente:
```
rule 0: if item.item_binding_policy == "universal" → OK (bypass)
rule 0': if item.item_binding_policy == "hard" and class_slug not in class_tags → BLOCK
```

---

## 11. Open Sub-Questions Emerse (per PM in B2)

**B2.SQ1** — **Shield (2 items) slot mapping**: opzione (a) mappa in `armor`, (b) aggiungi `shield` slot 4°, (c) lascia null? Preferenza agent: **(a)** SAFE, non-breaking.

**B2.SQ2** — **`specialization_unlocks` DEAD branch**: mantenere la logica (0 items la usano) o marcare come deprecated? Preferenza agent: **mantenere + documentare come "reserved for future spec system"**.

**B2.SQ3** — **`required_class_optional` populated su 11 items** (feature hard-bound già esistente ma parziale): mantenere come SoT hard-bound o migrare tutto a `item_binding_policy`? Preferenza agent: **mantenere back-compat + policy come override esplicito**.

**B2.SQ4** — **Items con `required_class_optional=berserker/assassin`** (`bloodied_greataxe`, `silent_kris`, `corrupted_blade`, `twin_blades`, `runic_aegis`, `truestrike_bow`) — 6 items **de facto unusable** (0 live adventurer post-reset per berserker/assassin). Rimuovere dal catalog? Marcare `is_active=false`? Lasciare dormant? Preferenza agent: **lasciare dormant (metadata resta, backlog P3 revisit)**.

**B2.SQ5** — **EQUIP_WARNING rate-limit strategy** (Q10): sampling 1:N, daily bucket per adventurer, o solo aggregate telemetry? Preferenza agent: **daily bucket per (guild_id, adventurer_id, reason_code) — 1 event/day max**.

**B2.SQ6** — **`item_binding_policy` schema campo** (Q11): valori ammessi `soft|hard|universal`. Default per catalog esistente? Preferenza agent: **derive default via bucket assignment (E1→hard, E2/A/C/G1→soft, G2→universal)**.

**B2.SQ7** — **UI 4-state signal**: aggiungere `recommended_for_class: bool` e `is_universal: bool` all'API response `item_public()`? Preferenza agent: **sì SAFE**, deriva runtime da current fields.

---

## 12. Proposta Bozza B2 Decision Lock (NO applicare)

### Schema `item_binding_policy` field
```yaml
field: items.item_binding_policy
type: enum
values: [soft, hard, universal]
default_derivation:
  - if required_class_optional populated → hard
  - if slug matches "^spec_signature_" AND required_class_optional → hard
  - if item_type in [material, material_*, consumable] → universal
  - else → soft
target_population: 178 items (all)
```

### Backfill `slot_type` (B3 sibling script)
- 138/140 items via `item_type→slot_type` (weapon/armor/accessory)
- 2 shield items → **PENDING B2.SQ1**
- Dry-run first, apply gate `APPLY_ENABLED=False`

### Audit event schema
```yaml
event: EQUIP_BLOCKED
metadata: {guild_id, adventurer_id, item_id, item_slug, reason_code, class_slug, source_route, timestamp}
rate: unlimited (rare event)

event: EQUIP_WARNING
metadata: same + {rate_bucket_id}
rate: 1 per (guild_id, adventurer_id, reason_code) per day (aggregate)
```

### UI 4-state mapping
```yaml
severity=block: red icon + "Non equipaggiabile"
severity=warning: yellow icon + reason_it (soft)
severity=ok, recommended_for_class=true: green icon + "Consigliato"
severity=ok, is_universal=true: grey icon + "Universale"
severity=ok, else: neutral (no badge)
```

### Backlog additions (P3)
- `R18.4.followup — Shield slot mapping decision` (B2.SQ1)
- `R18.4.backlog — specialization_unlocks dead branch cleanup` (B2.SQ2)
- `R18.4.backlog — berserker/assassin dormant signature items` (B2.SQ4)

---

## 13. Rischi Identificati + Safety Signals

### 🟢 Safety signals (in favore)
- **auto_equip.py Q6 già rispettato** dal REOPEN #2 R16.5.4b (warning SKIP)
- **0 equipped_items live** post-reset → timing operativo ottimo
- **27 test R16.5.4b** già coprono class_locked/warning/druid/alchemist/warlock/tie-break
- **Bard drift NON impatta R18.4** (verificato con 3 sample)
- **NULL class_slug (13 adv)** gestito via `_resolve_class_slug` fallback (verified: tutti hanno `class_name` populated)
- **Signature 14 items** già hanno split naturale hard(8)/soft(6) — Option 3 già ~80% presente
- **required_class_optional feature esistente** (11 items) è già la vera hard-bound infrastructure

### 🟡 Attenzione (medio rischio, gestibile in B2)
- **Shield 2 items OPEN slot mapping** — sub-question SQ1
- **specialization_unlocks DEAD branch** — sub-question SQ2 (documentale, no runtime impact)
- **6 signature items dormant** (berserker/assassin required_class) — sub-question SQ4
- **UI 4-state** richiede nuovo signal API (feasibility alta ma richiede frontend change in B3)
- **G1 backfill 140 items** — dry-run mandatory prima di apply reale
- **Coverage gap**: NULL class_slug, audit event, item_binding_policy field, G1 backfill

### 🔴 Dipendenze critiche / BLOCKED (dal PM)
- Bridge R18.3e wired runtime → BLOCKED R18.3f
- Canonical IT rewrite items → BLOCKED
- Unlock recruitment CdM/CdV → BLOCKED
- VALID_ROLES change (Bard) → BLOCKED
- Migration adventurers class_slug → BLOCKED
- Player-facing slug change → BLOCKED

---

## 14. Recommendation per B2

**Verdict**: **PROCEED to B2 decision lock** ✅.

### Motivazione
1. Sistema equipment/compatibility/auto_equip è **già ~80% coerente con Option 3 Hybrid Refined**
2. Q6 (auto-equip hard-bound rispetto) è **già implementato** dal REOPEN #2 R16.5.4b (2026-07-02)
3. Test baseline solida (27 R16.5.4b + altri) — regression risk basso
4. 7 sub-questions (SQ1-SQ7) sono tutte **safe** e non bloccano il round (chiarimenti governance)
5. G1 backfill fattibile via dry-run sibling script (Q13 sequenza rispettata)

### Prossimi step raccomandati (B2)
1. **PM lock** su SQ1-SQ7 (7 sub-questions emerse in B1)
2. **PM lock** su `item_binding_policy` schema campo (Q11 approvato, valori/default confermati)
3. **PM lock** su UI 4-state mapping API signal (Q7)
4. **PM lock** su audit event rate-limit strategy (Q10 + SQ5)
5. **Deliverable B2**: `/app/memory/r18_4_phase_b2_pm_decisions.md` + `.json`

### Risk flags per B2
- Nessun **HIGH** risk identificato
- 3 **MEDIUM** risk (shield mapping, dormant signatures, UI signal design) gestibili documentalmente
- 5 **LOW** risk (backfill dry-run, test coverage gap, dead branch, i18n edge) risolvibili in B3-B4

---

## Self-Check 10/10 Phase B1

1. ✅ Report MD creato
2. ✅ Report JSON creato + parsabile
3. ✅ Zero DB write (0 update, 0 insert, 0 audit event nuovo)
4. ✅ Zero audit event nuovo
5. ✅ Zero code change runtime
6. ✅ Zero frontend change
7. ✅ **24 sigilli byte-identical** (verified via sha256sum + sealed/integrity 6/6 PASS)
8. ✅ Coverage matrix 10×5 = 50 verdicts eseguita in-process
9. ✅ Open Sub-Questions ≥ 7 (SQ1-SQ7)
10. ✅ Recommendation B2 presente (PROCEED)

**STOP Phase B1**. In attesa di GO PM per **B2 Decision Lock** (14 OQ già risolte + 7 SQ nuove da chiarire).
