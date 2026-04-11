# inference.py
import requests
import sys
import time
import os

# Configuration
BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
TASKS = ["easy", "medium", "hard"]

def wait_for_server(timeout=30):
    """Wait for server to be ready."""
    print(f"[INFO] Waiting for server at {BASE_URL}...", flush=True)
    for i in range(timeout):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print(f"[INFO] Server is ready!", flush=True)
                return True
        except:
            pass
        time.sleep(1)
        if (i + 1) % 5 == 0:
            print(f"[INFO] Still waiting... ({i+1}/{timeout} seconds)", flush=True)
    
    print(f"[ERROR] Server did not become ready within {timeout} seconds", flush=True)
    return False

def grade_performance(total_reward, steps, max_steps=100):
    """Calculate a score between 0 and 1."""
    reward_score = min(total_reward / 100, 1) * 0.5
    step_score = max(0, 1 - steps / max_steps) * 0.5
    return round(reward_score + step_score, 2)

def run_task(task_name):
    """Run a single task and print structured output."""
    
    # ===== 1. PRINT START BLOCK =====
    print(f"[START] task={task_name}", flush=True)
    
    # Reset environment
    try:
        response = requests.post(
            f"{BASE_URL}/reset",
            params={"task": task_name},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"[ERROR] Reset failed: {response.status_code}", flush=True)
            print(f"[END] task={task_name} score=0.0 steps=0", flush=True)
            return
        
        print(f"[INFO] Reset successful for task: {task_name}", flush=True)
        
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}", flush=True)
        print(f"[END] task={task_name} score=0.0 steps=0", flush=True)
        return
    
    # Run episode
    total_reward = 0
    steps = 0
    done = False
    max_steps = 50
    
    for step_num in range(1, max_steps + 1):
        try:
            # Take a step (simple policy: always move right)
            response = requests.post(
                f"{BASE_URL}/step",
                json={"action_type": "MOVE", "direction": "RIGHT"},
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"[ERROR] Step {step_num} failed", flush=True)
                break
            
            data = response.json()
            reward = data.get("reward", 0)
            total_reward += reward
            done = data.get("done", False)
            steps = step_num
            
            # ===== 2. PRINT STEP BLOCK =====
            print(f"[STEP] step={step_num} reward={reward}", flush=True)
            
            if done:
                print(f"[INFO] Episode finished at step {step_num}", flush=True)
                break
                
        except Exception as e:
            print(f"[ERROR] Step {step_num} exception: {e}", flush=True)
            break
    
    # Calculate final score
    score = grade_performance(total_reward, steps)
    
    # ===== 3. PRINT END BLOCK =====
    print(f"[END] task={task_name} score={score} steps={steps}", flush=True)

def main():
    """Main function to run all tasks."""
    print("[INFO] Starting inference script", flush=True)
    print(f"[INFO] API URL: {BASE_URL}", flush=True)
    
    # Wait for server to be ready
    if not wait_for_server():
        print("[ERROR] Cannot proceed without server", flush=True)
        sys.exit(1)
    
    # Run all tasks
    for task in TASKS:
        print(f"[INFO] Running task: {task}", flush=True)
        run_task(task)
        time.sleep(0.5)  # Small delay between tasks
    
    print("[INFO] All tasks completed", flush=True)

if __name__ == "__main__":
    main()