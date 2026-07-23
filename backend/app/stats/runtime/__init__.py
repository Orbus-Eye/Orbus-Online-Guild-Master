"""RT2-A · Stat Evaluation Foundation (Runtime Stat Library).

Namespace per la foundation library del gate `R18.6.RV3-IS2-B-P2B-RT2-A`.

Regole invariabili (PM-ratified · Message 114):
- Foundation completamente STATELESS · deterministic · multi-worker-safe by design.
- NESSUN percorso qui è raggiunto dal flusso spedizione reale finché entrambi i
  flag RT2-A restano OFF (default): `runtime_stat_soft_cap_enabled=false` e
  `runtime_stat_shadow_enabled=false`.
- NESSUNA persistenza cross-request. NESSUN DB write. NESSUNA modifica OpenAPI.
- Esclusi in RT2-A: Mark, Drain, Fragments, proc RNG, cooldown, duration,
  effect instances, stacking, boss safeguards, item hooks, Legendary effects.
"""
from __future__ import annotations

__all__: list[str] = []
