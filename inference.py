import requests
from smart_waste_env.grader import grade

BASE_URL = "http://127.0.0.1:8000"

def run_task(task_name):
    """Run a specific task"""
    print(f"\n{'='*50}")
    print(f"Running {task_name.upper()} task")
    print(f"{'='*50}")
    
    # Reset with task parameter
    response = requests.post(f"{BASE_URL}/reset", json={
        "episode_id": task_name,
        "seed": 42,
        "task": task_name  # This tells the environment which task to use
    })
    
    if response.status_code != 200:
        print(f"Failed to reset: {response.text}")
        return None
    
    data = response.json()
    print(f"Reset response: {data}")
    
    total_reward = 0
    steps = 0
    overflow_count = 0
    done = False
    
    # Run up to 100 steps
    while not done and steps < 100:
        response = requests.post(f"{BASE_URL}/step", json={
            "action": {
                "action_type": "MOVE",
                "direction": "RIGHT"
            }
        })
        
        if response.status_code != 200:
            print(f"Step failed: {response.text}")
            break
        
        data = response.json()
        steps += 1
        reward = data.get("reward", 0)
        total_reward += reward
        done = data.get("done", False)
        
        # Get overflow count from info
        info = data.get("info", {})
        overflow_count = info.get("overflow_count", overflow_count)
        
        print(f"Step {steps}: reward={reward}, total={total_reward:.2f}, done={done}")
    
    # Calculate grade
    score = grade(total_reward, steps, overflow_count)
    
    print(f"\nResults for {task_name}:")
    print(f"  Total Reward: {total_reward:.2f}")
    print(f"  Steps Taken: {steps}")
    print(f"  Overflow Count: {overflow_count}")
    print(f"  Grade Score: {score}")
    
    return score

if __name__ == "__main__":
    # Test all three tasks
    results = {}
    for task in ["easy", "medium", "hard"]:
        score = run_task(task)
        if score is not None:
            results[task] = score
    
    # Print final results
    print(f"\n{'='*50}")
    print("FINAL RESULTS")
    print(f"{'='*50}")
    for task, score in results.items():
        print(f"{task.upper()}: {score}")
    
    print(f"\nOverall Average: {sum(results.values())/len(results):.2f}")