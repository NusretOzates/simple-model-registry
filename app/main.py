from contextlib import asynccontextmanager
from typing import List, Optional

import psutil
from fastapi import Depends, FastAPI, Form, UploadFile
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse, ORJSONResponse
from pydantic import ValidationError

from .config import app_settings
from .database.connection import Session, create_db_and_tables, engine, get_session
from .database.model_save import LocalModelSave
from .database.models import ModelWithVersions
from .services.model_service import (
    CreateModel,
    CreateVersion,
    ModelService,
    UpdateModel,
    Version,
)
from .utils import pydantic_model_fields_to_str


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    print("Starting app")
    create_db_and_tables()
    yield
    engine.dispose()




if app_settings.model_storage_method == "local":
    model_save = LocalModelSave(app_settings.model_storage_path)
else:
    raise ValueError("Invalid model save method")

app = FastAPI(lifespan=lifespan, default_response_class=ORJSONResponse)
model_service = ModelService(model_save)


@app.get("/")
def hi_everyone() -> dict[str, str]:
    """
    Root endpoint. Returns a simple message and says hello to the world.<br>
    """
    return {"message": "Hello World"}


@app.get("/models", response_model=List[ModelWithVersions], tags=["models"])
def get_models(session: Session = Depends(get_session)) -> List[ModelWithVersions]:
    """
    Get all models from the database.

    Returns: <br>
        List of models with their version details. If no models are present, an empty list is returned.
    """
    return model_service.get_all_models(session)


@app.post("/models", tags=["models"])
def upload_model(
    model_file: UploadFile,
    metadata: str = Form(
        description=f"Model metadata as JSON string. Expected format: {pydantic_model_fields_to_str(CreateModel.model_fields)}"
    ),
    session: Session = Depends(get_session),
) -> dict:
    """ Upload a model to the registry.
        
    A model file and metadata are required to upload a model.
    
    Args: <br>
        model_file: A file object containing the model file. It should be .skops file but no-one is checking that except you.<br>
        metadata: A JSON string containing the model metadata. Expected values are in the body description.
    
    Returns: <br>
        A dictionary containing the model ID and the model name.
    
    Raises:<br>
        HTTPException: If the model metadata is invalid or if there is an error saving the model.
    """
    try:
        model_metadata = CreateModel.model_validate_json(metadata)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors()) from e

    result = model_service.register_model(
        model_file.file, model_file.filename, model_metadata, session
    )

    if "error" in result:
        raise HTTPException(status_code=result["code"], detail=result["error"])

    return result


@app.get(
    "/models/{model_id}/", response_model=Optional[ModelWithVersions], tags=["models"]
)
def get_model(model_id: int, session: Session = Depends(get_session)) -> ModelWithVersions:
    """
    Get a model by its ID.
    Args: <br>
        model_id: The ID of the model to retrieve.

    Returns: <br>
        The model with the given ID.
    
    Raises: <br>
        HTTPException: If the model is not found.

    """
    model = model_service.get_model(model_id, session)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return model


@app.put("/models/{model_id}", tags=["models"])
def update_model(
    model_id: int, model_update: UpdateModel, session: Session = Depends(get_session)
) -> dict:
    """
    Update a model by its ID.
    
    Args: <br>
        model_id: The ID of the model to update. <br>
        model_update: The model update details. Expected values are in the body description.

    Returns: <br>
        The updated model details.
    
    Raises: <br>
        HTTPException: If the model is not found or if the model update details are invalid.

    """
    result = model_service.update_model(model_id, model_update, session)
    if "error" in result:
        raise HTTPException(status_code=result["code"], detail=result["error"])

    return result


@app.delete("/models/{model_id}", tags=["models"])
def delete_model(model_id: int, session: Session = Depends(get_session)) -> dict:
    """
    Delete a model by its ID.
    
    Args: <br>
        model_id: The ID of the model to delete.

    Returns: <br>
        A dictionary containing the model ID and the model name.
        
    Raises: <br>
        HTTPException: If the model is not found or if there is an error deleting the model.
    """
    result = model_service.delete_model(model_id, session)
    if "error" in result:
        raise HTTPException(status_code=result["code"], detail=result["error"])

    return result


