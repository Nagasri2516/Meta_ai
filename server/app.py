# server/app.py (corrected step endpoint)
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import uvicorn

from smart_waste_env.environment import SmartWasteEnvironment
from smart_waste_env.models import SmartWasteAction, SmartWasteObservation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_env: SmartWasteEnvironment = None
_current_task: str = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _env
    logger.info("Smart Waste Environment starting up...")
    _env = SmartWasteEnvironment()
    yield
    logger.info("Smart Waste Environment shutting down.")

app = FastAPI(
    title="Smart Waste Management Environment",
    description="RL environment for smart waste collection optimization",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "environment": "smart_waste_env"}

@app.post("/reset")
async def reset(task: str = "easy"):
    global _env, _current_task
    
    valid_tasks = ["easy", "medium", "hard"]
    if task not in valid_tasks:
        raise HTTPException(status_code=422, detail=f"Invalid task '{task}'")
    
    _current_task = task
    observation, reward, done, info = _env.reset(task=task)
    
    # Use model_dump instead of dict (fixes the deprecation warning)
    return {
        "observation": observation.model_dump(),
        "reward": reward,
        "done": done,
        "info": info,
        "task": task
    }

@app.post("/step")
async def step(action: SmartWasteAction):
    """Take an action - expects JSON like {"action_type": "MOVE", "direction": "RIGHT"}"""
    global _env
    
    if _env is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    
    try:
        observation, reward, done, info = _env.step(action)
        
        return {
            "observation": observation.model_dump(),
            "reward": reward,
            "done": done,
            "info": info
        }
    except Exception as e:
        logger.exception("Error during step")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/state")
async def get_state():
    global _env, _current_task
    
    if _env is None:
        raise HTTPException(status_code=400, detail="Environment not initialized")
    
    return {
        "task": _current_task,
        "truck_position": _env.truck_position,
        "fuel": _env.fuel,
        "done": _env.done,
        "steps_taken": getattr(_env, 'step_count', 0),
        "total_reward": getattr(_env, 'total_reward', 0),
    }

# ===== REQUIRED FOR OPENENV =====
def main():
    """Main entry point for OpenEnv"""
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()

main_app = app