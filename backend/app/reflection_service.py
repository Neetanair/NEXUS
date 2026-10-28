import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy.orm import Session

from .drift_engine import find_biggest_drift
from .models import GoalDB, ActivityDB, MemoryDB, RecommendationDB
from .progress_service import calculate_goal_progress
from .recommendation_service import save_recommendation
from .schemas import (
    Goal,
    Activity,
    Memory,
    ReflectionRequest,
    ReflectionResponse,
)


load_dotenv()


client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=os.environ["NEBIUS_API_KEY"],
)


MODEL = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"


def build_prompt(
    request: ReflectionRequest,
    biggest_drift,
    recent_recommendations: list[str],
    check_in_text: str | None = None,
) -> str:

    goals = "\n".join(
        f"- {goal.title}: "
        f"priority={goal.priority}, "
        f"target={goal.target_hours}h, "
        f"completed={goal.completed_hours}h"
        for goal in request.goals
    )

    activities = "\n".join(
        f"- {activity.title}: {activity.hours}h"
        for activity in request.activities
    )

    memories = "\n".join(
        f"- [{memory.type}] {memory.content}"
        for memory in request.memories
    )

    recommendation_history = (
        "\n".join(recent_recommendations)
        if recent_recommendations
        else "No previous recommendations."
    )

    remaining_hours = max(
        biggest_drift.target_hours
        - biggest_drift.completed_hours,
        0,
    )

    latest_check_in = check_in_text or "No check-in provided."

    return f"""
You are Nexus, an intent-aware personal AI.

Your job is to help the user make measurable progress
toward their stated goals.

The deterministic drift engine has already identified
the user's BIGGEST DRIFT.

This decision is authoritative.

You MUST NOT recalculate, reinterpret, or replace
the biggest drift goal.

Your ONLY job is to explain the drift and recommend
one concrete action for the provided goal.

AUTHORITATIVE TARGET GOAL:
{biggest_drift.title}

Priority: {biggest_drift.priority}
Target: {biggest_drift.target_hours} hours
Completed: {biggest_drift.completed_hours} hours
Remaining: {remaining_hours} hours

LATEST CHECK-IN:
{latest_check_in}

USER GOALS:
{goals}

RECENT ACTIVITIES:
{activities}

USER MEMORIES:
{memories}

RECENT RECOMMENDATION HISTORY:
{recommendation_history}

HISTORY RULES:

1. Review previous recommendations before creating a new one.

2. Do not recommend the exact same action that was already
   recommended recently.

3. If a previous recommendation was completed, advance the
   user to a natural next step toward the same goal.

4. If a previous recommendation was dismissed, avoid repeating
   it unless the current check-in provides a strong reason to
   reconsider it.

5. Recommendations should represent meaningful forward progress,
   not repetition.

6. Do not invent previous actions. Use only the recommendation
   history provided above.

PERSONALIZATION RULES:

1. Use relevant user memories when they directly help
   personalize the recommendation.

2. If a relevant preference exists, incorporate it into
   the recommended action.

3. For example, if the user prefers hands-on,
   project-based learning, prefer a practical activity
   such as building, coding, testing, or implementing
   something rather than passive reading.

4. Do not invent preferences or personal information.

5. The explanation should briefly mention the relevant
   preference when one was used, so the user can see
   why the recommendation was personalized.

6. If you actually use a memory to personalize the recommendation,
   set "personalized" to true and put the exact relevant memory
   content in "memory_used".

7. If no memory meaningfully influences the recommendation,
   set "personalized" to false and "memory_used" to null.

8. Do not claim a memory was used unless it genuinely influenced
   the recommendation.

RECOMMENDATION RULES:

1. The AUTHORITATIVE TARGET GOAL is:
   "{biggest_drift.title}"

2. You MUST recommend an action that directly advances
   "{biggest_drift.title}".

3. Do NOT choose a different goal, even if another goal
   appears complete, important, or more interesting.

4. Do NOT recommend an action primarily related to another goal.

5. Do NOT decide whether the target goal is complete.
   The deterministic engine has already made that decision.

6. Consider the user's recent activities and avoid blindly
   repeating something they just completed.

7. Use the latest check-in to understand what is realistic
   right now.

8. If the user says they are tired, overwhelmed, busy, or
   have limited time, recommend a smaller achievable action.

9. If the user gives an available amount of time, do not
   recommend more time than they have available.

10. Never recommend more time than the remaining target.

11. Use relevant memories to personalize the action.

12. Recommend exactly ONE concrete action.

13. The recommendation title should clearly describe the
    actual action.

14. The recommendation description should explain what the
    user should do, without confusing it with another goal.

15. Return ONLY valid JSON.

Return exactly:

{{
  "biggest_drift": {{
    "goal": "string",
    "severity": "low | medium | high",
    "reason": "string"
  }},
  "explanation": "string",
  "recommendation": {{
    "title": "string",
    "description": "string",
    "total_minutes": number
  }},
  "personalized": true,
  "memory_used": "exact memory content used, or null"
}}
"""


