"""Check request validation and how provider results become HTTP responses."""

from unittest.mock import Mock

import httpx
import pytest
from openai import APITimeoutError, AuthenticationError, NotFoundError

# Testing valid input for the /rule endpoint
def test_rule_returns_model_answer(client, monkeypatch):
    from app import main

    analyze = Mock(return_value="The order total must be positive.")
    monkeypatch.setattr(main, "analyze_rule", analyze)

    response = client.post("/rule", json={"rule": "Order total must exceed zero"})

    assert response.status_code == 200
    assert response.json() == {"answer": "The order total must be positive."}
    analyze.assert_called_once_with("Order total must exceed zero")


# Testing invalid input for the /rule endpoint
@pytest.mark.parametrize("payload", [{}, {"rule": ""}, {"rule": None}])
def test_rule_rejects_missing_or_empty_rule(client, payload):
    response = client.post("/rule", json=payload)

    assert response.status_code == 422

# Testing how provider errors are translated into HTTP responses
@pytest.mark.parametrize(
    "error_type, provider_status, expected_status, detail",
    [
        (APITimeoutError, None, 504, "Request to the model timed out."),
        (AuthenticationError, 401, 502, "Invalid API key."),
        (NotFoundError, 404, 502, "Model not found."),
    ],
)

# Testing the translation of provider errors into HTTP responses
def test_rule_translates_provider_errors(
    client, monkeypatch, error_type, provider_status, expected_status, detail
):
    from app import main

    request = httpx.Request("POST", "https://example.invalid/v1/chat/completions")
    if error_type is APITimeoutError:
        error = error_type(request=request)
    else:
        error = error_type(
            "Provider error",
            response=httpx.Response(provider_status, request=request),
            body=None,
        )
    monkeypatch.setattr(main, "analyze_rule", Mock(side_effect=error))

    response = client.post("/rule", json={"rule": "Order total must exceed zero"})

    assert response.status_code == expected_status
    assert response.json() == {"detail": detail}
