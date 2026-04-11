from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from models import LoanSharkAction
from server.environment import LoanSharkEnvironment


class ResetRequest(BaseModel):
    task_id: str


app = FastAPI(title="Loan Shark Escape Environment")
environment = LoanSharkEnvironment()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/reset")
def reset(payload: ResetRequest) -> dict:
    try:
        return environment.reset(payload.task_id)
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
