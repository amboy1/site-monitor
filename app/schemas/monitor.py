from pydantic import BaseModel, HttpUrl


class CheckRequest(BaseModel):
    url: HttpUrl
    timeout: float = 5

