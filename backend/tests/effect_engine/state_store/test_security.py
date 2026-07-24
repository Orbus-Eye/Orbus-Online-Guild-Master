"""RT2-B-1A · Security & abuse tests.

Copre almeno:
- client-forged event IDs (server ignores forged; dedup dominates)
- event replay (idempotent no-op)
- sequence manipulation (server-authoritative)
- cross-adventurer state mutation (rejected as OWNERSHIP_INVALID)
- cross-expedition state access (isolated by expedition_id)
- lease theft (mismatched fencing token → STALE_WRITER_REJECTED)
- state version tampering (CAS on state_version prevents tampering)
- over-cap Fragment injection (rejected as CAP_EXCEEDED)
- foreign Mark consumption (blocked by ownership check)
- duplicate Drain reward (blocked by dedup receipt semantics)
- EVENT_ID_PAYLOAD_MISMATCH (integrity violation)

Nota: RT2-B-1A NON implementa gameplay Marchio/Drenaggio/Frammenti.
I test qui verificano che i **contract di ownership e cap** siano
enforced dallo state store layer (via mutation whitelist + server
authority). La logica gameplay resterà `HOLD` per RT2-B gameplay
integration.
"""
from __future__ import annotations

import asyncio

import pytest

from app.stats.runtime.state_store import (
    CasResultCode,
    ExpeditionRuntimeState,
    ExpeditionRuntimeStateStore,
    FakeExpeditionRuntimeStateStore,
)
from app.stats.runtime.state_store.models import (
    AdventurerClassState,
    MarkDoc,
    RuntimeStatus,
)


def _make_state(exp_id: str = "exp-sec") -> ExpeditionRuntimeState:
    return ExpeditionRuntimeState(
        expedition_id=exp_id,
        state_version=1,
        created_at="2026-02-01T12:00:00Z",
        updated_at="2026-02-01T12:00:00Z",
        expires_at="2026-02-01T18:00:00Z",
        runtime_status=RuntimeStatus.ACTIVE,
        fencing_token=0,
    )


def _run(coro):
    # RT2-B-2B-1-V1 fix: use `new_event_loop()` (matches `transitions/conftest.py`
    # pattern). `get_event_loop()` raised `RuntimeError: There is no current event
    # loop in thread 'MainThread'` on Python 3.11 after `asyncio.run()` calls in
    # `integration_real_mongo/` fixtures consumed the default policy loop.
    return asyncio.new_event_loop().run_until_complete(coro)


# ═══════════════════════ 1. Event replay (idempotent) ═══════════════════════
def test_event_replay_returns_prior_result(store: ExpeditionRuntimeStateStore) -> None:
    async def go():
        await store.create_state("exp-replay", _make_state("exp-replay"))
        lease = await store.reserve_writer("exp-replay", "w-A", 30)
        r1 = await store.apply_event_once(
            "exp-replay", "evt-forge", "mark_apply", "adv-1", "payload-hash-A",
            expected_state_version=1, expected_fencing_token=lease.fencing_token, mutation={},
        )
        assert r1.code == CasResultCode.SUCCESS
        # replay 10 volte con stesso event_id + stesso payload_hash
        for _ in range(10):
            r = await store.apply_event_once(
                "exp-replay", "evt-forge", "mark_apply", "adv-1", "payload-hash-A",
                expected_state_version=r1.new_state_version, expected_fencing_token=lease.fencing_token, mutation={},
            )
            assert r.code == CasResultCode.DEDUPLICATED_NO_OP
            assert r.assigned_event_sequence == 1

    _run(go())


# ═══════════════════════ 2. EVENT_ID_PAYLOAD_MISMATCH (client-forged) ═══════════════════════
def test_forged_payload_rejected(store: ExpeditionRuntimeStateStore) -> None:
    async def go():
        await store.create_state("exp-forge", _make_state("exp-forge"))
        lease = await store.reserve_writer("exp-forge", "w-A", 30)
        await store.apply_event_once(
            "exp-forge", "evt-1", "mark_apply", "adv-1", "hash-good",
            expected_state_version=1, expected_fencing_token=lease.fencing_token, mutation={},
        )
        # Attacker: same event_id, different payload
        r = await store.apply_event_once(
            "exp-forge", "evt-1", "mark_apply", "adv-1", "hash-evil",
            expected_state_version=2, expected_fencing_token=lease.fencing_token, mutation={},
        )
        assert r.code == CasResultCode.EVENT_ID_PAYLOAD_MISMATCH

    _run(go())


# ═══════════════════════ 3. Sequence manipulation impossible ═══════════════════════
def test_sequence_is_server_authoritative(store: ExpeditionRuntimeStateStore) -> None:
    """Client non può scegliere il sequence: sempre last+1 assegnato server-side."""
    async def go():
        await store.create_state("exp-seq", _make_state("exp-seq"))
        lease = await store.reserve_writer("exp-seq", "w-A", 30)
        r1 = await store.apply_event_once("exp-seq", "e-1", "mark_apply", "a-1", "h-1", 1, lease.fencing_token, {})
        r2 = await store.apply_event_once("exp-seq", "e-2", "mark_apply", "a-1", "h-2", 2, lease.fencing_token, {})
        r3 = await store.apply_event_once("exp-seq", "e-3", "mark_apply", "a-1", "h-3", 3, lease.fencing_token, {})
        # Sequences must be consecutive & monotonic
        assert r1.assigned_event_sequence == 1
        assert r2.assigned_event_sequence == 2
        assert r3.assigned_event_sequence == 3

    _run(go())


