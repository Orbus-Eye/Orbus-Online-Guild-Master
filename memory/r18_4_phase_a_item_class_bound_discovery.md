# R18.4 Phase A — Item Class-Bound Player-Facing DISCOVERY LITE (read-only)

- **Round**: R18.4 — Item Class-Bound Player-Facing — Phase A
- **Tipo**: DISCOVERY LITE — READ-ONLY
- **Timestamp UTC**: `2026-07-05T20:35:00Z`
- **Perimetro**: analisi statica codebase + query DB read-only. NO DB write, NO code change, NO audit event.
- **Bridge R18.3e**: usato SOLO come input documentale/metadata (bridge_status, canonical_slug). NO runtime wiring.
- **Caveat obbligatorio**: `class_slug` live NON è ancora canonical IT. Adventurers restano su slug legacy EN (warrior, rogue, mage, ecc.).

---

## 1. Executive Summary

**Sistema equipment/compatibility già IBRIDO** (Option 3 parzialmente implementato in `/app/backend/app/equipment/compatibility.py`):

- **HARD BLOCK** già presente per: (a) signature/class-locked (`required_class_optional`), (b) heavy armor blacklist (6 classi caster), (c) arcane weapon blacklist (7 classi melee), (d) specialization_required.
- **SOFT WARNING** già presente per: `not_recommended_class`, `off_class_tags`, `specialization_mismatch` — allowed=True + `warning_it` esposto al client.
- **Adventurers live**: 3373 doc, TUTTI con `class_slug` legacy EN (warrior=331, monk=327, bard=324, druid=311, warlock=305, paladin=303, rogue=302, alchemist=299, ranger=299, mage=281, priest=278) + **13 NULL** (backlog P3 pre-esistente).
- **Items catalog**: 178 doc totali. **157** con `class_tags` non-empty, **157** con `recommended_classes` non-empty (allineati). Solo **17** con `slot_type` populated (weapon_main=7, amulet=5, chest=3, helm=1, ring=1).
- **Canonical IT references**: 49 items totali (**cacciatore_di_mostri=31**, **cacciatore_del_vuoto=18**) esclusivamente in `recommended_classes`. Zero in `class_tags`. Zero in adventurers live.
- **inventory_items**: 673 doc live + 111 archiviati R18. **equipped_items**: 0 (post-reset R18.Reset.1b, catalog vuoto).
- **Bridge R18.3e**: applicato — `warrior.canonical_slug="guerriero"`, `warrior.bridge_status="mapped_canonical"`, ecc. Presente su 18 doc `adventurer_classes` come 5 SAFE metadata field, NO runtime wired.

**Verdict Phase A**: L'infrastruttura equipment esiste già ed è funzionalmente ibrida. R18.4 può proseguire come consolidamento/estensione (non greenfield). La domanda principale per il PM: quale bucket eleva a hard-bound vs quale resta soft-warning?

---

## 2. Item Binding Current-State

### Hard-bound (esistente)
| Meccanismo | Field/Logic | Item impact |
|---|---|---|
| `required_class_optional` == class_slug | Explicit class lock (signature single-class) | 0 items nel catalog attuale usano questo field (ricontrollato) |
| `NO_HEAVY_ARMOR_CLASSES` × `armor_tags="heavy"` | Blacklist statica (mage, necromancer, priest, druid, bard, warlock) | Blocco derivato — dipende da `armor_tags` popolato (non presente nel sample schema top-30 keys) |
| `NO_ARCANE_WEAPON_CLASSES` × `weapon_tags ∩ ARCANE_WEAPON_TAGS` | Blacklist statica (7 classi melee) | Blocco derivato — dipende da `weapon_tags` popolato |
| `specialization_unlocks` × `spec_slug` mismatch + not in `recommended_classes` | Specialization gate (Round 16.0) | 12 items signature (`spec_signature_*`) usano questa logica |

### Soft-warning (esistente)
| Meccanismo | Field/Logic | Item impact |
|---|---|---|
| `recommended_classes` non-empty, class_slug NOT IN → `not_recommended_class` | Soft rec | 157 items eleggibili |
| `class_tags` non-empty, class_slug NOT IN → `off_class_tags` | Soft class_tags | 157 items eleggibili |
| `specialization_unlocks` non-empty + spec mismatch + class in recommended → `specialization_mismatch` | Soft spec | 12 signature items |

