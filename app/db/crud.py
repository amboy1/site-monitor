from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import get_password_hash
from app.db.models import Monitor, User
from app.schemas.monitor import MonitorCreate
from app.schemas.user import UserCreate

async def create_monitor(db: AsyncSession, monitor_input: MonitorCreate, user_id: int = 1):
    db_monitor = Monitor(
        name=monitor_input.name,
        url=str(monitor_input.url),
        timeout=monitor_input.timeout,
        interval=monitor_input.interval,
        is_active=monitor_input.is_active,
        user_id=user_id,
    )
    db.add(db_monitor)
    await db.commit()
    await db.refresh(db_monitor)
    return db_monitor

async def get_monitors(db: AsyncSession, user_id: int | None = None, skip: int = 0, limit: int = 100):
    stmt = select(Monitor)
    if user_id is not None:
        stmt = stmt.where(Monitor.user_id == user_id)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_monitor_by_id(db: AsyncSession, monitor_id: int, user_id: int | None = None):
    stmt = select(Monitor).where(Monitor.id == monitor_id)
    if user_id is not None:
        stmt = stmt.where(Monitor.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def delete_monitor(db: AsyncSession, monitor_id: int, user_id: int | None = None):
    monitor = await get_monitor_by_id(db=db, monitor_id=monitor_id, user_id=user_id)
    if not monitor:
        return None
    await db.delete(monitor)
    await db.commit()
    return monitor


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    db_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user