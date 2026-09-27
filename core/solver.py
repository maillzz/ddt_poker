"""Покерный солвер и симулятор Монте-Карло.

Контракт (см. core/__init__.py): run(params: dict) -> dict. Никакого Django,
HTTP или БД в этом модуле — только чистые функции над картами.
"""
import random

from treys import Card, Deck, Evaluator

VERSION = "1.0.0"

_EVALUATOR = Evaluator()
_RANKS = "23456789TJQKA"


def _to_treys(card: str) -> int:
    """'As' / 'th' / 'Td' -> внутреннее представление treys."""
    rank, suit = card[0].upper(), card[1].lower()
    return Card.new(rank + suit)


def hand_rank(cards: list[str]) -> tuple:
    """Упрощённая оценка ровно 5 карт для базовых юнит-тестов
    (например, «пара сильнее старшей карты»).

    Полная оценка 5–7 карт (с учётом стритов, флешей и т.д.) в симуляции
    выполняется через treys.Evaluator — см. run().
    """
    rank_order = {r: i for i, r in enumerate(_RANKS, start=2)}
    card_ranks = sorted([rank_order[c[0].upper()] for c in cards], reverse=True)
    counts = {r: card_ranks.count(r) for r in set(card_ranks)}
    sorted_by_freq = sorted(
        card_ranks, key=lambda r: (counts[r], r), reverse=True
    )

    if max(counts.values()) == 2:
        return (2, sorted_by_freq)
    return (1, sorted_by_freq)


def _recommend(equity: float, pot_size: float, call_amount: float) -> str:
    """Рекомендация на основе pot odds: сравниваем эквити с ценой колла.

    Порог для RAISE взят с запасом (+15 п.п. над pot odds), чтобы не
    рейзить на грани безубыточности.
    """
    if call_amount <= 0:
        return "CALL" if equity >= 0.5 else "FOLD"

    pot_odds = call_amount / (pot_size + call_amount)
    if equity >= pot_odds + 0.15:
        return "RAISE"
    if equity >= pot_odds:
        return "CALL"
    return "FOLD"


def run(params: dict) -> dict:
    """Запускает Монте-Карло симуляцию для текущего состояния раздачи.

    params:
        hole_cards: list[str]  — ровно 2 карты игрока, например ["As", "Ah"]
        community: list[str]   — 0..5 открытых карт стола
        opponents: int         — число противников (1..9)
        simulations: int       — число итераций симуляции
        seed: int | None       — фиксирует случайность для воспроизводимости
        pot_size, call_amount  — для рекомендации RAISE/CALL/FOLD (не обязательны)
    """
    hole_cards = params.get("hole_cards", [])
    community = params.get("community") or []
    opponents = int(params.get("opponents", 1))
    simulations = int(params.get("simulations", 10_000))
    seed = params.get("seed")
    pot_size = float(params.get("pot_size") or 0)
    call_amount = float(params.get("call_amount") or 0)

    hero = [_to_treys(c) for c in hole_cards]
    board_known = [_to_treys(c) for c in community]
    known = set(hero) | set(board_known)

    full_deck = Deck.GetFullDeck()
    remaining = [c for c in full_deck if c not in known]

    rng = random.Random(seed)
    wins = ties = losses = 0

    for _ in range(simulations):
        deck = remaining.copy()
        rng.shuffle(deck)

        board = list(board_known)
        while len(board) < 5:
            board.append(deck.pop())

        best_opponent_score = None
        for _ in range(opponents):
            opp_hand = [deck.pop(), deck.pop()]
            score = _EVALUATOR.evaluate(board, opp_hand)
            if best_opponent_score is None or score < best_opponent_score:
                best_opponent_score = score

        hero_score = _EVALUATOR.evaluate(board, hero)

        if hero_score < best_opponent_score:
            wins += 1
        elif hero_score == best_opponent_score:
            ties += 1
        else:
            losses += 1

    total = wins + ties + losses
    win_probability = wins / total
    tie_probability = ties / total
    loss_probability = losses / total
    equity = win_probability + tie_probability / 2

    return {
        "win_probability": round(win_probability, 4),
        "tie_probability": round(tie_probability, 4),
        "loss_probability": round(loss_probability, 4),
        "equity": round(equity, 4),
        "recommendation": _recommend(equity, pot_size, call_amount),
        "simulations": simulations,
    }
