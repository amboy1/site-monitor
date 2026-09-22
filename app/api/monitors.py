from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.monitor import MonitorResponse, MonitorCreate
from app.db.crud import create_monitor

router = APIRouter(prefix="/monitors", tags=["Monitors"])

@router.post("/", response_model=MonitorResponse, summary="Create a new monitor")
async def add_monitor(monitor_input: MonitorCreate, db: AsyncSession = Depends(get_db)):
    monitor = await create_monitor(db=db, monitor_input=monitor_input)
    return monitor 
