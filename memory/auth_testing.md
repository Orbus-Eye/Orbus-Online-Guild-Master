# Orbus Online — Flusso Auth per Testing

## Panoramica
- Auth type: **JWT Bearer** HS256, TTL 7 giorni, secret in `JWT_SECRET` del backend `.env`.
- Header richiesto sugli endpoint protetti: `Authorization: Bearer <access_token>`.
- Su risposta 401 il frontend rimuove il token dal localStorage e forza il logout.

## Endpoint

| Metodo | Path | Auth | Body | Success |
|-------|------|------|------|---------|
| GET  | `/api/health`         | no  | —                             | 200 `{status:"ok"}` |
| POST | `/api/auth/register`  | no  | `{email,password}`            | 201 `{user, access_token}` |
| POST | `/api/auth/login`     | no  | `{email,password}`            | 200 `{user, access_token}` |
| GET  | `/api/auth/me`        | ✅  | —                             | 200 `{id,email,role,created_at}` |
| POST | `/api/guilds`         | ✅  | `{name,description}`          | 201 guild JSON |
| GET  | `/api/guilds/mine`    | ✅  | —                             | 200 guild JSON / 404 |

Alias: `GET /api/guilds/me` è equivalente a `GET /api/guilds/mine`.

## Flusso completo (curl)
```bash
API=https://drain-dispatch.preview.emergentagent.com

# 1) Login
TOKEN=$(curl -s -X POST $API/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"tester@orbus.test","password":"password123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2) User corrente
curl -s $API/api/auth/me -H "Authorization: Bearer $TOKEN"

# 3) Gilda dell'utente
curl -s $API/api/guilds/mine -H "Authorization: Bearer $TOKEN"
```

## Errori tipici
- **400 `Email già registrata.`** — POST /api/auth/register con email esistente.
- **400 `Hai già fondato una gilda.`** — POST /api/guilds se l'utente ne ha già una.
- **400 `Nome gilda già in uso.`** — POST /api/guilds con nome duplicato.
- **401 `Token di accesso mancante.`** — endpoint protetto senza `Authorization`.
- **401 `Token di accesso non valido.`** / **`Sessione scaduta.`** — JWT invalido o expirato.
- **404 `Nessuna gilda trovata per questo utente.`** — GET /api/guilds/mine per utente senza gilda.
- **422** — errori di validazione Pydantic (formato email, lunghezza password, ecc.).
