import json

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from ..database.models import Alias, Version
from .helpers import upload_model


def test_upload_model_version_happy_path(client: TestClient, session: Session) -> None:
    response = upload_model(client)

    assert response.status_code == 200, "Failed to upload model"

    model_id = 1
    metadata = {
        "description": "test",
        "created_by": "test",
        "alias": "test",
        "tags": {"test": "test"},
        "metrics": {"accuracy": 0.99, "loss": 0.01},
        "parameters": {"epochs": 10, "batch_size": 32},
    }

    with open("app/tests/file_test.png", "rb") as f:
        model_file = f.read()

    response = client.post(
        f"/models/{model_id}/version",
        files={"model_file": ("file test.png", model_file)},
        data={"metadata": json.dumps(metadata)},
    )

    assert response.status_code == 200, "Failed to upload model version"

    # Check if the version was uploaded correctly
    statement = select(Version).where(
        Version.model_id == model_id, Version.version_number == 2
    )
    version = session.exec(statement).first()

    assert version is not None, "Version was not uploaded"
    assert version.description == metadata["description"]
    assert version.created_by == metadata["created_by"]
    assert version.tags == metadata["tags"]
    assert version.metrics == metadata["metrics"]
    assert version.parameters == metadata["parameters"]
    assert version.file_name == "file_test.png"
    assert version.version_number == 2


def test_upload_model_version_model_not_found(client: TestClient) -> None:
    response = upload_model(client)

    assert response.status_code == 200, "Failed to upload model"

    model_id = 2
    metadata = {
        "description": "test",
        "created_by": "test",
        "alias": "test",
        "tags": {"test": "test"},
        "metrics": {"accuracy": 0.99, "loss": 0.01},
        "parameters": {"epochs": 10, "batch_size": 32},
    }

    with open("app/tests/file_test.png", "rb") as f:
        model_file = f.read()

    response = client.post(
        f"/models/{model_id}/version",
        files={"model_file": ("file test.png", model_file)},
        data={"metadata": json.dumps(metadata)},
    )

    assert response.status_code == 404, "Failed to upload model version"


def test_upload_model_version_invalid_metadata(client: TestClient) -> None:
    response = upload_model(client)

    assert response.status_code == 200, "Failed to upload model"

    model_id = 1
    metadata = {
        "description": "test",
        "created_by": "test",
        "alias": "test",
        "tags": {"test": "test"},
        "metrics": {"accuracy": 0.99, "loss": 0.01},
        "parameters": "bla bla",
    }

    with open("app/tests/file_test.png", "rb") as f:
        model_file = f.read()

    response = client.post(
        f"/models/{model_id}/version",
        files={"model_file": ("file test.png", model_file)},
        data={"metadata": json.dumps(metadata)},
    )

    assert response.status_code == 422, "It should have failed to upload model version"


def test_upload_model_version_alias_already_exists(
    client: TestClient
) -> None:
    response = upload_model(client)

    assert response.status_code == 200, "Failed to upload model"

    model_id = 1
    metadata = {
        "description": "test",
        "created_by": "test",
        "alias": "superhero",
        "tags": {"test": "test"},
        "metrics": {"accuracy": 0.99, "loss": 0.01},
        "parameters": {"epochs": 10, "batch_size": 32},
    }

    with open("app/tests/file_test.png", "rb") as f:
        model_file = f.read()

    response = client.post(
        f"/models/{model_id}/version",
        files={"model_file": ("file test.png", model_file)},
        data={"metadata": json.dumps(metadata)},
    )

    assert response.status_code == 400, "It should have failed to upload model version"


def test_get_model_version_happy_path(client: TestClient) -> None:
    response = upload_model(client)

    assert response.status_code == 200, "Failed to upload model"

    model_id = 1
    version_id = 1
    response = client.get(f"/models/{model_id}/versions/{version_id}")

    assert response.status_code == 200, "Failed to get model version"


def test_get_model_version_model_or_version_not_found(
    client: TestClient
) -> None:
    response = upload_model(client)

    assert response.status_code == 200, "Failed to upload model"

    model_id = 2
    version_id = 1
    response = client.get(f"/models/{model_id}/versions/{version_id}")

    assert response.status_code == 404, "This should have failed to get model version"

    model_id = 1
    version_id = 3
    response = client.get(f"/models/{model_id}/versions/{version_id}")

    assert response.status_code == 404, "This should have failed to get model version"


def test_delete_model_version_happy_path(client: TestClient, session: Session) -> None:
    response = upload_model(client)

    assert response.status_code == 200, "Failed to upload model"

    model_id = 1
    version_number = 1
    response = client.delete(f"/models/{model_id}/versions/{version_number}")

    assert response.status_code == 200, "Failed to delete model version"

    # Check if the version was deleted correctly
    statement = select(Version).where(
        Version.model_id == model_id, Version.version_number == version_number
    )
    version = session.exec(statement).first()

    assert version is None, "Version was not deleted"

    # Check if the corresponding alias was deleted
    statement = select(Alias).where(Alias.name == "superhero")
    alias = session.exec(statement).first()

    assert alias is None, "Alias was not deleted"


def test_delete_model_version_model_or_version_not_found(
    client: TestClient
) -> None:
    response = upload_model(client)

    assert response.status_code == 200, "Failed to upload model"

    model_id = 1
    version_number = 2
    response = client.delete(f"/models/{model_id}/versions/{version_number}")

    assert response.status_code == 404, "It should have failed to delete model version"

    model_id = 2
    version_number = 1
    response = client.delete(f"/models/{model_id}/versions/{version_number}")

    assert response.status_code == 404, "It should have failed to delete model version"


def test_download_model_version_happy_path(client: TestClient) -> None:
    response = upload_model(client)

    assert response.status_code == 200, "Failed to upload model"

    model_id = 1
    version_number = 1
    response = client.get(f"/models/{model_id}/versions/{version_number}/download")

    assert response.status_code == 200, "Failed to download model version"
    assert (
        response.headers["Content-Disposition"]
        == 'attachment; filename="file_test.png"'
    )
    assert response.headers["Content-Type"] == "image/png"
    assert response.headers['Model-Name'] == "test2"


    with open("app/tests/file_test.png", "rb") as f:
        expected_file = f.read()

    assert response.content == expected_file
