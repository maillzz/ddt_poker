from decimal import Decimal

from django.conf import settings
from django.db import models


class PokerHand(models.Model):
    class Stage(models.TextChoices):
        PREFLOP = "PREFLOP", "Preflop"
        FLOP = "FLOP", "Flop"
        TURN = "TURN", "Turn"
        RIVER = "RIVER", "River"
        FINISHED = "FINISHED", "Finished"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="poker_hands",
    )
    stage = models.CharField(max_length=10, choices=Stage.choices, default=Stage.PREFLOP)
    players_count = models.PositiveSmallIntegerField()
    pot_size = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    call_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Hand #{self.pk} ({self.stage})"


class HandPlayer(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        FOLDED = "FOLDED", "Folded"
        ALL_IN = "ALL_IN", "All-in"
        WINNER = "WINNER", "Winner"
        LOSER = "LOSER", "Loser"

    hand = models.ForeignKey(
        PokerHand,
        on_delete=models.CASCADE,
        related_name="players",
    )
    player_number = models.PositiveSmallIntegerField()
    is_hero = models.BooleanField(default=False)
    stack = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["hand", "player_number"],
                name="unique_player_number_per_hand",
            ),
            models.UniqueConstraint(
                fields=["hand"],
                condition=models.Q(is_hero=True),
                name="one_hero_per_hand",
            ),
        ]
        ordering = ["player_number"]

    def __str__(self):
        return f"Player {self.player_number} in hand #{self.hand_id}"


class Card(models.Model):
    class Location(models.TextChoices):
        HOLE = "HOLE", "Hole"
        FLOP = "FLOP", "Flop"
        TURN = "TURN", "Turn"
        RIVER = "RIVER", "River"

    hand = models.ForeignKey(
        PokerHand,
        on_delete=models.CASCADE,
        related_name="cards",
    )
    player = models.ForeignKey(
        HandPlayer,
        on_delete=models.CASCADE,
        related_name="cards",
        null=True,
        blank=True,
    )
    card_code = models.CharField(max_length=2)
    location = models.CharField(max_length=6, choices=Location.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["hand", "card_code"],
                name="unique_card_per_hand",
            ),
        ]

    def __str__(self):
        return f"{self.card_code} ({self.location})"


class HandAction(models.Model):
    class ActionType(models.TextChoices):
        FOLD = "FOLD", "Fold"
        CHECK = "CHECK", "Check"
        CALL = "CALL", "Call"
        BET = "BET", "Bet"
        RAISE = "RAISE", "Raise"
        ALL_IN = "ALL_IN", "All-in"

    class Street(models.TextChoices):
        PREFLOP = "PREFLOP", "Preflop"
        FLOP = "FLOP", "Flop"
        TURN = "TURN", "Turn"
        RIVER = "RIVER", "River"

    hand = models.ForeignKey(
        PokerHand,
        on_delete=models.CASCADE,
        related_name="actions",
    )
    player = models.ForeignKey(
        HandPlayer,
        on_delete=models.CASCADE,
        related_name="actions",
    )
    action_type = models.CharField(max_length=10, choices=ActionType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    street = models.CharField(max_length=10, choices=Street.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.player} — {self.action_type} {self.amount}"


class Strategy(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    fold_threshold = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal("0"))
    call_threshold = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal("0"))
    raise_threshold = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal("0"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SimulationRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    hand = models.ForeignKey(
        PokerHand,
        on_delete=models.CASCADE,
        related_name="simulations",
    )
    strategy = models.ForeignKey(
        Strategy,
        on_delete=models.SET_NULL,
        related_name="simulation_requests",
        null=True,
        blank=True,
    )
    simulation_count = models.PositiveIntegerField(default=10000)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Simulation #{self.pk} for hand #{self.hand_id}"


class SimulationResult(models.Model):
    simulation = models.OneToOneField(
        SimulationRequest,
        on_delete=models.CASCADE,
        related_name="result",
    )
    iterations = models.PositiveIntegerField()

    wins = models.PositiveIntegerField(default=0)
    ties = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)

    win_probability = models.DecimalField(max_digits=8, decimal_places=6)
    tie_probability = models.DecimalField(max_digits=8, decimal_places=6)
    loss_probability = models.DecimalField(max_digits=8, decimal_places=6)

    expected_value = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Result for simulation #{self.simulation_id}"


class Recommendation(models.Model):
    class Action(models.TextChoices):
        FOLD = "FOLD", "Fold"
        CALL = "CALL", "Call"
        RAISE = "RAISE", "Raise"

    simulation = models.OneToOneField(
        SimulationRequest,
        on_delete=models.CASCADE,
        related_name="recommendation",
    )
    action = models.CharField(max_length=5, choices=Action.choices)
    expected_value = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    win_probability = models.DecimalField(max_digits=8, decimal_places=6, null=True, blank=True)
    tie_probability = models.DecimalField(max_digits=8, decimal_places=6, null=True, blank=True)
    loss_probability = models.DecimalField(max_digits=8, decimal_places=6, null=True, blank=True)
    confidence = models.DecimalField(max_digits=8, decimal_places=6, null=True, blank=True)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} for simulation #{self.simulation_id}"
