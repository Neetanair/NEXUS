from sqlalchemy.orm import Session

from .activity_service import extract_activities, save_activities
from .models import GoalDB
from .reflection_service import generate_reflection


from sqlalchemy.orm import Session

from .activity_service import extract_activities, save_activities
from .models import GoalDB
from .reflection_service import generate_reflection


def process_checkin(db: Session, text: str):
    goals = db.query(GoalDB).all()
    goal_titles = [goal.title for goal in goals]

    result = extract_activities(text, goal_titles)

    saved = save_activities(
        db,
        result.activities,
        goals,
    )

    try:
        reflection = generate_reflection(
            db,
            check_in_text=text,
        )

       
        return {
            "activities_saved": len(saved),
            "biggest_drift": reflection.biggest_drift,
            "explanation": reflection.explanation,
            "recommendation": reflection.recommendation,
            "personalized": reflection.personalized,
            "memory_used": reflection.memory_used,
        }

    except ValueError as e:
        if str(e) == "No active goal drift detected":
            return {
                "activities_saved": len(saved),
                "biggest_drift": None,
                "explanation": (
                    "You are currently on track with all "
                    "of your active goals. No intervention "
                    "is needed right now."
                ),
                "recommendation": None,
            }

        raise