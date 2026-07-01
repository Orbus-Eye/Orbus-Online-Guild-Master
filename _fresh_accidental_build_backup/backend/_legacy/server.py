"""Orbus Online: Guild Master — ASGI entry point.

Thin wrapper. All business logic lives in `app/*` modules.
This file exists for uvicorn/supervisor compatibility (`server:app`)
and to preserve backward-compat shims for tests that still do
`from server import …`.

Refactor history:
- Phase 5.5b/c/c.2/c.3/d/e/f: progressively extracted auth/guilds/items/
  dungeons/recruitment/adventurers/equipment/expeditions/admin domains.
- Phase 5.5g: lifespan + seeds + indexes + ASGI factory extracted.
- Phase 5.5h: equipment helper duplicates removed.
"""
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from app.core.app_factory import create_app  # noqa: E402

app = create_app()


# ─── Backward-compat shims for tests ───────────────────────────────────────────
# `tests/backend_phase3_test.py` still imports these directly via `from server
# import …`. Each shim is a 1-line re-export from the canonical location.
# Marked F401 because they are accessed by external test files, not by this
# module's code.
from app.admin.services import validate_item_monetization  # noqa: E402,F401
from app.expeditions.services import _resolve_levelup  # noqa: E402,F401


__all__ = ["app", "validate_item_monetization", "_resolve_levelup"]
