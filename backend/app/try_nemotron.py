import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).with_name(".env"))
client = OpenAI(
    base_url= os.environ["NEBIUS_BASE_URL"],
    api_key=os.environ["NEBIUS_API_KEY"],
    timeout=60.0,
    max_retries=0,
)

response = client.chat.completions.create(
    model=os.environ["NEBIUS_MODEL"],
    messages=[
        {
            "role": "system",
            "content": """Answer briefly"""
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": """Explain what an API is in one sentence."""
                }
            ]
        }
    ]
)


print(response.choices[0].message.content)