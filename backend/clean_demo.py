from app.database import SessionLocal
from app.models import (
    GoalDB,
    ActivityDB,
    TaskDB,
    RecommendationDB,
    RecommendationDecisionDB,
)

db = SessionLocal()

try:
    # Remove generated/test workflow data.
    db.query(ActivityDB).delete()
    db.query(TaskDB).delete()
    db.query(RecommendationDecisionDB).delete()
    db.query(RecommendationDB).delete()

    # Remove all existing goals.
    db.query(GoalDB).delete()

    # Create clean demo goals.
    db.add_all([
        GoalDB(
            title="Learn ROS2",
            priority="high",
            target_hours=3,
            completed_hours=0,
        ),
        GoalDB(
            title="Exercise",
            priority="medium",
            target_hours=3,
            completed_hours=0,
        ),
    ])

    db.commit()

    print("Demo database cleaned successfully.")

finally:
    db.close()