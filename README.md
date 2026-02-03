🚀 Async Site Monitor
Асинхронный мониторинг сайтов. 100% тесты.

🚀 Быстрый старт
bash
pip install -r requirements.txt
pytest test_monitor.py -v  # 18/18 ✅
python monitor.py check google.com
📋 Использование
bash
# Проверка
python monitor.py check google.com yandex.ru
python monitor.py check --file sites.txt

# Мониторинг (каждые 5 мин)
python monitor.py monitor google.com
python monitor.py monitor --interval 30 --file sites.txt
Вывод:

text
[OK 45ms] https://google.com
[OK 23ms] https://yandex.ru
✅ 2/2 OK
🧪 Тесты (100% покрытие)
bash
pytest test_monitor.py -v           # Все 18 тестов
pytest --cov=monitor test_monitor.py # Покрытие
📦 Установка
bash
git clone <repo>
cd AsyncMonitor
pip install -r requirements.txt
📁 Файлы
text
monitor.py     # Основной код
test_monitor.py # 18 тестов ✅
requirements.txt
pytest.ini
.gitignore
README.md
