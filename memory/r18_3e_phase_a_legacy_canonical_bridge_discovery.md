# R18.3e Phase A — Legacy EN ↔ Canonical IT Class Bridge Discovery (READ-ONLY)

- **Round**: R18.3e — Canonical IT ↔ Legacy EN Class Bridge — Phase A
- **Perimetro**: Discovery LITE read-only (no DB write, no code change, no route, no UI, no wiring)
- **Timestamp (UTC)**: `2026-07-05T18:06:50Z`
- **Baseline audit_log pre-scan**: `11896`
- **Baseline audit_log post-scan**: `11896` (delta = **0** ✅)
- **14 sigilli**: SHA256 salvati in `/tmp/r18_3e_sealed_hashes_pre.txt` (verificati byte-identici a fine discovery — vedi sezione 15)

---

## 1. Executive Summary

Il registry documentale R18.3d ha bloccato **27 classi canonical IT** vs **16 legacy live EN** (di cui 2 canonical hidden intersect: `cacciatore_di_mostri`, `cacciatore_del_vuoto`). Phase A conferma che i due set restano **quasi disgiunti** ma emergono 5 findings critici che il PM deve valutare **prima** di R18.3e Phase B:

1. **Il `display_name_it` è già popolato su tutti e 18 i doc live** di `adventurer_classes` (es. `warrior.display_name_it = "Guerriero"`). Il layer "IT label" **esiste già** al livello DB ma diverge dai candidate mapping PM su 3 slug: `priest→Sacerdote` (non "Paladino"), `ranger→Ranger` (non tradotto), `warlock→Occultista` (non "Cacciatore del Vuoto").
2. **Il frontend ha già un `CLASS_IT` map hardcoded** in `/app/frontend/src/utils/displayLabels.js:110-127` con le stesse 14 chiavi legacy → traduzioni IT statiche. Il map **non contiene le 2 canonical hidden** (`cacciatore_di_mostri`, `cacciatore_del_vuoto`), che verrebbero renderizzate come slug raw.
3. **49 items** hanno GIÀ soft-binding verso le 2 canonical hidden via `items.recommended_classes` (31 verso `cacciatore_di_mostri`, 18 verso `cacciatore_del_vuoto`). Le "hidden" non sono più veramente hidden — sono già live-referenced.
4. **`class_slug` è runtime-critical** in 10+ moduli backend (adventurers, equipment/compatibility, equipment/auto_equip, training, expeditions guard `recruit_unassigned`, PvP snapshot, admin) e in 15+ componenti/pagine frontend. Un rename di slug legacy è **breaking** trasversale.
5. **32 test file** referenziano slug legacy hardcoded. Un rewrite slug richiederebbe update coordinato dei test o un layer `alias_target` che i test non vedono.

**Raccomandazione**: R18.3e Phase B **deve essere un bridge documentale append-only sui 18 doc `adventurer_classes`** (SAFE metadata `bridge_status` + `canonical_slug` alias) o su registry file R18.3e (in-memory), **NON un rename slug live**. Deferire la migration reale a un round dedicato R18.3f post-decisione PM.

---

## 2. Lista Legacy Live Completa (16 + full 18 catalog)

**Query source**: `db.adventurer_classes.find({}, {"_id":0}).to_list(None)` — snapshot dei 18 doc live.

### 16 slug legacy live EN (i core PM-listati)

| # | slug | name | display_name_it (già live!) | role | primary_stat | is_active | is_playable | is_canonical | is_base_class |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `warrior` | Warrior | **Guerriero** | Tank | strength | ✅ True | (n.d.) | (n.d.) | ✅ True |
| 2 | `rogue` | Rogue | **Ladro** | DPS | agility | ✅ True | (n.d.) | (n.d.) | ✅ True |
| 3 | `mage` | Mage | **Mago** | DPS | intellect | ✅ True | (n.d.) | (n.d.) | ✅ True |
| 4 | `priest` | Priest | **Sacerdote** | Healer | faith | ✅ True | (n.d.) | (n.d.) | ✅ True |
| 5 | `ranger` | Ranger | **Ranger** ⚠️ | DPS | agility | ✅ True | (n.d.) | (n.d.) | ✅ True |
| 6 | `paladin` | Paladin | **Paladino** | Tank | **faith** ⚠️ | ✅ True | (n.d.) | (n.d.) | ✅ True |
| 7 | `berserker` | Berserker | **Berserker** ⚠️ | DPS | strength | ❌ False | (n.d.) | (n.d.) | (n.d.) |
| 8 | `druid` | Druid | **Druido** | Healer | faith | ✅ True | (n.d.) | (n.d.) | ✅ True |
| 9 | `necromancer` | Necromancer | **Negromante** | DPS | intellect | ❌ False | (n.d.) | (n.d.) | (n.d.) |
| 10 | `monk` | Monk | **Monaco** | DPS | agility | ✅ True | (n.d.) | (n.d.) | ✅ True |
| 11 | `bard` | Bard | **Bardo** | **Support** ⚠️ | intellect | ✅ True | (n.d.) | (n.d.) | ✅ True |
| 12 | `assassin` | Assassin | **Assassino** | DPS | agility | ❌ False | (n.d.) | (n.d.) | (n.d.) |
| 13 | `warlock` | Warlock | **Occultista** ⚠️ | DPS | intellect | ✅ True | (n.d.) | (n.d.) | ✅ True |
| 14 | `alchemist` | Alchemist | **Alchimista** | DPS | intellect | ✅ True | (n.d.) | (n.d.) | ✅ True |
| 15 | `recruit_unassigned` | (missing) | **Da riassegnare** | None | None | (n.d.) | ❌ False | ❌ False | ❌ False |
| 16 | `test-class-5e0064` | Updated Test Class | (missing) | Tank | (missing) | ❌ False | (n.d.) | (n.d.) | (n.d.) |

