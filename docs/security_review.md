# Security review — Poker Monte Carlo

**Дата:** 2026-10-01
**Область:** `config/settings.py`, `api/api.py`, `core/schemas.py`, `web/` (модели, сервисы, views), `requirements.txt`, `docker-compose.yml`.
**Проверка:** `pytest -q` (тесты безопасности — `tests/test_security.py`) + ручная проверка на `runserver` через HTTP.

| # | Пункт | Что было | Статус | Что сделано / где проверяется |
|---|-------|----------|--------|-------------------------------|
| 1 | `DEBUG` | `DEBUG=1` по умолчанию: в проде трейсбеки и настройки видны любому | **исправлено** | По умолчанию `False`, включается только `DEBUG=1` (`config/settings.py`). Проверено: без `DEBUG` страница 404 — без трейсбека |
| 2 | `SECRET_KEY` | Ключ по умолчанию `dev-only-insecure-key-change-me` в коде и в `docker-compose.yml` | **исправлено** | Ключ только из окружения/`.env`; без него `ImproperlyConfigured`, сервер не стартует; `docker compose` без ключа тоже не стартует. Тест `test_server_does_not_start_without_secret_key`. Добавлен `.env.example` |
| 3 | Длина ввода (`name`) | `name` без лимита: 100 000 символов → 202 и запись в БД | **исправлено** | `TaskIn.name: Field(max_length=255)` (= `Task.name`). 1000 символов → 422. Тесты `test_name_1000_chars_returns_422`, `test_name_255_chars_accepted` |
| 4 | Числовые лимиты (`pot_size`, `call_amount`) | Только `ge=0`, сверху без предела | **исправлено** | `ge=0, le=1_000_000` (`core/schemas.py`). Нижняя граница `ge=0`, а не `gt=0`: `call_amount=0` — штатный случай «доплачивать нечего» → CHECK. Тест `test_money_out_of_range_returns_422` |
| 5 | Аутентификация | Аноним создаёт и читает задачи | **исправлено** | API: сессионная аутентификация на всех эндпоинтах → аноним 401. Сайт: `@login_required` на всех страницах → редирект на `/accounts/login/`. Тесты `test_anonymous_*` |
| 6 | Доступ к чужим задачам (IDOR) | У `Task` нет владельца, `GET /api/tasks/{id}` и `/tasks/{id}/` отдают любую задачу | **исправлено** | `Task.owner` (FK на пользователя, `CASCADE`, миграция `0002_task_owner`); все функции `web/services.py` фильтруют по владельцу; чужая задача — 404, как несуществующая. Тесты `test_user2_*` |
| 7 | CSRF | Отдельной защиты API не было | **исправлено** | Сессионная аутентификация Ninja проверяет CSRF на POST: вошедший без `X-CSRFToken` → 403. Порядок: сначала вход (аноним → 401), потом CSRF. Тесты `test_post_without_csrf_token_returns_403`, `test_post_with_csrf_token_accepted` |
| 7а | Эндпоинт, отдающий `csrf_token` | — | **не найдено** | Такого эндпоинта в проекте нет. `{% csrf_token %}` есть только внутри HTML-форм (создание задачи, вход, выход) — это штатная защита формы, его удалять нельзя |
| 8 | Зависимости | Все версии через `>=`, сборка невоспроизводима | **исправлено** | Прямые зависимости закреплены `==` (`requirements.txt`). Транзитивные (`asgiref`, `sqlparse`, `pydantic-core`…) не закреплены — для полной фиксации нужен lock-файл (`pip freeze > constraints.txt` в чистом venv) |
| 9 | `ALLOWED_HOSTS` | В `docker-compose.yml`: `"*"` у `web`, нет у `worker` | **исправлено** | `${ALLOWED_HOSTS:-localhost,127.0.0.1}` у обоих сервисов; значение задаётся в `.env` |

## Как это проверить руками

```bash
cp .env.example .env            # вписать SECRET_KEY
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
- `curl -X POST localhost:8000/api/tasks -H 'Content-Type: application/json' -d '{"params":{"hole_cards":["As","Ah"]}}'` → `401`.
- Войти под пользователем 1, создать задачу; войти под пользователем 2 — `/tasks/<id>/` → `404`.

## Остаточные риски (не входили в задачу)

- Нет регистрации: пользователей создаёт администратор (`createsuperuser` / админка).
- Нет лимита частоты запросов: вошедший пользователь может запустить много тяжёлых расчётов подряд (фоновые потоки без ограничения — см. ADR-002).
- Задачи, созданные до миграции `0002`, остаются без владельца (`owner=NULL`) и не видны никому, кроме админки.
- Для продакшена без `DEBUG` нужна отдача статики (`collectstatic` + веб-сервер/WhiteNoise) и HTTPS-настройки (`SECURE_*`, `CSRF_COOKIE_SECURE`, `SESSION_COOKIE_SECURE`).
