import os
from abc import ABC, abstractmethod
from typing import BinaryIO


class ModelStorageMethod(ABC):
    """
    Abstract class for model storage methods
    
    Attributes:
        base_path (str): Base path to save the model file
        
    Every storage method must allow saving, deleting, downloading, checking the file, and listing files.
    """
    def __init__(self, base_path: str) -> None:
        self.base_path = base_path

    @abstractmethod
    def save(
        self, file_name: str, model_name: str, model_version: int, model_file: BinaryIO
    ) -> bool:
        pass

    @abstractmethod
    def delete(self, file_name: str, model_name: str, model_version: int) -> bool:
        pass

    @abstractmethod
    def download(self, file_name: str, model_name: str, model_version: int) -> str:
        pass

    @abstractmethod
    def check_file(self, file_name: str, model_name: str, model_version: int) -> bool:
        pass

    @abstractmethod
    def list_files(self, model_name: str, model_version: int) -> list[str]:
        pass


class LocalModelSave(ModelStorageMethod):
    """
    Local model storage method
    
    Attributes:
        base_path (str): Base path to save the model file
        
    It uses the local file system to save the model file into the base path.
    Model and version are used to create a directory structure to save the model file.
    """
    def save(
        self, file_name: str, model_name: str, model_version: int, model_file: BinaryIO
    ) -> bool:
        if not os.path.exists(f"{self.base_path}/{model_name}/{model_version}"):
            os.makedirs(f"{self.base_path}/{model_name}/{model_version}")

        with open(
            f"{self.base_path}/{model_name}/{model_version}/{file_name}", "wb"
        ) as f:
            model_file.seek(0)
            f.write(model_file.read())

        return True

    def delete(self, file_name: str, model_name: str, model_version: int) -> bool:
        if self.check_file(file_name, model_name, model_version):
            os.remove(f"{self.base_path}/{model_name}/{model_version}/{file_name}")
            return True

        return False

    def download(self, file_name: str, model_name: str, model_version: int) -> str:
        if self.check_file(file_name, model_name, model_version):
            return f"{self.base_path}/{model_name}/{model_version}/{file_name}"

        return ""

    def check_file(self, file_name: str, model_name: str, model_version: int) -> bool:
        return os.path.exists(
            f"{self.base_path}/{model_name}/{model_version}/{file_name}"
        )

    def list_files(self, model_name: str, model_version: int) -> list[str]:
        if os.path.exists(f"{self.base_path}/{model_name}/{model_version}"):
            return os.listdir(f"{self.base_path}/{model_name}/{model_version}")

        return []
