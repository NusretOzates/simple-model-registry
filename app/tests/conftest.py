import os
import shutil

os.environ["MODEL_STORAGE_PATH"] = "test_models"
os.environ["MODEL_STORAGE_METHOD"] = "local"
os.environ["DATABASE_URL"] = "sqlite:///test.db"

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from ..main import app, get_session


@pytest.fixture(name="session")
def session_fixture() -> Session:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session) -> TestClient:
    def get_session_override() -> Session:
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

    # Remove the test folder recursively
    if os.path.exists("test_models"):
        shutil.rmtree("test_models")
