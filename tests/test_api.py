import pytest
from django.test import Client


@pytest.mark.django_db
def test_create_poker_task_returns_202():
    """POST валидной покерной задачи возвращает 202 и id."""
    client = Client()
    payload = {
        "name": "AA против одного",
        "params": {
            "hole_cards": ["As", "Ah"],
            "opponents": 1,
            "simulations": 10000,
            "seed": 1,
        },
    }
    r = client.post(
        "/api/tasks",
        data=payload,
        content_type="application/json",
    )
    assert r.status_code == 202
    assert "id" in r.json()


@pytest.mark.django_db
def test_poker_api_validation_error():
    """POST с некорректным значением opponents (0 при ge=1) возвращает 422."""
    client = Client()
    payload = {
        "name": "Ошибка валидации",
        "params": {
            "hole_cards": ["As", "Ah"],
            "opponents": 0,
            "simulations": 10000,
        },
    }
    r = client.post(
        "/api/tasks",
        data=payload,
        content_type="application/json",
    )
    assert r.status_code == 422