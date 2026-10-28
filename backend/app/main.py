from fastapi import Depends
from sqlalchemy.orm import Session
from .models import GoalDB

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from .recommendation_service import (
    get_latest_recommendation,
    save_recommendation_decision,
    approve_recommendation,
)

from .schemas import RecommendationDecisionRequest
from .dashboard_service import get_dashboard_data

from .database import get_db
from .models import MemoryDB

from .schemas import TaskCreate
from .task_service import (
    create_task,
    get_tasks,
    complete_task,
)

from .schemas import (
    MemoryExtractionRequest,
    ActivityExtractionRequest,
    CheckInRequest,
    ReflectionResponse,
)

from .checkin_service import process_checkin

from .schemas import (
    MemoryExtractionRequest,
    ReflectionResponse,
)
from .activity_service import (
    extract_activities,
    save_activities,
)

from .schemas import (
    ActivityExtractionRequest,
)

from sqlalchemy.orm import Session
from fastapi import Depends

from .reflection_service import generate_reflection

from fastapi import FastAPI, HTTPException

from .memory_service import (
    extract_memories,
    save_memories,
)

from .schemas import (
    ReflectionRequest,
    ReflectionResponse,
)

from .models import (
    GoalDB,
    ActivityDB,
    MemoryDB,
)

from .reflection_service import generate_reflection
from .database import Base, engine
from . import models

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Nexus Personal AI",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "name": "Nexus",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }

@app.post("/goals")
def create_goal(
    title: str,
    priority: str,
    target_hours: float,
    db: Session = Depends(get_db),
):
    goal = GoalDB(
        title=title,
        priority=priority,
        target_hours=target_hours,
        completed_hours=0,
    )

    db.add(goal)
    db.commit()
    db.refresh(goal)

    return goal


@app.post("/activities")
def create_activity(
    title: str,
    hours: float,
    db: Session = Depends(get_db),
):
    activity = ActivityDB(
        title=title,
        hours=hours,
    )

    db.add(activity)
    db.commit()
    db.refresh(activity)

    return activity

@app.post(
    "/reflection",
    response_model=ReflectionResponse,
)
def reflection(
    db: Session = Depends(get_db),
):
    try:
        return generate_reflection(db)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@app.post("/memories")
def create_memory(
    memory_type: str,
    content: str,
    db: Session = Depends(get_db),
):
    memory = MemoryDB(
        type=memory_type,
        content=content,
        importance=1,
    )

    db.add(memory)
    db.commit()
    db.refresh(memory)

    return {
        "id": memory.id,
        "type": memory.type,
        "content": memory.content,
    }

@app.get("/memories")
def get_memories(
    db: Session = Depends(get_db),
):
    memories = (
        db.query(MemoryDB)
        .order_by(
            MemoryDB.importance.desc(),
            MemoryDB.id.desc(),
        )
        .all()
    )

    return [
        {
            "id": memory.id,
            "type": memory.type,
            "content": memory.content,
            "importance": memory.importance,
        }
        for memory in memories
    ]

@app.post("/memories/extract")
def extract_and_save_memories(
    request: MemoryExtractionRequest,
    db: Session = Depends(get_db),
):
    try:
        result = extract_memories(
            request.text
        )

        saved = save_memories(
            db,
            result.memories,
        )

        return {
            "extracted": len(result.memories),
            "saved": len(saved),
            "memories": [
                {
                    "id": memory.id,
                    "type": memory.type,
                    "content": memory.content,
                    "importance": memory.importance,
                }
                for memory in saved
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

@app.post("/activities/extract")
def extract_and_save_activities(
    request: ActivityExtractionRequest,
    db: Session = Depends(get_db),
):
    try:

        goals = db.query(GoalDB).all()

        goal_titles = [
            goal.title
            for goal in goals
        ]

        result = extract_activities(
            request.text,
            goal_titles,
        )

        saved = save_activities(
            db,
            result.activities,
            goals,
        )

        return {
            "extracted": len(result.activities),
            "saved": len(saved),
            "activities": [
                {
                    "id": activity.id,
                    "title": activity.title,
                    "hours": activity.hours,
                    "goal_id": activity.goal_id,
                }
                for activity in saved
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@app.post("/check-in")
def check_in(
    request: CheckInRequest,
    db: Session = Depends(get_db),
):
    try:
        return process_checkin(
            db,
            request.text,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

@app.post("/tasks")
def create_new_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
):
    return create_task(db, task)

@app.get("/tasks")
def list_tasks(
    db: Session = Depends(get_db),
):
    return get_tasks(db)

@app.post("/tasks/{task_id}/complete")
def mark_task_complete(
    task_id: int,
    db: Session = Depends(get_db),
):
    task = complete_task(db, task_id)

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    return task

@app.post("/recommendations/decision")
def recommendation_decision(
    request: RecommendationDecisionRequest,
    db: Session = Depends(get_db),
):
    try:
        return save_recommendation_decision(db, request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    try:
        return get_dashboard_data(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recommendations/latest")
def latest_recommendation(db: Session = Depends(get_db)):
    try:
        recommendation = get_latest_recommendation(db)

        if recommendation is None:
            return None

        return {
            "id": recommendation.id,
            "goal": recommendation.goal,
            "title": recommendation.title,
            "description": recommendation.description,
            "total_minutes": recommendation.total_minutes,
            "status": recommendation.status,
            "created_at": recommendation.created_at.isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommendations/{recommendation_id}/approve")
def approve_recommendation_endpoint(
    recommendation_id: int,
    db: Session = Depends(get_db),
):
    try:
        task = approve_recommendation(
            db,
            recommendation_id,
        )

        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "duration_minutes": task.duration_minutes,
            "status": task.status,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )



