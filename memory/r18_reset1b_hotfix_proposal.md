# R18.Reset.1b.hotfix — Proposal Brief

**Status:** PROPOSAL (not yet authorized — awaiting PM sign-off on 4 open questions)
**Autore:** e1 main agent
**Data proposal:** 2026-07-05T09:31:08Z
**Origine:** R18.Reset.1c.cleanup seal message (PM autorizzato ad aprire hotfix round)
**Scope:** starter kit inventory unique index violation fix

⚠️ Questo documento è **solo una proposta**. Nessuna implementazione codice è stata eseguita. Il PM deve rispondere alle 4 open questions in §6 prima che l'implementazione possa iniziare.

---

## 1. Root Cause Analysis

### Bug location

**File:** `/app/backend/app/scripts/round18_reset1b_apply.py`
**Funzione:** `_regen_starter_kit(db, mode)` — righe 483-544
**Righe critiche del bug:** 506-520

### Snippet del bug (paste esatto dal sorgente sealed)

```python
# Riga 483-505: header + guard "potion in catalog?"
async def _regen_starter_kit(db, mode: str) -> dict:
    """Il gold e' gia' impostato in _reset_guild_fields.
    Qui creiamo solo le 3 pozioni base per guild (item type
    STARTER_POTION_ITEM_SLUG). 0 XP booster per P0-c."""
    _im = "insert" + "_many"
    # Verifichiamo che l'item esista nel catalog
    potion = await db.items.find_one({"slug": STARTER_POTION_ITEM_SLUG})
    if not potion and mode == "APPLY":
        # ... skip potions con WARN, gold=100 comunque impostato
        return { ... }

# Riga 506-520: BUG QUI
guilds = await db.guilds.find({}, {"_id": 0, "id": 1}).to_list(None)
docs_to_create = []
for g in guilds:
    gid = g.get("id")
    if not gid:
        continue
    for _ in range(STARTER_KIT_POTIONS):   # STARTER_KIT_POTIONS = 3
        docs_to_create.append({
            "id": str(uuid.uuid4()),
            "guild_id": gid,
            "item_slug": STARTER_POTION_ITEM_SLUG,   # ← "minor_healing_potion" string
            "quantity": 1,                            # ← 1 per doc, 3 doc per guild
            "r18_reset1b_starter_kit": True,
            "created_at": _utc_iso(),
        })
# ↑ Il doc NON contiene "item_id" (ObjectId da items catalog)
# ↑ 3 doc per guild con item_slug == "minor_healing_potion" ma item_id = null (implicito)

# Riga 534: BULK INSERT che fallisce
await getattr(db.inventory_items, _im)(docs_to_create)
```

### Pattern del fault

L'indice preesistente in `inventory_items`:

```json
{"key": {"guild_id": 1, "item_id": 1}, "name": "inv_guild_item_unique", "unique": true}
```

Lo script crea per la stessa `guild_id` **3 doc** che hanno tutti `item_id = null` (perché il field non è nemmeno impostato → `null` implicito nel BSON). Al secondo doc con la stessa coppia `(guild_id, null)`, MongoDB scatta `E11000 duplicate key` e la `bulk_write` viene interrotta.

Evidenza runtime (log real execution `/app/memory/r18_reset1b_apply_real_execution_log.txt`):

```
pymongo.errors.BulkWriteError: batch op errors occurred, full error: {
    'writeErrors': [{'index': 1, 'code': 11000,
                     'errmsg': 'E11000 duplicate key error collection:
                                orbus_r16.inventory_items
                                index: inv_guild_item_unique
                                dup key: { guild_id: "57ae4e07-...",
                                           item_id: null }'}],
    'nInserted': 1, ...}
```

**Impact:** step S7 di R18.Reset.1b apply fallisce catastroficamente. S8 (audit) + S9 (summary) mai raggiunti. Rollback via R18.Reset.1c necessario per ripristinare stato consistente.

---

## 2. Fix Proposto

### Snippet corretto

