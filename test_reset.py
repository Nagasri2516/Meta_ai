# test_reset.py - Test just the reset functionality
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_reset(task_name):
    print(f"\nTesting reset with task: {task_name}")
    try:
        response = requests.post(f"{BASE_URL}/reset", json={
            "episode_id": task_name,
            "seed": 42,
            "task": task_name
        })
        
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Response keys: {list(data.keys())}")
            if 'observation' in data:
                print(f"Observation: {data['observation']}")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    # Test each task
    for task in ["easy", "medium", "hard", None]:
        test_reset(task)