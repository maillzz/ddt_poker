"""Presentation-only formatting of solver probabilities."""
from django import template

register = template.Library()


@register.filter
def percent(value):
    try:
        return f"{float(value) * 100:.2f}"
    except (ValueError, TypeError):
        return "—"


@register.filter
def recommendation_label(value):
    return {
        "RAISE": "Повысить ставку",
        "CALL": "Уравнять ставку",
        "CHECK": "Пропустить ход",
        "FOLD": "Сбросить карты",
    }.get(value, "—")