### Ownership/binding (non-class)
| Meccanismo | Modulo | Note |
|---|---|---|
| `is_bound` (guild-BoE) | `inventory/bound.py` | Phase 4/Round 4 — post-Forge refine/enchant/reroll |
| `bound_to_adventurer_id` (adventurer-bound) | `inventory/bound.py` | Round 6B.4 — hard limit su equip + retire block |

---

## 3. `class_tags` / `recommended_classes` Inventory

### Chi popola
- **Scripts seed**: `round15_seed_item_tags.py`, `round160_update_items_class_tags.py`, `round1654c_class_coverage_seed.py`, `round173_class_coverage_seed.py`
- **Bridge R18.3e**: NON popola item — solo adventurer_classes metadata (5 SAFE fields documental)

### Chi legge (runtime)
- `equipment/compatibility.py:check_equip_compatibility()` — soft warnings (righe 168, 178)
- `equipment/auto_equip.py` — fitness scoring (594 righe, da audit dedicato in Phase B se necessario)

### Formato valori — LEGACY EN dominante
Distribution `class_tags` (top): paladin=92, warrior=69, berserker=64, mage=34, necromancer=34, druid=34, priest=32, rogue=31, ranger=31, assassin=31, bard=29, monk=24, warlock=18, alchemist=18. **Zero canonical IT**.

Distribution `recommended_classes` (top): identico a `class_tags` per i legacy slug + **cacciatore_di_mostri=31**, **cacciatore_del_vuoto=18**. Totale canonical IT refs = **49** (coerente con report R18.3e).

### Mixed
2 items in bucket C (mixed legacy+canonical): `drake_slayer_blade`, `goblin_hunter_ring` — hanno legacy in `class_tags` e sia legacy che canonical in `recommended_classes`.

---

## 4. Item Count by Bucket (7 bucket A-G)

| Bucket | Definizione | Count | Note |
|---|---|---|---|
| **A** | Legacy EN only in ct/rc | **3** | drake_slayer_helm, drake_slayer_chest, arcane_adept_orb — tag legacy pure |
| **B** | Canonical IT only in ct/rc | **0** | Nessun item ha canonical IT senza legacy — coerente (canonical è additive) |
| **C** | Mixed legacy+canonical | **2** | drake_slayer_blade, goblin_hunter_ring — canonical solo su rc |
| **D** | No class binding | **0** | Nessun item genuinamente equipaggiabile senza binding (tutti gli slot_type populated hanno tags) |
| **E** | Signature/special (`spec_signature_*`) | **12** | Round 6C signature templates. Include CdM refs in 5+ items |
| **F** | Starter/common generici | **0** | Il criterio adottato (slug contiene starter/common) non ha match — starter kit usa `minor_healing_potion` (consumable, non equipaggiabile) |
| **G** | Missing slot_type / metadata | **161** | **G split**: 140 con class_tags populated, 21 senza. 54 weapon + 42 armor + 42 accessory + 8 material + 8 material_continental + 3 material_event + 2 shield + 2 consumable |

**Insight**: la classificazione naive mostra un forte squilibrio in G (161/178 = 90%). Root cause: `slot_type` è underused nel catalog attuale. Il campo `item_type` è più affidabile (weapon=61, accessory=48, armor=46). R18.4 dovrà probabilmente convergere su `item_type` come primary slot binding, con `slot_type` come derived o backfill.

**Bucket G suddivisione dettagliata**:
- **G1 — equipaggiabile con tags ma senza slot_type**: 140 items (weapon+armor+accessory+shield con class_tags legacy)
- **G2 — materiali/consumabili**: 21 items (material, material_continental, material_event, consumable — non equipaggiabili by design)

---

## 5. Item Count by Class Slug

### class_tags distribution (legacy EN only)
| Slug legacy | Count | Bridge target (R18.3e) |
|---|---|---|
| paladin | 92 | paladino (mapped_canonical) |
| warrior | 69 | guerriero (mapped_canonical) |
| berserker | 64 | (deprecated_alias, no target) |
| mage | 34 | mago (mapped_canonical) |
| necromancer | 34 | negromante (mapped_canonical) |
| druid | 34 | druido (mapped_canonical) |
| priest | 32 | (deprecated_alias, no target) |
| rogue | 31 | ladro (mapped_canonical) |
| ranger | 31 | cacciatore_di_mostri (mapped_alias) |
| assassin | 31 | ladro (mapped_canonical, alias di rogue) |
| bard | 29 | bardo (mapped_canonical) |
| monk | 24 | monaco (mapped_canonical) |
| warlock | 18 | cacciatore_del_vuoto (mapped_alias) |
| alchemist | 18 | alchimista (mapped_canonical) |

