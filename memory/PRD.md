# Orbus Online: Guild Master — PRD

## Problem statement (dall'utente)
Costruire un MMO gestionale testuale web-first ("Orbus Online: Guild Master") in cui gli utenti fondano una gilda, reclutano avventurieri, li mandano in dungeon come squadre e ricevono report narrativi degli esiti. Stack: FastAPI + MongoDB + React + JWT. UI dark minimalista, nessuna grafica pesante. Consegna a fasi.

## User personas
- **Guildmaster** — utente principale che gestisce la propria gilda: numeri, decisioni, ottimizzazione squadre.
- **Admin** — operatore che verifica lo stato server, gli account, i cataloghi (fasi future).

## Vincoli architetturali (validi per tutte le fasi)
- Modularità in `app/{accounts,guilds,adventurers,expeditions,dungeons,items,inventory,core}/`
- IDs UUID string (mai ObjectId esposti)
- Timestamp UTC ovunque
- Nessun hard delete: soft archiving via `archived_at`
- Tutta la logica di gioco nel backend
- Anti-P2W: solo oggetti cosmetici (non implementati ora)
- Nessun endpoint fuori `/api/*`

## Fasi

### ✅ Fase 0 — POC motore risoluzione spedizione — CHIUSO 2026-07-01
- File `/app/backend/app/expeditions/resolver.py` con `calculate_team_power`, `calculate_success_chance`, `resolve_expedition`.
- Report narrativo IT deterministico (seed → stesso output).
- 11/11 test pytest passati.

### ✅ Fase 1 — Auth + Guild + Dashboard — CHIUSO 2026-07-01
- Registrazione + Login JWT (bcrypt, HS256, 7 giorni).
- Endpoint: `/api/auth/{register,login,me}`, `/api/guilds`, `/api/guilds/mine`.
- Frontend: Landing, Login, Register, CreateGuild, Dashboard.
- Route guards: guest-only, auth-required, guild-required, no-guild.
- Seed idempotente: admin, tester (con Ordo Aurorae), clean.
- Dashboard mostra: level/reputation/gold/avventurieri (0), spedizioni/report placeholder, 4 quick action disabilitate.
- Smoke test curl 100% verdi.

## Backlog prossime fasi (priorità)

### P0 — Fase 2 (gameplay core)
- Recruitment + collezione avventurieri (Tank/Healer/DPS, stats, level).
- Catalogo dungeon statico (seed).
- Creazione squadra + avvio spedizione (usa `resolver.py`).
- Persistenza esiti in `expeditions` + endpoint report.
- Frontend: pagine `/recruitment`, `/adventurers`, `/dungeons`, `/expeditions/:id`.

### P1 — Fase 3
- Inventario e drop di oggetti (loot).
- Ricompense in oro/xp effettivamente applicate a gilda/avventurieri.
- Level up avventurieri.

### P2 — Fase 4
- Admin panel: reset avventurieri, override oro, health check.
- Ranking pubblico gilde (endpoint + pagina).

### P3 — Fase 5+
- Market interno, alliances, premium cosmetics (rispettando anti-P2W).

## Testing status
- Fase 0: pytest 11/11 verdi.
- Fase 1: curl smoke test 100% conformi; screenshot landing verificato manualmente.

## Credenziali di test
Vedi `/app/memory/test_credentials.md`.
