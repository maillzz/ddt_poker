from django.contrib import admin

from .models import (
    Card,
    HandAction,
    HandPlayer,
    PokerHand,
    Recommendation,
    SimulationRequest,
    SimulationResult,
    Strategy,
)


@admin.register(PokerHand)
class PokerHandAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "owner",
        "stage",
        "players_count",
        "pot_size",
        "call_amount",
        "created_at",
    )
    list_filter = ("stage",)
    search_fields = ("owner__username", "owner__email")


@admin.register(HandPlayer)
class HandPlayerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "hand",
        "player_number",
        "is_hero",
        "stack",
        "status",
    )
    list_filter = ("status", "is_hero")


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "hand",
        "player",
        "card_code",
        "location",
    )
    list_filter = ("location",)
    search_fields = ("card_code",)


@admin.register(HandAction)
class HandActionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "hand",
        "player",
        "action_type",
        "amount",
        "street",
        "created_at",
    )
    list_filter = ("action_type", "street")


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "fold_threshold",
        "call_threshold",
        "raise_threshold",
    )
    search_fields = ("name",)


@admin.register(SimulationRequest)
class SimulationRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "hand",
        "strategy",
        "simulation_count",
        "status",
        "created_at",
        "completed_at",
    )
    list_filter = ("status", "strategy")


@admin.register(SimulationResult)
class SimulationResultAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "simulation",
        "iterations",
        "wins",
        "ties",
        "losses",
        "expected_value",
    )


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "simulation",
        "action",
        "expected_value",
        "confidence",
        "created_at",
    )
    list_filter = ("action",)