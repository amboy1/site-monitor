from fastapi import FastAPI
import aiohttp
import asyncio
from contextlib import asynccontextmanager
from app.api.monitors import router as monitors_router
from app.api.users import router as users_router
from app.api.auth import router as auth_router
from app.schemas.monitor import CheckRequest, CheckResponse, CheckBatchRequest
from app.monitoring.checker import check_site
from app.services.worker import start_monitoring_loop

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Background monitoring worker starting...")
    task = asyncio.create_task(start_monitoring_loop())
    print("Background monitoring worker started!")
    try:
        yield
    finally:
        print("Background monitoring worker stopping...")
        task.cancel()
        print("Background monitoring worker stopped!")

app = FastAPI(
    title="Async Site Monitor API",
    description="Stage 1: Asynchronous website availability checker with batch support, configurable timeouts, and parallel request execution.",
    version="0.1.0 (Stage 1)",
    lifespan=lifespan,
)

app.include_router(monitors_router)
app.include_router(users_router)
app.include_router(auth_router)

@app.get("/", summary="API root")
def read_root():
    return {"message": "Async Site Monitor", "stage": 1, "docs": "/docs"}

@app.post("/api/v1/check", response_model=CheckResponse, summary="Check a single URL")
async def check(request: CheckRequest):
    async with aiohttp.ClientSession() as session:
        result = await check_site(
            str(request.url),
            session,
            request.timeout,
        )

    return result

@app.post("/api/v1/check/batch", response_model=list[CheckResponse], summary="Check multiple URLs in parallel")
async def check_batch(request: CheckBatchRequest):
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*[check_site(str(url), session, request.timeout) for url in request.urls])
    return results

