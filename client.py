from __future__ import annotations

import asyncio
from typing import Any, Union

import httpx

try:
    from models import LoanSharkAction
except Exception:  # pragma: no cover
    LoanSharkAction = None  # type: ignore


class LoanSharkEscapeEnv:
    """Async client for Loan Shark Escape OpenEnv server."""

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "LoanSharkEscapeEnv":
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
        return self._client

    async def reset(self, task_id: str) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.post("/reset", json={"task_id": task_id})
        response.raise_for_status()
        return response.json()

    async def step(self, action: Union[LoanSharkAction, dict[str, Any], int]) -> dict[str, Any]:
        client = await self._get_client()
        if LoanSharkAction is not None and isinstance(action, LoanSharkAction):
            payload = action.model_dump()
        elif isinstance(action, dict):
            payload = action
        else:
            payload = {"action": int(action)}

        response = await client.post("/step", json=payload)
        response.raise_for_status()
        return response.json()

    async def evaluate(self) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.post("/evaluate")
        response.raise_for_status()
        return response.json()

    async def state(self) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.get("/state")
        response.raise_for_status()
        return response.json()

    def sync(self, coro):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        raise RuntimeError("sync() cannot be used inside an active event loop. Use await instead.")
