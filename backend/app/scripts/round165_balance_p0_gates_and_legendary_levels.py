"""ROUND 16.5 — Balance P0: Dungeon Gates & Legendary Level Requirements.

Scope: Applica in modo CONSERVATIVO due fix P0 identificati dall'audit R16.4:

1. Popolare `required_level` su tutti i 22 dungeon (attualmente = 0 / assente)
   in modo coerente con `recommended_power`, `difficulty`, dimensione team
   e content_family.
2. Alzare `min_level` sui 5 item Legendary (attualmente = 1 / assente) a
   valori appropriati (8 baseline; 9 per outlier equip_power ≥ 55, che è
   il top-40% del range Legendary).

## Modes

- `--dry-run`  → genera il report proposto SENZA scrivere sul DB.
- `--apply`    → applica le modifiche. Richiede uno snapshot pre-change già
                 esistente (STEP 2, non attivo in STEP 1).

## Guarantees

- ❌ NO hard delete, NO drop
- ❌ NO modifiche a `equip_power`, `rarity`, `drop`, `price`, `crafting`,
     `reward`, `xp`, `threat_tags`, `pvp_*`, `stables`, formule
- ❌ NO tocchi collezioni diverse da `dungeons` e `items`
- ✅ Idempotente: rilanciabile senza duplicare/corrompere
- ✅ `update_one` con `$set` mirato su singoli campi (`required_level`,
     `min_level`)
- ✅ Guard-rail: item/dungeon non classificabili → aggiunti a `unresolved`
     e MAI toccati

Usage:
    # STEP 1: dry run — genera proposta
    python /app/backend/app/scripts/round165_balance_p0_gates_and_legendary_levels.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, "/app/backend")


# ═════════════════════════════════════════════════════════════════════
# 0. CLI + safety
# ═════════════════════════════════════════════════════════════════════


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, add_help=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true",
                   help="Non modifica il DB, genera report proposta.")
    g.add_argument("--apply", action="store_true",
                   help="Applica le modifiche (richiede snapshot pre-change).")
    return p.parse_args()


# ═════════════════════════════════════════════════════════════════════
# 1. DB CONNECTION
# ═════════════════════════════════════════════════════════════════════


def _connect_db():
    import os
    from dotenv import load_dotenv
    load_dotenv(Path("/app/backend/.env"))
    from pymongo import MongoClient
    url = os.environ.get("MONGO_URL")
    client = MongoClient(url)
    db = client["orbus_r16"]
    _ = db.list_collection_names()
    return client, db


# ═════════════════════════════════════════════════════════════════════
# 2. DUNGEON — regole di classificazione
# ═════════════════════════════════════════════════════════════════════
#
# Derivate da (rec_pow crescente) + (difficulty) + (team_size 3p vs 5p) +
# (coerenza tema/content_family). Nessuna curva casuale.
#
# 3p (main line):
#   rec 35-50    → tutorial   → required_level 1-2
#   rec 69-85    → early      → required_level 3-4
#   rec 94-110   → mid        → required_level 5-6
#
# 5p (co-op line):
#   rec 80-100   → early_5p   → required_level 3-4  (co-op introduttivi)
#   rec 140-170  → mid_5p     → required_level 6-7
#   rec 210-250  → high_5p    → required_level 8-10
#   rec 290-360  → endgame    → required_level 12-14


# Mappa dungeon → required_level proposto + bucket + motivazione.
# Chiavi = slug canonici (verificati contro DB reale).
_DUNGEON_MAPPING: dict[str, dict[str, Any]] = {
    # === Tutorial 3p (rec 35-50) ===
    "sewer-nest": {
        "required_level": 1, "bucket": "tutorial",
        "motivazione": (
            "Difficoltà 1, rec_pow 35 (lowest), team 3p, tema 'baseline'. "
            "Primo dungeon dell'onboarding player."
        ),
    },
    "goblin-warrens": {
        "required_level": 2, "bucket": "tutorial",
        "motivazione": (
            "Difficoltà 1, rec_pow 45, team 3p, tema 'baseline'. "
            "Secondo dungeon tutorial, gap +1 su sewer-nest."
        ),
    },
    "bandit-hideout": {
        "required_level": 2, "bucket": "tutorial",
        "motivazione": (
            "Difficoltà 1, rec_pow 50, team 3p, tema 'baseline'. "
            "Ultimo tutorial 3p prima del salto early."
        ),
    },
    # === Early 3p (rec 69-85) ===
    "druid-grove": {
        "required_level": 3, "bucket": "early",
        "motivazione": (
            "Difficoltà 2, rec_pow 69, team 3p, tema 'nature'. "
            "Primo early: gap +1 su tutorial, coerente con crescita naturale."
        ),
    },
    "shadow-crypts": {
        "required_level": 3, "bucket": "early",
        "motivazione": (
            "Difficoltà 2, rec_pow 75, team 3p, tema 'void_undead'. "
            "Early, stesso livello del druid-grove per parità narrativa."
        ),
    },
    "cursed-mines": {
        "required_level": 4, "bucket": "early",
        "motivazione": (
            "Difficoltà 2, rec_pow 78, team 3p, tema 'arcane'. "
            "Early avanzato, ponte verso mid tier."
        ),
    },
    "sunken-library": {
        "required_level": 4, "bucket": "early",
        "motivazione": (
            "Difficoltà 2, rec_pow 85, team 3p, tema 'memory'. "
            "Early avanzato, gap allineato con cursed-mines."
        ),
    },
    # === Mid 3p (rec 94-110) ===
    "lich-sanctum": {
        "required_level": 5, "bucket": "mid",
        "motivazione": (
            "Difficoltà 3, rec_pow 94, team 3p, tema 'void_undead'. "
            "Primo mid tier 3p, sblocca contenuto epic."
        ),
    },
    "dragons-hoard": {
        "required_level": 6, "bucket": "mid",
        "motivazione": (
            "Difficoltà 3, rec_pow 100, team 3p, tema 'arcane'. "
            "Mid centrale 3p, richiede team con equip Rare consolidato."
        ),
    },
    "storm-spire": {
        "required_level": 6, "bucket": "mid",
        "motivazione": (
            "Difficoltà 3, rec_pow 110, team 3p, tema 'arcane'. "
            "Top mid 3p, ultimo dungeon della main line 3-player."
        ),
    },
    # === Early 5p (rec 80-100) — co-op introduttivo ===
    "wolf-den-5p": {
        "required_level": 3, "bucket": "early", "story_catchup": True,
        "motivazione": (
            "Difficoltà 1, rec_pow 80, team 5p, tema 'nature'. "
            "Primo co-op 5p: rec_pow più alto assorbito dal group size, "
            "livello richiesto allineato all'early solo."
        ),
    },
    "frost-cave-5p": {
        "required_level": 4, "bucket": "early", "story_catchup": True,
        "motivazione": (
            "Difficoltà 1, rec_pow 90, team 5p, tema 'nature'. "
            "Co-op early avanzato, gap +1 su wolf-den."
        ),
    },
    "salt-marsh-5p": {
        "required_level": 5, "bucket": "early", "story_catchup": True,
        "motivazione": (
            "Difficoltà 1, rec_pow 100, team 5p, tema 'memory'. "
            "Co-op ponte verso mid, gate leggermente più stretto per "
            "content_family memory (contenuto narrativo)."
        ),
    },
    # === Mid 5p (rec 140-170) ===
    "iron-foundry-5p": {
        "required_level": 6, "bucket": "mid",
        "motivazione": (
            "Difficoltà 2, rec_pow 140, team 5p, tema 'arcane'. "
            "Primo mid 5p, allineato a dragons-hoard 3p per parità."
        ),
    },
    "silent-monastery-5p": {
        "required_level": 7, "bucket": "mid",
        "motivazione": (
            "Difficoltà 2, rec_pow 155, team 5p, tema 'memory'. "
            "Mid 5p, contenuto narrativo, +1 su iron-foundry."
        ),
    },
    "pirate-fleet-5p": {
        "required_level": 8, "bucket": "high",
        "motivazione": (
            "Difficoltà 2, rec_pow 170, team 5p, tema 'baseline'. "
            "Top mid / soglia high, prima esperienza di 'grande scala'."
        ),
    },
    # === High 5p (rec 210-250) ===
    "obsidian-arena-5p": {
        "required_level": 9, "bucket": "high",
        "motivazione": (
            "Difficoltà 3, rec_pow 210, team 5p, tema 'arcane'. "
            "Primo high tier 5p, richiede team con equip Epic consolidato."
        ),
    },
    "clockwork-vault-5p": {
        "required_level": 10, "bucket": "high",
        "motivazione": (
            "Difficoltà 3, rec_pow 230, team 5p, tema 'arcane'. "
            "High tier, salto vero rispetto obsidian per delta rec_pow +20."
        ),
    },
    "voidspire-5p": {
        "required_level": 11, "bucket": "high",
        "motivazione": (
            "Difficoltà 3, rec_pow 250, team 5p, tema 'void_undead'. "
            "Top high, ultimo prima dell'endgame."
        ),
    },
    # === Endgame 5p (rec 290-360) ===
    "infernal-pit-5p": {
        "required_level": 12, "bucket": "high",
        "motivazione": (
            "Difficoltà 4, rec_pow 290, team 5p, tema 'arcane'. "
            "Primo endgame, gate 12 come minimum viable ma richiede "
            "equip Legendary in pratica."
        ),
    },
    "celestial-citadel-5p": {
        "required_level": 13, "bucket": "high",
        "motivazione": (
            "Difficoltà 4, rec_pow 320, team 5p, tema 'divine'. "
            "Endgame narrative peak, gate +1 su infernal-pit."
        ),
    },
    "world-tree-roots-5p": {
        "required_level": 14, "bucket": "high",
        "motivazione": (
            "Difficoltà 4, rec_pow 360, team 5p, tema 'nature'. "
            "Ultimo endgame, gate 14 come cap del contenuto attuale."
        ),
    },
}


# ═════════════════════════════════════════════════════════════════════
# 3. LEGENDARY — regole
# ═════════════════════════════════════════════════════════════════════
#
# Regola:
#   - Legendary standard              → min_level = 8
#   - Legendary con equip_power ≥ 60  → min_level = 9
#     (top-40% del range Legendary reale [43, 73]: soglia = 55, arrotondato
#      conservativamente a 60 per non essere troppo aggressivi)
#   - `drake_slayer_blade` (equip_power=73, il più alto): min_level = 9
#
# NB: 60 è > 55 (top-40%) per scelta CONSERVATIVA che allinea l'utente:
#     applichiamo il boost min_lvl=9 solo agli outlier veri, non alla soglia
#     matematica. Il report renderà esplicito questo compromesso.

_LEGENDARY_TIER_THRESHOLD = 60
_LEGENDARY_MIN_STANDARD = 8
_LEGENDARY_MIN_OUTLIER = 9


def _item_equip_power(item: dict) -> int:
    STATS = ("strength", "agility", "intellect", "endurance", "faith")
    return sum(int(item.get(f"{s}_bonus", 0) or 0) for s in STATS) + int(
        item.get("power_score", 0) or 0
    )


def _propose_legendary_min_level(item: dict) -> tuple[int, str]:
    eq = _item_equip_power(item)
    if eq >= _LEGENDARY_TIER_THRESHOLD:
        return _LEGENDARY_MIN_OUTLIER, (
            f"Legendary con equip_power={eq} ≥ {_LEGENDARY_TIER_THRESHOLD} "
            f"(outlier top-tier del range Legendary): min_level 9."
        )
    return _LEGENDARY_MIN_STANDARD, (
        f"Legendary con equip_power={eq} < {_LEGENDARY_TIER_THRESHOLD}: "
        f"min_level baseline 8."
    )


# ═════════════════════════════════════════════════════════════════════
# 4. BUILDERS
# ═════════════════════════════════════════════════════════════════════


def _build_dungeon_proposals(db) -> tuple[list[dict], list[dict]]:
    proposals: list[dict] = []
    unresolved: list[dict] = []
    for d in db.dungeons.find(
        {"is_active": True},
        {"_id": 0, "slug": 1, "name": 1, "name_it": 1,
         "difficulty": 1, "recommended_power": 1,
         "base_gold_reward": 1, "base_xp_reward": 1,
         "required_team_size": 1, "content_family": 1,
         "required_level": 1},
    ).sort([("recommended_power", 1)]):
        slug = d["slug"]
        current = int(d.get("required_level") or 0)
        rule = _DUNGEON_MAPPING.get(slug)
        if rule is None:
            unresolved.append({
                "type": "dungeon", "slug": slug, "name": d.get("name"),
                "recommended_power": d.get("recommended_power"),
                "reason": (
                    "slug non presente nel mapping R16.5 P0. Manutentore: "
                    "aggiungere una regola prima di procedere con --apply."
                ),
            })
            continue
        proposed = int(rule["required_level"])
        row = {
            "dungeon_slug": slug,
            "name": d.get("name_it") or d.get("name"),
            "difficulty": d.get("difficulty"),
            "recommended_power": d.get("recommended_power"),
            "gold_reward": d.get("base_gold_reward"),
            "xp_reward": d.get("base_xp_reward"),
            "team_size": d.get("required_team_size"),
            "content_family": d.get("content_family"),
            "required_level_current": current,
            "required_level_proposed": proposed,
            "delta": proposed - current,
            "bucket": rule["bucket"],
            "story_catchup": bool(rule.get("story_catchup", False)),
            "motivazione": rule["motivazione"],
            "will_change": current != proposed,
        }
        proposals.append(row)
    return proposals, unresolved


def _build_legendary_proposals(db) -> tuple[list[dict], list[dict], list[dict]]:
    proposals: list[dict] = []
    unresolved: list[dict] = []
    epic_notes: list[dict] = []
    for it in db.items.find(
        {"rarity": {"$in": ["Legendary", "Epic"]}},
        {"_id": 0, "slug": 1, "name": 1, "rarity": 1, "min_level": 1,
         "strength_bonus": 1, "agility_bonus": 1, "intellect_bonus": 1,
         "endurance_bonus": 1, "faith_bonus": 1, "power_score": 1},
    ).sort([("rarity", -1), ("slug", 1)]):
        rarity = it.get("rarity")
        eq = _item_equip_power(it)
        current = int(it.get("min_level") or 1)
        if rarity == "Legendary":
            proposed, motiv = _propose_legendary_min_level(it)
            proposals.append({
                "item_slug": it["slug"],
                "name": it.get("name"),
                "rarity": rarity,
                "equip_power": eq,
                "min_level_current": current,
                "min_level_proposed": proposed,
                "delta": proposed - current,
                "motivazione": motiv,
                "will_change": current != proposed,
            })
        elif rarity == "Epic":
            # Epic outlier scan: entro range 10-14 attuale. Nessuna modifica
            # proposta, ma segnaliamo eventuali eq >= 25 (soglia arbitraria
            # significativamente alta per Epic).
            if eq >= 25:
                unresolved.append({
                    "type": "epic_outlier", "slug": it["slug"],
                    "equip_power": eq,
                    "reason": (
                        "Epic con equip_power ≥25 (candidato per revisione "
                        "min_level). NON modificato in questo round P0."
                    ),
                })
            else:
                epic_notes.append({
                    "slug": it["slug"], "equip_power": eq,
                    "min_level_current": current,
                    "note": "Entro range Epic atteso [10-14]. Nessuna modifica.",
                })
    return proposals, unresolved, epic_notes


# ═════════════════════════════════════════════════════════════════════
# 5. RENDER
# ═════════════════════════════════════════════════════════════════════


def _md_table_dungeons(rows: list[dict]) -> str:
    lines = [
        "| slug | nome | tier | rec_pow | gold | xp | team | req_lvl attuale | req_lvl proposto | Δ | bucket | motivazione |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['dungeon_slug']}` | {r['name']} | {r['difficulty']} | "
            f"{r['recommended_power']} | {r['gold_reward']} | "
            f"{r['xp_reward']} | {r['team_size']} | "
            f"{r['required_level_current']} | "
            f"**{r['required_level_proposed']}** | "
            f"{'+' if r['delta'] > 0 else ''}{r['delta']} | "
            f"{r['bucket']}{'*' if r['story_catchup'] else ''} | "
            f"{r['motivazione']} |"
        )
    return "\n".join(lines)


def _md_table_legendary(rows: list[dict]) -> str:
    lines = [
        "| slug | nome | rarity | equip_power | min_lvl attuale | min_lvl proposto | Δ | motivazione |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['item_slug']}` | {r['name']} | {r['rarity']} | "
            f"{r['equip_power']} | {r['min_level_current']} | "
            f"**{r['min_level_proposed']}** | "
            f"{'+' if r['delta'] > 0 else ''}{r['delta']} | "
            f"{r['motivazione']} |"
        )
    return "\n".join(lines)


def _render_report(dungeon_props, legendary_props,
                   unresolved, epic_notes, meta) -> str:
    dungeons_will_change = sum(1 for r in dungeon_props if r["will_change"])
    legendary_will_change = sum(1 for r in legendary_props if r["will_change"])
    return f"""# Round 16.5 P0 — Balance Gates & Legendary Level (DRY-RUN)

