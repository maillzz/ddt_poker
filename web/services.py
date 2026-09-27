"""Сервисный слой между веб/API-кодом и вычислительным ядром.

Правило проекта (см. AGENTS.md): views и API не содержат бизнес-логики и не
вызывают core напрямую — только через эти функции. Статус задачи меняется
только в execute_task (синхронный путь) и web/jobs.py:enqueue_task (очередь).
"""
from core.solver import run as solve_poker
from web.models import Task


def create_task(name: str, params: dict) -> Task:
    return Task.objects.create(name=name, params=params, status="PENDING")


def get_task(task_id: int) -> Task:
    return Task.objects.get(id=task_id)


def list_tasks():
    return Task.objects.all().order_by("-created_at")


def execute_task(task_id: int) -> Task:
    """Выполняет расчёт ядра для задачи и сохраняет результат/ошибку.

    Единственное место, где задача переходит в RUNNING/FINISHED/FAILED.
    Вызывается либо напрямую (синхронно, заезд 1), либо воркером очереди
    из web/jobs.py (заезд 2, USE_QUEUE=1).
    """
    task = Task.objects.get(id=task_id)
    task.status = "RUNNING"
    task.save(update_fields=["status", "updated_at"])

    try:
        result = solve_poker(task.params)
    except Exception as exc:  # noqa: BLE001 — граница сервиса: задача не должна «зависнуть»
        task.status = "FAILED"
        task.error = str(exc)
        task.save(update_fields=["status", "error", "updated_at"])
        return task

    task.status = "FINISHED"
    task.result = result
    task.error = ""
    task.save(update_fields=["status", "result", "error", "updated_at"])
    return task


def create_and_run(name: str, params: dict) -> Task:
    """Создаёт задачу и сразу считает её — синхронно или через очередь Redis/RQ.

    Флаг переключения — settings.USE_QUEUE (см. config/settings.py).
    """
    from django.conf import settings

    task = create_task(name=name, params=params)
    if settings.USE_QUEUE:
        from web.jobs import enqueue_task

        enqueue_task(task.id)
    else:
        execute_task(task.id)
        task.refresh_from_db()
    return task
