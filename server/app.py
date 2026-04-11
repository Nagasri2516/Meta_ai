# server/app.py - Standalone version for HF Spaces
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os

# ============================================
# Define models directly in this file
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
# Environment class directly in this file
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
# Create FastAPI app
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

@app.get("/")
async def root():
    return {"message": "Smart Waste Management Environment", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "ok", "environment": "smart_waste_env"}

@app.post("/reset")
async def reset(task: str = "easy"):
    global _env
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
    global _env
    observation, reward, done, info = _env.step(action)
    return {
        "observation": observation.model_dump(),
        "reward": reward,
        "done": done,
        "info": info
    }

# ============================================
# This is the key - the server must run and block
# ============================================
# server/app.py - Use port 8080
if __name__ == "__main__":
    # Try port 5000 (often free)
    port = 5000
    print(f"Starting server on port {port}...")
    print(f"Health check: http://127.0.0.1:{port}/health")
    
    uvicorn.run(
        app, 
        host="127.0.0.1",
        port=port,
        log_level="info"
    )