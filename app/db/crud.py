from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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

async def get_monitors(db: AsyncSession, skip: int = 0, limit: int = 100):
    stmt = select(Monitor).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_monitor_by_id(db: AsyncSession, monitor_id: int):
    stmt = select(Monitor).where(Monitor.id == monitor_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def delete_monitor(db: AsyncSession, monitor_id: int):
    monitor = await get_monitor_by_id(db=db, monitor_id=monitor_id)
    if not monitor:
        return None
    await db.delete(monitor)
    await db.commit()
    return monitor