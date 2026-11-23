"""Manual, billable smoke test. Run from the repository root; never used by CI."""

import os
from urllib.parse import urlparse

from app.try_nemotron import analyze_specification, client


def main():
    host = urlparse(str(client.base_url)).hostname
    model = os.environ.get("NEBIUS_MODEL", "").lower()
    if host != "api.tokenfactory.nebius.com" or not (
        "nvidia" in model and "nemotron" in model
    ):
        print("Smoke test skipped: configure Nebius Token Factory and NVIDIA Nemotron.")
        return 2

    specification = {
        "openapi": "3.0.3",
        "info": {"title": "Milestone smoke test", "version": "1.0"},
        "paths": {"/health": {"get": {
            "responses": {"200": {"description": "Healthy"}},
        }}},
    }
    try:
        analyze_specification(
            specification,
            "GET /health must return HTTP 200. Propose one concise scenario; do not execute it.",
        )
    except Exception as exc:
        # Avoid printing provider response bodies, credentials, or generated content.
        print(f"Live specification analysis failed: {type(exc).__name__}")
        return 1

    print("Nebius Token Factory / NVIDIA Nemotron: nonempty answer received.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
