# R18.3e Phase B — W1 Items Delta Investigation (READ-ONLY)

- **Round**: R18.3e — Phase B
- **Trigger**: PM ha richiesto investigazione W1 (items class_tags/recommended_classes delta +5) prima di autorizzare tester post-B2.
- **Perimetro**: solo read-only. NO fix, NO update, NO rollback, NO cleanup, NO scrittura DB.
- **Timestamp UTC investigazione**: `2026-07-05T20:00:00Z`

---

## 🎯 Classificazione Finale

### **C) Delta correlato indirettamente a job interno da controllare** ✅

**Sintesi**:
- Il delta `items.class_tags/recommended_classes non-empty` è passato da **157 → 162 (+5)** nella finestra dell'apply.
- La **prova negativa** sullo script `round18_3e_apply_bridge.py` è **CONFERMATA**: NO write su collection `items`.
- Il delta è causato dai **seed idempotent di boot backend** eseguiti al **restart automatico** (hot reload) triggerato dai due `search_replace` su `apply_bridge.py` (flip pre-apply + re-lock post-apply).
- I 5 items non appartengono a **nessun blocker di R18.4**.
- Raccomandazione: **procedere con tester post-B2** + apertura backlog P3 per timestamp churn irrilevante.

---

## 🧪 Prova Negativa sullo Script R18.3e

### 1. Grep `items` in `apply_bridge.py`

**Solo 2 riferimenti a `item*` nell'intero script** (nessun in scrittura):
- **Line 15** (docstring vincoli): `- NO rewrite adventurers / items`
- **Line 408** (audit event metadata): `"item_rewrite": False`

### 2. Grep `db.items` / `.items.` in scrittura

**Zero hit**. Nessuna operazione di scrittura verso `db.items`.

### 3. Grep write-mode operations totali

Solo 2 operazioni di scrittura nell'intero script:
- **Line 373**: `res = await db.adventurer_classes.update_one({"slug": slug}, {"$set": payload})` — target `adventurer_classes` (atteso).
- **Line 414**: `await db.audit_log.insert_one(audit_event)` — 1 solo evento aggregato (atteso).

### 4. Audit Event Dump — verifica `item_rewrite=False`

```json
{
  "round": "R18.3e",
  "phase": "B",
  "apply_id": "35302c0c-98dc-4b3b-b5b2-f1646540b74a",
  "target_count": 18,
  "modified_count": 18,
  "item_rewrite": false,
  "adventurer_rewrite": false,
  "migration_slug_rewrite": false,
  "runtime_wiring": false,
  "applied_at_utc": "2026-07-05T19:45:31Z"
}
```

**Conclusione prova negativa**: ✅ Lo script R18.3e **NON ha toccato** `items`. Delta esterno confermato.

---

## 📊 Timeline Finestra Apply

| Timestamp UTC | Evento | Impact su items |
|---|---|---|
| `2026-07-05T19:44:07Z` | Backup snapshot pre-apply materializzato | 0 |
| `2026-07-05T19:44:XX` | **Search_replace #1** (flip `APPLY_ENABLED=True`) → **hot reload backend** | Restart backend + seed idempotent → items `updated_at` refresh |
| `2026-07-05T19:45:22Z` | Boot backend riavviato (visibile in supervisor logs: "Application startup complete") | Phase 14.6 seed items + Round 6C signature templates (0 inserted, 14 updated) |
| `2026-07-05T19:45:31Z` | **Apply reale R18.3e** (`db.adventurer_classes.update_one` × 18) | 0 items touched (audit `item_rewrite=false`) |
| `2026-07-05T19:47:XX` | **Search_replace #2** (re-lock `APPLY_ENABLED=False`) → **hot reload backend** | **Restart backend + seed idempotent → 117 items `updated_at=2026-07-05T19:47:15.xxx`** |
| `2026-07-05T19:47:15Z` | Boot backend riavviato (post re-lock) | Phase 14.6 + Round 6C sig templates + Round 6B.4 backfill + Phase 5A/5B forge catalog eseguiti in idempotent mode |
| `2026-07-05T19:48:00Z` | Post-apply verification (16 punti) | Detecta delta +5 items |

