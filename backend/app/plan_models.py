"""Data contracts for proposed plans, not executable tests or execution results."""

from typing import Annotated, Literal

from pydantic import (
    BaseModel, ConfigDict, Field, JsonValue, StringConstraints, model_validator,
)


NonBlank = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class PlanModel(BaseModel):
    # Reject unexpected fields and coercions such as a string status code.
    model_config = ConfigDict(extra="forbid", strict=True)


class ExpectedBehavior(PlanModel):
    description: NonBlank
    requirement_reference: NonBlank = Field(
        description="Location in the supplied specification or business rules supporting this expectation."
    )
    status_code: int | None = Field(default=None, ge=100, le=599)


class SetupRequirement(PlanModel):
    description: NonBlank
    starting_data: dict[str, JsonValue] = Field(default_factory=dict)
    cleanup: NonBlank | None = Field(
        default=None, description="Reset/cleanup instructions, if known; null means unspecified."
    )


class ClarificationQuestion(PlanModel):
    question: NonBlank
    reason: NonBlank
    requirement_reference: NonBlank | None = None


class PlannedRequest(PlanModel):
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE"]
    path: Annotated[NonBlank, Field(pattern=r"^/([^/].*)?$")] = Field(
        description="OpenAPI path, such as /orders/{order_id}; not a target server URL."
    )
    path_parameters: dict[str, JsonValue] = Field(default_factory=dict)
    query_parameters: dict[str, JsonValue] = Field(default_factory=dict)
    headers: dict[str, NonBlank] = Field(default_factory=dict)
    body: JsonValue = None


class TestCase(PlanModel):
    name: NonBlank
    requirement_references: list[NonBlank] = Field(min_length=1)
    request: PlannedRequest
    setup_requirements: list[SetupRequirement]
    expected_behavior: list[ExpectedBehavior]
    clarification_questions: list[ClarificationQuestion]

    @model_validator(mode="after")
    def require_expectation_or_clarification(self):
        if not self.expected_behavior and not self.clarification_questions:
            raise ValueError("A case needs expected behavior or a clarification question.")
        return self


class TestPlan(PlanModel):
    # Both lists must be supplied explicitly; a clarification-only plan is valid.
    cases: list[TestCase]
    clarification_questions: list[ClarificationQuestion]

    @model_validator(mode="after")
    def require_case_or_clarification(self):
        if not self.cases and not self.clarification_questions:
            raise ValueError("A plan needs a case or a clarification question.")
        return self
