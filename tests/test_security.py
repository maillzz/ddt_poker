"""Безопасность: вход, изоляция задач по владельцу, CSRF, лимиты, SECRET_KEY.

Здесь django_db без transaction=True: transaction.on_commit не срабатывает,
фоновый расчёт не стартует — тесты проверяют только границу доступа.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.test import Client

from web import services
from web.models import Task

pytestmark = pytest.mark.django_db

PAYLOAD = {"name": "AA", "params": {"hole_cards": ["As", "Ah"], "simulations": 100}}


def post_json(client, data=PAYLOAD, **extra):
    return client.post("/api/tasks", data=data, content_type="application/json", **extra)


# --- аноним --------------------------------------------------------------------

def test_anonymous_create_task_returns_401():
    # enforce_csrf_checks — как настоящий клиент: аноним получает 401, а не 403 за CSRF
    r = post_json(Client(enforce_csrf_checks=True))
    assert r.status_code == 401
    assert Task.objects.count() == 0


@pytest.mark.parametrize("suffix", ["", "/result"])
def test_anonymous_get_task_returns_401(user, suffix):
    task = services.create_task("чужая", {}, owner=user)
    r = Client().get(f"/api/tasks/{task.pk}{suffix}")
    assert r.status_code == 401


@pytest.mark.parametrize("url", ["/", "/tasks/new/", "/tasks/1/"])
def test_anonymous_pages_redirect_to_login(url):
    r = Client().get(url)
    assert r.status_code == 302
    assert r["Location"] == f"/accounts/login/?next={url}"


def test_login_page_opens():
    assert Client().get("/accounts/login/").status_code == 200


# --- изоляция: пользователь 2 не видит задачу пользователя 1 ---------------------

@pytest.fixture
def other_client(django_user_model):
    other = django_user_model.objects.create_user(username="user2", password="test12345")
    c = Client()
    c.force_login(other)
    return c


def test_user2_gets_404_on_user1_task_page(user, other_client):
    task = services.create_task("задача user1", {}, owner=user)
    assert other_client.get(f"/tasks/{task.pk}/").status_code == 404


def test_user2_gets_404_on_user1_task_api(user, other_client):
    task = services.create_task("задача user1", {}, owner=user)
    r = other_client.get(f"/api/tasks/{task.pk}")
    assert r.status_code == 404
    assert r.json() == {"detail": "задача не найдена"}  # не отличить от несуществующей


def test_user2_list_has_no_user1_tasks(user, other_client):
    services.create_task("задача user1", {}, owner=user)
    r = other_client.get("/")
    assert r.status_code == 200
    assert list(r.context["tasks"]) == []


def test_owner_sees_own_task(client, user):
    task = services.create_task("моя", {}, owner=user)
    assert client.get(f"/tasks/{task.pk}/").status_code == 200
    assert client.get(f"/api/tasks/{task.pk}").json()["id"] == task.pk


def test_api_sets_owner_to_current_user(client, user):
    r = post_json(client)
    assert r.status_code == 202
    assert Task.objects.get(pk=r.json()["id"]).owner == user


# --- лимиты входа --------------------------------------------------------------

def test_name_1000_chars_returns_422(client):
    r = post_json(client, {**PAYLOAD, "name": "x" * 1000})
    assert r.status_code == 422
    assert Task.objects.count() == 0


def test_name_255_chars_accepted(client):
    assert post_json(client, {**PAYLOAD, "name": "x" * 255}).status_code == 202


@pytest.mark.parametrize("field", ["pot_size", "call_amount"])
@pytest.mark.parametrize("value", [1_000_001, 1e308, -1])
def test_money_out_of_range_returns_422(client, field, value):
    params = {**PAYLOAD["params"], field: value}
    assert post_json(client, {**PAYLOAD, "params": params}).status_code == 422


# --- CSRF ----------------------------------------------------------------------

@pytest.fixture
def csrf_client(user):
    """Клиент, который, как браузер, проверяет CSRF (обычный тестовый Client его пропускает)."""
    c = Client(enforce_csrf_checks=True)
    c.force_login(user)
    return c


def test_post_without_csrf_token_returns_403(csrf_client):
    assert post_json(csrf_client).status_code == 403
    assert Task.objects.count() == 0


def test_post_with_csrf_token_accepted(csrf_client):
    csrf_client.get("/accounts/login/")  # страница с формой выставляет cookie csrftoken
    token = csrf_client.cookies["csrftoken"].value
    assert post_json(csrf_client, HTTP_X_CSRFTOKEN=token).status_code == 202


# --- SECRET_KEY ----------------------------------------------------------------

def test_server_does_not_start_without_secret_key():
    # SECRET_KEY="" — «не задан» (и .env его не подставит: setdefault не перезаписывает).
    env = {**os.environ, "SECRET_KEY": "", "DJANGO_SETTINGS_MODULE": "config.settings"}
    r = subprocess.run(
        [sys.executable, "-c", "import django; django.setup()"],
        cwd=Path(__file__).resolve().parent.parent, env=env, capture_output=True, text=True,
    )
    assert r.returncode != 0
    assert "SECRET_KEY не задан" in r.stderr
