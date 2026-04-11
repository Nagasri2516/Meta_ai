# inference.py
import os
import requests
import json
import time
import urllib3

# Disable SSL warnings for local testing (optional)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================
# HACKATHON'S LLM PROXY (injected during validation)
# ============================================
LLM_API_BASE = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY = os.getenv("API_KEY") or os.getenv("HF_TOKEN")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

# ============================================
# YOUR ENVIRONMENT SERVER
# ============================================
# For local testing
ENV_URL = os.getenv("ENV_URL", "http://127.0.0.1:8000")
# For Hugging Face Space (uncomment when deploying to HF)
# ENV_URL = os.getenv("ENV_URL", "https://Nagasri16-Hackathon.hf.space")

TASK_NAME = os.getenv("TASK_NAME", "easy")
BENCHMARK = os.getenv("BENCHMARK", "smart_waste_env")
MAX_STEPS = 30

HAS_API_KEY = API_KEY is not None

if HAS_API_KEY:
    from openai import OpenAI
    client = OpenAI(base_url=LLM_API_BASE, api_key=API_KEY)
else:
    print("[WARNING] No API_KEY found. Using fallback rule-based actions.", flush=True)
    client = None

def call_environment(action_type, **kwargs):
    """Unified function to call your environment"""
    payload = {"action_type": action_type, **kwargs}
    
    # Try root endpoint first
    try:
        response = requests.post(f"{ENV_URL}/", json=payload, timeout=30, verify=False)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"[DEBUG] Root endpoint failed: {e}", flush=True)
    
    # Fallback to specific endpoints
    try:
        if action_type == "reset":
            response = requests.post(
                f"{ENV_URL}/reset", 
                params={"task": kwargs.get("task", "easy")}, 
                timeout=30,
                verify=False
            )
        else:
            response = requests.post(
                f"{ENV_URL}/step", 
                json={"action_type": "MOVE", "direction": kwargs.get("direction", "RIGHT")}, 
                timeout=30,
                verify=False
            )
        
        if response.status_code != 200:
            raise Exception(f"API call failed: {response.status_code} - {response.text}")
        return response.json()
    except requests.exceptions.ConnectionError:
        # If HTTPS fails, try HTTP
        http_url = ENV_URL.replace("https://", "http://")
        if action_type == "reset":
            response = requests.post(f"{http_url}/reset", params={"task": kwargs.get("task", "easy")}, timeout=30)
        else:
            response = requests.post(f"{http_url}/step", json={"action_type": "MOVE", "direction": kwargs.get("direction", "RIGHT")}, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"API call failed: {response.status_code} - {response.text}")
        return response.json()

def get_llm_action(observation, step_num, task):
    """Use LLM to decide next action"""
    truck_pos = observation.get("truck_position", [0, 0])
    fuel = observation.get("fuel", 50)
    bins = observation.get("bins", [])
    
    if client is None:
        return rule_based_action(truck_pos, bins, fuel)
    
    system_prompt = """You are an AI agent controlling a waste collection truck.
Available actions: MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT.
Respond with ONLY the action name."""
    
    user_prompt = f"""Task: {task}
Step: {step_num}
Position: {truck_pos}
Fuel: {fuel}
Bins: {json.dumps(bins)}
Which direction?"""
    
    try:
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
            else:
                action = "MOVE_RIGHT"
        return action
    except Exception as e:
        print(f"[DEBUG] LLM call failed: {e}", flush=True)
        return rule_based_action(truck_pos, bins, fuel)

def rule_based_action(truck_pos, bins, fuel):
    """Simple rule-based fallback when LLM is not available"""
    if bins:
        # Find nearest bin
        nearest_bin = min(bins, key=lambda b: abs(b["pos"][0] - truck_pos[0]) + abs(b["pos"][1] - truck_pos[1]))
        target_x, target_y = nearest_bin["pos"]
        
        if truck_pos[0] < target_x:
            return "MOVE_RIGHT"
        elif truck_pos[0] > target_x:
            return "MOVE_LEFT"
        elif truck_pos[1] < target_y:
            return "MOVE_UP"
        elif truck_pos[1] > target_y:
            return "MOVE_DOWN"
    
    # Default to moving right
    return "MOVE_RIGHT"

def log_start(task, env, model):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step, action, reward, done, error=None):
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success, steps, score, rewards):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

def main():
    # Initialize variables with default values
    rewards = []
    steps_taken = 0
    success = False
    score = 0.0  # Initialize score to avoid UnboundLocalError
    
    model_used = MODEL_NAME if HAS_API_KEY else "rule-based-fallback"
    log_start(task=TASK_NAME, env=BENCHMARK, model=model_used)
    
    try:
        # Wait for environment server
        print(f"[INFO] Connecting to environment at {ENV_URL}...", flush=True)
        
        # Reset environment
        data = call_environment("reset", task=TASK_NAME)
        observation = data.get("observation", {})
        print(f"[INFO] Reset successful. Starting position: {observation.get('truck_position', [0,0])}", flush=True)
        
        total_reward = 0.0
        
        for step_num in range(1, MAX_STEPS + 1):
            # Get action from LLM or rule-based
            action = get_llm_action(observation, step_num, TASK_NAME)
            direction = action.replace("MOVE_", "")
            
            # Execute action
            data = call_environment("step", direction=direction)
            reward = data.get("reward", 0.0)
            done = data.get("done", False)
            observation = data.get("observation", {})
            
            total_reward += reward
            rewards.append(reward)
            steps_taken = step_num
            
            log_step(step=step_num, action=action, reward=reward, done=done)
            
            if done:
                print(f"[INFO] Episode finished at step {step_num}", flush=True)
                break
        
        # Calculate score (normalized between 0 and 1)
        # Simple scoring: based on reward and steps
        max_possible_reward = 0
        min_possible_reward = -MAX_STEPS
        
        if total_reward >= 0:
            reward_score = 1.0
        else:
            reward_score = max(0, min(1, (total_reward - min_possible_reward) / (max_possible_reward - min_possible_reward)))
        
        step_score = max(0, 1 - (steps_taken / MAX_STEPS))
        score = (reward_score * 0.6) + (step_score * 0.4)
        score = round(score, 3)
        
        success = steps_taken > 0
        
        print(f"[INFO] Episode complete. Steps: {steps_taken}, Total Reward: {total_reward:.2f}, Score: {score}", flush=True)
        
    except Exception as e:
        print(f"[ERROR] Exception in main: {e}", flush=True)
        score = 0.0
        success = False
    
    finally:
        # Always log end (even on exception)
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

if __name__ == "__main__":
    main()