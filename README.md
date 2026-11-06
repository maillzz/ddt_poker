# Poker Monte Carlo

Учебный сервис поддержки решений в Texas Hold’em. Пользователь задаёт две свои карты,
общие карты, число соперников, банк и сумму колла. Метод Монте-Карло оценивает вероятность
победы, ничьей и поражения; результат сохраняется в истории пользователя.

## Что умеет сервис

- Симулирует случайные руки соперников и неизвестные карты стола; комбинации оценивает `treys`.
- Показывает вероятности в процентах, эквити и рекомендацию с поясняющими русскими подписями.
- При `call_amount = 0` всегда рекомендует **CHECK** (пропустить ход).
- При положительной ставке сравнивает эквити с ценой колла `call / (pot + call)`:
  эквити ниже порога → **FOLD**, от порога → **CALL**, от порога + 0,15 → **RAISE**.
- Сохраняет задачи и результаты; каждый пользователь видит только свои расчёты.
- Выполняет расчёт в фоновом потоке (`USE_QUEUE=0`) либо в очереди Redis/RQ (`USE_QUEUE=1`).

Модель учебная: соперники получают случайные руки, их стиль и будущие ставки не учитываются.
Эквити считается как `Win + Tie / 2`; для ничьих с несколькими соперниками это приближение.

## Стек

Python 3.14 (минимум 3.12), Django 5.x, Django Ninja, pydantic, `treys`, SQLite для локального
запуска, PostgreSQL для Docker, Redis + RQ для очереди. Тесты — pytest, стиль — ruff.
Версии зафиксированы в [requirements.txt](requirements.txt), выбор объяснён в [ADR-001](docs/adr/001-stack.md).

## Запуск с нуля без Docker

```bash
git clone https://github.com/maillzz/ddt_poker.git
cd ddt_poker
python -m venv .venv
```

Активация: Windows PowerShell — `.\.venv\Scripts\Activate.ps1`,
Linux/macOS — `source .venv/bin/activate`:

```bash
python -m pip install -r requirements.txt
```

Скопируйте `.env.example` в `.env`: в PowerShell `Copy-Item .env.example .env`,
в Linux/macOS `cp .env.example .env`. Сгенерируйте ключ и впишите его в `SECRET_KEY` в `.env`:

```bash
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

Для локальной разработки оставьте `DEBUG=1`, `USE_QUEUE=0`, `DATABASE_URL=` из шаблона.
`.env` с ключом не добавляется в Git. Без ключа сервер не запустится.

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Вход: <http://127.0.0.1:8000/accounts/login/>. Калькулятор: `/tasks/new/`, история: `/`,
документация API: `/api/docs`. Аккаунт создаёт администратор, самостоятельной регистрации нет.

## Docker и очередь

После настройки `.env`:

```bash
docker compose up --build -d
docker compose exec web python manage.py createsuperuser
```

Compose запускает PostgreSQL, Redis, веб-приложение и воркер; для веба включён `USE_QUEUE=1`.
Миграции применяются при старте веб-контейнера. Очередь называется `calc`; при постановке задача
остаётся в существующем статусе `PENDING`, воркер переводит её в `RUNNING`, затем `FINISHED` или `FAILED`.

Чтобы использовать очередь при локальном запуске: поднимите Redis (`docker compose up -d redis`),
поставьте в `.env` `USE_QUEUE=1`, `REDIS_URL=redis://localhost:6379/0` и в отдельном терминале запустите
`python manage.py rqworker`. Для штатного воркера RQ используйте Linux, WSL или Docker.

Статику (общий CSS и JS) в Docker и под gunicorn отдаёт WhiteNoise из `STATIC_ROOT`;
`collectstatic --noinput` запускается при сборке образа (см. Dockerfile). Локальный `runserver`
отдаёт её сам при `DEBUG=1`.

## Вычислительное ядро из командной строки

[example_input.json](example_input.json) — пример покерной раздачи.
Вход CLI, формы и API проверяется одной pydantic-схемой до расчёта.

```bash
python -m core --help
python -m core example_input.json
python -m core example_input.json result.json
```

Пример: `As Ah`, 1 соперник, 10 000 симуляций, `seed=1`, нулевая ставка — вероятность победы
85,12 % (ничья 0,60 %, поражение 14,28 %), рекомендация **CHECK**. При фиксированном seed результат воспроизводим.

## API

Все четыре операции требуют входа по сессии Django. POST дополнительно требует CSRF-токен
в заголовке `X-CSRFToken` из cookie `csrftoken`.