### 2 canonical hidden IT (già live nel DB, is_canonical=True, is_playable=False)

| # | slug | display_name_it | role | is_active | is_playable | is_canonical | description |
|---|---|---|---|---|---|---|---|
| 17 | `cacciatore_di_mostri` | Cacciatore di Mostri | TBD | ✅ True | ❌ False | ✅ True | Migration target class R18.3a orphan migration **from `ranger`** |
| 18 | `cacciatore_del_vuoto` | Cacciatore del Vuoto | TBD | ✅ True | ❌ False | ✅ True | Migration target class R18.3a orphan migration **from `warlock`** |

**Totale live catalog**: **18 doc** (16 legacy + 2 canonical hidden).

**Divergenze `display_name_it` vs candidate mapping PM**:
- `priest.display_name_it = "Sacerdote"` MA candidate mapping PM = "paladino" → ambiguo, Sacerdote ≠ Paladino a livello canonical.
- `ranger.display_name_it = "Ranger"` (untranslated!) MA candidate mapping PM = "cacciatore_di_mostri" → coerente con R18.3a orphan migration target.
- `warlock.display_name_it = "Occultista"` MA candidate mapping PM = "cacciatore_del_vuoto" → **incongruenza label**: già oggi in UI un warlock è mostrato come "Occultista", ma il canonical dice "Cacciatore del Vuoto".
- `bard.role = "Support"` è **out of `VALID_ROLES=(Tank,DPS,Healer)`** — drift già a backlog `R18.3d.followup`.
- `paladin.primary_stat = "faith"` diverge dal canonical design (`strength`) — LOCKED live su faith per non corrompere 303 paladini live.

---

## 3. Usage Count per Legacy Slug (Adventurers Live)

**Query source**: `db.adventurers.aggregate([{$group:{_id:$class_slug, n:{$sum:1}}}])`

| # | class_slug | adventurers live | % del roster |
|---|---|---|---|
| 1 | `warrior` | 331 | 9.81% |
| 2 | `monk` | 327 | 9.69% |
| 3 | `bard` | 324 | 9.60% |
| 4 | `druid` | 311 | 9.22% |
| 5 | `warlock` | 305 | 9.04% |
| 6 | `paladin` | 303 | 8.98% |
| 7 | `rogue` | 302 | 8.95% |
| 8 | `ranger` | 299 | 8.86% |
| 9 | `alchemist` | 299 | 8.86% |
| 10 | `mage` | 281 | 8.33% |
| 11 | `priest` | 278 | 8.24% |
| 12 | `<null>` (drift) | 13 | 0.39% |
| **TOTAL** | | **3373** | 100% |

**Findings**:
- 11 slug playable coprono **3360 adventurers** (già distribuiti in modo abbastanza uniforme 8-10%).
- **13 adventurers con `class_slug=NULL`** — tutti hanno però `class_name` set (drift pre-R16 residuo). Fallback runtime li salva via `class_name.lower()`.
- **0 adventurers live** su `berserker`, `assassin`, `necromancer` (già `is_active=False`), `recruit_unassigned`, `test-class-5e0064`, `cacciatore_di_mostri`, `cacciatore_del_vuoto`. Le due canonical hidden non hanno mai avuto un player.

---

## 4. Player-Facing Impact

**Frontend (React) — 20+ file** referenziano `class_slug`, `class_name`, `class_role`:

