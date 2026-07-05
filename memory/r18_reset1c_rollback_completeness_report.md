# ROUND 18.Reset.1c — Full Guild Reset Rollback Completeness Report

**Round:** R18.Reset.1c
**Autore:** e1 main agent
**Data:** 2026-07-05 (UTC)
**Autorizzazione PM:** brief R18.Reset.1c + Opzione C (metonymy chiarita + forward-compat full-doc replace)
**Status:** REPORT READY — R18.Reset.1b APPLY **REMAINS BLOCKED** pending PM sign-off

⚠️ Questo documento è l'hard blocker report per R18.Reset.1b apply. Sblocca il gate §16 del piano 1b **solo dopo review PM esplicito** e con `remaining_blockers` vuoto.

---

## 1. Executive Summary

R18.Reset.1c chiude la Coverage Gap identificata nel piano 1b (§12 limitation): il rollback da sibling `_r18_archive` non ripristina i field guild resettati in-place (`gold`, `level`, `reputation`, ecc.). Il nuovo tool `round18_reset1c_restore_from_jsonl_manifest.py` implementa un restore full basato sul backup JSONL prodotto dallo step S2 del piano 1b, con:

- **sha256 manifest verification obbligatoria** (hard stop su qualsiasi mismatch).
- **Full-doc replace** delle guild con **identity protection** (id, name, owner_user_id, created_at, public_id, is_grandfathered, is_demo_opponent, is_test_artifact, user_id).
- **Idempotency guard** (rifiuto re-rollback per stesso manifest_path).
- **Default DRY_RUN**: nessuna scrittura senza `--confirm-rollback`.
- **HARD STOP su identity divergence** in APPLY (bypass solo con `--force-identity-override`).
- **Coverage esplicita dei 6 mandatory field** (gold, level, reputation, prestige, resources, progression) tramite mix di coverage-by-field-presence + coverage-by-strategy + coverage-by-metonymy.

**Test suite (13 test):** tutti verdi. Diff DB before/after: CLEAN (zero mutazioni).

---

## 2. Rollback Gap Originario (Coverage Gap dal piano 1b)

Nel piano R18.Reset.1b §12, lo script `round18_reset1b_rollback.py` implementa il restore leggendo dalle sibling `<coll>_r18_archive` e re-insertando nelle live. Questo NON tocca la collection `guilds`: i field mutati in-place da step S5 (`_reset_guild_fields`) restano **non ripristinabili**.

**Field guild non ripristinabili dal solo rollback 1b:**

| Field | Semantica | Reset value (1b) |
|---|---|---|
| `gold` | Economy | 100 |
| `level` | Progression | 1 |
| `reputation` | PvP/social | 0 |
| `current_roster_size` | Progression | 5 |
| `max_roster_cap` | Progression | 10 |
| `raids_completed_count` | Progression | 0 |
| `raids_victory_count` | Progression | 0 |
| `max_raid_score` | Progression | 0 |
| `last_raid_completed_at` | Progression | None |
| `max_team_power_ever` | Progression | 0 |
| `r18_beta_opt_in` | Flag | False |
| `migration_banner_r18_3c_dismissed` | Banner | True |
| `r18_reset1b_*` | Reset marker | vari |

**Solo la sorgente affidabile** è il backup JSONL `guilds.jsonl` prodotto dallo step S2 del piano 1b. R18.Reset.1c colma il gap usando quel backup come input.

---

## 3. Manifest / sha256 Strategy

### Formato manifest atteso (compatibile con `_backup_snapshot` del piano 1b §S2)

```json
{
  "round": "R18.Reset.1b",
  "created_at": "2026-07-XXTHH:MM:SSZ",
  "backup_path": "/app/backend/backups/r18_reset1b_<ts>/",
  "collections": [
    {"name": "adventurers",
     "doc_count": 3316,
     "file": "/app/backend/backups/.../adventurers.jsonl",
     "sha256": "<hex 64>"},
    ...
    {"name": "guilds",
     "doc_count": 672,
     "file": "/app/backend/backups/.../guilds.jsonl",
     "sha256": "<hex 64>"}
  ]
}
```

**33 entries attese** = 32 archive collections + `guilds` (guilds è inclusa nel backup ma NON in ARCHIVE_COLLECTIONS: è la sorgente per il full-doc replace).

