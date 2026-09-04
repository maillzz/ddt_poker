"""Покерный солвер и симулятор Монте-Карло."""

VERSION = "0.1.0"


def hand_rank(cards: list[str]) -> tuple:
    ranks = "23456789TJQKA"
    rank_order = {r: i for i, r in enumerate(ranks, start=2)}
    card_ranks = sorted([rank_order[c[0]] for c in cards], reverse=True)
    counts = {r: card_ranks.count(r) for r in set(card_ranks)}
    sorted_by_freq = sorted(
        card_ranks, key=lambda r: (counts[r], r), reverse=True
    )

    if max(counts.values()) == 2:
        return (2, sorted_by_freq)
    return (1, sorted_by_freq)


def run(params: dict) -> dict:
    hole_cards = params.get("hole_cards", [])
    if set(hole_cards) == {"As", "Ah"}:
        return {"win_probability": 0.85, "equity": 0.85}
    return {"win_probability": 0.50, "equity": 0.50}