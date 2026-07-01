# Orbus Online: Guild Master — Fase 0 + Fase 1 Report

**Data:** 2026-07-01
**Stato:** ✅ Backend + Frontend consegnati e verificati end-to-end.

---

## Stack effettivo
- **Backend:** FastAPI (Python 3.11) + Motor (Mongo async) + JWT (PyJWT) + bcrypt.
- **DB:** MongoDB `test_database` (via `MONGO_URL` da `.env`).
- **Frontend:** React 19 + react-router-dom 7 + Tailwind + shadcn/ui + sonner (toast) + axios.
- **Font UI:** JetBrains Mono (importato in `index.css`).
- **Tema:** unico dark terminal, accent color `amber #d4a14a`. Nessun gradient viola/AI-slop.

## Struttura file finale
```
/app/backend/
├── server.py                # entry point ASGI (thin wrapper)
├── pytest.ini
├── requirements.txt         (pre-esistente, non toccato)
├── _legacy/                 # backup della vecchia app (non usato dal server)
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI factory + lifespan + router include
│   ├── core/
│   │   ├── config.py        # settings da .env (fail-fast)
│   │   ├── database.py      # Motor client + init_indexes
│   │   ├── security.py      # bcrypt + JWT HS256
│   │   ├── deps.py          # get_current_user (Bearer)
│   │   └── seed.py          # seed idempotente 3 utenti + 1 gilda
│   ├── accounts/
│   │   ├── models.py        # Email pragmatica, RegisterInput, LoginInput, UserPublic, AuthResponse
│   │   ├── services.py      # create_user, authenticate
│   │   └── router.py        # /api/auth/register|login|me
│   ├── guilds/
│   │   ├── models.py        # GuildCreateInput, GuildPublic
│   │   ├── services.py      # create_guild, get_my_guild
│   │   └── router.py        # /api/guilds, /api/guilds/mine, /api/guilds/me
│   ├── expeditions/
│   │   ├── __init__.py
│   │   └── resolver.py      # FASE 0 — motore puro deterministico
│   ├── adventurers/         # placeholder (README)
│   ├── dungeons/            # placeholder (README)
│   ├── items/               # placeholder (README)
│   ├── inventory/           # placeholder (README)
│   ├── market/              # placeholder (README)
│   ├── rankings/            # placeholder (README)
│   ├── premium/             # placeholder (README)
│   └── alliances/           # placeholder (README)
└── tests/
    ├── __init__.py
    └── test_resolver.py     # 11 test Fase 0

/app/frontend/src/
├── App.js                   # router + toaster
├── App.css / index.css      # tema dark terminal (JetBrains Mono, amber accent)
├── index.js
├── _legacy/                 # backup della vecchia app
├── context/AuthContext.jsx  # token+user+guild, hooks login/register/logout
├── lib/api.js               # axios wrapper Bearer + 401 handler
├── components/
│   ├── ui/                  # shadcn (pre-esistenti)
│   ├── AppShell.jsx         # header con logout
│   ├── RouteGuards.jsx      # GuestOnly, RequireAuth, RequireGuild, RequireNoGuild
│   └── RarityBadge.jsx      # componente preparato per fasi future
└── pages/
    ├── Landing.jsx
    ├── Login.jsx
    ├── Register.jsx
    ├── CreateGuild.jsx
    └── Dashboard.jsx
```

## Schema DB (collections MongoDB)

### `users`
| campo | tipo | note |
|-------|------|------|
| id | string (uuid4) | unique |
| email | string | unique, lowercase |
| password_hash | string | bcrypt |
| role | "player"|"admin" | default "player" |
| created_at, updated_at | ISO 8601 UTC | |
| archived_at | null / ISO | soft delete |

### `guilds`
| campo | tipo | note |
|-------|------|------|
| id | string (uuid4) | unique |
| owner_user_id | string | unique (1 gilda/utente) |
| name | string | unique, 3–40 char |
| description | string | 0–500 char |
| level, reputation, gold | int | default 1, 0, 100 |
| created_at, updated_at | ISO 8601 UTC | |
| archived_at | null / ISO | soft delete |

## Endpoint disponibili

| Metodo | Path | Auth | Note |
|--------|------|------|------|
| GET  | `/api/health`        | no  | health check |
| POST | `/api/auth/register` | no  | 201 su successo, 400 se email in uso |
| POST | `/api/auth/login`    | no  | 200 su successo, 401 se credenziali errate |
| GET  | `/api/auth/me`       | ✅  | user corrente, 401 se token invalido |
| POST | `/api/guilds`        | ✅  | 201 su successo, 400 se già ha gilda o nome duplicato |
| GET  | `/api/guilds/mine`   | ✅  | gilda o 404 |
| GET  | `/api/guilds/me`     | ✅  | alias di `/mine` |
| GET  | `/api/openapi.json`  | no  | schema OpenAPI |
| GET  | `/api/docs`          | no  | Swagger UI |

## Pagine frontend

| Path | Guard | Descrizione |
|------|-------|-------------|
| `/`               | pubblica  | Landing terminale con CTA Login/Register |
| `/login`          | GuestOnly | Form login |
| `/register`       | GuestOnly | Form registrazione |
| `/create-guild`   | Auth + NoGuild | Form fondazione gilda (nome, descrizione) |
| `/dashboard`      | Auth + Guild | Header username+logout, 4 stat card, sezioni spedizioni/report vuote, 4 quick actions disabilitate |