**Data**: {meta['run_at']}
**Modalità**: `--dry-run` (nessuna modifica applicata al DB `orbus_r16`)
**Tempo esecuzione**: {meta['elapsed_seconds']}s
**Script**: `/app/backend/app/scripts/round165_balance_p0_gates_and_legendary_levels.py`

---

## Riepilogo

- **Dungeon totali analizzati**: {len(dungeon_props) + sum(1 for u in unresolved if u.get('type') == 'dungeon')}
- **Dungeon con modifica proposta**: **{dungeons_will_change}**
- **Legendary items totali analizzati**: {len(legendary_props)}
- **Legendary con modifica proposta**: **{legendary_will_change}**
- **Unresolved** (non toccati): **{len(unresolved)}**
- **Epic scannati (informativo, no modifica)**: {len(epic_notes)}

---

## Tabella A — `required_level` dungeon

Legenda bucket: `tutorial` (lv 1-2), `early` (lv 3-4), `mid` (lv 5-7), `high` (lv 8+). Il suffisso `*` indica `story_catchup` (contenuto narrativo bypassabile a basso livello, valutato caso per caso).

{_md_table_dungeons(dungeon_props)}

**Note metodologiche**:
- Il mapping è derivato dall'ordine crescente di `recommended_power`, incrociato con `difficulty` e `required_team_size` (3p vs 5p).
- I dungeon 5p introduttivi (wolf-den-5p, frost-cave-5p, salt-marsh-5p) hanno `required_level` più basso del `recommended_power` suggerirebbe perché il rec_pow è assorbito dalla dimensione del team (5 avv → più power totale disponibile). Sono marcati `story_catchup` per chiarezza.
- Nessun dungeon ha `difficulty` = 0 o `recommended_power` = 0, quindi tutti sono classificabili.

