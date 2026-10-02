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
    assert "81.2%" in html
    assert "1.2%" in html
    assert "17.6%" in html
    assert '81.8<span>%</span>' in html
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
