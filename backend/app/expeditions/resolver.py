"""FASE 0 — Motore di risoluzione spedizione (puro, no DB, no side effect).

Contiene:
- calculate_team_power
- calculate_success_chance
- resolve_expedition
- report narrativo deterministico in italiano

Dataclasses semplici per l'input; nessuna dipendenza esterna oltre a
`random` (con seed opzionale) e `dataclasses`.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Iterable


# ─── Data structures ──────────────────────────────────────────────────────
@dataclass(frozen=True)
class AdventurerSnapshot:
    """Snapshot immutabile di un avventuriero per la risoluzione."""

    id: str
    name: str
    role: str  # "Tank" | "Healer" | "DPS"
    level: int
    strength: int = 0
    agility: int = 0
    intellect: int = 0
    vitality: int = 0

    @property
    def stat_sum(self) -> int:
        return self.strength + self.agility + self.intellect + self.vitality


@dataclass(frozen=True)
class DungeonSpec:
    """Snapshot immutabile di un dungeon."""

    slug: str
    name: str
    recommended_power: int
    base_gold_reward: int
    base_xp_reward: int


@dataclass
class ExpeditionResult:
    """Risultato deterministico prodotto dal resolver."""

    outcome: str  # "success" | "failure"
    team_power: int
    success_chance: int
    roll: int
    gold_reward: int
    xp_per_member: int
    loot_dropped: bool
    report_text: str
    seed_used: int | None = None
    members_used: list[str] = field(default_factory=list)


# ─── Team power ───────────────────────────────────────────────────────────
def calculate_team_power(
    team: Iterable[AdventurerSnapshot],
    roles: list[str] | None = None,
) -> int:
    """Somma stats + level*2 per membro, più bonus di composizione.

    Il parametro `roles` è mantenuto per firma esplicita dal brief; se
    non fornito, viene derivato dai membri del team.
    """
    team_list = list(team)
    base = sum(a.stat_sum + a.level * 2 for a in team_list)

    present_roles = {r.lower() for r in (roles or [a.role for a in team_list])}
    has_tank = "tank" in present_roles
    has_healer = "healer" in present_roles
    has_dps = "dps" in present_roles

    comp_bonus = 0
    if has_tank:
        comp_bonus += 5
    if has_healer:
        comp_bonus += 5
    if has_dps:
        comp_bonus += 5
    if has_tank and has_healer and has_dps:
        comp_bonus += 10  # bonus squadra bilanciata

    return base + comp_bonus


# ─── Success chance ───────────────────────────────────────────────────────
def calculate_success_chance(team_power: int, recommended_power: int) -> int:
    """base 50 + delta, con clamp [10, 95].

    Delta = (team_power - recommended_power) // 2, così che 20 punti di
    scarto valgano ~10% di probabilità in più.
    """
    delta = (team_power - recommended_power) // 2
    raw = 50 + delta
    if raw < 10:
        return 10
    if raw > 95:
        return 95
    return raw


# ─── Report narrativo ─────────────────────────────────────────────────────
_SUCCESS_TEMPLATES = [
    (
        "La tua squadra è entrata nei {dungeon_name} all'alba. "
        "{leader} ha guidato l'avanzata mentre {support} coordinava le manovre. "
        "Dopo uno scontro breve ma brutale, la minaccia principale è caduta e "
        "il gruppo ha reclamato il bottino. Spedizione riuscita."
    ),
    (
        "I vostri avventurieri hanno affrontato i {dungeon_name} con disciplina. "
        "{leader} teneva la prima linea, {support} copriva le retrovie. "
        "Nessun membro è rimasto indietro. Il capitano nemico è fuggito nei "
        "tunnel inferiori. Spedizione riuscita."
    ),
    (
        "Le torce hanno tremato nei corridoi dei {dungeon_name}. "
        "Grazie alla presenza di {leader} e alla lucidità di {support}, "
        "la squadra ha superato le insidie e strappato la vittoria. "
        "Spedizione riuscita."
    ),
]

_FAILURE_TEMPLATES = [
    (
        "La tua squadra si è spinta troppo in profondità nei {dungeon_name}. "
        "Un'imboscata nascosta ha spezzato la formazione di {leader} e "
        "{support} ha ordinato la ritirata prima che fosse tardi. "
        "La spedizione è fallita, ma i sopravvissuti sono tornati con esperienza preziosa."
    ),
    (
        "I {dungeon_name} si sono rivelati più letali del previsto. "
        "{leader} ha coperto la fuga mentre {support} trascinava i feriti fuori dalle tenebre. "
        "La missione è stata interrotta: spedizione fallita."
    ),
    (
        "Un errore di lettura della mappa ha condotto la squadra dentro una trappola dei {dungeon_name}. "
        "{leader} e {support} hanno tenuto duro il tempo necessario per ritirarsi. "
        "Spedizione fallita, ma nessuno è stato lasciato indietro."
    ),
]


def _pick_narrative_actors(team: list[AdventurerSnapshot]) -> tuple[str, str]:
    """Sceglie due nomi rappresentativi (leader + support) preferendo ruoli."""
    if not team:
        return ("la vanguardia", "il resto del gruppo")
    tank = next((a for a in team if a.role.lower() == "tank"), None)
    healer = next((a for a in team if a.role.lower() == "healer"), None)
    dps = next((a for a in team if a.role.lower() == "dps"), None)
    leader = tank or dps or team[0]
    support = healer or dps or (team[1] if len(team) > 1 else leader)
    if support is leader and len(team) > 1:
        support = team[1]
    return (leader.name, support.name)


def _build_report(
    outcome: str,
    dungeon: DungeonSpec,
    team: list[AdventurerSnapshot],
    rng: random.Random,
) -> str:
    templates = _SUCCESS_TEMPLATES if outcome == "success" else _FAILURE_TEMPLATES
    tpl = rng.choice(templates)
    leader, support = _pick_narrative_actors(team)
    return tpl.format(dungeon_name=dungeon.name, leader=leader, support=support)


# ─── Resolver principale ──────────────────────────────────────────────────
def resolve_expedition(
    team: list[AdventurerSnapshot],
    dungeon: DungeonSpec,
    rng_seed: int | None = None,
) -> ExpeditionResult:
    """Risolve una spedizione in modo deterministico se `rng_seed` è fornito."""
    rng = random.Random(rng_seed) if rng_seed is not None else random.Random()

    roles = [a.role for a in team]
    power = calculate_team_power(team, roles)
    chance = calculate_success_chance(power, dungeon.recommended_power)

    roll = rng.randint(1, 100)
    success = roll <= chance

    if success:
        outcome = "success"
        gold = dungeon.base_gold_reward
        xp = dungeon.base_xp_reward
        loot = rng.random() < 0.5
    else:
        outcome = "failure"
        gold = round(dungeon.base_gold_reward * 0.25)
        xp = round(dungeon.base_xp_reward * 0.4)
        loot = False

    report = _build_report(outcome, dungeon, team, rng)

    return ExpeditionResult(
        outcome=outcome,
        team_power=power,
        success_chance=chance,
        roll=roll,
        gold_reward=gold,
        xp_per_member=xp,
        loot_dropped=loot,
        report_text=report,
        seed_used=rng_seed,
        members_used=[a.id for a in team],
    )
