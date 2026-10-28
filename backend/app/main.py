
from fastapi import FastAPI

from pydantic import BaseModel, Field

from fastapi import HTTPException
from openai import APITimeoutError, AuthenticationError, NotFoundError
from fastapi import File, Form, UploadFile
import json

from app.try_nemotron import analyze_rule

app = FastAPI()

class BusinessRuleEndpoint(BaseModel):
    rule: str = Field(min_length=1)

@app.post("/rule")
def create_rule(item: BusinessRuleEndpoint):
    try:
        answer = analyze_rule(item.rule)
    except APITimeoutError as exc:
        raise HTTPException(status_code=504, detail="Request to the model timed out.") from exc
    except AuthenticationError as exc:
        raise HTTPException(status_code=502, detail="Invalid API key.") from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=502, detail="Model not found.") from exc
    return {"answer": answer}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), rule: str = Form(..., min_length=1)):
    content = await file.read(1024 * 1024 + 1)  # Read up to 1 MiB + 1 byte
    if len(content) > 1024 * 1024:
        raise HTTPException(status_code=413, detail="File size exceeds 1 MiB limit.")
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    try:
        specification = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid JSON.") from exc
    if not isinstance(specification, dict):
        raise HTTPException(status_code=400,detail="The specification must be a JSON object."
        )
    openapi_version = specification.get("openapi")
    if not isinstance(openapi_version, str) or not openapi_version.startswith("3."):
        raise HTTPException(
            status_code=400,
            detail="The specification must declare an OpenAPI 3.x version in 'openapi'."
        )
    return {"filename": file.filename, "size_bytes": len(content), "rule": rule}





