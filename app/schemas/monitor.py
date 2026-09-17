from pydantic import BaseModel, HttpUrl, Field
from typing import Optional


class CheckRequest(BaseModel):
    url: HttpUrl
    timeout: float = Field(default=5, gt=0, le=30, description="Request timeout in seconds (0 < timeout ≤ 30)")

class CheckResponse(BaseModel):
    status: str
    time: float
    code: int
    error: Optional[str] = None

class CheckBatchRequest(BaseModel):
    urls: list[HttpUrl] = Field(min_length=1, max_length=50, description="List of URLs to check (1-50)")
    timeout: float = Field(default=5, gt=0, le=30, description="Request timeout in seconds (0 < timeout ≤ 30)")
