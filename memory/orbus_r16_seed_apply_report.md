# Post-Recovery Seed Apply Report — Orbus Round 16.x

Data: 2026-07-01 13:30 UTC
DB target: `orbus_r16` (locale al pod preview/dev, `mongodb://localhost:27017`, `bindIp: 127.0.0.1`)
Riferimenti collegati:
- `/app/memory/incident_recovery_report.md` (recovery iniziale)
- `/app/memory/dry_run_static_seeds_report.md` (STEP 1 dry-run)
- `/app/memory/environment_scope_verification.md` (verifica ambito)
- `/app/memory/bug_pytest_db_isolation.md` (STEP F diagnosi)
- `/app/memory/test_credentials.md` (credenziali smoke)

## Ambito (formulazione ufficiale)
> Il drop ha toccato solo il DB locale preview/dev del pod: `test_database`.
> Dal pod non esiste accesso a cluster produzione.
> Nessuna email/gilda dell'ALLOWLIST reale era nel DB droppato.
> Quindi il danno riguarda solo l'ambiente preview/dev locale.
> La produzione, se esiste su cluster separato come indicato dai file memory, non è stata raggiungibile né toccabile da questo pod.
> Produzione non raggiungibile dal pod; nessuna evidenza di contatto o modifica prod.

---

# Report 21 punti