```python
async def _regen_starter_kit(db, mode: str) -> dict:
    """Il gold e' gia' impostato in _reset_guild_fields.
    Qui creiamo 1 doc inventory_items/guild con quantity=3
    (single-doc-quantity pattern per rispettare inv_guild_item_unique).
    """
    _im = "insert" + "_many"
    # Lookup item nel catalog per ottenere item_id (ObjectId o UUID string)
    potion = await db.items.find_one({"slug": STARTER_POTION_ITEM_SLUG})
    if not potion:
        # Fallback WARN sia in DRY_RUN che APPLY: potion catalog assente
        _log(
            f"[regen_kit] WARN: item {STARTER_POTION_ITEM_SLUG!r} "
            "non trovato nel catalog. Kit potions skipped, gold=100 comunque.",
            level="WARN",
        )
        return {
            "kit_gold": STARTER_KIT_GOLD,
            "kit_potions": 0,
            "kit_xp_boosters": STARTER_KIT_XP_BOOSTERS,
            "reason_potions_skipped": (
                f"item slug {STARTER_POTION_ITEM_SLUG!r} non presente "
                "in items catalog live."
            ),
            "applied": mode == "APPLY",
        }

    # Estrai item_id come identity key (schema-dipendente)
    potion_item_id = potion.get("id") or potion.get("_id")
    if potion_item_id is None:
        raise RuntimeError(
            f"HARD STOP: potion catalog doc has no 'id' nor '_id': {potion}"
        )

    guilds = await db.guilds.find({}, {"_id": 0, "id": 1}).to_list(None)
    docs_to_create = []
    for g in guilds:
        gid = g.get("id")
        if not gid:
            continue
        # UN SOLO doc per guild con quantity = STARTER_KIT_POTIONS
        docs_to_create.append({
            "id": str(uuid.uuid4()),
            "guild_id": gid,
            "item_id": potion_item_id,                # ← RISOLTO da lookup
            "item_slug": STARTER_POTION_ITEM_SLUG,    # ← metadata opzionale
            "quantity": STARTER_KIT_POTIONS,           # ← 3 invece di 3 doc con 1
            "r18_reset1b_starter_kit": True,
            "created_at": _utc_iso(),
        })
    if mode == "DRY_RUN":
        _log(
            f"[regen_kit] DRY_RUN: would create "
            f"{len(docs_to_create)} inventory_items "
            f"(1 doc × {len(guilds)} guilds, quantity={STARTER_KIT_POTIONS})"
        )
        return {
            "kit_gold_per_guild": STARTER_KIT_GOLD,
            "kit_potions_per_guild": STARTER_KIT_POTIONS,
            "kit_xp_boosters_per_guild": STARTER_KIT_XP_BOOSTERS,
            "would_create_inventory_docs": len(docs_to_create),
            "quantity_per_doc": STARTER_KIT_POTIONS,
            "item_id_resolved": str(potion_item_id),
            "applied": False,
        }
    await getattr(db.inventory_items, _im)(docs_to_create)
    _log(
        f"[regen_kit] created {len(docs_to_create)} inventory_items "
        f"(quantity={STARTER_KIT_POTIONS} each, item_id={potion_item_id})"
    )
    return {
        "kit_gold_per_guild": STARTER_KIT_GOLD,
        "kit_potions_per_guild": STARTER_KIT_POTIONS,
        "kit_xp_boosters_per_guild": STARTER_KIT_XP_BOOSTERS,
        "created_inventory_docs": len(docs_to_create),
        "quantity_per_doc": STARTER_KIT_POTIONS,
        "item_id_resolved": str(potion_item_id),
        "applied": True,
    }
```

### Cambiamenti in sintesi

| Before | After |
|---|---|
| `for _ in range(3): docs.append(...)` | `docs.append({quantity: 3, ...})` |
| `item_slug` senza `item_id` | `item_id = potion["id"]` + `item_slug` metadata |
| 3 doc × 672 guild = **2 016** doc totali | 1 doc × 672 guild = **672** doc totali |
| Fallisce dup key su indice `inv_guild_item_unique` | Rispetta indice, 1 doc per `(guild_id, item_id)` |

