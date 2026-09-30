from django.core.exceptions import ObjectDoesNotExist
from ninja import NinjaAPI, Schema
from ninja.errors import HttpError
from ninja.responses import Response

from core.schemas import PokerParams
from web import services

api = NinjaAPI(title="Poker API")


class TaskIn(Schema):
    name: str = "AA против одного"
    params: PokerParams


class TaskOut(Schema):
    id: int
    status: str = "PENDING"


@api.post("/tasks", response={202: TaskOut})
def create_task(request, payload: TaskIn):
    task = services.create_and_run(
        name=payload.name,
        params=payload.params.model_dump(),
    )
    return Response({"id": task.id, "status": getattr(task, "status", "PENDING")}, status=202)


@api.get("/tasks/{task_id}")
def get_task(request, task_id: int):
    try:
        task = services.get_task(task_id)
    except ObjectDoesNotExist:
        raise HttpError(404, "задача не найдена") from None
    return {"id": task.id, "status": getattr(task, "status", "PENDING")}
