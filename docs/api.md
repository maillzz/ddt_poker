# API — Poker Monte Carlo

Интерактивная документация (Swagger UI): **`/api/docs`**, схема OpenAPI: **`/api/openapi.json`**.

**Доступ:** все эндпоинты — только после входа (сессия Django, вход на `/accounts/login/`).
POST дополнительно требует CSRF-токен: заголовок `X-CSRFToken` со значением cookie `csrftoken`.
Каждый пользователь видит только свои задачи; чужая задача неотличима от несуществующей (404).

## Эндпоинты

| Адрес | Метод | Что делает | Коды ответа |
|-------|-------|------------|-------------|
| `/api/tasks` | POST | Создаёт задачу и запускает расчёт в фоне (не ждёт окончания). Тело: `{"name": "...", "params": {...}}`, ответ: `{"id": 7, "status": "PENDING"}` | **202** принята · **401** не вошёл · **403** нет CSRF-токена · **422** неверные параметры |
| `/api/tasks/{task_id}` | GET | Статус задачи: `{"id": 7, "status": "RUNNING"}`. Этот адрес опрашивает страница задачи раз в 1,5 с | **200** · **401** не вошёл · **404** нет такой задачи или она чужая |
| `/api/tasks/{task_id}/result` | GET | Результат готовой задачи: `win_probability`, `tie_probability`, `loss_probability`, `equity`, `recommendation`, `simulations` | **200** готово · **401** не вошёл · **404** нет такой задачи или она чужая · **409** ещё не готова (`PENDING`/`RUNNING`/`FAILED`) |
| `/api/docs` | GET | Swagger UI: описание и ручной вызов эндпоинтов | **200** |
| `/api/openapi.json` | GET | Машиночитаемая схема API (OpenAPI 3) | **200** |

## Параметры задачи (`params`)

Проверяются схемой `core/schemas.py:PokerParams` до расчёта, нарушение → 422.
Подробная таблица границ — в [README, «Границы входных данных»](../README.md).

| Поле | Обязательное | Допустимо |
|------|:---:|-----------|
| `hole_cards` | да | ровно 2 карты, например `["As", "Kh"]` |
| `community` | нет | 0–5 карт |
| `opponents` | нет | 1–9 (по умолчанию 1) |
| `simulations` | нет | 100–200 000 (по умолчанию 10 000) |
| `seed` | нет | целое или `null` |
| `pot_size`, `call_amount` | нет | 0–1 000 000 |

Карта — 2 символа «ранг + масть»: ранги `23456789TJQKA`, масти `shdc`; карты не повторяются.
`name` — до 255 символов.

## Формат ошибок

Все ошибки — JSON с полем `detail`:

```json
{"detail": "задача не найдена"}          // 404
{"detail": "ещё не готова: RUNNING"}      // 409
{"detail": "Unauthorized"}                // 401
{"detail": "CSRF check Failed"}           // 403
{"detail": [{"loc": ["body", "payload", "params", "hole_cards", 1],
             "msg": "Value error, карта 'Zz': неизвестный ранг 'Z', ...", "type": "value_error"}]}  // 422
```

## Жизненный цикл задачи

```
POST /api/tasks ─► PENDING ─► RUNNING ─► FINISHED   (GET …/result → 200)
                                    └──► FAILED     (GET …/result → 409, текст ошибки — на странице задачи)
```

## Пример (curl)

```bash
# 1. Войти и сохранить cookie (sessionid, csrftoken) — например, через страницу /accounts/login/ в браузере
# 2. Создать задачу
curl -b cookies.txt -H "X-CSRFToken: <csrftoken>" -H "Content-Type: application/json" \
     -d '{"params": {"hole_cards": ["As", "Ah"], "opponents": 1, "simulations": 10000}}' \
     http://127.0.0.1:8000/api/tasks                  # → 202 {"id": 7, "status": "PENDING"}
# 3. Статус и результат
curl -b cookies.txt http://127.0.0.1:8000/api/tasks/7          # → 200 {"id": 7, "status": "FINISHED"}
curl -b cookies.txt http://127.0.0.1:8000/api/tasks/7/result   # → 200 {"win_probability": 0.85, ...}
```
