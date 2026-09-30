# core/schemas.py
"""Граница входных данных: всё, что не прошло эту схему, до core.solver не доходит.

API (Django Ninja) превращает ошибку схемы в 422, форма — в сообщение об ошибке.
"""
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, model_validator

RANKS = "23456789TJQKA"
SUITS = "shdc"  # пики, червы, бубны, трефы


def _normalize_card(card: str) -> str:
    """'as' / 'AS' / 'As' → 'As'. Всё, что не «ранг + масть», — ошибка валидации."""
    if len(card) != 2:
        raise ValueError(f"карта {card!r}: нужно ровно 2 символа — ранг и масть, например 'As'")
    rank, suit = card[0].upper(), card[1].lower()
    if rank not in RANKS:
        raise ValueError(f"карта {card!r}: неизвестный ранг {card[0]!r}, допустимы {RANKS}")
    if suit not in SUITS:
        raise ValueError(f"карта {card!r}: неизвестная масть {card[1]!r}, допустимы {SUITS}")
    return rank + suit


Card = Annotated[str, AfterValidator(_normalize_card)]


class PokerParams(BaseModel):
    hole_cards: list[Card] = Field(min_length=2, max_length=2)
    community: list[Card] = Field(default=[], max_length=5)
    opponents: int = Field(default=1, ge=1, le=9)
    simulations: int = Field(default=10_000, ge=100, le=200_000)
    seed: int | None = Field(default=None)
    # Нужны только для рекомендации RAISE/CALL/CHECK/FOLD (см. core/solver.py:_recommend).
    pot_size: float = Field(default=0.0, ge=0)
    call_amount: float = Field(default=0.0, ge=0)

    @model_validator(mode="after")
    def _no_duplicate_cards(self) -> "PokerParams":
        # Одна колода: карта не может повториться ни в руке, ни на столе, ни между ними.
        seen, duplicates = set(), []
        for card in self.hole_cards + self.community:
            if card in seen:
                duplicates.append(card)
            seen.add(card)
        if duplicates:
            raise ValueError(f"карты повторяются: {', '.join(duplicates)}")
        return self


TaskInParams = PokerParams
