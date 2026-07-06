# R18.4.followup — UI 4-State Item Compatibility Activation — Phase A Discovery (READ-ONLY)

- **Round naming**: `R18.4.followup — UI 4-State Item Compatibility Activation`
- **Phase**: A — Discovery lite (READ-ONLY, zero DB write, zero code change)
- **Generated at UTC**: `2026-07-06T07:55:00Z`
- **Perimetro**: pura investigazione file + endpoint + frontend components. Nessuna modifica di codice o dati.

---

## 1. Round naming decision

**Scelta**: `R18.4.followup — UI 4-State Item Compatibility Activation`

**Motivazione**:
- `R18.5` nel roadmap `/app/memory/orbus_world_roadmap.md` riga 29 è **già riservato**: `R18.5 | ⏸ WAITING R18.4 | PWR Solo-Equip + XP Curve Lv60 (3 varianti) + Item Tier Rework (2 modelli)`.
- Usare `R18.5` per UI 4-state creerebbe conflict di naming in roadmap registry.
- Il nuovo scope è direttamente derivato dal backlog `R18.4.followup — Public API serializer exposure of slot_type + item_binding_policy for UI activation` già registrato durante B4 SEAL.
- Naming `R18.4.followup` è coerente con altri follow-up già presenti (`R18.4.followup — Shield slot mapping decision`).

**Governance impact**: nessuno. Round R18.5 originale (PWR Solo-Equip) resta disponibile per futuro pickup senza collisione.

---

## 2. Serializer/API attuali che servono item al frontend

### 2.1 Endpoint pubblici
| Path | File | Serializer | Route method | Uso principale |
|---|---|---|---|---|
| `GET /api/items` | `/app/backend/app/items/routes.py:11-15` | `list_active_items` → `item_public` | list | catalog pubblico item attivi non-test |
| `GET /api/inventory` | `/app/backend/app/inventory/routes.py` | `inventory_public(row)` → embed `item_public` (services.py:42) | list | inventario gilda con item embedded |
| `POST /api/adventurers/{id}/equip` | `/app/backend/app/adventurers/routes.py` | payload `{item_id, slot}` | mutation | equip item su avventuriero |

### 2.2 Endpoint admin
| Path | File | Serializer | Uso |
|---|---|---|---|
| `GET /api/admin/items` | `/app/backend/app/admin/routes.py:292` | ricava item_public (probabile) | admin catalog |
| `POST /api/admin/items` | `/app/backend/app/admin/routes.py:298` | crea item | admin create |
| `PATCH /api/admin/items/{id}` | `/app/backend/app/admin/routes.py:322` | update item | admin update |
| `POST /api/admin/items/{id}/toggle-active` | `/app/backend/app/admin/routes.py:339` | toggle is_active | admin |
| `POST /api/admin/guilds/{id_or_public}/grant-item` | `/app/backend/app/admin/routes.py:602` | grant item to guild | admin |

### 2.3 Payload struttura attuale `item_public()` — **CAMPI ESPOSTI**
Da `/app/backend/app/items/services.py:14-56`:

```python
{
  "id": str, "slug": str, "name": str,
  "display_name_it": str, "display_name_en": str,
  "description": str, "item_type": str, "rarity": str,
  "level_required": int, "required_adventurer_level": int,
  "power_score": int,
  "strength_bonus": int, "agility_bonus": int, "intellect_bonus": int,
  "endurance_bonus": int, "faith_bonus": int,
  "is_tradeable": bool, "is_cosmetic": bool,
  "affects_combat": bool, "affects_economy": bool, "affects_ranking": bool,
  "can_be_sold_for_gold": bool, "can_be_sold_for_real_money": bool,
  "is_active": bool,
  "flavor_text_it": str|null, "flavor_text_en": str|null,
  "lore_tags": list, "spoiler_level": str, "lore_reviewed": bool
}
```

### 2.4 Campi NON esposti (candidati per UI 4-state)
- **`class_tags`** (soft signal, presente in DB, letto da `compatibility.py`)
- **`recommended_classes`** (soft signal principale)
- **`required_class_optional`** (hard signal, letto da compatibility)
- **`slot_type`** (nuovo R18.4, popolato su 140+17=157 items equipabili)
- **`item_binding_policy`** (nuovo R18.4, popolato su tutti i 178 items)
- **`is_universal`** (derived signal, SQ7 lock)
- **`recommended_for_class`** (derived signal per-class, SQ7 lock)

