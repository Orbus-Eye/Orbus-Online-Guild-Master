# Prod Raid Recovery Runbook — Orbus Online: Guild Master (Round 16.x)

**Data creazione**: 2026-07-01
**Autore**: incident recovery pipeline
**Ambito**: recovery raid `status=in_progress` bloccati dopo `ends_at` in produzione.
**Ambiente target**: cluster prod (`orbusonline.net`) — NON il preview.
**Ambiente sviluppo verificato**: preview `orbus_r16` DB, `guild-master-5.preview.emergentagent.com`.

---

## 0. TL;DR

Il codice legacy Round 16.1.1 **contiene già la fix on-visit fallback** in `app/raids/__init__.py`:
- `GET /api/raids` chiama `auto_resolve_stuck_raids_for_guild()` best-effort prima di listare i raid.
- `GET /api/raids/{raid_id}` chiama `resolve_stuck_raid()` best-effort prima di rispondere.
- Entrambe le chiamate sono in try/except (fail-safe: la GET risponde sempre 200 anche se la recovery raise).

Il fix `recovery.py` filtra rigidamente `status=in_progress AND ends_at<=now` con CAS transition `in_progress → resolving` per evitare double-resolve concorrente.

**Non serve alcuna modifica al codice prod.** Serve solo eseguire lo script di recovery una tantum (o attendere che la prima visita dell'utente triggeri il fallback).

---

## 1. Preconditions (SEMPRE, in ordine)

1. Backup snapshot del cluster prod (mongodump o snapshot volumetrico). Nome consigliato:
   `orbus_prod_pre_raid_recovery_YYYYMMDD_HHMM.tar.gz`.
2. Verificare `MONGO_URL` prod e `DB_NAME` prod da vault/secret manager (NON da `.env` locale).
3. Aprire finestra di manutenzione (o bassa affluenza): raid recovery scrive su `raids`, `raid_participants`, `guilds` (reset `expedition_in_progress=False`), `adventurers` (reset `is_available=true`), `audit_log`.
4. Notificare i team owner delle gilde con raid stuck (via chat in-game o email di cortesia).

---

## 2. Diagnostica read-only (OBBLIGATORIA prima di ogni scrittura)

Eseguire da un pod con accesso al Mongo prod. **NON usare `mongosh` con drop/updateMany.**

### 2.1 Conta i raid stuck globalmente

```python
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os, asyncio, json

async def diag():
    client = AsyncIOMotorClient(os.environ["MONGO_URL_PROD"])
    db = client[os.environ["DB_NAME_PROD"]]
    now_iso = datetime.now(timezone.utc).isoformat()
    q = {"status": "in_progress", "ends_at": {"$lte": now_iso}}
    total = await db.raids.count_documents(q)
    per_guild = await db.raids.aggregate([
        {"$match": q},
        {"$group": {"_id": "$guild_id", "n": {"$sum": 1}}},
        {"$sort": {"n": -1}},
    ]).to_list(200)
    print(json.dumps({"stuck_total": total, "per_guild": per_guild}, default=str, indent=2))

asyncio.run(diag())
```

Salva output in `/app/memory/prod_raid_stuck_diag_YYYYMMDD.json`.

### 2.2 Verifica gilde impattate

```python
# Per ogni guild_id trovato sopra, controlla flag expedition_in_progress
# e stato adventurers.is_available.
async def guild_state(guild_id):
    g = await db.guilds.find_one({"id": guild_id}, {"_id":0,"name":1,"expedition_in_progress":1})
    advs = await db.adventurers.count_documents({"guild_id": guild_id, "is_available": False})
    print(guild_id, g, "adv_busy=", advs)
```

Nessuna scrittura in questo step.

---

## 3. Recovery in DRY RUN (evidence-only)

Il codice espone `resolve_stuck_raid(db, raid_id, dry_run=True, reason=...)` in `app/raids/recovery.py`.

**Non commit** — legge lo stato, calcola la risoluzione forzata (outcome=timeout_forced), ritorna il diff senza scrivere.

Esempio orchestrazione dry-run globale:

```python
async def dry_run_all():
    now_iso = datetime.now(timezone.utc).isoformat()
    raids_stuck = await db.raids.find(
        {"status": "in_progress", "ends_at": {"$lte": now_iso}},
        {"_id": 0, "id": 1, "guild_id": 1, "ends_at": 1},
    ).to_list(500)
    results = []
    from app.raids.recovery import resolve_stuck_raid
    for r in raids_stuck:
        res = await resolve_stuck_raid(
            db, r["id"], dry_run=True, reason="prod_recovery_dry_run_YYYYMMDD",
        )
        results.append(res)
    with open("/app/memory/prod_raid_dry_run_report_YYYYMMDD.json", "w") as f:
        json.dump(results, f, default=str, indent=2)
```

**Revisione manuale obbligatoria** del JSON di dry-run prima di procedere:
- controlla che ogni raid abbia `eligible=true` e `reason != ends_at_invalid`.
- verifica che il numero di participants abbia senso (no fantasmi).

---

## 4. Recovery apply (solo se dry-run OK)

Due strategie alternative — **scegli UNA**, non entrambe:

### 4.A — Strategia "on-visit" passiva (raccomandata, zero-touch)

Non fare nulla di più. Alla prossima visita utente ai path `GET /api/raids` o `GET /api/raids/{id}`, il codice `raids/__init__.py:684-687` e `raids/__init__.py:699-705` chiama automaticamente `resolve_stuck_raid()` fail-safe.

**Pro**: nessun cron, nessuna manutenzione, ogni utente sblocca solo la propria gilda quando torna in gioco.
**Contro**: se un utente non torna, il raid resta stuck (impatto solo per lui, non per il sistema).

Se questa è la scelta:
- Aggiungi entry `chronicle` in prod: "hotfix raid on-visit attivo dal $DATE — nessun'azione richiesta".
- Fine.

### 4.B — Strategia "batch" (apply forzato)

Solo se manutenzione pianificata e vuoi risolvere tutto in una passata.

```python
async def apply_all():
    now_iso = datetime.now(timezone.utc).isoformat()
    raids_stuck = await db.raids.find(
        {"status": "in_progress", "ends_at": {"$lte": now_iso}},
        {"_id": 0, "id": 1},
    ).to_list(500)
    from app.raids.recovery import resolve_stuck_raid
    ok, fail = 0, 0
    for r in raids_stuck:
        res = await resolve_stuck_raid(
            db, r["id"], dry_run=False, reason="prod_recovery_apply_YYYYMMDD",
        )
        if res.get("ok"):
            ok += 1
        else:
            fail += 1
            print("FAIL", r["id"], res)
    print(f"apply done: ok={ok} fail={fail}")
```

**Vincoli**:
- Ogni chiamata a `resolve_stuck_raid()` è idempotente (CAS `status=in_progress → resolving`). Rieseguibile in caso di failure parziale.
- Se un raid è già stato preso in carico da un'altra chiamata concorrente, il CAS ritorna `already_resolving` e non fa danni.

---

## 5. Post-apply verification

```python
# Deve tornare 0 (o comunque un valore stabile e non crescente)
still_stuck = await db.raids.count_documents(
    {"status": "in_progress", "ends_at": {"$lte": datetime.now(timezone.utc).isoformat()}},
)
print("still_stuck=", still_stuck)

# Verifica che nessuna gilda abbia expedition_in_progress residuo senza raid attivo
async for g in db.guilds.find({"expedition_in_progress": True}, {"_id":0,"id":1,"name":1}):
    active = await db.raids.count_documents({"guild_id": g["id"], "status": "in_progress"})
    if active == 0:
        print("orphan expedition_in_progress:", g)
```

Se `still_stuck > 0`: rieseguire step 4.B (idempotente).

Se `orphan expedition_in_progress`: bug residuo — apri incident separato, NON toccare a mano.

---

## 6. Rollback

Il fix on-visit **NON è disabilitabile senza deploy**. Se qualcosa va storto:

1. Ripristina lo snapshot Mongo dal step 1.
2. Deploy immediato del codice precedente (`git revert` del commit hotfix on-visit se necessario).
3. Comunica agli utenti.

**Non** cercare di "sistemare" i raid a mano con `updateMany`: è la strada per corruzione del gioco.

---

## 7. Comunicazione utenti

Template messaggio in-game (chat globale / consortium chat):

> Manutenzione lampo: i raid rimasti bloccati oltre il tempo di scadenza sono stati risolti automaticamente con esito `timeout_forced`. La reputazione e l'oro sono stati calcolati sulla base dei progressi effettivi. Nessuna perdita di avventurieri. Grazie della pazienza.

---

## 8. Checklist finale prima di chiudere l'incident

- [ ] Snapshot Mongo prod archiviato
- [ ] Diagnostica read-only report salvato in `/app/memory/prod_raid_stuck_diag_YYYYMMDD.json`
- [ ] Dry-run report salvato in `/app/memory/prod_raid_dry_run_report_YYYYMMDD.json`
- [ ] Scelta strategia 4.A o 4.B documentata
- [ ] (Se 4.B) apply report con `ok/fail` counts
- [ ] Verifica post-apply `still_stuck=0`
- [ ] Nessun `orphan expedition_in_progress` residuo
- [ ] Chronicle entry aggiunta in prod
- [ ] Utenti impattati notificati

---

## 9. Riferimenti codice

| Path | Cosa fa |
|---|---|
| `app/raids/__init__.py:684-687` | Chiama `auto_resolve_stuck_raids_for_guild()` in `GET /api/raids` (fail-safe) |
| `app/raids/__init__.py:699-705` | Chiama `resolve_stuck_raid()` in `GET /api/raids/{id}` (fail-safe) |
| `app/raids/recovery.py:97-249` | `resolve_stuck_raid()` — filtro `in_progress + ends_at<=now` + CAS + calcolo outcome |
| `app/raids/recovery.py:351-401` | `auto_resolve_stuck_raids_for_guild()` — batch per gilda |
| `app/raids/recovery.py:120-132` | Filtri di eligibility (guardia contro `status!=in_progress` e `now < ends_at`) |
| `app/raids/recovery.py:144-148` | CAS transition `in_progress → resolving` (anti-doppio) |

---

**Fine runbook.** Ogni deviazione dagli step qui sopra richiede autorizzazione esplicita dell'owner del progetto.
