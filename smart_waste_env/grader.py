# smart_waste_env/grader.py
def grade(total_reward, steps, overflow_count):
    """
    Grade the agent's performance.
    Returns a score strictly between 0 and 1.
    """
    max_steps = 100
    max_overflow = 10
    
    # Reward efficiency (max 0.5 points)
    reward_score = min(total_reward / 100, 1) * 0.5
    
    # Overflow penalty (max 0.3 points)
    overflow_score = max(0, 1 - overflow_count / max_overflow) * 0.3
    
    # Step efficiency (max 0.2 points)
    step_score = max(0, 1 - steps / max_steps) * 0.2
    
    raw_score = reward_score + overflow_score + step_score
    
    # Ensure score is strictly between 0 and 1
    epsilon = 0.001
    score = max(epsilon, min(1 - epsilon, raw_score))
    
    return round(score, 3)