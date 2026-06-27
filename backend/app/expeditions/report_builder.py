"""Phase 14.5 (ROUND 2 Fase 3) — Expedition report explainability.

Pure builder that derives a human-readable post-mortem from data already
persisted on the expedition document. NO new DB writes, NO new RNG roll:
the report explains the *expedition that actually happened* using the
final_score, success_chance, team_power, equipment delta and the
traits/class snapshots captured at dispatch.

Compatibility: any field can be missing on legacy expedition docs; the
builder degrades to `report_summary=None, report_steps=[]` so the UI can
show its fallback without crashing.

Localisation: the builder emits Italian display copy (the production
language). The English audience is a small minority on the EN i18n path;
the front-end falls back gracefully to those Italian strings when no
override exists (acceptable for ROUND 2 Fase 3 — explicit follow-up note
in the deploy doc).
"""
from __future__ import annotations

import hashlib
import re
from typing import Optional


# ── Test-trait anti-leak (mirrors seed_runner._TEST_TRAIT_NAME_RE) ────────────
_TEST_TRAIT_NAME_RE = re.compile(
    r"^(Test|TEST_|qa_|dev_|pytest_)|_[a-f0-9]{6,}$|^[a-f0-9-]{16,}$",
    re.IGNORECASE,
)


def _is_player_facing_trait(t: dict) -> bool:
    """A trait is shown in the report only if:
    - it's marked active (or has no flag — legacy traits default to active),
    - it's NOT marked test (or has no flag — legacy traits default to non-test),
    - its display name does NOT match the test-pattern regex.

    This mirrors the public projection used by `adventurers/services.py`
    so the report cannot leak hidden test traits.
    """
    if t.get("is_active") is False:
        return False
    if t.get("is_test") is True:
        return False
    name = (t.get("display_name") or t.get("name") or "").strip()
    if not name:
        return False
    if _TEST_TRAIT_NAME_RE.search(name):
        return False
    return True


# ── Class display names (Italian, single source of truth here) ────────────────
CLASS_DISPLAY_IT = {
    "Warrior": ("Guerriero", "Tank"),
    "Mage": ("Mago", "DPS"),
    "Priest": ("Sacerdote", "Healer"),
    "Rogue": ("Ladro", "DPS"),
    "Ranger": ("Ranger", "DPS"),
}


def _class_display(class_name: str, fallback_role: str) -> dict:
    pair = CLASS_DISPLAY_IT.get(class_name)
    if pair:
        return {"display_name": pair[0], "role": pair[1]}
    # Unknown class — degrade to the snapshotted English name + provided role.
    return {"display_name": class_name or "—", "role": fallback_role or "—"}


def _trait_public(t: dict) -> dict:
    return {
        "display_name": (t.get("display_name") or t.get("name") or "").strip(),
        "polarity": t.get("polarity") or ("positive" if t.get("is_positive", True) else "negative"),
        "description": (t.get("description") or "").strip(),
    }


# ── Outcome classification ────────────────────────────────────────────────────
def _classify_outcome(exp: dict) -> str:
    """Map result_summary + (final_score vs success_chance) into 3 buckets.

    - success: hard win (final_score <= success_chance - 10), or summary=="Success"
      with score within the easy band.
    - partial_success: summary=="Success" but final_score within 10 of the
      threshold (a "barely made it" run) — explains the lack of premium loot.
    - failure: summary != "Success".
    """
    summary = exp.get("result_summary")
    score = exp.get("final_score")
    chance = exp.get("success_chance") or 0
    if summary == "Success":
        if score is None:
            return "success"
        # Barely-made-it window: within the last 10 points of the threshold.
        if score >= max(1, chance - 9):
            return "partial_success"
        return "success"
    if summary in (None, "in_progress"):
        # Should not be called before completion; defensive return.
        return "failure"
    return "failure"


def _outcome_title(outcome: str) -> str:
    return {
        "success": "Vittoria",
        "partial_success": "Successo parziale",
        "failure": "Sconfitta",
    }[outcome]


def _narrative_summary(outcome: str, dungeon_name: str, team_size: int) -> str:
    if outcome == "success":
        return (
            f"La squadra di {team_size} avventurieri ha completato {dungeon_name} "
            f"con margine: missione riuscita, bottino raccolto e nessun ritiro forzato."
        )
    if outcome == "partial_success":
        return (
            f"La spedizione a {dungeon_name} è stata vinta, ma per un soffio: "
            f"qualche errore nelle fasi centrali e bottino sotto le aspettative."
        )
    return (
        f"Il gruppo non è riuscito a domare {dungeon_name}. "
        f"Il ritiro ordinato ha salvato gli avventurieri, ma le ricompense restano scarne."
    )


