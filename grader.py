def grade(final_state):
    """
    Winning-level grading logic.
    Returns a score between 0.0 and 1.0.
    """
    debt = getattr(final_state, 'debt', getattr(final_state, 'total_debt', 1.0))
    credit = getattr(final_state, 'credit_score', 0)

    if debt <= 0:
        return 0.95
    elif debt < 2000:
        return 0.7
    elif credit > 600:
        return 0.5
    else:
        return 0.2