### recommended_classes distribution (identico + 2 canonical hidden)
Come sopra + `cacciatore_di_mostri=31`, `cacciatore_del_vuoto=18`.

### Adventurers class_slug distribution (3373 doc)
| Slug legacy live | Count |
|---|---|
| warrior | 331 |
| monk | 327 |
| bard | 324 |
| druid | 311 |
| warlock | 305 |
| paladin | 303 |
| rogue | 302 |
| alchemist | 299 |
| ranger | 299 |
| mage | 281 |
| priest | 278 |
| (null) | 13 |
| **Totale** | **3373** |

**Coverage bridge R18.3e vs adventurers live**: 11 slug legacy live effettivi, TUTTI presenti nel bridge come `mapped_canonical` o `mapped_alias`. `berserker`/`assassin` documentati nel registry ma **0 adventurers live** (post-reset R18.Reset.1b safe classes = 11).

---

## 6. Player-Facing Equip Flow (attuale)

### Frontend components identificati
- `/app/frontend/src/pages/Inventory.jsx` — lista globale inventory guild
- `/app/frontend/src/pages/AdventurerEquipment.jsx` — pagina equip dedicata per adventurer
- `/app/frontend/src/components/InventoryEquipModal.jsx` — modal equip/unequip
- `/app/frontend/src/components/AdventurerDetailModal.jsx` — dettaglio adventurer con slot equip

### Flow attuale (dedotto dai routes + compatibility.py)
1. Player clicca "Equipaggia" su un item in inventory
2. Frontend chiama `POST /api/adventurers/{id}/equip` con `{item_id, slot}`
3. Backend `equip_item_service` → `check_equip_compatibility(adventurer, item)` (pure fn)
4. Se `severity=block` → HTTP 400 con `reason_it` + `reason_code`
5. Se `severity=warning` → 201 con `warning_it` esposto nella response
6. Se `severity=ok` → 201 clean

**UI compatibility badge**: non verificato in questa discovery (Phase B se necessario). Presumibilmente `InventoryEquipModal.jsx` riceve `warning_it` e mostra visual cue.

---

## 7. Backend Equip Validation Flow

### Endpoint
- `GET /api/adventurers/{adventurer_id}/equipment`
- `POST /api/adventurers/{adventurer_id}/equip` → `EquipIn{item_id, slot}`
- `POST /api/adventurers/{adventurer_id}/unequip` → `UnequipIn{slot}`
- `POST /api/adventurers/{adventurer_id}/auto-equip` (Round 16.0 Phase 3)

### Guard (server-authoritative)
1. `user_guild_or_404(db, current_user["id"])` — ownership check
2. `equip_item_service` (394 righe, `equipment/services.py`):
   - carica adventurer + item + inventory_row
   - `is_bound_to_other_adventurer` → HTTP 422 (Round 6B.4 guard)
   - `resolve_item_required_level` → level gate (`level_gate.py`)
   - `check_equip_compatibility` → block/warning/ok (`compatibility.py`)
   - se block → HTTP 400
   - se warning → allowed + warning_it in response
   - persist `equipped_items` row + update inventory

### Compatibility rules (via `check_equip_compatibility`)
- Hard: `required_class_optional`, `heavy_armor_forbidden` (6 classi), `arcane_weapon_forbidden` (7 classi), `specialization_required`
- Soft: `not_recommended_class`, `off_class_tags`, `specialization_mismatch`
- Universal: `is_universal=true` bypass ogni check

---

## 8. Auto-Equip Dependency Map

- **File**: `/app/backend/app/equipment/auto_equip.py` (594 righe, non aperto in dettaglio in Phase A)
- **Endpoint**: `POST /api/adventurers/{id}/auto-equip`
- **Round intro**: 16.0 Phase 3
- **Signature nota**: `auto_equip_adventurer(db, guild=..., adventurer_id=..., actor_user_id=...)`
- **Presumibili input signal** (da audit Phase B):
  - `class_slug` dell'adventurer
  - `power_score` degli item disponibili
  - `class_tags` + `recommended_classes` per fitness scoring
  - `stat_tags` + `role_tags` (dal sample item schema)
  - `level_required` / `required_adventurer_level` per gate
  - `heavy_armor` / `arcane_weapon` blacklist (via compatibility)
