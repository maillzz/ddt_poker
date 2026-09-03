"""
Сервисный слой покерного приложения.

Views/API работают с прикладной логикой через этот слой,
а не создают и не изменяют покерные сущности напрямую.
"""

from django.db import transaction
from django.utils import timezone

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


@transaction.atomic
def create_hand(
    *,
    owner,
    players_count: int,
    pot_size=0,
    call_amount=0,
) -> PokerHand:
    """Создаёт новую покерную раздачу."""
    hand = PokerHand.objects.create(
        owner=owner,
        players_count=players_count,
        pot_size=pot_size,
        call_amount=call_amount,
    )

    return hand


@transaction.atomic
def add_player(
    *,
    hand: PokerHand,
    player_number: int,
    is_hero: bool = False,
    stack=None,
) -> HandPlayer:
    """Добавляет игрока в раздачу."""
    return HandPlayer.objects.create(
        hand=hand,
        player_number=player_number,
        is_hero=is_hero,
        stack=stack,
    )


@transaction.atomic
def add_card(
    *,
    hand: PokerHand,
    card_code: str,
    location: str,
    player: HandPlayer | None = None,
) -> Card:
    """Добавляет карту в раздачу."""
    return Card.objects.create(
        hand=hand,
        player=player,
        card_code=card_code,
        location=location,
    )


@transaction.atomic
def add_action(
    *,
    hand: PokerHand,
    player: HandPlayer,
    action_type: str,
    amount=0,
    street: str,
) -> HandAction:
    """Добавляет действие игрока."""
    return HandAction.objects.create(
        hand=hand,
        player=player,
        action_type=action_type,
        amount=amount,
        street=street,
    )


@transaction.atomic
def create_simulation(
    *,
    hand: PokerHand,
    strategy: Strategy | None = None,
    simulation_count: int = 10000,
) -> SimulationRequest:
    """Создаёт запрос на симуляцию."""
    return SimulationRequest.objects.create(
        hand=hand,
        strategy=strategy,
        simulation_count=simulation_count,
    )


def execute_simulation(simulation_id: int) -> SimulationRequest:
    """
    Выполняет симуляцию.

    На данном этапе это граница между Django и покерным
    вычислительным ядром. Реальную Monte Carlo-логику
    подключим следующим этапом.
    """
    simulation = SimulationRequest.objects.select_related(
        "hand",
        "strategy",
    ).get(pk=simulation_id)

    simulation.status = SimulationRequest.Status.RUNNING
    simulation.started_at = timezone.now()
    simulation.save(update_fields=["status", "started_at"])

    try:
        # TODO: подключить настоящее покерное ядро симуляции.
        #
        # Здесь должны появиться:
        # - расчёт wins / ties / losses;
        # - win_probability / tie_probability / loss_probability;
        # - expected_value;
        # - Recommendation.

        raise NotImplementedError(
            "Покерное вычислительное ядро ещё не подключено."
        )

    except Exception:
        simulation.status = SimulationRequest.Status.FAILED
        simulation.completed_at = timezone.now()
        simulation.save(update_fields=["status", "completed_at"])
        raise