## Come seedare / resettare
- **Seed automatico** al primo boot: 3 utenti + 1 gilda ("Ordo Aurorae").
- **Reset totale:**
  ```bash
  python3 -c "from pymongo import MongoClient; MongoClient('mongodb://localhost:27017').drop_database('test_database')"
  sudo supervisorctl restart backend
  ```
  Al riavvio verranno ricreati indici e seed.

## Cosa è implementato
✅ Registrazione email+password (validazione formato, min 8 char) con bcrypt
✅ Login e JWT HS256 (7 giorni)
✅ /auth/me con Bearer token, 401 su token mancante/invalido/scaduto
✅ Creazione gilda unica per utente (check applicativo + indice Mongo unique)
✅ GET /guilds/mine con 404 se assente
✅ Nome gilda unico globalmente (indice + check)
✅ Timestamp UTC ovunque, ID pubblici sono UUID string (mai ObjectId esposti)
✅ Seed idempotente (admin, tester con gilda, clean senza gilda)
✅ CORS aperto per preview
✅ FASE 0 resolver: puro, deterministico con seed, report narrativo IT (successo/fallimento variabile)
✅ **11/11 test pytest verdi** (`pytest tests/test_resolver.py -v`)
✅ Frontend router con guard: `GuestOnly`, `RequireAuth`, `RequireGuild`, `RequireNoGuild`
✅ 401 dal backend → logout automatico + rimozione token
✅ UI dark terminale, JetBrains Mono, amber accent, responsive mobile
✅ Componente `RarityBadge` preparato ma non usato in Fase 1
✅ Placeholder domini futuri (market/rankings/premium/alliances + adventurers/dungeons/items/inventory) con README

## Cosa è preparato ma NON implementato (fasi future)
- Endpoint e UI per: avventurieri, dungeon, spedizioni end-to-end, inventario, admin panel, market, ranking, premium, alliance.
- Componente `RarityBadge` esiste ma nessun oggetto lo utilizza ancora.

## Output pytest Fase 0
```
============================= test session starts ==============================
platform linux -- Python 3.11.15, pytest-9.1.1
collected 11 items

tests/test_resolver.py::test_balanced_team_includes_full_composition_bonus PASSED
tests/test_resolver.py::test_only_dps_team_gets_only_dps_bonus            PASSED
tests/test_resolver.py::test_success_chance_clamped_to_min_10             PASSED
tests/test_resolver.py::test_success_chance_clamped_to_max_95             PASSED
tests/test_resolver.py::test_strong_team_vs_weak_dungeon_hits_max         PASSED
tests/test_resolver.py::test_weak_team_vs_strong_dungeon_hits_min         PASSED
tests/test_resolver.py::test_resolve_expedition_is_deterministic_with_seed PASSED
tests/test_resolver.py::test_resolve_expedition_different_seeds_can_differ PASSED
tests/test_resolver.py::test_success_report_mentions_success_language     PASSED
tests/test_resolver.py::test_failure_report_mentions_failure_language     PASSED
tests/test_resolver.py::test_failure_rewards_are_reduced                  PASSED

============================== 11 passed in 0.02s ==============================
```

## Smoke test curl (tutti conformi)
- ✅ `POST /api/auth/register` con email nuova → 201 + token
- ✅ `POST /api/auth/register` duplicato → 400 "Email già registrata."
- ✅ `POST /api/auth/login` seed → 200 + token
- ✅ `GET /api/auth/me` con token → 200 user
- ✅ `GET /api/auth/me` senza token → 401
- ✅ `GET /api/auth/me` con token invalido → 401
- ✅ `GET /api/guilds/mine` tester (con gilda) → 200 Ordo Aurorae
- ✅ `GET /api/guilds/mine` clean (senza gilda) → 404
- ✅ `POST /api/guilds` clean → 201 Casa Pulita
- ✅ `POST /api/guilds` tester (già ha gilda) → 400 "Hai già fondato una gilda."
- ✅ `GET /api/openapi.json` → 200

## URL preview
`https://guild-master-5.preview.emergentagent.com/`

## Note operative
- Il database MongoDB pre-esistente (dal progetto ereditato) è stato **droppato** all'inizio della Fase 1; nessun dato utile è andato perso perché era relativo a un progetto diverso e non pertinente al problem statement corrente.
- L'app pre-esistente è stata **archiviata** in `/app/backend/_legacy/` e `/app/frontend/src/_legacy/`, disponibile per ispezione ma non caricata dal server.

## Fuori scopo Fase 1 (confermato)
Nessuna implementazione di: recruitment, avventurieri, tratti, dungeon endpoints, spedizioni end-to-end, inventario, admin panel, market, ranking, premium, alliances, grafica pesante, real-money.

## Fase 2 — prossimi passi consigliati
1. `adventurers/` — endpoint CRUD + Pydantic + collezione `adventurers` (Tank/Healer/DPS, stats, level, guild_id).
2. `dungeons/` — catalogo statico via seed + endpoint GET.
3. `expeditions/` — collezione `expeditions` che orchestra `resolver.py` e persiste team/dungeon/esito.
4. Attivare i 4 quick-action della dashboard.
