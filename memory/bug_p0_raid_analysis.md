# Bug P0 — Raid Stuck: Analisi (STEP 1.A)

Data: 2026-07-01 13:47 UTC
DB target: `orbus_r16` (locale al pod preview/dev)

## Sintesi one-line
**Nel DB `orbus_r16` attuale non ci sono raid stuck da recuperare** (`raids: 0`, `raid_participants: 0`). I 3 adventurer bloccati e le 2 expeditions in_progress sono tutti su **gilde archiviate junk** (nomi R6B2A, OC — archiviate ieri dallo STEP 7 recovery). Nessun problema attuale sulle 4 gilde attive.

Se il tester ha riportato un bug "raid stuck" reale, **stava operando su un'istanza diversa** (probabilmente produzione o preview URL diversa) — non su questo pod. Il codice di recovery `app/raids/recovery.py` + `app/scripts/recover_stuck_raids.py` **esiste già** ed è progettato bene (CAS-based, idempotente, deterministic replay). Se il bug è reale in altra istanza, quella fix è già disponibile e va solo lanciata lì.

---

## Numeri chiave

### Collection raid-related
| collection | count |
|---|---|
| `raids` | **0** |
| `raid_participants` | 0 |
| `raid_dungeons` | 3 (catalogo statico) |
| `squads` | 2 (entrambe `is_test_user_data=true` con adventurer_ids placeholder `"x"`, `"y"`) |
| `adventurers` | 890 |
| adventurers `is_available=false` | **3** |
| `expeditions` (status="in_progress") | **2** (dati fantasma, vedi sotto) |

### Adventurers bloccati (3)
| id | name | guild_id | guild status |
|---|---|---|---|
| `b01d8b81…` | Retire Test | `257280d8…` | **archived_pre_launch=true** (R6B2A 73f3db) |
| `c91e4af0…` | Retire Test | `9d8493e4…` | **archived_pre_launch=true** (R6B2A 4e88d9) |
| `24d175c6…` | Test Adv 0 | `6c0ac604…` | **archived_pre_launch=true** (OC 28fb95) |

Tutti e 3 hanno nomi `Retire Test` / `Test Adv 0` (residui di test lifecycle), tutti in gilde archiviate.

### Expeditions in_progress (2) — DATI FANTASMA
```json
{ "id": "08cb03c6...", "guild_id": "1e005e0e...", "dungeon": undefined,
  "started_at": undefined, "ends_at": undefined,
  "adventurer_ids": ["73497c29..."] }
{ "id": "460a4bd8...", "guild_id": "011ee09d...", "dungeon": undefined,
  "started_at": undefined, "ends_at": undefined,
  "adventurer_ids": ["f7070845..."] }
```
- Entrambe legate a gilde **archived_pre_launch=true** (`R6B2A ed4c58`, `R6B2A eda667`).
- Tutti i timestamp sono `undefined` → dati sporchi da test bugati / seed abortiti.
- `ends_at < now` count: **0** → non falliscono il check "stuck" perché `ends_at` è undefined.

### Gilde attive (non archiviate) — check parallelo
| gilda | adventurer occupati |
|---|---|
| Custodi del Vento (demo opp) | 0 |
| Esiliati del Vuoto (demo opp) | 0 |
| Compagnia delle Tre Lune (demo opp) | 0 |
| la lanterna di ferro (tester) | 0 |
| Test Admin Guild (admin, appena creata) | 0 |

**Zero problemi sulle gilde attive.**

---

## Codice raid già presente

### `/app/backend/app/raids/__init__.py` (~700 righe)
Endpoint completi (montati sotto `/api/raids`):
- `GET /catalog`
- `POST /preview`
- `POST /` (`start_raid`)
- `POST /{raid_id}/complete`
- `GET /`
- `GET /{raid_id}`

### `/app/backend/app/raids/recovery.py` (401 righe)
Funzioni:
- `resolve_stuck_raid(db, raid_id, dry_run)` — idempotente, CAS-based su `status="in_progress"`, replay deterministico con RNG seedato da `raid_id`.
- `_preview_recovery(db, raid)` — dry-run puro read-only.