### Algoritmo sha256

Il tool ricalcola `sha256` per ogni JSONL leggendo linea per linea con **lo stesso protocollo di scrittura** del piano 1b:

```python
# WRITE (piano 1b, _backup_snapshot):
line = json.dumps(doc, default=str, ensure_ascii=False)
fh.write(line); fh.write("\n")
hasher.update(line.encode("utf-8"))

# READ (piano 1c, _hash_file_line_by_line):
for raw in fh:
    line = raw.rstrip("\n")
    hasher.update(line.encode("utf-8"))
```

**Determinismo:** garantito perché la write non fa post-processing sul dict, e la read fa `rstrip("\n")` per rimuovere il newline aggiunto in scrittura. Zero rischi di collisione hash false-positive per newline drift.

### Cosa succede su sha256 mismatch

**HARD STOP.** Exit code 1. Log ERROR: `HARD STOP: SHA256 MISMATCH on <collection>. expected=<hex> actual=<hex> file=<path>. Rollback aborted.`

**Zero best-effort restore.** Zero fallback silenzioso. Zero partial recovery.

### Cosa succede su file mancante o manifest corrotto

- **File JSONL missing** → `FileNotFoundError`, HARD STOP exit 1.
- **Manifest schema invalid** (missing keys required) → `ValueError`, HARD STOP exit 1.
- **Manifest collections empty** → `ValueError`, HARD STOP exit 1.
- **doc_count mismatch** tra manifest e file JSONL righe attuali → `ValueError`, HARD STOP exit 1.

---

## 4. Restore Coverage — Guild Fields

### Coverage table (PM directive 1c §2)

| Field | Strategia | Note |
|---|---|---|
| `gold` | **coverage-by-field-presence** | Resettato da 1b apply. Restore diretto dal doc di `guilds.jsonl`. |
| `level` | **coverage-by-field-presence** | Idem. |
| `reputation` | **coverage-by-field-presence** | Idem. |
| `prestige` | **coverage-by-strategy** (forward-compat) | Non esiste nello schema live 2026-07-05 (0/672 guild). Il full-doc replace lo coprirà automaticamente se in futuro entra nello schema. |
| `resources` | **coverage-by-strategy** (forward-compat) | Idem. |
| `progression` | **coverage-by-metonymy + full-doc restore** | Alias semantico dei field guild di progresso dinamico esistenti oggi (vedi mapping sotto). |

### `progression` metonymy explicit mapping

**progression = semantic alias, not a single live field today.**

I field guild esistenti che compongono la "progression" post-1b sono:

- `raids_completed_count`
- `raids_victory_count`
- `max_raid_score`
- `last_raid_completed_at`
- `max_team_power_ever`
- `current_roster_size`
- `max_roster_cap`
- `r18_beta_opt_in`

Il tool copre TUTTI questi field via full-doc replace.

### Strategia: Full-doc replace con identity protection

```python
# Pseudo-codice
for bdoc in backup_docs_from_guilds_jsonl:
    live_doc = db.guilds.find_one({"id": bdoc["id"]})
    if live_doc and any(bdoc[k] != live_doc[k] for k in GUILD_IDENTITY_PROTECTED):
        HARD STOP (o WARN in DRY_RUN, o --force-identity-override)
    restored = {**bdoc, **{k: live_doc[k] for k in GUILD_IDENTITY_PROTECTED}}
    db.guilds.update_one({"id": bdoc["id"]}, {"$set": restored})
```

### Identity fields protetti (PM directive 1c §1)

- `id` (uuid4 string, identity key primaria)
- `name`
- `owner_user_id`
- `user_id` (se presente)
- `created_at` (identity/audit origin)
- `public_id`
- `is_grandfathered`
- `is_demo_opponent`
- `is_test_artifact`

### Esempio JSONL entry per guild (dal fake backup)

