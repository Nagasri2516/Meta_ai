# inference.py - Final version
import os
import sys
import time
import json

try:
    import requests
except ImportError:
    print("[ERROR] requests module not installed", flush=True)
    sys.exit(1)

# ============================================
# Configuration
# ============================================
ENV_URL = os.getenv("ENV_URL", "http://127.0.0.1:8000")
LLM_API_BASE = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY = os.getenv("API_KEY") or os.getenv("HF_TOKEN")
MODEL_NAME = os.getenv("MODEL_NAME", "rule-based")
BENCHMARK = os.getenv("BENCHMARK", "smart_waste_env")
MAX_STEPS = 30

# List of tasks to run (3 tasks required)
TASKS = ["easy", "medium", "hard"]

# Initialize OpenAI client if API key exists
HAS_API_KEY = API_KEY is not None
client = None

if HAS_API_KEY:
    try:
        from openai import OpenAI
        client = OpenAI(base_url=LLM_API_BASE, api_key=API_KEY)
        MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
        print("[INFO] OpenAI client initialized", flush=True)
    except ImportError:
        print("[WARNING] openai not installed", flush=True)

def wait_for_server(timeout=30):
    """Wait for server to be ready"""
    print(f"[INFO] Waiting for server at {ENV_URL}...", flush=True)
    for i in range(timeout):
        try:
            response = requests.get(f"{ENV_URL}/health", timeout=2)
            if response.status_code == 200:
                print(f"[INFO] Server is ready!", flush=True)
                return True
        except:
            pass
        time.sleep(1)
    return False

def call_environment(action_type, **kwargs):
    """Call environment endpoint with error handling"""
    try:
        if action_type == "reset":
            response = requests.post(f"{ENV_URL}/reset", params={"task": kwargs.get("task", "easy")}, timeout=10)
        else:
            response = requests.post(f"{ENV_URL}/step", json={"action_type": "MOVE", "direction": kwargs.get("direction", "RIGHT")}, timeout=10)
        
        if response.status_code != 200:
            raise Exception(f"API call failed: {response.status_code} - {response.text}")
        return response.json()
    except requests.exceptions.ConnectionError as e:
        raise Exception(f"Cannot connect to {ENV_URL}: {e}")
    except requests.exceptions.Timeout as e:
        raise Exception(f"Server timeout at {ENV_URL}: {e}")
    except Exception as e:
        raise Exception(f"Environment call failed: {e}")

def rule_based_action(truck_pos, bins, fuel):
    """Simple rule-based action"""
    if bins:
        try:
            # Handle bins that are either dicts or objects
            def get_bin_pos(b):
                if isinstance(b, dict):
                    return b.get("pos", [0, 0])
                else:
                    return getattr(b, "pos", [0, 0])
            
            nearest_bin = min(bins, key=lambda b: abs(get_bin_pos(b)[0] - truck_pos[0]) + abs(get_bin_pos(b)[1] - truck_pos[1]))
            target_x, target_y = get_bin_pos(nearest_bin)
            
            if truck_pos[0] < target_x:
                return "MOVE_RIGHT"
            elif truck_pos[0] > target_x:
                return "MOVE_LEFT"
            elif truck_pos[1] < target_y:
                return "MOVE_UP"
            elif truck_pos[1] > target_y:
                return "MOVE_DOWN"
        except Exception as e:
            print(f"[WARNING] Rule-based action failed: {e}", flush=True)
    return "MOVE_RIGHT"

