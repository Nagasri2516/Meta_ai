# smart_waste_env/tasks.py
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
        {"pos": [2, 2], "fill": 0.7},
        {"pos": [3, 3], "fill": 0.8},
        {"pos": [4, 4], "fill": 0.5}
    ]
    return env

def hard_task(env):
    """Configure environment for hard difficulty"""
    env.reset()
    env.bins = [
        {"pos": [2, 2], "fill": 0.9},
        {"pos": [3, 3], "fill": 0.8},
        {"pos": [4, 4], "fill": 0.9},
        {"pos": [5, 5], "fill": 0.7},
        {"pos": [6, 6], "fill": 0.8}
    ]
    return env