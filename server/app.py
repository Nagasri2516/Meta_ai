# server/app.py
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import uvicorn

from smart_waste_env.environment import SmartWasteEnvironment
from smart_waste_env.models import SmartWasteAction, SmartWasteObservation

# Configure logging to show everything
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global environment instance
_env: SmartWasteEnvironment = None
_current_task: str = None

print("="*50)
print("Starting Smart Waste Environment Server...")
print("="*50)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for startup/shutdown"""
    global _env
    logger.info("Smart Waste Environment starting up...")
    print("🚀 Server is starting...")
    _env = SmartWasteEnvironment()
    yield
    logger.info("Smart Waste Environment shutting down.")
    print("👋 Server is shutting down...")


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
    """Reset the environment"""
    global _env, _current_task
    
    print(f"📡 Reset request received for task: {task}")
    
    valid_tasks = ["easy", "medium", "hard"]
    if task not in valid_tasks:
        raise HTTPException(
            status_code=422, 
            detail=f"Invalid task '{task}'. Choose from {valid_tasks}"
        )
    
    _current_task = task
    logger.info(f"Resetting environment with task: {task}")
    
    observation, reward, done, info = _env.reset(task=task)
    
    return {
        "observation": observation.dict(),
        "reward": reward,
        "done": done,
        "info": info,
        "task": task
    }


@app.post("/step")
async def step(action: SmartWasteAction):
    """Take an action"""
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


# OpenEnv requires this
main = app

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚛 Smart Waste Management Environment")
    print("="*50)
    print(f"📡 Server will start at: http://127.0.0.1:8000")
    print(f"📚 API Docs: http://127.0.0.1:8000/docs")
    print(f"❤️  Health Check: http://127.0.0.1:8000/health")
    print("="*50)
    print("\n✨ Server is starting...\n")
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info",
        access_log=True
    )