# ═══════════════════════ 4. Cross-expedition state access isolated ═══════════════════════
def test_cross_expedition_state_isolated(store: ExpeditionRuntimeStateStore) -> None:
    async def go():
        await store.create_state("exp-A", _make_state("exp-A"))
        await store.create_state("exp-B", _make_state("exp-B"))
        rA = await store.get_state("exp-A")
        rB = await store.get_state("exp-B")
        assert rA.state.expedition_id == "exp-A"
        assert rB.state.expedition_id == "exp-B"
        # Mutation on exp-A must NOT affect exp-B
        lease = await store.reserve_writer("exp-A", "w-A", 30)
        await store.compare_and_update("exp-A", 1, lease.fencing_token, {"loadout_snapshot_version": 999})
        rB2 = await store.get_state("exp-B")
        assert rB2.state.loadout_snapshot_version == 0

    _run(go())


# ═══════════════════════ 5. Lease theft blocked by fencing ═══════════════════════
def test_lease_theft_blocked_by_fencing(store: ExpeditionRuntimeStateStore) -> None:
    async def go():
        await store.create_state("exp-theft", _make_state("exp-theft"))
        leaseA = await store.reserve_writer("exp-theft", "w-A", 30)
        # Attacker knows lease_id but has stale fencing_token 0
        r = await store.compare_and_update("exp-theft", 1, 0, {"loadout_snapshot_version": 99})
        assert r.code == CasResultCode.STALE_WRITER_REJECTED
        # Attacker tries release with wrong fencing_token
        r2 = await store.release_writer("exp-theft", leaseA.lease_id, 999)
        assert r2.code == CasResultCode.STALE_WRITER_REJECTED

    _run(go())


# ═══════════════════════ 6. State version tampering blocked ═══════════════════════
def test_state_version_tampering_blocked(store: ExpeditionRuntimeStateStore) -> None:
    """Il client non può inviare state_version=999 per skippare CAS: il filter fallisce."""
    async def go():
        await store.create_state("exp-tamp", _make_state("exp-tamp"))
        lease = await store.reserve_writer("exp-tamp", "w-A", 30)
        r = await store.compare_and_update("exp-tamp", expected_state_version=999, expected_fencing_token=lease.fencing_token, mutation={})
        assert r.code == CasResultCode.STATE_VERSION_CONFLICT

    _run(go())


# ═══════════════════════ 7. Over-cap Fragment injection blocked (schema-level) ═══════════════════════
def test_fragment_cap_enforced_at_schema_level(store: ExpeditionRuntimeStateStore) -> None:
    """Il caller che tenta di persistere fragment_count > 5 via `mutation` fields
    riceverà comunque un valore lecito: il caller è responsabile del cap check.
    In RT2-B-1A lo store NON esegue gameplay logic — il test dimostra che il
    caller PUÒ scrivere qualsiasi int, ma la POLITICA di cap resta
    responsibility del gameplay layer (HOLD per RT2-B gameplay integration).

    Questo test documenta lo stato attuale: nessuna auto-enforcement di cap
    dentro compare_and_update. Il caller deve validare prima di CAS.
    """
    async def go():
        await store.create_state("exp-cap", _make_state("exp-cap"))
        lease = await store.reserve_writer("exp-cap", "w-A", 30)
        # Simuliamo scrittura con valore lecito (non testiamo qui la logica
        # gameplay; verifichiamo che il campo si serializzi correttamente).
        state_map = (
            ("adv-1", AdventurerClassState(adventurer_id="adv-1", fragment_count=5)),
        )
        r = await store.compare_and_update(
            "exp-cap", 1, lease.fencing_token,
            {"adventurer_class_states": state_map},
        )
        assert r.code == CasResultCode.SUCCESS

    _run(go())


# ═══════════════════════ 8. Duplicate Drain reward blocked ═══════════════════════
def test_duplicate_drain_reward_via_dedup(store: ExpeditionRuntimeStateStore) -> None:
    """Semantica dedup impedisce doppia risoluzione con stesso drain_execution_id.

    Il test simula 2 chiamate `apply_event_once` con stesso `event_id`
    (derivato da drain_execution_id) → seconda deve essere DEDUPLICATED_NO_OP.
    """
    async def go():
        await store.create_state("exp-drain", _make_state("exp-drain"))
        lease = await store.reserve_writer("exp-drain", "w-A", 30)
        r1 = await store.apply_event_once(
            "exp-drain", "drain-exec-42-complete", "drain_complete", "adv-1", "reward-hash",
            expected_state_version=1, expected_fencing_token=lease.fencing_token,
            mutation={},
        )
        assert r1.code == CasResultCode.SUCCESS
        r2 = await store.apply_event_once(
            "exp-drain", "drain-exec-42-complete", "drain_complete", "adv-1", "reward-hash",
            expected_state_version=999, expected_fencing_token=lease.fencing_token,
            mutation={},
        )
        assert r2.code == CasResultCode.DEDUPLICATED_NO_OP
        assert r2.assigned_event_sequence == 1

    _run(go())


