import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from smart_waste_env.server.environment import SmartWasteEnvironment
from smart_waste_env.models import SmartWasteAction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global environment instance
_env: SmartWasteEnvironment = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _env
    logger.info("Smart Waste Environment starting...")
    _env = SmartWasteEnvironment()
    yield
    logger.info("Smart Waste Environment shutting down...")


app = FastAPI(
    title="Smart Waste Management Environment",
    description=(
        "An OpenEnv-compatible RL environment for optimizing waste collection. "
        "The agent controls a garbage truck to collect waste efficiently while minimizing fuel usage."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS (for Hugging Face / browser access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    return {"status": "ok", "env": "smart-waste"}


# 🔹 RESET
@app.post("/reset")
async def reset(episode_id: str = "test", seed: int = 42):
    global _env
    _env = SmartWasteEnvironment()

    obs = _env.reset(episode_id=episode_id, seed=seed)

    return {
        "observation": obs.dict()
    }


# 🔹 STEP
@app.post("/step")
async def step(action: dict):
    global _env

    if _env is None:
        raise HTTPException(status_code=400, detail="Call /reset first")

    try:
        # convert dict → model
        action_obj = SmartWasteAction(**action["action"])

        obs = _env.step(action_obj)

        return {
            "observation": {
                "truck_position": obs.truck_position,
                "bins": [b.dict() for b in obs.bins],
                "fuel": obs.fuel
            },
            "reward": obs.reward,
            "done": obs.done
        }

    except Exception as e:
        logger.exception("Error in step")
        raise HTTPException(status_code=500, detail=str(e))


# 🔹 STATE (optional)
@app.get("/state")
async def get_state():
    global _env

    if _env is None:
        raise HTTPException(status_code=400, detail="Call /reset first")

    return {
        "truck_position": _env.truck_position,
        "bins": _env.bins,
        "fuel": _env.fuel
    }


# 🔹 MAIN
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)