**Gap primario**: il frontend NON riceve alcun signal di compatibility/binding dall'API. Attualmente deve inferire lo slot da `item_type` (vedi sez. 3.2).

---

## 3. Componenti frontend che consumano item metadata

### 3.1 Files identificati
| File | Ruolo | Metadata consumati |
|---|---|---|
| `/app/frontend/src/pages/Inventory.jsx` | pagina inventario gilda | slot derivato da `item_type` |
| `/app/frontend/src/components/InventoryEquipModal.jsx` | modale equip player | `item.item_type` → slot, `item.level_required`, `item.power_score` |
| `/app/frontend/src/components/AdventurerDetailModal.jsx` | detail avventuriero + equipment | equipment slot render |
| `/app/frontend/src/pages/RaidBuilder.jsx` | raid setup | item selection |
| `/app/frontend/src/pages/Crafting.jsx` | crafting UI | material selection |
| `/app/frontend/src/pages/Resources.jsx`, `MaterialsPublic.jsx` | catalog materiali | item_type filter |
| `/app/frontend/src/components/MountCard.jsx`, `TraitBadge.jsx` | side features | non-item metadata |

### 3.2 Come rendered attualmente (esempio critico)
`/app/frontend/src/components/InventoryEquipModal.jsx:46`:
```javascript
const slot = row.item.item_type;   // ← usa item_type direttamente come slot
```
E line 66: `await api.post(``/adventurers/${adv.id}/equip``, { item_id: it.id, slot });`

**Rischio noto** (vedi sez. 10.1): per i 2 shield items (`spec_signature_aegis_of_the_defender`, `spec_signature_thornwood_shield`) `item_type="shield"` ma `slot_type="armor"` post-R18.4 SQ1a. Se il backend equip endpoint valida contro `slot_type` (o EQUIPMENT_SLOTS), l'attuale frontend passerebbe `slot="shield"` che potrebbe essere rifiutato.

### 3.3 UI patterns già presenti riusabili
- **Badge system**: `data-testid="equip-modal-adv-bound-badge"` (già presente per adventurer-bound) — pattern riusabile per compatibility badge.
- **Disabled state**: `equip-modal-no-eligible` message per "nessun avventuriero compatibile" — pattern riusabile per state "Bloccato".
- **Level required warning**: già rendered come parte del filtro "livello richiesto {it.level_required || 1}+" — pattern riusabile per "Non consigliato".
- **Toast success/error**: `toast.success(t("equipment_extra.toast_equipped"))` — pattern per feedback compatibility.

---

## 4. Mapping API → UI 4-state

### 4.1 4 stati player-facing (locked B2 SQ7)
| # | Stato | Signal backend richiesto | Logica derivativa |
|---|---|---|---|
| 1 | **Bloccato / Non equipaggiabile** | severity=block da `check_equip_compatibility` (context: adventurer specifico) | hard signal: `required_class_optional` mismatch, heavy_armor_forbidden, arcane_weapon_forbidden, level_gate, ownership |
| 2 | **Equipaggiabile ma non consigliato** | severity=warning | soft signal: `class_tags`/`recommended_classes` mismatch |
| 3 | **Consigliato per questa classe** | severity=ok AND `recommended_for_class=true` | classe in recommended_classes o class_tags |
| 4 | **Universale** | severity=ok AND `is_universal=true` AND !recommended_for_class | `item_binding_policy="universal"` |

### 4.2 Proposta: server-side vs client-side

| Aspetto | Server-side (raccomandato) | Client-side |
|---|---|---|
| Consistency policy | ✅ Single source of truth | ❌ Drift risk (2 impl backend/frontend) |
| Performance | Compute per item su list (potenzialmente cached) | 0 network overhead |
| i18n | Server produce label localizzata IT | Client dipende da traduzione JSON |
| Testability | Test backend copre policy | Test frontend E2E richiesto |
| Retro-compat | Nuovi field additivi (safe) | Frontend vecchi ignorano nuovi field (safe) |

**Raccomandazione**: **server-side compute** per `recommended_for_class` (dipende da classe) e `is_universal` (item-only). Client-side rendering ma senza logica policy.

**Note su `recommended_for_class`**: è per-class. Due strategie:
- **Strategia A**: `item_public(item, class_slug=None)` — se class_slug fornito, calcola signal. Se None, ritorna solo `is_universal`.
- **Strategia B**: espone lista `recommended_class_slugs` (già presente in `recommended_classes`) + client fa il match.

Da decidere in Phase B (SQ formulation sotto).

---