- **NOT AUDITED IN PHASE A**: score weights, tie-breaker, materiali/potion handling, "best per slot" selection.

---

## 9. Frontend Inventory/Equip Dependency Map

### Components identificati (senza deep-dive Phase A)
| Componente | File | Ruolo probabile |
|---|---|---|
| Inventory (page) | `/app/frontend/src/pages/Inventory.jsx` | Lista global guild inventory |
| AdventurerEquipment (page) | `/app/frontend/src/pages/AdventurerEquipment.jsx` | Slot management per adventurer |
| InventoryEquipModal | `/app/frontend/src/components/InventoryEquipModal.jsx` | Modal transactional equip |
| AdventurerDetailModal | `/app/frontend/src/components/AdventurerDetailModal.jsx` | Dettaglio slot con equip inline |

### Data flow probabile (da confermare Phase B)
- API `GET /api/inventory` → lista item guild
- API `GET /api/adventurers/{id}/equipment` → slot correnti
- API `POST /api/adventurers/{id}/equip` → server-side compatibility validator
- Response `warning_it` → UI badge/toast/inline notice

### NON AUDITATO in Phase A
- Signal UI class-bound badge (icon color, tooltip, sort filter)
- Filter/sort "solo equipaggiabile"
- Auto-equip button UX
- Multi-select equip flows

---

## 10. Bridge R18.3e Applicability

### Come il bridge PUÒ informare R18.4 (documentalmente)
Il bridge R18.3e presente su 18 `adventurer_classes` docs fornisce:
- `canonical_slug` (es. warrior→guerriero) — utile per **future migration path** class_slug
- `alias_target` (es. ranger→cacciatore_di_mostri) — utile per **soft alias binding**
- `bridge_status` (mapped_canonical / mapped_alias / deprecated_alias / canonical_native / technical_placeholder / test_artifact) — utile per **filter policy** (es. escludere deprecated_alias da recommended_classes)

### Esempi mapping utili per R18.4 semantic dedup
Items con `class_tags=["warrior"]` sono semanticamente equivalenti a items con `recommended_classes=["guerriero"]` **via bridge_status=mapped_canonical**. Attualmente nessun item usa `guerriero` come canonical target (0 in class_tags, 0 in recommended_classes). Il bridge è disponibile per future migration BUT NON è wired al runtime.

### Applicazione consigliata (documentale, no wiring runtime in R18.4)
- **Compatibility validator**: potrebbe accettare BOTH legacy EN AND canonical IT come input (transparent alias resolution via bridge), MA sarebbe modifica runtime non richiesta in R18.4.
- **Auto-equip fitness**: idem — bridge come lookup table read-only.
- **Frontend badge**: mostrare canonical_slug come "nome design" opzionale accanto al legacy.

**Conservative default**: R18.4 usa SOLO slug legacy live come SoT runtime. Bridge R18.3e resta metadata documental fino a R18.3f (slug migration planning, deferred).

---

## 11. Risk Matrix

| Modifica candidata | Impatto | Rischio | Blocked? |
|---|---|---|---|
| Aggiungere UI badge "consigliato per classe X" (leggendo esistente `not_recommended_class` warning) | Frontend only, no schema change | **SAFE** | NO |
| Backfill `slot_type` per 140 items in bucket G1 (equipaggiabili senza slot_type) | Schema fill, no logic change | **SAFE** ma richiede seed dedicato + audit event | NO |
| Convergere `item_type` → derived `slot_type` per equip pathway | Runtime path change | **RISKY** (impatta 178 items live + auto-equip) | Richiede test regression |
| Hard-bound su tutti gli item con `class_tags` non-empty | Breaking change: bloccherebbe cross-class equip su warning-only oggi | **RISKY** | Richiede audit degli equipped_items current + gate PM |
| Wire bridge R18.3e runtime (canonical_slug in compatibility) | Cambia semantica equip senza migration slug | **RISKY** | Blocked fino a R18.3f slug migration |
| Migrate adventurers.class_slug da legacy EN → canonical IT | Rewrite 3373 doc + inventory + equipped_items | **BLOCKED** | Round separato R18.3f (deferred) |
| Unlock recruitment classi hidden (CdM/CdV) per rendere items 49 utilizzabili live | Recruitment UX + is_playable flip | **BLOCKED** | Fuori scope R18.4 (esplicitamente escluso da PM) |
| Populate `class_tags` con canonical IT su tutti gli item | Rewrite 157 items + bridge dependency runtime | **BLOCKED** | Round separato dopo R18.3f |
| Rewrite 12 signature items (bucket E) con hard `required_class_optional` | Trasforma soft→hard su signature | **RISKY** (breaking per adventurers che li usano oggi) | Richiede audit + gate PM |
| Frontend: nuovo tab "Equip per classe" con filtro compat | Nuovo UI, no schema change | **SAFE** | NO |
| Aggiungere audit event `EQUIP_BLOCKED` / `EQUIP_WARNING` per telemetry | Audit-only, no logic change | **SAFE** | NO |
| Backfill `recommended_classes` con canonical target (bridge apply) su 157 items | Rewrite items collection | **RISKY** (equivalente a slug migration parziale) | Richiede R18.3f |

