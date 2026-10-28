from sqlalchemy.orm import Session

from .models import GoalDB, ActivityDB


def calculate_goal_progress(
    db: Session,
    goal: GoalDB,
) -> float:

    total = (
        db.query(ActivityDB)
        .filter(
            ActivityDB.goal_id == goal.id
        )
        .all()
    )

    completed = sum(
        activity.hours
        for activity in total
    )

    return completed