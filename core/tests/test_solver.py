# core/tests/test_solver.py
from core.solver import _recommend, hand_rank, run

PAIR = ["As", "Ad", "7c", "5h", "2d"]  # пара тузов
HIGH = ["Ks", "Qd", "9c", "5h", "2d"]  # только старшая карта


def test_pair_beats_high_card():
    # эталон: правило игры — известно до первой строки кода
    assert hand_rank(PAIR) > hand_rank(HIGH)


def test_aa_wins_about_85_percent():
    # эталон: справочная таблица шансов (heads-up AA ~85% winrate), поэтому ДИАПАЗОН
    r = run(
        {
            "hole_cards": ["As", "Ah"],
            "opponents": 1,
            "simulations": 10_000,
            "seed": 1,
        }
    )
    assert 0.80 < r["win_probability"] < 0.90


def test_quads_on_board_is_always_a_tie():
    # эталон: каре тузов на столе + кикер-король — сильнее уже не собрать
    # ни герою, ни оппоненту (все 4 туза уже разобраны), поэтому ответ
    # известен ТОЧНО заранее: 100% ничья при любом количестве раздач.
    r = run(
        {
            "hole_cards": ["2s", "3s"],
            "community": ["Ah", "Ad", "As", "Ac", "Kh"],
            "opponents": 1,
            "simulations": 2_000,
            "seed": 42,
        }
    )
    assert r["tie_probability"] == 1.0
    assert r["win_probability"] == 0.0
    assert r["loss_probability"] == 0.0


def test_no_bet_to_call_recommends_check_not_fold():
    # эталон: call_amount = 0 — ставить нечего, сброс бессмыслен, поэтому CHECK
    assert _recommend(equity=0.2, pot_size=100, call_amount=0) == "CHECK"
