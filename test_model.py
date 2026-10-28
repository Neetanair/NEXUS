import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=os.environ["NEBIUS_API_KEY"]
)

models = client.models.list()

# for model in models.data:
#     print(model.id)

for model in models.data:
    if "nemotron" in model.id.lower():
        print(model.id)