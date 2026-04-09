import requests

BASE_URL = "http://127.0.0.1:8000"

# Test reset endpoint
print("Testing /reset endpoint...")
response = requests.post(f"{BASE_URL}/reset", json={
    "episode_id": "test_episode",
    "seed": 42
})

print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(f"Response: {response.json()}")
else:
    print(f"Error: {response.text}")

# Test step endpoint if reset worked
if response.status_code == 200:
    print("\nTesting /step endpoint...")
    response = requests.post(f"{BASE_URL}/step", json={
        "action": {
            "action_type": "MOVE",
            "direction": "RIGHT"
        }
    })
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
    else:
        print(f"Error: {response.text}")