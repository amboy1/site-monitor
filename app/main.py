from fastapi import FastAPI
from app.schemas.monitor import CheckRequest
from app.monitoring.checker import check_site
import aiohttp
import time

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Async Site Monitor"}

@app.post("/api/v1/check")
async def check(request: CheckRequest):
    async with aiohttp.ClientSession() as session:
        result = await check_site(
            str(request.url),
            session,
        )

    return result