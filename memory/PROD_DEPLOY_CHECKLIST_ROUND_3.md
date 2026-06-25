# Production Deploy Checklist — ROUND 3.A + 3.B + 3.D
### Target: `https://orbusonline.net`
### Date: 2026-06-25 21:50

This deploy bundles ROUND 3.A (item model + IT seed), 3.B (crafting), and 3.D
(audit log + loot pool wiring + UI inventory polish). **Mercato (3.C) is
NOT in this deploy** — it will ship in a separate redeploy after validation.

---

## 1. What's shipping

### ROUND 3.A — Foundation (additive item model)
- 17 canonical Italian items seeded (5 materials, 4 weapons, 3 armors, 3 accessories, 2 consumables)
- New optional item fields: `display_name_it/en`, `description_it/en`, `stackable`, `craftable`, `is_test`, `source`, `bind_state`
- `GET /api/items` now filters `is_test=True` (anti-leak, parallel to traits)
- Idempotent seed via `update_one({"slug": ...}, "$setOnInsert/$set", upsert=True)`

### ROUND 3.B — Crafting
- 5 starter recipes seeded
- 2 new endpoints:
  - `GET /api/recipes` (per-guild eligibility with status / missing / gold_short)
  - `POST /api/recipes/{slug}/craft` (atomic decrement with rollback on conflict)
- New `/crafting` page (sidebar `FORGIA` / `FORGE`)
- i18n EN/IT (`crafting.*`, 16 keys)

### ROUND 3.D — Audit + Wiring + Polish
- New `audit_log` collection (auto-created at first boot)
- 3 compound indexes created idempotently by `ensure_audit_indexes()`
- 7 event types tracked: `loot_awarded`, `item_crafted`, `crafting_inputs_consumed`, `gold_debited`, `gold_credited`, `equip_item`, `unequip_item`
- Privacy guard: drops `password|token|hash|smtp_password|secret` keys, masks email values
- Loot pool wiring: 17 IT items automatic via global rarity pool (no per-dungeon list change). `is_test=True` excluded at roll time too.
- Inventory UI polish: header summary, type filters, rarity filters, "Materiale crafting" badge
- Report ROUND 2: `loot_found[]` now includes `display_name_it` + `display_name_en`

### Backend invariants kept
- OpenAPI path count: **43 → 45** (+2 crafting endpoints; NO admin audit endpoint)
- No schema migration. All new item/inventory fields are optional with safe defaults.
- Seeds remain idempotent (verified by double-boot test).
- `audit_log` writes never block business flow (failures → WARNING log only).

---

## 2. Pre-deploy verification (preview, complete)

| Check | Status |
| --- | --- |
| `yarn build` frontend | ✅ Compiled (194.7 kB gz) |
| ESLint on touched files | ✅ Clean |
| pytest ROUND 3.D | ✅ 7/7 |
| pytest ROUND 3.A+B | ✅ 10/10 |
| pytest ROUND 2 (report) | ✅ 15/15 |
| pytest ROUND 1.5 (inventory/equip) | ✅ 5/5 |
| pytest ROUND 1 (trait+preview) | ✅ 9/9 |
| pytest Step A2 (leaderboard) | ✅ 5/5 |
| pytest OpenAPI guard | ✅ 11/11 |
| **Total pytest** | **✅ 62/62** in 14.83s |
| Preview `/api/health` | ✅ `{"status":"ok","env":"development"}` |
| Preview `/api/openapi.json` path count | ✅ 45 |
| Preview `/api/recipes` | ✅ 5 active recipes |
| Preview `items.count(slug ∈ IT seed)` | ✅ 17 |
| Preview `audit_log` collection | ✅ exists with 3 compound indexes |
| Seed idempotency (double boot log) | ✅ "Phase 14.6: seeded 17 IT items + 5 recipes (idempotent)" |

---

## 3. Production environment variables

**No new env vars introduced** by ROUND 3.A+B+D. The audit_log collection is
created on first write/index by the running backend; nothing to configure.

Required vars (must already be set from previous deploys):
```env
APP_BASE_URL="https://orbusonline.net"
APP_ENV="production"
EMAIL_PROVIDER="smtp"
SMTP_HOST="smtp.ionos.it"
SMTP_USERNAME="support@orbusonline.net"
SMTP_PASSWORD="<from IONOS mailbox>"
EMAIL_FROM="Orbus Online <support@orbusonline.net>"
EMAIL_REPLY_TO="support@orbusonline.net"
SEND_WELCOME_EMAIL="true"
MONGO_URL="<production cluster>"
DB_NAME="<production DB>"
JWT_SECRET="<production secret>"
CORS_ORIGINS="<production origins>"
```

Quick sanity from prod pod console:
```bash
echo $APP_ENV $APP_BASE_URL $EMAIL_PROVIDER $SMTP_USERNAME
```

