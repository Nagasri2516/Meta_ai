# server/app.py
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import uvicorn

from smart_waste_env.environment import SmartWasteEnvironment
from smart_waste_env.models import SmartWasteAction, SmartWasteObservation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_env: SmartWasteEnvironment = None

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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

@app.get("/health")
async def health():
    return {"status": "ok", "environment": "smart_waste_env"}

@app.post("/reset")
async def reset(task: str = "easy"):
    """Reset the environment with a specific task"""
    global _env
    
    valid_tasks = ["easy", "medium", "hard"]
    if task not in valid_tasks:
        raise HTTPException(status_code=422, detail=f"Invalid task '{task}'. Choose from {valid_tasks}")
    
    logger.info(f"Resetting environment with task: {task}")
    observation, reward, done, info = _env.reset(task=task)
    
    return {
        "observation": observation.model_dump(),
        "reward": reward,
        "done": done,
        "info": info,
        "task": task
    }

@app.post("/step")
async def step(action: SmartWasteAction):
    """Take an action in the environment"""
    global _env
    
    if _env is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    
    logger.debug(f"Step called with action: {action.action_type} {action.direction}")
    observation, reward, done, info = _env.step(action)
    
    return {
        "observation": observation.model_dump(),
        "reward": reward,
        "done": done,
        "info": info
    }

@app.get("/state")
async def get_state():
    """Get current environment state"""
    global _env
    
    if _env is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    
    return {
        "truck_position": _env.truck_position,
        "fuel": _env.fuel,
        "done": _env.done,
        "steps_taken": getattr(_env, 'step_count', 0),
        "total_reward": getattr(_env, 'total_reward', 0),
    }

def main():
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

if __name__ == "__main__":
    main()