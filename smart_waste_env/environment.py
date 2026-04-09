# smart_waste_env/environment.py

class SmartWasteEnvironment:
    def __init__(self):
        self.truck_position = [0, 0]
        self.fuel = 50
        self.done = False
        # Add tracking for grader metrics
        self.total_reward = 0
        self.steps_taken = 0
        self.overflow_count = 0

    def reset(self, episode_id=None, seed=None):
        self.truck_position = [0, 0]
        self.fuel = 50
        self.done = False
        # Reset tracking metrics
        self.total_reward = 0
        self.steps_taken = 0
        self.overflow_count = 0

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
        self.total_reward += reward
        self.steps_taken += 1

        # Check for overflow (example logic - adjust based on your game rules)
        for bin in self.bins:
            if bin.get("fill", 0) > 1.0:  # If fill exceeds capacity
                self.overflow_count += 1
                # Handle overflow...

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

        # Check if episode should end
        if self.fuel <= 0 or self.steps_taken >= 100:  # Max steps limit
            self.done = True

        return (
            {
                "truck_position": self.truck_position,
                "bins": self.bins,
                "fuel": self.fuel
            },
            reward,
            self.done,
            {
                "total_reward": self.total_reward,
                "steps": self.steps_taken,
                "overflow_count": self.overflow_count
            }  # Include metrics in the info dict
        )