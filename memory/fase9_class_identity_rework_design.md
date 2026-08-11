# FASE 9 — Class Identity Rework: audit e design
Data: 2026-08-11 · Branch: `Lavoro-partito-08/08/2026` · Baseline: `06129f8`

## 1. Direzione

Eliminazione completa di **specializzazione selezionabile** e **build
selezionabile**. Nuova catena canonica:

```
AVVENTURIERO → CLASSE → RUOLO FISSO → EQUIP DI CLASSE → SET RAID DI CLASSE
```

Il ruolo NON si chiama più "specializzazione": il termine canonico è
**`class_role`** (`DPS` | `TANK` | `HEALER`).

Lo **SLOT DI CLASSE** (futura componente ibrida) è approvato come
direzione ma NON viene implementato in questa tranche: il registry
riserva il punto di estensione (`hybrid_slot`, sempre `None` oggi) così
l'aggiunta futura non richiederà refactor.

## 2. Registry canonico (Source of Truth)

Nuovo modulo **`backend/app/classes/registry.py`**: 27 classi, ognuna con
`class_id` (slug), `class_name` (IT), `class_role` fisso,
`class_identity` (identità narrativa), `class_mechanics` (descrizione
gameplay), `class_equipment_rules` (primary_stat + armor/weapon tags dal
catalogo Hall esistente), `class_visual_identity` (slug emblema +
palette). Tutti gli slug esistono già nel catalogo Class Hall — nessuna
classe nuova, nessuna rinominata.

| Ruolo | Classi |
|---|---|
| DPS (13) | guerriero, ladro, mago, monaco, negromante, cacciatore_del_vuoto, artificiere, cartografo, runista, burattinaio, giocatore_d_azzardo, pittore, cacciatore_del_sangue |
| TANK (6) | paladino, cacciatore_di_mostri, fabbro_arcano, parassita, cavaliere_della_morte, cavaliere_di_draghi |
| HEALER (8) | alchimista, bardo, druido, sciamano, cronista, mercante, astrologo, sognatore |

Nota: la vecchia tassonomia (`Tank/DPS/Support/Hybrid/Utility` nel
catalogo Hall e nei doc `adventurer_classes`) viene SOSTITUITA a runtime
dal registry. Cambi rilevanti: Guerriero Tank→DPS, Paladino
Support→TANK, Cacciatore di Mostri DPS→TANK, Mercante/Astrologo/
Sognatore/Cronista →HEALER, ecc.

## 3. Audit: dove vivono oggi specialization e build

### 3.1 Backend — sistema "specializzazione" (2 generazioni)
1. **ROUND 6C (Training Grounds)** — `app/training/`:
   `SPEC_DEFINITIONS` (10 spec ibride selezionabili, costi oro, respec
   24h, item firma `spec_signature_*` bound on-apply),
   `seed_signature.py`, endpoint apply/respec in `training/routes.py`,
   `MIN_ADVENTURER_LEVEL=5`. Campo scritto:
   `adventurers.specialization_slug` (+ `specialization_respec_count`).
   → **RIMOSSO** (la pagina Addestramento rinasce XP-only in 9I).
2. **ROUND 16.0 (Class Hall)** — `class_halls/services.unlock_specialization`,
   route `POST /{class_slug}/unlock-specialization`, campo
   `class_halls.unlocked_specializations`, collezione DB
   `class_specializations` (counter_tags per spec). → **RIMOSSO**.

### 3.2 Backend — sistema "build" (81 = 27×3)
- `class_halls/mechanics.py`: `BuildIdentity` ×3 per classe (Wave A–E),
  `resolve_class_mechanic` sceglie la build dai tag equip e concede
  +1 base +2 risonanza. Consumato da `expeditions/services.py`
  (`class_item_resonance_bonus` per membro → `formulas.py` team power →
  `report_builder.py`).
- `class_halls/build_lab.py` + route `GET /{hall_id}/build-lab` (UI
  Build Lab), `build_reachability.py` (audit 81 build raggiungibili).
- `admin/tester_journey.py`: analytics di tuning per-build (T8),
  reset/journey checks che contano build e risonanza.
→ **RIMOSSO** il concetto di build. La meccanica di classe resta ma
  senza selezione: risonanza = equip allineato ai tag della PROPRIA
  classe (armor/weapon tags del registry), bonus e counter_tags
  invariati come grandezza. Nessuna scelta player.

### 3.3 Backend — altri consumer
- `equipment/compatibility.py`: ramo 4a `specialization_unlocks` /
  `specialization_match|mismatch|required` → rimosso; restano i check di
  classe (heavy armour, arcane, class_tags/recommended).
- `dungeons/preview.py` + `expeditions/threats.py`: counter_tags da
  `class_specializations`+spec → ora da `CLASS_MECHANICS[class].counter_tags`
  (via classe, sempre attivi per classe assegnata).
- `adventurers/services.py` (payload `specialization_slug` → rimosso),
  `adventurers/routes.py` (filtri `?spec=`), `adventurers/retire.py`.
- `items/final_catalog.py` + `training/catalog.py`:
  `spec_signature_*` item (10) → legacy da rimuovere in 9M.
- `contracts/catalog.py`: contratti che citano spec → riformulati su
  classi/ruoli.
- Script storici `round160_*`, `refund_failed_specializations`,
  `round18_*`: NON toccati (storia sigillata), esclusi dal runtime.

