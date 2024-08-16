from typing import Any, BinaryIO, List, Optional

from sqlmodel import Session, select

from ..database.model_save import ModelStorageMethod
from ..database.models import (
    Alias,
    CreateModel,
    CreateVersion,
    Model,
    UpdateModel,
    Version,
    datetime,
    timezone,
)


class ModelService:
    def __init__(self, storage_method: ModelStorageMethod) -> None:
        self.storage = storage_method

    def __normalize_name(self, name: str) -> str:
        return name.lower().replace(" ", "_")

    def get_all_models(self, session: Session) -> List[Model]:
        statement = select(Model)
        return session.exec(statement).all()


    def get_model(self, model_id: int, session: Session) -> Optional[Model]:
        return session.get(Model, model_id)


    def get_version_details(
        self, model_id: int, version_number: int, session: Session
    ) -> Version | dict[str, Any]:
        statement = select(Version).where(
            Version.model_id == model_id, Version.version_number == version_number
        )
        version = session.exec(statement).first()

        if not version:
            return {
                "error": f"Model ID: {model_id}  Version: {version_number} not found",
                "code": 404,
            }

        return version

    def delete_version(
        self, model_id: int, version_number: int, session: Session
    ) -> dict[str, Any]:
        statement = select(Version).where(
            Version.model_id == model_id, Version.version_number == version_number
        )
        version = session.exec(statement).first()

        if not version:
            return {
                "error": f"Model ID: {model_id}  Version: {version_number} not found",
                "code": 404,
            }

        model_name = self.__normalize_name(version.model.name)

        session.delete(version)
        session.commit()

        # Delete the model folder
        self.storage.delete(version.file_name, model_name, version_number)

        return {
            "message": f"Model ID: {model_id}  Version: {version_number} deleted successfully"
        }

    def register_model(
        self, model_file: BinaryIO, file_name: str, model: CreateModel, session: Session
    ) -> dict[str, Any]:
        # Check if the model already exists
        statement = select(Model).where(Model.name == model.name)
        existing_model = session.exec(statement).first()

        if existing_model:
            return {
                "error": f"Model {model.name} already exists. Please upload a new version using /models/{existing_model.model_id}/version.",
                "code": 400,
            }

        file_name = self.__normalize_name(file_name)

        db_model = Model(
            name=model.name,
            description=model.description,
            created_by=model.created_by,
            tags=model.tags,
        )

        session.add(db_model)
        session.commit()
        session.refresh(db_model)

        version = Version(
            version_number=1,
            description=model.version_description,
            created_by=model.created_by,
            tags=model.version_tags,
            metrics=model.version_metrics,
            parameters=model.version_parameters,
            model_id=db_model.model_id,
            file_name=file_name,
        )

        session.add(version)
        session.commit()
        session.refresh(version)

        if model.version_alias:
            # Check if the alias already exists
            statement = select(Alias).where(Alias.name == model.version_alias)
            existing_alias = session.exec(statement).first()

            if existing_alias:
                return {
                    "error": f"Alias {model.version_alias} already exists. Please use a different alias.",
                    "code": 400,
                }

            alias = Alias(name=model.version_alias, version_id=version.version_id)
            session.add(alias)
            session.commit()
            session.refresh(alias)

        # Move the model to the models folder from the temp location
        file_name = self.__normalize_name(file_name)

        self.storage.save(
            file_name, self.__normalize_name(model.name), 1, model_file
        )

        return {"message": f"Model {model.name} uploaded successfully", "model_id": db_model.model_id}

    def register_model_version(
        self,
        model_file: BinaryIO,
        file_name: str,
        model_id: int,
        create_version: CreateVersion,
        session: Session,
    ) -> dict[str, Any]:
        # Check if the model exists in temp location and in the database
        model = session.get(Model, model_id)

        if not model:
            return {"error": f"Model {model_id} not found", "code": 404}

        file_name = self.__normalize_name(file_name)

        db_version = Version(
            version_number=model.latest_version_id + 1,
            description=create_version.description,
            created_by=create_version.created_by,
            tags=create_version.tags,
            metrics=create_version.metrics,
            parameters=create_version.parameters,
            model_id=model_id,
            file_name=file_name,
        )

        session.add(db_version)
        session.commit()
        session.refresh(db_version)

        if create_version.alias:
            # Check if the alias already exists
            statement = select(Alias).where(Alias.name == create_version.alias)
            existing_alias = session.exec(statement).first()

            if existing_alias:
                return {
                    "error": f"Alias {create_version.alias} already exists. Please use a different alias.",
                    "code": 400,
                }

            alias = Alias(name=create_version.alias, version_id=db_version.version_id)
            session.add(alias)
            session.commit()
            session.refresh(alias)

        model.latest_version_id += 1
        model.updated_at = db_version.created_at
        session.add(model)
        session.commit()
        session.refresh(model)

        # Move the model to the models folder from the temp location
        self.storage.save(
            file_name,
            self.__normalize_name(model.name),
            model.latest_version_id,
            model_file,
        )

        return {
            "message": f"Model {model_id} version {model.latest_version_id} uploaded successfully",
            "version_number": model.latest_version_id,
            "version_id": db_version.version_id,
        }

    def update_model(
        self, model_id: int, update_model: UpdateModel, session: Session
    ) -> dict[str, Any]:
        model = session.get(Model, model_id)

        if not model:
            return {"error": f"Model {model_id} not found", "code": 404}

        update_dump = update_model.model_dump(exclude_unset=True)
        model.sqlmodel_update(obj=update_dump)
        model.updated_at = datetime.now(timezone.utc)

        session.add(model)
        session.commit()

        return {"message": f"Model {model_id} updated successfully"}

    def delete_model(self, model_id: int, session: Session) -> dict[str, Any]:
        model = session.get(Model, model_id)

        if not model:
            return {"error": f"Model {model_id} not found", "code": 404}

        latest_version = model.latest_version_id

        for i in range(1, latest_version + 1):
            self.storage.delete(
                model.versions[i - 1].file_name, self.__normalize_name(model.name), i
            )

        session.delete(model)
        session.commit()

        return {"message": f"Model {model_id} deleted successfully"}

    def download_model(
        self, model_id: int, version_number: int, session: Session
    ) -> dict[str, Any]:
        # Check if the model exists in the database and the version exists
        statement = select(Version).where(
            Version.model_id == model_id, Version.version_number == version_number
        )

        version = session.exec(statement).first()

        if not version:
            return {
                "error": f"Model ID: {model_id}  Version: {version_number} not found",
                "code": 404,
            }

        file_path = self.storage.download(
            version.file_name, self.__normalize_name(version.model.name), version_number
        )

        model_name = version.model.name

        return {"file_path": file_path, "file_name": version.file_name, "model_name": model_name}
