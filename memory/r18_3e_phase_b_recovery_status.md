# R18.3e Phase B — Recovery Audit Status Report (READ-ONLY)

- **Round**: R18.3e — Canonical IT ↔ Legacy EN Class Bridge — Phase B
- **Trigger**: builder cancellato durante Phase B; PM ha richiesto opzione **C** (recovery audit prima di riprendere).
- **Perimetro**: audit read-only. NO DB write, NO apply, NO cleanup, NO sovrascrittura, NO resume automatico, NO seal.
- **Timestamp UTC audit**: `2026-07-05T18:57:00Z` (approssimato al momento del recovery run).
- **Baseline audit_log pre-Phase B**: 11896

---

## 🔒 Classificazione Finale

### **C) Artefatti parziali presenti — serve cleanup/overwrite autorizzato PM**

**Dettaglio**:
- Tutti i 6 file R18.3e sono presenti sul filesystem con struttura valida.
- 5 file su 6 sono **completi e funzionanti** (B0 decision lock MD+JSON, B1 registry MD+JSON, B2 dry-run script).
- **1 file su 6 è parzialmente fixato**: `backend/tests/backend_r18_3e_bridge_test.py`:
  - `test_01` fix (set comparison) ✅ applicato
  - `test_14` / `test_15` fix (rimozione subprocess pytest ricorsivo) ❌ **NON applicato** — il `mcp_search_replace` post-run era stato interrotto da errore `Bad Gateway` prima della cancellazione builder.
- **Bug residuo test_15**: subprocess.run(pytest -k "sealed or integrity") dentro un test che è esso stesso selezionato da `-k "sealed or integrity"` → **ricorsione**. Il test hanga o timeout.
- **DB completamente invariato**: 0 write, 0 audit event R18_3E, 0 bridge field su adventurer_classes.
- **5/5 R18.3d sealed byte-identical** vs closure report noto (SHA256 MATCH totale).
- **Gameplay live healthy** (200 su /api/health e /api/dungeons).

**Cosa serve dal PM**:
1. Autorizzazione a **overwrite** di `test_14` e `test_15` nel file `backend_r18_3e_bridge_test.py` per rimuovere `subprocess.run(pytest)` ricorsivo e sostituirlo con check inline (in-process assertions).
2. Oppure: accettare stato attuale e documentare `test_14/test_15` come "skip in xdist due to nested pytest deadlock".

Nessuna altra azione necessaria: gli altri 5 artefatti R18.3e sono completi, il DB è vergine, i sigilli sono intatti.

---

## 📋 Tabella Artefatti (8 dimensioni × 6 file R18.3e)

Legenda: ✅ OK, ⚠️ parziale, ❌ non OK, N/A non applicabile.

| # | Artefatto | 1. Esiste | 2. Bytes | 3. mtime UTC | 4. Completo | 5. JSON parsabile | 6. 14 answers PM | 7. 16 legacy + 27 canon | 8. Solo dry-run |
|---|---|---:|---:|---|---|---|---|---|---|
| 1 | `pm_decisions.md` | ✅ | 6297 | 2026-07-05 18:41:16 | ✅ (ends: "Il SHA256 di questo file...") | N/A | ✅ (Q1..Q14 verbatim) | ✅ (mapping 16 legacy verbatim) | N/A |
| 2 | `pm_decisions.json` | ✅ | 8113 | 2026-07-05 18:41:16 | ✅ (JSON closed, structured) | ✅ | ✅ (`answers_verbatim.Q1..Q14`) | ✅ (`mapping_official_locked` = 16 entries) | N/A |
| 3 | `bridge_registry.json` | ✅ | 9730 | 2026-07-05 18:41:16 | ✅ (8 top-level keys, all present) | ✅ | ✅ (cross-ref decision lock) | ✅ (27 canonical + 18 bridge_entries) | N/A |
| 4 | `bridge_registry.md` | ✅ | 9738 | 2026-07-05 18:44:27 | ✅ (172 lines, ends: "NO touch ai 16 sigilli") | N/A | ✅ (Q3/Q6/Q12 pm_notes inline) | ✅ (tabella completa 18 entries + 27 canonical) | N/A |
| 5 | `round18_3e_apply_bridge.py` | ✅ | 13448 | 2026-07-05 18:45:13 | ✅ (module completes, __main__ ok) | N/A | N/A | N/A | ✅ (`APPLY_ENABLED: bool = False`, doppio flag required, dry-run tested OK 18/18) |
| 6 | `backend_r18_3e_bridge_test.py` | ✅ | 16007 | 2026-07-05 18:48:58 | ⚠️ (15 test def presenti, ma test_14/15 usano subprocess pytest ricorsivo) | N/A | ✅ (test_04 cross-ref) | ✅ (test_03, test_05) | ✅ (test_07, test_09) |

