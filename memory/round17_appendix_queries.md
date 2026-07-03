# Round 17.0 — Appendix: Query MongoDB e greps utilizzati

**Data**: 2026-07-03T21:30Z (UTC).
**Scopo**: trasparenza sul metodo. Tutte le query sono state read-only. Nessuna scrittura DB effettuata durante l'audit.

## Sample MongoDB queries (motor async)

```python
# Classi catalog completo
classes = await db.adventurer_classes.find({}).to_list(length=None)

# Distribuzione classi tra avventurieri
async for a in db.adventurers.find({}, {"class_slug":1,"class_name":1}):
    class_dist[a.get("class_slug")] += 1

# Item coverage per classe / slot / rarity
async for it in db.items.find({}, {"item_type":1,"rarity":1,"class_tags":1,"required_level":1}):
    for tg in (it.get("class_tags") or []):
        class_slot_count[tg][it.get("item_type")] += 1

# Distribuzione Prestigio globale
async for g in db.guilds.find({}, {"guild_level":1}):
    lvl_dist[g.get("guild_level", 0)] += 1

# XP hook events breakdown all-time
db.audit_log.aggregate([
    {"$match": {"event_type": "guild_xp_gained"}},
    {"$group": {"_id": "$source", "count": {"$sum": 1},
                "xp_total": {"$sum": "$metadata.xp_amount"}}},
    {"$sort": {"count": -1}},
])

# Achievement unlocked breakdown
db.audit_log.aggregate([
    {"$match":{"event_type":"achievement_unlocked"}},
    {"$group":{"_id":"$metadata.achievement_slug","count":{"$sum":1}}},
    {"$sort":{"count":-1}},
])

# Adventurer level distribution
async for a in db.adventurers.find({}, {"level":1}):
    lvl[a.get("level",0)] += 1

# Expedition status distribution
async for e in db.expeditions.find({}, {"status":1}):
    counter[e.get("status","?")] += 1
```

## Collections rilevanti verificate

| Collection | Count | Note |
| --- | --- | --- |
| `adventurer_classes` | 14 | ✅ tutte le classi presenti |
| `adventurers` | 2040 | 6 orfani class_slug |
| `items` | 158 | 158 totale (weapon 57, armor 40, accessory 38, altro 23) |
| `dungeons` | 22 | Lv1-Lv14, no reward field top-level esposto |
| `raids` | 1 | **doc null** — catalog vuoto |
| `achievements` | 0 | **catalog vuoto** ma 578 unlock in audit |
| `resource_gathering_missions` | 0 | **catalog vuoto** |
| `continent_resource_catalog` | 8 | continenti configurati |
| `class_halls` | 1673 | recruitment queue attiva |
| `guilds` | 289 | 96 con `guild_level` mancante |
| `expeditions` | 3 | 2 in progress + 1 completed all-time |
| `onboarding_states` | 0 | **funnel non tracciato** |
| `recipes` | 5 | crafting base |
| `legendary_recipe_catalog` | 6 | crafting endgame |
| `legendary_forge_crafting_orders` | 0 | mai usato |
| `audit_log` | 1000+ | 578 `guild_xp_gained` + `achievement_unlocked` |
| `guild_xp_daily_cap_tracker` | 2 | attivo, no duplicati |
| `mount_catalog` | 9 | Stables (out-of-scope R17.0) |
| `narrative_routes` | 5 | Stables lore |

## Code greps utilizzati

```bash
# Hook XP location
grep -rn "on_expedition_completed\|on_raid_completed\|on_resource_mission_completed" /app/backend/app/

# Curva Prestigio
cat /app/backend/app/achievements/levels.py

# Legacy guild.level update paths
grep -rn '\$inc.*"level"' /app/backend/app/
# → 0 match (confermato: `guild.level` legacy non è mai bumped)

# Achievement engine
grep -n "def add_guild_xp\|async def add_guild_xp" /app/backend/app/achievements/engine.py

# Dungeon schema
db.dungeons.find_one({"slug":"sewer-nest"}) # → base_gold_reward, base_xp_reward
```

## Metodologia

1. **Query aggregate** eseguite in un singolo script Python async per efficienza.
2. **No mutation**: solo `find`, `count_documents`, `aggregate` con `$match/$group`.
3. **Cross-check**: dove i dati audit divergevano dal catalog (es. 578 achievement unlock vs 0 achievement in collection), il divario è stato annotato in P0.
4. **Genre benchmark**: riferimenti mentali a Kingdom of Loathing (onboarding wizard), A Dark Room (minimalismo testuale), Melvor Idle (progression clarity) — nessuna copia diretta.

## Nessun dato di telemetria oltre a MongoDB

- Non ho accesso a Google Analytics, PostHog, Mixpanel o simili.
- Le stime "tempo per livello" nel report principale sono modelli teorici basati su cap giornalieri codificati.
- **Suggerimento**: agganciare event tracking client-side in R17.1 per validare i modelli.

## File di reference generati durante audit

- `/tmp/r17_audit_data.txt` — output completo delle query aggregate (raw).
- `/app/memory/round17_refoundation_audit.md` — report principale (12 sezioni).
- `/app/memory/round17_appendix_queries.md` — questo file.

**Fine appendix.**
