"""Exercise multipart uploads using small, in-memory files."""

import json
from unittest.mock import Mock

import httpx
import pytest
from openai import APITimeoutError, AuthenticationError, NotFoundError


## Test fixtures and helper functions
@pytest.fixture
def specification():
    return {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0"},
        "paths": {},
    }


# Helper function to upload a file and rule to the /upload endpoint.
def upload(client, content):
    return client.post(
        "/upload",
        files={"file": ("openapi.json", content, "application/json")},
        data={"rule": "Order total must exceed zero"},
    )

# Test that the upload endpoint accepts a valid OpenAPI specification and returns the expected response.
def test_upload_accepts_specification(client, specification, monkeypatch):
    from app import main

    analyze = Mock(return_value="Check that order totals are positive.")
    # Patch where the endpoint looks up the function, not its original module.
    monkeypatch.setattr(main, "analyze_specification", analyze)
    content = json.dumps(specification).encode("utf-8")

    response = upload(client, content)

    assert response.status_code == 200
    assert response.json() == {
        "filename": "openapi.json",
        "size_bytes": len(content),
        "rule": "Order total must exceed zero",
        "answer": "Check that order totals are positive.",
    }
    analyze.assert_called_once_with(specification, "Order total must exceed zero")


@pytest.mark.parametrize(
    "error_type, provider_status, expected_status, detail",
    [
        (APITimeoutError, None, 504, "Request to the model timed out."),
        (AuthenticationError, 401, 502, "Invalid API key."),
        (NotFoundError, 404, 502, "Model not found."),
    ],
)
def test_upload_translates_provider_errors(
    client, specification, monkeypatch,
    error_type, provider_status, expected_status, detail,
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
    analyze = Mock(side_effect=error)
    monkeypatch.setattr(main, "analyze_specification", analyze)

    response = upload(client, json.dumps(specification).encode("utf-8"))

    assert response.status_code == expected_status
    assert response.json() == {"detail": detail}
    analyze.assert_called_once_with(specification, "Order total must exceed zero")


# Test that the upload endpoint rejects invalid files, including empty files, non-JSON files, and files that exceed the size limit.
@pytest.mark.parametrize(
    "content, status, detail",
    [
        (b"", 400, "Uploaded file is empty."),
        (b"not json", 400, "Uploaded file is not a valid JSON."),
        (b"\xff", 400, "Uploaded file is not a valid JSON."),
        (b"[]", 400, "The specification must be a JSON object."),
        (b"null", 400, "The specification must be a JSON object."),
        (b"42", 400, "The specification must be a JSON object."),
        (b'{"openapi":', 400, "Uploaded file is not a valid JSON."),
        (b"x" * (1024 * 1024 + 1), 413, "File size exceeds 1 MiB limit."),
    ],
)
# Test that the upload endpoint rejects invalid files, including empty files, non-JSON files, and files that exceed the size limit.
def test_upload_rejects_invalid_files(client, content, status, detail):
    response = upload(client, content)

    assert response.status_code == status
    assert response.json() == {"detail": detail}


# Test that the upload endpoint rejects specifications with invalid 'openapi', 'info', or 'paths' fields.
@pytest.mark.parametrize(
    "field, value, detail",
    [
        ("openapi", "2.0", "The specification must declare an OpenAPI 3.x version in 'openapi'."),
        ("info", [], "The specification's 'info' must be a JSON object."),
        ("paths", [], "The specification's 'paths' must be a JSON object."),
    ],
)
def test_upload_rejects_invalid_specification_fields(client, specification, field, value, detail):
    specification[field] = value

    response = upload(client, json.dumps(specification).encode("utf-8"))

    assert response.status_code == 400
    assert response.json() == {"detail": detail}


# Test that the upload endpoint requires the 'info.title' and 'info.version' fields to be nonempty strings.
@pytest.mark.parametrize("field", ["title", "version"])
@pytest.mark.parametrize("value", [None, "", "   ", "\t\r\n", 123, True, [], {}])
def test_upload_requires_info_fields(client, specification, field, value):
    specification["info"][field] = value

    response = upload(client, json.dumps(specification).encode("utf-8"))

    assert response.status_code == 400
    assert response.json() == {
        "detail": f"The specification's 'info.{field}' must be a nonempty string."
    }


# Test that the upload endpoint rejects specifications that are missing required 'info' fields.
@pytest.mark.parametrize("field", ["title", "version"])
def test_upload_rejects_missing_info_fields(client, specification, field):
    del specification["info"][field]

    response = upload(client, json.dumps(specification).encode("utf-8"))

    assert response.status_code == 400
    assert response.json() == {
        "detail": f"The specification's 'info.{field}' must be a nonempty string."
    }


# Test that the upload endpoint requires the 'info' and 'paths' fields to be JSON objects.
@pytest.mark.parametrize("field", ["info", "paths"])
@pytest.mark.parametrize("value", [None, [], "", 123, True])
def test_upload_requires_object_fields(client, specification, field, value):
    specification[field] = value

    response = upload(client, json.dumps(specification).encode("utf-8"))

    assert response.status_code == 400
    assert response.json() == {
        "detail": f"The specification's '{field}' must be a JSON object."
    }


# Test that the upload endpoint rejects specifications that are missing required fields.
@pytest.mark.parametrize("field", ["openapi", "info", "paths"])
def test_upload_rejects_missing_specification_fields(client, specification, field):
    del specification[field]

    response = upload(client, json.dumps(specification).encode("utf-8"))

    assert response.status_code == 400
    assert "detail" in response.json()


# Test that the upload endpoint requires both a file and a rule to be provided.
@pytest.mark.parametrize("missing", ["file", "rule"])
def test_upload_requires_file_and_rule(client, missing):
    kwargs = {
        "files": {"file": ("openapi.json", b"{}", "application/json")},
        "data": {"rule": "Order total must exceed zero"},
    }
    del kwargs["files" if missing == "file" else "data"]

    response = client.post("/upload", **kwargs)

    assert response.status_code == 422
