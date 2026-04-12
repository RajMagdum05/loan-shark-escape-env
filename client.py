import httpx
from typing import Any, Dict, Optional

class LoanClient:
    """Standalone client to interact with the Loan Shark Escape API."""
    def __init__(self, base_url: str = "http://localhost:7860"):
        self.base_url = base_url.rstrip("/")

    async def reset(self, task_id: str = "lse-easy") -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/reset", json={"task_id": task_id})
            resp.raise_for_status()
            return resp.json()

    async def step(self, action_type: str, amount: float = 0.0) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/step", json={"action_type": action_type, "amount": amount})
            resp.raise_for_status()
            return resp.json()

    async def evaluate(self) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/evaluate")
            resp.raise_for_status()
            return resp.json()

    async def get_state(self) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/state")
            resp.raise_for_status()
            return resp.json()
