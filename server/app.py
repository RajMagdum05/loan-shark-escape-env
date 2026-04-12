from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from models import LoanSharkAction
from server.environment import LoanSharkEnvironment

app = FastAPI(title="Loan Shark Escape Environment")
environment = LoanSharkEnvironment()

# Default when POST /reset has no body (some automated validators send empty body).
DEFAULT_TASK_ID = "lse-easy"


@app.get("/")
def root() -> dict[str, str]:
    """Some deploy probes hit `/` — keep a 200 for Space liveness."""
    return {"status": "ok", "service": "loan-shark-escape-env"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "loan-shark-escape-env"}


@app.post("/reset")
async def reset(request: Request) -> dict:
    """Accept JSON ``{"task_id": "..."}`` or an empty body (defaults to easy task)."""
    task_id = DEFAULT_TASK_ID
    try:
        raw = await request.body()
        if raw:
            data = json.loads(raw.decode("utf-8"))
            if isinstance(data, dict) and data.get("task_id") is not None:
                tid = data["task_id"]
                if isinstance(tid, str) and tid.strip():
                    task_id = tid.strip()
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError):
        pass

    try:
        return environment.reset(task_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/step")
def step(action: LoanSharkAction) -> dict:
    try:
        return environment.step(action.action)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/state")
def state() -> dict:
    try:
        return environment.get_state()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/evaluate")
def evaluate() -> dict:
    try:
        reward = environment.evaluate()
        snapshot = environment.get_state()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "reward": reward,
        "all_loans_cleared": snapshot["all_loans_cleared"],
        "total_fees_paid": round(snapshot["total_fees_paid"], 2),
        "baseline_fees": round(snapshot["baseline_fees"], 2),
        "spiral_lock_triggered": snapshot["spiral_lock"],
        "grader": environment.last_grader_result,
    }
