# server/app.py - Complete working version for Hugging Face Space
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# ============================================
# Models
# ============================================
class Bin(BaseModel):
    pos: List[int]
    fill: float
    priority: Optional[int] = 1

class SmartWasteObservation(BaseModel):
    truck_position: List[int]
    bins: List[Bin]
    fuel: int

class SmartWasteAction(BaseModel):
    action_type: str
    direction: Optional[str] = None

# ============================================
# Environment Class
# ============================================
class SmartWasteEnvironment:
    def __init__(self):
        self.truck_position = [0, 0]
        self.fuel = 50
        self.done = False
        self.step_count = 0
        self.total_reward = 0
        self.bins_data = []
        self.current_task = None

    def reset(self, task: str = "easy"):
        print(f"Resetting with task: {task}")
        
        self.truck_position = [0, 0]
        self.fuel = 50
        self.done = False
        self.step_count = 0
        self.total_reward = 0
        self.current_task = task
        
        if task == "easy":
            self.bins_data = [
                {"pos": [1, 1], "fill": 0.5, "priority": 1},
                {"pos": [2, 2], "fill": 0.6, "priority": 1}
            ]
        elif task == "medium":
            self.bins_data = [
                {"pos": [2, 2], "fill": 0.7, "priority": 1},
                {"pos": [3, 3], "fill": 0.8, "priority": 1},
                {"pos": [4, 4], "fill": 0.5, "priority": 1}
            ]
        elif task == "hard":
            self.bins_data = [
                {"pos": [2, 2], "fill": 0.9, "priority": 2},
                {"pos": [3, 3], "fill": 0.8, "priority": 2},
                {"pos": [4, 4], "fill": 0.9, "priority": 1},
                {"pos": [5, 5], "fill": 0.7, "priority": 1},
                {"pos": [6, 6], "fill": 0.8, "priority": 2}
            ]
        else:
            self.bins_data = [
                {"pos": [2, 2], "fill": 0.5, "priority": 1},
                {"pos": [4, 4], "fill": 0.7, "priority": 1}
            ]
        
        bins = [Bin(**bin_data) for bin_data in self.bins_data]
        
        observation = SmartWasteObservation(
            truck_position=self.truck_position,
            bins=bins,
            fuel=self.fuel
        )
        
        return observation, 0.0, False, {}

    def step(self, action: SmartWasteAction):
        reward = -1.0
        self.total_reward += reward
        self.step_count += 1
        
        if action.action_type == "MOVE" and action.direction:
            if action.direction == "RIGHT":
                self.truck_position[0] += 1
            elif action.direction == "LEFT":
                self.truck_position[0] -= 1
            elif action.direction == "UP":
                self.truck_position[1] += 1
            elif action.direction == "DOWN":
                self.truck_position[1] -= 1
        
        self.fuel -= 1
        
        if self.fuel <= 0 or self.step_count >= 50:
            self.done = True
        
        bins = [Bin(**bin_data) for bin_data in self.bins_data]
        
        observation = SmartWasteObservation(
            truck_position=self.truck_position,
            bins=bins,
            fuel=self.fuel
        )
        
        info = {
            "total_reward": self.total_reward,
            "steps": self.step_count,
            "overflow_count": 0
        }
        
        return observation, reward, self.done, info

# ============================================
# FastAPI App - NO REDIRECTS
# ============================================
app = FastAPI(title="Smart Waste Management Environment")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global environment instance
_env = SmartWasteEnvironment()

# ============================================
# API Endpoints - All return JSON directly
# ============================================

@app.get("/")
async def root():
    """Root endpoint - shows API info"""
    return {
        "name": "Smart Waste Management Environment",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "reset": "POST /reset?task=easy|medium|hard",
            "step": "POST /step with body: {\"action_type\":\"MOVE\",\"direction\":\"RIGHT\"}"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "environment": "smart_waste_env"}

@app.post("/reset")
async def reset(task: str = "easy"):
    """Reset the environment with a specific task"""
    global _env
    
    valid_tasks = ["easy", "medium", "hard"]
    if task not in valid_tasks:
        raise HTTPException(status_code=422, detail=f"Invalid task '{task}'. Choose from {valid_tasks}")
    
    _env = SmartWasteEnvironment()
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
        "task": _env.current_task,
        "truck_position": _env.truck_position,
        "fuel": _env.fuel,
        "done": _env.done,
        "steps_taken": _env.step_count,
        "total_reward": _env.total_reward,
        "num_bins": len(_env.bins_data)
    }

# ============================================
# Run the server
# ============================================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)