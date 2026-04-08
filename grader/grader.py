def grade(total_reward, steps, overflow_count):

    score = 0

    # reward efficiency
    score += min(total_reward / 100, 1) * 0.5

    # overflow penalty
    score += max(0, 1 - overflow_count / 10) * 0.3

    # step efficiency
    score += max(0, 1 - steps / 100) * 0.2

    return round(score, 2)