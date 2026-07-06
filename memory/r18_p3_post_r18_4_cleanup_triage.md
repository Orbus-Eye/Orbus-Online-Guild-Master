# R18.P3 — Post-R18.4 Cleanup & Backlog Triage — Phase A

- **Round**: `R18.P3 — Post-R18.4 Cleanup & Backlog Triage`
- **Fase**: A — Triage READ-ONLY di 8 P3 backlog items post-R18.4
- **Executed at UTC**: `2026-07-06T11:40:00Z`
- **Author**: MainAgent (E1)
- **Governance**: **zero DB writes, zero code changes, zero sealed touch** (36 sigilli byte-identical verificati pre/post).

## 1. Purpose

Analizzare i **8 P3 attivi** ereditati da R18.4 + R18.4.followup e classificarli per raccomandazione PM in vista di una Phase B di cleanup "safe fix" o dedicated round. Nessun fix applicato in Phase A: solo audit e proposta.

## 2. Metodologia

- **Read-only audit** su codebase (`grep`, `pytest`, `curl` a endpoint pubblici), collection MongoDB (`find`, no update).
- Nessuna esecuzione di apply script, migration, backfill.
- Nessun test rewrite; solo lettura output test suite esistente.
- Nessuna modifica frontend o backend runtime.
- Sigilli 36/36 verificati byte-identical **prima** e **dopo** la triage.

## 3. Triage per singolo P3

### P3 #1 — R18.4.followup — Shield slot mapping SQ1

- **Backlog ID**: `R18.4.followup — Shield slot mapping (SQ1)`
- **Origine**: R18.4 Phase A discovery (backlog SQ1)
- **Stato attuale**: **aperto — decisione PM richiesta**
- **Analisi tecnica**: catalog live contiene 2 shield attivi:
  - `spec_signature_aegis_of_the_defender` → `item_type=shield`, `slot_type=armor`
  - `spec_signature_thornwood_shield` → `item_type=shield`, `slot_type=armor`
  Il fallback `slot_type ?? item_type` in frontend permette equip normale come armor slot. Nessun bug funzionale attivo. La domanda è: shield deve avere uno slot **dedicato** (`slot_type='shield'`) con nuovo campo `secondary_weapon_slot` o simile, oppure mantenere il collapse in `armor`?
- **Raccomandazione classificazione**: **dedicated round** (richiede decisione PM su schema evolution + eventuale migration + UI changes: 4 slot invece di 3).
- **Rischio**: **medio** (schema change su collection `items`, updates a `equipment/services.py`, UI ridisegno equipment page).
- **Test richiesti** se si passa a fix: T-shield-01 (schema migration idempotency), T-shield-02 (equip flow con nuovo slot), T-shield-03 (retrocompatibilità con equipment attuali).
- **Impatto**: DB (migration slot_type dei 2 shield) + backend (`equipment/services.py`, `equipment/ui_4state.py`) + frontend (nuovo slot in `AdventurerEquipment.jsx`) + test.
- **Sub-questions PM**: 
  - **P3.SQ1.a**: promuovere shield a slot dedicato o mantenere collapse in `armor`?
  - **P3.SQ1.b**: se dedicato, un adventurer può equipaggiare shield **oltre** ad armor+weapon+accessory (4 slot) o è alternativa a weapon (dual-wield)?

---

### P3 #2 — R18.4.backlog — specialization_unlocks dead branch cleanup

- **Backlog ID**: `R18.4.backlog — specialization_unlocks dead branch cleanup (SQ2)`
- **Origine**: R18.4 Phase A discovery (backlog SQ2)
- **Stato attuale**: **aperto — dead code confermato**
- **Analisi tecnica**: query DB `db.classes.find({specialization_unlocks: {$exists: True}})` → **0 documenti**. Il campo `specialization_unlocks` non esiste in nessuna class doc. Il branch di codice che ne dipende (in `backend/app/equipment/compatibility.py` e `backend/app/scripts/round18_4_apply_class_bound_apply.py`) è **dead**.
- **Blocco governance**: `equipment/compatibility.py` è **sealed R18.3e**; `round18_4_apply_class_bound_apply.py` è **sealed R18.4 B4**. **Non è possibile cleanup del branch senza rompere sigilli**.
- **Raccomandazione classificazione**: **defer / keep hold** (il dead code non impatta runtime — è un no-op condizionale — e rimuoverlo richiederebbe un round dedicato per gestire re-seal).
- **Rischio**: **basso** (dead code inerte).
- **Test richiesti**: N/A in Phase B; se dedicated round → T-spec-01 (assert branch never triggered live).
- **Impatto**: solo doc/pulizia futura; nessun impatto runtime.
- **Sub-questions PM**: **P3.SQ2.a**: mantenere il dead branch (accetta debt permanente per preservare sigilli) o schedulare dedicated re-seal round?

