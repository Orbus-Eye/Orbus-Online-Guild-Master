"""ROUND 17.1 P0.5 (browser check) — Prep helper.

Registers a fresh test account, creates a guild (with starter roster of 5
adventurers seeded by `ensure_starter_roster`), starts an expedition on
`training-yard` with a 3-adv team, then FORCES the expedition to fail by
directly patching `db.expeditions.<id>.success_chance = 0` in Mongo.

This is a **runtime override** (single expedition doc, single guild) —
NO service code change, NO drop table change, NO reward global change.

Guard-rails:
  - Only affects the freshly-created expedition doc.
  - Audit event `TEST_FORCED_FAIL_APPLIED` written before the patch.
  - Audit event `TEST_FORCED_FAIL_REVERTED` NOT applicable (nothing to revert:
    the `success_chance` field is per-expedition, not per-dungeon; the
    training-yard dungeon config is never touched).

Prints JSON with `email`, `password`, `report_url` for Playwright to consume.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Load backend .env so MONGO_URL / DB_NAME / REACT_APP_BACKEND_URL are visible.
load_dotenv(Path("/app/backend/.env"))
load_dotenv(Path("/app/frontend/.env"))


BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BACKEND_URL:
    print(json.dumps({"error": "REACT_APP_BACKEND_URL missing"}))
    sys.exit(1)

API = f"{BACKEND_URL}/api"


async def _register_and_seed(client: httpx.AsyncClient, email: str, password: str, username: str):
    r = await client.post(
        f"{API}/auth/register",
        json={"email": email, "password": password, "username": username},
    )
    r.raise_for_status()
    token = r.json()["access_token"]
    # Backend sets both access_token cookie AND csrf_token cookie on register.
    # Since httpx keeps cookies, subsequent mutating requests need X-CSRF-Token
    # header matching the csrf_token cookie (double-submit CSRF).
    csrf = client.cookies.get("csrf_token")
    headers = {"Authorization": f"Bearer {token}"}
    if csrf:
        headers["X-CSRF-Token"] = csrf
    return token, headers


async def _create_guild(client: httpx.AsyncClient, headers: dict, guild_name: str) -> dict:
    r = await client.post(
        f"{API}/guilds",
        headers=headers,
        json={"name": guild_name, "description": "R17.1 fallback UI check"},
    )
    r.raise_for_status()
    return r.json()


async def _list_adventurers(client: httpx.AsyncClient, headers: dict) -> list[dict]:
    r = await client.get(f"{API}/adventurers", headers=headers)
    r.raise_for_status()
    body = r.json()
    if isinstance(body, dict):
        return body.get("adventurers", body.get("items", []))
    return body


async def _find_training_yard(client: httpx.AsyncClient, headers: dict) -> dict | None:
    r = await client.get(f"{API}/expeditions?starter=training-yard", headers=headers)
    r.raise_for_status()
    body = r.json()
    dungeons = body.get("dungeons") if isinstance(body, dict) else None
    if dungeons is None:
        # Fallback: some builds return the list directly.
        r2 = await client.get(f"{API}/dungeons", headers=headers)
        if r2.status_code == 200:
            b2 = r2.json()
            dungeons = b2.get("dungeons") if isinstance(b2, dict) else b2
    for d in (dungeons or []):
        if d.get("slug") == "training-yard":
            return d
    return None


async def _start_expedition(
    client: httpx.AsyncClient, headers: dict, dungeon_id: str, adventurer_ids: list[str]
) -> dict:
    r = await client.post(
        f"{API}/expeditions",
        headers=headers,
        json={"dungeon_id": dungeon_id, "adventurer_ids": adventurer_ids},
    )
    r.raise_for_status()
    body = r.json()
    return body.get("expedition", body)


async def _force_fail_and_shorten(exp_id: str, guild_id: str):
    """Runtime override: set expedition success_chance=0 + completes_at=now
    so the sweep at next GET completes it as failed.

    Also writes an audit event TEST_FORCED_FAIL_APPLIED for traceability.
    NO change to dungeon config, NO change to service code.
    """
    from motor.motor_asyncio import AsyncIOMotorClient

    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"]]

    now = datetime.now(timezone.utc)
    past = now.isoformat()

    # Snapshot pre-override
    exp_pre = await db.expeditions.find_one({"id": exp_id}, {"_id": 0})
    snap = {
        "exp_id": exp_id,
        "success_chance_before": exp_pre.get("success_chance"),
        "completes_at_before": exp_pre.get("completes_at"),
        "status_before": exp_pre.get("status"),
    }

    # Audit-only marker (best-effort; if audit_log write fails, ignore).
    try:
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "event_type": "TEST_FORCED_FAIL_APPLIED",
            "actor_guild_id": guild_id,
            "source": "r171_browser_check",
            "related_entity_id": exp_id,
            "metadata": {"snapshot": snap, "reason": "R17.1 fallback UI check"},
            "created_at": past,
        })
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] audit write failed (non-blocking): {exc}", file=sys.stderr)

    # Runtime override on the single expedition doc: force fail + shortcut.
    await db.expeditions.update_one(
        {"id": exp_id, "status": "in_progress"},
        {
            "$set": {
                "success_chance": 0,  # cannot beat: randint(1,100) > 0 always
                "completes_at": past,  # already due → sweep completes it
            }
        },
    )

    c.close()
    return snap


async def _wait_for_completion(client: httpx.AsyncClient, headers: dict, exp_id: str, timeout_s: int = 30) -> dict:
    """Poll GET report until status becomes completed/failed."""
    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        r = await client.get(f"{API}/expeditions/{exp_id}", headers=headers)
        r.raise_for_status()
        body = r.json()
        exp = body.get("expedition", {})
        last = body
        if exp.get("status") in ("completed", "failed") or exp.get("result_summary") in ("Failed", "Success"):
            return body
        await asyncio.sleep(1.5)
    return last or {}


async def main():
    ts = int(time.time())
    email = f"r171-fallback-ui-{ts}@orbus.test"
    password = "Testpass123!"
    username = f"r171fb{ts}"[:20]

    async with httpx.AsyncClient(timeout=30.0) as client:
        _, headers = await _register_and_seed(client, email, password, username)
        guild = await _create_guild(client, headers, f"Fallback Guild {ts}")
        guild_id = guild.get("id") or guild.get("guild", {}).get("id")

        advs = await _list_adventurers(client, headers)
        if len(advs) < 3:
            print(json.dumps({"error": f"expected ≥3 adventurers, got {len(advs)}"}))
            sys.exit(2)

        dungeon = await _find_training_yard(client, headers)
        if not dungeon:
            print(json.dumps({"error": "training-yard dungeon not found"}))
            sys.exit(3)

        team = [a["id"] for a in advs[:3]]
        exp = await _start_expedition(client, headers, dungeon["id"], team)
        exp_id = exp.get("id")
        if not exp_id:
            print(json.dumps({"error": "no expedition id", "raw": exp}))
            sys.exit(4)

        snap = await _force_fail_and_shorten(exp_id, guild_id)
        final = await _wait_for_completion(client, headers, exp_id)
        exp_final = final.get("expedition", {})

        out = {
            "email": email,
            "password": password,
            "username": username,
            "guild_id": guild_id,
            "expedition_id": exp_id,
            "dungeon_slug": dungeon.get("slug"),
            "report_url": f"{BACKEND_URL}/expeditions/{exp_id}",
            "final_status": exp_final.get("status"),
            "final_result_summary": exp_final.get("result_summary"),
            "fallback_reward_payload": final.get("fallback_reward"),
            "force_override_snapshot": snap,
        }
        print(json.dumps(out, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
