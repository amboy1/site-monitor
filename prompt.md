Ты работаешь над существующим Python-проектом **Async Site Monitor**.

Цель текущего этапа: полностью довести API-часть Stage 1 до аккуратного рабочего состояния, **НЕ добавляя пока SQLAlchemy, PostgreSQL, Redis, Celery/ARQ, JWT, Docker и другие следующие этапы**.

Стек текущего этапа:

* Python
* FastAPI
* Pydantic
* aiohttp
* asyncio
* pytest
* httpx

## Что уже реализовано

Есть структура примерно:

```text
async-site-monitor/
├── app/
│   ├── main.py
│   ├── api/
│   ├── schemas/
│   │   └── monitor.py
│   └── monitoring/
│       └── checker.py
├── cli/
├── tests/
├── requirements.txt
└── README.md
```

`checker.py` содержит асинхронную функцию:

```python
async def check_site(
    url: str,
    session: aiohttp.ClientSession,
    timeout: float = 5
):
    ...
```

Она проверяет URL через aiohttp и возвращает `dict` с результатом:

```python
{
    "status": "OK",
    "time": 123.4,
    "code": 200
}
```

или, например:

```python
{
    "status": "TIMEOUT",
    "time": 5000.0,
    "code": 0
}
```

При ошибке:

```python
{
    "status": "FAIL",
    "time": 100.0,
    "code": 0,
    "error": "..."
}
```

Есть Pydantic-схемы `CheckRequest`, `CheckBatchRequest` и `CheckResponse`.

API уже содержит:

```text
GET /
POST /api/v1/check
POST /api/v1/check/batch
```

Batch использует одну `aiohttp.ClientSession` и `asyncio.gather()` для конкурентной проверки нескольких URL.

## Твоя задача

Доведи Stage 1 до качественного состояния перед переходом к БД.

### 1. Проверить и исправить timeout

Убедись, что значение timeout действительно передаётся из API в `check_site()`.

Не должно быть ситуации:

```python
timeout: float = 5
```

но внутри:

```python
aiohttp.ClientTimeout(total=5)
```

Должно использоваться переданное значение.

Проверь это и для `/check`, и для `/check/batch`.

---

### 2. Валидация timeout

Добавь Pydantic-валидацию:

```text
timeout > 0
timeout <= 30
```

Например, значения:

```text
-1
0
31
100
```

должны отклоняться FastAPI с HTTP 422.

Значения:

```text
0.1
5
10
30
```

должны приниматься.

Используй возможности актуального Pydantic, не пиши собственную ручную проверку в endpoint без необходимости.

---

### 3. Ограничение batch

Для `CheckBatchRequest` введи ограничение на количество URL:

```text
минимум 1
максимум 50
```

То есть:

```json
{
  "urls": []
}
```

должно быть отклонено.

И запрос с более чем 50 URL тоже должен получать HTTP 422.

---

### 4. Response models

Убедись, что endpoints используют Pydantic response models:

```python
@app.post("/api/v1/check", response_model=CheckResponse)
```

и:

```python
@app.post(
    "/api/v1/check/batch",
    response_model=list[CheckResponse]
)
```

Не нужно вручную делать:

```python
CheckResponse(**result)
```

в endpoint, если FastAPI уже может выполнить валидацию через `response_model`.

Предпочтительно возвращать:

```python
return result
```

или:

```python
return results
```

---

### 5. Проверить разделение ответственности

Не нужно пока полностью переписывать архитектуру.

Но проверь, что:

* `checker.py` отвечает за проверку сайтов;
* FastAPI endpoint отвечает за HTTP/API;
* Pydantic schemas отвечают за валидацию входа и структуру ответа;
* CLI отвечает за вывод результатов пользователю.

Если `print()` в `checker.py` мешает нормальному разделению ответственности, аккуратно убери его из `checker.py` и перенеси отображение результата туда, где оно действительно нужно.

При этом **не ломай существующий CLI**.

---