| Componente/Pagina | Usa | Note |
|---|---|---|
| `pages/Adventurers.jsx` | `classLabel(a.class_slug) \|\| a.class_name` (r. 368, 494) | Client-side lookup su `CLASS_IT` map |
| `pages/RaidBuilder.jsx` | `a.class_name`, `a.class_role` (r. 166, 190, 210, 253, 691) | Filter roster per klass |
| `pages/PvpChallenge.jsx` | `a.class_name \|\| a.class_slug` (r. 132) | Fallback readable |
| `pages/PvpBattleReport.jsx` | `a.class_slug` (r. 181) | Snapshot post-battle |
| `pages/ExpeditionReport.jsx` | `m.class_name_snapshot` (r. 597) | Snapshot immutabile |
| `pages/ExpeditionNew.jsx` | `a.class_role`, `a.class_slug \|\| a.class_name` (r. 49, 187, 339, 517) | Filter e display |
| `pages/WorldBossEvent.jsx` | `a.class_slug` (r. 178) | Display raw slug (bug potenziale) |
| `pages/Training.jsx` | `a.class_name`, `a.class_slug` (r. 312, 335, 425, 482) | Eligibility check |
| `pages/RosterManage.jsx` | `a.class_role`, `a.class_name \|\| a.class_slug` (r. 76, 99, 535) | Filter role, display |
| `pages/ClassHalls.jsx` | `h.class_slug` (r. 40, 230, 248, 338) | Class-bound routing (`/class-halls/${classSlug}/unlock-specialization`) |
| `pages/Recruitment.jsx` | `candidate.class_name`, `candidate.class_role` (r. 68, 75, 157) | Display badge |
| `pages/SquadBuilder.jsx` | `adv.class_role`, `adv.class_name` (r. 54, 74, 83, 178) | Role marker |
| `components/AdventurerDetailModal.jsx` | `classLabel(adventurer.class_slug)` (r. 168) | Client lookup CLASS_IT |
| `components/InventoryEquipModal.jsx` | `a.class_role`, `a.class_name` (r. 166, 170) | Filter |
| `components/RespecModal.jsx` | `adv.class_slug`, `adv.class_name` (r. 47, 92) | Class change UI |
| `components/AdventurerRenameModal.jsx` | `adventurer.class_name`, `adventurer.class_role` (r. 83) | Display |
| `components/RosterFilterBar.jsx` | `state.class_slug` (r. 71, 72) | Query filter |

**Contract `CLASS_IT` map (frontend hardcoded)** in `utils/displayLabels.js:110-127`:
```js
const CLASS_IT = {
    warrior: "Guerriero", rogue: "Ladro", mage: "Mago",
    priest: "Sacerdote", ranger: "Ranger", paladin: "Paladino",
    druid: "Druido", monk: "Monaco", bard: "Bardo",
    warlock: "Occultista", alchemist: "Alchimista",
    // Deprecated legacy slugs kept for safe rendering on old data:
    berserker: "Berserker", assassin: "Assassino", necromancer: "Negromante",
};
```
Non contiene `cacciatore_di_mostri`, `cacciatore_del_vuoto`, `recruit_unassigned`, `test-class-5e0064` → renderizzati come slug raw. **Attenzione**: se il bridge assegna `warlock.canonical_slug=cacciatore_del_vuoto` e la UI legge canonical_slug, il render diventa "cacciatore_del_vuoto" invece di "Occultista".

---

## 5. Recruitment Impact

**Reclutabili live (`is_active=True`, presente in offer pool via `recruitment/services.py`)**:
- 11 slug (i playable): `warrior, rogue, mage, priest, ranger, paladin, druid, monk, bard, warlock, alchemist`.

**Non reclutabili**:
- `berserker`, `assassin`, `necromancer` (is_active=False, deprecate silenziose ma display_name_it presente per legacy render).
- `cacciatore_di_mostri`, `cacciatore_del_vuoto` (is_playable=False, is_canonical=True — target migration, non offer pool).
- `recruit_unassigned` (is_playable=False, is_canonical=False — tecnico orphan holder).
- `test-class-5e0064` (is_active=False — artifact test).

**Guard `recruit_unassigned`** in `expeditions/services.py:907`:
```python
if _cs == "recruit_unassigned" or not _cs or _cs not in _playable_slugs:
    # BLOCK: adventurers.recruit_unassigned_in_set
```
Un rename di `recruit_unassigned` romperebbe questo guard.

**Migration path R18.3a residuo (`round181_schema_foundation.py`)**:
- `recruit_unassigned` è la classe target per orphan cleanup (91 orfani migrati storicamente).
- `cacciatore_di_mostri` è descritta come **"Migration target class R18.3a for orphan migration from `ranger`"**.
- `cacciatore_del_vuoto` è descritta come **"Migration target class R18.3a for orphan migration from `warlock`"**.
- Questo suggerisce che il **bridge canonical è già stato deciso a livello design in R18.3a** per (`ranger→cacciatore_di_mostri`, `warlock→cacciatore_del_vuoto`), ma **non è mai stato applicato al DB** (adventurers restano su slug legacy).

---

## 6. Item / Equipment Impact

**`items` collection**: 178 doc totali.

