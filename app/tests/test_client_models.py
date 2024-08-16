import os

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from ..database.models import Version
from .helpers import upload_model


def test_hello_world(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_get_models_empty(client: TestClient) -> None:
    response = client.get("/models")
    assert response.status_code == 200
    assert response.json() == []


def test_get_models_not_empty(client: TestClient) -> None:
    response = upload_model(client)

    assert response.status_code == 200, "Failed to upload model"

    # Then get the models
    response = client.get("/models")
    assert response.status_code == 200
    assert len(response.json()) == 1

    model = response.json()[0]

    assert model["name"] == "test2"
    assert model["description"] == "test"
    assert model["created_by"] == "test"
    assert model["latest_version_id"] == 1
    assert len(model["versions"]) == 1
    assert model["versions"][0]["version_number"] == 1
    assert model["versions"][0]["description"] == "test"
    assert model["versions"][0]["created_by"] == "test"
    assert model["versions"][0]["file_name"] == "file_test.png"
    assert model["versions"][0]["tags"] == {}
    assert model["versions"][0]["metrics"] == {}
    assert model["versions"][0]["parameters"] == {}


def test_upload_model_happy_path(client: TestClient) -> None:
    response = upload_model(client)

    assert response.status_code == 200, "Failed to upload model"


def test_upload_model_duplicate_upload(client: TestClient) -> None:
    response = upload_model(client)

    assert response.status_code == 200, "Failed to upload model"

    response = upload_model(client)

    assert response.status_code == 400, "Duplicate model upload should have failed"
    assert "detail" in response.json()


def test_upload_model_invalid_metadata(client: TestClient) -> None:
    response = upload_model(client, metadata={"abc": "Abc"})

    assert response.status_code == 422, "Invalid metadata should have failed"
    assert "detail" in response.json()


def test_upload_model_missing_field(client: TestClient) -> None:
    response = upload_model(client, metadata={"name": "test"})

    assert response.status_code == 422, "Missing field should have failed"
    assert "detail" in response.json()

def test_upload_model_empty_field(client: TestClient) -> None:
    metadata = {
        "name": "",
        "description": "test",
        "created_by": "test",
        "version_description": "test",
    }

    response = upload_model(client, metadata=metadata)
    
    assert response.status_code == 422, "Missing field should have failed"
    assert "detail" in response.json()

def test_get_model_happy_path(client: TestClient) -> None:
    metadata = {
        "name": "test",
        "description": "test",
        "created_by": "test",
        "version_description": "test",
    }

    response = upload_model(client, metadata=metadata)

    assert response.status_code == 200, "Failed to upload model"

    response = client.get("/models/1/")
    assert response.status_code == 200
    model = response.json()

    assert model["name"] == "test"
    assert model["description"] == "test"
    assert model["created_by"] == "test"
    assert model["latest_version_id"] == 1
    assert len(model["versions"]) == 1
    assert model["versions"][0]["version_number"] == 1
    assert model["versions"][0]["description"] == "test"
    assert model["versions"][0]["created_by"] == "test"
    assert model["versions"][0]["file_name"] == "file_test.png"
    assert model["versions"][0]["tags"] == {}
    assert model["versions"][0]["metrics"] == {}
    assert model["versions"][0]["parameters"] == {}


def test_get_model_not_found(client: TestClient) -> None:
    response = client.get("/models/1/")
    assert response.status_code == 404


def test_update_model_happy_path(client: TestClient) -> None:
    response = upload_model(client)

    assert response.status_code == 200, "Failed to upload model"

    update_metadata = {
        "name": "test2",
        "description": "test2",
        "created_by": "test2",
    }

    response = client.put(
        "/models/1",
        json=update_metadata,
    )

    assert response.status_code == 200

    response = client.get("/models/1/")
    assert response.status_code == 200
    model = response.json()

    assert model["name"] == "test2"
    assert model["description"] == "test2"
    assert model["created_by"] == "test2"


def test_update_model_not_found(client: TestClient) -> None:
    update_metadata = {
        "name": "test2",
        "description": "test2",
        "created_by": "test2",
    }

    response = client.put(
        "/models/1",
        json=update_metadata,
    )

    assert response.status_code == 404


def test_update_model_invalid_metadata(client: TestClient) -> None:
    update_metadata = {
        "name": "test2",
        "description": "test2",
        "created_by": {"name": "Dev"},
    }

    response = client.put(
        "/models/1",
        json=update_metadata,
    )

    assert response.status_code == 422

def test_update_model_empty_field(client: TestClient) -> None:
    update_metadata = {
        "name": "",
        "description": "test2",
        "created_by": "test2",
    }

    response = client.put(
        "/models/1",
        json=update_metadata,
    )

    assert response.status_code == 422


def test_delete_model_happy_path(client: TestClient, session: Session) -> None:
    response = upload_model(client)

    assert response.status_code == 200, "Failed to upload model"

    response = client.delete("/models/1")
    assert response.status_code == 200

    response = client.get("/models")
    assert response.status_code == 200
    assert response.json() == []

    # Check if the model is deleted from the filesystem
    assert not os.path.exists("test_models/test/1")

    # Also no version should be present in the database
    statement = select(Version).where(Version.model_id == 1)
    version = session.exec(statement).first()
    assert version is None


def test_delete_model_not_found(client: TestClient) -> None:
    response = client.delete("/models/1")
    assert response.status_code == 404
