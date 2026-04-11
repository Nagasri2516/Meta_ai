# server/app.py
import logging
import sys
import os
from contextlib import asynccontextmanager

# Configure logging immediately at startup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)
logger = logging.getLogger(__name__)

logger.info("="*50)
logger.info("Starting Smart Waste Environment Server")
logger.info("="*50)

# Rest of your imports...
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from smart_waste_env.environment import SmartWasteEnvironment
from smart_waste_env.models import SmartWasteAction, SmartWasteObservation

_env: SmartWasteEnvironment = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _env
    logger.info("Smart Waste Environment starting up...")
    _env = SmartWasteEnvironment()
    logger.info("Environment initialized successfully")
    yield
    logger.info("Smart Waste Environment shutting down.")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    logger.debug("Health check called")
    return {"status": "ok"}

@app.post("/reset")
async def reset(task: str = "easy"):
    logger.info(f"Reset called with task: {task}")
    global _env
    observation, reward, done, info = _env.reset(task=task)
    return {
        "observation": observation.model_dump(),
        "reward": reward,
        "done": done,
        "info": info
    }

@app.post("/step")
async def step(action: SmartWasteAction):
    logger.debug(f"Step called with action: {action.action_type} {action.direction}")
    global _env
    if _env is None:
        raise HTTPException(status_code=400, detail="Call /reset first")
    observation, reward, done, info = _env.step(action)
    return {
        "observation": observation.model_dump(),
        "reward": reward,
        "done": done,
        "info": info
    }

def main():
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    main()