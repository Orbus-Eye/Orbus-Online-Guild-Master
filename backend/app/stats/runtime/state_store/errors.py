"""RT2-B-1A · Exception hierarchy per state store operations.

Ogni eccezione ha un codice diagnostico stringato leggibile (`code` attribute)
che mappa uno-a-uno sui `CasResultCode` in `results.py`. Le eccezioni sono
sollevate SOLO da percorsi eccezionali: le operazioni normali ritornano
`CasResult(code=...)` senza sollevare eccezioni.

Convenzione: le eccezioni portano un `code` che è la stringa esatta del
`CasResultCode`. Le mutation NON producono mai partial state.
"""
from __future__ import annotations


class StoreError(Exception):
    """Base class per tutte le eccezioni della state-store library."""

    code: str = "STORE_ERROR"

    def __init__(self, message: str = "") -> None:
        super().__init__(message or self.code)


class StoreInfraError(StoreError):
    """Infrastruttura sottostante non disponibile / timeout / errore trasporto.

    Mappa Mongo `PyMongoError` (e superclassi) alla state-store layer.
    Il retry automatico NON è previsto qui — la decisione è del chiamante.
    """

    code = "STATE_INFRA_UNAVAILABLE"


class NotFoundError(StoreError):
    """Il documento stato richiesto non esiste."""

    code = "NOT_FOUND"


class StateVersionConflictError(StoreError):
    """CAS mismatch su `state_version`.

    Il chiamante può ritentare (max 3 volte, dopo fresh read).
    """

    code = "STATE_VERSION_CONFLICT"


class StaleWriterError(StoreError):
    """Fencing token mismatch: writer stale.

    NON ritentabile. Il writer stale deve rilasciare tutte le referenze
    e ottenere una nuova lease valida.
    """

    code = "STALE_WRITER_REJECTED"


class OwnershipInvalidError(StoreError):
    """Cross-adventurer o cross-expedition mutation attempt.

    NON ritentabile. Emesso quando l'ownership check (source_adventurer_id
    ∈ expedition scope, target scope, ecc.) fallisce.
    """

    code = "OWNERSHIP_INVALID"


class CapExceededError(StoreError):
    """Cap violation (Marks ≤ 5, source-target ≤ 1, Fragments ≤ 5, focus ≤ 2).

    NON ritentabile.
    """

    code = "CAP_EXCEEDED"


class LeaseExpiredError(StoreError):
    """La lease del writer è scaduta.

    Il writer deve ri-acquisire (nuovo fencing_token).
    """

    code = "LEASE_EXPIRED"


class EventIdPayloadMismatchError(StoreError):
    """Same `event_id`, `payload_hash` differente = integrity violation.

    NON ritentabile. Segnala tentativo di duplicazione con payload alterato.
    """

    code = "EVENT_ID_PAYLOAD_MISMATCH"