| Field | Count non-empty | Distinct values (relevant) |
|---|---|---|
| `class_slug` | 0 | (never set on items) |
| `class_bound_slug` | 0 | (never set) |
| `class_tags` | **157** | `alchemist, assassin, bard, berserker, druid, mage, monk, necromancer, paladin, priest, ranger, rogue, warlock, warrior` (14 legacy EN) |
| `recommended_classes` | **157** | Le 14 legacy EN + **`cacciatore_di_mostri` (31 items!), `cacciatore_del_vuoto` (18 items!)** |
| `role_tags` | 115 | `dps_caster, dps_melee, dps_ranged, frontline, healer_aoe, healer_dedicated, stealth, support, tank` |

**Findings item bindings**:
- **Nessun HARD binding** (`class_slug`, `bound_class_slug`, `class_lock`, ecc. su items = 0). L'unico binding è SOFT via `class_tags` / `recommended_classes` — usato da `equipment/compatibility.py:167-182` con `reason_code="off_class_tags"` come **WARN**, non block.
- **49 items già bindano canonical hidden** in `recommended_classes` (31 verso `cacciatore_di_mostri`, 18 verso `cacciatore_del_vuoto`). Le hidden **non sono più veramente hidden a livello dati**.
- Item sample `drake_slayer_helm`:
  - `class_tags=['warrior','paladin','berserker']` (misto: 2 legacy attivi + 1 deprecato)
  - `recommended_classes=['warrior','paladin','berserker']`
  - `role_tags=['tank','dps_melee','frontline']`

**Collezioni class-bound VUOTE (0 doc live)**:
- `equipment: 0`, `player_inventory: 0`, `specializations: 0`, `class_halls: 0`, `adventurer_specializations: 0`, `training_specs: 0`.

**Recipes: 5 doc**, tutti `is_active=True`, **nessun class binding** (solo material inputs).

---

## 7. Frontend / API / Test Dependencies

### Backend runtime path che leggono/scrivono `class_slug` / `class_name` / `class_role`

| File | Righe | Ruolo |
|---|---|---|
| `app/adventurers/services.py` | 161, 169, 196, 200-206 | `class_slug` con fallback su `class_name.lower()` — CRITICAL per read/write path |
| `app/adventurers/routes.py` | 65, 96-97, 101, 127 | Filter `class_slug` e `class_role` in query API |
| `app/adventurers/common.py` | 127-133 | Write path: popola `class_slug`, `class_name`, `class_role` da doc `adventurer_classes` |
| `app/adventurers/generator.py` | 216 | Offer generation con `class_slug: klass["slug"]` |
| `app/equipment/compatibility.py` | 54, 67-68, 128, 167-182 | Equipment fitness — usa `class_slug` + `class_tags`/`recommended_classes` |
| `app/equipment/auto_equip.py` | 149-178, 236-245 | Auto-equip — `_resolve_class_slug()` con fallback `class_name` |
| `app/equipment/services.py` | 320 | Emit `class_slug` in equipment events |
| `app/training/services.py` | 36-63, 190-198, 576-583 | `_resolve_class_slug()` + `eligible_classes` check |
| `app/training/catalog.py` | 409-414 | `specs_for_class_and_tier(class_slug)` |
| `app/expeditions/services.py` | 872-917 | **GUARD `recruit_unassigned`** + non-playable class hard-stop |
| `app/pvp_continental/services.py` | 112 | Snapshot `class_slug` per PvP matchup |
| `app/recruitment/services.py` | 113-114, 433-434 | Offer generation `class_name`, `class_role` |
| `app/recruitment/freeze_bench.py` | 52, 91-92, 238, 374-375 | Bench snapshot include `class_name`, `class_role` |
| `app/recruitment/routes.py` | 73 | Response emit `class_name` |
| `app/onboarding/services.py` | 57, 58, 117 | Seed clean_onboarding con `class_name`, `class_role` |
| `app/admin/tester_tools.py` | 186, 216, 239-240, 335 | Class map admin |
| `app/admin/audit_routes.py` | 142 | Audit `adventurer_class_slug_only` |
| `app/admin/routes.py` | 57, 89, 97, 116, 123-131 | Admin CRUD su `adventurer_classes` |
| `app/guilds/routes.py` | 92, 135 | Zero leak metadata `previous_class_slug` (già gestito) |
| `app/contracts/services.py` | 99 | Comment: "fallback lesson from Round 6C `class_slug` bug" |
| `app/audit/log.py` | 234 | Event key `item_class_tags_extended` |

### Frontend runtime path (già dettagliato in sezione 4)

20+ file usano `class_slug`, `class_name`, `class_role`, `classLabel()`.

### Test file dependencies

**32 file** in `/app/backend/tests/` contengono almeno un match hardcoded su slug legacy (`warrior`, `rogue`, `mage`, ecc.). Totale match: **339 occorrenze**. Rename slug = 32 file da aggiornare in coordinata (o alias layer trasparente ai test).

