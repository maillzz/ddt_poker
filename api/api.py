"""
REST API покерного приложения на Django Ninja.

Основные ресурсы:
- PokerHand
- HandPlayer
- Card
- HandAction
- SimulationRequest
- SimulationResult
- Recommendation
"""

from typing import Any

from django.shortcuts import get_object_or_404
from ninja import NinjaAPI, Schema
from ninja.responses import Status

from web import services
from web.models import (
    Card,
    HandAction,
    HandPlayer,
    PokerHand,
    Recommendation,
    SimulationRequest,
    SimulationResult,
    Strategy,
)


api = NinjaAPI(
    title="Poker Strategy API",
    version="1.0",
    description="API для покерных раздач, симуляций и рекомендаций",
)


class HandIn(Schema):
    players_count: int
    pot_size: float = 0
    call_amount: float = 0


class HandOut(Schema):
    id: int
    stage: str
    players_count: int
    pot_size: float
    call_amount: float


class PlayerIn(Schema):
    player_number: int
    is_hero: bool = False
    stack: float | None = None


class PlayerOut(Schema):
    id: int
    player_number: int
    is_hero: bool
    stack: float | None
    status: str


class CardIn(Schema):
    card_code: str
    location: str
    player_id: int | None = None


class CardOut(Schema):
    id: int
    card_code: str
    location: str
    player_id: int | None


class ActionIn(Schema):
    player_id: int
    action_type: str
    amount: float = 0
    street: str


class ActionOut(Schema):
    id: int
    player_id: int
    action_type: str
    amount: float
    street: str


class SimulationIn(Schema):
    strategy_id: int | None = None
    simulation_count: int = 10000


class SimulationOut(Schema):
    id: int
    hand_id: int
    strategy_id: int | None
    simulation_count: int
    status: str


class ResultOut(Schema):
    id: int
    simulation_id: int
    iterations: int
    wins: int
    ties: int
    losses: int
    win_probability: float
    tie_probability: float
    loss_probability: float
    expected_value: float | None


class RecommendationOut(Schema):
    id: int
    simulation_id: int
    action: str
    expected_value: float | None
    win_probability: float | None
    tie_probability: float | None
    loss_probability: float | None
    confidence: float | None
    reason: str


class ErrorOut(Schema):
    detail: str


@api.post(
    "/hands",
    response={201: HandOut, 401: ErrorOut},
    summary="Создать покерную раздачу",
)
def create_hand(request, payload: HandIn):
    if not request.user.is_authenticated:
        return Status(401, {"detail": "Authentication required"})

    hand = services.create_hand(
        owner=request.user,
        players_count=payload.players_count,
        pot_size=payload.pot_size,
        call_amount=payload.call_amount,
    )

    return Status(201, hand)


@api.get(
    "/hands",
    response=list[HandOut],
    summary="Список покерных раздач",
)
def list_hands(request):
    qs = PokerHand.objects.all()

    if request.user.is_authenticated:
        qs = qs.filter(owner=request.user)

    return qs[:100]


@api.get(
    "/hands/{hand_id}",
    response=HandOut,
    summary="Получить покерную раздачу",
)
def get_hand(request, hand_id: int):
    return get_object_or_404(PokerHand, pk=hand_id)


@api.post(
    "/hands/{hand_id}/players",
    response={201: PlayerOut, 404: ErrorOut},
    summary="Добавить игрока",
)
def create_player(request, hand_id: int, payload: PlayerIn):
    hand = get_object_or_404(PokerHand, pk=hand_id)

    player = services.add_player(
        hand=hand,
        player_number=payload.player_number,
        is_hero=payload.is_hero,
        stack=payload.stack,
    )

    return Status(201, player)


@api.get(
    "/hands/{hand_id}/players",
    response=list[PlayerOut],
    summary="Получить игроков раздачи",
)
def list_players(request, hand_id: int):
    hand = get_object_or_404(PokerHand, pk=hand_id)
    return hand.players.all()