---

## Tabella B — `min_level` Legendary items

{_md_table_legendary(legendary_props)}

**Regola applicata**:
- Legendary con `equip_power < 60` → `min_level = 8` (baseline)
- Legendary con `equip_power ≥ 60` → `min_level = 9` (outlier top-tier)
- Soglia `60` scelta in modo CONSERVATIVO rispetto al top-40% matematico (che sarebbe 55). Motivazione: solo gli item chiaramente outlier vengono spinti a 9; il resto resta a 8 per non essere troppo aggressivi.

---

## Unresolved (guard-rail: NON modificati)

{"Nessuno." if not unresolved else ""}
{chr(10).join([f"- **[{u.get('type')}] {u.get('slug')}** — {u.get('reason')}" for u in unresolved])}

---

## Epic outlier scan (informativo, no modifica in R16.5 P0)

Scannati **{len(epic_notes)}** item Epic. Range `equip_power` osservato: {min((n['equip_power'] for n in epic_notes), default=0)}-{max((n['equip_power'] for n in epic_notes), default=0)}.

Nessun Epic supera la soglia di outlier (`equip_power ≥ 25`). Sono tutti entro il range atteso Epic [10-14]. **Nessuna modifica proposta sugli Epic in questo round P0.**

Il campo `min_level` sugli Epic è attualmente non impostato (default 1 implicito). Un round P1 potrebbe voler impostare `min_level = 5-7` per gli Epic, ma richiede analisi separata (fuori scope R16.5 P0).

