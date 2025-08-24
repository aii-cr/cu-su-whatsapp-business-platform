# NEW CODE
"""
HTTP cliente compartido con timeouts y reintentos seguros (httpx).
"""

from __future__ import annotations
import asyncio
from typing import Any, Dict, Optional, Tuple
import httpx

_DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=5.0)
_MAX_RETRIES = 3
_BACKOFF_SECS = (0.3, 0.8, 1.5)

class HttpService:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=_DEFAULT_TIMEOUT)

    async def _retry(self, func, *args, **kwargs) -> httpx.Response:
        last_exc: Optional[Exception] = None
        for attempt, backoff in zip(range(_MAX_RETRIES), _BACKOFF_SECS):
            try:
                resp = await func(*args, **kwargs)
                if resp.status_code >= 500:
                    raise httpx.HTTPStatusError("Server error", request=resp.request, response=resp)
                return resp
            except Exception as e:
                last_exc = e
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(backoff)
        if last_exc:
            raise last_exc
        raise RuntimeError("Unexpected retry loop exit")

    async def get_json(self, path: str) -> Tuple[int, Dict[str, Any]]:
        resp = await self._retry(self._client.get, path)
        return resp.status_code, resp.json()

    async def post_json(self, path: str, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        resp = await self._retry(self._client.post, path, json=payload)
        return resp.status_code, resp.json()

# Singleton for Reservations API
reservations_http = HttpService(base_url="http://localhost:8010/api/v1/reservations")