@app.post("/models/{model_id}/version", tags=["versions"])
def upload_model_version(
    model_id: int,
    model_file: UploadFile,
    metadata: str = Form(
        description=f"Version metadata as JSON string. Expected format: {pydantic_model_fields_to_str(CreateVersion.model_fields)}"
    ),
    session: Session = Depends(get_session),
) -> dict:
    """
    Upload a model version to the registry.
    
    Args: <br>
        model_id: The ID of the model to which the version belongs. <br>
        model_file: A file object containing the model version file. It should be .skops file but no-one is checking that except you. <br>
        metadata: A JSON string containing the version metadata. Expected values are in the body description.

    Returns: <br>
        A dictionary containing the model ID, the model name, and the version number.
    
    Raises: <br>
        HTTPException: If the version metadata is invalid or if there is an error saving the model version.
    """
    try:
        version_metadata = CreateVersion.model_validate_json(metadata)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors()) from e

    result = model_service.register_model_version(
        model_file.file, model_file.filename, model_id, version_metadata, session
    )

    if "error" in result:
        raise HTTPException(status_code=result["code"], detail=result["error"])

    return result


@app.get(
    "/models/{model_id}/versions/{version_number}",
    response_model=Version,
    response_model_exclude={"version_id"},
    tags=["versions"],
)
def get_model_version(
    model_id: int, version_number: int, session: Session = Depends(get_session)
) -> Version:
    """
    Get a model version by its version
    
    Args: <br>
        model_id: ID of the model to which the version belongs. <br>
        version_number: The version number of the model version to retrieve.

    Returns: <br>
        The model version with the given version number.
    
    Raises: <br>
        HTTPException: If the model version is not found.
    """
    result = model_service.get_version_details(model_id, version_number, session)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=result["code"], detail=result["error"])

    return result


@app.delete("/models/{model_id}/versions/{version_number}", tags=["versions"])
def delete_model_version(
    model_id: int, version_number: int, session: Session = Depends(get_session)
) -> dict:
    """
    Delete a model version by its version number.
    
    Args: <br>
        model_id: ID of the model to which the version belongs. <br>
        version_number: The version number of the model version to delete.

    Returns: <br>
        A dictionary containing the model ID, the model name, and the version number.
    
    Raises: <br>
        HTTPException: If the model version is not found or if there is an error deleting the model version.

    """
    result = model_service.delete_version(model_id, version_number, session)
    if "error" in result:
        raise HTTPException(status_code=result["code"], detail=result["error"])

    return result


@app.get("/models/{model_id}/versions/{version_number}/download", tags=["versions"])
def download_model(
    model_id: int, version_number: int, session: Session = Depends(get_session)
) -> FileResponse:
    """
    Download a model version by its version number.
    
    Args: <br>
        model_id: ID of the model to which the version belongs. <br>
        version_number: The version number of the model version to download.

    Returns:
        A file response containing the model version file.
        
    Raises: <br>
        HTTPException: If the model version is not found or if there is an error downloading the model version.
    """
    result = model_service.download_model(model_id, version_number, session)
    if "error" in result:
        raise HTTPException(status_code=result["code"], detail=result["error"])

    return FileResponse(result["file_path"], filename=result["file_name"], headers={
        "Model-Name": result["model_name"],
    })

@app.get("/health")
def health(session: Session = Depends(get_session)) -> dict[str, float|int]:
    """
    Health check endpoint. Returns cpu and memory usage of the server by percentage. <br>
    Also returns the number of models present in the database.
    
    Returns: <br>
        Dictionary containing cpu and memory usage of the server.
    
    Raises: <br>
        HTTPException: If there is an error getting the server health.
    """
    try:
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
        number_of_models = len(model_service.get_all_models(session))

        return {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "number_of_models": number_of_models,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
