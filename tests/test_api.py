import threading
import time

import pytest

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


def test_create_poker_task_returns_202_and_finishes(client):
    """POST возвращает 202 и id, задача существует и в фоне доходит до FINISHED."""
    r = post_task(client)
    assert r.status_code == 202
    task_id = r.json()["id"]

    r = client.get(f"/api/tasks/{task_id}")
    assert r.status_code == 200
    assert r.json()["status"] in ("PENDING", "RUNNING", "FINISHED")

    wait_status(client, task_id, "FINISHED")


def test_post_does_not_wait_for_calculation(client, monkeypatch):
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

    r = post_task(client)  # вернулся, хотя solver ещё заблокирован
    assert r.status_code == 202
    task_id = r.json()["id"]

    wait_status(client, task_id, "RUNNING")
    release.set()
    wait_status(client, task_id, "FINISHED")

    # расчёт шёл не в потоке запроса
    assert calc_threads and calc_threads[0] is not threading.main_thread()


def test_background_error_marks_task_failed(client, monkeypatch):
    """Исключение в фоновом расчёте переводит задачу в FAILED, а не оставляет RUNNING."""

    def broken_solver(params):
        raise ValueError("сломалось ядро")

    monkeypatch.setattr("web.services.solve_poker", broken_solver)

    task_id = post_task(client).json()["id"]
    wait_status(client, task_id, "FAILED")


def test_get_missing_task_returns_404(client):
    """GET несуществующей задачи возвращает 404, а не 500."""
    r = client.get("/api/tasks/999")
    assert r.status_code == 404
    assert r.json() == {"detail": "задача не найдена"}


def test_poker_api_validation_error(client):
    """POST с некорректным значением opponents (0 при ge=1) возвращает 422."""
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


# --- Граница схемы: плохие входы отклоняются с 422 ДО расчёта ------------------

VALID_PARAMS = {"hole_cards": ["As", "Kh"], "opponents": 1, "simulations": 1000, "seed": 1}
MISSING = object()  # маркер «поле не передано вовсе»

BAD_INPUTS = [
    # пустое значение
    pytest.param({"hole_cards": ""}, id="empty-string"),
    pytest.param({"hole_cards": []}, id="empty-list"),
    pytest.param({"hole_cards": ["", ""]}, id="empty-card"),
    pytest.param({"hole_cards": MISSING}, id="missing-hole_cards"),
    # повтор карты
    pytest.param({"hole_cards": ["As", "As"]}, id="duplicate-As-As"),
    pytest.param({"hole_cards": ["As", "as"]}, id="duplicate-other-case"),
    pytest.param({"community": ["As", "7c", "2d"]}, id="duplicate-hand-and-board"),
    pytest.param({"community": ["7c", "7c", "2d"]}, id="duplicate-on-board"),
    # недопустимая карта
    pytest.param({"hole_cards": ["As", "Zz"]}, id="card-Zz"),
    pytest.param({"hole_cards": ["As", "Zs"]}, id="bad-rank"),
    pytest.param({"hole_cards": ["As", "Kx"]}, id="bad-suit"),
    pytest.param({"hole_cards": ["As", "10h"]}, id="card-3-chars"),
    pytest.param({"hole_cards": ["As", "K"]}, id="card-1-char"),
    # огромное значение
    pytest.param({"simulations": 200_001}, id="simulations-over-max"),
    pytest.param({"simulations": 10**12}, id="simulations-huge"),
    pytest.param({"opponents": 10}, id="opponents-over-max"),
    pytest.param({"hole_cards": ["As", "Kh", "Qd"]}, id="three-hole-cards"),
    pytest.param({"community": ["2c", "3c", "4c", "5c", "6c", "7c"]}, id="six-board-cards"),
    # отрицательное / ниже минимума
    pytest.param({"simulations": -1}, id="simulations-negative"),
    pytest.param({"simulations": 99}, id="simulations-under-min"),
    pytest.param({"opponents": -1}, id="opponents-negative"),
    pytest.param({"opponents": 0}, id="opponents-zero"),
    pytest.param({"pot_size": -1}, id="pot_size-negative"),
    pytest.param({"call_amount": -5}, id="call_amount-negative"),
    # неправильный тип
    pytest.param({"simulations": "abc"}, id="letters-instead-of-number"),
    pytest.param({"simulations": 1.5}, id="fraction-instead-of-int"),
    pytest.param({"hole_cards": 123}, id="number-instead-of-list"),
    pytest.param({"hole_cards": "As Kh"}, id="string-instead-of-list"),
    pytest.param({"hole_cards": [1, 2]}, id="number-instead-of-card"),
    pytest.param({"opponents": [1]}, id="list-instead-of-number"),
    pytest.param({"seed": "x"}, id="seed-letters"),
]


