from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .models import GoalDB, ActivityDB, TaskDB
from .progress_service import calculate_goal_progress
from .drift_engine import find_biggest_drift
from .schemas import Goal


def get_dashboard_data(db: Session):
    # -------------------------
    # Goals + real progress
    # -------------------------
    goals_db = db.query(GoalDB).all()

    goals = [
        {
            "id": goal.id,
            "title": goal.title,
            "priority": goal.priority,
            "target_hours": goal.target_hours,
            "completed_hours": calculate_goal_progress(db, goal),
        }
        for goal in goals_db
    ]

    # Convert to schema objects for drift calculation
    goal_objects = [
        Goal(
            title=goal["title"],
            priority=goal["priority"],
            target_hours=goal["target_hours"],
            completed_hours=goal["completed_hours"],
        )
        for goal in goals
    ]

    # -------------------------
    # Biggest drift
    # -------------------------
    biggest_drift = find_biggest_drift(goal_objects)

    drift_data = None

    if biggest_drift:
        remaining_hours = max(
            biggest_drift.target_hours
            - biggest_drift.completed_hours,
            0,
        )

        drift_data = {
            "goal": biggest_drift.title,
            "priority": biggest_drift.priority,
            "target_hours": biggest_drift.target_hours,
            "completed_hours": biggest_drift.completed_hours,
            "remaining_hours": remaining_hours,
        }

    # -------------------------
    # Today's activities
    # -------------------------
    today = datetime.utcnow().date()

    activities_db = (
        db.query(ActivityDB)
        .order_by(ActivityDB.occurred_at.desc())
        .all()
    )

    activities = [
        {
            "id": activity.id,
            "title": activity.title,
            "hours": activity.hours,
            "goal_id": activity.goal_id,
            "occurred_at": activity.occurred_at.isoformat(),
        }
        for activity in activities_db
        if activity.occurred_at.date() == today
    ]

    # -------------------------
    # Tasks
    # -------------------------
    tasks_db = (
        db.query(TaskDB)
        .order_by(TaskDB.created_at.desc())
        .all()
    )

    tasks = [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "duration_minutes": task.duration_minutes,
            "status": task.status,
            "created_at": task.created_at.isoformat(),
        }
        for task in tasks_db
    ]

    return {
        "goals": goals,
        "biggest_drift": drift_data,
        "activities": activities,
        "tasks": tasks,
    }