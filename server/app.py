# server/app.py
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from smart_waste_env.environment import SmartWasteEnvironment
from smart_waste_env.models import SmartWasteAction, SmartWasteObservation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global environment instance
_env: SmartWasteEnvironment = None
_current_task: str = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for startup/shutdown"""
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def root():
    """Redirect to API docs"""
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "version": "1.0.0", "environment": "smart_waste_env"}


@app.post("/reset")
async def reset(task: str = "easy"):
    """
    Reset the environment with a specific task difficulty.
    
    Parameters:
    - task: "easy", "medium", or "hard"
    
    Returns initial observation and state.
    """
    global _env, _current_task
    
    valid_tasks = ["easy", "medium", "hard"]
    if task not in valid_tasks:
        raise HTTPException(
            status_code=422, 
            detail=f"Invalid task '{task}'. Choose from {valid_tasks}"
        )
    
    _current_task = task
    logger.info(f"Resetting environment with task: {task}")
    
    # Reset the environment
    observation, reward, done, info = _env.reset(task=task)
    
    # Convert Pydantic model to dict for response
    return {
        "observation": observation.dict(),
        "reward": reward,
        "done": done,
        "info": info,
        "task": task
    }


@app.post("/step")
async def step(action: SmartWasteAction):
    """
    Take an action in the environment.
    
    Body: { "action_type": "MOVE", "direction": "RIGHT" }
    
    Returns observation, reward, done flag, and additional info.
    """
    global _env
    
    if _env is None:
        raise HTTPException(
            status_code=400, 
            detail="Environment not initialized. Call /reset first."
        )
    
    try:
        observation, reward, done, info = _env.step(action)
        
        return {
            "observation": observation.dict(),
            "reward": reward,
            "done": done,
            "info": info
        }
    except Exception as e:
        logger.exception("Error during step")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state")
async def get_state():
    """Get current environment state"""
    global _env, _current_task
    
    if _env is None:
        raise HTTPException(
            status_code=400, 
            detail="Environment not initialized. Call /reset first."
        )
    
    return {
        "task": _current_task,
        "truck_position": _env.truck_position,
        "fuel": _env.fuel,
        "done": _env.done,
        "steps_taken": getattr(_env, 'step_count', 0),
        "total_reward": getattr(_env, 'total_reward', 0),
        "num_bins": len(getattr(_env, 'bins_data', []))
    }


@app.get("/openapi.json")
async def get_openapi():
    """Return OpenAPI schema"""
    return app.openapi()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)