## 5. Dove esporre `slot_type`

### 5.1 Endpoint target
- `GET /api/items` (catalog): esporre in ogni item_public
- `GET /api/inventory` (embedded item): esporre in ogni inventory_row.item
- `GET /api/admin/items` (admin catalog): esporre per admin visibility
- Optional: `GET /api/adventurers/{id}/equipment` — item embedded esposti con slot_type

### 5.2 Localization
- **NO localizzazione IT necessaria** per `slot_type` (enum tecnico weapon/armor/accessory).
- UI userà label già presente `itemTypeLabel(slot).toUpperCase()` (vedi InventoryEquipModal.jsx:131). Potenzialmente estendibile a `slotTypeLabel(slot_type)`.

---

## 6. Dove esporre `item_binding_policy`

### 6.1 Endpoint target
- Stessi endpoint di `slot_type` (§5.1).

### 6.2 Formato esposizione
Due opzioni (da decidere in Phase B):
- **Opzione A — raw enum**: espone `item_binding_policy: "hard"|"soft"|"universal"` diretto. Client fa mapping label.
- **Opzione B — derived only**: espone solo `is_universal: bool` + `recommended_for_class: bool` (quando class_slug fornito). Enum raw resta backend-only.

**Trade-off**: Opzione A è più flessibile (client può implementare custom UI); Opzione B è più minimalista + evita esposizione policy interna.

### 6.3 Localization
Se Opzione A scelta, il client renderizza le label localizzate. Il backend può opzionalmente esporre `item_binding_policy_label_it` (es. "Vincolato", "Consigliato", "Universale") per consistency IT-only. Da decidere in SQ Phase B.

---

## 7. Impatto mobile/responsive

### 7.1 Stato attuale UI
Il frontend usa Tailwind + shadcn/ui components (badge, tooltip, disabled). Già responsive base tramite classi Tailwind (`flex-wrap`, `text-xs`, `md:text-sm`).

### 7.2 Proposta 4-state su mobile
- **Bloccato**: badge rosso + icona lucide `Ban` o `Lock` (già in `lucide-react` npm). Testo IT "Bloccato". Su mobile: solo icona con `aria-label`.
- **Non consigliato**: badge giallo/amber + icona `AlertTriangle`. Testo "Non consigliato". Su mobile: solo icona.
- **Consigliato**: badge verde + icona `Check` o `Star`. Testo "Consigliato".
- **Universale**: badge grigio/neutro + icona `Globe` o `Users`. Testo "Universale".

**Nessuna grafica pesante**: solo icone lucide-react + badge Tailwind (già in stack, zero nuove dipendenze).

### 7.3 Tooltip
Su desktop: hover tooltip con testo esteso ("Questa classe non è consigliata per questo item"). Su mobile: tap-to-toggle popover (pattern già usato per adventurer-bound badge).

---

## 8. Test esistenti che coprono item serializer / inventory / equipment UI

| File test | Coverage attuale |
|---|---|
| `/app/backend/tests/backend_phase19_4a_inventory_shape_test.py` | Inventory endpoint shape validation |
| `/app/backend/tests/backend_round1654b_test.py` | 27 test compatibility + auto_equip (baseline R16.5.4b) |
| `/app/backend/tests/backend_r18_4_class_bound_test.py` | 16 test R18.4 registry + dry-run + guard |
| `/app/backend/tests/backend_r18_4_sealed_integrity_test.py` | 5 test sealed integrity 30 files |
| `/app/backend/tests/backend_r18_3e_bridge_test.py` | 27+ test bridge R18.3e |

**Gap identificato**: nessun test copre l'esposizione dei nuovi field `slot_type`/`item_binding_policy` in `item_public()` (perché non ancora esposti).

---

## 9. Test mancanti identificati per UI 4-state

Da implementare in Phase B (backend) + Phase C (frontend):

**Backend**:
1. `test_item_public_exposes_slot_type` (default: null se missing)
2. `test_item_public_exposes_item_binding_policy` (default derivation)
3. `test_item_public_exposes_is_universal_derived` (true se policy=universal o item_type material/consumable)
4. `test_item_public_exposes_recommended_for_class_when_class_slug_provided` (Strategia A)
5. `test_item_public_backward_compat_absent_class_slug_no_recommended_for_class` (Strategia A)
6. `test_list_active_items_all_178_expose_new_fields`
7. `test_inventory_public_embed_item_new_fields`
8. `test_ui_4_state_derivation_all_combinations` (Bloccato/Warning/Recommended/Universal)