| Метод | Адрес | Ответ |
|-------|-------|-------|
| GET | `/api/tasks` | 200: список `[{"id": 7, "status": "PENDING"}]`, только свои задачи, новые первыми |
| POST | `/api/tasks` | 202: `{"id": 7, "status": "PENDING"}`, расчёт запускается в фоне |
| GET | `/api/tasks/{id}` | 200: идентификатор и текущий статус |
| GET | `/api/tasks/{id}/result` | 200: результат; 409, пока задача не завершена успешно |

Без входа — 401, чужая или отсутствующая задача — 404. Плохие параметры — 422 без создания задачи.
Формат запросов, ошибки и примеры — в [docs/api.md](docs/api.md).

## Границы входных данных

Проверяются схемой `core/schemas.py:PokerParams` до запуска ядра.

| Поле | Допустимо | По умолчанию |
|------|-----------|--------------|
| `hole_cards` | ровно 2 карты, обязательно | — |
| `community` | 0–5 карт | `[]` |
| `opponents` | целое 1–9 | 1 |
| `simulations` | целое 100–200 000 | 10 000 |
| `seed` | целое, включая отрицательное, или `null` | `null` |
| `pot_size`, `call_amount` | число 0–1 000 000 | 0 |
| `name` (API) | строка до 255 символов | «AA против одного» |

Карта — два символа: ранг `23456789TJQKA` и масть `shdc`, например `As`, `Td`, `7c`.
Регистр нормализуется; повтор одной карты в руке и/или на столе запрещён.
Вероятности API — доли от 0 до 1; веб-интерфейс переводит их в проценты.

## Проверка

```bash
pytest -q
ruff check .
python manage.py check
python manage.py makemigrations --check --dry-run
```

Тесты проверяют эталонные раздачи, CHECK при нулевой ставке, изоляцию пользователей,
валидацию, интерфейс и CLI. Очередь проверяется с подменой Redis/RQ;
реальный Docker-запуск проверяется отдельно.

## Вклад

### Работа участников

<table>
  <thead>
    <tr>
      <th>Участник</th>
      <th>Что делал</th>
      <th>Основные файлы</th>
      <th>Тема на зачёте</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>Супаев Висхан</th>
      <td>Ядро и эталонные тесты</td>
      <td><code>core/</code>, <code>example_input.json</code></td>
      <td>Монте-Карло, оценка комбинаций, шансы AA</td>
    </tr>
    <tr>
      <th>Харцаев Муслим</th>
      <td>Формы и интерфейс</td>
      <td><code>web/forms.py</code>, <code>web/views.py</code>, <code>templates/</code>, <code>web/static/</code></td>
      <td>Валидация формы, выбор карт, вывод результата</td>
    </tr>
    <tr>
      <th>Асхабов Дени</th>
      <td>API, сервисы и архитектура</td>
      <td><code>api/</code>, <code>web/services.py</code>, <code>docs/</code></td>
      <td>Четыре операции API, доступ владельца, границы слоёв</td>
    </tr>
    <tr>
      <th>Мустафаев Зелим</th>
      <td>Docker, очередь и тестирование</td>
      <td><code>Dockerfile</code>, <code>docker-compose.yml</code>, <code>web/jobs.py</code>, <code>tests/</code></td>
      <td>Redis/RQ, статусы задач, миграции и тесты</td>
    </tr>
  </tbody>
</table>

### Доработки к зачёту

<table>
  <thead>
    <tr>
      <th>Участник</th>
      <th>Последние изменения</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>Супаев Висхан</th>
      <td>CHECK при нулевой ставке; удаление неиспользуемой оценки; CLI со справкой и покерный пример</td>
    </tr>
    <tr>
      <th>Харцаев Муслим</th>
      <td>Русские подписи; короткие ошибки формы; таблицы параметров и результата; округление чисел</td>
    </tr>
    <tr>
      <th>Асхабов Дени</th>
      <td>Список своих задач в API; обновление описания API, ADR-001 и архитектуры</td>
    </tr>
    <tr>
      <th>Мустафаев Зелим</th>
      <td>Исправление статуса очереди на PENDING; отдача статики в Docker через WhiteNoise;
      регрессионные тесты; миграция подписей статусов</td>
    </tr>
  </tbody>
</table>

## Документация

[Архитектура](docs/architecture.md) · [ADR-001](docs/adr/001-stack.md) ·
[API](docs/api.md) · [Фронтенд](docs/frontend.md) · [Безопасность](docs/security_review.md).