File più caldi (sample):
- `backend_round181_migration_test.py` — 20+ ref (test guard `recruit_unassigned`, count 91/85)
- `backend_round1812_guard_test.py` — whitelist slugs sealed test
- `backend_round1b_hotfix_v1_2_starter_stats_test.py` — starter stats mapping per slug
- `backend_round1b_hotfix_v1_3_schema_compat_test.py` — schema compat post-reset
- `backend_r18_3d_stat_role_registry_test.py` — R18.3d self test (SEALED)
- `backend_round6c_specialization_test.py` — spec per class
- `backend_round6e_respec_test.py` — respec per class

---

## 8. Candidate Mapping Legacy → Canonical (10 proposti, con confidence)

**Fonte**: draft PM (msg 80/GO R18.3e) + verifica registry R18.3d + `display_name_it` live.

| # | legacy_slug | proposed canonical_slug | display_name_it live | Confidence | Evidenza tecnica |
|---|---|---|---|---|---|
| 1 | `warrior` | `guerriero` | Guerriero | **HIGH** | display_name_it match. Canonical `guerriero` in registry R18.3d design-only. Nessun conflict semantico. |
| 2 | `rogue` | `ladro` | Ladro | **HIGH** | display_name_it match. Canonical `ladro` in registry design-only. |
| 3 | `mage` | `mago` | Mago | **HIGH** | display_name_it match. Canonical `mago` in registry design-only. |
| 4 | `monk` | `monaco` | Monaco | **HIGH** | display_name_it match. Canonical `monaco` in registry design-only. |
| 5 | `druid` | `druido` | Druido | **HIGH** | display_name_it match. Canonical `druido` in registry design-only. |
| 6 | `bard` | `bardo` | Bardo | **MEDIUM** | display_name_it match, MA `bard.role="Support"` drift out of VALID_ROLES (R18.3d.followup backlog). Il bridge dovrebbe accettare o rimappare role. |
| 7 | `alchemist` | `alchimista` | Alchimista | **HIGH** | display_name_it match. Canonical `alchimista` in registry design-only. |
| 8 | `necromancer` | `negromante` | Negromante | **MEDIUM** | display_name_it match, MA `is_active=False` deprecato silenziosamente. Deve essere mappato o marcato `deprecated`? PM decide. |
| 9 | `ranger` | `cacciatore_di_mostri` | **Ranger** ⚠️ | **MEDIUM** | Coerente con R18.3a "Migration target from ranger". MA `display_name_it="Ranger"` (untranslated) mentre canonical è "Cacciatore di Mostri". UI cambia label da "Ranger" a "Cacciatore di Mostri" — decisione PM. 299 adventurers live impattati. |
| 10 | `warlock` | `cacciatore_del_vuoto` | **Occultista** ⚠️ | **MEDIUM** | Coerente con R18.3a "Migration target from warlock". MA `display_name_it="Occultista"` diverge da canonical "Cacciatore del Vuoto". UI cambia label da "Occultista" a "Cacciatore del Vuoto" — decisione PM. 305 adventurers live impattati. 18 items già bindano `cacciatore_del_vuoto`. |

**Nessun mapping è stato applicato**. Sono candidate proposte per Phase B.

---

## 9. Ambiguous Mappings (6 mapping con Open Questions PM)

| # | legacy_slug | Opzioni | Pro/Contro | Decisione richiesta al PM |
|---|---|---|---|---|
| 1 | `priest` | (a) `paladino` (b) `sacerdote` (nuova canonical) (c) `deprecato` | (a) semplice ma role/stats non allineati (paladin=Tank/faith, priest=Healer/faith); (b) coerente con display_name_it="Sacerdote" ma **`sacerdote` NON è in registry R18.3d canonical**; (c) 278 adventurers live orfani | (b) è la scelta più fedele al display_name_it ma richiede aggiunta `sacerdote` a canonical set. |
| 2 | `paladin` | (a) `paladino` (mapping semplice) (b) `deprecato` (c) split in `paladino_tank` + `sacerdote` | display_name_it="Paladino" match, MA `paladin.primary_stat="faith"` diverge da canonical design (`strength`, LOCKED live). Role="Tank" corretto. | (a) mapping semplice ma stat drift resta documentale (già in R18.3d) |
| 3 | `assassin` | (a) `ladro` (dup di rogue) (b) `assassino` (nuova canonical) (c) `deprecated_alias_target=ladro` | is_active=False, 0 adventurers live. In frontend map (`CLASS_IT`) è tenuto per "safe rendering on old data". Spec `assassin_spec` è una specializzazione di rogue (r. 135). | (c) mantenere come deprecated alias verso `ladro` + rimuovere dal recruitment pool (già escluso via is_active=False) |
| 4 | `berserker` | (a) `guerriero` (dup di warrior) (b) `berserker` (nuova canonical) (c) `deprecated_alias_target=guerriero` | is_active=False, 0 adventurers live. Spec `berserker_spec` è specializzazione di warrior. `class_tags` di alcuni items include berserker (drift). | (c) deprecated alias verso `guerriero` + hard-remove `berserker` da `items.class_tags` in un round cleanup (NON ora) |
| 5 | `recruit_unassigned` | (a) escluso dal canonical bridge (b) canonical `nessuna_classe` (c) mantenuto legacy-only | Tecnico placeholder per orphans. Guard `expeditions/services.py:907` hardcoded su questo slug. is_playable=False, is_canonical=False. | (a) escluso dal bridge — resta legacy tecnico non-canonical. Rename romperebbe guard runtime. |
| 6 | `test-class-5e0064` | (a) test artifact permanente (b) delete dal catalog (c) rename `test_artifact_reserved` | is_active=False, name="Updated Test Class", origina da test admin CRUD. Nessun runtime dep. | (a) test artifact permanente — mark `bridge_status=test_artifact` senza mapping canonical. |