---

## 12. Proposed R18.4 Design Options

### Option 1 — Soft Recommendation Only (status-quo consolidamento)
- **Descrizione**: Mantieni comportamento attuale ibrido. Investi in UI badge, filtri, tooltip per esporre `recommended_classes` e `warning_it` in modo player-friendly. No backend change.
- **Prerequisiti**: nessuno.
- **Migration path**: nessuna.
- **Impatto UI**: alto (nuovi badge/tooltip/filter).
- **Impatto backend**: basso (nessun cambio logic, opzionale audit event).
- **Impatto test**: medio (nuovi frontend test per UI badge/filter).
- **Pro**: zero breaking, immediate delivery, non tocca 3373 adventurers.
- **Contro**: non aggiunge coerenza design (ranger che equipaggia grimoire arcano oggi rimane bloccato via arcane_weapon_forbidden ma un warrior che equipaggia amuleto "mage" ottiene solo warning).
- **Rischio**: **BASSO**.

### Option 2 — Hard Class-Bound Full
- **Descrizione**: Trasforma tutti i `not_recommended_class` warning in `block`. `class_tags` diventa hard-bound: se class_slug NOT IN class_tags → HTTP 400.
- **Prerequisiti**: (a) audit `equipped_items` current per non-compatible legacy equips (attualmente 0 doc live, quindi safe timing post-reset); (b) gate PM esplicito.
- **Migration path**: nessuna (0 equipped_items live).
- **Impatto UI**: alto (rimozione warning path, hard error dialog).
- **Impatto backend**: medio (modify compatibility.py, add audit event EQUIP_BLOCKED_HARD).
- **Impatto test**: alto (rewrite compatibility test cases + regression).
- **Pro**: coerenza design forte, semantica pulita, prevede migration futura.
- **Contro**: breaking future se players riempiranno equipped_items pre-R18.4 apply (attualmente 0, ma se posticipato rischia); rigido per items "generalisti" (bucket A drake_slayer_helm su 3 classi).
- **Rischio**: **ALTO** post-first-equip populate.

### Option 3 — Hybrid Refined (RACCOMANDATO)
- **Descrizione**: Formalizza il pattern ibrido già presente + aggiunge UI polish. 
  - **Hard-bound**: bucket E (12 signature) + `required_class_optional` populated + heavy/arcane blacklist esistente.
  - **Soft-recommended**: bucket A/C/G1 (140+3+2 = 145 items) — `not_recommended_class` warning esposto in UI con badge chiaro.
  - **Universal**: bucket G2 (materiali/consumabili) — is_universal=true skip (dove applicabile).
- **Prerequisiti**: (a) backfill `slot_type` su bucket G1 (140 items), preferibilmente derivato da `item_type`; (b) audit event opzionale per warnings; (c) UI badge upgrade.
- **Migration path**: solo backfill `slot_type` (SAFE seed).
- **Impatto UI**: medio (badge + filter).
- **Impatto backend**: basso (compatibility.py invariato, solo audit event opzionale).
- **Impatto test**: medio (backfill validation + audit event test).
- **Pro**: incrementale, non-breaking, riflette il design esistente, prepara ground per R18.3f senza forzarlo, sfrutta bridge R18.3e come reference documentale.
- **Contro**: mantiene ambiguità semantica su bucket A (soft warning per off-class items).
- **Rischio**: **MEDIO-BASSO**.

---

## 13. Open Questions PM (14 domande, min 12 richiesto)

