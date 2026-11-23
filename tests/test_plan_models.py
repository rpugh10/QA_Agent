"""Validate plan contracts independently of the provider and HTTP endpoints."""

import json

import pytest
from pydantic import ValidationError

from app.plan_models import TestPlan as ProposedPlan


@pytest.fixture
def plan_data():
    return {
        "cases": [{
            "name": "Create an order",
            "requirement_references": ["business_rules: rule 1"],
            "request": {"method": "POST", "path": "/orders", "body": {"total": 10}},
            "setup_requirements": [{
                "description": "A customer exists",
                "starting_data": {"customer_id": 7},
                "cleanup": "Delete the created order",
            }],
            "expected_behavior": [{
                "description": "Order is created",
                "requirement_reference": "openapi: paths./orders.post.responses.201",
                "status_code": 201,
            }],
            "clarification_questions": [],
        }],
        "clarification_questions": [],
    }


def test_plan_round_trips_json(plan_data):
    plan = ProposedPlan.model_validate_json(json.dumps(plan_data))
    assert plan.cases[0].request.body == {"total": 10}
    assert plan.cases[0].setup_requirements[0].starting_data == {"customer_id": 7}
    assert ProposedPlan.model_validate_json(plan.model_dump_json()) == plan


@pytest.mark.parametrize("status", [99, 600, "201", True])
def test_plan_rejects_invalid_status(plan_data, status):
    plan_data["cases"][0]["expected_behavior"][0]["status_code"] = status
    with pytest.raises(ValidationError):
        ProposedPlan.model_validate(plan_data)


@pytest.mark.parametrize("field,value", [
    ("method", "FETCH"), ("path", "https://example.com/orders"),
    ("path", "//example.com/orders"), ("path", "orders"),
])
def test_plan_rejects_invalid_request(plan_data, field, value):
    plan_data["cases"][0]["request"][field] = value
    with pytest.raises(ValidationError):
        ProposedPlan.model_validate(plan_data)


@pytest.mark.parametrize("field", ["name", "setup_requirements", "expected_behavior"])
def test_plan_rejects_missing_case_fields(plan_data, field):
    del plan_data["cases"][0][field]
    with pytest.raises(ValidationError):
        ProposedPlan.model_validate(plan_data)


def test_plan_rejects_blank_reference_and_unknown_fields(plan_data):
    plan_data["cases"][0]["requirement_references"] = [" \t"]
    plan_data["cases"][0]["approved"] = True
    with pytest.raises(ValidationError) as exc:
        ProposedPlan.model_validate(plan_data)
    assert {error["type"] for error in exc.value.errors()} == {
        "string_too_short", "extra_forbidden",
    }


def test_unknown_expectation_requires_question(plan_data):
    case = plan_data["cases"][0]
    case["expected_behavior"] = []
    with pytest.raises(ValidationError):
        ProposedPlan.model_validate(plan_data)
    case["clarification_questions"] = [{
        "question": "What status should an invalid total return?",
        "reason": "The supplied rule does not specify a status code.",
    }]
    plan = ProposedPlan.model_validate(plan_data)
    assert plan.cases[0].expected_behavior == []


def test_plan_can_contain_only_clarifications():
    plan = ProposedPlan(cases=[], clarification_questions=[{
        "question": "Which endpoint does the rule concern?",
        "reason": "The rule does not identify an operation.",
    }])
    assert not plan.cases


def test_plan_rejects_empty_plan():
    with pytest.raises(ValidationError):
        ProposedPlan(cases=[], clarification_questions=[])
