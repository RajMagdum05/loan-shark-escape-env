import sys
import os
from fastapi import FastAPI, HTTPException, Body
from typing import Dict, Any

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from environment import LoanSharkEnvironment
from models import LoanSharkAction, LoanSharkObservation

app = FastAPI(title="Loan Shark Escape API")

# Initialize environment
env = LoanSharkEnvironment()

@app.post("/reset")
async def reset(payload: Dict[str, str] = Body(...)):
    task_id = payload.get("task_id", "lse-medium")
    try:
        obs_payload = env.reset(task_id)
        return obs_payload
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/step")
async def step(payload: Dict[str, Any] = Body(...)):
    action_val = payload.get("action")
    if action_val is None:
        raise HTTPException(status_code=400, detail="Action required")
    
    try:
        result = env.step(int(action_val))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/state")
async def get_state():
    if env.state is None:
        raise HTTPException(status_code=400, detail="Environment not initialized")
    return env.state

@app.post("/evaluate")
async def evaluate():
    if env.state is None:
        raise HTTPException(status_code=400, detail="Environment not initialized")
    
    score = env.evaluate()
    return {
        "reward": score,
        "total_fees_paid": env.state["total_interest_paid"],
        "baseline_fees": env.baseline_fees,
        "all_loans_cleared": all(l["balance"] <= 0 for l in env.state["loans"]),
        "spiral_lock_triggered": env.state["spiral_lock"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
