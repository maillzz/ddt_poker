from pydantic import BaseModel, Field


class PokerParams(BaseModel):
    hole_cards: list[str] = Field(
        description="Две закрытые карты игрока, например ['As', 'Kh']"
    )
    community_cards: list[str] = Field(
        default_factory=list,
        description="Открытые карты стола, от 0 до 5 карт"
    )
    opponents: int = Field(
        default=1,
        ge=1,
        le=9,
        description="Количество противников"
    )
    pot: float = Field(
        default=0,
        ge=0,
        description="Размер текущего банка"
    )
    call_amount: float = Field(
        default=0,
        ge=0,
        description="Размер ставки для колла"
    )
    simulations: int = Field(
        default=10_000,
        ge=100,
        le=1_000_000,
        description="Количество симуляций"
    )


class PokerResult(BaseModel):
    win_probability: float
    tie_probability: float
    loss_probability: float
    ev: float
    recommendation: str
    simulations: int
    core_version: str