"""FASE 9I — contratto dell'Addestramento solo-XP.

Acceptance del mandato:
  * capacità 2, durata max 24h;
  * SOLO XP, con curva LENTA derivata dalla curva XP reale;
  * una sessione di 24h non permette salti assurdi di livello
    (mai ≥ 2 livelli, nemmeno col recupero);
  * bonus recupero +50% sotto il benchmark di gilda, MAI cumulato con
    altri moltiplicatori (l'XP di addestramento è piatta).
"""
from app.shared.constants import ADVENTURER_MAX_LEVEL
from app.shared.progression import xp_required_for_next_level
from app.training.catalog import (
    TRAINING_CAPACITY,
    TRAINING_CATCHUP_MULTIPLIER,
    TRAINING_LEVEL_FRACTION_PER_DAY,
    TRAINING_MAX_HOURS,
    TRAINING_MIN_HOURS,
    catchup_benchmark_level,
    has_training_catchup,
    simulate_training_curve,
    training_xp_for_session,
    training_xp_per_hour,
)

SIM_LEVELS = (1, 10, 20, 40, 60, 80)


def test_regole_base():
    assert TRAINING_CAPACITY == 2
    assert TRAINING_MAX_HOURS == 24
    assert TRAINING_MIN_HOURS == 1
    assert TRAINING_CATCHUP_MULTIPLIER == 1.5


def test_simulazione_curva_lenta_ma_utile():
    rows = simulate_training_curve(SIM_LEVELS)
    assert [r["level"] for r in rows] == list(SIM_LEVELS)
    for r in rows:
        if r["level"] >= ADVENTURER_MAX_LEVEL:
            assert r["xp_per_hour"] == 0
            continue
        # Utile: almeno metà livello al giorno...
        assert r["level_fraction_24h_base"] >= 0.5, r
        # ...ma lenta: mai un livello intero senza recupero.
        assert r["level_fraction_24h_base"] < 1.0, r
        # Il target di design è ~75% del livello/24h.
        assert abs(
            r["level_fraction_24h_base"] - TRAINING_LEVEL_FRACTION_PER_DAY
        ) < 0.05, r


def test_24h_non_permette_salti_assurdi():
    """Anche col recupero +50%, una sessione da 24h non vale mai 2 livelli."""
    for level in SIM_LEVELS:
        if level >= ADVENTURER_MAX_LEVEL:
            continue
        xp = training_xp_for_session(level, TRAINING_MAX_HOURS, catchup=True)
        two_levels = (
            xp_required_for_next_level(level)
            + xp_required_for_next_level(level + 1)
        )
        assert xp < two_levels, level


def test_xp_rate_cresce_col_livello_e_si_azzera_al_cap():
    rates = [training_xp_per_hour(lvl) for lvl in (1, 10, 20, 40, 60, 79)]
    assert rates == sorted(rates)
    assert all(r > 0 for r in rates)
    assert training_xp_per_hour(ADVENTURER_MAX_LEVEL) == 0
    assert training_xp_for_session(ADVENTURER_MAX_LEVEL, 24, catchup=True) == 0


def test_catchup_benchmark_top5():
    # Benchmark = media dei 5 livelli più alti del roster.
    assert catchup_benchmark_level([40, 38, 35, 30, 28, 5, 3]) == 34
    assert catchup_benchmark_level([10]) == 10
    assert catchup_benchmark_level([]) == 1
    assert has_training_catchup(5, 34) is True
    assert has_training_catchup(34, 34) is False
    assert has_training_catchup(40, 34) is False


def test_bonus_recupero_esattamente_una_volta():
    """+50% esatto: nessun cumulo con trait/consumabili (XP piatta)."""
    base = training_xp_for_session(10, 10, catchup=False)
    boosted = training_xp_for_session(10, 10, catchup=True)
    assert boosted == int(base * TRAINING_CATCHUP_MULTIPLIER)


def test_le_ore_oltre_il_massimo_non_contano():
    assert training_xp_for_session(10, 48, catchup=False) == \
        training_xp_for_session(10, TRAINING_MAX_HOURS, catchup=False)
    assert training_xp_for_session(10, 0, catchup=True) == 0