**Frontend E2E** (Phase C):
9. `test_inventory_shows_4_state_badges`
10. `test_equip_modal_disables_incompatible_items`
11. `test_mobile_responsive_badges_render`
12. `test_tooltip_or_popover_on_badge_interaction`

---

## 10. Rischi identificati

### 10.1 Shield slot mismatch frontend-backend
**Descrizione**: `InventoryEquipModal.jsx:46` fa `const slot = row.item.item_type;` — per shield items (2 su 178) `item_type="shield"` ma `slot_type="armor"` post-R18.4 SQ1a. Se backend equip endpoint valida contro EQUIPMENT_SLOTS = {weapon, armor, accessory}, l'attuale frontend chiamerebbe con `slot="shield"` → 400/422.

**Impatto**: **basso oggi** perché i 2 shield items sono signature soft (nessuna acquisizione player-live nota), ma diventa MEDIO se in R18.4.followup si espone slot_type ed il frontend continua ad usare `item_type` come slot.

**Mitigation raccomandata Phase B**: frontend dovrebbe usare `item.slot_type ?? item.item_type` (fallback) — richiede update `InventoryEquipModal.jsx` + `Inventory.jsx`.

**Governance nota**: NO fix in Phase A (read-only). Registra come SQ Phase B.

### 10.2 Retro-compat serializer
**Descrizione**: aggiunta di nuovi field a `item_public()` è **additiva safe** (client vecchi ignorano field sconosciuti). Verificato pattern: item_public già è cambiato in passato senza rompere client (es. `required_adventurer_level` aggiunto in R11.3).

**Rischio**: **basso**. Nessun action richiesto.

### 10.3 Performance su list endpoints
**Descrizione**: `GET /api/items` ritorna 178 items · `GET /api/inventory` ritorna N righe embed. Se `recommended_for_class` è per-class + computed per-item, complessità O(N × classes).

**Mitigation**: pre-computare solo `is_universal` in item_public (item-only), delegare `recommended_for_class` a un endpoint helper opzionale (`GET /api/items?for_class=<slug>`) o al client con la lista `recommended_classes` già esposta.

### 10.4 Localization scope
**Descrizione**: label 4-state ("Bloccato", "Non consigliato", "Consigliato", "Universale") devono essere IT (game è IT-native).

**Mitigation**: usare i file di i18n frontend esistenti (`/app/frontend/src/i18n/` se presente) o hardcoded IT strings in badge component. NO EN traduzioni per ora (deferrable a round dedicato).

### 10.5 Consistency canonical IT vs legacy EN class_slug
**Descrizione**: R18.3e bridge documental. `adventurers.class_slug` live resta legacy EN. Compat check usa `cls_slug = adv.class_slug.lower()` legacy.

**Impatto**: signal `recommended_for_class` dovrà usare la stessa base (legacy EN) per matching. NO scope creep in EN→IT migration.

**Mitigation**: usare `adventurer.class_slug` legacy EN in compatibility check. Coerente con `check_equip_compatibility` esistente.

### 10.6 Test regression risk
Aggiunta di nuovi field a `item_public()` potrebbe rompere test snapshot che fanno assertion strict su chiavi. Verificare i test esistenti che snapshot-testano item shape.

**Grep result** (Phase A): `backend_phase19_4a_inventory_shape_test.py` fa shape assertion — potenziale impact. Verificare in Phase B pre-implementation.

---

## 11. Sub-Questions PM per implementation Phase B

Domande concrete, binary-answerable (stile R18.4 B1):

### **B.SQ1 — Enum values naming**
Backend espone raw `item_binding_policy` enum al client? Opzioni:
- **(a)** SÌ, espone `item_binding_policy: "hard"|"soft"|"universal"` — flessibile
- **(b)** NO, espone solo `is_universal: bool` + `recommended_for_class: bool` — minimalista

Preferenza agent: **(a)** — abilita futuri use case (filtri catalog admin, telemetry).

### **B.SQ2 — Computed vs raw exposure**
Backend calcola `recommended_for_class` server-side (richiede class_slug context) o client-side (richiede esporre `recommended_classes` + `class_tags`)?
- **(a)** server-side, endpoint `GET /api/items?for_class=<slug>` + `GET /api/adventurers/{id}/inventory` con context class
- **(b)** client-side, backend espone raw `recommended_classes` + `class_tags` liste

Preferenza agent: **(b)** — semplifica backend, client conosce già l'adventurer selezionato.

