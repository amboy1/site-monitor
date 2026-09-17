# 🌐 Async Site Monitor

Асинхронный инструмент для проверки доступности сайтов с **CLI** и **FastAPI** интерфейсом.  
Stage 1 — параллельная проверка, таймауты, валидация, Swagger UI и тесты.

Проект идеально подойдёт, если нужно:
- проверить список сайтов на доступность;
- замерить время ответа;
- следить за аптаймом с заданным интервалом (CLI monitor);
- использовать HTTP API для интеграции с другими сервисами.

---

## 🚀 Возможности Stage 1

- ⚡ Асинхронная проверка сайтов (`aiohttp` + `asyncio.gather()`)
- 💻 **CLI**: режимы `check` (одноразово) и `monitor` (интервал)
- 🌐 **FastAPI** с двумя endpoint:
  - `POST /api/v1/check` — проверка одного URL
  - `POST /api/v1/check/batch` — параллельная проверка до 50 URL (одна ClientSession)
- 📚 Автоматическая **Swagger UI** (`/docs`) и **ReDoc** (`/redoc`)
- ⏱️ Настраиваемый таймаут (0.1 – 30 секунд, валидация через Pydantic)
- 📦 Batch-ограничение (1 – 50 URL, валидация через Pydantic)
- 📄 Загрузка сайтов из файла или аргументов CLI
- 🧠 Умное добавление `https://`, если протокол не указан
- ✅ 37 **pytest-тестов** с mock (без внешнего интернета)

---

## 📦 Установка

```bash
git clone https://github.com/yourname/async-site-monitor.git
cd async-site-monitor
```

Установи зависимости:

```bash
pip install -r requirements.txt
```

> Python **3.9+** рекомендуется

---

## 🧑‍💻 CLI — Терминал

### 🔍 Одноразовая проверка сайтов

```bash
python monitor.py check google.com github.com
```

или из файла, с указанием таймаута:

```bash
python monitor.py check --file sites.txt --timeout 10
```

---

### 📡 Мониторинг сайтов (циклическая проверка)

Проверка сайтов с интервалом (по умолчанию — 300 секунд):

```bash
python monitor.py monitor google.com github.com
```

С указанием интервала и таймаута:

```bash
python monitor.py monitor --file sites.txt --interval 60 --timeout 15
```

---

## 📄 Формат файла `sites.txt`

```text
# Комментарии игнорируются
google.com
https://github.com
example.org
```

---

## 🌐 FastAPI — HTTP API

Запусти сервер:

```bash
uvicorn app.main:app --reload
```

Открой Swagger UI: **http://127.0.0.1:8000/docs**

---

### `GET /` — Корень API

**Response:**
```json
{
  "message": "Async Site Monitor",
  "stage": 1,
  "docs": "/docs"
}
```

---

### `POST /api/v1/check` — Один URL

**Request:**
```json
{
  "url": "https://example.com",
  "timeout": 5
}
```

- `url` (HttpUrl) — **обязательный**
- `timeout` (0.1 – 30) — по умолчанию `5`

**Response 200:**
```json
{
  "status": "OK",
  "time": 123.4,
  "code": 200
}
```

Возможные статусы:
| status    | Описание                                         |
|-----------|--------------------------------------------------|
| `OK`      | HTTP 200                                         |
| `ERROR`   | HTTP 4xx / 5xx (но **не** HTTP 4xx/5xx нашего API) |
| `TIMEOUT` | Превышен таймаут                                 |
| `FAIL`    | Ошибка соединения (включает поле `error`)        |

> ⚠️ Внешний 500/404 сайта → наш API всё равно отвечает **HTTP 200**, статус в `status`.

---

### `POST /api/v1/check/batch` — Много URL (параллельно)

**Request:**
```json
{
  "urls": ["https://example.com", "https://google.com"],
  "timeout": 5
}
```

- `urls` (массив HttpUrl) — **обязательный**, 1 – 50 URL
- `timeout` (0.1 – 30) — по умолчанию `5`