@api.post(
    "/hands/{hand_id}/cards",
    response={201: CardOut, 404: ErrorOut},
    summary="Добавить карту",
)
def create_card(request, hand_id: int, payload: CardIn):
    hand = get_object_or_404(PokerHand, pk=hand_id)

    player = None
    if payload.player_id is not None:
        player = get_object_or_404(
            HandPlayer,
            pk=payload.player_id,
            hand=hand,
        )

    card = services.add_card(
        hand=hand,
        card_code=payload.card_code,
        location=payload.location,
        player=player,
    )

    return Status(201, card)


@api.get(
    "/hands/{hand_id}/cards",
    response=list[CardOut],
    summary="Получить карты раздачи",
)
def list_cards(request, hand_id: int):
    hand = get_object_or_404(PokerHand, pk=hand_id)
    return hand.cards.all()


@api.post(
    "/hands/{hand_id}/actions",
    response={201: ActionOut, 404: ErrorOut},
    summary="Добавить действие игрока",
)
def create_action(request, hand_id: int, payload: ActionIn):
    hand = get_object_or_404(PokerHand, pk=hand_id)

    player = get_object_or_404(
        HandPlayer,
        pk=payload.player_id,
        hand=hand,
    )

    action = services.add_action(
        hand=hand,
        player=player,
        action_type=payload.action_type,
        amount=payload.amount,
        street=payload.street,
    )

    return Status(201, action)


@api.get(
    "/hands/{hand_id}/actions",
    response=list[ActionOut],
    summary="Получить действия раздачи",
)
def list_actions(request, hand_id: int):
    hand = get_object_or_404(PokerHand, pk=hand_id)
    return hand.actions.all()


@api.post(
    "/hands/{hand_id}/simulations",
    response={202: SimulationOut, 404: ErrorOut},
    summary="Создать симуляцию",
)
def create_simulation(request, hand_id: int, payload: SimulationIn):
    hand = get_object_or_404(PokerHand, pk=hand_id)

    strategy = None
    if payload.strategy_id is not None:
        strategy = get_object_or_404(
            Strategy,
            pk=payload.strategy_id,
        )

    simulation = services.create_simulation(
        hand=hand,
        strategy=strategy,
        simulation_count=payload.simulation_count,
    )

    return Status(202, simulation)


@api.get(
    "/simulations/{simulation_id}",
    response=SimulationOut,
    summary="Статус симуляции",
)
def get_simulation(request, simulation_id: int):
    return get_object_or_404(
        SimulationRequest,
        pk=simulation_id,
    )


@api.get(
    "/simulations/{simulation_id}/result",
    response={200: ResultOut, 409: ErrorOut},
    summary="Получить результат симуляции",
)
def get_simulation_result(request, simulation_id: int):
    simulation = get_object_or_404(
        SimulationRequest,
        pk=simulation_id,
    )

    if simulation.status != SimulationRequest.Status.COMPLETED:
        return Status(
            409,
            {
                "detail": (
                    "Симуляция ещё не завершена: "
                    f"статус {simulation.status}"
                )
            },
        )

    result = get_object_or_404(
        SimulationResult,
        simulation=simulation,
    )

    return Status(200, result)


@api.get(
    "/simulations/{simulation_id}/recommendation",
    response={200: RecommendationOut, 409: ErrorOut},
    summary="Получить покерную рекомендацию",
)
def get_recommendation(request, simulation_id: int):
    simulation = get_object_or_404(
        SimulationRequest,
        pk=simulation_id,
    )

    if simulation.status != SimulationRequest.Status.COMPLETED:
        return Status(
            409,
            {
                "detail": (
                    "Рекомендация ещё недоступна: "
                    f"статус {simulation.status}"
                )
            },
        )

    recommendation = get_object_or_404(
        Recommendation,
        simulation=simulation,
    )

    return Status(200, recommendation)