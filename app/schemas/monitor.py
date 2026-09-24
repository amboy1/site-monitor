from datetime import datetime
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

class MonitorCreate(BaseModel):
    name: str
    url: HttpUrl
    timeout: float = Field(default=5, gt=0, le=30, description="Request timeout in seconds (0 < timeout ≤ 30)")
    interval: int = Field(default=60, gt=0, le=60 * 60 * 24 * 30, description="Check interval in seconds (0 < interval ≤ 30 days)")
    is_active: bool = Field(default=True)

class MonitorResponse(BaseModel):
    id: int
    name: str
    url: HttpUrl
    timeout: float
    interval: int
    is_active: bool
    created_at: datetime
    user_id: int
    
