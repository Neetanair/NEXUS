import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy.orm import Session

from .models import MemoryDB
from .schemas import (
    ExtractedMemory,
    MemoryExtractionResponse,
)


load_dotenv()


client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=os.environ["NEBIUS_API_KEY"],
)


MODEL = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"


def extract_memories(
    text: str,
) -> MemoryExtractionResponse:

    prompt = f"""
You are Nexus, a personal AI memory system.

Analyze the user's statement and identify information
that would be useful for personalizing future assistance.

Only extract durable information.

Good memories include:
- preferences
- long-term goals
- commitments
- stable personal context

Do NOT extract:
- temporary conversational details
- obvious facts that are not useful later
- guesses about the user
- information not explicitly stated

USER STATEMENT:
{text}

Return ONLY valid JSON.

Return exactly:

{{
  "memories": [
    {{
      "type": "goal | preference | commitment | context",
      "content": "concise memory",
      "importance": 1
    }}
  ]
}}

Importance must be:
1 = mildly useful
2 = useful
3 = highly useful
"""


    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You extract durable personal "
                    "memories for Nexus."
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

    return MemoryExtractionResponse.model_validate(data)


def save_memories(
    db: Session,
    memories: list[ExtractedMemory],
):
    saved = []

    for memory in memories:

        # Basic safety/quality filter.
        if not memory.content.strip():
            continue

        if memory.importance < 1:
            continue

        if memory.importance > 3:
            memory.importance = 3

        # Avoid exact duplicate memories.
        existing = (
            db.query(MemoryDB)
            .filter(
                MemoryDB.content == memory.content
            )
            .first()
        )

        if existing:
            continue

        db_memory = MemoryDB(
            type=memory.type,
            content=memory.content,
            importance=memory.importance,
        )

        db.add(db_memory)
        saved.append(db_memory)

    db.commit()

    for memory in saved:
        db.refresh(memory)

    return saved