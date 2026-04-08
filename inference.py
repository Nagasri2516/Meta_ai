import requests

BASE_URL = "http://127.0.0.1:8000"

# RESET
res = requests.post(f"{BASE_URL}/reset", json={
    "episode_id": "test",
    "seed": 42
})

data = res.json()
print("Reset:", data)

# STEP LOOP
for i in range(5):

    res = requests.post(f"{BASE_URL}/step", json={
        "action": {   # 🔥 IMPORTANT FIX
            "action_type": "MOVE",
            "direction": "RIGHT"
        }
    })

    data = res.json()
    print(f"Step {i+1}:", data)

    # safety check
    if "done" in data and data["done"]:
        break