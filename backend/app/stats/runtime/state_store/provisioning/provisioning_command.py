"""RT2-B-1B-1 · CLI provisioning command per `expedition_runtime_states`.

Comando amministrativo idempotente per creare/verificare/rimuovere la
collection su un target LOCAL-ISOLATED-ONLY. Non è cablato al runtime
applicativo — invocato manualmente o dai test integration.

Flags:
- `--dry-run` — nessuna scrittura, solo report della azione proposta
- `--apply` — esegue provisioning (idempotente)
- `--verify` — read-only check (index list + collection presence)
- `--rollback` — drop `expedition_runtime_states` (guarded)
- `--host <uri>` — Mongo URI (default `mongodb://localhost:27017`)
- `--db <name>` — database target (obbligatorio in `--apply`/`--rollback`)
- `--confirm` — richiesto per operazioni distruttive non dry-run

Guardrail invarianti (via `guards.py`):
- host = loopback
- db in allowlist (`orbus_r16_rt2b_test` OR `orbus_r16_rt2b_it_<run_id>`)
- `orbus_r16` esplicitamente bloccato

Idempotency contract:
- `create_collection` seguito da `create_index` è no-op se già consistente
- Motor `create_collection` con `check_exists=False` fallback → uso di `list_collection_names` pre-check
- `create_index` di pymongo è già idempotente (no-op se spec matcha)
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.stats.runtime.state_store.provisioning.guards import (
    ProvisioningGuardError,
    verify_target,
)


COLLECTION_NAME = "expedition_runtime_states"
TTL_FIELD = "expires_at"
TTL_EXPIRE_AFTER_SECONDS = 0
TTL_INDEX_NAME = "expedition_runtime_states_expires_at_ttl"


@dataclass
class ProvisioningReport:
    """Structured output of a provisioning/verify/rollback run."""

    action: str
    target_host: str
    target_db: str
    dry_run: bool
    collection_present_before: bool = False
    collection_present_after: bool = False
    indexes_before: List[Dict[str, Any]] = field(default_factory=list)
    indexes_after: List[Dict[str, Any]] = field(default_factory=list)
    collection_created: bool = False
    ttl_index_created: bool = False
    ttl_index_verified: bool = False
    collection_dropped: bool = False
    errors: List[str] = field(default_factory=list)
    success: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "target_host": self.target_host,
            "target_db": self.target_db,
            "dry_run": self.dry_run,
            "collection_present_before": self.collection_present_before,
            "collection_present_after": self.collection_present_after,
            "indexes_before": self.indexes_before,
            "indexes_after": self.indexes_after,
            "collection_created": self.collection_created,
            "ttl_index_created": self.ttl_index_created,
            "ttl_index_verified": self.ttl_index_verified,
            "collection_dropped": self.collection_dropped,
            "errors": self.errors,
            "success": self.success,
        }


class ProvisioningCommand:
    """Idempotent provisioning of `expedition_runtime_states`.

    The command accepts an already-configured Motor client to keep it
    unit-testable. The CLI entrypoint (`main`) constructs the client from
    `--host` after running guardrail checks.
    """

    def __init__(self, client: Any, host_uri: str, db_name: str) -> None:
        # Guardrails: MUST run BEFORE any Mongo op (idempotent to re-check).
        host, db = verify_target(host_uri, db_name)
        self._client = client
        self._host = host
        self._host_uri = host_uri
        self._db_name = db
        self._db = client[db]
        self._coll = self._db[COLLECTION_NAME]

    # ─────────────────────────── read helpers ───────────────────────────
    async def _list_collection_names(self) -> List[str]:
        return await self._db.list_collection_names()

    async def _collection_present(self) -> bool:
        return COLLECTION_NAME in await self._list_collection_names()

    async def _list_indexes(self) -> List[Dict[str, Any]]:
        """Return list of index specs from `list_indexes` cursor.

        Returns [] if collection doesn't exist. Motor's `list_indexes()`
        returns an async cursor.
        """
        try:
            cursor = self._coll.list_indexes()
            return [idx async for idx in cursor]
        except Exception:
            return []

    # ─────────────────────────── verify ───────────────────────────
    async def verify(self) -> ProvisioningReport:
        report = ProvisioningReport(
            action="verify",
            target_host=self._host,
            target_db=self._db_name,
            dry_run=True,
        )
        report.collection_present_before = await self._collection_present()
        report.collection_present_after = report.collection_present_before
        report.indexes_before = await self._list_indexes()
        report.indexes_after = report.indexes_before
        ttl_ok = any(
            idx.get("name") == TTL_INDEX_NAME
            and idx.get("expireAfterSeconds") == TTL_EXPIRE_AFTER_SECONDS
            and idx.get("key", {}).get(TTL_FIELD) == 1
            for idx in report.indexes_after
        )
        report.ttl_index_verified = ttl_ok
        if not report.collection_present_before:
            report.errors.append("collection not present")
            report.success = False
        elif not ttl_ok:
            report.errors.append(f"TTL index {TTL_INDEX_NAME!r} missing or misconfigured")
            report.success = False
        return report

    # ─────────────────────────── apply ───────────────────────────
    async def apply(self, dry_run: bool = False) -> ProvisioningReport:
        report = ProvisioningReport(
            action="apply",
            target_host=self._host,
            target_db=self._db_name,
            dry_run=dry_run,
        )
        report.collection_present_before = await self._collection_present()
        report.indexes_before = await self._list_indexes()
        if dry_run:
            report.collection_created = not report.collection_present_before
            report.ttl_index_created = not any(
                idx.get("name") == TTL_INDEX_NAME for idx in report.indexes_before
            )
            report.collection_present_after = True
            report.indexes_after = report.indexes_before
            report.ttl_index_verified = True
            return report

        # Real apply — idempotent
        if not report.collection_present_before:
            await self._db.create_collection(COLLECTION_NAME)
            report.collection_created = True

        # TTL index: create_index is idempotent (no-op if spec matches)
        pre_ttl = any(idx.get("name") == TTL_INDEX_NAME for idx in report.indexes_before)
        await self._coll.create_index(
            [(TTL_FIELD, 1)],
            expireAfterSeconds=TTL_EXPIRE_AFTER_SECONDS,
            name=TTL_INDEX_NAME,
        )
        report.ttl_index_created = not pre_ttl

        report.collection_present_after = await self._collection_present()
        report.indexes_after = await self._list_indexes()
        report.ttl_index_verified = any(
            idx.get("name") == TTL_INDEX_NAME
            and idx.get("expireAfterSeconds") == TTL_EXPIRE_AFTER_SECONDS
            and idx.get("key", {}).get(TTL_FIELD) == 1
            for idx in report.indexes_after
        )
        if not report.ttl_index_verified:
            report.errors.append("TTL index post-apply verification failed")
            report.success = False
        return report

    # ─────────────────────────── rollback ───────────────────────────
    async def rollback(self, dry_run: bool = False) -> ProvisioningReport:
        report = ProvisioningReport(
            action="rollback",
            target_host=self._host,
            target_db=self._db_name,
            dry_run=dry_run,
        )
        report.collection_present_before = await self._collection_present()
        report.indexes_before = await self._list_indexes()
        if dry_run:
            report.collection_dropped = report.collection_present_before
            report.collection_present_after = False
            report.indexes_after = []
            return report

        # Guardrails re-verified at rollback boundary
        verify_target(self._host_uri, self._db_name)

        if report.collection_present_before:
            await self._db.drop_collection(COLLECTION_NAME)
            report.collection_dropped = True

        report.collection_present_after = await self._collection_present()
        report.indexes_after = []
        if report.collection_present_after:
            report.errors.append("collection still present after drop")
            report.success = False
        return report


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="rt2_b_1b_provision_expedition_runtime_states",
        description=(
            "RT2-B-1B-1 provisioning CLI · LOCAL ISOLATED ONLY · "
            "target must be localhost + orbus_r16_rt2b_test|orbus_r16_rt2b_it_<run_id>."
        ),
    )
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Report proposed actions without writes.")
    mode.add_argument("--apply", action="store_true", help="Apply provisioning (idempotent).")
    mode.add_argument("--verify", action="store_true", help="Read-only verify.")
    mode.add_argument("--rollback", action="store_true", help="Drop collection (guarded).")
    p.add_argument(
        "--host",
        default="mongodb://localhost:27017",
        help="Mongo URI (must resolve to loopback).",
    )
    p.add_argument("--db", required=True, help="Target database (must be in allowlist).")
    p.add_argument(
        "--confirm",
        action="store_true",
        help="Required for --apply/--rollback when not dry-run.",
    )
    return p


async def _run_command(args: argparse.Namespace) -> ProvisioningReport:
    from motor.motor_asyncio import AsyncIOMotorClient  # local import (test path)

    # Guardrails FIRST (before instantiating client)
    verify_target(args.host, args.db)
    print(f"[GUARD] Mongo host verified: localhost")
    print(f"[GUARD] Database verified: {args.db}")
    print(f"TARGET: host={args.host} db={args.db}")

    client = AsyncIOMotorClient(args.host)
    try:
        cmd = ProvisioningCommand(client, args.host, args.db)
        if args.dry_run:
            return await cmd.apply(dry_run=True)
        if args.verify:
            return await cmd.verify()
        if args.apply:
            if not args.confirm:
                raise SystemExit("--apply requires --confirm when not dry-run")
            return await cmd.apply(dry_run=False)
        if args.rollback:
            if not args.confirm:
                raise SystemExit("--rollback requires --confirm when not dry-run")
            return await cmd.rollback(dry_run=False)
        raise SystemExit("no action selected")
    finally:
        client.close()


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        report = asyncio.run(_run_command(args))
    except ProvisioningGuardError as exc:
        print(f"[FAIL-STOP] {exc.code}: {exc.detail}", file=sys.stderr)
        return 2
    import json as _json
    print(_json.dumps(report.to_dict(), indent=2, default=str))
    return 0 if report.success else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "COLLECTION_NAME",
    "TTL_FIELD",
    "TTL_EXPIRE_AFTER_SECONDS",
    "TTL_INDEX_NAME",
    "ProvisioningReport",
    "ProvisioningCommand",
    "build_arg_parser",
    "main",
]