**Note dettaglio artefatto 6 (test suite)**:
- Test definiti: 15/15 (`test_01_...` fino a `test_15_...`) ✅
- `test_01` fix applicato: usa `set(answers.keys())` invece di sorted lex ✅
- `test_14_r18_3d_registry_regression`: chiama `subprocess.run([python, -m pytest, tests/backend_r18_3d_stat_role_registry_test.py])` — funzionale ma lento con xdist. Non blocca ma non ottimale.
- `test_15_sealed_integrity_16_sigilli`: chiama `subprocess.run([python, -m pytest, -k "sealed or integrity"])` — **ricorsione**: il subprocess include ANCHE il test corrente → potenziale hang/deadlock/infinite loop.
- Fix pianificato pre-cancellazione (non applicato): sostituire test_14 con check inline dei counter R18.3d registry, e test_15 con solo verifica file existence + hash (senza subprocess pytest).

---

## 🛡️ Invarianti 10 Punti

| # | Invariante | Result | Evidenza |
|---|---|---|---|
| 1 | Zero DB write su `adventurer_classes` (nessun doc ha 5 SAFE bridge field) | ✅ PASS | `count_documents({canonical_slug: exists})` = 0 su tutti e 5 i SAFE field |
| 2 | Zero audit event `R18_3E_*` emesso | ✅ PASS | `audit_log.count({event_type: /R18_3E/})` = 0 |
| 3 | Zero modifica `adventurers` (nessun nuovo bridge field) | ✅ PASS | `adventurers.count` = 3373 (baseline invariato) |
| 4 | Zero modifica `items` (nessun rewrite `class_tags`/`recommended_classes`) | ✅ PASS | `items.class_tags` non-empty = 157, `recommended_classes` non-empty = 157 (baseline invariati) |
| 5 | Zero modifica frontend (`git status /app/frontend/src`) | ✅ PASS | `git status` shows no tracked frontend changes |
| 6 | Zero runtime wiring del futuro loader (grep import in runtime paths) | ✅ PASS | `grep r18_3e\|round18_3e\|R18.3e /app/backend/app --exclude-dir=scripts --exclude-dir=tests` = empty |
| 7 | Sigilli R18.Reset + R18.3d ancora byte-identici | ✅ PASS | 5/5 R18.3d SHA256 MATCH vs closure report noto. `pytest -k "sealed or integrity"` = 4/4 PASS sui round precedenti (test_15 R18.3e sospeso per bug ricorsione ma NON incide sui sigilli reali) |
| 8 | Freeze flags OFF | ✅ PASS | `/tmp/orbus_maintenance.flag` NOT exists, `/tmp/orbus_internal_job_freeze.flag` NOT exists |
| 9 | Gameplay live healthy | ✅ PASS | `/api/health` = 200 (0.19s), `/api/dungeons` = 200, `/api/adventurers` = 401 senza token (atteso) |
| 10 | `audit_log` count = 11896 (invariato pre-Phase B) | ✅ PASS | `audit_log.count()` = 11896, delta = 0 |

**Risultato invarianti**: **10/10 PASS**. Nessun impatto runtime né DB. La cancellazione builder non ha causato alcun side-effect.

---

## 📄 Artefatti R18.3e in `/app/memory/`

```
r18_3e_bridge_registry.json                             9730 B  2026-07-05 18:41
r18_3e_bridge_registry.md                               9738 B  2026-07-05 18:44
r18_3e_phase_a_legacy_canonical_bridge_discovery.json  23620 B  2026-07-05 18:21  (Phase A, non toccato)
r18_3e_phase_a_legacy_canonical_bridge_discovery.md    32832 B  2026-07-05 18:21  (Phase A, non toccato)
r18_3e_phase_b_pm_decisions.json                        8113 B  2026-07-05 18:41
r18_3e_phase_b_pm_decisions.md                          6297 B  2026-07-05 18:41
```

