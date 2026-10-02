from django.core.exceptions import ObjectDoesNotExist
from ninja import Field, NinjaAPI, Schema
from ninja.errors import HttpError
from ninja.responses import Response
from ninja.security import SessionAuth

from core.schemas import PokerParams
from web import services


class LoginThenCsrf(SessionAuth):
    """django_auth (вход по сессии + CSRF на POST), но сначала проверяется вход.

    Стандартный SessionAuth проверяет CSRF первым, и аноним без токена получает 403.
    Здесь аноним всегда получает 401 «войдите», а вошедший без CSRF-токена — 403.
    """

    def __call__(self, request):
        if not request.user.is_authenticated:
            return None  # → 401
        return super().__call__(request)  # CSRF (X-CSRFToken из cookie csrftoken), затем вход


# Аутентификация на всех эндпоинтах API.
api = NinjaAPI(title="Poker API", auth=LoginThenCsrf())


class TaskIn(Schema):
    name: str = Field(default="AA против одного", max_length=255)  # = Task.name.max_length
    params: PokerParams


class TaskOut(Schema):
    id: int
    status: str = "PENDING"


@api.post("/tasks", response={202: TaskOut})
def create_task(request, payload: TaskIn):
    task = services.create_and_run(
        name=payload.name,
        params=payload.params.model_dump(),
        owner=request.user,
    )
    return Response({"id": task.id, "status": getattr(task, "status", "PENDING")}, status=202)


@api.get("/tasks/{task_id}")
def get_task(request, task_id: int):
    try:
        task = services.get_task(task_id, owner=request.user)
    except ObjectDoesNotExist:
        raise HttpError(404, "задача не найдена") from None
    return {"id": task.id, "status": getattr(task, "status", "PENDING")}


@api.get("/tasks/{task_id}/result")
def get_result(request, task_id: int):
    try:
        task = services.get_task(task_id, owner=request.user)
    except ObjectDoesNotExist:
        raise HttpError(404, "задача не найдена") from None
    if task.status != "FINISHED":
        raise HttpError(409, f"ещё не готова: {task.status}")
    return task.result
