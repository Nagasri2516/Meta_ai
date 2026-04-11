# inference.py
import os
import requests
import json
import time
from openai import OpenAI

# ============================================
# URL 1: HACKATHON'S LLM PROXY (DO NOT CHANGE)
# ============================================
LLM_API_BASE = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY = os.getenv("API_KEY") or os.getenv("HF_TOKEN")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

# ============================================
# URL 2: YOUR ENVIRONMENT SERVER (CHANGE THIS IF NEEDED)
# ============================================
# For local testing:
ENV_URL = "http://127.0.0.1:8000"
# For Hugging Face Space (uncomment when deploying):
# ENV_URL = "https://nagasri16-hackathon.hf.space"

TASK_NAME = os.getenv("TASK_NAME", "easy")
BENCHMARK = os.getenv("BENCHMARK", "smart_waste_env")
MAX_STEPS = 30

# Initialize OpenAI client with HACKATHON'S proxy (NOT your environment)
client = OpenAI(
    base_url=LLM_API_BASE,  # This calls hackathon's LLM proxy
    api_key=API_KEY,
)

def get_llm_action(observation, step_num, task):
    """
    Use LLM to decide the next action.
    This calls the HACKATHON'S LLM PROXY, not your environment.
    """
    
    truck_pos = observation.get("truck_position", [0, 0])
    fuel = observation.get("fuel", 50)
    bins = observation.get("bins", [])
    
    system_prompt = """You are an AI agent controlling a waste collection truck.
Your goal is to collect waste from bins efficiently while conserving fuel.

Available actions:
- MOVE_UP: Move truck up (increase y coordinate)
- MOVE_DOWN: Move truck down (decrease y coordinate)  
- MOVE_LEFT: Move truck left (decrease x coordinate)
- MOVE_RIGHT: Move truck right (increase x coordinate)

Respond with ONLY the action name (e.g., MOVE_RIGHT) and nothing else."""
    
    user_prompt = f"""Task Difficulty: {task}
Current Step: {step_num}
Truck Position: {truck_pos}
Fuel Remaining: {fuel}
Bins to Collect: {json.dumps(bins)}

Which direction should the truck move?
Respond with ONLY: MOVE_UP, MOVE_DOWN, MOVE_LEFT, or MOVE_RIGHT"""
    
    try:
        # This calls the HACKATHON'S LLM PROXY
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=20,
            timeout=10
        )
        
        action = completion.choices[0].message.content.strip().upper()
        
        valid_actions = ["MOVE_UP", "MOVE_DOWN", "MOVE_LEFT", "MOVE_RIGHT"]
        if action not in valid_actions:
            if "UP" in action:
                action = "MOVE_UP"
            elif "DOWN" in action:
                action = "MOVE_DOWN"
            elif "LEFT" in action:
                action = "MOVE_LEFT"
            elif "RIGHT" in action:
                action = "MOVE_RIGHT"
            else:
                action = "MOVE_RIGHT"
            
        return action
        
    except Exception as e:
        print(f"[DEBUG] LLM call failed: {e}", flush=True)
        return "MOVE_RIGHT"

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: str = None) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: list) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

def calculate_score(total_reward, steps_taken, max_steps=100):
    max_possible_reward = 0
    min_possible_reward = -max_steps
    
    if total_reward >= 0:
        reward_score = 1.0
    else:
        reward_score = max(0, min(1, (total_reward - min_possible_reward) / (max_possible_reward - min_possible_reward)))
    
    step_score = max(0, 1 - (steps_taken / max_steps))
    score = (reward_score * 0.6) + (step_score * 0.4)
    return round(score, 3)

def main():
    rewards = []
    steps_taken = 0
    success = False
    total_reward = 0
    
    # Log start with required format
    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)
    
    try:
        # Wait for YOUR environment server to be ready
        for i in range(30):
            try:
                resp = requests.get(f"{ENV_URL}/health", timeout=2)
                if resp.status_code == 200:
                    break
            except:
                pass
            time.sleep(1)
        
        # Reset YOUR environment
        response = requests.post(f"{ENV_URL}/reset", params={"task": TASK_NAME}, timeout=10)
        if response.status_code != 200:
            log_step(step=0, action="null", reward=0.0, done=True, error="reset_failed")
        else:
            data = response.json()
            observation = data.get("observation", {})
            
            for step_num in range(1, MAX_STEPS + 1):
                # Get action from LLM (calls hackathon's proxy)
                action = get_llm_action(observation, step_num, TASK_NAME)
                
                # Convert action for YOUR environment
                direction = action.replace("MOVE_", "")
                
                # Execute action on YOUR environment
                response = requests.post(
                    f"{ENV_URL}/step",
                    json={"action_type": "MOVE", "direction": direction},
                    timeout=10
                )
                
                if response.status_code != 200:
                    log_step(step=step_num, action=action, reward=0.0, done=False, error="step_failed")
                    break
                
                data = response.json()
                reward = data.get("reward", 0.0)
                done = data.get("done", False)
                observation = data.get("observation", {})
                
                total_reward += reward
                rewards.append(reward)
                steps_taken = step_num
                
                # Log step with required format
                log_step(step=step_num, action=action, reward=reward, done=done, error=None)
                
                if done:
                    break
        
        # Calculate final score
        score = calculate_score(total_reward, steps_taken)
        success = steps_taken > 0 and total_reward > -MAX_STEPS
        
    except Exception as e:
        print(f"[DEBUG] Error: {e}", flush=True)
        score = 0.0
        success = False
    
    finally:
        # Log end with required format
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

if __name__ == "__main__":
    main()