# ── Step assemblers ───────────────────────────────────────────────────────────
def _gather_traits_for_step(
    step_type: str,
    members: list,
    *,
    polarity_filter: Optional[set] = None,
) -> tuple[list[str], list[dict]]:
    """Collect adventurer names + display-only trait dicts pertinent to a step.

    `polarity_filter` constrains which trait polarities surface here (e.g.
    only positive on the Loot step). Pertinence is decided by `_TRAIT_TAGS`.
    """
    names: list[str] = []
    traits: list[dict] = []
    seen_keys: set[str] = set()
    for m in members:
        member_traits = m.get("traits_snapshot") or []
        keep_member = False
        for t in member_traits:
            if not _is_player_facing_trait(t):
                continue
            stats = _TRAIT_TAGS.get(_canonical_trait_key(t), set())
            if step_type not in stats:
                continue
            if polarity_filter and (t.get("polarity") not in polarity_filter):
                continue
            pub = _trait_public(t)
            key = pub["display_name"].lower()
            if key in seen_keys:
                continue
            seen_keys.add(key)
            traits.append(pub)
            keep_member = True
        if keep_member:
            names.append(m.get("name_snapshot") or "?")
    return names, traits


def _canonical_trait_key(t: dict) -> str:
    """Lowercased `code` first (Phase 14.3-c canonical), fallback to display_name."""
    code = (t.get("code") or "").strip().lower()
    if code:
        return code
    return (t.get("display_name") or t.get("name") or "").strip().lower()


# Which step types each canonical trait is *narratively* pertinent to.
# Lowercase canonical codes — keep this list short, explicit and stable.
_TRAIT_TAGS: dict[str, set[str]] = {
    # Phase 14.3-c canonical IT trait codes
    "lucky":      {"traps", "loot"},
    "brave":      {"combat", "boss"},
    "disciplined":{"exploration", "combat"},
    "sharp_eye":  {"exploration", "traps"},
    "reckless":   {"combat", "boss"},
    "fragile":    {"combat", "boss", "recovery"},
    "greedy":     {"loot"},
    "loyal":      {"combat", "recovery"},
    "clumsy":     {"traps", "exploration"},
    "inspired":   {"reward"},
    # Legacy English-named traits (best-effort tagging)
    "fortunato":  {"traps", "loot"},
    "coraggioso": {"combat", "boss"},
    "disciplinato": {"exploration", "combat"},
    "occhio acuto": {"exploration", "traps"},
    "avventato":  {"combat", "boss"},
    "fragile":    {"combat", "boss", "recovery"},  # noqa: F601 — IT label same as canonical
    "avido":      {"loot"},
    "leale":      {"combat", "recovery"},
    "goffo":      {"traps", "exploration"},
    "ispirato":   {"reward"},
}


def _class_modifiers_for_step(step_type: str, members: list) -> list[dict]:
    """Class/role contributions narratively pertinent to a step."""
    roles_present: dict[str, str] = {}
    for m in members:
        role = (m.get("role_snapshot") or "").strip()
        class_name = (m.get("class_name_snapshot") or "").strip()
        if role and role not in roles_present:
            roles_present[role] = class_name
    out: list[dict] = []
    if step_type == "combat" or step_type == "boss":
        if "Tank" in roles_present:
            out.append(_class_display(roles_present["Tank"], "Tank"))
        if "DPS" in roles_present:
            out.append(_class_display(roles_present["DPS"], "DPS"))
    if step_type in ("combat", "boss", "recovery"):
        if "Healer" in roles_present:
            out.append(_class_display(roles_present["Healer"], "Healer"))
    if step_type in ("exploration", "traps"):
        # Rogue / Ranger as scouts
        for m in members:
            cls = (m.get("class_name_snapshot") or "").strip()
            if cls in ("Rogue", "Ranger"):
                out.append(_class_display(cls, m.get("role_snapshot") or "DPS"))
                break
    # Deduplicate while preserving order
    seen = set()
    dedup = []
    for c in out:
        k = (c["display_name"], c["role"])
        if k not in seen:
            seen.add(k)
            dedup.append(c)
    return dedup


