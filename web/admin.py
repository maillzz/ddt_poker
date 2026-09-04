from django.contrib import admin
from web.models import Card, HandAction, HandPlayer, PokerHand, Strategy, Task


class HandPlayerInline(admin.TabularInline):
    model = HandPlayer
    extra = 0


class HandActionInline(admin.TabularInline):
    model = HandAction
    extra = 0


class CardInline(admin.TabularInline):
    model = Card
    extra = 0


@admin.register(PokerHand)
class PokerHandAdmin(admin.ModelAdmin):
    list_display = ("id", "current_street", "pot", "created_at")
    list_filter = ("current_street",)
    inlines = [HandPlayerInline, CardInline, HandActionInline]


@admin.register(HandPlayer)
class HandPlayerAdmin(admin.ModelAdmin):
    list_display = ("id", "hand", "name", "position", "stack", "is_active")
    list_filter = ("position", "is_active")


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("id", "rank", "suit", "hand", "player")
    list_filter = ("suit", "rank")


@admin.register(HandAction)
class HandActionAdmin(admin.ModelAdmin):
    list_display = ("id", "hand", "player", "street", "action_type", "amount", "order")
    list_filter = ("street", "action_type")


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = ("id", "hand", "status", "created_at")
    list_filter = ("status",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status", "created_at")
    list_filter = ("status",)