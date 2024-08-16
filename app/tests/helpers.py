import json

from fastapi.testclient import TestClient
from requests.models import Response


def upload_model(client: TestClient, metadata: dict = None) -> Response:
    # First upload a model
    with open("app/tests/file_test.png", "rb") as f:
        model_file = f.read()

    if not metadata:
        metadata = {
            "name": "test2",
            "description": "test",
            "created_by": "test",
            "version_description": "test",
            "version_alias": "superhero",
        }

    return client.post(
        "/models",
        files={"model_file": ("file test.png", model_file)},
        data={"metadata": json.dumps(metadata)},
    )

