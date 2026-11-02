"""Список API доступен только владельцу задач."""
import pytest
from django.test import Client

from web import services


@pytest.mark.django_db
def test_api_list_contains_only_current_users_tasks(client, user, django_user_model):
    other = django_user_model.objects.create_user(username="other")
    services.create_task("test", {}, owner=other)
    first = services.create_task("test test", {}, owner=user)
    latest = services.create_task("test test", {}, owner=user)
    response = client.get("/api/tasks")
    assert response.status_code == 200
    assert response.json() == [
        {"id": latest.pk, "status": "PENDING"},
        {"id": first.pk, "status": "PENDING"},
    ]
    client.force_login(other)
    assert all(item["id"] not in {first.pk, latest.pk} for item in client.get("/api/tasks").json())



@pytest.mark.django_db
def test_api_list_requires_login():
    assert Client().get("/api/tasks").status_code == 401

