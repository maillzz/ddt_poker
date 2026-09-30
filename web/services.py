"""Сервисный слой между веб/API-кодом и вычислительным ядром.

Правило проекта (см. AGENTS.md): views и API не содержат бизнес-логики и не
вызывают core напрямую — только через эти функции. Статус задачи меняется
только в execute_task (фоновый поток) и web/jobs.py:enqueue_task (очередь).
"""
import threading

from django.db import connection, transaction

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


def _execute_in_thread(task_id: int) -> None:
    """Тело фонового потока: считает задачу и закрывает своё соединение с БД.

    Соединения Django привязаны к потоку — без close() каждый расчёт
    оставлял бы открытое соединение.
    """
    try:
        execute_task(task_id)
    finally:
        connection.close()


def create_and_run(name: str, params: dict) -> Task:
    """Создаёт задачу и запускает расчёт, НЕ дожидаясь его окончания.

    USE_QUEUE=1 — задача уходит в очередь Redis/RQ (web/jobs.py).
    Иначе — расчёт в отдельном потоке этого же процесса (ADR-002): HTTP-ответ
    уходит сразу, статус RUNNING → FINISHED/FAILED клиент узнаёт опросом
    GET /api/tasks/{id}. Флаг переключения — settings.USE_QUEUE.
    """
    from django.conf import settings

    task = create_task(name=name, params=params)
    if settings.USE_QUEUE:
        from web.jobs import enqueue_task

        enqueue_task(task.id)
    else:
        # on_commit: поток стартует, только когда строка задачи уже видна
        # другим соединениям (в autocommit — немедленно).
        transaction.on_commit(
            lambda: threading.Thread(
                target=_execute_in_thread, args=(task.id,), daemon=True
            ).start()
        )
    return task