def _modifier_phrases(traits: list[dict], step_type: str) -> list[str]:
    """Generate Italian one-liners from trait public dicts."""
    out: list[str] = []
    for t in traits:
        name = t["display_name"]
        pol = t.get("polarity")
        if step_type == "loot":
            verb = "ha migliorato la qualità del bottino" if pol == "positive" else (
                "ha ridotto la qualità del bottino" if pol == "negative" else "ha influenzato il bottino"
            )
        elif step_type == "traps":
            verb = "ha aiutato a evitare le trappole" if pol == "positive" else (
                "ha aumentato il rischio di trappole" if pol == "negative" else "ha influenzato le trappole"
            )
        elif step_type == "combat":
            verb = "ha rafforzato il fronte" if pol == "positive" else (
                "ha indebolito il fronte" if pol == "negative" else "ha alterato lo scontro"
            )
        elif step_type == "boss":
            verb = "ha contribuito allo scontro decisivo" if pol == "positive" else (
                "ha aumentato il rischio nello scontro decisivo" if pol == "negative" else "ha influenzato il boss"
            )
        elif step_type == "exploration":
            verb = "ha aiutato l'esplorazione" if pol == "positive" else (
                "ha rallentato l'esplorazione" if pol == "negative" else "ha alterato l'esplorazione"
            )
        elif step_type == "recovery":
            verb = "ha mitigato le ferite" if pol == "positive" else (
                "ha aggravato le ferite" if pol == "negative" else "ha influenzato il recupero"
            )
        else:
            verb = "ha influenzato l'esito"
        out.append(f"{name}: {verb}.")
    return out


def _result_of_step(step_type: str, outcome: str, team_power: int, rec_power: int) -> str:
    """Map (step_type, expedition outcome, power delta) to step result."""
    margin = team_power - rec_power
    if step_type == "exploration":
        if outcome == "failure":
            return "partial" if margin >= -5 else "failure"
        return "success" if margin >= 0 else "partial"
    if step_type == "combat":
        if outcome == "success":
            return "success"
        if outcome == "partial_success":
            return "partial"
        return "failure"
    if step_type == "traps":
        return "neutral" if outcome != "failure" else "partial"
    if step_type == "boss":
        return {"success": "success", "partial_success": "partial", "failure": "failure"}[outcome]
    if step_type == "loot":
        return "success" if outcome == "success" else (
            "partial" if outcome == "partial_success" else "neutral"
        )
    if step_type == "recovery":
        return "partial"
    return "neutral"


def _step(
    *,
    type_: str,
    label: str,
    result: str,
    description: str,
    members: list,
    polarity_filter: Optional[set] = None,
) -> dict:
    inv_names, inv_traits = _gather_traits_for_step(type_, members, polarity_filter=polarity_filter)
    inv_classes = _class_modifiers_for_step(type_, members)
    modifiers = _modifier_phrases(inv_traits, type_)
    return {
        "type": type_,
        "label": label,
        "result": result,
        "description": description,
        "modifiers": modifiers,
        "involved_adventurers": inv_names,
        "involved_traits": inv_traits,
        "involved_classes": inv_classes,
    }


def _is_boss_dungeon(dungeon: dict) -> bool:
    slug = (dungeon or {}).get("slug") or ""
    if slug in ("dragons-hoard",):
        return True
    rec = int((dungeon or {}).get("recommended_power") or 0)
    return rec >= 60