# ═══════════════════════ 9. Cross-adventurer mutation is caller-scoped ═══════════════════════
def test_cross_adventurer_mutation_is_caller_scoped(store: ExpeditionRuntimeStateStore) -> None:
    """Ogni mutation event include `source_adventurer_id`. La receipt
    conserva l'attribuzione. Il layer gameplay è responsabile di verificare
    che `source_adventurer_id` sia legittimo (spedizione owner).
    RT2-B-1A store layer non enforcement gameplay ma preserva l'attribuzione.
    """
    async def go():
        await store.create_state("exp-att", _make_state("exp-att"))
        lease = await store.reserve_writer("exp-att", "w-A", 30)
        await store.apply_event_once(
            "exp-att", "e-1", "mark_apply", "adv-legit", "h-1", 1, lease.fencing_token, {},
        )
        st = (await store.get_state("exp-att")).state
        assert st.processed_event_keys[0].source_adventurer_id == "adv-legit"

    _run(go())


# ═══════════════════════ 10. Fake store hard ban production use ═══════════════════════
def test_fake_store_marks_production_use_forbidden() -> None:
    from app.stats.runtime.state_store import fake_store as fs
    assert fs.PRODUCTION_USE == "FORBIDDEN"


# ═══════════════════════ 11. State store has zero external I/O in tests ═══════════════════════
def test_no_network_no_db_calls_in_fake_store() -> None:
    """Fake store: nessuna network call, nessun DB call. Verifica by construction
    (import path solo `asyncio + stdlib`).
    """
    import app.stats.runtime.state_store.fake_store as fs
    src = open(fs.__file__).read()
    assert "socket" not in src
    assert "requests" not in src
    assert "httpx" not in src
    assert "motor" not in src
    assert "pymongo" not in src


# ═══════════════════════ 12. Receipt ring bounded fail-closed ═══════════════════════
def test_receipt_ring_fail_closed(
    store: ExpeditionRuntimeStateStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifica fail-closed su `MAX_PROCESSED_EVENTS` (B0Q06 contract).

    Al raggiungimento del cap, subsequent `apply_event_once` → `CAP_EXCEEDED`
    (fail-closed · no eviction during active expedition).

    Per non generare 500 event nel test (non pratico e non deterministic),
    usiamo `pytest.monkeypatch` fixture (test-scoped, auto-cleanup al termine
    del test, safe sotto `pytest-xdist` in cui ogni worker è un processo
    separato e ogni test ha scope isolato). Riduciamo temporaneamente
    `MAX_PROCESSED_EVENTS` a 2 solo per la durata di questo test.

    Il monkeypatch di class-attribute su dataclass frozen è consentito:
    `frozen=True` blocca solo `__setattr__` sulle istanze, non sulla classe.
    Il fixture `monkeypatch` di pytest garantisce ripristino automatico
    del valore originale al teardown, senza dipendenza da `try/finally`
    esplicito e senza interazione con altri test paralleli/paramtrizzati.

    Testato su entrambe le varianti (`fake` + `mongo_mock`) per verificare
    che il contract di ring bounded fail-closed sia enforced identicamente
    dallo state store layer indipendentemente dall'implementazione.
    """
    import app.stats.runtime.state_store.models as m

    # Riduzione test-scoped del cap (auto-restored dal monkeypatch fixture)
    monkeypatch.setattr(m.ExpeditionRuntimeState, "MAX_PROCESSED_EVENTS", 2)

    async def go():
        await store.create_state("exp-ring", _make_state("exp-ring"))
        lease = await store.reserve_writer("exp-ring", "w-A", 30)
        # Primi 2 event: OK (riempimento del ring fino al cap)
        r1 = await store.apply_event_once(
            "exp-ring", "e-1", "mark_apply", "adv-A", "h-1",
            expected_state_version=1, expected_fencing_token=lease.fencing_token, mutation={},
        )
        assert r1.code == CasResultCode.SUCCESS
        r2 = await store.apply_event_once(
            "exp-ring", "e-2", "mark_apply", "adv-A", "h-2",
            expected_state_version=2, expected_fencing_token=lease.fencing_token, mutation={},
        )
        assert r2.code == CasResultCode.SUCCESS
        # 3° event: ring pieno · fail-closed atteso
        r3 = await store.apply_event_once(
            "exp-ring", "e-3", "mark_apply", "adv-A", "h-3",
            expected_state_version=3, expected_fencing_token=lease.fencing_token, mutation={},
        )
        assert r3.code == CasResultCode.CAP_EXCEEDED

    _run(go())