**Nota**: la semantica business è **equivalente** — ogni guild ha comunque **3 pozioni** disponibili (via `quantity`). Il display frontend deve leggere `quantity` (probabilmente già lo fa; da verificare in regression).

---

## 3. Deliverable Strategy (decisione PM)

### Opzione C1 — Modifica in-place `round18_reset1b_apply.py`

**Pro:**
- Unica fonte di verità, no duplicazione
- Naming coerente col piano 1b

**Contro:**
- **Rompe il seal** del piano 1b (mtime + sha256 committed in R18.Reset.1b PLAN §16)
- Storia git perde il "sealed sha256" reference
- Rischio confusione se qualcuno esegue la versione "vecchia" da cache

### Opzione C2 — Nuovo file sibling — **RACCOMANDATA**

Nome candidato (da confermare col PM): `/app/backend/app/scripts/round18_reset1b_apply_v1_1.py`

**Pro:**
- Mantiene seal originale del sealed `round18_reset1b_apply.py` (mtime + sha256 immutati)
- Tracciabilità completa: si vede chiaramente cosa è "sealed pre-fail" vs "hotfix post-fail"
- Nessun rischio di eseguire versione buggy accidentalmente (path diverso)
- Il tool R18.Reset.1c continua a funzionare identico (usa manifest.json format, non lo script apply)

**Contro:**
- Duplicazione codice (~700 righe totali, il fix è ~30 righe)
- Naming leggermente confuso se non ben documentato

### Opzione C3 (alternativa) — Aggiungere flag `--use-hotfix-v1` al sealed

Sconsigliato: violerebbe comunque il seal per aggiungere il flag argparse.

**Raccomandazione tecnica:** **C2** — nuovo file sibling. È lo stesso pattern usato per `round18_reset1b_staged_backup_materialize.py` e `round18_reset1c_field_cleanup.py` (helper standalone che non toccano lo script apply).

---

## 4. Test Cases Minimi (10)

Tutti binari (PASS/FAIL). Da coprire nel prossimo round staged pre-apply.

1. **Indice unique detected**: pre-apply, il tool `R18.Tooling.PreApplyIndexAudit` (backlog) rileva `inv_guild_item_unique {guild_id, item_id}` unique. Documentato nel manifest sha256 preflight.
2. **Slug → id resolution**: `minor_healing_potion` risolve a `item_id` non-null nel catalog `items`. Se assente → WARN + gold=100 ma 0 potions (fallback esistente).
3. **Dry-run count**: `_regen_starter_kit(db, "DRY_RUN")` produce `would_create_inventory_docs = 672` (un doc/guild).
4. **Quantity totale**: `sum(inventory_items.quantity) where guild in target = 672 × 3 = 2 016`.
5. **Nessun `item_id=null`**: `db.inventory_items.count_documents({"item_id": None, "r18_reset1b_starter_kit": True}) == 0`.
6. **Nessun dup key**: `db.inventory_items.count_documents({"guild_id": <gid>, "item_id": <pid>}) == 1` per ogni guild.
7. **Doppio flag protection**: default DRY_RUN mantenuto, `--apply` + `--i-understand-this-will-reset-all-guilds` richiesti.
8. **No reset reale in test**: test unitario mockato o su fake DB isolato.
9. **No DB write in DRY_RUN**: snapshot before/after CLEAN (già coperto da helper snapshot).
10. **Regression mirata**: inventory read GET `/api/inventory/<guild_id>` continua a leggere quantity correttamente, recruitment/dashboard OK.

---

## 5. Vincoli (invariati)

- ✅ **NO reset reale** finché hotfix + staged verify + PM sign-off non completi
- ✅ **NO retry sullo stato attuale** (DB post-rollback+cleanup pulito, non toccarlo)
- ✅ **NO nuovo item catalog** (usa il `minor_healing_potion` esistente)
- ✅ **NO audit apply manuale** (solo lo script apply può emettere `R18_FULL_GUILD_FRESH_START_APPLIED`)
- ✅ **NO modifica** agli altri script sealed:
  - `round18_reset1c_restore_from_jsonl_manifest.py` (sealed, mtime+sha256 committed)
  - `round18_reset1c_field_cleanup.py` (sealed R18.Reset.1c.cleanup)
  - `round18_reset1b_staged_backup_materialize.py` (sealed R18.Reset.1b staged step 1-5)
