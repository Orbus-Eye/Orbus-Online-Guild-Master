# FASE 1.10 — Censimento testi/nomi inglesi residui

Generato da `scripts/fase1_censimento_testi_inglesi.py`.
Euristica a parole segnale: aspettarsi qualche falso positivo.
Le voci elencate sono la lista di lavoro traduzioni per la Fase 3.

## Frontend — 5 stringhe sospette

- `frontend/src/pages/AdminTesterTools.jsx:206` — guild.level
- `frontend/src/pages/AdminTesterTools.jsx:207` — guild.gold
- `frontend/src/pages/AdminTesterTools.jsx:208` — max_team_power_ever
- `frontend/src/pages/Guide.jsx:579` — required_adventurer_level
- `frontend/src/pages/Guide.jsx:605` — HTTP 423 equipment.required_level_not_met

## Backend (messaggi player-facing) — 8 stringhe sospette

- `backend/app/chat/services.py:111` — chat.guild_required
- `backend/app/expeditions/preview.py:95` — Questo dungeon richiede esattamente {required} avventurieri
- `backend/app/expeditions/services.py:1152` — Questo dungeon richiede esattamente {dungeon['required_team_size']} avventurieri
- `backend/app/resources/__init__.py:474` — Richiede Livello di Gilda {MIN_GUILD_LEVEL} per raccogliere risorse.
- `backend/app/squads/services.py:118` — adventurer_ids.size_invalid (expected {expected}, got {len(adventurer_ids)})
- `backend/app/squads/services.py:158` — adventurer_ids.not_in_guild ({len(missing)} ids)
- `backend/app/squads/services.py:224` — raid_parties.not_allowed_for_type
- `backend/app/squads/services.py:309` — raid_parties.not_allowed_for_type

## DB items

Esegui con `--db` (env MONGO_URL/DB_NAME) per aggiungere
l'audit degli item senza `display_name_it`.
