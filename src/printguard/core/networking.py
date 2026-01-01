import time
import asyncio
import httpx
from pydantic import BaseModel, HttpUrl, Field
from typing import Any, Dict, Optional
from .config import settings

class ClientConfig(BaseModel):
    """Configuration model for the client initialization."""
    max_retries: int = Field(default=3, ge=0)
    initial_delay: float = Field(default=0.5, gt=0)

class RequestParams(BaseModel):
    """Input model for the HTTP request."""
    url: HttpUrl
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    json_data: Optional[Dict[str, Any]] = None
    timeout: float = 10.0

class ResponseData(BaseModel):
    """Output model for the HTTP response."""
    status_code: Optional[int]
    content: Any
    is_success: bool

class SafeHttpClient:
    def __init__(self, config: ClientConfig):
        self.max_retries = config.max_retries
        self.initial_delay = config.initial_delay

    def _get_delay(self, attempt: int) -> float:
        """Calculates exponential backoff delay."""
        return self.initial_delay * (2 ** attempt)

    def run_sync(self, params: RequestParams) -> ResponseData:
        """Synchronous request with retries"""
        with httpx.Client() as client:
            for attempt in range(self.max_retries + 1):
                try:
                    resp = client.request(
                        method=params.method,
                        url=str(params.url),
                        headers=params.headers,
                        params=params.params,
                        json=params.json_data,
                        timeout=params.timeout
                    )
                    resp.raise_for_status()
                    return ResponseData(status_code=resp.status_code, content=resp.json(), is_success=True)
                
                except (httpx.HTTPStatusError, httpx.RequestError) as e:
                    if attempt == self.max_retries:
                        return ResponseData(status_code=None, content={"error": str(e)}, is_success=False)
                    time.sleep(self._get_delay(attempt))

    async def run_async(self, params: RequestParams) -> ResponseData:
        """Asynchronous request with retries."""
        async with httpx.AsyncClient() as client:
            for attempt in range(self.max_retries + 1):
                try:
                    resp = await client.request(
                        method=params.method,
                        url=str(params.url),
                        headers=params.headers,
                        params=params.params,
                        json=params.json_data,
                        timeout=params.timeout
                    )
                    resp.raise_for_status()
                    return ResponseData(status_code=resp.status_code, content=resp.json(), is_success=True)
                
                except (httpx.HTTPStatusError, httpx.RequestError) as e:
                    if attempt == self.max_retries:
                        return ResponseData(status_code=None, content={"error": str(e)}, is_success=False)
                    await asyncio.sleep(self._get_delay(attempt))

http_client = SafeHttpClient(ClientConfig(max_retries=settings.MAX_RETRIES, initial_delay=settings.INITIAL_DELAY))