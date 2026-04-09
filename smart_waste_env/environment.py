# smart_waste_env/environment.py
from typing import Optional, Dict, Any, Tuple
from smart_waste_env.models import SmartWasteObservation, SmartWasteAction, Bin

class SmartWasteEnvironment:
    def __init__(self):
        self.truck_position = [0, 0]
        self.fuel = 50
        self.done = False
        self.step_count = 0
        self.total_reward = 0
        self.bins_data = []
        self.current_task = None

    def reset(self, episode_id: Optional[str] = None, seed: Optional[int] = None, task: Optional[str] = None) -> Tuple[SmartWasteObservation, float, bool, Dict]:
        """Reset environment"""
        print(f"Resetting with task: {task}")
        
        # Reset state
        self.truck_position = [0, 0]
        self.fuel = 50
        self.done = False
        self.step_count = 0
        self.total_reward = 0
        self.current_task = task
        
        # Configure bins based on task
        if task == "easy":
            self.bins_data = [
                {"pos": [1, 1], "fill": 0.5, "priority": 1},
                {"pos": [2, 2], "fill": 0.6, "priority": 1}
            ]
        elif task == "medium":
            self.bins_data = [
                {"pos": [2, 2], "fill": 0.7, "priority": 1},
                {"pos": [3, 3], "fill": 0.8, "priority": 1},
                {"pos": [4, 4], "fill": 0.5, "priority": 1}
            ]
        elif task == "hard":
            self.bins_data = [
                {"pos": [2, 2], "fill": 0.9, "priority": 2},
                {"pos": [3, 3], "fill": 0.8, "priority": 2},
                {"pos": [4, 4], "fill": 0.9, "priority": 1},
                {"pos": [5, 5], "fill": 0.7, "priority": 1},
                {"pos": [6, 6], "fill": 0.8, "priority": 2}
            ]
        else:
            self.bins_data = [
                {"pos": [2, 2], "fill": 0.5, "priority": 1},
                {"pos": [4, 4], "fill": 0.7, "priority": 1}
            ]
        
        # Convert to Bin objects
        bins = [Bin(**bin_data) for bin_data in self.bins_data]
        
        # Create observation
        observation = SmartWasteObservation(
            truck_position=self.truck_position,
            bins=bins,
            fuel=self.fuel
        )
        
        return observation, 0.0, False, {}

    def step(self, action: SmartWasteAction) -> Tuple[SmartWasteObservation, float, bool, Dict]:
        """Take a step"""
        reward = -1.0
        self.total_reward += reward
        self.step_count += 1
        
        # Process movement
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
        if self.fuel <= 0 or self.step_count >= 100:
            self.done = True
        
        # Convert to Bin objects
        bins = [Bin(**bin_data) for bin_data in self.bins_data]
        
        # Create observation
        observation = SmartWasteObservation(
            truck_position=self.truck_position,
            bins=bins,
            fuel=self.fuel
        )
        
        info = {
            "total_reward": self.total_reward,
            "steps": self.step_count,
            "overflow_count": 0,
            "task": self.current_task
        }
        
        return observation, reward, self.done, info

    def close(self):
        """Clean up"""
        pass