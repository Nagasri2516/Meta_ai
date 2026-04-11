# inference.py - With proper imports and error handling
import os
import sys
import time

# Try to import required modules with error handling
try:
    import requests
except ImportError:
    print("[ERROR] requests module not installed. Run: pip install requests", flush=True)
    sys.exit(1)

try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass

# ============================================
# Configuration with fallbacks
# ============================================
def find_server():
    """Try to find the running server on common ports"""
    common_ports = [7860, 8000, 8080]
    for port in common_ports:
        try:
            response = requests.get(f"http://127.0.0.1:{port}/health", timeout=2)
            if response.status_code == 200:
                print(f"[INFO] Found server on port {port}", flush=True)
                return f"http://127.0.0.1:{port}"
        except:
            pass
    return "http://127.0.0.1:7860"

ENV_URL = os.getenv("ENV_URL", find_server())
LLM_API_BASE = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY = os.getenv("API_KEY") or os.getenv("HF_TOKEN")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
TASK_NAME = os.getenv("TASK_NAME", "easy")
BENCHMARK = os.getenv("BENCHMARK", "smart_waste_env")
MAX_STEPS = 30

# Initialize OpenAI client only if API key exists
HAS_API_KEY = API_KEY is not None
client = None

if HAS_API_KEY:
    try:
        from openai import OpenAI
        client = OpenAI(base_url=LLM_API_BASE, api_key=API_KEY)
        print("[INFO] OpenAI client initialized for LLM calls", flush=True)
    except ImportError:
        print("[WARNING] openai module not installed", flush=True)
        HAS_API_KEY = False
else:
    print("[WARNING] No API_KEY found. Using fallback rule-based actions.", flush=True)

def call_environment(action_type, **kwargs):
    """Call environment endpoint with error handling"""
    try:
        if action_type == "reset":
            response = requests.post(
                f"{ENV_URL}/reset", 
                params={"task": kwargs.get("task", "easy")}, 
                timeout=10
            )
        else:
            response = requests.post(
                f"{ENV_URL}/step", 
                json={"action_type": "MOVE", "direction": kwargs.get("direction", "RIGHT")}, 
                timeout=10
            )
        
        if response.status_code != 200:
            raise Exception(f"API call failed: {response.status_code} - {response.text}")
        return response.json()
    except requests.exceptions.ConnectionError:
        raise Exception(f"Cannot connect to {ENV_URL}. Is the server running?")
    except Exception as e:
        raise Exception(f"Environment call failed: {e}")

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
        if (i + 1) % 5 == 0:
            print(f"[INFO] Still waiting... ({i+1}/{timeout} seconds)", flush=True)
    
    print(f"[ERROR] Server not ready after {timeout} seconds", flush=True)
    return False

def rule_based_action(truck_pos, bins, fuel):
    """Simple rule-based fallback"""
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
    return "MOVE_RIGHT"

def get_llm_action(observation, step_num, task):
    """Use LLM or rule-based to decide action"""
    truck_pos = observation.get("truck_position", [0, 0])
    fuel = observation.get("fuel", 50)
    bins = observation.get("bins", [])
    
    # Use rule-based if no client
    if client is None or not HAS_API_KEY:
        return rule_based_action(truck_pos, bins, fuel)
    
    try:
        system_prompt = """You are an AI agent controlling a waste collection truck.
Available actions: MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT.
Respond with ONLY the action name."""
        
        user_prompt = f"""Task: {task}
Step: {step_num}
Position: {truck_pos}
Fuel: {fuel}
Bins: {len(bins)} bins
Which direction?"""
        
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=10,
            timeout=10
        )
        
        action = completion.choices[0].message.content.strip().upper()
        
        valid_actions = ["MOVE_UP", "MOVE_DOWN", "MOVE_LEFT", "MOVE_RIGHT"]
        for v in valid_actions:
            if v in action:
                return v
        return "MOVE_RIGHT"
        
    except Exception as e:
        print(f"[DEBUG] LLM call failed: {e}", flush=True)
        return rule_based_action(truck_pos, bins, fuel)

def log_start(task, env, model):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step, action, reward, done, error=None):
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success, steps, score, rewards):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards) if rewards else ""
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

def main():
    rewards = []
    steps_taken = 0
    success = False
    score = 0.0
    
    model_used = MODEL_NAME if HAS_API_KEY else "rule-based-fallback"
    log_start(task=TASK_NAME, env=BENCHMARK, model=model_used)
    
    if not wait_for_server():
        log_end(success=False, steps=0, score=0.0, rewards=[])
        return
    
    try:
        # Reset environment
        data = call_environment("reset", task=TASK_NAME)
        observation = data.get("observation", {})
        print(f"[INFO] Reset successful. Position: {observation.get('truck_position', [0,0])}", flush=True)
        
        total_reward = 0.0
        
        for step_num in range(1, MAX_STEPS + 1):
            action = get_llm_action(observation, step_num, TASK_NAME)
            direction = action.replace("MOVE_", "")
            
            data = call_environment("step", direction=direction)
            reward = data.get("reward", 0.0)
            done = data.get("done", False)
            observation = data.get("observation", {})
            
            total_reward += reward
            rewards.append(reward)
            steps_taken = step_num
            
            log_step(step=step_num, action=action, reward=reward, done=done)
            
            if done:
                break
        
        # Calculate score
        if steps_taken > 0:
            step_score = max(0, 1 - (steps_taken / MAX_STEPS))
            reward_score = max(0, min(1, (total_reward + MAX_STEPS) / MAX_STEPS))
            score = round((reward_score * 0.6) + (step_score * 0.4), 3)
            success = True
        
    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        score = 0.0
        success = False
    
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

if __name__ == "__main__":
    main()