---

## 10. Unsafe Mappings (che romperebbero runtime)

| # | Scenario | Perché è unsafe | Runtime path colpito |
|---|---|---|---|
| 1 | Rename slug `warrior → guerriero` in `adventurer_classes.slug` | Rompe `adventurers.class_slug='warrior'` su 331 doc + fallback `class_name.lower()='warrior'` in `adventurers/services.py:200-206` | Auto-equip, training, expeditions, PvP snapshot |
| 2 | Rename `recruit_unassigned → da_riassegnare` (o simili) | Rompe guard `expeditions/services.py:907` hardcoded `"recruit_unassigned"` + `round181_schema_foundation.py:70,105,124,128` orphan target | Expeditions hard-block + orphan migration script |
| 3 | Rimozione `is_active=True` su `warlock`, `ranger`, `priest`, ecc. | Rompe recruitment pool (307-299 adventurers/mo generation) | `recruitment/services.py` offer generation |
| 4 | Rimozione `class_tags` values (es. `berserker`) dagli items | 0 adventurers live berserker ma frontend `CLASS_IT` la mantiene per safe render. Item filter `equipment/compatibility.py:178` non tocca (soft warn) — MA modification triggera WARN sui 32 test | Test suite legacy assumptions |
| 5 | Aggiungere `class_slug` HARD field su items | Feature nuova (R18.4). Non è unsafe di per sé, ma richiederebbe cascade rewrite di 157 items + item filter runtime + admin UI item edit | R18.4 scope |
| 6 | Aggiornare `paladin.primary_stat: faith → strength` | Rompe XP debuff calc su 303 adventurers paladin live (soglia `threshold_per_level=0.5` di `xp_primary_stat_policy`) | `xp_primary_stat_policy` runtime |

**Conclusione**: **nessun rename slug live è safe** senza migration DB coordinata + rewrite cascade di 32 test + frontend map update. Il bridge documentale (append-only meta field su `adventurer_classes`) è l'unica opzione senza rischio breaking.

---

## 11. No-op / Deprecated / Test-Only Classes

| slug | Classification | Adventurers live | Runtime dep | Note |
|---|---|---|---|---|
| `recruit_unassigned` | Tecnical placeholder | 0 | ✅ hardcoded in guards | Escluso dal canonical bridge. Migration target orphan (round181). |
| `test-class-5e0064` | Test artifact | 0 | ❌ none | Marcare `bridge_status="test_artifact"`. Non-canonical, non-playable. |
| `berserker` | Deprecated legacy | 0 | Frontend safe-render map + items class_tags (12 items) | is_active=False. Deprecated alias verso `guerriero` (proposta). |
| `assassin` | Deprecated legacy | 0 | Frontend safe-render map + items class_tags (n items) | is_active=False. Deprecated alias verso `ladro` (proposta). |
| `necromancer` | Deprecated legacy | 0 | Frontend safe-render map + items class_tags (n items) | is_active=False. Deprecated alias verso `negromante` (proposta). |
| `cacciatore_di_mostri` | Canonical hidden — soft-live | 0 (adv) / 31 items | is_playable=False, is_canonical=True | Bridge target da `ranger` (già designato R18.3a). |
| `cacciatore_del_vuoto` | Canonical hidden — soft-live | 0 (adv) / 18 items | is_playable=False, is_canonical=True | Bridge target da `warlock` (già designato R18.3a). |

---

## 12. Recommended Bridge Shape (proposta, NON applicare)

**Approccio raccomandato**: **bridge documentale append-only** su `adventurer_classes` con 5 field SAFE (aggiungibili via `$set`, reversibili via `$unset`), tutti backend/documental — **zero runtime read**.

### 12.1 Field proposti (5 SAFE, 0 RISKY, 0 BLOCKED)

