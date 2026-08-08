# FASE 1.10 — Censimento testi/nomi inglesi residui

Generato da `scripts/fase1_censimento_testi_inglesi.py`.
Euristica a parole segnale: aspettarsi qualche falso positivo.
Le voci elencate sono la lista di lavoro traduzioni per la Fase 3.

## Frontend — 19 stringhe sospette

- `frontend/src/pages/Admin.jsx:172` — Gold reward
- `frontend/src/pages/Admin.jsx:209` — Level required
- `frontend/src/pages/Admin.jsx:234` — Sellable for gold
- `frontend/src/pages/AdminTesterTools.jsx:206` — guild.level
- `frontend/src/pages/AdminTesterTools.jsx:207` — guild.gold
- `frontend/src/pages/AdminTesterTools.jsx:208` — max_team_power_ever
- `frontend/src/pages/guide/R161GuideSections.jsx:53` — COME SCEGLIERE UN TEAM DUNGEON · Building a dungeon team
- `frontend/src/pages/Guide.jsx:72` — peak team power
- `frontend/src/pages/Guide.jsx:93` — Peak Team Power
- `frontend/src/pages/Guide.jsx:313` — recommended power
- `frontend/src/pages/Guide.jsx:394` — min_adventurer_level
- `frontend/src/pages/Guide.jsx:415` — : massimo team power mai raggiunto da una squadra della gilda.
- `frontend/src/pages/Guide.jsx:572` — required_adventurer_level
- `frontend/src/pages/Guide.jsx:598` — HTTP 423 equipment.required_level_not_met
- `frontend/src/pages/Guide.jsx:890` — NO power gear nei reward: nessun oggetto con bonus combattimento.
- `frontend/src/pages/Guide.jsx:891` — NO premium / NO XP gilda diretta: la progressione resta nelle spedizioni.
- `frontend/src/pages/Guide.jsx:892` — Reward bilanciati: daily 30% / weekly 80% / milestone-T3 200% di un dungeon clear standard.
- `frontend/src/pages/Guide.jsx:999` — Controlla il max team power
- `frontend/src/pages/Guide.jsx:1106` — : massimo team_power raggiunto.

## Backend (messaggi player-facing) — 48 stringhe sospette

- `backend/app/adventurers/routes.py:280` — Adventurer not found
- `backend/app/adventurers/services.py:365` — Adventurer not found
- `backend/app/adventurers/services.py:448` — Adventurer not found
- `backend/app/chat/services.py:111` — chat.guild_required
- `backend/app/crafting/services.py:164` — Requires guild level {recipe.get('required_guild_level', 1)}
- `backend/app/crafting/services.py:173` — Item '{slug}' is not available
- `backend/app/crafting/services.py:178` — Not enough gold
- `backend/app/equipment/services.py:145` — Adventurer not found
- `backend/app/equipment/services.py:180` — Cannot modify equipment of adventurer currently in expedition
- `backend/app/equipment/services.py:250` — Item not in your guild inventory
- `backend/app/equipment/services.py:287` — Item not available (already equipped on another adventurer)
- `backend/app/equipment/services.py:389` — Cannot modify equipment of adventurer currently in expedition
- `backend/app/expeditions/preview.py:80` — dungeon_id is required
- `backend/app/expeditions/preview.py:82` — adventurer_ids is required
- `backend/app/expeditions/preview.py:86` — Dungeon not found
- `backend/app/expeditions/preview.py:92` — This dungeon requires exactly {required} adventurers
- `backend/app/expeditions/preview.py:105` — One or more adventurers do not belong to your guild
- `backend/app/expeditions/services.py:944` — Dungeon not found
- `backend/app/expeditions/services.py:956` — Duplicate adventurer in team
- `backend/app/expeditions/services.py:960` — This dungeon requires exactly {dungeon['required_team_size']} adventurers
- `backend/app/expeditions/services.py:972` — Adventurer {aid} not found in your guild
- `backend/app/expeditions/services.py:980` — Adventurer {adv['name']} is not available
- `backend/app/expeditions/services.py:1366` — No completed expedition yet
- `backend/app/expeditions/services.py:1381` — No completed expedition yet
- `backend/app/expeditions/services.py:1405` — Expedition not found
- `backend/app/guilds/services.py:57` — No guild found for this user
- `backend/app/guilds/services.py:71` — You already own a guild
- `backend/app/guilds/services.py:108` — You already own a guild
- `backend/app/market/services.py:266` — Item cannot be sold for gold
- `backend/app/market/services.py:272` — Not enough available quantity (have {available}, want {quantity})
- `backend/app/market/services.py:435` — Only the seller can cancel this listing
- `backend/app/market/services.py:438` — Listing is not active (status={listing['status']})
- `backend/app/market/services.py:492` — Listing not available (status={listing['status']})
- `backend/app/market/services.py:578` — Not enough gold
- `backend/app/quests/services.py:285` — Quest not completed yet
- `backend/app/quests/services.py:451` — Reward already claimed for this cycle
- `backend/app/quests/services.py:472` — Reward already claimed for this cycle
- `backend/app/quests/services.py:671` — Weekly quest not completed yet
- `backend/app/raids/__init__.py:169` — raid_dungeon_not_found
- `backend/app/raids/__init__.py:590` — raids.not_ended_yet
- `backend/app/raids/__init__.py:999` — no_completed_raid
- `backend/app/recruitment/services.py:345` — Insufficient gold (need {cost}, have {gold})
- `backend/app/recruitment/services.py:387` — Refresh state changed concurrently, please retry
- `backend/app/resources/__init__.py:474` — Richiede Livello di Gilda {MIN_GUILD_LEVEL} per raccogliere risorse.
- `backend/app/squads/services.py:118` — adventurer_ids.size_invalid (expected {expected}, got {len(adventurer_ids)})
- `backend/app/squads/services.py:158` — adventurer_ids.not_in_guild ({len(missing)} ids)
- `backend/app/squads/services.py:224` — raid_parties.not_allowed_for_type
- `backend/app/squads/services.py:309` — raid_parties.not_allowed_for_type

## DB items

Esegui con `--db` (env MONGO_URL/DB_NAME) per aggiungere
l'audit degli item senza `display_name_it`.