1. **R18.4 deve essere soft, hard o hybrid?** (Raccomandazione Option 3 hybrid refined.)
2. **Gli item starter/common devono restare generici (bucket F, oggi vuoto)?** Devono essere ridefiniti o si accetta l'assenza?
3. **Gli item signature (bucket E, 12 items) devono essere hard class-bound?** Attualmente usano `specialization_unlocks` (soft con block se spec required); trasformare in hard-required-class?
4. **`recommended_classes` deve usare slug legacy live o canonical IT (via bridge)?** Coerenza design vuole canonical, coerenza runtime vuole legacy.
5. **`class_tags` deve restare legacy o diventare bridge-aware (accetta entrambi)?** Bridge-aware = 2x lookup e alias resolution.
6. **Auto-equip deve rispettare class-bound o solo raccomandazioni?** Se hard, un adventurer senza items compatibili resta unarmed?
7. **UI deve mostrare "non compatibile" (block) o solo "consigliato" (warning)?** Impatta severity mapping.
8. **Cosa succede a items già equipaggiati non compatibili se si passa a hard-bound?** Attualmente 0 equipped_items live (post-reset), quindi timing OK — vale come regola?
9. **Le 2 canonical hidden CdM/CdV possono avere item class-bound anche se non reclutabili?** 49 items references già presenti ma nessun adventurer live può indossarli.
10. **Serve audit event per equip blocked/failed?** Utile per telemetry ma aumenta audit_log traffic.
11. **Serve migration metadata sugli item prima di enforcement?** Es. `item_binding_policy: soft|hard|universal` per governance esplicita.
12. **R18.4 può partire senza R18.3f (slug migration)?** Sì se Option 1/3, marginale se Option 2 (bridge non wired).
13. **Bucket G1 (140 items senza slot_type) va backfillato prima o durante R18.4?** Blocker per hard-bound in slot-specific check.
14. **Il round R18.3d.followup Bard Role Drift (bard.role="Support" fuori VALID_ROLES) impatta R18.4?** Bard ha 29 items recommended — se R18.4 usa role_tags, il drift potrebbe emergere.

---

## 14. Recommendation Phase B

**Approccio staged raccomandato per Phase B** (in attesa di GO PM su Option 1/2/3):

### Phase B1 — Deep-dive audit (READ-ONLY)
1. Audit completo `auto_equip.py` (594 righe): fitness weights, tie-breaker, class impact
2. Audit frontend components `InventoryEquipModal.jsx`, `AdventurerEquipment.jsx`: badge current, warning display
3. Test suite baseline: run `pytest -k equip` + snapshot report
4. Sample verify: 10 items × 5 classi = 50 compatibility_check calls, coverage matrix

### Phase B2 — Decision Lock (PM decisioni)
- 14 Open Questions → PM decisions locked in `/app/memory/r18_4_phase_b_pm_decisions.md`
- Selezione Option 1 / 2 / 3
- Backlog policy per bucket G1 (140 items slot_type backfill)

### Phase B3 — Registry + Sibling script (documental)
- `/app/memory/r18_4_item_class_bound_registry.md` + `.json` (bucket assignment, target policy, safe/blocked fields)
- Sibling apply/rollback script `round18_4_apply_class_bound.py` (dry-run only initially, gate `APPLY_ENABLED=False`)
- Test suite `backend_r18_4_class_bound_test.py` (16+ test)

### Phase B4 — Contract lock + SEAL
- e1_tester regression (4-6 macro tests)
- SEAL R18.4 con banner CLOSED & SEALED sui file
- Registry aggregato 29 sigilli (24 attuali + 5 R18.4)

### NON in Phase B (deferred)
- Slug migration (R18.3f)
- Recruitment unlock CdM/CdV
- Rewrite items canonical IT
- Bard role drift resolution (R18.3d.followup, backlog P3)

---

## Vincoli Rispettati (Phase A read-only)

- ❌ Zero DB write (no items rewrite, no adventurers touch, no audit event)
- ❌ Zero code change runtime (equipment/compatibility/auto_equip invariati)
- ❌ Zero frontend change (Inventory/Equipment components invariati)
- ❌ Zero migration slug legacy → canonical
- ❌ Zero unlock recruitment classi hidden
- ❌ Zero rewrite `items.class_tags` / `items.recommended_classes`
- ❌ Zero touch ai 24 sigilli (14 R18.Reset.1b/1.2 + 5 R18.3d + 5 R18.3e) byte-identici
- ❌ Zero runtime wiring bridge R18.3e
- ❌ Zero hard delete
- ❌ Zero apply R18.4 (Phase A discovery-only)

**STOP Phase A**. In attesa di GO PM per Phase B (Option 1/2/3 selection + Deep-dive audit).