| Field | Tipo | SAFE/RISKY/BLOCKED | Descrizione | Esempio |
|---|---|---|---|---|
| `canonical_slug` | str \| null | **SAFE** (append-only, non runtime-read finché unwired) | Slug canonical IT target per il legacy slug (se applicabile). Null per non-canonical o test artifact. | `warrior.canonical_slug = "guerriero"` |
| `alias_target` | str \| null | **SAFE** | Alias per legacy deprecated (semantic alias, non FK). Null se il legacy È il canonical. | `assassin.alias_target = "ladro"` |
| `bridge_status` | enum | **SAFE** | Stato bridge documentale: `mapped_canonical` \| `mapped_alias` \| `ambiguous_pending_pm` \| `deprecated_alias` \| `test_artifact` \| `technical_placeholder` \| `canonical_native`. | `warrior.bridge_status = "mapped_canonical"` |
| `bridge_source_round` | str | **SAFE** | Audit trail. Es. `"R18.3e Phase B"`. | `"R18.3e Phase B"` |
| `bridge_applied_at` | ISO datetime UTC | **SAFE** | Timestamp SET del bridge. | `"2026-07-XX..."` |

### 12.2 Field da NON aggiungere (RISKY o BLOCKED)

| Field | Perché evitare |
|---|---|
| `canonical_class_slug` | **RISKY duplicate naming vs `canonical_slug`**. Confusione contract. Scartare. |
| Rename `slug` field | **BLOCKED** — rompe 20+ backend path + 20+ frontend + 32 test. Non fare senza migration round dedicato. |
| Rimozione `class_name` field | **BLOCKED** — frontend hard-dependency in 15+ pagine. |
| Rimozione `is_active`, `is_playable`, `is_canonical` | **BLOCKED** — recruitment pool + admin filter. |

### 12.3 Registry file bridge (in-memory, unwired)

Analogo al pattern R18.3d Phase B: registry JSON in `/app/memory/r18_3e_bridge_registry.json` (documental-only, unwired). Contiene:
- `legacy_slug → {canonical_slug, alias_target, bridge_status, drift_notes}` map per 16 slug legacy
- `canonical_slug → legacy_slug[]` reverse map (per verificare N:1)
- `mapping_confidence` (HIGH/MEDIUM/LOW/AMBIGUOUS) per ogni riga
- 5 SAFE field da applicare (identici al pattern R18.3d)
- Dry-run script `round18_3e_apply_bridge.py` unwired (APPLY_ENABLED=False)

**Bridge Phase B applicable via $set** (dopo GO PM su Open Questions) sui 18 doc `adventurer_classes` con:
```
{"canonical_slug", "alias_target", "bridge_status", "bridge_source_round", "bridge_applied_at"}
```

**Non runtime read finché R18.4 non introduce l'accesso.**

---

## 13. Open Questions PM (14 domande — minimo 10 richieste)

Domande da chiudere **prima** di R18.3e Phase B apply. Nessun default automatico.

1. **Q1**. Usare `canonical_slug` come field principale o `alias_target`? Oppure entrambi (semantica: `canonical_slug` per mapping "positivo verso set canonical", `alias_target` per deprecated legacy che non ha canonical dedicato)?
2. **Q2**. Il bridge deve stare su `adventurer_classes` docs (schema-side), su `/app/memory/r18_3e_bridge_registry.json` (documental-only), o entrambi (registry come source-of-truth + $set append-only sui doc)?
3. **Q3**. `priest` → `paladino` (semplice mapping) o `sacerdote` (aggiungere `sacerdote` al canonical set) o `deprecated_alias_target=paladino`? **Il display_name_it live è "Sacerdote"**, non "Paladino".
4. **Q4**. `assassin` → `ladro` (deprecated_alias) o `assassino` (aggiungere al canonical set) o `deprecated_no_alias`? 0 adventurers live.
5. **Q5**. `berserker` → `guerriero` (deprecated_alias) o `berserker` (aggiungere al canonical set) o `deprecated_no_alias`? 0 adventurers live ma items `class_tags` include berserker.
6. **Q6**. `ranger` / `warlock` restano bridge verso `cacciatore_di_mostri` / `cacciatore_del_vuoto` anche se: (i) le 2 canonical sono `is_playable=False`; (ii) i display_name_it live sono "Ranger"/"Occultista" — cambio label significativo user-facing.
7. **Q7**. `recruit_unassigned` — escluso dal canonical bridge (bridge_status=`technical_placeholder`) o inserito come "nessuna_classe" nel canonical set?
8. **Q8**. `test-class-5e0064` — marcato come `test_artifact` permanente o eliminato dal catalog (delete_one)?
9. **Q9**. R18.4 può usare bridge append-only documentale (bridge_status letto ma slug primary invariato) o richiede migration DB completa (rewrite `adventurers.class_slug` da legacy → canonical)? La seconda opzione impatta 3373 adventurers + 32 test + 20+ backend path.
10. **Q10**. Serve UI label IT player-facing (mostrare "Cacciatore del Vuoto" invece di "Occultista" post-bridge) o solo admin/design layer (bridge invisibile agli utenti)? Impatto frontend `CLASS_IT` map.
11. **Q11** (bonus). `class_tags` sugli items va ri-scritto per usare canonical slugs (`guerriero` invece di `warrior`) o resta con legacy slug come chiave e il bridge risolve solo lato adventurer?
12. **Q12** (bonus). `bard.role="Support"` — mantenere drift documentato (R18.3d.followup) o cogliere occasione R18.3e per allineare a `Healer`/`DPS`? Impatto frontend `RoleMarker` (già gestisce Support).
13. **Q13** (bonus). Il bridge deve emettere un audit_log event dedicato (es. `R18_3E_BRIDGE_APPLIED`) o è documental-only zero-audit?
14. **Q14** (bonus). I 13 adventurers con `class_slug=NULL` vanno backfillati durante R18.3e (via `class_name.lower()`) o si continua a fare fallback runtime? Non è propriamente bridge ma è drift residuo emerso in Phase A.

