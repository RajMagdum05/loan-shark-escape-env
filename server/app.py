from __future__ import annotations

import json

from fastapi import FastAPI
from starlette.requests import Request
import uvicorn

from models import LoanAction, LoanActionRequest
from server.environment import LoanSharkEnvironment

app = FastAPI(
    title="Loan Shark Escape Environment",
    description="OpenEnv-style debt-trap simulation: reset, step, state, evaluate.",
    version="1.0.0",
)
environment = LoanSharkEnvironment()


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "service": "loan-shark-escape-env"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "loan-shark-escape-env"}


@app.post("/reset")
async def reset(request: Request):
    task_id = "lse-easy"
    try:
        body = await request.body()
        if body:
            data = json.loads(body)
            if isinstance(data, dict) and data.get("task_id"):
                tid = data["task_id"]
                if isinstance(tid, str) and tid.strip():
                    task_id = tid.strip()
    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    return environment.reset(task_id)


@app.post("/step")
def step(body: LoanActionRequest):
    action = LoanAction(action_type=body.action_type.strip().lower(), amount=body.amount)
    return environment.step(action)


@app.get("/state")
def state():
    return environment.get_state()


@app.post("/evaluate")
def evaluate():
    return environment.evaluate()


def main() -> None:
    """Entry point for the fraud environment server."""
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
