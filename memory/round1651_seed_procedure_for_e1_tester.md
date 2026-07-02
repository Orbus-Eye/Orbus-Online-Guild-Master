# Procedura seed dati raid per re-run e1_tester (Round 16.5.1)

Il tester ha bisogno di:
- **Test 2 (Replay raid)**: un raid `status=completed` per `tester@orbus.test`
- **Test 3 (Countdown live)**: un raid `status=in_progress` per `tester@orbus.test`

Nessun nuovo endpoint dedicato: usiamo i Tester Tools esistenti + endpoint raid pubblici.

---

## Setup base (una tantum)

Login come **admin**:
```bash
API=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2)
ADMIN_TOKEN=$(curl -sk -X POST "$API/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@orbus.test","password":"admin123"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
```

Prima marca il target come test-user (una tantum, solo se manca `is_test_user`):
```bash
# Verifica: se target_email non è test-user il Tester Tool rifiuta con 403
curl -sk "$API/api/admin/tester-tools/status?target_email=tester@orbus.test" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

Se restituisce 403 `target_is_not_a_test_user`, il DBA (o l'utente PM) deve
fare uno dei due:
- Aggiornare direttamente il record in DB (`db.users.update_one({email:"tester@orbus.test"}, {$set:{is_test_user:True}})`)
- Oppure creare un target NUOVO con email `@orbus.test` che è già whitelisted implicitamente

## Passo 1 — Fornisci roster + oro al target

Usa Tester Tool **Set MAX** per portare il target a stato completo (guild lv15,
100k oro, 20 avv lv10 attivi):

```bash
curl -sk -X POST "$API/api/admin/tester-tools/set-max" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target_email":"tester@orbus.test"}'
```

Risposta attesa: `{"applied":"MAX","snapshot_id":"...","guild_id":"..."}`

## Passo 2 — Avvia raid per Test 3 (countdown live)

Fai login come **target** e avvia un raid di lungo respiro (2-3 ore di durata
è quello che serve per Test 3, il countdown funziona anche a 10 minuti):

```bash
USER_TOKEN=$(curl -sk -X POST "$API/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"tester@orbus.test","password":"password123"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# Prendi 20 adventurer_ids del target
ADV_IDS=$(curl -sk "$API/api/adventurers" \
  -H "Authorization: Bearer $USER_TOKEN" \
  | python -c "import sys,json;a=json.load(sys.stdin)['adventurers'][:20]; import json as j; print(j.dumps([x['id'] for x in a]))")

# Prendi il primo raid_slug dal catalog (raid con difficulty più bassa)
RAID_SLUG=$(curl -sk "$API/api/raids/catalog" \
  -H "Authorization: Bearer $USER_TOKEN" \
  | python -c "import sys,json;print(json.load(sys.stdin)['raid_dungeons'][0]['slug'])")

# Divide in 4 parties da 5 avv ciascuno (schema attuale RaidStartIn)
python << PY | tee /tmp/raid_start_body.json
import json
adv_ids = $ADV_IDS
parties = [{"adventurer_ids": adv_ids[i:i+5]} for i in range(0, 20, 5)]
print(json.dumps({"raid_slug": "$RAID_SLUG", "parties": parties}))
PY

# Avvia il raid
curl -sk -X POST "$API/api/raids/start" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/raid_start_body.json
```

Risposta: `{"raid_id":"...","status":"in_progress","ends_at":"...","remaining_seconds":10800,...}`

Ora Test 3 può girare: la pagina `/raids` mostrerà una sezione "Raid in
corso" con countdown live che si aggiorna ogni secondo.

## Passo 3 — Forza completion per Test 2 (replay raid card)

Il raid appena avviato ha `ends_at` nel futuro. Per farlo comparire come
`status=completed` per Test 2, ci sono due opzioni:

### Opzione A — Attesa naturale + on-visit fallback

Attendi che `ends_at` sia passato (default 3h). Al primo GET `/api/raids`
o `/api/raids/last`, il fallback `auto_resolve_stuck_raids_for_guild` lo
completa automaticamente. Poi la Dashboard mostra la card "Ultimo Raid".

### Opzione B — Forza completion via DB (isolato o preview)

⚠️ **Solo in ambiente preview/test**. Su `orbus_r16` è tecnicamente
possibile ma il PM (utente) deve autorizzarlo esplicitamente.

```python
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
load_dotenv('/app/backend/.env')
db = MongoClient(os.environ['MONGO_URL'])['orbus_r16']
# Forza il raid attivo del tester a ends_at nel passato → prossimo
# GET /api/raids lo risolve via fallback
db.raids.update_one(
    {"status": "in_progress"},
    {"$set": {"ends_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()}},
    sort=[("started_at", -1)],
)
```

Poi il tester chiama `GET /api/raids` o naviga sulla Dashboard: il
fallback risolve il raid e la card "Ultimo Raid" appare popolata.

## Passo 4 — Verifica manuale

```bash
# Verifica card "Ultimo Raid" mostri dati
curl -sk "$API/api/raids/last" -H "Authorization: Bearer $USER_TOKEN"

# Verifica replay preview
curl -sk -X POST "$API/api/raids/replay-preview" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"raid_slug\":\"$RAID_SLUG\",\"squad_ids\":$ADV_IDS}"
```

## Se qualcosa non va

- **Cooldown attivo** (`raids.cooldown_active`): il target ha completato un raid
  di recente. Attendi 4h o azzera `guild.last_raid_completed_at`.
- **Already in progress** (`raids.already_in_progress`): il target ha
  già un raid attivo. Usa Set MAX di nuovo (che non tocca lo stato dei
  raid) e poi forza completion via Opzione B.
- **Missing adventurers** (nel replay preview): il target ha meno di 20
  avv attivi. Rilancia Set MAX (con `confirm=True`).

## Note

- I Tester Tools NON avviano/completano raid: la scelta è deliberata
  per non mescolare stato di gioco (raid runtime) e stato admin.
- Se il PM autorizza espansione dello scope, aggiungerei
  `POST /api/admin/tester-tools/seed-raid-scenario` con parametri
  `{status: in_progress|completed}` che internamente esegue Passo 2+3.
  Fuori scope del bug-fix corrente.
