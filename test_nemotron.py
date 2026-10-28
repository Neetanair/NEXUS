import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=os.environ["NEBIUS_API_KEY"]
)

prompt = """
You are Nexus, an intent-aware personal AI.

Your job is to analyze whether a user's activities align
with their stated goals.

IMPORTANT RULES:

1. Prioritize goals according to their priority level.
2. Use the numerical data provided.
3. Do not recommend more time than the user's remaining
   target unless there is a strong reason.
4. Recommend ONE concrete action.
5. Personalize the recommendation using the user's memories.
6. Return ONLY valid JSON.

USER GOALS:

- Learn ROS2
  Priority: HIGH
  Weekly target: 3 hours
  Completed: 0 hours
  Remaining: 3 hours

- Exercise
  Priority: MEDIUM
  Weekly target: 3 sessions
  Completed: 2 sessions
  Remaining: 1 session

USER ACTIVITIES:

- Frontend work: 8 hours
- Meetings: 4 hours
- ROS2: 0 hours

USER MEMORY:

- User prefers learning through projects.

Return JSON in exactly this format:

{
  "biggest_drift": {
    "goal": "string",
    "severity": "low | medium | high",
    "reason": "string"
  },
  "explanation": "string",
  "recommendation": {
    "title": "string",
    "description": "string",
    "total_minutes": number
  }
}
"""

response = client.chat.completions.create(
    model="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
    messages=[
        {
            "role": "system",
            "content": "You are Nexus, a helpful intent-aware personal AI."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
)

# print(response.choices[0].message.content)

content = response.choices[0].message.content

print("Raw response:")
print(content)

print("\nParsed JSON:")

data = json.loads(content)

print("Biggest drift:", data["biggest_drift"]["goal"])
print("Severity:", data["biggest_drift"]["severity"])
print("Recommendation:", data["recommendation"]["title"])
print("Minutes:", data["recommendation"]["total_minutes"])