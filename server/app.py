# server/app.py
import os
import sys
import logging
from contextlib import asynccontextmanager

# Add parent directory to path so smart_waste_env can be found
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/reset")
async def reset(task: str = "easy"):
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
    port = int(os.getenv("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()