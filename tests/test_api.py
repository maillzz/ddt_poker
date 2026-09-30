import threading
import time

import pytest
from django.test import Client

# Расчёт идёт в фоновом потоке со своим соединением к БД, поэтому тестам нужна
# реальная фиксация транзакций (transaction=True): иначе поток не увидит задачу.
pytestmark = pytest.mark.django_db(transaction=True)

PAYLOAD = {
    "name": "AA против одного",
    "params": {
        "hole_cards": ["As", "Ah"],
        "opponents": 1,
        "simulations": 1000,
        "seed": 1,
    },
}


def post_task(client):
    return client.post("/api/tasks", data=PAYLOAD, content_type="application/json")


def wait_status(client, task_id, expected, timeout=10.0):
    """Опрашивает GET /api/tasks/{id}, как это делает detail.html, пока не придёт expected."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = client.get(f"/api/tasks/{task_id}").json()["status"]
        if status == expected:
            return status
        time.sleep(0.02)
    raise AssertionError(f"задача {task_id}: ждали {expected}, последний статус {status}")


def test_create_poker_task_returns_202_and_finishes():
    """POST возвращает 202 и id, задача существует и в фоне доходит до FINISHED."""
    client = Client()
    r = post_task(client)
    assert r.status_code == 202
    task_id = r.json()["id"]

    r = client.get(f"/api/tasks/{task_id}")
    assert r.status_code == 200
    assert r.json()["status"] in ("PENDING", "RUNNING", "FINISHED")

    wait_status(client, task_id, "FINISHED")


def test_post_does_not_wait_for_calculation(monkeypatch):
    """POST отвечает, пока расчёт ещё идёт: видим RUNNING, затем FINISHED.

    Ядро подменено функцией, которая ждёт сигнала, — так статус RUNNING
    держится ровно столько, сколько нужно тесту, без привязки ко времени.
    """
    release = threading.Event()
    calc_threads = []

    def slow_solver(params):
        calc_threads.append(threading.current_thread())
        assert release.wait(timeout=10)
        return {"equity": 0.85, "recommendation": "RAISE"}

    monkeypatch.setattr("web.services.solve_poker", slow_solver)
    client = Client()

    r = post_task(client)  # вернулся, хотя solver ещё заблокирован
    assert r.status_code == 202
    task_id = r.json()["id"]

    wait_status(client, task_id, "RUNNING")
    release.set()
    wait_status(client, task_id, "FINISHED")

    # расчёт шёл не в потоке запроса
    assert calc_threads and calc_threads[0] is not threading.main_thread()


def test_background_error_marks_task_failed(monkeypatch):
    """Исключение в фоновом расчёте переводит задачу в FAILED, а не оставляет RUNNING."""

    def broken_solver(params):
        raise ValueError("сломалось ядро")

    monkeypatch.setattr("web.services.solve_poker", broken_solver)
    client = Client()

    task_id = post_task(client).json()["id"]
    wait_status(client, task_id, "FAILED")


def test_get_missing_task_returns_404():
    """GET несуществующей задачи возвращает 404, а не 500."""
    client = Client()
    r = client.get("/api/tasks/999")
    assert r.status_code == 404
    assert r.json() == {"detail": "задача не найдена"}


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