---

## 4. Deploy procedure (Emergent dashboard)

The agent cannot deploy. You (user) must:

1. **DB snapshot recommended** (especially because audit_log will start
   recording from this deploy onward — having a pre-deploy snapshot helps
   any timeline reconstruction).
2. **Allowlist sanity check** (read-only):
   ```python
   # in prod pod console
   await db.users.count_documents({"email": {"$in": ["mr.gualmini@gmail.com", "gianluca.brandi42@gmail.com"]}, "is_test_user": True})
   # expected: 0
   ```
3. Open **Emergent Dashboard → Orbus → Deploy → `orbusonline.net`**.
4. Confirm env vars (no changes needed).
5. Click **Redeploy**.
6. Wait for "healthy" status.
7. Ping agent: "**deploy fatto**". Agent runs §5 smoke.

### Rollback path
If §5 fails: redeploy the previous commit from the Emergent dashboard. The
`audit_log` collection will remain (harmless — empty collection on rollback).
No schema rollback needed.

---

## 5. Post-deploy smoke (executed by agent against prod, read-only)

```bash
# 5.1 health
curl -s https://orbusonline.net/api/health
# expected: {"status":"ok","env":"production"}

# 5.2 OpenAPI path count = 45
curl -s https://orbusonline.net/api/openapi.json | jq '.paths | length'
# expected: 45

# 5.3 crafting endpoints present
curl -s https://orbusonline.net/api/openapi.json | jq '.paths | keys[]' | grep recipes
# expected: "/api/recipes" and "/api/recipes/{recipe_slug}/craft"

# 5.4 leaderboard (Drakarys + Sentiero di Efreto should appear if they have power)
curl -s "https://orbusonline.net/api/leaderboard/guilds?limit=20" | jq

# 5.5 landing page
curl -s https://orbusonline.net/ | grep -o "<title>[^<]*</title>"
# expected: <title>Orbus Online: Guild Master</title>
```

What the agent **cannot** test from curl:
- UI filters / "Materiale crafting" badge / `/crafting` action → browser playtest.
- Audit log content → user verifies via prod Mongo shell.
- Real SMTP send → user triggers password reset on their own mailbox.

---

## 6. Production DB audit additions (for `prod_audit.py`)

Append these checks to the script in `PROD_AUDIT_INSTRUCTIONS.md`:

```python
# ROUND 3.A — Italian item catalog
italian_slugs = [
    "iron_shard", "raw_leather", "healing_herb", "arcane_dust", "dull_gem",
    "iron_sword", "balanced_dagger", "apprentice_staff", "path_bow",
    "light_cuirass", "reinforced_cloak", "initiate_robe",
    "chipped_ring", "wanderer_amulet", "minor_sigil",
    "minor_healing_potion", "travel_ration",
]
report["items_italian_count"] = await db.items.count_documents(
    {"slug": {"$in": italian_slugs}}
)  # expected: 17

# ROUND 3.B — Recipes
report["recipes_count_active"] = await db.recipes.count_documents(
    {"is_active": True, "is_test": {"$ne": True}}
)  # expected: 5

# ROUND 3.D — Audit log
colls = await db.list_collection_names()
report["audit_log_exists"] = "audit_log" in colls
from datetime import datetime, timezone, timedelta
since = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
report["audit_log_last_1h"] = await db.audit_log.count_documents(
    {"created_at": {"$gte": since}}
) if "audit_log" in colls else 0
report["audit_log_event_types_seen"] = await db.audit_log.distinct("event_type") if "audit_log" in colls else []
```

Sanity expectations after the deploy starts receiving traffic:
- `items_italian_count == 17`
- `recipes_count_active == 5`
- `audit_log_exists == True`
- `audit_log_event_types_seen` will grow as users play (initially empty is fine)

---

## 7. Sign-off checklist

| Owner | Action | Time |
| --- | --- | --- |
| User | DB snapshot prod | __:__ |
| User | Allowlist sanity check | __:__ |
| User | Redeploy via Emergent dashboard | __:__ |
| User | Ping agent "deploy fatto" | __:__ |
| Agent | §5 smoke checks | __:__ |
| User | Browser playtest (forge, inventory filters, audit via shell) | __:__ |
| User | Run §6 audit additions | __:__ |
| User | Validate Drakarys + Sentiero di Efreto intact | __:__ |

---

## 8. NOT in this deploy

- **Mercato (3.C)**: will ship in a separate redeploy after this one is
  validated. No market_* event types, no auction collection, no marketplace
  routes.
- **Admin audit log UI endpoint**: intentionally not exposed (`/api/admin/audit_log` deferred). Audit is consultable via Mongo shell for now.

*Document generated 2026-06-25 21:50.*
