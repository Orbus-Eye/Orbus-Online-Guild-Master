"""ROUND 18.Reset.1b.hotfix.write_freeze_full — Internal Job Freeze.

Estende il write-freeze oltre l'HTTP `MaintenanceMiddleware` (R18.Reset.1b.ops)
per bloccare i job async **interni** (invocati da lifespan boot, sweep
GET-triggered, e resolver on-visit) durante la finestra di apply.

Vincoli PM (R18.Reset.1b.hotfix.write_freeze_full):
    - Env var `ORBUS_INTERNAL_JOB_FREEZE` (default `false`)
    - Fallback file flag `/tmp/orbus_internal_job_freeze.flag`
    - Runtime refresh (nessun restart necessario per il file flag)
    - Job coperti: SKIP silenzioso + WARN log + no retry/backoff/exception
    - Zero DB write dai job coperti quando freeze attivo
    - Nessun cambio di logica ai job — solo guard all'ingresso

Coverage decisa in `/app/memory/r18_reset1b_hotfix_write_freeze_full_job_inventory.md`
(12 job hard-include: L1, L5, L7, L9=AMB-1, L10=AMB-2, R1, R2, R3, D1, D2,
D3, D4).

Il decorator `frozen_when_active(job_name, freeze_return_value=None)` e'
l'API pubblica principale. Per casi in cui il return neutro non e' `None`
(job che ritornano dict con chiavi attese dai caller), il chiamante puo'
passare `freeze_return_value={...}`.

Live evidence (R18.Reset.1b.hotfix Fase A hot-reload 2026-07-05T10:21:55Z):
    "orbus.onboarding - INFO - starter roster seeded: guild=907b4ae4 inserted=2"
Il boot lifespan HA scritto 2 adventurers su una guild live durante il
restart backend. Il freeze attivato PRIMA di un apply reale eviterebbe
esattamente questa fuga di scritture.
"""
from __future__ import annotations

import inspect
import logging
import os
from functools import wraps
from pathlib import Path
from typing import Any, Callable

FREEZE_ENV_VAR = "ORBUS_INTERNAL_JOB_FREEZE"
FREEZE_FLAG_FILE = "/tmp/orbus_internal_job_freeze.flag"
_TRUE_TOKENS = frozenset({"true", "1", "yes"})

_LOG = logging.getLogger("orbus.job_freeze")


def is_freeze_active() -> bool:
    """Rilegge env var + file flag ad OGNI invocation.

    Env var: `ORBUS_INTERNAL_JOB_FREEZE`. Case-insensitive.
        Accettati come "true": "true", "1", "yes".
        Tutto il resto (compresi "false", "0", "no", "", None) = false.

    File flag: se `/tmp/orbus_internal_job_freeze.flag` esiste
    (indipendentemente dal contenuto), il freeze e' attivo. Utile per
    toggle runtime senza restart supervisor.

    Il refresh e' per-call (nessun caching) come richiesto dal PM per
    consentire ON/OFF durante l'apply senza restart.
    """
    env_val = os.getenv(FREEZE_ENV_VAR, "false").strip().lower()
    if env_val in _TRUE_TOKENS:
        return True
    if Path(FREEZE_FLAG_FILE).exists():
        return True
    return False


def frozen_when_active(
    job_name: str,
    *,
    freeze_return_value: Any = None,
) -> Callable:
    """Decorator per job async/sync che devono essere skippati quando
    `ORBUS_INTERNAL_JOB_FREEZE` e' attivo.

    Args:
        job_name: identificatore leggibile del job (per il WARN log).
        freeze_return_value: valore da restituire in caso di skip. Per
            job che ritornano `dict`, passa `{}` o dict con chiavi neutre
            compatibili col caller. Default `None`.

    Comportamento in freeze:
        - Emette WARN: `"Internal job skipped due to ORBUS_INTERNAL_JOB_FREEZE"`
        - Ritorna `freeze_return_value` (default None)
        - Zero DB write, zero exception, zero retry
        - Idempotente per definizione: chiamate ripetute in freeze non
          producono side effect.

    Comportamento con freeze OFF:
        - Passa attraverso alla funzione decorata come no-op wrapper.
    """
    def deco(fn: Callable) -> Callable:
        if inspect.iscoroutinefunction(fn):
            @wraps(fn)
            async def _async_wrapped(*args, **kwargs):
                if is_freeze_active():
                    _LOG.warning(
                        "Internal job skipped due to %s — job=%s",
                        FREEZE_ENV_VAR, job_name,
                    )
                    return freeze_return_value
                return await fn(*args, **kwargs)
            return _async_wrapped

        @wraps(fn)
        def _sync_wrapped(*args, **kwargs):
            if is_freeze_active():
                _LOG.warning(
                    "Internal job skipped due to %s — job=%s",
                    FREEZE_ENV_VAR, job_name,
                )
                return freeze_return_value
            return fn(*args, **kwargs)
        return _sync_wrapped

    return deco


__all__ = [
    "FREEZE_ENV_VAR",
    "FREEZE_FLAG_FILE",
    "is_freeze_active",
    "frozen_when_active",
]