### 3.4 DB fields coinvolti (migration 9M)
| Collection | Campo | Azione |
|---|---|---|
| `adventurers` | `specialization_slug`, `specialization_respec_count`, `specialization_applied_at` | `$unset` in 9M |
| `class_halls` | `unlocked_specializations` | `$unset` in 9M |
| `class_specializations` | intera collection | drop in 9M (counter_tags migrati nel registry/mechanics) |
| `items` (catalogo+istanze) | `specialization_unlocks`, item `spec_signature_*`, item legacy build-driven | audit + cleanup 9M (`fase9_old_item_cleanup`) |
| `adventurer_classes` | `role` legacy (Support/Hybrid/Utility) | il runtime ignora il campo: fa fede il registry |

### 3.5 Frontend
- `components/SpecializationBadge.jsx` (SpecChip + SpecializationPanel):
  usato da AdventurerDetailModal, Adventurers, RosterManage,
  PvpBattleReport → rimosso.
- `components/RespecModal.jsx`, sezioni spec di `pages/Training.jsx` →
  rimossi (Training riscritta in 9I).
- `components/ClassHallBuildLab.jsx` + sezioni build in
  `pages/ClassHalls.jsx` → rimossi (redesign 9F).
- `utils/displayLabels.specLabel`, i18n `specialization.*` → rimossi.
- Guida: `ClassesAndStatsSection.jsx`, `R16GuideSections.jsx` → riscritti
  su CLASSE → RUOLO.
- Filtri roster `spec`/`no_spec` → sostituiti da filtro ruolo.
- **NON toccato**: `GuildSpecialization*` (specializzazione DI GILDA,
  ROUND 16.3 Phase 6 — concetto diverso e vivo) e
  `SpecializationMiniCard` (mini-card di quella feature).

### 3.6 Test e telemetry
- Test integration esistenti su spec/build (round6c/6e, round160 phase2,
  T8 tuning): restano nel repo come storia; quelli attivi che
  contraddicono il nuovo contratto vengono aggiornati solo se fanno
  parte della suite runtime (i sealed R18 non si toccano).
- Telemetry/audit: eventi `specialization_*` restano nel log storico;
  nessun nuovo emit.
- Nuovi test 9N: 27/27 ruoli canonici (13/6/8), 0 endpoint spec/build,
  compat equip senza ramo spec, threats via classe.

## 4. Nuovo modello equipment (9D)

Gli item NON richiedono build. Un item di classe dichiara:
`item_class` (slug registry) oppure resta generico di ruolo/universale.
Gli effetti rafforzano il ruolo della classe usando le statistiche REALI
del runtime (`strength/agility/intellect/endurance/faith` +
`*_bonus` slot equip); il mapping ruolo→stat pesa:
- DPS → primary stat della classe (danno/crit narrativi nel lore);
- TANK → `endurance` (+ mitigazione narrativa);
- HEALER → `faith`/`intellect` (+ supporto narrativo).
La compatibilità resta data-driven su `class_tags`/`armor_tags`/
`weapon_tags` del registry, senza `specialization_unlocks`.

## 5. Set raid (9E)

27 classi × 4 raid = **108 set**, generati in
`app/raids/class_sets.py` (catalogo puro) con: `set_id`
(`set_{raid}_{class}`), nome IT, lore legato al tema del raid, 5 pezzi
sugli slot canonici (`weapon, chest, legs, head, accessory`), livello e
budget stat crescenti per tier raid (T1 moonfall-vigil Lv40 → T4 Lv80),
bonus set 3-pezzi (parziale) e 5-pezzi (completo) espressi su stat reali
allineate al ruolo, `source = raid:<slug>`, rarità epic→legendary per
tier. Documentazione generata: `memory/fase9_raid_sets_catalog.md`.

## 6. Class Hall redesign (9F) e identità visiva (9G)

- Pagina Hall: header con emblema/nome/ruolo/identità + corpo con prova,
  stile di combattimento, punti di forza, equip di classe, progressione,
  set raid. NIENTE spec/build/Build Lab/81 build.
- 27 emblemi SVG unici (`frontend/public/assets/classes/{slug}.svg`) +
  card/banner, generati da `scripts/fase9_genera_emblemi_classi.py` con
  simboli distintivi per classe (identity map nel manifest asset).

## 7. Traits (9H)

Player-facing rimossi da Guida e Avventurieri. Il runtime resta finché
attivo: audit in 9H stabilisce se `TRAIT_RUNTIME_STILL_ACTIVE` (atteso:
sì — counter_tags trait nel sistema minacce, moltiplicatori XP) e lo
riporta nel report finale: nessun modificatore invisibile non
documentato.

## 8. Ordine di implementazione e commit

Un commit per macro-fase (9A già `06129f8`): 9B registry+ruoli →
9C rimozione spec/build → 9D equipment → 9E set raid → 9F/9G Hall+visual
→ 9H traits → 9I training → 9J sigillo XP → 9K/9L banner+dashboard →
9M migration/cleanup (`fase9_old_item_cleanup` dry-run/--apply,
idempotente, fail-closed) → 9N test+report+push.

Il cleanup distruttivo degli item vecchi avviene SOLO dopo che il nuovo
catalogo è pronto e verificato, e MAI automaticamente in produzione.

## 9. Backlog (futuro, NON in questa tranche)

- **SLOT DI CLASSE**: un unico slot per innesti ibridi controllati
  (es. "Sigillo di Ruolo secondario"), agganciato al registry tramite
  `hybrid_slot`; richiederà: campo item dedicato, validatore equip,
  cap di potenza, UI Hall. Registrato in `memory/backlog.md`.
