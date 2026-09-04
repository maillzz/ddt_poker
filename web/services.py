from web.models import Task


def create_task(name: str, params: dict) -> Task:
    return Task.objects.create(name=name, params=params, status="PENDING")


def get_task(task_id: int) -> Task:
    return Task.objects.get(id=task_id)


def list_tasks():
    return Task.objects.all().order_by("-created_at")