# smart_waste_env/grader.py

def grade(total_reward, steps, overflow_count):
    """
    Grade the agent's performance in the waste collection environment.
    
    Args:
        total_reward (float): Total reward accumulated during episode
        steps (int): Number of steps taken
        overflow_count (int): Number of times bins overflowed
    
    Returns:
        float: Score between 0 and 1
    """
    score = 0

    # Reward efficiency (max 0.5 points)
    # Higher rewards are better, cap at 100 reward for full points
    score += min(total_reward / 100, 1) * 0.5

    # Overflow penalty (max 0.3 points)
    # Fewer overflows = higher score, cap at 10 overflows
    score += max(0, 1 - overflow_count / 10) * 0.3

    # Step efficiency (max 0.2 points)
    # Fewer steps = higher score, cap at 100 steps
    score += max(0, 1 - steps / 100) * 0.2

    return round(score, 2)