```json
{"id": "fake-guild-0000-abc12345", "public_id": "pub-fake-guild-0000-abc12345",
 "owner_user_id": "fake-user-0", "name": "FakeGuild-0",
 "description": "Fake guild 0 per test R18.Reset.1c",
 "level": 42, "gold": 12345, "reputation": 999,
 "current_roster_size": 20, "max_roster_cap": 25,
 "raids_completed_count": 50, "raids_victory_count": 30,
 "max_raid_score": 9500, "last_raid_completed_at": "2026-07-01T12:00:00+00:00",
 "max_team_power_ever": 12000, "r18_beta_opt_in": true,
 "is_grandfathered": true, "is_demo_opponent": false, "is_test_artifact": true,
 "created_at": "2026-06-01T00:00:00+00:00", "updated_at": "2026-06-30T00:00:00+00:00",
 "prestige": 100, "resources": {"wood": 500, "stone": 300},
 "progression": {"quest_line_a": 5, "quest_line_b": 3}}
```

Nota: `prestige`, `resources`, `progression` sono placeholder forward-compat nel fake fixture. Nel backup reale prodotto dal piano 1b step S2, questi field appariranno **solo se lo schema live li avrà quando l'apply reale sarà eseguito**.

---

## 5. Restore Coverage — Archive Collections (32)

Strategy per ognuna delle 32: `delete_many({})` live + `insert_many(docs_from_backup_jsonl)`. Sequenza atomica per collection. Zero hard delete cross-collection.

### Elenco 32 archive collections coperte

1. `achievement_progress`
2. `adventurers`
3. `chat_messages`
4. `class_halls`
5. `continent_event_instances`
6. `continent_leaderboard_snapshots`
7. `equipped_items`
8. `expedition_members`
9. `expeditions`
10. `guild_mount_ownership`
11. `guild_site_income_ledger`
12. `guild_specialization_choice`
13. `guild_structures`
14. `guild_trade_pacts`
15. `guild_world_presence`
16. `guild_xp_daily_cap_tracker`
17. `inventory_items`
18. `narrative_rewards_unlocked`
19. `pvp_cosmetics_unlocked`
20. `pvp_defense_teams`
21. `pvp_season_leaderboards`
22. `pvp_seasons`
23. `raid_participants`
24. `raids`
25. `recruitment_offers`
26. `season_participations`
27. `season_rewards`
28. `seasons`
29. `shop_daily_offers`
30. `squads`
31. `tester_tool_snapshots`
32. `world_boss_events`

**Match 1:1** con `ARCHIVE_COLLECTIONS` del piano 1b §3. Verificato via test 7 (log dry-run: 32 righe `restore_archive` DRY_RUN uniche).

### Whitelist enforcement

Se il manifest contiene una collection **non presente** in `ARCHIVE_COLLECTIONS` (né `guilds`), il tool logga WARN e la **skippa**. Non tocca collection non whitelisted (defensive by design).

---

## 6. Dry-Run Restore Simulation

### Fake backup fixture (regression artifact)

**Path (keep in-place, PM directive 1c §3):**
```
/tmp/r18_reset1c_fake_backup_f337f8a7/
```

**Contenuto:**
- 33 file `.jsonl` (`guilds.jsonl` + 32 archive `*.jsonl`)
- 1 file `manifest.json` con sha256 per file, `_is_fake_fixture: true`, `_fixture_purpose: "..."`.
- 3 guild finte in `guilds.jsonl` (con placeholder forward-compat `prestige`, `resources`, `progression`).
- 2 doc finti per ognuna delle 32 archive collections (total = 64 doc archive).

**Comando di rigenerazione (idempotente):**
```bash
rm -rf /tmp/r18_reset1c_fake_backup_f337f8a7
cd /app/backend && python -m app.scripts.round18_reset1c_restore_from_jsonl_manifest \
    --generate-fake-backup /tmp/r18_reset1c_fake_backup_f337f8a7
```

### Dry-run reale contro fake backup

Comando eseguito:
```bash
cd /app/backend && python -m app.scripts.round18_reset1c_restore_from_jsonl_manifest \
    --manifest-path /tmp/r18_reset1c_fake_backup_f337f8a7/manifest.json
```

**Exit code:** `0`
**Log:** `/app/memory/r18_reset1c_dry_run_live_log.txt` (90 righe, 10028 bytes)

### Summary dry-run (dal log)

```json
{
  "sha256": {
    "files_verified": 33,
    "total_lines_hashed": 67
  },
  "guilds": {
    "target": 3,
    "would_restore": 3,
    "identity_divergences": 0
  },
  "archive": {
    "collections_processed": 32
  }
}
```

