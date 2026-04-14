---
title: Smart Waste Management RL Environment
emoji: ♻️
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
tags:
  - openenv
  - reinforcement-learning
  - smart-city
---

# ♻️ Smart Waste Management — OpenEnv Environment

A reinforcement learning environment where an AI agent controls a waste collection truck to empty bins efficiently while managing fuel.

---

## 🚀 What it does

- **State**: truck position, fuel level, bin locations and fill levels
- **Actions**: move up, down, left, or right
- **Reward**: -1 per move, +10 for emptying a bin, penalty for overflow
- **Tasks**: Easy (2 bins), Medium (5 bins), Hard (10 bins with priorities)

---

## 📦 Project Structure

```
smart-waste-ai/
├── server/app.py          # FastAPI server (health, reset, step)
├── smart_waste_env/
│   ├── environment.py     # RL environment logic
│   ├── models.py          # Pydantic models
│   ├── tasks.py           # easy/medium/hard configurations
│   └── grader.py          # Score function (0-1)
├── inference.py           # Runs agent with structured output
├── openenv.yaml           # OpenEnv manifest
├── requirements.txt
├── Dockerfile
└── pyproject.toml
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/reset?task=easy` | Reset environment |
| POST | `/step` | Move truck (body: `{"action_type":"MOVE","direction":"RIGHT"}`) |
| GET | `/state` | Current environment state |

Interactive docs: `/docs`

---

## ⚡ Quick Start

### Local

```bash
# Setup
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install -e .

# Run server
python server/app.py

# In another terminal, run inference
python inference.py
```

### Docker

```bash
docker build -t smart-waste .
docker run -p 8000:8000 smart-waste
```

### Hugging Face Space

Push this repo to a Space with **Docker** SDK. The Space will auto‑deploy.

---

## 🧪 OpenEnv Validation

Passes all checks:

- `main()` function in `server/app.py`
- `pyproject.toml` with `[project.scripts]`
- `uv.lock` present
- 3 tasks defined in `openenv.yaml`
- Structured output `[START]` / `[STEP]` / `[END]`
- LLM proxy support (`API_BASE_URL`, `API_KEY`)

---

## 🔧 Environment Variables

| Variable | Purpose |
|----------|---------|
| `PORT` | Server port (default 8000) |
| `API_BASE_URL` | LiteLLM proxy URL (hackathon injects) |
| `API_KEY` | Auth key for proxy (hackathon injects) |
| `MODEL_NAME` | Model name (e.g., `Qwen/Qwen2.5-72B-Instruct`) |

---

## 📄 License

MIT
```

This version is clean, easy to scan, and contains everything a judge or user needs to understand and run your project. No fluff.
