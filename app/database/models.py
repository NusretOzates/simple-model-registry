from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlmodel import JSON, Column, Field, Relationship, SQLModel


class BaseVersion(SQLModel):
    description: str = Field(...,min_length=1)
    created_by: str = Field(...,min_length=1)
    tags: dict = Field(default_factory=dict, sa_column=Column(JSON))
    metrics: dict = Field(default_factory=dict, sa_column=Column(JSON))
    parameters: dict = Field(default_factory=dict, sa_column=Column(JSON))


class BaseMLModel(SQLModel):
    name: str = Field(index=True, unique=True, min_length=1)
    description: str = Field(...,min_length=1)
    created_by: str = Field(...,min_length=1)
    tags: dict = Field(default_factory=dict, sa_column=Column(JSON))


class Alias(SQLModel, table=True):
    alias_id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, min_length=1)
    version_id: int = Field(
        foreign_key="version.version_id", index=True, ondelete="CASCADE"
    )
    version: "Version" = Relationship(back_populates="alias")


class Version(BaseVersion, table=True):
    version_id: int | None = Field(default=None, primary_key=True)
    model_id: int = Field(foreign_key="model.model_id", index=True, ondelete="CASCADE")
    version_number: int
    file_name: str
    alias: Alias | None = Relationship(back_populates="version", cascade_delete=True)
    model: "Model" = Relationship(back_populates="versions")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VersionWithAlias(BaseVersion):
    version_id: int | None
    version_number: int
    alias: Alias | None
    file_name: str

class CreateVersion(BaseVersion):
    alias: str|None = None

class Model(BaseMLModel, table=True):
    model_id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    latest_version_id: int = 1
    versions: list[Version] = Relationship(back_populates="model", cascade_delete=True)


class ModelWithVersions(BaseMLModel):
    model_id: int | None
    created_at: datetime
    updated_at: datetime
    latest_version_id: int
    versions: list[VersionWithAlias]


class CreateModel(BaseMLModel):
    version_metrics: Optional[Dict[str, float]] = {}
    version_parameters: Optional[Dict[str, Any]] = {}
    version_tags: Optional[Dict[str, Any]] = {}
    version_description: str  = Field(...,min_length=1)
    version_alias: str | None = None

class UpdateModel(SQLModel):
    name: str | None =  Field(None,min_length=1)
    description: str | None =  Field(None,min_length=1)
    created_by: str | None =  Field(None,min_length=1)
    tags: dict | None = None