## 1. Fix `import uuid` applicato
- **SI**.
- File: `/app/backend/app/scripts/round160_seed_classes_v2.py` — riga import 30-33.
- Backup: `/app/backend/app/scripts/round160_seed_classes_v2.py.bak_pre_uuid_fix` (18508 bytes).
- Diff: aggiunta singola riga `import uuid` (nessun'altra modifica).
- Verifica sintassi post-fix: `python -c "import ast; ast.parse(open('.../round160_seed_classes_v2.py').read())"` → `SYNTAX OK`.

## 2. Dry-run classes_v2 post-fix
- Output pulito: `{'dry_run': True, 'base_classes': {'inserted': 1, 'flagged_base': 9, 'skipped': 0}, 'deprecations': {'deprecated': 3, 'skipped': 0}, 'specializations': {'inserted': 30, 'skipped': 0}}`.
- Verdetto: SAFE-TO-APPLY.

## 3. Apply `class_identity` (round15_seed_class_identity.py)
- PRIMA: 0/12 classi con `primary_stat`.
- Apply summary: `updated=12, untouched=0, skipped_inactive=0, conflicts=0`.
- DOPO: 12/12 classi con `primary_stat`.
- Warnings: nessuno.

## 4. Apply `classes_v2` (round160_seed_classes_v2.py)
- PRIMA: 12 classes, 0 class_specializations.
- Apply summary: `base_classes.inserted=1 (warlock) flagged_base=9`, `deprecations.deprecated=3`, `specializations.inserted=30`.
- DOPO:
  - `adventurer_classes`: 13 (10 base + 3 deprecate)
  - `class_specializations`: 30
  - Deprecate: `berserker → warrior/berserker_spec`, `assassin → rogue/assassin_spec`, `necromancer → mage/necromancer_spec`.
- **Verifica esplicita (mongosh)**:
  ```
  is_base_class=true: 10 (11 attese nel brief; il file di seed implementa 10 base + 30 spec)
  is_active=false (deprecate): 3
  ```
- Nota: il target "11 base" nel brief utente originale si riferisce probabilmente al conteggio *con* warlock. Nell'implementazione attuale ci sono 10 base + 30 spec + 3 deprecate = **13 righe totali in `adventurer_classes`** + 30 in `class_specializations`. Se serve una 11ª base non presente in questo seed, va aggiunta separatamente (fuori scope di questo apply).

## 5. Apply `races` (round160_seed_races.py)
- PRIMA: 0.
- Apply summary: `inserted=50, skipped=0, total=50`.
- DOPO: 50 razze totali (common 30, uncommon 12, rare 6, epic 2 — distribuzione confermata).
- Warnings: nessuno.

## 6. Dry-run cleanup gilde junk
- Script: `/app/backend/app/scripts/round14_cleanup_archive_demo_guilds.py`
- Analisi:
  - **Identificazione junk**: `is_test_artifact=true` OR nome match regex `^(G_|G |Test|Demo|tester|R[0-9]|[0-9]+[A-Z]|P[0-9]+[A-Za-z]*\s+[0-9a-fA-F]|Ver\s+ver_|RaidSmoke\s+raidsmoke_)` OR `^Guild(house)?[_\s]`. Filtro escluso: già archiviate.
  - **PRESERVE_EMAILS**: `{"tester@orbus.test"}` — hard-coded nel codice.
  - **Preservazione demo opponents**: gilde con `is_demo_opponent=true`.
  - **NO hard delete**: usa `update_many` con `$set: {is_archived_pre_launch: true, archived_at, archived_reason: "round14_pre_launch_cleanup"}`.
  - **Idempotenza**: filtro esclude `is_archived_pre_launch: true` → rerun non modifica gilde già archiviate.
- Simulazione mongosh (SOLO lettura): match 148 candidati, 4 preservati (`la lanterna di ferro` [tester] + 3 demo opponents `Custodi del Vento`, `Esiliati del Vuoto`, `Compagnia delle Tre Lune`), **0 false positive** (nessuna gilda non-preservata al di fuori dei candidati).
- **Verdetto: SAFE**.
- ⚠️ Sub-nota: preserve list del codice include SOLO `tester@orbus.test`, NON `admin@orbus.test` né `clean_onboarding@orbus.test`. Per il cleanup di oggi non è stato un problema (queste due utenze non avevano gilde). Se in futuro creano gilde, andranno aggiunte manualmente al set `PRESERVE_EMAILS` o marcate `is_demo_opponent=true`.

## 7. Apply cleanup gilde junk
- PRIMA: 152 gilde totali (tutte non archiviate).
- Apply: `archived_in_this_run=148, active_after=4`.
- DOPO: 4 attive (tester + 3 demo opponents), 148 archiviate.
- Audit events scritti: fino a 148 (audit best-effort, wrapped in try/except).
- Warnings: nessuno.

## 8. Gilde junk residue
- **0 gilde junk residue** dopo il cleanup (verificato).
- Se sessioni pytest future dovessero rieseguire senza isolation (bug F ancora aperto), il cleanup dev'essere rilanciato prima di ogni smoke test.

## 9. Apply `class_halls` (round160_seed_class_halls.py)
- **Eseguito**: sì (post-cleanup C.2 come previsto dalla decisione B2 dell'utente).
- PRIMA: 0.
- Apply summary: `guilds_seen=152, halls_inserted=1672, halls_skipped=0`.
- DOPO: 1672 halls totali. Il conto include anche le 148 gilde ora archiviate perché lo script filtra su `archived_pre_launch != true` (naming diverso da `is_archived_pre_launch`) — piccolo *inconsistency legacy*, non blocking.
- Distribuzione halls per gilda: 11 halls per ogni gilda (script preseeda incluso warlock come base class).
- Warnings: nessuno.

## 10. Apply `achievements` (round15_seed_achievements.py)
- PRIMA: `achievements_catalog: 0`.
- Apply summary: `inserted=110, updated=0`.
- DOPO: 110 achievement in `achievements_catalog`.
- Distribuzione categorie: `classi_stats 12, consorzi 3, crafting 8, dungeon 12, economia 6, equipaggiamento 10, leaderboard 5, lore 8, meta_beta 4, primi_passi 8, pvp_stagioni 8, raid 8, roster 10, territorio 8`.
- **Anti-P2W enforcement attivo**: reward_type ristretto a `xp_points`, `xp_points_title`, `xp_points_badge`, `xp_points_frame`. Whitelist strict su payload keys.
- Warnings: nessuno.

## 11. Apply `item_tags` (round15_seed_item_tags.py)
- PRIMA: 131 items attivi non-test; 0 con class_tags.
- Apply summary: `items scanned=131, updated=131, untouched=0`.
- DOPO: 131 items con `class_tags`, `recommended_classes`, `role_tags`, `stat_tags`; signature items con `weapon_tags`/`armor_tags`/`required_class_optional` hard-locked.
- Sample: `drake_slayer_blade`, `drake_slayer_helm`, `drake_slayer_chest`, `dragon_essence`, `arcane_adept_orb`.
- Warnings: nessuno.

## 12. Count finale classi base
- **10** (con `is_base_class=true`). Include `warrior, rogue, mage, priest, ranger, paladin, druid, monk, bard, warlock`.
- Se il target contrattuale è "11", manca 1 classe non implementata da questo seed (documenta come gap).

## 13. Count finale specializzazioni
- **30** in `class_specializations` (3 per ogni base class).

## 14. Count finale razze
- **50** in `races`.

## 15. Count finale Class Hall
- **1672** in `class_halls`.

## 16. Count finale achievement
- **110** in `achievements_catalog`.

## 17. Count item taggati
- **131 / 131** items attivi non-test (100% coverage).

## 18. Stato bug pytest DB isolation
- **Bug confermato**. Report dettagliato in `/app/memory/bug_pytest_db_isolation.md`.
- **Sintesi**: `conftest.py` carica `.env` del backend con `DB_NAME=orbus_r16`; poi tenta di caricare `tests/.env.test` per override, ma **il file non esiste** (solo `.env.test.example`). Singoli test file istanziano direttamente `AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]` → scritte dirette sul DB attivo.
- **Impatto storico**: 148 gilde junk create durante l'incident recovery, ora tutte archiviate.
- **Fix proposto (NON applicato, autorizzazione utente richiesta)**:
  1. Creare `/app/backend/tests/.env.test` con `DB_NAME=orbus_r16_test` + `APP_ENV=test`.
  2. Aggiungere safety rail in `conftest.py`: `assert os.environ["DB_NAME"].endswith("_test") or os.environ.get("APP_ENV") == "test"`.
- **NON eseguito full pytest** (rispettata la regola).

## 19. Conferma NO hard delete
- **SI**. Evidence:
  - `round14_cleanup_archive_demo_guilds.py` usa `update_many` con `$set: {is_archived_pre_launch: true, archived_at}` — nessun `delete_many` / `deleteOne`.
  - Nessun `db.dropDatabase` / `db.collection.drop` invocato in questa sessione (verificato grep sui log backend).
  - Tutti i seed applicati sono additive (`insert_one`/`update_one`/`upsert`), zero delete.

## 20. Conferma NO demo/dev seed eseguito
- **SI**. Evidence:
  - Non eseguiti: `seed_tester_adventurers.py`, `seed_tester_inventory.py`, `seed_round12_preseason.py`, `seed_round12_demo_opponents.py`, `seed_round12_release_tester_roster.py`, `seed_round12_rewards.py`, `seed_test_bound_items.py`, `seed_preview_tester_round6c.py`, `seed_preview_tester_round6e.py`.
  - Non eseguiti script blacklist: `recover_stuck_*`, `refund_failed_specializations.py`, `reset_test_account_*.py`, `round160_migrate_adventurers_deprecated_classes.py`, `round160_1_cleanup_recruitment_offers.py`, `rollback_territory_free_purchases.py`.
- **NB**: i seed *automatici* del `lifespan.py` (14 script listati in `incident_recovery_report.md` punto 15) vengono eseguiti al boot del backend — non da me, ma dal framework Round 16.x. Sono di sistema, idempotenti, e includono la creazione automatica di `tester@orbus.test` e `clean_onboarding@orbus.test`.

## 21. Prossimo step consigliato
- **Smoke test 21-punti tramite `e1_tester`** — orchestrato dall'utente.
- **Verdetto smoke-ready: SI** (a valle di STEP H, vedi sotto).

---

# STEP H — Prep smoke completato

| item | stato | evidence |
|---|---|---|
| `.env` backup pre-admin-setup | ✅ | `/app/backend/.env.bak_pre_admin_setup` esiste |
| `ADMIN_EMAILS=admin@orbus.test,tester@orbus.test` in .env | ✅ | `grep '^ADMIN_EMAILS' .env` |
| `TESTER_PASSWORD=password123` in .env | ✅ | `grep '^TESTER_PASSWORD' .env` |
| Fix newline `.env` (concatenazione APP_ENV con ADMIN_EMAILS) | ✅ | ripristinato + append pulito |
| Creazione `admin@orbus.test / admin123` | ✅ | via `POST /api/auth/register` con `{email, password, username:"admin"}`, patch `is_admin=true` via mongosh |
| `admin@orbus.test` login | ✅ | `HTTP 200` verificato |
| `tester@orbus.test` `is_admin=true` conservato | ✅ | verify: `{"email":"tester@orbus.test","is_admin":true}` |
| `tester@orbus.test` login | ✅ | `HTTP 200` verificato |
| Cache HMR pulita | ✅ | `rm -rf node_modules/.cache && restart frontend` |
| Frontend compile status | ⚠️ | `Compiled with warnings` — 1 warning eslint minore (`ClassHalls.jsx:244` missing useEffect dep). Non blocking. |
| `test_credentials.md` aggiornato | ✅ | vedi `/app/memory/test_credentials.md` |
| Backend RUNNING | ✅ | pid 19115, seed lifespan completo |

## Verdetto smoke-ready
**SI** — l'ambiente è pronto per lo smoke test 21-punti che l'utente orchestrerà con `e1_tester`.

Livelli di attenzione da comunicare al tester:
- Il DB `orbus_r16` contiene stato **post-recovery + post-seed**. Presenta:
  - 10 base classes (Round 16.0 v2) + 3 deprecate + 30 specializzazioni
  - 50 razze
  - 152 gilde (**4 attive**: `la lanterna di ferro` + 3 demo opponents; 148 archiviate)
  - 885 adventurers (di cui la maggior parte in gilde archiviate — filtra per gilde attive nei test)
  - 1672 class_halls
  - 110 achievement catalog entries
  - 131 items taggati
  - 8 continenti Round 16.3, world boss "Alveora", 12 continent events, 8 continent resources
- **`admin@orbus.test / admin123`** e **`tester@orbus.test / password123`** entrambi con `is_admin=True` e login funzionante.
- **Schema register**: richiede `{email, password, username}` — NON solo email+password come nella Fase 1 fresh. Adattare gli smoke test di registrazione.

---

# Task tracciati per dopo lo smoke test

## P2 — env config
- **`APP_BASE_URL="https://orbusonline.net"`** in `/app/backend/.env` è un valore di production. Impatta i link generati nelle email (welcome, password reset). In preview dovrebbe puntare al preview URL (`https://drain-dispatch.preview.emergentagent.com`). Da correggere post-smoke.
- Le email SMTP falliscono comunque in preview (log `SMTPRecipientsRefused` per domini `.test`), quindi il rischio pratico è nullo finché non c'è un tester con email reale.

## P2 — bug DB isolation pytest
- Fix proposto in `/app/memory/bug_pytest_db_isolation.md` (opzione 1 + safety rail).
- Non applicato in questa sessione (regola: no full pytest, no code changes non autorizzati).

## P2 — inconsistency naming class_halls vs cleanup
- `round160_seed_class_halls.py` filtra su `archived_pre_launch != true` (senza `is_`).
- `round14_cleanup_archive_demo_guilds.py` scrive `is_archived_pre_launch: true` (con `is_`).
- Risultato: le halls vengono create anche sulle gilde archiviate. Bug legacy minore, non blocking.

## P2 — 11ª classe base mancante
- Il brief menziona "11 classi base" ma `round160_seed_classes_v2.py` implementa solo 10 (9 esistenti + warlock). Verificare se manca una classe (Alchemist? — nota: esiste `round160_1_seed_alchemist_class.py` non incluso nella lista utente P0). Da confermare col PM.

## P2 — warning eslint frontend
- `src/pages/ClassHalls.jsx:244` missing useEffect dependency `load`. Non blocking. Fix banale.

---

# File modificati/creati in questa sessione

## Modifiche codice
- `/app/backend/app/scripts/round160_seed_classes_v2.py` → aggiunta 1 riga `import uuid` (backup in `.bak_pre_uuid_fix`)

## Modifiche `.env`
- `ADMIN_EMAILS=admin@orbus.test,tester@orbus.test` aggiunto (backup in `.env.bak_pre_admin_setup`)
- `TESTER_PASSWORD=password123` aggiunto

## Documenti creati
- `/app/memory/dry_run_static_seeds_report.md`
- `/app/memory/environment_scope_verification.md`
- `/app/memory/bug_pytest_db_isolation.md`
- `/app/memory/orbus_r16_seed_apply_report.md` (questo file)

## Documenti aggiornati
- `/app/memory/test_credentials.md`
- `/app/memory/PRD.md`
- `/app/memory/incident_recovery_report.md`

## Nessuna cancellazione, nessun drop, nessun hard delete
Confermato.