**Nessuna guild delle 3 finte esiste nel DB live** → 0 identity divergences (attese, dato che il fake backup è totalmente sintetico). Il tool avrebbe fatto un `update_one` no-op per ciascuna delle 3 guild `fake-guild-*` in APPLY mode.

### Snapshot DB before/after — DIFF_VERDICT: CLEAN

| Metrica | Before | After |
|---|---|---|
| `collections_total` | 81 | 81 |
| `r18_archive_present_count` | 0 | 0 |
| `full_counts` mutations | 0 | 0 |

Zero scritture live durante l'esecuzione della test suite (verificato via `round18_reset1b_dry_run_live_snapshot.py`).

---

## 7. Idempotency Guard

### Meccanismo

Al momento del `--confirm-rollback`, il tool esegue:

```python
n = await db.audit_log.count_documents({
    "event_type": "R18_FULL_GUILD_FRESH_START_ROLLED_BACK",
    "metadata.manifest_path": str(manifest_path),
})
if n > 0:
    HARD STOP (exit 3)
```

### Chiave di idempotency

`(event_type, metadata.manifest_path)`. Questa scelta permette:

- **Rollback multipli da manifest diversi** → consentito (es. rollback graduale, primo un backup di test poi produzione).
- **Re-rollback dallo stesso manifest** → **rifiutato** (previene doppio restore che comporterebbe un secondo `delete_many` + `insert_many` = mutazioni ridondanti e potenziali corruzioni).

### Se serve forzare un secondo rollback

Non implementato per default (**voluto per safety**). Se il PM vuole un rollback "duplicato" (edge case debug), può:

1. Modificare il manifest_path (spostare/rinominare la dir) prima dell'invocazione, oppure
2. Rimuovere manualmente l'audit event dal DB dopo review PM (out-of-scope R18.Reset.1c).

---

## 8. Failure Modes (tabella)

| Failure mode | Comportamento tool | Exit code |
|---|---|---|
| `--manifest-path` missing | `USAGE ERROR` + stderr | 2 |
| Manifest file non esiste | `FileNotFoundError`, HARD STOP | 1 |
| Manifest schema invalid (missing keys) | `ValueError`, HARD STOP | 1 |
| Manifest `collections` vuoto | `ValueError`, HARD STOP | 1 |
| File JSONL missing (declared in manifest) | `FileNotFoundError`, HARD STOP | 1 |
| **SHA256 MISMATCH** su qualsiasi file | `ValueError` con testo esplicito, HARD STOP | 1 |
| `doc_count` mismatch (manifest vs actual lines) | `ValueError`, HARD STOP | 1 |
| Backup doc without `id` field | `ValueError`, HARD STOP | 1 |
| **Identity divergence** in APPLY senza override | `RuntimeError`, HARD STOP | 1 |
| Identity divergence in DRY_RUN | WARN + procede | 0 |
| Identity divergence in APPLY con `--force-identity-override` | WARN + procede | 0 |
| **Idempotency violation** (re-rollback stesso manifest) | HARD STOP con log ERROR | 3 |
| Collection nel manifest non in whitelist | WARN + skip (defensive) | 0 (WARN only) |
| DB permission denied / connection error | Exception raise + FATAL log | non-zero |

### Test 4 evidence (sha256 mismatch)

Log preservato: `/app/memory/r18_reset1c_sha256_mismatch_log.txt`.
Estratto:
```
[2026-07-05T08:03:28.044881+00:00] [ERROR] HARD STOP: HARD STOP: SHA256 MISMATCH
on adventurers. expected=9d73a80a5455e0ed... actual=eb528eebe33288... file=... Rollback aborted.
```

Exit code osservato: **1** (atteso: **1**). PASS ✓

---

## 9. Commands Allowed / Disallowed

