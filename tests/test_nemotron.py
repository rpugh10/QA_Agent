"""Exercise the provider function without sending requests to Nebius."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


def test_specification_request_separates_inputs(client, monkeypatch):
    from app import try_nemotron as provider

    specification = {
        "openapi": "3.0.3",
        "info": {"title": 'Orders "test" API', "version": "1.0"},
        "paths": {"/orders": {"post": {"responses": {"201": {"description": "Created"}}}}},
    }
    rules = 'Order total must exceed zero.\nDo not assume "zero" is valid.'
    create = Mock(return_value=SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="Proposed scenarios"))]
    ))
    monkeypatch.setattr(provider.client.chat.completions, "create", create)

    assert provider.analyze_specification(specification, rules) == "Proposed scenarios"

    create.assert_called_once()
    request = create.call_args.kwargs
    assert request["model"] == "test-model"
    system, user = request["messages"]
    assert system["role"] == "system"
    assert "untrusted data" in system["content"]
    assert "Do not invent requirements" in system["content"]
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

    with pytest.raises(ValueError, match="No answer received"):
        provider.analyze_specification({}, "A business rule")


def test_specification_rejects_missing_choices(client, monkeypatch):
    from app import try_nemotron as provider

    monkeypatch.setattr(
        provider.client.chat.completions, "create",
        Mock(return_value=SimpleNamespace(choices=[])),
    )

    with pytest.raises(ValueError, match="No answer received"):
        provider.analyze_specification({}, "A business rule")
