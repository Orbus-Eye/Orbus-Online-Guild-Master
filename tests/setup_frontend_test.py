"""Setup user + bound item for frontend Phase17 testing."""
import os, uuid, sys, json
import requests
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path("/app/backend/.env"))

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") if os.environ.get("REACT_APP_BACKEND_URL") else None
if not BASE_URL:
    # fallback parsing /app/frontend/.env
    for line in open("/app/frontend/.env"):
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
            break

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
print(f"BASE={BASE_URL}, DB={DB_NAME}")

tag = f"fe_p17_{uuid.uuid4().hex[:6]}"
email = f"{tag}@orbus.test"
password = "Test12345!"

# Register
r = requests.post(f"{BASE_URL}/api/auth/register",
    json={"email": email, "username": tag, "password": password}, timeout=15)
print("register:", r.status_code)
assert r.status_code == 201, r.text
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

# Create guild
r2 = requests.post(f"{BASE_URL}/api/guilds",
    json={"name": f"Forge Test {tag[-4:]}", "description": ""},
    headers=h, timeout=15)
print("guild:", r2.status_code)
assert r2.status_code == 201, r2.text
gid = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).json()["guild"]["id"]
print("guild_id:", gid)

# Direct DB: seed gold + iron_shard + drake_slayer_helm
client = MongoClient(MONGO_URL)
db = client[DB_NAME]
db.guilds.update_one({"id": gid}, {"$inc": {"gold": 5000}})

def _add_inv(slug, qty=1, *, refinement_level=0, enchants=None, affixes=None, is_bound=False):
    item = db.items.find_one({"slug": slug})
    assert item, f"item {slug} not seeded"
    row_id = str(uuid.uuid4())
    db.inventory_items.insert_one({
        "id": row_id,
        "instance_id": str(uuid.uuid4()),
        "guild_id": gid,
        "item_id": item["id"],
        "quantity": qty,
        "refinement_level": refinement_level,
        "enchants": enchants or [],
        "affixes": affixes or [],
        "reroll_count": 0,
        "is_bound": is_bound,
        "disenchanted_at": None,
        "acquired_at": "2026-06-26T00:00:00+00:00",
        "source": "fe_test",
    })
    return row_id

# Iron shards for refine ops
iron_id = _add_inv("iron_shard", qty=20, is_bound=False)
# Bound legendary item (already refined)
bound_id = _add_inv("drake_slayer_helm", qty=1, refinement_level=1, is_bound=True,
                    affixes=[{"slug": "atk_pct_5", "name": "+5% ATK", "value": 5}])
# Unbound legendary for forge demonstration
unbound_id = _add_inv("drake_slayer_chest", qty=1, is_bound=False)

print(json.dumps({
    "email": email, "password": password, "guild_id": gid,
    "iron_row_id": iron_id, "bound_row_id": bound_id, "unbound_row_id": unbound_id,
    "base_url": BASE_URL,
}))
