"""RT2-B-1B-1 · Local isolated Mongo provisioning module.

Contiene i tool CLI per il provisioning idempotente della collection
`expedition_runtime_states` in ambiente LOCAL-ISOLATED-ONLY.

**INVARIANT**:
- Host `localhost` **obbligatorio** (fail-stop `TARGET_ENVIRONMENT_REJECTED`)
- Database **in allowlist** (fail-stop `TARGET_DATABASE_REJECTED`)
- `orbus_r16` **esplicitamente vietato** (fail-stop `FORBIDDEN_DATABASE_ORBUS_R16`)
- Nessuna wiring del runtime applicativo (invocazione manuale o via test)
- Idempotente: `--apply` × N deve produrre lo stesso stato

Regime: `RT2-B-1B-1 · LOCAL ISOLATED ONLY · NO SHARED ENV APPLY`.
"""
from app.stats.runtime.state_store.provisioning.guards import (
    ALLOWED_STABLE_DATABASE,
    IT_DATABASE_REGEX,
    ProvisioningGuardError,
    verify_database_allowlist,
    verify_host_localhost,
    verify_not_orbus_r16,
    verify_target,
)
from app.stats.runtime.state_store.provisioning.provisioning_command import (
    COLLECTION_NAME,
    TTL_INDEX_NAME,
    ProvisioningCommand,
    build_arg_parser,
)
from app.stats.runtime.state_store.provisioning.unique_run_id import (
    generate_unique_run_id,
    it_database_name,
)


__all__ = [
    "ALLOWED_STABLE_DATABASE",
    "IT_DATABASE_REGEX",
    "ProvisioningGuardError",
    "verify_database_allowlist",
    "verify_host_localhost",
    "verify_not_orbus_r16",
    "verify_target",
    "COLLECTION_NAME",
    "TTL_INDEX_NAME",
    "ProvisioningCommand",
    "build_arg_parser",
    "generate_unique_run_id",
    "it_database_name",
]
