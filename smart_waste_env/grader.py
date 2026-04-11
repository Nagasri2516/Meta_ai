# smart_waste_env/grader.py
def grade(total_reward, steps, overflow_count):
    """
    Grade the agent's performance.
    Returns a score STRICTLY between 0 and 1.
    """
    # Normalize reward (typical range: -100 to 0)
    reward_score = max(0, min(1, (total_reward + 100) / 100))
    
    # Normalize steps (typical range: 0 to 100)
    step_score = max(0, min(1, 1 - (steps / 100)))
    
    # Normalize overflow (0 to 10)
    overflow_score = max(0, min(1, 1 - (overflow_count / 10)))
    
    # Combined score
    raw_score = (reward_score * 0.4) + (step_score * 0.3) + (overflow_score * 0.3)
    
    # Ensure strictly between 0 and 1 (not including boundaries)
    if raw_score <= 0.001:
        return 0.001
    if raw_score >= 0.999:
        return 0.999
    return round(raw_score, 3)