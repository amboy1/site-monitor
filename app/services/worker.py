import asyncio
import aiohttp
from datetime import datetime, timezone
from sqlalchemy import select

from app.db.database import SessionLocal  # Импортируем твой SessionLocal
from app.db.models import Monitor, MonitorCheck

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

async def ping_one_monitor(http_session: aiohttp.ClientSession, monitor: Monitor) -> dict:
    """Пингует конкретный монитор и возвращает результаты."""
    start_time = asyncio.get_event_loop().time()
    try:
        async with http_session.get(
            monitor.url, 
            headers=HEADERS, 
            timeout=aiohttp.ClientTimeout(total=monitor.timeout)
        ) as response:
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            if response.status == 200:
                return {"monitor": monitor, "status": "OK", "time": elapsed, "status_code": response.status, "error": None}
            return {"monitor": monitor, "status": "ERROR", "time": elapsed, "status_code": response.status, "error": f"HTTP {response.status}"}
    except asyncio.TimeoutError:
        elapsed = monitor.timeout * 1000
        return {"monitor": monitor, "status": "TIMEOUT", "time": elapsed, "status_code": None, "error": "Request timed out"}
    except Exception as e:
        return {"monitor": monitor, "status": "FAIL", "time": 0.0, "status_code": None, "error": str(e)}

async def check_monitors():
    """Достает все активные мониторы и пингует их параллельно."""
    async with SessionLocal() as db:
        result = await db.execute(select(Monitor).where(Monitor.is_active == True))
        monitors = result.scalars().all()

        if not monitors:
            return

        # Создаем асинхронную сессию для HTTP-запросов
        async with aiohttp.ClientSession() as http_session:
            # Запускаем пинг всех сайтов одновременно
            tasks = [ping_one_monitor(http_session, monitor) for monitor in monitors]
            results = await asyncio.gather(*tasks)

            # Обновляем данные в объектах и сохраняем в базу
            for res in results:
                m = res["monitor"]
                m.last_status = res["status"]
                m.last_response_time = res["time"]
                m.last_error = res["error"]
                m.last_checked = datetime.now(timezone.utc).replace(tzinfo=None)
                
                check = MonitorCheck(
                    monitor_id=m.id,
                    status=res["status"],
                    response_time=res["time"],
                    status_code=res["status_code"],
                    error=res["error"],
                    checked_at=m.last_checked
                )
                db.add(check)

            await db.commit()

async def start_monitoring_loop():
    """Бесконечный цикл фонового воркера."""
    while True:
        try:
            await check_monitors()
        except Exception as e:
            print(f"Ошибка в цикле мониторинга: {e}")
        
        # Интервал между проверками (например, каждые 30 секунд)
        await asyncio.sleep(30)