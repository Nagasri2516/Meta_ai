import random

def medium_task(env):
    env.reset()
    env.bins = [
        {"pos": [random.randint(0, 4), random.randint(0, 4)], "fill": random.uniform(0.4, 0.8)}
        for _ in range(5)
    ]
    return env