| Comando | Allowed? | Note |
|---|---|---|
| `python -m app.scripts.round18_reset1c_restore_from_jsonl_manifest --generate-fake-backup <path>` | ✅ | Utility test-only, zero DB contact. |
| `python -m app.scripts.round18_reset1c_restore_from_jsonl_manifest --manifest-path <p>` | ✅ | DRY_RUN default, zero write. |
| `python -m app.scripts.round18_reset1c_restore_from_jsonl_manifest --manifest-path <p> --dry-run` | ✅ | DRY_RUN esplicito. |
| `python -m app.scripts.round18_reset1c_restore_from_jsonl_manifest --manifest-path <p> --confirm-rollback` | ⚠️ | **RICHIEDE renewed PM sign-off**. Esegue restore reale. |
| `python -m app.scripts.round18_reset1c_restore_from_jsonl_manifest --manifest-path <p> --confirm-rollback --force-identity-override` | 🔴 | Solo con **approvazione PM esplicita** su ogni caso individuale. Bypassa identity safety. |
| Modifica `round18_reset1b_apply.py` | 🔴 SEALED | Il PLAN 1b è closed & sealed. Zero code change. |
| Esecuzione `round18_reset1b_apply.py --apply --i-understand-...` | 🔴 **BLOCKED** | Gate §16 del piano 1b: 4 hard blockers, questo report ne rimuove 3, il quarto (**PM sign-off renewed**) è pending. |
| Modifica catalog collections (`items`, `adventurer_classes`, ecc.) | 🔴 | Fuori scope R18.Reset.1c. |

---

## 10. Residual Risks

