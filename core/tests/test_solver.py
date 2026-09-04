# core/tests/test_solver.py
from core.solver import hand_rank, run

PAIR = ["As", "Ad", "7c", "5h", "2d"]  # пара тузов
HIGH = ["Ks", "Qd", "9c", "5h", "2d"]  # только старшая карта


def test_pair_beats_high_card():
    # эталон: правило игры — известно до первой строки кода
    assert hand_rank(PAIR) > hand_rank(HIGH)


def test_aa_wins_about_85_percent():
    # эталон: справочная таблица шансов, поэтому ДИАПАЗОН
    r = run(
        {
            "hole_cards": ["As", "Ah"],
            "opponents": 1,
            "simulations": 10_000,
            "seed": 1,
        }
    )
    assert 0.80 < r["win_probability"] < 0.90