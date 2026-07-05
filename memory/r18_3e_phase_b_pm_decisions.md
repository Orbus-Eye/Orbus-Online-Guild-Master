# R18.3e Phase B — PM Decision Lock (B0)

- **Round**: R18.3e — Canonical IT ↔ Legacy EN Class Bridge — Phase B
- **Stage**: B0 (Decision Lock, blocker per B1/B2)
- **Timestamp UTC**: `2026-07-05T18:39:19Z`
- **Seal Authority**: PM Orchestrator
- **Reference discovery**: `/app/memory/r18_3e_phase_a_legacy_canonical_bridge_discovery.md` (Phase A report)
- **Deviation policy**: qualsiasi cambiamento a Q1-Q14 richiede nuovo gate PM.

---

## 14 Risposte PM (verbatim)

### Q1 — canonical_slug vs alias_target?
**Risposta**: **Entrambi**.
- `canonical_slug` = target canonico IT di riferimento.
- `alias_target` = solo per alias legacy/deprecati che dovranno essere trattati come alias espliciti in futuro.
- `bridge_status` determina come interpretarli.

### Q2 — Bridge in adventurer_classes docs, registry file, o entrambi?
**Risposta**: **(c) Entrambi ma STAGED**.
- `r18_3e_bridge_registry.json` = source documentale di design.
- `adventurer_classes` = eventuale reflection append-only, **SOLO dopo dry-run + nuovo gate PM**.
- Per ora autorizzato SOLO: registry file + loader UNWIRED + dry-run dello script `$set`.

### Q3 — priest?
**Risposta**: **(c) `priest → paladino` deprecated_alias_target**.
- Non aggiungere `sacerdote` al canonical set.
- Non rinominare `priest`.
- Non cambiare `display_name_it="Sacerdote"` ora.
- Bridge documentale: `priest.canonical_slug=paladino`, `bridge_status=mapped_alias`.
- Player continua a vedere "Sacerdote" fino a round UI dedicato.

### Q4 — assassin?
**Risposta**: **(a) `assassin → ladro` deprecated_alias**. No migration.

### Q5 — berserker?
**Risposta**: **(a) `berserker → guerriero` deprecated_alias**. NO rewrite `items.class_tags`.

### Q6 — ranger/warlock?
**Risposta**: `ranger → cacciatore_di_mostri` / `warlock → cacciatore_del_vuoto` con `bridge_status=mapped_alias`.
Vincoli: no migration slug, no unlock recruitment, no cambio `display_name_it`, no cambio label player-facing.
Il bridge è design mapping puro.

### Q7 — recruit_unassigned?
**Risposta**: **(a) Escluso dal canonical bridge**.
- `bridge_status = technical_placeholder`
- `canonical_slug = null`
- `alias_target = null`

### Q8 — test-class-5e0064?
**Risposta**: **(a) `bridge_status=test_artifact` permanente**. NO `delete_one`.

### Q9 — R18.4?
**Risposta**: **R18.4 usa bridge documentale/read-only**. NO migration DB completa. NO rewrite `adventurers.class_slug`, frontend slug map, backend runtime assumptions, test fixtures.
Migration completa (se mai) = round separato **R18.3f — Class Slug Migration Planning**.

### Q10 — UI label player-facing?
**Risposta**: **(b) NO UI player-facing**. Bridge admin/design only.
Niente "Occultista→Cacciatore del Vuoto", "Ranger→Cacciatore di Mostri", "Sacerdote→Paladino" in UI.

### Q11 — items.class_tags rewrite?
**Risposta**: **(b) `items.class_tags` resta legacy come chiave**. NO rewrite.
R18.4 potrà leggere bridge documentale per compatibilità futura, senza cambiare tag esistenti.

### Q12 — Bard drift?
**Risposta**: **(a) Bardo drift deferred**. Resta backlog `R18.3d.followup — Bard Role Drift Resolution`.

### Q13 — Audit event?
**Risposta**: **Audit SOLO se DB apply reale futuro**.
- B1 documental-only = **zero audit**.
- Eventuale B2 apply reale futuro = **1 solo evento aggregato** `R18_3E_BRIDGE_METADATA_APPLIED` (NO audit per-doc).

### Q14 — Null class_slug backfill?
**Risposta**: **(b) `class_slug=NULL` fallback runtime continua**. NO backfill in R18.3e.
Aggiungi backlog `R18.Backlog — Null Adventurer Class Slug Backfill Review` (P3, non-blocking).

---

## Mapping Bridge Ufficiale (verbatim, LOCKED)

```
warrior            → guerriero              [mapped_canonical]
rogue              → ladro                  [mapped_canonical]
mage               → mago                   [mapped_canonical]
priest             → paladino               [mapped_alias]  (deprecated_alias semantic)
ranger             → cacciatore_di_mostri   [mapped_alias]  (canonical hidden)
monk               → monaco                 [mapped_canonical]
paladin            → paladino               [mapped_canonical]
druid              → druido                 [mapped_canonical]
alchemist          → alchimista             [mapped_canonical]
bard               → bardo                  [mapped_canonical]
warlock            → cacciatore_del_vuoto   [mapped_alias]  (canonical hidden)
necromancer        → negromante             [mapped_canonical]
assassin           → ladro                  [deprecated_alias]  (0 adv live)
berserker          → guerriero              [deprecated_alias]  (0 adv live)
recruit_unassigned → null                   [technical_placeholder]
test-class-5e0064  → null                   [test_artifact]
```

**Note PM**:
- `priest` e `paladin` possono entrambi puntare a `paladino` (semantica alias).
- `ranger`/`warlock` puntano a canonical hidden **senza modificarne visibilità**.
- `recruit_unassigned` e `test-class-5e0064` **non sono canoniche**.

**Note main agent (per canonical hidden `cacciatore_di_mostri` / `cacciatore_del_vuoto`)**:
Il PM non ha esplicitato lo status di queste 2 classi canonical native già presenti nel DB.
Raccomandazione applicata (documentata, richiede validazione PM al gate B2 apply):
- `cacciatore_di_mostri.bridge_status = canonical_native`, `canonical_slug = cacciatore_di_mostri` (self), `alias_target = null`.
- `cacciatore_del_vuoto.bridge_status = canonical_native`, `canonical_slug = cacciatore_del_vuoto` (self), `alias_target = null`.
Questa scelta rende il registry auto-descrittivo per i 18 doc live e chiarisce che le hidden sono target legittimi, non alias.

---

## Vincoli Assoluti (LOCKED per Phase B)

- ❌ NO DB apply reale (bridge metadata)
- ❌ NO migration `class_slug`
- ❌ NO rewrite `adventurers`
- ❌ NO rewrite `items`
- ❌ NO modifica frontend label player-facing
- ❌ NO unlock classi hidden
- ❌ NO seed nuove classi
- ❌ NO hard delete
- ❌ NO audit event emesso in B0/B1/B2 dry-run
- ❌ NO touch ai **16 sigilli** (14 R18.Reset.1b/1.2/1c + 2 R18.3d Phase B) — byte-identici obbligatori

---

## Self-hash Decision Lock

Il SHA256 di questo file (post-creazione) è calcolato in `pm_decisions.json.meta.self_hash_sha256`.