---

### P3 #3 — R18.4.backlog — berserker/assassin dormant signature items

- **Backlog ID**: `R18.4.backlog — berserker/assassin dormant signature items (SQ4)`
- **Origine**: R18.4 backlog SQ4
- **Stato attuale**: **aperto — items presenti ma classi dormant**
- **Analisi tecnica**: query DB `db.items.find({recommended_classes: {$in: ['berserker','assassin']}})` → **84 items** con reference a berserker/assassin come `recommended_classes` o `required_class_optional`. Esempi: `drake_slayer_helm`, `drake_slayer_chest`, `drake_slayer_blade`, `goblin_hunter_ring`. Le classi berserker/assassin **non sono attivate** nel gioco (unlock via specialization roadmap futura). I dati sono seed pre-preparati per future unlock.
- **Raccomandazione classificazione**: **defer / keep hold** (comportamento by-design in vista di R18.5+ unlock roadmap). Nessuna azione richiesta finché le classi non vengono attivate.
- **Rischio**: **basso** (dati inerti, non consumati da nessun runtime path).
- **Test richiesti**: N/A. Al momento dell'unlock, R18.5 dovrà verificare che questi 84 items siano correttamente accessibili.
- **Impatto**: nessuno in R18.P3.
- **Sub-questions PM**: nessuna (chiaramente defer).

---

### P3 #4 — R18.4.backlog — Backfill Apply Idempotency Counter Pattern

- **Backlog ID**: `R18.4.backlog — Backfill Apply Idempotency Counter Pattern`
- **Origine**: R18.4 B3 risk note
- **Stato attuale**: **aperto — technical debt su sealed apply scripts**
- **Analisi tecnica**: `round18_4_backfill_slot_type_apply.py` e `round18_4_apply_class_bound_apply.py` (entrambi **sealed R18.4 B4**) usano un audit_event per tracciare l'esecuzione, ma **mancano counter espliciti** tipo `already_present_skip`, `no_change_delta_count`. In re-run idempotente non c'è log strutturato dell'idempotency ratio, solo l'audit event con il conteggio delta. Debito tecnico non-blocking.
- **Blocco governance**: entrambi gli script sono **sealed** — non modificabili senza re-seal round.
- **Raccomandazione classificazione**: **defer / keep hold** (o **dedicated round** se PM vuole pattern uniformato per apply futuri; produrre un doc "apply pattern spec" invece di modificare i sealed script).
- **Rischio**: **basso** (audit already registrato; counter mancante è cosmetico).
- **Test richiesti**: se dedicated → T-apply-01 (apply pattern spec compliance).
- **Impatto**: doc-only (spec pattern) o dedicated round per re-seal.
- **Sub-questions PM**: **P3.SQ4.a**: produrre "R18.apply.pattern.spec.md" come guideline per apply futuri (senza toccare sealed) o dedicated round per riscrivere gli apply script?

---

### P3 #5 — R18.4.backlog — Class-Bound Apply Zero-Write Audit Noise