### 6. Проверить batch

Batch должен использовать одну `ClientSession`:

```text
ClientSession
      │
      ├── site 1
      ├── site 2
      ├── site 3
      └── ...
```

и `asyncio.gather()` для конкурентного выполнения.

Не создавай отдельную `ClientSession` для каждого URL.

Проверь, что timeout из `CheckBatchRequest` передаётся каждому `check_site()`.

---

### 7. Обработка HTTP-статусов

Важно сохранить текущую семантику мониторинга:

Если внешний сайт вернул:

```text
200 → OK
500 → ERROR
404 → ERROR
```

это **не ошибка FastAPI**.

Например, API может вернуть:

```json
{
  "status": "ERROR",
  "time": 120.5,
  "code": 500
}
```

с HTTP 200 от нашего API.

Не превращай ответ внешнего сайта 404/500 автоматически в HTTP 404/500 нашего API.

HTTP 422 должен использоваться для невалидных входных данных.

---

### 8. Тесты

Добавь/дополни pytest-тесты.

Не используй реальные Google/GitHub и другие внешние сайты в тестах.

Нужно протестировать минимум:

#### Checker

* `200` → `OK`
* `500` → `ERROR`
* timeout → `TIMEOUT`
* исключение aiohttp → `FAIL`
* переданный timeout действительно используется

#### API

* `/` работает
* `/api/v1/check` принимает корректный запрос
* `/api/v1/check` возвращает ожидаемую структуру
* `/api/v1/check/batch` принимает несколько URL
* batch возвращает массив результатов
* timeout `<= 0` → 422
* timeout `> 30` → 422
* пустой batch → 422
* batch > 50 URL → 422

Для API используй `httpx`/FastAPI TestClient или актуальный рекомендуемый способ для текущей версии FastAPI.

Для сетевых запросов используй mock/stub, чтобы тесты были быстрыми и независимыми от интернета.

---

### 9. Swagger

Проверь `/docs`.

В Swagger должно быть понятно:

`POST /api/v1/check`

Request:

```json
{
  "url": "https://example.com",
  "timeout": 5
}
```

Response:

```json
{
  "status": "OK",
  "time": 123.4,
  "code": 200
}
```

И:

`POST /api/v1/check/batch`

Request:

```json
{
  "urls": [
    "https://example.com",
    "https://google.com"
  ],
  "timeout": 5
}
```

Response:

```json
[
  {
    "status": "OK",
    "time": 123.4,
    "code": 200
  },
  {
    "status": "OK",
    "time": 150.2,
    "code": 200
  }
]
```

---

### 10. README

Обнови README так, чтобы он описывал текущую функциональность:

* что делает проект;
* запуск;
* CLI;
* FastAPI;
* `/docs`;
* `/api/v1/check`;
* `/api/v1/check/batch`;
* timeout;
* batch;
* запуск тестов.

Не описывай PostgreSQL, Redis и остальные технологии как уже реализованные.

Можно указать их в отдельном разделе `Roadmap`, если он уже существует.

---

## Ограничения

**Критически важно:**

НЕ добавляй сейчас:

* SQLAlchemy
* PostgreSQL
* Alembic
* Redis
* Celery
* ARQ
* JWT
* пользователей
* авторизацию
* Docker
* Telegram notifications
* background workers
* систему incidents
* статистику

Это будет следующим этапом после завершения Stage 1.

Не переписывай проект целиком.

Сохрани существующую CLI-функциональность.

Не добавляй ненужные абстракции и классы только ради архитектуры.

После выполнения:

1. Покажи изменённые файлы.
2. Кратко объясни каждое существенное изменение.
3. Покажи, какие тесты добавлены.
4. Запусти тесты и сообщи результат.
5. Отдельно укажи, что Stage 1 завершён и проект готов к следующему этапу — SQLAlchemy + PostgreSQL.
6. Если обнаружишь архитектурную проблему, сначала объясни её, а не переписывай проект без необходимости.