def post_params(client, overrides):
    params = dict(VALID_PARAMS)
    for key, value in overrides.items():
        if value is MISSING:
            params.pop(key)
        else:
            params[key] = value
    return client.post(
        "/api/tasks", data={"name": "граница", "params": params}, content_type="application/json"
    )


@pytest.mark.parametrize("overrides", BAD_INPUTS)
def test_bad_input_rejected_with_422_before_calculation(client, overrides, monkeypatch):
    """Плохой вход → 422 от схемы; задача не создаётся, ядро не вызывается."""
    from web.models import Task

    def solver_must_not_run(params):
        raise AssertionError("расчёт запущен для невалидного входа")

    monkeypatch.setattr("web.services.solve_poker", solver_must_not_run)

    r = post_params(client, overrides)
    assert r.status_code == 422, r.content
    assert Task.objects.count() == 0


def test_missing_params_rejected_with_422(client):
    """Тело без params (обязательное поле) → 422, а не 500."""
    r = client.post("/api/tasks", data={"name": "без params"}, content_type="application/json")
    assert r.status_code == 422


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"simulations": 100}, id="simulations-min"),
        pytest.param({"simulations": 10_000}, id="simulations-10k"),
        pytest.param({"simulations": 100_000}, id="simulations-100k"),
        pytest.param({"simulations": 200_000}, id="simulations-max"),
        pytest.param({"opponents": 9, "simulations": 200_000}, id="opponents-max-simulations-max"),
        pytest.param({"community": ["7c", "5d", "2h", "Jc", "9s"]}, id="full-board"),
        pytest.param({"seed": -1}, id="seed-negative-allowed"),
    ],
)
def test_boundary_values_accepted(client, overrides, monkeypatch):
    """Граничные значения проходят схему. Ядро подменено быстрым — тяжёлого расчёта нет."""
    from web.models import Task

    monkeypatch.setattr("web.services.solve_poker", lambda params: {"equity": 0.5})

    r = post_params(client, overrides)
    assert r.status_code == 202, r.content
    task_id = r.json()["id"]
    wait_status(client, task_id, "FINISHED")  # дождаться потока до очистки БД
    stored = Task.objects.get(pk=task_id).params
    for key, value in overrides.items():
        assert stored[key] == value


def test_cards_normalized_to_canonical_case(client, monkeypatch):
    """'as kH' принимается и сохраняется как 'As', 'Kh' — в ядро идёт единый формат."""
    from web.models import Task

    monkeypatch.setattr("web.services.solve_poker", lambda params: {"equity": 0.5})

    r = post_params(client, {"hole_cards": ["as", "kH"]})
    assert r.status_code == 202
    wait_status(client, r.json()["id"], "FINISHED")
    assert Task.objects.get(pk=r.json()["id"]).params["hole_cards"] == ["As", "Kh"]


# --- GET /api/tasks/{id}/result ------------------------------------------------
# Задачи создаются сервисом напрямую, без расчёта: статус выставляем сами.

RESULT = {"win_probability": 0.85, "equity": 0.86, "recommendation": "RAISE"}


def make_task(owner, status, result=None):
    from web import services

    task = services.create_task("результат", {}, owner=owner)
    task.status, task.result = status, result
    task.save()
    return task


def test_result_of_own_finished_task_returns_200(client, user):
    task = make_task(user, "FINISHED", RESULT)
    r = client.get(f"/api/tasks/{task.pk}/result")
    assert r.status_code == 200
    assert r.json() == RESULT


def test_result_of_other_users_task_returns_404(client, django_user_model):
    other = django_user_model.objects.create_user(username="user2", password="test12345")
    task = make_task(other, "FINISHED", RESULT)
    r = client.get(f"/api/tasks/{task.pk}/result")
    assert r.status_code == 404
    assert r.json() == {"detail": "задача не найдена"}


def test_result_of_missing_task_returns_404(client):
    assert client.get("/api/tasks/999/result").status_code == 404


@pytest.mark.parametrize("status", ["PENDING", "RUNNING"])
def test_result_of_unfinished_task_returns_409(client, user, status):
    task = make_task(user, status)
    r = client.get(f"/api/tasks/{task.pk}/result")
    assert r.status_code == 409
    assert r.json() == {"detail": f"ещё не готова: {status}"}


def test_result_after_real_calculation(client):
    """Сквозной путь: POST → расчёт в фоне → FINISHED → /result отдаёт результат ядра."""
    task_id = post_task(client).json()["id"]
    wait_status(client, task_id, "FINISHED")
    r = client.get(f"/api/tasks/{task_id}/result")
    assert r.status_code == 200
    assert set(r.json()) >= {"win_probability", "equity", "recommendation"}