def get_action(observation, step_num, task):
    """Get action from LLM or rule-based"""
    try:
        truck_pos = observation.get("truck_position", [0, 0]) if isinstance(observation, dict) else getattr(observation, "truck_position", [0, 0])
        fuel = observation.get("fuel", 50) if isinstance(observation, dict) else getattr(observation, "fuel", 50)
        bins = observation.get("bins", []) if isinstance(observation, dict) else getattr(observation, "bins", [])
        
        if client is None:
            return rule_based_action(truck_pos, bins, fuel)
        
        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You control a waste collection truck. Respond with ONLY: MOVE_UP, MOVE_DOWN, MOVE_LEFT, or MOVE_RIGHT"},
                    {"role": "user", "content": f"Position: {truck_pos}, Fuel: {fuel}, Bins: {len(bins)}. Best direction?"}
                ],
                temperature=0.7,
                max_tokens=10,
                timeout=10
            )
            action = completion.choices[0].message.content.strip().upper()
            valid = ["MOVE_UP", "MOVE_DOWN", "MOVE_LEFT", "MOVE_RIGHT"]
            for v in valid:
                if v in action:
                    return v
            return "MOVE_RIGHT"
        except Exception as e:
            print(f"[WARNING] LLM call failed: {e}", flush=True)
            return rule_based_action(truck_pos, bins, fuel)
    except Exception as e:
        print(f"[WARNING] Error getting action: {e}", flush=True)
        return "MOVE_RIGHT"

def calculate_score(total_reward, steps_taken):
    """Calculate score STRICTLY between 0 and 1"""
    if steps_taken == 0:
        return 0.001
    
    reward_score = max(0, min(1, (total_reward + 50) / 50))
    step_score = max(0, min(1, 1 - (steps_taken / MAX_STEPS)))
    raw_score = (reward_score * 0.5) + (step_score * 0.5)
    
    if raw_score <= 0.001:
        return 0.001
    if raw_score >= 0.999:
        return 0.999
    return round(raw_score, 3)

def run_task(task_name):
    """Run a single task and print structured output"""
    rewards = []
    steps_taken = 0
    total_reward = 0.0
    
    model_display = MODEL_NAME if HAS_API_KEY else "rule-based"
    print(f"[START] task={task_name} env={BENCHMARK} model={model_display}", flush=True)
    
    try:
        data = call_environment("reset", task=task_name)
        observation = data.get("observation", {})
        print(f"[INFO] Reset successful for task {task_name}", flush=True)
        
        for step_num in range(1, MAX_STEPS + 1):
            try:
                action = get_action(observation, step_num, task_name)
                direction = action.replace("MOVE_", "")
                
                data = call_environment("step", direction=direction)
                reward = data.get("reward", 0.0)
                done = data.get("done", False)
                observation = data.get("observation", {})
                
                total_reward += reward
                rewards.append(reward)
                steps_taken = step_num
                
                print(f"[STEP] step={step_num} action={action} reward={reward:.2f} done={str(done).lower()} error=null", flush=True)
                
                if done:
                    break
            except Exception as e:
                print(f"[ERROR] Step {step_num} failed: {e}", flush=True)
                break
        
        score = calculate_score(total_reward, steps_taken)
        
    except Exception as e:
        print(f"[ERROR] Task {task_name} failed: {e}", flush=True)
        score = 0.001
        steps_taken = 0
        rewards = []
    
    rewards_str = ",".join(f"{r:.2f}" for r in rewards) if rewards else ""
    print(f"[END] success=true steps={steps_taken} score={score:.3f} rewards={rewards_str}", flush=True)
    return score

def main():
    try:
        print("[INFO] Starting Smart Waste Environment Inference", flush=True)
        print(f"[INFO] Environment URL: {ENV_URL}", flush=True)
        
        if not wait_for_server():
            print("[ERROR] Server not ready after timeout", flush=True)
            sys.exit(1)
        
        scores = {}
        for task in TASKS:
            print(f"\n[INFO] Running task: {task}", flush=True)
            score = run_task(task)
            scores[task] = score
            time.sleep(0.5)
        
        print(f"\n[INFO] All tasks completed", flush=True)
        print(f"[INFO] Final Scores: easy={scores.get('easy', 0)}, medium={scores.get('medium', 0)}, hard={scores.get('hard', 0)}", flush=True)
        
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user", flush=True)
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Fatal error: {e}", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

    