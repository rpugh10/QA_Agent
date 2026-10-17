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

def analyze_rule(rule: str) -> str:
    response = client.chat.completions.create(
        model=os.environ["NEBIUS_MODEL"],
        messages=[
            {
                "role": "system",
                "content": """You are a helpful assistant that analyzes rules and provides insights."""
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": rule
                    }
                ]
            }
        ]
    )
    answer = response.choices[0].message.content
    if not answer:
        raise ValueError("No answer received from the model.")
    return answer

if __name__ == "__main__":
    result = analyze_rule("An order total must be greater than zero")
    print(result)
