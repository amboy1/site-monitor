from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Monitor
from app.schemas.monitor import MonitorCreate

async def create_monitor(db: AsyncSession, monitor_input: MonitorCreate):
    db_monitor = Monitor(
        name=monitor_input.name,
        url=str(monitor_input.url),
        timeout=monitor_input.timeout,
        interval=monitor_input.interval,
        is_active=monitor_input.is_active,
    )
    db.add(db_monitor)
    await db.commit()
    await db.refresh(db_monitor)
    return db_monitor