**Estratto commento sorgente** (importante per root cause futuro):
> "il complete_raid è manuale, nessuno scheduler globale lo invoca"

**Root cause architetturale**: manca uno scheduler background che chiami `complete_raid` quando `ends_at` viene raggiunto. Il completamento è gated sull'azione dell'utente. Se l'utente non torna, il raid resta in_progress ma non ha reward assegnate.

**Mitigazione consigliata**: aggiungere on-visit fallback in `GET /api/raids/mine` e `GET /api/raids/{raid_id}` che chiami `resolve_stuck_raid` per raid propri con `ends_at < now`. **Non l'ho fatto perché il bug non è riproducibile nel DB attuale.** Se il tester conferma che serve, lo aggiungo mirato.

### `/app/backend/app/scripts/recover_stuck_raids.py` (124 righe)
CLI dry-run/apply. Supporta:
- `--dry-run` (default) — mostra `[raid_id | guild_id | members_blocked | proposed_outcome | reward_dup_risk]`
- `--apply` — esegue recovery
- `--raid-id X` — singolo raid
- Reward dup risk check: cerca `audit_log` per event `raid_completed`/`raid_recovered` sullo stesso `raid_id`.

**Se lanciato ORA su `orbus_r16`**: output sarà `raid stuck: 0 → nothing to recover`.

---

## Ipotesi sul report del tester

Il tester ha riportato "raid stuck" ma dal DB attuale non emerge nulla. Ipotesi ordinata per plausibilità:

1. **Il tester opera su produzione (cluster esterno)**, non sul pod preview. I raid stuck vivono lì. La fix esiste già in codice — va solo eseguita in prod.
2. **Il tester ha visto il bug su una sessione precedente al recovery**. Il recovery odierno + cleanup gilde ha implicitamente archiviato tutto quello che poteva essere "stuck". Oggi il DB è pulito, il bug non si ripresenta.
3. **Il tester chiama "raid" un'altra entità** (expedition, dungeon, quest). Le 2 expeditions ghost potrebbero essere quello, ma sono su gilde archiviate.
4. **Il bug è latente**: manca on-visit fallback, quindi qualsiasi raid futuro che l'utente abbandona finirà stuck. Va fixato come prevention anche se ora non si manifesta.

---

## Cosa NON ho fatto

- ❌ Non ho eseguito `recover_stuck_raids.py --apply` (non c'è nulla da recuperare).
- ❌ Non ho toccato le 2 expedition ghost né i 3 adventurer bloccati (sono su gilde archiviate; NON è compito di questa recovery pulirli).
- ❌ Non ho eseguito `recover_stuck_raids.py --dry-run` (posso farlo se vuoi la conferma "0 stuck").
- ❌ Non ho modificato `app/raids/__init__.py` per aggiungere on-visit fallback (attendo tua conferma sul fix "prevention").

---

## Attendo la tua decisione

**Opzioni**:

**A) Lancio dry-run del recovery esistente** su `orbus_r16` per confermare via evidence che non c'è nulla. Output atteso: `stuck: 0`. Sicuro (nessuna scrittura).

**B) Passo direttamente al BUG 2 (Forgia 404)** dato che il bug 1 non è riproducibile in questo pod, e la fix eventuale (recover_stuck_raids.py) è già disponibile per essere eseguita altrove. **Consiglio B.**

**C) Applico il fix "prevention" on-visit fallback** in `GET /api/raids/mine` e `GET /api/raids/{raid_id}` anche se il bug non è riproducibile ora, per evitare regressioni future. Modifica al codice legacy → serve tua autorizzazione.

**D) Pulisco anche i 3 adventurer/2 expeditions ghost** (soft-flag `archived=true` o `is_available=true`) — sono su gilde archiviate, quindi tecnicamente non impattano il gameplay. **Non consigliato**: sono dati fossili, non c'è utente reale in attesa. Solo pulizia cosmetica.

Attendo tua indicazione. Il mio consiglio è **B** (passo a Forgia 404 subito).
