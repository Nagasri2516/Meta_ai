# inference.py - Place this in the project root directory
import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def wait_for_server(timeout=30):
    """Wait for server to be ready"""
    print(f"Waiting for server at {BASE_URL}...")
    for i in range(timeout):
        try:
            response = requests.get(f"{BASE_URL}/openapi.json", timeout=2)
            if response.status_code == 200:
                print("✓ Server is ready!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        except Exception as e:
            print(f"  Attempt {i+1}/{timeout}: {str(e)[:50]}")
        
        time.sleep(1)
        if (i + 1) % 5 == 0:
            print(f"  Still waiting... ({i+1}/{timeout} seconds)")
    
    print("✗ Server failed to start within timeout")
    return False

def run_task(task_name):
    """Run a single task episode"""
    print(f"\n{'='*50}")
    print(f"Running {task_name.upper()} task")
    print(f"{'='*50}")
    
    try:
        # Reset the environment
        print(f"Resetting environment with task: {task_name}")
        response = requests.post(f"{BASE_URL}/reset", json={
            "episode_id": task_name,
            "seed": 42,
            "task": task_name
        }, timeout=5)
        
        if response.status_code != 200:
            print(f"✗ Reset failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
        
        data = response.json()
        print(f"✓ Reset successful!")
        print(f"  Initial observation: {data.get('observation', {})}")
        
        # Run the episode
        total_reward = 0
        steps = 0
        done = False
        
        print("\nTaking actions...")
        while not done and steps < 50:
            # Take a step (simple policy: always move right)
            response = requests.post(f"{BASE_URL}/step", json={
                "action": {
                    "action_type": "MOVE",
                    "direction": "RIGHT"
                }
            }, timeout=5)
            
            if response.status_code != 200:
                print(f"✗ Step {steps + 1} failed: {response.text}")
                break
            
            data = response.json()
            reward = data.get("reward", 0)
            total_reward += reward
            done = data.get("done", False)
            steps += 1
            
            print(f"  Step {steps:2d}: reward={reward:6.2f}, total={total_reward:6.2f}, done={done}")
        
        print(f"\n✓ Episode complete!")
        print(f"  Total steps: {steps}")
        print(f"  Total reward: {total_reward:.2f}")
        return total_reward
        
    except requests.exceptions.ConnectionError:
        print(f"✗ Cannot connect to server at {BASE_URL}")
        print("\nMake sure the server is running in another terminal:")
        print("  Terminal 1: uvicorn server.app:app --reload")
        return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def main():
    """Main function to run all tasks"""
    print("\n" + "="*50)
    print("SMART WASTE ENVIRONMENT TEST")
    print("="*50)
    
    # Check if server is running
    if not wait_for_server():
        print("\n❌ ERROR: Server is not running!")
        print("\nPlease start the server first:")
        print("  1. Open a new terminal")
        print("  2. Run: cd C:\\Users\\User\\OneDrive\\Desktop\\smart-waste-ai")
        print("  3. Run: venv\\Scripts\\activate")
        print("  4. Run: uvicorn server.app:app --reload")
        print("\nThen run this script again in another terminal.")
        sys.exit(1)
    
    # Run all tasks
    results = {}
    for task in ["easy", "medium", "hard"]:
        total_reward = run_task(task)
        if total_reward is not None:
            results[task] = total_reward
    
    # Print summary
    print("\n" + "="*50)
    print("FINAL RESULTS")
    print("="*50)
    for task, reward in results.items():
        print(f"  {task.upper()}: {reward:.2f}")
    
    if results:
        avg_reward = sum(results.values()) / len(results)
        print(f"\n  Average reward: {avg_reward:.2f}")
    
    print("\n✓ Testing complete!")

if __name__ == "__main__":
    main()