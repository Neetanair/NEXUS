from sqlalchemy.orm import Session

from .models import RecommendationDB, RecommendationDecisionDB
from .schemas import RecommendationDecisionRequest
from .models import RecommendationDB, RecommendationDecisionDB, TaskDB


def save_recommendation(
    db: Session,
    goal: str,
    title: str,
    description: str,
    total_minutes: int,
):
    recommendation = RecommendationDB(
        goal=goal,
        title=title,
        description=description,
        total_minutes=total_minutes,
        status="pending",
    )

    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)

    return recommendation


def get_latest_recommendation(db: Session):
    return (
        db.query(RecommendationDB)
        .order_by(
            RecommendationDB.created_at.desc(),
            RecommendationDB.id.desc(),
        )
        .first()
    )


def save_recommendation_decision(
    db: Session,
    request: RecommendationDecisionRequest,
):
    recommendation = (
        db.query(RecommendationDB)
        .filter(
            RecommendationDB.goal == request.goal,
            RecommendationDB.title == request.recommendation_title,
            RecommendationDB.status == "pending",
        )
        .order_by(RecommendationDB.created_at.desc())
        .first()
    )

    if recommendation is None:
        raise ValueError("Pending recommendation not found")

    recommendation.status = request.decision

    decision = RecommendationDecisionDB(
        goal=request.goal,
        recommendation_title=request.recommendation_title,
        decision=request.decision,
    )

    db.add(decision)
    db.commit()
    db.refresh(decision)

    return decision

def approve_recommendation(
    db: Session,
    recommendation_id: int,
):
    recommendation = (
        db.query(RecommendationDB)
        .filter(
            RecommendationDB.id == recommendation_id,
            RecommendationDB.status == "pending",
        )
        .first()
    )

    if recommendation is None:
        raise ValueError("Pending recommendation not found")

    recommendation.status = "approved"

    task = TaskDB(
        title=recommendation.title,
        description=recommendation.description,
        duration_minutes=recommendation.total_minutes,
        status="pending",
    )

    db.add(task)

    db.commit()
    db.refresh(task)

    return task