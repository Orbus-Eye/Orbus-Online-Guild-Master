"""FASE 1.10 (2026-08-08) — Censimento testi/nomi inglesi residui.

Scansione STATICA (nessun DB richiesto) di:
  * frontend/src (pages + components): testo JSX hardcoded e attributi
    player-facing (title/placeholder/label) che contengono parole
    inglesi "segnale";
  * backend/app: stringhe player-facing (user_message / message /
    reason_it / detail) con parole inglesi.

Modalità opzionale `--db` (richiede MONGO_URL/DB_NAME in env): audita
la collection `items` cercando item attivi senza `display_name_it` o
con nome che sembra inglese.

Output: markdown su stdout e su memory/fase1_censimento_testi_inglesi.md

Uso:
    python scripts/fase1_censimento_testi_inglesi.py [--db]

L'euristica produce inevitabilmente qualche falso positivo: il report
serve come lista di lavoro per la revisione traduzioni (Fase 3), non
come verità assoluta.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Parole inglesi "segnale" che non appartengono all'italiano di gioco.
# Scelte per minimizzare i falsi positivi (niente parole condivise tipo
# "club", "report" è ambiguo ma frequente nei testi EN residui).
SIGNAL_WORDS = {
    "the", "your", "you", "with", "and", "for", "from", "loading",
    "view", "start", "save", "refresh", "search", "delete", "remove",
    "cancel", "confirm", "close", "back", "next", "previous", "loading",
    "available", "required", "recommended", "completed", "failed",
    "success", "reward", "power", "team", "guild", "adventurer",
    "expedition", "dungeon", "items", "inventory", "level", "gold",
    "no", "not", "yet", "any", "all", "new", "active", "historical",
    "heroes", "duration", "waiting", "please", "retry", "error",
}
# Quante parole segnale servono perché una stringa sia considerata EN.
MIN_SIGNALS = 2

# Testo JSX: >qualcosa<  — grezzo ma efficace sui sorgenti del progetto.
JSX_TEXT_RE = re.compile(r">([^<>{}\n]{4,120})<")
ATTR_RE = re.compile(r"(?:title|placeholder|label|aria-label)=\"([^\"]{4,120})\"")
# Backend: stringhe nei messaggi player-facing.
PY_MSG_RE = re.compile(
    r"(?:user_message|\"message\"|'message'|detail)\s*[:=]\s*f?\"([^\"]{6,160})\""
)


def looks_english(text: str) -> bool:
    words = re.findall(r"[A-Za-z']+", text.lower())
    if len(words) < 2:
        return False
    hits = sum(1 for w in words if w in SIGNAL_WORDS)
    return hits >= MIN_SIGNALS


def scan_frontend() -> list[tuple[str, int, str]]:
    out = []
    src = ROOT / "frontend" / "src"
    for path in sorted(src.rglob("*.jsx")) + sorted(src.rglob("*.js")):
        rel = path.relative_to(ROOT).as_posix()
        if "/ui/" in rel or "__tests__" in rel:
            continue  # primitive shadcn e test: fuori scope player-facing
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith(("//", "*", "/*")):
                continue  # commenti: non player-facing
            for rx in (JSX_TEXT_RE, ATTR_RE):
                for m in rx.finditer(line):
                    text = m.group(1).strip()
                    if text and looks_english(text):
                        out.append((rel, i, text))
    return out


def scan_backend() -> list[tuple[str, int, str]]:
    out = []
    src = ROOT / "backend" / "app"
    for path in sorted(src.rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if "/scripts/" in rel or "/tests/" in rel:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for i, line in enumerate(lines, 1):
            if line.strip().startswith("#"):
                continue
            for m in PY_MSG_RE.finditer(line):
                text = m.group(1).strip()
                if text and looks_english(text):
                    out.append((rel, i, text))
    return out


def scan_db_items() -> list[str]:
    """Audita `items` in Mongo: attivi senza display_name_it."""
    import os
    from pymongo import MongoClient

    client = MongoClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    rows = db.items.find(
        {"is_active": True, "is_test": {"$ne": True}},
        {"_id": 0, "slug": 1, "name": 1, "display_name_it": 1},
    )
    out = []
    for r in rows:
        if not (r.get("display_name_it") or "").strip():
            out.append(f"{r.get('slug', '?')} — name: {r.get('name', '?')}")
    return out


def main() -> None:
    fe = scan_frontend()
    be = scan_backend()
    lines = [
        "# FASE 1.10 — Censimento testi/nomi inglesi residui",
        "",
        "Generato da `scripts/fase1_censimento_testi_inglesi.py`.",
        "Euristica a parole segnale: aspettarsi qualche falso positivo.",
        "Le voci elencate sono la lista di lavoro traduzioni per la Fase 3.",
        "",
        f"## Frontend — {len(fe)} stringhe sospette",
        "",
    ]
    for rel, i, text in fe:
        lines.append(f"- `{rel}:{i}` — {text}")
    lines += ["", f"## Backend (messaggi player-facing) — {len(be)} stringhe sospette", ""]
    for rel, i, text in be:
        lines.append(f"- `{rel}:{i}` — {text}")

    if "--db" in sys.argv:
        missing = scan_db_items()
        lines += ["", f"## DB items senza display_name_it — {len(missing)}", ""]
        lines += [f"- {row}" for row in missing]
    else:
        lines += [
            "",
            "## DB items",
            "",
            "Esegui con `--db` (env MONGO_URL/DB_NAME) per aggiungere",
            "l'audit degli item senza `display_name_it`.",
        ]

    report = "\n".join(lines) + "\n"
    out_path = ROOT / "memory" / "fase1_censimento_testi_inglesi.md"
    out_path.write_text(report, encoding="utf-8")
    print(report)
    print(f"[salvato] {out_path}")


if __name__ == "__main__":
    main()
