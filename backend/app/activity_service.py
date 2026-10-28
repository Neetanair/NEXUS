import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy.orm import Session

from .models import ActivityDB
from .schemas import (
    ExtractedActivity,
    ActivityExtractionResponse,
)


load_dotenv()


client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=os.environ["NEBIUS_API_KEY"],
)


MODEL = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"


def extract_activities(
    text: str,
    goals: list[str],
) -> ActivityExtractionResponse:
    goal_list = "\n".join(
    f"- {goal}"
    for goal in goals
)

    prompt = f"""
    You are Nexus, a personal AI activity tracker.

    Extract the activities explicitly mentioned by the user.

    Convert durations into decimal hours.

    Available user goals:

    {goal_list}

    For each activity, determine which goal it contributes
    to based on the SUBJECT or PURPOSE of the activity,
    not merely a shared word.

    Important:
    - Match based on meaning and subject.
    - "ROS2 exercise" belongs to "Learn ROS2".
    - "30 minute ROS2 exercise" belongs to "Learn ROS2".
    - The word "exercise" by itself does NOT mean the user's
    physical Exercise goal.
    - Physical workouts, running, gym, walking, etc. belong
    to an Exercise goal.
    - If there is no clear semantic match, use null.

    Return the exact goal title.
    Do not invent or modify goal titles.

    If it clearly matches a goal, return that goal's
    exact title as goal_title.

    If there is no clear match, use null.

    Do not invent activities.
    Do not invent goal relationships.

    Examples:

    "30 minutes of ROS2"
    => 0.5 hours

    "1 hour and 30 minutes of exercise"
    => 1.5 hours

    USER STATEMENT:
    {text}

    Return ONLY valid JSON.

    Return exactly:

    {{
    "activities": [
        {{
        "title": "string",
        "hours": number,
        "goal_title": "string | null"
        }}
    ]
    }}
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You extract structured activity "
                    "data for Nexus."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    content = response.choices[0].message.content

    data = json.loads(content)

    return ActivityExtractionResponse.model_validate(data)


def save_activities(
    db: Session,
    activities: list[ExtractedActivity],
    goals,
):

    saved = []

    for activity in activities:

        if not activity.title.strip():
            continue

        if activity.hours <= 0:
            continue

        goal_id = None

        if activity.goal_title:

            matching_goal = next(
                (
                    goal
                    for goal in goals
                    if goal.title == activity.goal_title
                ),
                None,
            )

            if matching_goal:
                goal_id = matching_goal.id

        db_activity = ActivityDB(
            title=activity.title,
            hours=activity.hours,
            goal_id=goal_id,
        )

        db.add(db_activity)
        saved.append(db_activity)

    db.commit()

    for activity in saved:
        db.refresh(activity)

    return saved