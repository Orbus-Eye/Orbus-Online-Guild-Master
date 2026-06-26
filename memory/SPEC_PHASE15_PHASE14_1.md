# SPEC — Phase 15 (Daily Streak) + Phase 14.1 (Weekly Quest Variety)

> Documento di specifica contrattuale. Nessuna modifica al codice senza approvazione
> esplicita del prodotto.

---

## 1. Field Naming — IMPORTANTE

> 🔒 **Contratto API stabile**: il campo che indica il valore obiettivo di una
> weekly quest si chiama **`objective_target`** (canonical).
>
> - ⚠️ **NON rinominare** `objective_target` → `target`. Una rinomina romperebbe:
>   - il frontend `WeeklyQuestsCard.jsx` (usa `quest.objective_target`)
>   - i 22 test backend (`backend_phase15_streak_phase14_1_weekly_test.py`)
>   - eventuali consumer mobile / esterni.
> - Il prefisso `objective_` mantiene coerenza con `objective_type`
>   (`expeditions_completed`, `items_crafted`, `market_purchases`, ...).
>
> Qualunque nuovo campo futuro relativo agli obiettivi quest DEVE seguire la
> convenzione `objective_*`.

---

## 2. API Contract — `/api/quests/weekly`

### Request
```http
GET /api/quests/weekly
Authorization: Bearer <jwt>
```

### Response — `200 OK`
```json
{
  "rotation_week": "2026-W26",
  "next_reset_at": "2026-06-29T00:00:00+00:00",
  "quests": [
    {
      "slug": "weekly_run_expeditions_3",
      "display_key": "quests.weekly.run_expeditions_3",
      "objective_type": "expeditions_completed",
      "objective_target": 3,
      "progress": 0,
      "completed": false,
      "claimed": false,
      "can_claim": false,
      "reward_gold": 150,
      "reward_materials": [
        {"slug": "iron_shard", "qty": 2}
      ],
      "completed_at": null,
      "claimed_at": null
    }
  ]
}
```

### Field reference
| Field | Type | Meaning |
|---|---|---|
| `rotation_week` | string | ISO week key, e.g. `"2026-W26"`. Server-authoritative. |
| `next_reset_at` | ISO datetime (UTC) | Next Monday 00:00 UTC. |
| `quests[].slug` | string | Stable identifier for claim endpoint. |
| `quests[].display_key` | string | i18n key, e.g. `"quests.weekly.run_expeditions_3"`. |
| `quests[].objective_type` | enum | One of: `expeditions_completed`, `items_crafted`, `market_purchases`, `items_equipped`, `expedition_loot_items`, `market_listings_created`. |
| **`quests[].objective_target`** | int | **Canonical name.** The progress threshold required to complete the quest. **NON rinominare a `target`.** |
| `quests[].progress` | int | Current progress, capped at `objective_target`. |
| `quests[].completed` | bool | `progress >= objective_target`. |
| `quests[].claimed` | bool | True once user has redeemed the reward. |
| `quests[].can_claim` | bool | `completed && !claimed`. |
| `quests[].reward_gold` | int | 80–180 gold (binding economy). |
| `quests[].reward_materials` | list | 0–2 entries `{slug, qty}` — only Common/Uncommon items. |
| `quests[].completed_at` | ISO datetime \| null | Stamped when `progress` first reaches `objective_target`. |
| `quests[].claimed_at` | ISO datetime \| null | Stamped on successful claim. |

---

## 3. API Contract — `/api/quests/weekly/claim/{slug}`

### Request
```http
POST /api/quests/weekly/claim/{slug}
Authorization: Bearer <jwt>
```

### Responses
| Code | Meaning |
|---|---|
| `200` | Claim successful. Returns `{success, slug, gold_granted, materials_granted, guild_gold, weekly}`. |
| `404` | Unknown slug (not in active rotation). |
| `409` | Already claimed this week. |
| `422` | Quest not yet completed (`progress < objective_target`). |

---

## 4. API Contract — `/api/quests/streak`

### Request
```http
GET /api/quests/streak
Authorization: Bearer <jwt>
```

### Response — `200 OK`
```json
{
  "current": 0,
  "longest": 0,
  "last_streak_date": null,
  "today_completed": false,
  "next_reset_at": "2026-06-27T00:00:00+00:00",
  "current_tier": null,
  "current_reward": null,
  "can_claim_reward": false,
  "schedule": [
    {"day": 1, "reward": {"gold": 20, "materials": []}},
    {"day": 3, "reward": {"gold": 50, "materials": [{"slug": "iron_shard", "qty": 2}]}},
    {"day": 5, "reward": {"gold": 100, "materials": [{"slug": "arcane_dust", "qty": 1}]}},
    {"day": 7, "reward": {"gold": 200, "materials": [{"slug": "healing_herb", "qty": 3}]}}
  ]
}
```

