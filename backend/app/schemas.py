from pydantic import BaseModel
from typing import Literal


class Goal(BaseModel):
    title: str
    priority: Literal["low", "medium", "high"]
    target_hours: float = 0
    completed_hours: float = 0


class Activity(BaseModel):
    title: str
    hours: float


class Memory(BaseModel):
    type: Literal["goal", "preference", "commitment", "context"]
    content: str


class ReflectionRequest(BaseModel):
    goals: list[Goal]
    activities: list[Activity]
    memories: list[Memory] = []


class BiggestDrift(BaseModel):
    goal: str
    severity: Literal["low", "medium", "high"]
    reason: str


class Recommendation(BaseModel):
    title: str
    description: str
    total_minutes: int


class ReflectionResponse(BaseModel):
    biggest_drift: BiggestDrift
    explanation: str
    recommendation: Recommendation
    personalized: bool = False
    memory_used: str | None = None


class ExtractedMemory(BaseModel):
    type: Literal[
        "goal",
        "preference",
        "commitment",
        "context",
    ]

    content: str
    importance: int


class MemoryExtractionRequest(BaseModel):
    text: str


class MemoryExtractionResponse(BaseModel):
    memories: list[ExtractedMemory]


class ExtractedActivity(BaseModel):
    title: str
    hours: float
    goal_title: str | None = None


class ActivityExtractionRequest(BaseModel):
    text: str


class ActivityExtractionResponse(BaseModel):
    activities: list[ExtractedActivity]

class CheckInRequest(BaseModel):
    text: str


class CheckInResponse(BaseModel):
    activities_saved: int
    biggest_drift: BiggestDrift | None
    explanation: str
    recommendation: Recommendation | None

class TaskCreate(BaseModel):
    title: str
    description: str = ""
    duration_minutes: int = 0


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    duration_minutes: int
    status: str

class RecommendationDecisionRequest(BaseModel):
    goal: str
    recommendation_title: str
    decision: Literal["approved", "dismissed"]