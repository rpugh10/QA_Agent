"""Exercise the provider function without sending requests to Nebius."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import httpx
from openai import APIConnectionError


def test_specification_request_separates_inputs(client, monkeypatch, clarification_plan):
    from app import try_nemotron as provider

    specification = {
        "openapi": "3.0.3",
        "info": {"title": 'Orders "test" API', "version": "1.0"},
        "paths": {"/orders": {"post": {"responses": {"201": {"description": "Created"}}}}},
    }
    rules = 'Order total must exceed zero.\nDo not assume "zero" is valid.'
    create = Mock(return_value=SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=clarification_plan.model_dump_json()))]
    ))
    monkeypatch.setattr(provider.client.chat.completions, "create", create)

    assert provider.analyze_specification(specification, rules) == clarification_plan

    create.assert_called_once()
    request = create.call_args.kwargs
    assert request["model"] == "test-model"
    system, user = request["messages"]
    assert system["role"] == "system"
    assert "untrusted data" in system["content"]
    assert "Do not invent requirements" in system["content"]
    assert "JSON schema:" in system["content"]
    assert "expected_behavior" in system["content"]
    assert user["role"] == "user"
    assert json.loads(user["content"][0]["text"]) == {
        "openapi_specification": specification,
        "business_rules": rules,
    }


@pytest.mark.parametrize("answer", [None, "", " \t\n"])
def test_specification_rejects_empty_answer(client, monkeypatch, answer):
    from app import try_nemotron as provider

    create = Mock(return_value=SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=answer))]
    ))
    monkeypatch.setattr(provider.client.chat.completions, "create", create)

    with pytest.raises(provider.InvalidPlanError, match="after 2 attempts"):
        provider.analyze_specification({}, "A business rule")
    assert create.call_count == 2


def test_specification_rejects_missing_choices(client, monkeypatch):
    from app import try_nemotron as provider

    monkeypatch.setattr(
        provider.client.chat.completions, "create",
        Mock(return_value=SimpleNamespace(choices=[])),
    )

    with pytest.raises(provider.InvalidPlanError, match="after 2 attempts"):
        provider.analyze_specification({}, "A business rule")


@pytest.mark.parametrize("invalid", ["not JSON", "{}", '{"cases": [], "clarification_questions": []}',
                                      '```json\n{}\n```'])
def test_invalid_plan_gets_one_retry(client, monkeypatch, clarification_plan, invalid):
    from app import try_nemotron as provider

    def response(text):
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])

    create = Mock(side_effect=[response(invalid), response(clarification_plan.model_dump_json())])
    monkeypatch.setattr(provider.client.chat.completions, "create", create)

    assert provider.analyze_specification({}, "An ambiguous rule") == clarification_plan
    assert create.call_count == 2
    retry_messages = create.call_args.kwargs["messages"]
    assert "previous attempt" in retry_messages[0]["content"]
    assert retry_messages[1] == create.call_args_list[0].kwargs["messages"][1]


def test_connection_errors_are_not_retried(client, monkeypatch):
    from app import try_nemotron as provider

    create = Mock(side_effect=APIConnectionError(request=httpx.Request("POST", "https://example.invalid")))
    monkeypatch.setattr(provider.client.chat.completions, "create", create)
    with pytest.raises(APIConnectionError):
        provider.analyze_specification({}, "A rule")
    create.assert_called_once()
