import random

def hard_task(env):
    env.reset()

    env.bins = [
        {
            "pos": [random.randint(0, 8), random.randint(0, 8)],
            "fill": random.uniform(0.6, 0.9),
            "priority": 2 if i % 2 == 0 else 1
        }
        for i in range(10)
    ]

    env.fill_rate = 0.1  # faster filling

    return env