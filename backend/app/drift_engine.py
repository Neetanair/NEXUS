from .schemas import Goal


PRIORITY_WEIGHT = {
    "low": 1,
    "medium": 2,
    "high": 3,
}


def calculate_drift(goal: Goal) -> float:
    """
    Calculate a simple deterministic drift score.

    Higher score = greater misalignment between
    the user's stated goal and actual progress.
    """

    if goal.target_hours <= 0:
        return 0

    progress_ratio = min(
        goal.completed_hours / goal.target_hours,
        1.0
    )

    remaining_ratio = 1.0 - progress_ratio

    priority = PRIORITY_WEIGHT[goal.priority]

    return priority * remaining_ratio

def find_biggest_drift(goals: list[Goal]) -> Goal | None:
    if not goals:
        return None

    active_goals = [
        goal
        for goal in goals
        if goal.target_hours > 0
        and goal.completed_hours < goal.target_hours
    ]

    if not active_goals:
        return None

    return max(
        active_goals,
        key=calculate_drift,
    )