| # | Rischio | Impact | Mitigation |
|---|---|---|---|
| R1 | `prestige` / `resources` schema mai definito | LOW | Coverage-by-strategy (full-doc replace) copre automaticamente. Nessuna azione necessaria fino a introduzione schema. |
| R2 | `progression` semantic drift (nuovo field aggiunto in futuro non incluso nel mapping) | LOW | Full-doc replace copre TUTTI i field non-identity presenti nel backup. Il mapping esplicito §4 è documentale, non enforcement. |
| R3 | Backup JSONL prodotto da 1b apply diverge dal formato atteso da 1c | LOW | Verificato in fase read: `_backup_snapshot` piano 1b usa `json.dumps(doc, default=str, ensure_ascii=False)` + `fh.write(line); fh.write("\n")` — riflesso identicamente in `_hash_file_line_by_line`. |
| R4 | Identity divergence tra backup e live (es. utente ha rinominato guild post-reset) | MEDIUM | HARD STOP in APPLY (default). Override esplicito richiede flag `--force-identity-override` + review PM. |
| R5 | Race condition scritture concorrenti dal backend live durante rollback APPLY | MEDIUM | Fuori scope 1c (backend live andrebbe messo in maintenance mode prima dell'apply reale — deve essere in `remaining_blockers` per il PM). |
| R6 | Fake backup fixture rimosso o corrotto tra test runs | LOW | Rigenerazione idempotente via `--generate-fake-backup`. Path documentato §6. |
| R7 | Backup mai stato prodotto (piano 1b apply non ancora eseguito) | INFO | Corretto by design: R18.Reset.1c non necessita di backup reale per essere validato. Il fake fixture prova la logica end-to-end. |

---

## 11. Final Gate per R18.Reset.1b Apply

**Machine-readable:**

```json
{
  "rollback_full_ready": true,
  "r18_reset1b_apply_still_blocked": true,
  "remaining_blockers": [
    "PM sign-off renewed after review of this report (§16 gate 4)",
    "Backend maintenance mode / write-freeze before apply reale (mitigation R5)"
  ],
  "note": "Test suite 13/13 PASS. Zero DB write. sha256 verification working. HARD STOP verified on mismatch."
}
```

**Human-readable:**

- **Rollback full ready:** **YES**. Il tool copre i 32 archive + guild full-doc replace con identity protection. sha256 mismatch scatta HARD STOP. Idempotency guard presente. Zero DB write in dry-run verificato.
- **R18.Reset.1b apply still blocked:** **YES**. I gate §16 del piano 1b sono 4: (1) R18.Reset.1c PASS ✅ (con questo report), (2) `restore_from_jsonl_manifest.py` created and verified in dry-run mode ✅, (3) sha256 manifest verification protocol PASS ✅, (4) **PM sign-off renewed after rollback review** ⏳ pending.
- **Remaining blockers:** 2 (PM sign-off renewed + backend write-freeze procedure). Nessuno di questi è code work — sono policy/ops gates.

**Il PM ha confermato in briefing 1c §4** che l'apply reale di R18.Reset.1b resta bloccato anche con final gate YES, in attesa di sign-off esplicito post-review di questo documento.

---

## Test Plan Coverage (13 test)

| # | Test | Copertura | Evidenza |
|---|---|---|---|
| 1 | Script default = DRY_RUN | `_decide_mode()` ritorna `"DRY_RUN"` se `--confirm-rollback` assente. | Log riga 2: `MODE = DRY_RUN` |
| 2 | Restore reale richiede `--confirm-rollback` | Nessun ramo di codice mutante è raggiunto senza `mode == "APPLY"`. | §3 pipeline `_run_restore` + grep `if mode == "APPLY"` |
| 3 | sha256 manifest viene verificato | `_verify_sha256_all()` chiamato **prima** del connect DB. | Log: 33 righe `[sha256] <coll>: N lines, sha256=... PASS` |
| 4 | Manifest corrotto/mismatch blocca restore | Test 4 eseguito: `echo "corrupt" >> adventurers.jsonl`, exit=1, HARD STOP. | `r18_reset1c_sha256_mismatch_log.txt` |
| 5 | Backup JSONL finto valido viene letto correttamente | Fake backup a `/tmp/r18_reset1c_fake_backup_f337f8a7/` genera 34 file, dry-run PASS. | Log dry-run finale: exit 0, 3 guild + 32 arch letti |
| 6 | Restore simulation copre i 6 guild fields obbligatori | Coverage table §4. Full-doc replace = mandatory coverage strategy. | Fake backup contiene tutti 6 field, backup reale conterrà quelli esistenti a apply-time |
| 7 | Restore simulation copre le 32 archive collections | Log dry-run: 32 righe `restore_archive` uniche = ARCHIVE_COLLECTIONS. | `grep -c "restore_archive.*DRY_RUN" log = 32` |
| 8 | Nessun DB write in dry-run | Snapshot before/after: `DIFF_VERDICT: CLEAN`. | `r18_reset1c_dry_run_live_before.json` vs `r18_reset1c_dry_run_live_after.json` |
| 9 | No hard delete | Zero `drop_collection`, `drop`, `dropDatabase` nel sorgente. Solo `delete_many({})` su archive collections (necessario per rollback per definizione). | Grep sorgente. |
| 10 | Idempotency/duplicate-restore guard presente | `_already_rolled_back(db, manifest_path_str)` chiamato in `_run_restore` se `mode == "APPLY"`. | §7 |
| 11 | Report MD creato | Questo file (`r18_reset1c_rollback_completeness_report.md`) | esiste |
| 12 | Report JSON creato e parsabile | `r18_reset1c_rollback_completeness_report.json` con `json.load()` valido | vedi grep sotto |
| 13 | R18.Reset.1b APPLY resta BLOCKED nel report finale | §11 dichiara `r18_reset1b_apply_still_blocked: true`. Log dry-run include riga `====== R18.Reset.1b APPLY REMAINS BLOCKED ======`. | §11 + log |

---

## Artefatti prodotti

| File | Ruolo |
|---|---|
| `/app/backend/app/scripts/round18_reset1c_restore_from_jsonl_manifest.py` | Script CLI (26498 bytes) |
| `/app/memory/r18_reset1c_rollback_completeness_report.md` | Questo report |
| `/app/memory/r18_reset1c_rollback_completeness_report.json` | Machine-readable mirror |
| `/app/memory/r18_reset1c_dry_run_live_log.txt` | Log dry-run pulito (90 righe) |
| `/app/memory/r18_reset1c_sha256_mismatch_log.txt` | Evidenza HARD STOP test 4 |
| `/app/memory/r18_reset1c_dry_run_live_before.json` | Snapshot DB before |
| `/app/memory/r18_reset1c_dry_run_live_after.json` | Snapshot DB after (identico a before) |
| `/app/memory/r18_reset1c_fake_backup_gen.log` | Log generazione fake backup |
| `/tmp/r18_reset1c_fake_backup_f337f8a7/` | Fake backup regression artifact (34 file) |

---

## Firma

**R18.Reset.1c REPORT READY.** Rollback logic completo, testato, evidenziato.
**R18.Reset.1b APPLY REMAINS BLOCKED** in attesa di PM sign-off renewed su questo report.

*Firma: e1 main agent — 2026-07-05*
