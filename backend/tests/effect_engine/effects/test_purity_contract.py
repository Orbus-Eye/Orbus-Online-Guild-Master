from __future__ import annotations

import ast
from pathlib import Path


FORBIDDEN_IMPORT_ROOTS = {
    "asyncio",
    "httpx",
    "logging",
    "motor",
    "os",
    "pymongo",
    "random",
    "requests",
    "socket",
    "time",
    "uuid",
}
P1_PURE_MODULES = (
    "__init__.py",
    "models.py",
    "registry.py",
    "resolver.py",
    "serialization.py",
)


def test_p1_production_modules_have_no_io_clock_rng_or_global_mutation_imports():
    effects_dir = (
        Path(__file__).resolve().parents[3] / "app" / "stats" / "runtime" / "effects"
    )
    violations = []
    for filename in P1_PURE_MODULES:
        path = effects_dir / filename
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".", 1)[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom):
                roots = {(node.module or "").split(".", 1)[0]}
            else:
                continue
            forbidden = roots & FORBIDDEN_IMPORT_ROOTS
            if forbidden:
                violations.append((path.name, node.lineno, sorted(forbidden)))
    assert violations == []
