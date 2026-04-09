import requests
from smart_waste_env.grader import grade

BASE_URL = "http://127.0.0.1:8000"

def run_episode(task_name="easy", num_steps=100):
    # Reset with task
    res = requests.post(f"{BASE_URL}/reset", json={
        "episode_id": task_name,
        "seed": 42,
        "task": task_name
    })
    
    if res.status_code != 200:
        print(f"Reset failed: {res.text}")
        return None
    
    data = res.json()
    print(f"Reset ({task_name}):", data)
    
    total_reward = 0
    steps = 0
    overflow_count = 0
    
    # Step loop
    for i in range(num_steps):
        res = requests.post(f"{BASE_URL}/step", json={
            "action": {
                "action_type": "MOVE",
                "direction": "RIGHT"
            }
        })
        
        if res.status_code != 200:
            print(f"Step {i+1} failed: {res.text}")
            break
            
        data = res.json()
        steps += 1
        reward = data.get("reward", 0)
        total_reward += reward
        
        # Extract metrics from response
        info = data.get("info", {})
        overflow_count = info.get("overflow_count", overflow_count)
        
        print(f"Step {i+1}: reward={reward}, total_reward={total_reward}")
        
        if data.get("done", False):
            break
    
    # Calculate grade
    score = grade(total_reward, steps, overflow_count)
    print(f"\nTask: {task_name}")
    print(f"Total Reward: {total_reward}")
    print(f"Steps Taken: {steps}")
    print(f"Overflow Count: {overflow_count}")
    print(f"Grade Score: {score}")
    
    return score

if __name__ == "__main__":
    # Test all tasks
    results = {}
    for task in ["easy", "medium", "hard"]:
        print(f"\n{'='*50}")
        print(f"Running {task.upper()} task")
        print(f"{'='*50}")
        score = run_episode(task)
        if score is not None:
            results[task] = score
    
    print(f"\n{'='*50}")
    print("FINAL RESULTS")
    print(f"{'='*50}")
    for task, score in results.items():
        print(f"{task}: {score}")