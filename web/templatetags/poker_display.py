"""Presentation-only formatting of solver probabilities."""
from django import template

register = template.Library()


@register.filter
def percent(value):
    try:
        return f"{float(value) * 100:.1f}"
    except (ValueError, TypeError):
        return "—"
