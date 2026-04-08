class SmartWasteEnvironment:

    def __init__(self):
        self.truck_position = [0, 0]
        self.fuel = 50
        self.done = False

    def reset(self, episode_id=None, seed=None):
        self.truck_position = [0, 0]
        self.fuel = 50
        self.done = False

        self.bins = [
            {"pos": [2, 2], "fill": 0.5, "priority": 1},
            {"pos": [4, 4], "fill": 0.7, "priority": 2}
        ]

        return (
            {
                "truck_position": self.truck_position,
                "bins": self.bins,
                "fuel": self.fuel
            },
            0.0,
            False,
            {}
        )

    def step(self, action):
        if self.done:
            return (
                {
                    "truck_position": self.truck_position,
                    "bins": self.bins,
                    "fuel": self.fuel
                },
                0.0,
                True,
                {}
            )

        reward = -1

        if action.action_type == "MOVE":
            if action.direction == "RIGHT":
                self.truck_position[0] += 1
            elif action.direction == "LEFT":
                self.truck_position[0] -= 1
            elif action.direction == "UP":
                self.truck_position[1] += 1
            elif action.direction == "DOWN":
                self.truck_position[1] -= 1

            self.fuel -= 1

        return (
            {
                "truck_position": self.truck_position,
                "bins": self.bins,
                "fuel": self.fuel
            },
            reward,
            False,
            {}
        )

    def close(self):
        pass

    async def reset_async(self, episode_id=None, seed=None):
        return self.reset(episode_id, seed)

    async def step_async(self, action):
        return self.step(action)