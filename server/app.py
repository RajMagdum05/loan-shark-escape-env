from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from server.environment import LoanSharkEnvironment
from models import LoanSharkAction, LoanSharkObservation

app = FastAPI(title="Loan Shark Escape API")

# Global environment instance
env = LoanSharkEnvironment()

class ResetRequest(BaseModel):
    task_id: str

class ActionRequest(BaseModel):
    action: int

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/reset")
async def reset(request: ResetRequest):
    try:
        observation = env.reset(request.task_id)
        return observation
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Task {request.task_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/step")
async def step(request: ActionRequest):
    if env.state is None:
        raise HTTPException(status_code=400, detail="Environment not reset")
    
    try:
        observation, reward, done = env.step(request.action)
        return {
            "observation": observation,
            "reward": reward,
            "done": done
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/state")
async def get_state():
    if env.state is None:
        raise HTTPException(status_code=400, detail="Environment not reset")
    return env._get_observation()

@app.post("/evaluate")
async def evaluate():
    try:
        score = env.evaluate()
        return {"score": score}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
