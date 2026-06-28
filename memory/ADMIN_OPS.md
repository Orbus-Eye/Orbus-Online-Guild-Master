# Admin Ops — Runbook (Round 11.2 TASK 5/6)

Documentazione operativa per gli endpoint admin-only introdotti in ROUND 11.2 (TASK 5a/5b)
e per i due endpoint pubblici di catalog (TASK 6 G1-G2). Audience: ops/sysadmin e tester
QA. Tutto quello che segue è **già in produzione** (Round 11.2 deploy in attesa di approvazione).

---

## 1. Accesso & autorizzazione

### 1.1 Chi può accedere
- Solo utenti con `users.is_admin = true` nel DB (campo booleano).
- In `APP_ENV != production`, l'account `tester@orbus.test` viene seeded con `is_admin=true`
  ad ogni boot (idempotente). Vedi `app/seeds/seed_runner.py:seed_tester`.
- In produzione, **niente seed automatico**: bisogna promuovere un user a mano (vedi §6).

### 1.2 Frontend route
- `/admin/ops` — pagina React con 3 tab (Search / Detail / Audit).
- Se l'utente loggato non è admin → pagina `NotAuthorized` (nessun redirect silente).

### 1.3 Auth flow (post Round 11.1 Slice 2)
Due meccanismi supportati, entrambi compatibili con gli endpoint admin:

| Meccanismo | Quando usarlo |
|---|---|
| **Cookie + CSRF** (raccomandato) | Frontend SPA, client moderni. `withCredentials: true`, `X-CSRF-Token` su POST. |
| **Bearer fallback** (14gg) | Script di ops, server-to-server, test suite legacy. `Authorization: Bearer <jwt>`. |

Il backend emette un log `auth.legacy_bearer_usage` ad ogni chiamata Bearer, così
monitoriamo quanti client legacy esistono prima del cleanup (~14 giorni post-deploy).

---

## 2. Endpoint admin (prefisso `/api/admin`)

Tutti richiedono `is_admin=true` (`Depends(get_admin_user)`).

| Metodo | Path | Funzione |
|---|---|---|
| GET  | `/api/admin/guilds/search?q=&limit=20&offset=0` | Ricerca per nome (regex case-insensitive) o `public_id` (8 hex). Ritorna shape paginata. |
| GET  | `/api/admin/guilds/{id_or_public}` | Dettaglio gilda + roster cap + struttura territory. Accetta `id` UUID o `public_id`. |
| POST | `/api/admin/guilds/{id}/grant-gold` | Body `{amount, reason}`. Max 100k oro/op. Atomic `$inc`. Audit-trail. |
| POST | `/api/admin/guilds/{id}/grant-item` | Body `{item_slug, quantity, reason}`. Max 1000/op. Stackable upsert. Audit-trail. |
| GET  | `/api/admin/audit?guild=&action=&since=&limit=50&offset=0` | Lista audit eventi filtrabili. PII-masked. |

### 2.1 Limiti hard-coded
| Limite | Default | Override env |
|---|---|---|
| `ADMIN_MAX_GRANT_GOLD` | 100.000 oro/operazione | `ADMIN_MAX_GRANT_GOLD=<int>` |
| `ADMIN_MAX_GRANT_ITEM_QTY` | 1.000 unità/operazione | `ADMIN_MAX_GRANT_ITEM_QTY=<int>` |
| `search.limit` | 50 max (1..50) | n/a |
| `audit.limit` | 200 max (1..200) | n/a |

Oltre il cap → HTTP **422** con codice strutturato (`admin.grant_gold.amount_over_max` /
`admin.grant_item.qty_over_max`).

### 2.2 Validazione & errori comuni
| Codice | Causa | Status |
|---|---|---|
| `admin.guild.not_found` | id o public_id non trovato | 404 |
| `admin.item.unknown_slug` | slug item inesistente in `db.items` | 422 |
| `admin.item.bound_not_grantable` | item template marcato `is_bound=true` | 422 |
| `admin.item.p2w_blocked` | item `can_be_sold_for_real_money + affects_combat` (no cosmetic) | 422 |
| `auth.csrf.invalid` | header `X-CSRF-Token` assente o non coincide con cookie | 403 |