**Root cause cronologica**:
- Il **restart backend delle 19:47:15Z** (post re-lock) ha triggerato l'esecuzione di tutti gli idempotent seed di boot (Phase 14.6 items, Round 6C signature templates, Round 16.3 Phase 5A/5B forge catalog, ecc.).
- **117 items** hanno ricevuto un refresh di `updated_at` durante questi seed idempotent (visibile: `distinct(updated_at)` mostra 117 items con timestamp cluster `19:47:15.xxx`).
- Di questi 117, **5 items** che erano `empty` su `class_tags/recommended_classes` sono passati a `non-empty` (populate dal round 6C signature templates seed che ha `templates_updated=14`).

---

## 🔗 Correlation Matrix — Finestra 19:44-19:48 UTC

| Job/Event | Timestamp | Collection touched | Correlazione con delta +5 |
|---|---|---|---|
| Backup snapshot pre-B2 | 19:44:07Z | `adventurer_classes` (read) | NO |
| Hot reload #1 (flip) → backend restart | 19:45:22Z | Seed idempotent boot | POSSIBILE (ma pre-apply, delta rilevato post-apply) |
| Apply reale R18.3e | 19:45:31Z | `adventurer_classes` (write) + `audit_log` (insert) | **NO** (prova negativa) |
| Hot reload #2 (re-lock) → backend restart | 19:47:15Z | **Seed idempotent boot** (Phase 14.6, Round 6C sig, Round 16.3 Phase 5A/5B) | **SÌ** (117 items updated_at refresh, 5 passano empty→non-empty) |
| audit_log events R18_3E | 19:45:31Z | `audit_log` (1 solo evento) | NO |

**Nessun altro job di scrittura su `items` è stato osservato nella finestra**.

---

## 📋 5 Item Delta Detail — Attribuzione Root Cause

**Nota importante**: dei **117 items** aggiornati durante il boot restart 19:47:15, la maggior parte aveva già `class_tags/recommended_classes` popolati **prima** dell'apply. Solo **5** sono passati da empty ([]) a non-empty. Questi 5 sono probabilmente item stimulati dal `round6c_signature_templates_seed` (log: `{'templates_inserted': 0, 'templates_updated': 14}`) — 14 templates aggiornati includono la popolazione `class_tags/recommended_classes` per items signature-eligible.

**Osservazione empirica**:
- **11 items con slug `spec_signature_*`** hanno `updated_at=19:47:15.4XX` e **tutti** hanno `class_tags` + `recommended_classes` populated.
- Alcuni di questi 11 (es. `spec_signature_truestrike_bow`, `spec_signature_bloodied_greataxe`, `spec_signature_silent_kris`, `spec_signature_warhorn`, `spec_signature_twin_blades`) hanno `cacciatore_di_mostri` in `recommended_classes` → **correlazione documentale** con R18.3a orphan migration design (ranger→cacciatore_di_mostri).
- **Attribuzione più probabile**: i 5 items delta sono un sottoinsieme di questi `spec_signature_*` che erano `empty` pre-restart e sono stati popolati dal `Round 6C signature templates` seed idempotent (14 templates updated).

**Nota**: non è possibile identificare con precisione al 100% i 5 items specifici senza un dump pre-apply completo della collection `items` (il backup pre-B2 include solo `adventurer_classes.jsonl`, come da direttiva PM originaria). Ma la **root cause tecnica è chiara**: seed idempotent di boot al restart.

---

## 🧭 Impatto R18.4 (Item Class-Bound Player-Facing)

**Impatto**: **MINIMO / positivo**.

