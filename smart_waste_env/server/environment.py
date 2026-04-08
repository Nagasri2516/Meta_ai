from smart_waste_env.models import SmartWasteAction, SmartWasteObservation, Bin


class SmartWasteEnvironment:

    def __init__(self):
        self.grid_size = 10
        self.fill_rate = 0.05
        self.reset()

    # 🔹 RESET (OpenEnv compatible)
    def reset(self, episode_id: str = None, seed: int = None):
        self.truck_position = [0, 0]
        self.fuel = 50
        self.steps = 0

        self.bins = [
            {"pos": [2, 2], "fill": 0.5, "priority": 1},
            {"pos": [4, 4], "fill": 0.7, "priority": 2}
        ]

        return SmartWasteObservation(
            truck_position=self.truck_position,
            bins=[Bin(**b) for b in self.bins],
            fuel=self.fuel,
            reward=0,
            done=False
        )

    # 🔹 STEP
    def step(self, action: SmartWasteAction):

        reward = 0
        self.steps += 1

        # 🚗 MOVE
        if action.action_type == "MOVE":
            if action.direction == "UP":
                self.truck_position[1] += 1
            elif action.direction == "DOWN":
                self.truck_position[1] -= 1
            elif action.direction == "LEFT":
                self.truck_position[0] -= 1
            elif action.direction == "RIGHT":
                self.truck_position[0] += 1

            # keep inside grid
            self.truck_position[0] = max(0, min(self.grid_size, self.truck_position[0]))
            self.truck_position[1] = max(0, min(self.grid_size, self.truck_position[1]))

            self.fuel -= 1
            reward -= 1

        # 🗑️ COLLECT
        elif action.action_type == "COLLECT":
            for b in self.bins:
                if b["pos"] == self.truck_position:
                    reward += 10 * b["fill"] * b.get("priority", 1)
                    b["fill"] = 0

        # ⏳ bins fill over time
        for b in self.bins:
            b["fill"] += self.fill_rate
            if b["fill"] > 1:
                reward -= 20 * b.get("priority", 1)

        # episode end
        done = self.fuel <= 0 or self.steps >= 100

        return SmartWasteObservation(
            truck_position=self.truck_position,
            bins=[Bin(**b) for b in self.bins],
            fuel=self.fuel,
            reward=reward,
            done=done
        )

    # 🔹 REQUIRED (OpenEnv)
    def close(self):
        pass

    async def reset_async(self, episode_id: str = None, seed: int = None):
        return self.reset(episode_id, seed)

    async def step_async(self, action):
       return self.step(action)