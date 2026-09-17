from fastapi import FastAPI

from app.schemas.monitor import CheckRequest, CheckResponse, CheckBatchRequest
from app.monitoring.checker import check_site
import aiohttp
import asyncio

app = FastAPI(
    title="Async Site Monitor API",
    description="Stage 1: Asynchronous website availability checker with batch support, configurable timeouts, and parallel request execution.",
    version="0.1.0 (Stage 1)",
)

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
