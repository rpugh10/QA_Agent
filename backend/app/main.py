from fastapi import FastAPI

from pydantic import BaseModel, Field

app = FastAPI()

class BusinessRuleEndpoint(BaseModel):
    rule: str = Field(min_length=1)

@app.post("/rule")
def create_rule(item: BusinessRuleEndpoint):
    return item

@app.get("/health")
def health_check():
    return {"status": "ok"}

d