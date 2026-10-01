"""Общие фикстуры для tests/: API и страницы закрыты входом (django_auth / login_required)."""
import pytest

TEST_USERNAME = "test_user"
TEST_PASSWORD = "test12345"


@pytest.fixture
def user(django_user_model):
    """Тестовый пользователь. django_user_model — встроенная фикстура pytest-django (класс модели)."""
    return django_user_model.objects.create_user(username=TEST_USERNAME, password=TEST_PASSWORD)


@pytest.fixture(autouse=True)
def _login(request):
    """Каждый тест в tests/ получает уже залогиненный client.

    Тесты без БД (django_db) не трогаем — им пользователь не нужен.
    Анонимные сценарии создают свой Client() без входа.
    """
    if request.node.get_closest_marker("django_db") is None:
        return
    request.getfixturevalue("client").force_login(request.getfixturevalue("user"))
