"""Front-end integration: server validation and correct probability units."""
import pytest

from web.models import Task


@pytest.mark.django_db
def test_result_displays_probability_as_percentage(client, user):
    task = Task.objects.create(
        owner=user,
        name="AA",
        params={"hole_cards": ["As", "Ah"], "community": [], "opponents": 1},
        status="FINISHED",
        result={
            "win_probability": 0.8123,
            "tie_probability": 0.012,
            "loss_probability": 0.1757,
            "equity": 0.8183,
            "recommendation": "RAISE",
        },
    )
    response = client.get(f"/tasks/{task.pk}/")
    assert response.status_code == 200
    html = response.content.decode()
    assert "81.23%" in html
    assert "1.20%" in html
    assert "17.57%" in html
    assert '81.83<span>%</span>' in html
    assert 'id="task-params"' in html


@pytest.mark.django_db
def test_duplicate_cards_keep_bound_form_without_creating_task(client):
    response = client.post(
        "/tasks/new/",
        {"hole_cards": "As As", "opponents": 1, "simulations": 1000},
    )
    assert response.status_code == 200
    assert response.context["form"].errors
    assert 'value="As As"' in response.content.decode()
    assert Task.objects.count() == 0


@pytest.mark.django_db
def test_form_validation_is_short_and_readable(client):
    response = client.post("/tasks/new/", {
        "hole_cards": "As As", "opponents": 1, "simulations": 100,
    })
    html = response.content.decode()
    assert "карты повторяются: As" in html
    assert "validation error" not in html
    assert "input_value" not in html
    assert "errors.pydantic.dev" not in html
    assert Task.objects.count() == 0



@pytest.mark.django_db
def test_finished_status_and_recommendation_are_russian(client, user):
    task = Task.objects.create(
        owner=user, name="test", status="FINISHED",
        params={"hole_cards": ["As", "Ah"], "opponents": 1},
        result={"recommendation": "CHECK", "equity": 0.85},
    )
    html = client.get(f"/tasks/{task.pk}/").content.decode()
    assert "Завершена" in html
    assert "Пропустить ход" in html
    assert "Finished" not in html
    assert "CHECK" not in html
    assert "Завершена" in client.get("/").content.decode()
