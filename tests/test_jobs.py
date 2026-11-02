"""Очередь работает с существующими статусами; Redis/RQ подменены."""
from unittest.mock import Mock

import pytest

from web import jobs, services
from web.models import Task


@pytest.mark.django_db
def test_enqueue_task_uses_existing_status(user, monkeypatch):
    task = services.create_task("test", {}, owner=user)
    Task.objects.filter(pk=task.pk).update(status="FAILED")
    queue = Mock()
    monkeypatch.setattr(jobs, "get_queue", lambda: queue)
    jobs.enqueue_task(task.pk)
    task.refresh_from_db()
    assert task.status == "PENDING"
    assert task.status in dict(Task.STATUS_CHOICES)
    queue.enqueue.assert_called_once_with("web.services.execute_task", task.pk, job_timeout=600)



@pytest.mark.django_db
def test_queue_mode_api_returns_202(client, settings, monkeypatch):
    settings.USE_QUEUE = True
    queue = Mock()
    monkeypatch.setattr(jobs, "get_queue", lambda: queue)
    response = client.post(
        "/api/tasks", {"params": {"hole_cards": ["As", "Ah"], "simulations": 100}},
        content_type="application/json",
    )
    assert response.status_code == 202
    task = Task.objects.get(pk=response.json()["id"])
    assert task.status == "PENDING"
    queue.enqueue.assert_called_once_with("web.services.execute_task", task.pk, job_timeout=600)

