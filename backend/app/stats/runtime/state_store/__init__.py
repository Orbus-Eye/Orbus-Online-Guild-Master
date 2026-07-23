"""RT2-B-1A · State Store Contract & Non-Wired Adapter Foundation (stand-alone library).

Namespace per la state-store library del gate `R18.6.RV3-IS2-B-P2B-RT2-B-1A`.

Regole invarianti (PM-ratified · dispatch RT2-B-1A):
- Library **STAND-ALONE · NON CABLATA AL RUNTIME APPLICATIVO**.
- Nessun percorso di questo namespace è raggiunto dal flusso spedizione reale.
  Il codice è raggiungibile SOLO dai test (fake_store, mongo_adapter con collezione mockata).
- `cdv_transient_state_enabled = false` invariante in ambiente attuale. Nessuna wiring, nessun startup provisioning.
- Nessun DB write reale · nessun network call · nessuna migrazione · nessun index.
- La collezione fisica `expedition_runtime_states` NON viene creata in questo gate
  (provisioning deferito a `RT2-B-1B`).
- Il Mongo adapter accetta la collection **iniettata al costruttore**; NON importa
  il db globale dell'applicazione.
- Non implementa gameplay Marchio/Drenaggio/Frammenti · solo schema + cap validation
  applicata via CAS.

Public exports minimi. Consumatori (test) importano dal namespace pubblico:

    from app.stats.runtime.state_store import (
        ExpeditionRuntimeStateStore,
        FakeExpeditionRuntimeStateStore,
        MongoExpeditionRuntimeStateStore,
        ExpeditionRuntimeState,
        AdventurerClassState,
        WriterLease,
        EventReceipt,
        CasResultCode,
        CasResult,
        StoreError,
    )
"""
from __future__ import annotations

from app.stats.runtime.state_store.errors import (
    CapExceededError,
    EventIdPayloadMismatchError,
    LeaseExpiredError,
    NotFoundError,
    OwnershipInvalidError,
    StaleWriterError,
    StateVersionConflictError,
    StoreError,
    StoreInfraError,
)
from app.stats.runtime.state_store.interface import ExpeditionRuntimeStateStore
from app.stats.runtime.state_store.models import (
    AdventurerClassState,
    DrainDoc,
    EventReceipt,
    ExpeditionRuntimeState,
    FragmentUsage,
    MarkDoc,
    WriterLease,
)
from app.stats.runtime.state_store.results import (
    CasResult,
    CasResultCode,
    LeaseAcquireResult,
    ReadResult,
)

# Fake and Mongo store implementations exported by name.
from app.stats.runtime.state_store.fake_store import FakeExpeditionRuntimeStateStore
from app.stats.runtime.state_store.mongo_adapter import MongoExpeditionRuntimeStateStore

__all__ = [
    "ExpeditionRuntimeStateStore",
    "FakeExpeditionRuntimeStateStore",
    "MongoExpeditionRuntimeStateStore",
    "ExpeditionRuntimeState",
    "AdventurerClassState",
    "MarkDoc",
    "DrainDoc",
    "FragmentUsage",
    "WriterLease",
    "EventReceipt",
    "CasResultCode",
    "CasResult",
    "LeaseAcquireResult",
    "ReadResult",
    "StoreError",
    "StoreInfraError",
    "StateVersionConflictError",
    "StaleWriterError",
    "NotFoundError",
    "OwnershipInvalidError",
    "CapExceededError",
    "LeaseExpiredError",
    "EventIdPayloadMismatchError",
]
