# smart_waste_env/tasks.py
import random

def easy_task(env):
    """Configure environment for easy difficulty"""
    env.reset()
    env.bins = [
        {"pos": [1, 1], "fill": 0.5},
        {"pos": [2, 2], "fill": 0.6}
    ]
    return env

def medium_task(env):
    """Configure environment for medium difficulty"""
    env.reset()
    env.bins = [
        {"pos": [random.randint(0, 4), random.randint(0, 4)], "fill": random.uniform(0.4, 0.8), "priority": 1}
        for _ in range(5)
    ]
    return env

def hard_task(env):
    """Configure environment for hard difficulty"""
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