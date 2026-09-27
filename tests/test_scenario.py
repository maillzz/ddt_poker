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


@pytest.mark.django_db
def test_full_scenario_form_to_result():
    """Сквозной сценарий: форма → расчёт ядром → результат на странице задачи.

    Эталон известен заранее: каре тузов на столе — гарантированная ничья
    (см. core/tests/test_solver.py::test_quads_on_board_is_always_a_tie).
    """
    client = Client()

    response = client.post(
        "/tasks/new/",
        data={
            "hole_cards": "2s 3s",
            "community": "Ah Ad As Ac Kh",
            "opponents": 1,
            "simulations": 2000,
            "seed": 42,
            "pot_size": 0,
            "call_amount": 0,
        },
    )
    # Успешный POST редиректит на страницу созданной задачи
    assert response.status_code == 302

    detail = client.get(response["Location"])
    assert detail.status_code == 200

    task = detail.context["task"]
    assert task.status == "FINISHED"
    assert task.result["tie_probability"] == 1.0
    assert task.result["win_probability"] == 0.0