# tests/test_scenario.py
import pytest
from django.test import Client


@pytest.mark.django_db
def test_poker_web_flow():
    """Проверка доступности главной страницы веб-интерфейса покера."""
    client = Client()
    response = client.get("/")
    # Проверяем, что эндпоинт отдает успешный ответ
    assert response.status_code in (200, 302)