# inference.py
import requests
import sys
import time

BASE_URL = "http://127.0.0.1:8000" # Or the URL of your running Space

def run_episode(task_name, max_steps=20):
    """Run one episode and print structured output for the validator."""
    
    # --- 1. Print the START block ---
    # Format: [START] task=NAME
    print(f"[START] task={task_name}", flush=True)

    # Reset the environment
    try:
        response = requests.post(f"{BASE_URL}/reset", params={"task": task_name}, timeout=10)
        if response.status_code != 200:
            # If reset fails, we can't continue.
            print(f"[ERROR] Reset failed for task {task_name}: {response.text}", flush=True)
            # You might still print an [END] block here, but the validator expects steps.
            # For a hard failure, printing nothing might be best. Let's just return.
            return
    except Exception as e:
        print(f"[ERROR] Could not connect to server: {e}", flush=True)
        return

    total_reward = 0
    steps_taken = 0
    done = False

    # Run the episode
    for step_num in range(1, max_steps + 1):
        if done:
            break

        try:
            # Take a step (simple policy: always move right)
            step_response = requests.post(f"{BASE_URL}/step", json={
                "action_type": "MOVE",
                "direction": "RIGHT"
            }, timeout=10)
            
            if step_response.status_code != 200:
                print(f"[ERROR] Step {step_num} failed: {step_response.text}", flush=True)
                break

            data = step_response.json()
            reward = data.get('reward', 0)
            total_reward += reward
            done = data.get('done', False)
            steps_taken = step_num

            # --- 2. Print the STEP block ---
            # Format: [STEP] step=N reward=VALUE
            # The validator likely just needs the reward.
            print(f"[STEP] step={step_num} reward={reward}", flush=True)

        except Exception as e:
            print(f"[ERROR] Exception during step {step_num}: {e}", flush=True)
            break

    # --- 3. Print the END block ---
    # Format: [END] task=NAME score=SCORE steps=N
    # You need to calculate a score. The grader.py file you have is perfect for this.
    # Let's import your grading function.
    try:
        from smart_waste_env.grader import grade
        # The grader expects total_reward, steps, overflow_count.
        # We don't track overflow in this simple example, so pass 0.
        final_score = grade(total_reward, steps_taken, 0)
    except ImportError:
        # Fallback if grader can't be imported (e.g., on the validation server)
        # A simple score could be total_reward / max_steps, but using your grader is best.
        final_score = total_reward / max_steps if max_steps > 0 else 0
        final_score = max(0.0, min(1.0, final_score)) # Clamp between 0 and 1

    print(f"[END] task={task_name} score={final_score} steps={steps_taken}", flush=True)


if __name__ == "__main__":
    # The validator might run the script once and expect all tasks.
    # Let's run all three difficulties.
    # A small delay between tasks to avoid overwhelming the server.
    for task in ["easy", "medium", "hard"]:
        run_episode(task)
        time.sleep(1) # Be gentle to the server

    print("[INFO] Inference script finished.", flush=True)