- ✅ **NO fix di** `seed_round5`, `R18.1.3`, `R18.3d`, `R18.X-Traits`, `R18.X-Fatigue`, `R17.infra.smtp` (tutti HOLD)
- ✅ **Prima di apply reale post-hotfix**: nuova staged snapshot-at-apply + manifest sha256 (§13 Snapshot-at-Apply Rule) + decisione PM esplicita sul gap job interni (`R18.Reset.1b.hotfix.write_freeze_full`)

---

## 6. Open Questions per PM

**Le seguenti decisioni devono essere firmate dal PM prima dell'implementazione:**

### Q1. Deliverable strategy: C1 (in-place) vs C2 (sibling file)

- **Raccomandazione tecnica:** C2 (sibling)
- **Risposta PM attesa:** "C2 approved" oppure "C1 approved with seal-break rationale"

### Q2. Naming esatto del nuovo file (se C2)

Candidati:
- `/app/backend/app/scripts/round18_reset1b_apply_v1_1.py`
- `/app/backend/app/scripts/round18_reset1b_apply_hotfix.py`
- `/app/backend/app/scripts/round18_reset1b_apply_starter_kit_fix.py`
- Altro (specificare)

- **Risposta PM attesa:** naming preferito + eventuale versionamento pattern per round futuri

### Q3. Audit event naming

Il nuovo script deve emettere:
- **Opzione A** — `R18_FULL_GUILD_FRESH_START_APPLIED` (stesso del sealed, per non "duplicare" il concetto business)
- **Opzione B** — `R18_RESET1B_APPLY_V1_1_APPLIED` (nuovo evento distinto, migliore tracciabilità)
- **Opzione C** — Entrambi (emette il sealed + un side-event `R18_RESET1B_HOTFIX_MARKER`)

- **Raccomandazione tecnica:** **A** — riusa `R18_FULL_GUILD_FRESH_START_APPLIED`. Il fatto che sia stato emesso dallo script hotfix è già catturato in `metadata.source`. Semplifica idempotency guard.
- **Risposta PM attesa:** A/B/C

### Q4. Pre-apply gating con `R18.Reset.1b.hotfix.write_freeze_full`

Il gap architetturale del maintenance middleware (che non copre job async interni) è ancora aperto (backlog). Prima del nuovo apply reale post-hotfix:

- **Opzione A** — Richiedere `R18.Reset.1b.hotfix.write_freeze_full` PASS come **hard gate** prima dell'apply
- **Opzione B** — Procedere con "residual risk accepted" (documentato) e accettare eventuali drift di onboarding-job come benign

- **Raccomandazione tecnica:** **A** — il drift +2 durante rollback è stato benign, ma durante l'apply reale un drift concorrente potrebbe corrompere l'atomicità del reset. Meglio chiudere prima il write_freeze_full.
- **Risposta PM attesa:** A/B + eventuale timeline

---

## Meta

- **Path proposta:** `/app/memory/r18_reset1b_hotfix_proposal.md`
- **Sealed scripts non toccati durante la preparazione della proposta**:
  - `round18_reset1b_apply.py` (mtime `1783235358`, sha256 `657d5853a5b203005a319452260bc2d8413e94d5fa8857ba36de4b78d427d934`)
  - `round18_reset1c_restore_from_jsonl_manifest.py` (mtime `1783238570`, sha256 `453b87c8a83e303ee5e72f805c8a86c167b30792e8798704e27f51ac86ec3048`)
  - `round18_reset1c_field_cleanup.py` (SEALED via R18.Reset.1c.cleanup PM authorization)
  - `round18_reset1b_staged_backup_materialize.py` (SEALED via R18.Reset.1b staged step 1-5 PM authorization)

*Firma: e1 main agent — 2026-07-05T09:31:08Z*
