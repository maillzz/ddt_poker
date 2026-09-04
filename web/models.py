from decimal import Decimal
from django.db import models


class PokerHand(models.Model):
    STREET_CHOICES = [
        ("PREFLOP", "Preflop"),
        ("FLOP", "Flop"),
        ("TURN", "Turn"),
        ("RIVER", "River"),
        ("SHOWDOWN", "Showdown"),
    ]

    pot = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Текущий банк",
    )
    current_street = models.CharField(
        max_length=10,
        choices=STREET_CHOICES,
        default="PREFLOP",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Hand #{self.id} ({self.current_street})"


class HandPlayer(models.Model):
    POSITION_CHOICES = [
        ("BTN", "Button"),
        ("SB", "Small Blind"),
        ("BB", "Big Blind"),
        ("UTG", "Under the Gun"),
        ("MP", "Middle Position"),
        ("CO", "Cutoff"),
    ]

    hand = models.ForeignKey(
        PokerHand,
        on_delete=models.CASCADE,
        related_name="players",
    )
    name = models.CharField(max_length=50)
    stack = models.DecimalField(max_digits=10, decimal_places=2)
    position = models.CharField(max_length=5, choices=POSITION_CHOICES)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.position}) - {self.stack}"


class Card(models.Model):
    SUIT_CHOICES = [
        ("s", "Spades"),
        ("h", "Hearts"),
        ("d", "Diamonds"),
        ("c", "Clubs"),
    ]
    RANK_CHOICES = [(r, r) for r in "23456789TJQKA"]

    hand = models.ForeignKey(
        PokerHand,
        on_delete=models.CASCADE,
        related_name="board_cards",
        null=True,
        blank=True,
    )
    player = models.ForeignKey(
        HandPlayer,
        on_delete=models.CASCADE,
        related_name="hole_cards",
        null=True,
        blank=True,
    )
    rank = models.CharField(max_length=1, choices=RANK_CHOICES)
    suit = models.CharField(max_length=1, choices=SUIT_CHOICES)

    def __str__(self):
        return f"{self.rank}{self.suit}"


class HandAction(models.Model):
    ACTION_CHOICES = [
        ("FOLD", "Fold"),
        ("CHECK", "Check"),
        ("CALL", "Call"),
        ("BET", "Bet"),
        ("RAISE", "Raise"),
    ]

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
    street = models.CharField(max_length=10, choices=PokerHand.STREET_CHOICES)
    action_type = models.CharField(max_length=10, choices=ACTION_CHOICES)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.order}: {self.player.name} {self.action_type} {self.amount}"


class Strategy(models.Model):
    hand = models.OneToOneField(
        PokerHand,
        on_delete=models.CASCADE,
        related_name="strategy",
    )
    status = models.CharField(max_length=20, default="PENDING")
    result_file = models.FileField(
        upload_to="strategies/",
        null=True,
        blank=True,
        help_text="Путь к большому JSON/бинарному файлу дерева решений",
    )
    summary_metrics = models.JSONField(
        default=dict,
        blank=True,
        help_text="Легковесные агрегированные метрики для отображения",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Strategy for Hand #{self.hand_id} ({self.status})"


class Task(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("FINISHED", "Finished"),
        ("FAILED", "Failed"),
    ]
    name = models.CharField(max_length=255)
    params = models.JSONField(default=dict)
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default="PENDING",
    )
    result = models.JSONField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Task #{self.id} ({self.name}) - {self.status}"