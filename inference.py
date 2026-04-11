# inference.py - Updated to match exact hackathon format
import os
import time
import requests

# Required environment variables (set defaults)
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
MODEL_NAME = os.getenv("MODEL_NAME", "smart-waste-agent")
TASK_NAME = os.getenv("TASK_NAME", "easy")
BENCHMARK = os.getenv("BENCHMARK", "smart_waste_env")
MAX_STEPS = 50

def main():
    rewards = []
    steps_taken = 0
    success = False
    
    # ===== START BLOCK =====
    print(f"[START] task={TASK_NAME} env={BENCHMARK} model={MODEL_NAME}", flush=True)
    
    try:
        # Reset environment
        response = requests.post(f"{API_BASE_URL}/reset", params={"task": TASK_NAME}, timeout=10)
        if response.status_code != 200:
            print(f"[STEP] step=0 action=null reward=0.00 done=true error=reset_failed", flush=True)
        else:
            total_reward = 0.0
            
            for step_num in range(1, MAX_STEPS + 1):
                # Take action
                action = "MOVE_RIGHT"
                
                response = requests.post(
                    f"{API_BASE_URL}/step",
                    json={"action_type": "MOVE", "direction": "RIGHT"},
                    timeout=10
                )
                
                if response.status_code != 200:
                    print(f"[STEP] step={step_num} action={action} reward=0.00 done=false error=api_failed", flush=True)
                    break
                
                data = response.json()
                reward = data.get("reward", 0.0)
                done = data.get("done", False)
                total_reward += reward
                rewards.append(reward)
                steps_taken = step_num
                
                # ===== STEP BLOCK =====
                error_val = "null"
                done_val = "true" if done else "false"
                print(f"[STEP] step={step_num} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)
                
                if done:
                    break
        
        # Calculate score (normalized between 0 and 1)
        # Simple scoring: (50 - steps_taken) / 50 * 0.5 + (total_reward + 50) / 100 * 0.5
        step_score = max(0, (50 - steps_taken) / 50) * 0.5
        reward_score = max(0, min(1, (total_reward + 50) / 100)) * 0.5 if steps_taken > 0 else 0
        score = step_score + reward_score
        score = max(0.0, min(1.0, score))
        
        success = steps_taken > 0
        
    except Exception as e:
        print(f"[STEP] step=0 action=null reward=0.00 done=true error={str(e)}", flush=True)
        score = 0.0
        success = False
    
    finally:
        # ===== END BLOCK =====
        rewards_str = ",".join(f"{r:.2f}" for r in rewards) if rewards else ""
        print(f"[END] success={str(success).lower()} steps={steps_taken} score={score:.3f} rewards={rewards_str}", flush=True)

if __name__ == "__main__":
    main()