# 🌐 Async Site Monitor

Асинхронный CLI-инструмент для проверки доступности сайтов и их мониторинга во времени.  
Быстро, параллельно и без лишнего шума.

Проект идеально подойдёт, если нужно:
- проверить список сайтов на доступность;
- замерить время ответа;
- следить за аптаймом с заданным интервалом;
- использовать всё это из терминала.

---

## 🚀 Возможности

- ⚡ Асинхронная проверка сайтов (`aiohttp + asyncio`)
- 🔁 Два режима работы: **check** и **monitor**
- ⏱️ Измерение времени ответа (ms)
- 📄 Загрузка сайтов из файла или аргументов CLI
- 🧠 Умное добавление `https://`, если протокол не указан
- 🛑 Таймауты и обработка ошибок
- 📊 Наглядный вывод статусов в консоль

---

## 📦 Установка

```bash
git clone https://github.com/yourname/async-site-monitor.git
cd async-site-monitor
```

Установи зависимости:

```bash
pip install requirements.txt
```

> Python **3.9+** рекомендуется

---

## 🧑‍💻 Использование

### 🔍 Одноразовая проверка сайтов

```bash
python monitor.py check google.com github.com
```

или из файла:

```bash
python monitor.py check --file sites.txt
```

---

### 📡 Мониторинг сайтов

Проверка сайтов с интервалом (по умолчанию — 300 секунд):

```bash
python monitor.py monitor google.com github.com
```

С указанием интервала:

```bash
python monitor.py monitor --file sites.txt --interval 60
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

## 📊 Пример вывода

```text
Checking 3 sites...
Starting parallel checks...
[OK 120ms] https://google.com
[ERROR 502 340ms] https://example.org
[TIMEOUT 5000ms] https://slow-site.com
✅ 1/3 OK
```

### Статусы:
- `OK` — сайт доступен (HTTP 200)
- `ERROR` — сайт ответил, но с ошибкой (4xx / 5xx)
- `TIMEOUT` — превышен таймаут ожидания
- `FAIL` — ошибка соединения или другая проблема

---

## 🧪 Тесты

Файл `test_monitor.py` предназначен для тестирования логики мониторинга  
(можно использовать `pytest`).

---

## 🛠️ Внутри проекта

- `monitor.py` — основной CLI-скрипт
- `test_monitor.py` — тесты
- `asyncio.gather` — параллельные запросы
- `argparse` — удобный CLI интерфейс

---
