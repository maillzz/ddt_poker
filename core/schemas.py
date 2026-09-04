# core/schemas.py
from typing import Optional
from pydantic import BaseModel, Field


class PokerParams(BaseModel):
    hole_cards: list[str] = Field(min_length=2, max_length=2)
    community: list[str] = Field(default=[], max_length=5)
    opponents: int = Field(default=1, ge=1, le=9)
    simulations: int = Field(default=10_000, ge=100, le=200_000)
    seed: Optional[int] = Field(default=None)


TaskInParams = PokerParams