### Field reference
| Field | Type | Meaning |
|---|---|---|
| `current` | int | Current consecutive days (0–30 soft cap). |
| `longest` | int | All-time best streak. Preserved across resets. |
| `last_streak_date` | YYYY-MM-DD UTC \| null | Last UTC date a daily quest was claimed. |
| `today_completed` | bool | `last_streak_date == today` AND `current > 0`. |
| `next_reset_at` | ISO datetime UTC | Tomorrow 00:00 UTC. |
| `current_tier` | int \| null | Highest unlocked tier in `{1,3,5,7}` for this cycle. |
| `current_reward` | object \| null | The reward object for `current_tier`. |
| `can_claim_reward` | bool | True iff `current_tier` has not been claimed in the current 7-day cycle. |
| `schedule` | list | Static reference of all tier rewards. |

---

## 5. API Contract — `/api/quests/streak/claim/{tier}`

### Request
```http
POST /api/quests/streak/claim/{tier}    # tier ∈ {1, 3, 5, 7}
Authorization: Bearer <jwt>
```

### Responses
| Code | Meaning |
|---|---|
| `200` | Claim successful. Returns `{success, tier, gold_granted, materials_granted, guild_gold, streak}`. |
| `404` | Unknown tier (not in `{1,3,5,7}`). |
| `409` | Reward already claimed for this 7-day cycle. |
| `422` | `current_tier != tier` (the requested tier is not currently unlocked). |

---

## 6. Locked Economy (binding)

| Layer | Tier / Quest | Gold | Materials |
|---|---|---|---|
| Daily Streak | D1 | 20 | — |
| Daily Streak | D3 | 50 | iron_shard ×2 (Common) |
| Daily Streak | D5 | 100 | arcane_dust ×1 (Uncommon) |
| Daily Streak | D7 | 200 | healing_herb ×3 (Common) |
| Daily Streak cycle | — | — | Cycles every 7 days past D7, soft cap at day 30. |
| Weekly | `weekly_run_expeditions_3` | 150 | iron_shard ×2 |
| Weekly | `weekly_craft_items_2` | 180 | arcane_dust ×1 |
| Weekly | `weekly_market_buy_1` | 100 | raw_leather ×2 |
| Weekly | `weekly_equip_items_3` | 80 | healing_herb ×1 |
| Weekly | `weekly_expedition_loot_10` | 160 | dull_gem ×1 |
| Weekly | `weekly_market_listings_1` | 100 | raw_leather ×1 |

Weekly: 4 quests visible/week (rotating via ISO week index), theoretical max
~700g + materials per week.

### Invariants (DO NOT break)
- ❌ **No reputation** rewarded by streak or weekly.
- ❌ **No power gear** rewarded by streak or weekly (Common/Uncommon materials only).
- ❌ **No premium / pay-to-win** mechanic in any quest reward.
- ✅ Every claim emits an `audit_log` row (`streak_reward_claimed`, `weekly_quest_claimed`, `quest_reward_claimed`).
- ✅ Claims are atomic (Mongo CAS) and idempotent (double-claim → 409).
- ✅ Reset windows are server-authoritative (UTC).

---

## 7. Source of truth

- Backend constants: `/app/backend/app/quests/services.py` — `STREAK_REWARDS`, `WEEKLY_QUEST_POOL`, `WEEKLY_ACTIVE_COUNT`.
- Routes: `/app/backend/app/quests/routes.py`.
- Audit events: `/app/backend/app/audit/log.py` (`EVENT_TYPES` set).
- Frontend: `/app/frontend/src/components/StreakBadge.jsx`, `/app/frontend/src/components/WeeklyQuestsCard.jsx`.
- Tests: `/app/backend/tests/backend_phase15_streak_phase14_1_weekly_test.py` (22 tests, contract-locking).

---

## Changelog

- **2026-06-26** — Phase 15 + Phase 14.1 shipped. 22/22 backend tests PASS, 7/10
  frontend E2E PASS (3 deferred, backend-covered). No regressions on existing
  daily quest / market / crafting / equipment suites after updating 3
  hardcoded OpenAPI path-count assertions (49 → 53).
- **2026-06-26** — Field naming locked: `objective_target` is the canonical
  API field name for weekly quest thresholds. Documented to prevent future
  refactors from regressing the frontend.