### **B.SQ3 — Localization scope**
Backend espone label localizzata (`compatibility_label_it`) o client fa mapping enum → label?
- **(a)** solo enum, client mapping (Tailwind + i18n JSON)
- **(b)** backend espone label IT preformattata

Preferenza agent: **(a)** — segue pattern esistente (item_public non ritorna label localizzate per item_type/rarity).

### **B.SQ4 — Mobile display strategy**
Su schermo mobile (viewport < 640px) il badge 4-state mostra:
- **(a)** solo icona lucide (Ban/Alert/Check/Globe) con `aria-label`
- **(b)** icona + label breve (2-3 char, es "BLK"/"WRN"/"REC"/"UNI")
- **(c)** stesso layout desktop (icona + label full)

Preferenza agent: **(a)** — massima compattezza, tap-to-tooltip per dettaglio.

### **B.SQ5 — Backward compat strategy**
Client Frontend attuali che leggono `item.item_type` come slot devono essere aggiornati a usare `item.slot_type` fallback `item_type`?
- **(a)** SÌ, frontend update in Phase B (impatta InventoryEquipModal.jsx, Inventory.jsx)
- **(b)** NO, backend backfill `item_type` per shield (item_type=shield → item_type=armor) — WAIT: violerebbe SQ1(a) governance R18.4 (SQ4 NO change class_slug/item_type)
- **(c)** postpone al round separato

Preferenza agent: **(a)** — additivo safe, no violazione governance R18.4.

### **B.SQ6 — Endpoint contract per `for_class` context**
Se scelta B.SQ2(a), quale endpoint fornisce class context?
- **(a)** query param: `GET /api/items?for_class=warrior`
- **(b)** header: `X-For-Class: warrior`
- **(c)** implicit: `GET /api/adventurers/{id}/eligible-items` — usa class dell'avventuriero

Preferenza agent: **(c)** — semantica RESTful chiara.

### **B.SQ7 — Shield fix scope**
Il fix del rischio 10.1 (shield slot mismatch frontend-backend) è incluso in Phase B UI 4-state o separato in round dedicato?
- **(a)** incluso in Phase B (frontend usa `slot_type ?? item_type`)
- **(b)** separato in R18.4.followup Shield slot mapping decision (backlog P3 esistente)

Preferenza agent: **(a)** — bugfix coerente con l'esposizione slot_type.

### **B.SQ8 — Test coverage minimo per Phase B**
Numero minimo di test unitari + E2E richiesti prima del SEAL Phase B:
- **(a)** 8 backend (§9 list 1-8) + 4 frontend E2E (§9 list 9-12) = **12 test**
- **(b)** solo backend (12) + frontend testing manuale via e1_tester
- **(c)** exhaustive coverage 20+ test

Preferenza agent: **(a)** — bilanciamento tra rigore e velocità delivery.

---

## Self-check Phase A 12/12

- ✅ Round naming decision documentata (R18.4.followup)
- ✅ Serializer/API attuali mappati (3 pubblici + 5 admin)
- ✅ Componenti frontend identificati (13+ files)
- ✅ Mapping API → 4-state formalizzato
- ✅ Slot_type exposure plan
- ✅ item_binding_policy exposure plan
- ✅ Impatto mobile/responsive analizzato
- ✅ Test esistenti censiti (5 file)
- ✅ Test mancanti identificati (12 futuri)
- ✅ 6 rischi identificati (con severity + mitigation)
- ✅ 8 Sub-questions PM formulate (binary-answerable)
- ✅ Vincoli READ-ONLY rispettati (zero DB write, zero code change, zero sigilli toccati)

---

## Governance verifica Phase A

| Vincolo | Status |
|---|---|
| Zero DB writes | ✅ |
| Zero runtime enforcement changes | ✅ |
| Zero class_slug migration | ✅ |
| Zero class_tags canonical rewrite | ✅ |
| Zero runtime bridge activation | ✅ |
| Zero unlock CdM/CdV | ✅ |
| Zero unlock berserker/assassin | ✅ |
| Zero Bard role drift change | ✅ |
| Zero VALID_ROLES change | ✅ |
| Zero hard delete | ✅ |
| Zero sealed file modification | ✅ (verifica statica pre/post) |
| Zero apply script execution | ✅ |
| Zero code changes frontend/backend | ✅ |

**STOP Phase A**. In attesa di **PM review + risposta a B.SQ1..SQ8** per aprire Phase B (implementation).

Nessun scope-creep emerso (no class_slug migration richiesto per esporre metadata).