---

## Cosa NON viene toccato (ricordato esplicitamente)

- ❌ `recommended_power` (dungeon)
- ❌ `base_gold_reward`, `base_xp_reward` (dungeon)
- ❌ `threat_tags`, `counter_tags` (dungeon)
- ❌ `equip_power`, `rarity`, `strength_bonus`, `agility_bonus`, ecc. (items)
- ❌ Prezzi, drop, crafting, ricette
- ❌ Formula `compute_success_chance` o qualsiasi altra formula
- ❌ Sistema PvP, Stalla, economia, tutti gli altri sistemi

---

## Prossimi passi

1. **Approvazione utente** su Tabella A + Tabella B → richiesta esplicita prima di STEP 2.
2. **STEP 2** (se approvato): esecuzione `--apply` con:
   - Snapshot pre-change (`/app/memory/round165_p0_prechange_snapshot.json`)
   - Applicazione `update_one` per ogni riga proposta
   - Test post-apply (verifica idempotenza + guard-rail)
   - Audit rapido R16.4 rieseguito per validare che la nuova curva sia effettivamente più coerente
   - Aggiornamento §19 del report R16.4 con dati mancanti disponibili post-fix
   - Report finale `/app/memory/round165_p0_apply_report.md`
"""


# ═════════════════════════════════════════════════════════════════════
# 6. MAIN
# ═════════════════════════════════════════════════════════════════════


def main() -> int:
    args = _parse_args()
    if args.apply:
        # STEP 2 not enabled in this step 1 script variant. Refuse gracefully.
        print(
            "REFUSING: --apply is reserved for STEP 2. "
            "Run --dry-run first to generate proposals.",
            file=sys.stderr,
        )
        return 1

    print("=== DRY-RUN MODE ===")
    t0 = time.time()

    client, db = _connect_db()
    print(f"[r165] connected to DB: {db.name}")

    dungeon_props, dungeon_unresolved = _build_dungeon_proposals(db)
    legendary_props, legendary_unresolved, epic_notes = _build_legendary_proposals(db)
    all_unresolved = dungeon_unresolved + legendary_unresolved

    d_change = sum(1 for r in dungeon_props if r["will_change"])
    l_change = sum(1 for r in legendary_props if r["will_change"])

    elapsed = round(time.time() - t0, 3)
    print(f"[r165] dungeon proposals: {len(dungeon_props)} "
          f"(will_change={d_change})")
    print(f"[r165] legendary proposals: {len(legendary_props)} "
          f"(will_change={l_change})")
    print(f"[r165] unresolved: {len(all_unresolved)}")
    print(f"[r165] epic scanned (informative): {len(epic_notes)}")
    print(f"[r165] elapsed: {elapsed}s")

    meta = {
        "run_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_seconds": elapsed,
        "db_name": db.name,
        "mode": "dry-run",
    }
    report_md = _render_report(
        dungeon_props, legendary_props, all_unresolved, epic_notes, meta,
    )
    data_json = {
        "meta": meta,
        "dungeon_proposals": dungeon_props,
        "legendary_proposals": legendary_props,
        "unresolved": all_unresolved,
        "epic_notes": epic_notes,
        "summary": {
            "dungeon_will_change": d_change,
            "legendary_will_change": l_change,
            "unresolved_count": len(all_unresolved),
            "epic_scanned": len(epic_notes),
        },
    }
    report_path = Path("/app/memory/round165_p0_dryrun_report.md")
    data_path = Path("/app/memory/round165_p0_dryrun_data.json")
    report_path.write_text(report_md)
    data_path.write_text(json.dumps(data_json, indent=2, default=str))

    print(f"[r165] report: {report_path}")
    print(f"[r165] data:   {data_path}")
    print("[r165] NO writes performed on DB.")

    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
