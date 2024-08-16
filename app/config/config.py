from pydantic import Field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    model_storage_path: str = Field(..., description="Path to save the model file")
    model_storage_method: str = Field(
        description="Method to save the model file. Supported methods: local"
    )
    database_url: str = Field(..., description="URL of the database. Might be a sqlite database or any other SQL database")


app_settings = AppSettings()
