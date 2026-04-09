# test_inference.py
import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def run_episode(task_name, max_steps=20):
    """Run one episode with the given task"""
    print(f"\n{'='*50}")
    print(f"Running {task_name.upper()} task")
    print(f"{'='*50}")
    
    # Reset environment
    print(f"Resetting environment...")
    response = requests.post(f"{BASE_URL}/reset", params={"task": task_name})
    
    if response.status_code != 200:
        print(f"❌ Reset failed: {response.status_code}")
        return None
    
    data = response.json()
    print(f"✓ Reset successful!")
    print(f"  Initial fuel: {data['observation']['fuel']}")
    print(f"  Initial position: {data['observation']['truck_position']}")
    print(f"  Number of bins: {len(data['observation']['bins'])}")
    
    # Run episode
    total_reward = 0
    steps = 0
    done = False
    
    print(f"\nTaking actions...")
    while not done and steps < max_steps:
        # Take a step (always move right)
        response = requests.post(f"{BASE_URL}/step", json={
            "action_type": "MOVE",
            "direction": "RIGHT"
        })
        
        if response.status_code != 200:
            print(f"❌ Step failed: {response.status_code}")
            break
        
        data = response.json()
        steps += 1
        total_reward += data['reward']
        done = data['done']
        
        print(f"  Step {steps:2d}: Reward={data['reward']:5.1f}, "
              f"Position={data['observation']['truck_position']}, "
              f"Fuel={data['observation']['fuel']}, Done={done}")
        
        if done:
            print(f"\n✓ Episode finished after {steps} steps!")
            break
    
    # Get final state
    response = requests.get(f"{BASE_URL}/state")
    if response.status_code == 200:
        state = response.json()
        print(f"\n📊 Final Stats:")
        print(f"  Total Reward: {total_reward:.1f}")
        print(f"  Steps Taken: {steps}")
        print(f"  Final Fuel: {data['observation']['fuel']}")
        print(f"  Final Position: {data['observation']['truck_position']}")
    
    return {"task": task_name, "total_reward": total_reward, "steps": steps}

def main():
    print("🚀 Smart Waste Environment Test")
    print("="*50)
    
    # Test all three tasks
    results = []
    for task in ["easy", "medium", "hard"]:
        result = run_episode(task)
        if result:
            results.append(result)
        time.sleep(0.5)  # Small delay between tasks
    
    # Print summary
    print(f"\n{'='*50}")
    print("📊 SUMMARY RESULTS")
    print(f"{'='*50}")
    for result in results:
        print(f"{result['task'].upper():6s}: Total Reward = {result['total_reward']:6.1f}, Steps = {result['steps']}")
    
    if results:
        avg_reward = sum(r['total_reward'] for r in results) / len(results)
        print(f"\nAverage Reward: {avg_reward:.1f}")
    
    print("\n✅ Testing complete!")

if __name__ == "__main__":
    main()