"""Exercise multipart uploads using small, in-memory files."""

import json

import pytest


@pytest.fixture
def specification():
    return {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0"},
        "paths": {},
    }


def upload(client, content):
    return client.post(
        "/upload",
        files={"file": ("openapi.json", content, "application/json")},
        data={"rule": "Order total must exceed zero"},
    )


def test_upload_accepts_specification(client, specification):
    content = json.dumps(specification).encode("utf-8")

    response = upload(client, content)

    assert response.status_code == 200
    assert response.json() == {
        "filename": "openapi.json",
        "size_bytes": len(content),
        "rule": "Order total must exceed zero",
    }


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
def test_upload_rejects_invalid_files(client, content, status, detail):
    response = upload(client, content)

    assert response.status_code == status
    assert response.json() == {"detail": detail}


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


@pytest.mark.parametrize("field", ["title", "version"])
@pytest.mark.parametrize("value", [None, "", "   ", "\t\r\n", 123, True, [], {}])
def test_upload_requires_info_fields(client, specification, field, value):
    specification["info"][field] = value

    response = upload(client, json.dumps(specification).encode("utf-8"))

    assert response.status_code == 400
    assert response.json() == {
        "detail": f"The specification's 'info.{field}' must be a nonempty string."
    }


@pytest.mark.parametrize("field", ["title", "version"])
def test_upload_rejects_missing_info_fields(client, specification, field):
    del specification["info"][field]

    response = upload(client, json.dumps(specification).encode("utf-8"))

    assert response.status_code == 400
    assert response.json() == {
        "detail": f"The specification's 'info.{field}' must be a nonempty string."
    }


@pytest.mark.parametrize("field", ["info", "paths"])
@pytest.mark.parametrize("value", [None, [], "", 123, True])
def test_upload_requires_object_fields(client, specification, field, value):
    specification[field] = value

    response = upload(client, json.dumps(specification).encode("utf-8"))

    assert response.status_code == 400
    assert response.json() == {
        "detail": f"The specification's '{field}' must be a JSON object."
    }


@pytest.mark.parametrize("field", ["openapi", "info", "paths"])
def test_upload_rejects_missing_specification_fields(client, specification, field):
    del specification[field]

    response = upload(client, json.dumps(specification).encode("utf-8"))

    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.parametrize("missing", ["file", "rule"])
def test_upload_requires_file_and_rule(client, missing):
    kwargs = {
        "files": {"file": ("openapi.json", b"{}", "application/json")},
        "data": {"rule": "Order total must exceed zero"},
    }
    del kwargs["files" if missing == "file" else "data"]

    response = client.post("/upload", **kwargs)

    assert response.status_code == 422
