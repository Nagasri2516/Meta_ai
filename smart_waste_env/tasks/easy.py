def easy_task(env):
    env.reset()
    env.bins = [
        {"pos": [1, 1], "fill": 0.5},
        {"pos": [2, 2], "fill": 0.6}
    ]
    return env