def generate_reflection(
    db: Session,
    check_in_text: str | None = None,
) -> ReflectionResponse:

    goals_db = db.query(GoalDB).all()

    activities_db = db.query(ActivityDB).all()

    memories_db = (
        db.query(MemoryDB)
        .order_by(MemoryDB.importance.desc())
        .all()
    )

    recent_recommendations_db = (
        db.query(RecommendationDB)
        .order_by(
            RecommendationDB.created_at.desc(),
            RecommendationDB.id.desc(),
        )
        .limit(5)
        .all()
    )

    if not goals_db:
        raise ValueError("No goals found")

    goals = [
        Goal(
            title=goal.title,
            priority=goal.priority,
            target_hours=goal.target_hours,
            completed_hours=calculate_goal_progress(
                db,
                goal,
            ),
        )
        for goal in goals_db
    ]

    activities = [
        Activity(
            title=activity.title,
            hours=activity.hours,
        )
        for activity in activities_db
    ]

    memories = [
        Memory(
            type=memory.type,
            content=memory.content,
        )
        for memory in memories_db
    ]

    recent_recommendations = [
        (
            f"- {recommendation.title} "
            f"(goal: {recommendation.goal}, "
            f"status: {recommendation.status})"
        )
        for recommendation in recent_recommendations_db
    ]

    request = ReflectionRequest(
        goals=goals,
        activities=activities,
        memories=memories,
    )

    biggest_drift = find_biggest_drift(request.goals)

    # Debug deterministic drift calculation.
    print("\n===== DETERMINISTIC DRIFT =====")

    for goal in request.goals:
        print(
            f"{goal.title}: "
            f"{goal.completed_hours}h / "
            f"{goal.target_hours}h "
            f"priority={goal.priority}"
        )

    if biggest_drift is None:
        print("SELECTED DRIFT: None")
    else:
        print(
            f"SELECTED DRIFT: {biggest_drift.title}"
        )

    print("===============================\n")

    if biggest_drift is None:
        raise ValueError(
            "No active goal drift detected"
        )

    prompt = build_prompt(
        request,
        biggest_drift,
        recent_recommendations,
        check_in_text=check_in_text,
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are Nexus, an intent-aware "
                    "personal AI."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError(
            "Nemotron returned an empty response"
        )

    # Debug Nemotron output.
    print("\n===== NEMOTRON RAW RESPONSE =====")
    print(content)
    print("=================================\n")

    data = json.loads(content)

    reflection = ReflectionResponse.model_validate(data)

    # The deterministic engine owns the selected goal.
    reflection.biggest_drift.goal = biggest_drift.title

    print("PERSONALIZATION:", reflection.personalized)
    print("MEMORY USED:", reflection.memory_used)

    remaining_minutes = int(
        max(
            biggest_drift.target_hours
            - biggest_drift.completed_hours,
            0,
        ) * 60
    )

    if remaining_minutes <= 0:
        raise ValueError(
            "No remaining time for recommendation"
        )

    # NEXUS recommends a small, actionable intervention.
    # Never exceed the remaining target.
    recommended_minutes = min(30, remaining_minutes)

    reflection.recommendation.total_minutes = recommended_minutes

    save_recommendation(
        db=db,
        goal=reflection.biggest_drift.goal,
        title=reflection.recommendation.title,
        description=reflection.recommendation.description,
        total_minutes=reflection.recommendation.total_minutes,
    )

    return reflection