---

## 14. Phase B Recommendation (staged, no auto-decision)

**Raccomandazione staged** — nessun apply automatico:

### Stage B0 — PM decide sulle 14 Open Questions (blocker)
Zero action code. Solo decisione documentale nel report PM.

### Stage B1 — Bridge registry file (documental-only, unwired)
- Creazione `/app/memory/r18_3e_bridge_registry.json` (+ MD companion) con le 16 righe legacy→canonical decise in B0.
- Analogo al pattern R18.3d Phase B: registry JSON in-memory + Python loader unwired + dry-run script + test suite dedicata.
- **Zero DB write**. Zero runtime wiring. Zero UI change.
- Chiusura come `CLOSED_AND_SEALED_DOCUMENTAL_ONLY`.

### Stage B2 — Optional DB append-only apply (SOLO su GO PM)
- Dry-run script `round18_3e_apply_bridge.py` (unwired, `APPLY_ENABLED=False`).
- Se GO PM: `$set` su 18 doc `adventurer_classes` con i 5 SAFE field. Reversibile via `$unset`.
- Audit event `R18_3E_BRIDGE_APPLIED` (se Q13 decide sì).
- 0 impatto adventurers docs (`class_slug` invariato). 0 impatto items (`class_tags`/`recommended_classes` invariati).
- Rollback plan: `$unset` dei 5 SAFE field via script simmetrico.

### Stage B3 — R18.4 può leggere `canonical_slug` (documental-only)
Post-B1/B2: R18.4 può opzionalmente usare `bridge_status` / `canonical_slug` per feature player-facing (es. show canonical name in item recommendation). **Nessuna migration slug**.

### Stage B4 — DEFERRED — Migration slug live (R18.3f o simili)
- SOLO se PM decide che il bridge documentale non basta.
- Round dedicato con downtime window, migration `adventurers.class_slug`, rewrite 32 test, aggiornamento frontend `CLASS_IT` map, update guard `expeditions/services.py:907` con nuovo slug `recruit_unassigned`.
- **NON in scope R18.3e**.

---

## 15. Self-Check Phase A (10 punti)

| # | Check | Result |
|---|---|---|
| 1 | Report MD creato | ✅ `/app/memory/r18_3e_phase_a_legacy_canonical_bridge_discovery.md` |
| 2 | Report JSON creato e parsabile | ✅ `/app/memory/r18_3e_phase_a_legacy_canonical_bridge_discovery.json` (parsed OK) |
| 3 | Zero DB write (audit_log delta) | ✅ `audit_log` pre-scan=11896, post-scan=11896, delta=0 |
| 4 | Zero audit event nuovo | ✅ 0 event R18_3E aggiunti |
| 5 | Zero route nuova | ✅ `/app/backend/app/**/routes.py` invariati (nessun `search_replace`) |
| 6 | Zero UI change | ✅ `/app/frontend/src/**` invariati |
| 7 | Zero runtime import/wiring | ✅ Nessun modulo runtime importa registry R18.3e (registry file non ancora esistente) |
| 8 | Sealed files intatti (14 sigilli) | ✅ SHA256 di 14 sigilli verificati byte-identici (vedi `/tmp/r18_3e_sealed_hashes_pre.txt` + rerun post-report). `pytest -k "sealed or integrity"` = 5/5 PASS |
| 9 | 16+ legacy slugs documentati con 8 dimensioni | ✅ 16 core + 2 canonical hidden = 18 doc coperti in sezioni 2-11 |
| 10 | Open Questions PM ≥ 10 | ✅ 14 domande in sezione 13 (10 richieste + 4 bonus) |

---

## STOP Phase A

**R18.3e Phase A discovery LITE completata.** In attesa di GO PM su:
- 14 Open Questions (sezione 13)
- Approvazione bridge shape (sezione 12) o proposta alternativa
- Decisione Stage B1 vs B2 vs B4 (sezione 14)

**Non avvio Phase B in autonomia.**
