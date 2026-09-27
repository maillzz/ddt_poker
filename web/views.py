from pydantic import ValidationError

from django.shortcuts import get_object_or_404, redirect, render

from core.schemas import PokerParams
from web import services
from web.forms import PokerTaskForm
from web.models import Task


def task_list(request):
    tasks = services.list_tasks()[:50]
    return render(request, "web/list.html", {"tasks": tasks})


def task_create(request):
    if request.method == "POST":
        form = PokerTaskForm(request.POST)
        if form.is_valid():
            try:
                # Валидация pydantic-схемой ДО запуска расчёта (см. AGENTS.md, п.4) —
                # той же самой, что использует API, чтобы форма и API считали одинаково.
                validated = PokerParams(
                    hole_cards=form.cleaned_data["hole_cards"],
                    community=form.cleaned_data["community"],
                    opponents=form.cleaned_data["opponents"],
                    simulations=form.cleaned_data["simulations"],
                    seed=form.cleaned_data["seed"],
                    pot_size=form.cleaned_data["pot_size"] or 0,
                    call_amount=form.cleaned_data["call_amount"] or 0,
                )
            except ValidationError as exc:
                form.add_error(None, str(exc))
            else:
                name = "{} против {}".format(
                    " ".join(validated.hole_cards), validated.opponents
                )
                task = services.create_and_run(
                    name=name, params=validated.model_dump()
                )
                return redirect("task_detail", pk=task.pk)
    else:
        form = PokerTaskForm()
    return render(request, "web/form.html", {"form": form})


def task_detail(request, pk: int):
    task = get_object_or_404(Task, pk=pk)
    return render(request, "web/detail.html", {"task": task})