**Response 200:**
```json
[
  { "status": "OK", "time": 123.4, "code": 200 },
  { "status": "OK", "time": 150.2, "code": 200 }
]
```

Каждый URL проверяется параллельно через **одну** `aiohttp.ClientSession` + `asyncio.gather()`.

---

### Ошибки валидации → HTTP 422

Примеры запросов, которые FastAPI отклонит автоматически:

```json
{ "url": "https://x.com", "timeout": -1 }  → 422 (timeout > 0)
{ "url": "https://x.com", "timeout": 0 }   → 422
{ "url": "https://x.com", "timeout": 31 }  → 422 (timeout ≤ 30)
{ "urls": [], "timeout": 5 }               → 422 (batch не пустой)
{ "urls": [50+ URL...], "timeout": 5 }     → 422 (batch не больше 50)
```

---

## 📊 Пример вывода CLI

```text
Checking 3 sites...
Starting parallel checks...
[OK 120ms] https://google.com
[ERROR 502 340ms] https://example.org
[TIMEOUT 5000ms] https://slow-site.com
✅ 1/3 OK
```

### Статусы CLI совпадают с API:
- `OK` — HTTP 200
- `ERROR` — HTTP 4xx / 5xx
- `TIMEOUT` — превышен таймаут
- `FAIL` — ошибка соединения (показывается `error`)

---

## 🧪 Тесты

Все тесты используют mock-объекты — **реальные сетевые вызовы отсутствуют**.

```bash
pytest -v
```

Результат последнего запуска: **37 passed**

### Покрытые кейсы:
#### Checker (`tests/test_checker.py`)
- `200 → OK`
- `500 → ERROR`
- `TimeoutError → TIMEOUT`
- `ConnectionError → FAIL`
- переданный `timeout` действительно передаётся в `aiohttp.ClientTimeout`
- `one_time_check` и `monitor_loop` передают timeout дальше
- `load_sites` (аргументы, файл, комментарии, FileNotFoundError)

#### API (`tests/test_api.py`)
- `GET /` работает
- `POST /api/v1/check` принимает и возвращает структуру
- `timeout` передаётся из API в `check_site()`
- внешний HTTP 500 сайта → наш API отвечает HTTP 200 (не перепутываем статусы)
- валидация `timeout`: `-1 / 0 / 31 / 100 → 422`; `0.1 / 5 / 10 / 30 → 200`
- `POST /api/v1/check/batch` принимает URL, возвращает массив
- batch: `timeout` передаётся каждому URL
- batch: пустой массив → 422, 51 URL → 422, ровно 50 → OK
- batch: валидация timeout такая же

#### CLI (`tests/test_cli.py`)
- `parse_args` (команды check/monitor, --file, --interval)
- `main()`: нормальный запуск и пустой список сайтов → SystemExit

---

## 🗂️ Структура проекта

```
AsyncMonitor/
├── app/
│   ├── main.py                 # FastAPI приложение + endpoints
│   ├── cli.py                  # CLI + печать результатов
│   ├── schemas/
│   │   └── monitor.py          # Pydantic CheckRequest/Response/Batch
│   └── monitoring/
│       └── checker.py          # check_site(), one_time_check(), monitor_loop()
├── tests/
│   ├── conftest.py
│   ├── test_checker.py
│   ├── test_api.py             # Новые API-тесты (httpx + ASGITransport)
│   └── test_cli.py
├── requirements.txt
├── pytest.ini
├── monitor.py                  # Entrypoint для CLI
└── sites.txt                   # Пример списка сайтов
```

---

## 🛣️ Roadmap (следующие этапы)

- Stage 2: **SQLAlchemy + PostgreSQL** (хранение результатов проверок)
- Alembic (миграции)
- Stage 3: **Redis** + background workers (Celery / ARQ)
- Stage 4: **JWT авторизация** + пользователи
- Stage 5: Telegram notifications, система incidents, статистика
- Docker / docker-compose

---

## ✅ Stage 1 ГОТОВ

Проект готов к переходу на Stage 2 — **SQLAlchemy + PostgreSQL**.
