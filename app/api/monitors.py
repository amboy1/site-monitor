from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.monitor import MonitorResponse, MonitorCreate
from app.db.crud import create_monitor, get_monitors, get_monitor_by_id, delete_monitor

router = APIRouter(prefix="/monitors", tags=["Monitors"])

@router.post("/", response_model=MonitorResponse, summary="Create a new monitor")
async def add_monitor(monitor_input: MonitorCreate, db: AsyncSession = Depends(get_db)):
    monitor = await create_monitor(db=db, monitor_input=monitor_input)
    return monitor 

@router.get("/", response_model=list[MonitorResponse], summary="Get list of monitors")
async def list_monitors(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    monitors = await get_monitors(db=db, skip=skip, limit=limit)
    return monitors

@router.get("/{monitor_id}", response_model=MonitorResponse, summary="Get a specific monitor by ID")
async def read_monitor(monitor_id: int, db: AsyncSession = Depends(get_db)):
    monitor = await get_monitor_by_id(db=db, monitor_id=monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return monitor

@router.delete("/{monitor_id}", summary="Delete a monitor by ID")
async def remove_monitor(monitor_id: int, db: AsyncSession = Depends(get_db)):
    monitor = await delete_monitor(db=db, monitor_id=monitor_id)

    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return {"message": "Monitor successfully deleted", "id": monitor_id}