**Nessun file log/report parziale trovato**. La Phase A discovery (2 file, `18:21`) è la baseline già chiusa nel round precedente e non è toccata da questo audit.

---

## 🎯 Sanity Check Dry-Run Script (in-process, no DB)

Esecuzione: `python -m app.scripts.round18_3e_apply_bridge --json`

```
mode                        = dry_run
apply_enabled               = False
source_round                = R18.3e Phase B
registry_sha256             = 4934f5d2527125144b00588611621348faf1ee862c0e4821ce7c63518498627f
decision_lock_sha256        = 17fdc96cb05efce24f1f9f3a8bde4ff318ff117939e27b0f5e8b9df3b7e5dbfc
total_entries               = 18
would_modify_count          = 18
skipped_count               = 0
errors_count                = 0
guard_hard_stop_passed      = 18/18
canonical_slug_ref_passed   = 18/18
breakdown_by_bridge_status  = {mapped_canonical: 9, mapped_alias: 3, deprecated_alias: 2,
                               technical_placeholder: 1, test_artifact: 1, canonical_native: 2}
audit_event.actually_emit   = False
backup_snapshot.actually_wr = False
real_apply_result           = BLOCKED — APPLY_ENABLED=False (LOCKED per R18.3e Phase B)
```

**Il dry-run è pienamente funzionante**. `--apply` senza / con ack fallisce con SystemExit exit=1 (verificato via subprocess.run: `returncode=1`).

---

## 📝 Raccomandazione Tecnica Compatta

**Scenario**: 5/6 artefatti completi e funzionanti. 1/6 con bug residuo isolato al file test (test_14/test_15 usano subprocess pytest ricorsivo).

**Opzioni**:

- **Opzione 1 (raccomandata)**: **Autorizzare overwrite di `test_14` + `test_15`** in `backend_r18_3e_bridge_test.py`. Sostituire il subprocess pytest con:
  - `test_14`: in-process check del registry R18.3d (count 27 canonical + 16 legacy + `meta.seal_status == "CLOSED_AND_SEALED_DOCUMENTAL_ONLY"`). Elimina il subprocess.
  - `test_15`: solo `Path.exists()` + `hashlib.sha256(...)` valid-hex check su 16 file. Elimina il subprocess pytest. La regression sealed/integrity resta comunque garantita dal command command-line separato `pytest -k "sealed or integrity"` (già usato nel pre-report R18.3d Phase B) — che a valle del fix funzionerà pulito senza self-recursion.
  - Costo: 1 `search_replace` mirato al file test, ~50 righe di codice sostituite. Nessun altro artefatto toccato.
  - Verifica post-fix: `pytest tests/backend_r18_3e_bridge_test.py` deve tornare **15/15 PASS**. Poi `pytest -k "sealed or integrity"` deve tornare **5/5 PASS** (i 4 esistenti + il nuovo test_15 R18.3e inline).

- **Opzione 2**: Accettare stato attuale, marcare `test_14` e `test_15` con `@pytest.mark.skip(reason="nested pytest deadlock in xdist")` senza modificare la logica. Costo: identico a Opzione 1, ma non regge come regression check.

- **Opzione 3**: Ripartire da zero cancellando i 6 file R18.3e e rifacendo B0→B1→B2 senza il bug. **Sconsigliato** — 5/6 artefatti sono già validi e la cancellazione builder non ha causato drift.

**Il PM decida quale opzione autorizzare**. Nel frattempo:
- NO resume automatico di Phase B
- NO cleanup automatico
- NO seal
- Il registry R18.3e resta in stato `OPEN_STAGE_B1_DOCUMENTAL_ONLY` (come da `meta.seal_status`)

---

## 🚫 Boundary Conditions Rispettate

- ❌ Zero DB write in questa recovery audit (evidenza: audit_log delta = 0)
- ❌ Zero apply
- ❌ Zero cleanup file (i 6 artefatti R18.3e restano intatti)
- ❌ Zero sovrascrittura (nessun `search_replace` a file esistenti durante audit)
- ❌ Zero resume automatico di Phase B
- ❌ Zero seal
- ❌ Zero touch ai 16 sigilli (14 R18.Reset.1b/1.2/1c + 2 R18.3d Phase B) — verifica SHA256 baseline recovery vs closure report R18.3d = tutti MATCH

**STOP totale post-report. Attendo GO PM.**