# ── Top-level builder ────────────────────────────────────────────────────────
def build_expedition_report(
    exp: dict,
    members: list,
    dungeon: Optional[dict],
    loot_items: list,
) -> dict:
    """Pure builder. Returns {report_summary, report_steps} or both None for legacy/in-progress.

    - exp:     expedition Mongo doc (already post-completion). For an
               in_progress doc we return both fields as None.
    - members: list of expedition_members Mongo docs (with traits_snapshot).
    - dungeon: the dungeon doc (may be None if dungeon was deleted).
    - loot_items: list of item_public dicts (already projected).
    """
    if (exp or {}).get("status") != "completed":
        return {"report_summary": None, "report_steps": None}

    outcome = _classify_outcome(exp)
    team_power = int(exp.get("final_team_power") or exp.get("team_power") or 0)
    rec_power = int((dungeon or {}).get("recommended_power") or 0)
    dungeon_name = exp.get("dungeon_name") or (dungeon or {}).get("name") or "il dungeon"
    team_size = len(members or [])
    success_chance_used = int(
        exp.get("success_chance_with_equipment")
        or exp.get("success_chance")
        or 0
    )

    summary = {
        "outcome": outcome,
        "title": _outcome_title(outcome),
        "narrative_summary": _narrative_summary(outcome, dungeon_name, team_size),
        "success_chance_used": success_chance_used,
        "team_power": team_power,
        "recommended_power": rec_power,
        "final_score": exp.get("final_score"),
        "gold_earned": int(exp.get("gold_reward") or 0),
        "xp_earned": int(exp.get("xp_reward") or 0),
        "loot_found": [
            {
                "item_id": it.get("id"),
                "name": it.get("name"),
                "display_name_it": it.get("display_name_it") or it.get("name"),
                "display_name_en": it.get("display_name_en") or it.get("name"),
                "rarity": it.get("rarity"),
            }
            for it in (loot_items or [])
        ],
        "injuries": 0,   # not modelled in current schema
        "fatigue": 0,    # not modelled in current schema
    }

    steps: list[dict] = []

    # 1) Exploration
    steps.append(_step(
        type_="exploration",
        label="Esplorazione",
        result=_result_of_step("exploration", outcome, team_power, rec_power),
        description=(
            "Il gruppo si muove con metodo tra le prime sale: pochi sprechi, ritmo solido."
            if outcome != "failure"
            else "Il gruppo si addentra con cautela, ma il terreno è ostico."
        ),
        members=members,
    ))

    # 2) Traps — show only if any pertinent trait is present, otherwise skip.
    trap_inv_names, trap_inv_traits = _gather_traits_for_step("traps", members)
    if trap_inv_traits:
        steps.append(_step(
            type_="traps",
            label="Trappole",
            result=_result_of_step("traps", outcome, team_power, rec_power),
            description=(
                "Lungo il corridoio principale alcuni meccanismi vengono individuati e disinnescati."
                if outcome != "failure"
                else "Una trappola sorprende il gruppo: il margine d'errore si è assottigliato."
            ),
            members=members,
        ))

    # 3) Combat
    steps.append(_step(
        type_="combat",
        label="Combattimento",
        result=_result_of_step("combat", outcome, team_power, rec_power),
        description=(
            "Lo scontro centrale è gestito con disciplina, la formazione tiene."
            if outcome == "success"
            else (
                "Lo scontro centrale è duro: il gruppo vince ma con qualche sbavatura."
                if outcome == "partial_success"
                else "La formazione cede sotto pressione, il gruppo è costretto a ripiegare."
            )
        ),
        members=members,
    ))

    # 4) Boss (only if dungeon qualifies)
    if dungeon and _is_boss_dungeon(dungeon):
        steps.append(_step(
            type_="boss",
            label="Scontro decisivo",
            result=_result_of_step("boss", outcome, team_power, rec_power),
            description=(
                "Il nemico più temibile della spedizione viene affrontato a viso aperto."
                if outcome == "success"
                else (
                    "Lo scontro decisivo si chiude per il rotto della cuffia."
                    if outcome == "partial_success"
                    else "Il nemico più temibile è troppo: il gruppo arretra."
                )
            ),
            members=members,
        ))

    # 5) Loot — always present so the user sees an explicit outcome
    if summary["loot_found"]:
        loot_desc = (
            f"Recuperati {len(summary['loot_found'])} oggetti dal sito."
        )
    else:
        loot_desc = (
            "Nessun bottino degno di nota questa volta."
            if outcome != "success"
            else "La squadra è uscita a mani vuote nonostante la vittoria."
        )
    steps.append(_step(
        type_="loot",
        label="Bottino",
        result=_result_of_step("loot", outcome, team_power, rec_power),
        description=loot_desc,
        members=members,
        polarity_filter={"positive", "mixed"} if outcome == "success" else None,
    ))

    # 6) Recovery — only on failure (and partial)
    if outcome != "success":
        steps.append(_step(
            type_="recovery",
            label="Ritirata",
            result="partial",
            description=(
                "Il gruppo si ritira in ordine, qualche ferita leggera ma nessuna perdita."
                if outcome == "partial_success"
                else "Ritirata forzata: il gruppo torna alla base con esperienza ma poche ricompense."
            ),
            members=members,
        ))

    # Use exp.id for a deterministic but irrelevant hash check — kept for
    # potential future ordering tweaks. ROUND 6B FASE C — SHA-256 (was MD5;
    # value is discarded so the swap is a no-op for behaviour but removes
    # MD5 from the dependency graph entirely).
    _ = hashlib.sha256((exp.get("id") or "").encode("utf-8")).hexdigest()

    return {"report_summary": summary, "report_steps": steps}


__all__ = ["build_expedition_report"]
