# server/app.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

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
    return {"status": "reset ok", "task": task}

@app.post("/step") 
async def step(action: dict):
    return {"status": "step ok", "reward": -1.0, "done": False}

def main():
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="127.0.0.1", port=port)

if __name__ == "__main__":
    main()