import pytest
from django.test import Client


@pytest.mark.django_db
def test_create_poker_task_returns_202_and_finishes():
    """POST валидной покерной задачи возвращает 202 и id, задача реально посчитана."""
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
    task_id = r.json()["id"]

    # Расчёт идёт синхронно в запросе — задача уже должна быть посчитана
    r = client.get(f"/api/tasks/{task_id}")
    assert r.status_code == 200
    assert r.json() == {"id": task_id, "status": "FINISHED"}


@pytest.mark.django_db
def test_get_missing_task_returns_404():
    """GET несуществующей задачи возвращает 404, а не 500."""
    client = Client()
    r = client.get("/api/tasks/999")
    assert r.status_code == 404
    assert r.json() == {"detail": "задача не найдена"}


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