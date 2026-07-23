"""RT2-B-1A · conftest · fixtures parametrizzati fake / mongo-mocked.

Ogni contract test riceve un `store: ExpeditionRuntimeStateStore` iniettato
in due varianti:
- `fake`: `FakeExpeditionRuntimeStateStore` in-memory.
- `mongo_mock`: `MongoExpeditionRuntimeStateStore` con **collection mocked**
  che simula in-memory il comportamento di `find_one_and_update / find_one /
  insert_one / delete_one`. Mai un real DB, mai una network call.

Il mock Mongo replica la semantica CAS/filter matching per gli stessi
scenari attesi. Non usa `mongomock` (non presente in stack): usa
`unittest.mock.AsyncMock` con implementazione custom Python.

Clock injection: `frozen_clock` fixture per test deterministici.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

import pytest

from app.stats.runtime.state_store import (
    ExpeditionRuntimeStateStore,
    FakeExpeditionRuntimeStateStore,
    MongoExpeditionRuntimeStateStore,
)


# ═══════════════════════ FROZEN CLOCK ═══════════════════════
class _FrozenClock:
    """Clock deterministico avanzabile a mano per test."""

    def __init__(self, start: datetime) -> None:
        self._t = start

    def __call__(self) -> datetime:
        return self._t

    def advance(self, seconds: int) -> None:
        self._t = self._t + timedelta(seconds=seconds)


@pytest.fixture
def frozen_clock() -> _FrozenClock:
    return _FrozenClock(datetime(2026, 2, 1, 12, 0, 0, tzinfo=timezone.utc))


# ═══════════════════════ MOCKED MONGO COLLECTION ═══════════════════════
class _InMemoryMongoCollectionMock:
    """Implementazione in-memory del subset di Mongo API che l'adapter chiama.

    Metodi coperti:
        - insert_one
        - find_one (con projection best-effort · ritorna tutto il doc)
        - find_one_and_update (filtro + update con $inc, $set, $push)
        - delete_one

    Non è un mock di comodo: implementa la semantica CAS filter matching
    (equality + $ne + $lt + $gt + $nin + $or) necessaria per l'adapter.
    Nessuna network call, nessun DB.

    NOTA: non è un mongomock completo; supporta solo i pattern esatti usati
    da `MongoExpeditionRuntimeStateStore`.
    """

    def __init__(self) -> None:
        self.docs: Dict[str, Dict[str, Any]] = {}
        # Call log for injection contract verification
        self.calls: List[Dict[str, Any]] = []

    # ── helpers ────────────────────────────────────────────────
    def _match(self, doc: Dict[str, Any], filt: Dict[str, Any]) -> bool:
        for k, v in filt.items():
            if k == "$or":
                if not any(self._match(doc, sub) for sub in v):
                    return False
                continue
            actual = _get_path(doc, k)
            if isinstance(v, dict):
                for op, opval in v.items():
                    if op == "$ne":
                        if actual == opval:
                            return False
                        # for nested-array checks like "processed_event_keys.event_id": {"$ne": X}
                        # actual may be a list of values; ensure X ∉ actual
                        if isinstance(actual, list) and opval in actual:
                            return False
                    elif op == "$lt":
                        if actual is None or actual >= opval:
                            return False
                    elif op == "$gt":
                        if actual is None or actual <= opval:
                            return False
                    elif op == "$nin":
                        if actual in opval:
                            return False
                    else:
                        # unsupported operator → treat as mismatch (safer)
                        return False
            else:
                if actual != v:
                    return False
        return True

    def _apply_update(self, doc: Dict[str, Any], update: Dict[str, Any]) -> None:
        if "$set" in update:
            for k, v in update["$set"].items():
                _set_path(doc, k, v)
        if "$inc" in update:
            for k, v in update["$inc"].items():
                cur = _get_path(doc, k) or 0
                _set_path(doc, k, cur + v)
        if "$push" in update:
            for k, v in update["$push"].items():
                lst = _get_path(doc, k)
                if lst is None:
                    lst = []
                    _set_path(doc, k, lst)
                lst.append(v)

    # ── Mongo API surface ─────────────────────────────────────
    async def insert_one(self, doc: Dict[str, Any]) -> Any:
        self.calls.append({"op": "insert_one", "doc": dict(doc)})
        _id = doc["_id"]
        if _id in self.docs:
            raise Exception("E11000 duplicate key")
        # deep copy via json-ish for lists/dicts
        self.docs[_id] = _deep_copy(doc)
        return type("Ins", (), {"inserted_id": _id})()

    async def find_one(self, filt: Dict[str, Any], projection: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        self.calls.append({"op": "find_one", "filter": dict(filt), "projection": projection})
        _id = filt.get("_id")
        if _id is None:
            return None
        doc = self.docs.get(_id)
        if doc is None:
            return None
        # For simplicity ignore additional filter conds on find_one
        # (adapter uses find_one only for probes on _id).
        return _deep_copy(doc)

    async def find_one_and_update(
        self,
        filt: Dict[str, Any],
        update: Dict[str, Any],
        return_document: bool = True,
    ) -> Optional[Dict[str, Any]]:
        self.calls.append({"op": "find_one_and_update", "filter": dict(filt), "update": _deep_copy(update)})
        _id = filt.get("_id")
        if _id is None:
            return None
        doc = self.docs.get(_id)
        if doc is None:
            return None
        if not self._match(doc, filt):
            return None
        self._apply_update(doc, update)
        return _deep_copy(doc)

    async def delete_one(self, filt: Dict[str, Any]) -> Any:
        self.calls.append({"op": "delete_one", "filter": dict(filt)})
        _id = filt.get("_id")
        if _id is None or _id not in self.docs:
            return type("Del", (), {"deleted_count": 0})()
        del self.docs[_id]
        return type("Del", (), {"deleted_count": 1})()


def _get_path(doc: Dict[str, Any], path: str) -> Any:
    parts = path.split(".")
    cur: Any = doc
    for p in parts:
        if isinstance(cur, dict):
            cur = cur.get(p)
        elif isinstance(cur, list):
            # e.g. "processed_event_keys.event_id" → return list of that field
            vals = [item.get(p) if isinstance(item, dict) else None for item in cur]
            return vals
        else:
            return None
    return cur


def _set_path(doc: Dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    cur: Any = doc
    for p in parts[:-1]:
        nxt = cur.get(p) if isinstance(cur, dict) else None
        if nxt is None or not isinstance(nxt, dict):
            nxt = {}
            cur[p] = nxt
        cur = nxt
    if isinstance(cur, dict):
        cur[parts[-1]] = value


def _deep_copy(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _deep_copy(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_deep_copy(x) for x in obj]
    return obj


@pytest.fixture
def mongo_mock_collection() -> _InMemoryMongoCollectionMock:
    return _InMemoryMongoCollectionMock()


# ═══════════════════════ PARAMETRIZED STORE FIXTURE ═══════════════════════
@pytest.fixture(params=["fake", "mongo_mock"])
def store(
    request: pytest.FixtureRequest,
    frozen_clock: _FrozenClock,
    mongo_mock_collection: _InMemoryMongoCollectionMock,
) -> ExpeditionRuntimeStateStore:
    variant = request.param
    if variant == "fake":
        return FakeExpeditionRuntimeStateStore(clock=frozen_clock)
    if variant == "mongo_mock":
        return MongoExpeditionRuntimeStateStore(mongo_mock_collection, clock=frozen_clock)
    raise ValueError(f"unknown store variant: {variant}")
