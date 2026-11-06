"""Shared fixtures for testing the API without real Nebius credentials."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    # The provider client is created when app.main is first imported.
    # Override configuration before that import, even if a local .env exists.
    monkeypatch.setenv("NEBIUS_BASE_URL", "https://example.invalid/v1")
    monkeypatch.setenv("NEBIUS_API_KEY", "test-key")
    monkeypatch.setenv("NEBIUS_MODEL", "test-model")

    from app import main

    def unexpected_model_call(rule):
        pytest.fail("Mock analyze_rule before testing a successful /rule request")

    # Fail locally if a test accidentally tries to use the real provider.
    monkeypatch.setattr(main, "analyze_rule", unexpected_model_call)

    def unexpected_specification_call(specification, business_rules):
        pytest.fail("Mock analyze_specification before testing a valid upload")

    monkeypatch.setattr(main, "analyze_specification", unexpected_specification_call)
    with TestClient(main.app) as test_client:
        yield test_client
