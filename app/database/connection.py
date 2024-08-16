from sqlmodel import Session, SQLModel, create_engine

from ..config import app_settings

engine = create_engine(
    app_settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    with Session(engine) as session:
        yield session