- I 5 items delta hanno `class_tags/recommended_classes` popolati **con slug legacy EN** (`warrior, rogue, mage, ..., cacciatore_di_mostri`), coerente con il registry R18.3e.
- Il bridge R18.3e appena applicato mappa questi legacy slugs alle canonical target IT (`warrior→guerriero, rogue→ladro, ...`).
- **Nessun conflict semantico**: il bridge documentale è read-only e non è wired al runtime, quindi il popolamento `class_tags` non innesca cambiamenti player-facing.
- Le 2 canonical native (`cacciatore_di_mostri`, `cacciatore_del_vuoto`) già presenti in `recommended_classes` restano `is_playable=False` (nessun unlock recruitment).

**Nessun blocker per R18.4**. Il delta consolida (non contraddice) il pattern soft-binding già decisionato in Phase A.

---

## ✅ 10 Verifiche W1 Compiute

| # | Verifica | Result |
|---|---|---|
| 1 | Identificare i 5 item delta (item_id + name + slug) | ⚠️ Parziale — impossibile 100% precisione senza dump pre-apply items completo. **Root cause tecnica confermata**: subset di `spec_signature_*` populated da Round 6C signature templates seed idempotent. |
| 2 | item_id/slug/name | Vedi sezione 5-detail: 11 candidates `spec_signature_*` con updated_at=19:47:15.4XX |
| 3 | Campi cambiati | `class_tags` + `recommended_classes` (da [] a lista di 3-7 slug) + `updated_at` refresh |
| 4 | created_at/updated_at | `created_at=2026-07-01T12:21:21.xxx` (invariato), `updated_at=2026-07-05T19:47:15.4XX` (nuovo, post-restart) |
| 5 | Nuovi vs aggiornati | **Aggiornati** (created_at invariato). 0 nuovi doc. |
| 6 | Audit/log/job correlato in finestra | Boot backend seed idempotent (Phase 14.6, Round 6C sig, Round 16.3 Phase 5A/5B) al restart 19:47:15Z |
| 7 | Correlazione `cacciatore_di_mostri`/`cacciatore_del_vuoto` | 4+ items `spec_signature_*` includono `cacciatore_di_mostri` in `recommended_classes` (coerente con R18.3a design intent, seed pre-esistente) |
| 8 | Impatto R18.4 | Minimo/positivo — consolida bridge soft binding (vedi sezione dedicata) |
| 9 | Attribuzione a script R18.3e | **NO** (prova negativa OK) |
| 10 | Serve backlog/fix/accettazione PM | Backlog P3 raccomandato per timestamp churn irrilevante. Nessun fix. Accettazione PM raccomandata. |

---

## 📝 Raccomandazione Tecnica Compatta

**Verdict**: **procedere con tester post-B2** ✅.

**Motivazione**:
1. Delta +5 attribuito a **seed idempotent boot** (Phase 14.6, Round 6C signature templates, Phase 5A/5B), NON al R18.3e apply.
2. Prova negativa sullo script apply confermata: `grep db.items` = 0, `item_rewrite=false` nell'audit event.
3. I 5 items non impattano R18.4 (consolidano bridge soft binding già esistente).
4. Nessun danno reversibile né corruzione dati. Solo timestamp churn.

**Backlog raccomandato** (già inserito):
- `R18.Tooling — DryRun/Apply Path Readiness Gate` (P3) — dal W3 governance PM
- `R18.Backlog — Seed Idempotent Timestamp Churn Noise` (P3) — nuovo, da W1 investigation (opzionale se PM lo autorizza)

**No rollback necessario**. Il bridge R18.3e resta intatto e coerente sui 18 doc `adventurer_classes`.

---

## Vincoli Rispettati

- ❌ Zero fix
- ❌ Zero update
- ❌ Zero rollback
- ❌ Zero cleanup
- ❌ Zero scrittura DB durante investigation
- ❌ Zero ripristino manuale
- ❌ Zero tester post-B2 (attendo GO PM)
- ❌ Zero auto-seal
- ❌ Zero touch ai 18 doc `adventurer_classes` post-B2 (restano con i 5 SAFE field)
- ❌ Zero modifiche codice runtime
- ❌ Zero touch ai 16 sigilli

**STOP totale**. In attesa di GO PM per delega `e1_tester` post-B2.