### 2.3 Audit trail
Ogni grant scrive in `db.audit_log` un evento con campi:
- `event_type`: `admin_gold_granted` o `admin_item_granted`
- `actor_user_id`: id admin
- `actor_guild_id`: id gilda target (NB: non l'autore!)
- `metadata.admin_actor_email_masked`: email mascherata (`f***@orbus.test`)
- `metadata.target_guild_public_id`: hash 8-hex per consultazione
- `metadata.reason`: motivazione fornita dall'admin
- `metadata.gold_before` / `gold_after` o `inventory_entries_created`
- `created_at`: ISO UTC

L'`audit_event_id` viene **restituito al client** ed è ricercabile in `/api/admin/audit`.

---

## 3. Endpoint pubblici catalog (TASK 6 G1-G2)

Entrambi **NO AUTH** (intenzionalmente pubblici, PII-safe).

| Metodo | Path | Funzione |
|---|---|---|
| GET | `/api/traits/catalog` | Lista trait giocatore-safe. Filtra `is_test=true` e `is_active=false`. Sort: rarity → display_name_it. |
| GET | `/api/stats/catalog` | Lista stat code-defined (`app/stats/public_catalog.py`). Include `power_score` derivato. |

Shape `/api/traits/catalog`:
```json
{
  "total": 41,
  "traits": [
    {
      "id": "...",
      "display_name_it": "Coraggioso",
      "display_name_en": "Brave",
      "description_it": "Saldo sotto pressione, ...",
      "description_en": "Steady under pressure, ...",
      "rarity": "common",
      "polarity": "positive",
      "affected_stat": "strength",
      "modifier_type": "flat",
      "modifier_value": 1.0
    }
  ]
}
```

Shape `/api/stats/catalog`:
```json
{
  "total": 11,
  "stats": [
    {
      "key": "strength",
      "display_name_it": "Forza",
      "display_name_en": "Strength",
      "description_it": "Determina il danno fisico ...",
      "description_en": "Determines physical damage ...",
      "affects_pwr": true,
      "ui_locations": ["adventurer-card", "detail-stats"],
      "implemented": true
    }
  ]
}
```

---

## 4. Esempi `curl` (1 per endpoint)

Setup variabili (Bearer mode):
```bash
API="$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2)"
TOKEN=$(curl -s -X POST "$API/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"tester@orbus.test","password":"password123"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
```

### 4.1 Search gilde
```bash
curl -s "$API/api/admin/guilds/search?q=Eclipse&limit=10" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### 4.2 Detail gilda
```bash
curl -s "$API/api/admin/guilds/<public_id_or_uuid>" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### 4.3 Grant gold (Bearer)
```bash
curl -s -X POST "$API/api/admin/guilds/<public_id>/grant-gold" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 500, "reason": "Refund compensativo bug spec atomicity"}'
```

### 4.4 Grant item (Cookie + CSRF — flusso preferito post Round 11.1.2)
```bash
# 1) Login: cattura cookie nel jar
curl -s -c /tmp/jar.txt -X POST "$API/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"tester@orbus.test","password":"password123"}' >/dev/null

# 2) Estrai CSRF token (cookie `csrf_token` è JS-readable, qui via grep)
CSRF=$(grep csrf_token /tmp/jar.txt | tail -1 | awk '{print $7}')

# 3) Esegui la mutazione con cookie + header
curl -s -b /tmp/jar.txt -X POST "$API/api/admin/guilds/<public_id>/grant-item" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF" \
  -d '{"item_slug": "iron_shard", "quantity": 10, "reason": "Compensazione lost shipment"}'
```

### 4.5 Audit list (filtrato per gilda + action + data)
```bash
curl -s "$API/api/admin/audit?guild=<public_id>&action=admin_gold_granted&since=2026-06-01T00:00:00Z" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### 4.6 Catalog pubblici (NO AUTH richiesta)
```bash
curl -s "$API/api/traits/catalog" | python3 -m json.tool | head -30
curl -s "$API/api/stats/catalog" | python3 -m json.tool
```

---

## 5. Audit query patterns frequenti

```bash
# Tutti i grant-gold dell'ultimo giorno UTC
curl -s "$API/api/admin/audit?action=admin_gold_granted&since=$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)" \
  -H "Authorization: Bearer $TOKEN"

# Tutti gli interventi su una gilda specifica
curl -s "$API/api/admin/audit?guild=<public_id>&limit=100" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 6. Bootstrap produzione (promozione primo admin)

In produzione **nessun seed automatico**. Per promuovere il primo admin:

```bash
# Via mongo shell (su pod prod)
mongosh "$MONGO_URL/$DB_NAME" --eval '
  db.users.updateOne(
    {email: "ops@orbus-online.example"},
    {$set: {is_admin: true, updated_at: new Date().toISOString()}}
  )
'

# Verifica
mongosh "$MONGO_URL/$DB_NAME" --eval '
  db.users.findOne({email: "ops@orbus-online.example"}, {is_admin: 1, email: 1})
'
```

Dopo la promozione, l'admin può fare login e accedere a `/admin/ops`. Nessun restart richiesto.

**Revoca**: setta `is_admin: false`. Il JWT esistente conserva la claim originale, quindi
forza anche il logout/refresh dell'admin (la prossima `GET /api/auth/me` riflette il flag dal DB).

---

## 7. Sicurezza & best practice

- **NEVER** condividere il JWT in chat / log / screenshot. Il token vale 7 giorni di accesso pieno.
- I `reason` dei grant sono visibili a tutti gli admin via `/api/admin/audit` — usa un linguaggio professionale, niente dati sensibili dei player.
- I limiti `ADMIN_MAX_GRANT_*` sono per-operazione, non per-giornata. Se ti serve un grant > cap, splittalo in più chiamate (ognuna audit-trailed indipendentemente).
- Gli item bound (`is_bound=true`) **non** sono grantabili — è una guard volontaria contro errori di policy.
- Per audit di alto volume, considera l'index su `audit_log.event_type + created_at` (già attivo, vedi `app/audit/log.py`).

---

## 8. Limiti noti / Roadmap

- **O(n)** search by `public_id`: il backend scansiona fino a 2000 gilde. P2 ticket: aggiungere campo materializzato `guilds.public_id` con index unico (vedi REFACTOR_LOG, voce 11.2-P2).
- **Bearer fallback** rimosso ~14 giorni post-deploy Round 11.1 Slice 2. Monitora `auth.legacy_bearer_usage` log e migra eventuali script ops a cookie+CSRF prima del cleanup.

---

*Ultimo aggiornamento: Round 11.2 TASK 6, 2026-06-28.*