- **Backlog ID**: `R18.4.backlog — Class-Bound Apply Zero-Write Audit Noise`
- **Origine**: R18.4 B3 risk note
- **Stato attuale**: **aperto — technical debt su sealed apply script**
- **Analisi tecnica**: `round18_4_apply_class_bound_apply.py` (sealed) esegue `db.audit_log.insert_one(audit_event)` **anche quando** il delta è zero (no rows to update). Genera "audit noise" (audit log rows per no-op runs). Nessun impatto funzionale ma rumore in query audit log per accountability.
- **Blocco governance**: script **sealed R18.4 B4** — non modificabile.
- **Raccomandazione classificazione**: **defer / keep hold** (accorpabile con P3 #4 in un futuro "apply pattern refactor" round). Alternativa **fix now** su un post-processor read-only che filtra i no-op audit events al momento della query, ma è patch parallelo che aumenta complessità.
- **Rischio**: **basso** (rumore audit non impatta runtime).
- **Test richiesti**: se accorpato con #4 → T-apply-02 (skip insert when delta=0).
- **Impatto**: doc / dedicated round.
- **Sub-questions PM**: vedi P3.SQ4.a (accorpabile).

---

### P3 #6 — R18.4.followup — Public API serializer exposure

- **Backlog ID**: `R18.4.followup — Public API serializer exposure`
- **Origine**: Tester nota POST-APPLY R18.4 B4
- **Stato attuale**: **probabilmente completato** (verifica in Phase A)
- **Analisi tecnica**: verifica live via `GET /api/items` (executed 2026-07-06T11:33:00Z):
  - `item_binding_policy`: **ESPOSTO** ✅ (raw enum `hard`/`soft`/`universal`)
  - `slot_type`: **ESPOSTO** ✅ (canonical `weapon`/`armor`/`accessory`)
  - `is_universal`: **ESPOSTO** ✅ (derived flag)
  - Sample: `item_binding_policy=soft slot_type=weapon is_universal=False`
- Coperto anche da test t06 `test_item_public_exposes_new_r18_4_fields` PASS in R18.4.followup Phase B test suite.
- **Raccomandazione classificazione**: **close now** (già completato in R18.4.followup Phase B/C, verificato in Phase A).
- **Rischio**: **basso** (chiusura amministrativa).
- **Test richiesti**: N/A (già coperto da t06).
- **Impatto**: doc only (rimozione da backlog).
- **Sub-questions PM**: nessuna.

---

### P3 #7 — R18.backlog — phase14_* legacy regression debt cleanup

- **Backlog ID**: `R18.backlog — phase14_* legacy regression debt cleanup`
- **Origine**: R18.4.followup Phase C (aperto per chiudere Nota 2 PM)
- **Stato attuale**: **aperto — 10 test failed confermato**
- **Analisi tecnica**: rerun `pytest backend/tests/backend_phase14_4_round15_test.py backend/tests/backend_phase14_6_round3ab_test.py` → **10 failed, 5 passed, 2 rerun**. Cause identificate:
  - **Password policy stale**: `_make_user_with_guild` builder usa password `12345678` che non passa più validation. Failing tests: circa 8 (test suite phase14_4).
  - **Path count congelato**: `test_path_count_now_45` si aspetta 86 endpoints, attuali 275. Failing test: 1.
  - **Altri drift minori**: 1 test.
- **Blocco governance**: nessuno — questi 2 test file **NON sono sealed**.
- **Raccomandazione classificazione**: **fix now (safe)** in Phase B — è test-only cleanup, zero impatto runtime.
- **Rischio**: **basso** (test refresh, nessuna logica applicativa toccata).
- **Test richiesti**: rerun completo di `phase14_*` post-fix → deve essere green.
- **Impatto**: test file only (`backend/tests/backend_phase14_4_round15_test.py`, `backend/tests/backend_phase14_6_round3ab_test.py`).
- **Sub-questions PM**: **P3.SQ7.a**: aggiornare `path_count` con valore corrente (275) o convertirlo in soft-assert threshold (>= 200) per evitare stale drift a ogni nuovo endpoint?

---

### P3 #8 — R18.backlog — SMTPRecipientsRefused warning on register flow

- **Backlog ID**: `R18.backlog — SMTPRecipientsRefused warning on register flow`
- **Origine**: R18.4.followup Phase C (test log noise durante `POST /api/auth/register`)
- **Stato attuale**: **aperto — warning noto in test env**
- **Analisi tecnica**: `backend/.env` ha `SMTP_HOST="smtp.ionos.it"` come default. Durante test suite, `POST /api/auth/register` con email fittizia `t09a_XXX@orbus.test` (dominio non-deliverable) genera `SMTPRecipientsRefused` a livello log. Il registration flow completa comunque (`201 Created`), ma il warning appare nei log backend. Nessun failure test, solo rumore log.
- **Blocco governance**: nessuno — solo config/env manipulation, no code sealed toccato.
- **Raccomandazione classificazione**: **fix now (safe)** in Phase B tramite guard su dominio email test-only (`*.test` domain skip SMTP send) o env flag `EMAIL_ENABLED=false` in `.env.test`. Fix minimale (5-10 righe in `backend/app/email/service.py` con env check).
- **Rischio**: **basso** (guard config-level).
- **Test richiesti**: T-smtp-01 (register con email `@orbus.test` → nessun SMTP call, nessun ERROR log).
- **Impatto**: backend code (`app/email/*.py`) + `backend/tests/.env.test` (aggiunta flag).
- **Sub-questions PM**: **P3.SQ8.a**: usare pattern `dominio @*.test → skip SMTP` (automatico) o pattern `EMAIL_ENABLED=false in .env.test` (esplicito)?

---

## 4. Sommario classificazione

| Raccomandazione | Count | P3 IDs |
|---|---|---|
| **Close now** | 1 | #6 |
| **Duplicate** | 0 | — |
| **Fix now (safe, Phase B candidato)** | 2 | #7, #8 |
| **Dedicated round** | 1 | #1 |
| **Defer / keep hold** | 4 | #2, #3, #4, #5 |
| **TOTALE** | 8 | — |

## 5. Sub-questions PM aggregate

Domande binary-answerable emerse durante triage:

1. **P3.SQ1.a — Shield slot dedicato**: promuovere `shield` a slot dedicato (nuovo `slot_type='shield'`) o mantenere collapse in `armor`?
2. **P3.SQ1.b — Shield UI 4-slot vs dual-wield**: se dedicato, quarto slot indipendente o alternativo a weapon?
3. **P3.SQ2.a — specialization_unlocks dead branch**: mantenere dead code (accetta debt permanente) o schedulare re-seal round?
4. **P3.SQ4.a — Apply pattern spec**: produrre `R18.apply.pattern.spec.md` guideline (safe, no re-seal) o dedicated round di re-seal degli apply script?
5. **P3.SQ7.a — path_count strategy**: refresh hardcoded a 275 o convertire in soft-assert threshold (`>= 200`)?
6. **P3.SQ8.a — SMTP guard pattern**: dominio `@*.test` auto-skip o env flag `EMAIL_ENABLED=false` esplicito?

## 6. Rischio complessivo Phase B (cleanup round proposto)

**Rischio complessivo: BASSO**.

- I 2 candidati fix now (#7, #8) sono **test-only** e **config-only** (no runtime enforcement).
- La chiusura di #6 è amministrativa (aggiornamento backlog).
- Gli 1 dedicated round (#1) e 4 defer (#2, #3, #4, #5) **non entrano** in Phase B.
- Zero sigilli toccati.
- Zero DB writes.

## 7. Proposta scope Phase B (autorizzazione PM richiesta)

**Ordine di esecuzione consigliato**:

1. **Chiusura amministrativa P3 #6** — `Public API serializer exposure` → move a "Backlog risolti" in `/app/memory/backlog.md`. Zero code change.
2. **Fix P3 #8 — SMTP guard** (dopo risposta P3.SQ8.a) → 5-10 righe in `backend/app/email/*.py` + env flag → test T-smtp-01.
3. **Fix P3 #7 — phase14_* legacy cleanup** (dopo risposta P3.SQ7.a) → refresh 2 test file → rerun `pytest phase14_*` verde.
4. **Update backlog** con `close`/`defer` classificazioni per gli 8 items.

**Stop before**: qualsiasi touch a sealed files, a runtime enforcement, a DB writes. Se emerge complessità imprevista → STOP + report.

## 8. Governance check (post-triage)

- **Sigilli 36/36 byte-identical**: verificato via `pytest backend_r18_4_sealed_integrity_test.py` → **6/6 PASSED** (nessun drift SHA256).
- **Zero DB writes** durante Phase A: solo `find()` in audit `db.classes` (0 doc) e `db.items` (84 read).
- **Zero code changes** durante Phase A: nessun file backend o frontend modificato. Diff working tree: solo `/app/memory/PRD.md` (documental) + 2 nuovi file triage (`.md` + `.json`).
- **Zero apply script execution**: nessuno script eseguito.
- **Zero test rewrite**: `phase14_*` non toccato (rimane in aperto per Phase B).

## 9. Self-check Phase A triage 10/10

1. ✅ Purpose + metodologia documentati
2. ✅ 8 P3 triaged con 9 field ciascuno
3. ✅ Sommario classificazione con contatori
4. ✅ Sub-questions PM aggregate (6 SQ formulate)
5. ✅ Rischio complessivo Phase B valutato
6. ✅ Proposta scope Phase B con ordine
7. ✅ Governance check completato
8. ✅ 36 sigilli byte-identical
9. ✅ Zero DB writes / zero code changes
10. ✅ Deliverable `.md` + `.json` creati

---

**Ready for PM review** → attesa autorizzazione Phase B con risposte a 6 sub-questions.
