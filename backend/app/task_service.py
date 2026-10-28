from datetime import datetime

from sqlalchemy.orm import Session

from .models import TaskDB, GoalDB, ActivityDB
from .progress_service import calculate_goal_progress
from .schemas import TaskCreate


def create_task(db: Session, task: TaskCreate):
    db_task = TaskDB(
        title=task.title,
        description=task.description,
        duration_minutes=task.duration_minutes,
        status="pending",
    )

    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    return db_task


def get_tasks(db: Session):
    return (
        db.query(TaskDB)
        .order_by(TaskDB.created_at.desc())
        .all()
    )


def complete_task(db: Session, task_id: int):
    task = (
        db.query(TaskDB)
        .filter(TaskDB.id == task_id)
        .first()
    )

    if not task:
        return None

    # Prevent duplicate activity creation.
    if task.status == "completed":
        return task

    task.status = "completed"

    goals = db.query(GoalDB).all()

    task_text = (
        f"{task.title} {task.description}"
    ).lower()

    matching_goals = []

    for goal in goals:
        goal_words = goal.title.lower().split()

        # Ignore generic words and look for meaningful overlap.
        meaningful_words = [
            word
            for word in goal_words
            if word not in {
                "learn",
                "learning",
                "goal",
                "the",
                "a",
                "an",
            }
        ]

        if any(
            word in task_text
            for word in meaningful_words
        ):
            progress = calculate_goal_progress(
                db,
                goal,
            )

            if progress < goal.target_hours:
                matching_goals.append(goal)

    # Prefer the matching goal with the most remaining progress.
    matching_goal = None

    if matching_goals:
        matching_goal = max(
            matching_goals,
            key=lambda goal: (
                goal.target_hours
                - calculate_goal_progress(db, goal)
            ),
        )

    if matching_goal and task.duration_minutes > 0:
        activity = ActivityDB(
            title=task.title,
            hours=task.duration_minutes / 60,
            goal_id=matching_goal.id,
            occurred_at=datetime.utcnow(),
        )

        db.add(activity)

    db.commit()
    db.refresh(task)

    return task