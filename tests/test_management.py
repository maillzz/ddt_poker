"""Команды первоначальной настройки из README."""
import secrets
from io import StringIO
from unittest.mock import Mock

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_interactive_createsuperuser_validates_password_and_allows_login(
    client, django_user_model, monkeypatch,
):
    password = secrets.token_urlsafe(24)
    getpass = Mock(side_effect=["short", "short", password, password])
    monkeypatch.setattr("django.contrib.auth.management.commands.createsuperuser.getpass.getpass", getpass)
    # Короткий пароль отклоняем, затем вводим допустимый пароль.
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    errors = StringIO()

    call_command(
        "createsuperuser", username="exam_admin", email="exam@example.test",
        interactive=True, stdin=Mock(isatty=Mock(return_value=True)),
        stdout=StringIO(), stderr=errors,
    )

    assert getpass.call_count == 4
    assert errors.getvalue()
    admin = django_user_model.objects.get(username="exam_admin")
    assert admin.is_staff and admin.is_superuser
    assert client.login(username=admin.username, password=password)
