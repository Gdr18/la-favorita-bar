from typing import List, Union, Annotated
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, Field, field_validator
from pymongo.results import InsertOneResult, DeleteResult

from src.services.db_service import db
from src.utils.models_helpers import to_json_serializable

NonEmptyListStr = Annotated[List[str], Field(min_length=1)]


# Campos únicos: "name". Está configurado en MongoDB Atlas.
class SettingModel(BaseModel, extra="forbid"):
    name: str = Field(..., min_length=1, max_length=50)
    value: Union[NonEmptyListStr, bool] = Field(...)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator("value", mode="after")
    @classmethod
    def __validate_values(cls, v):
        if isinstance(v, list) and not all(len(item) > 0 for item in v):
            raise ValueError(
                "Los elementos de la lista 'values' debe tener al menos un caracter en cada string."
            )
        return v

    # Solicitudes a la colección "settings"
    def insert_setting(self) -> InsertOneResult:
        new_setting = db.settings.insert_one(self.model_dump())
        return new_setting

    @staticmethod
    def get_settings(skip: int, per_page: int) -> List[dict]:
        settings = db.settings.find().skip(skip).limit(per_page)
        return to_json_serializable(settings)

    @staticmethod
    def get_setting(setting_id: str) -> dict:
        setting = db.settings.find_one({"_id": ObjectId(setting_id)}, {"_id": 0})
        return to_json_serializable(setting)

    @staticmethod
    def get_setting_by_name(name: str) -> dict:
        setting = db.settings.find_one({"name": name}, {"_id": 0})
        return to_json_serializable(setting)

    def update_setting(self, setting_id: str) -> dict:
        updated_setting = db.settings.find_one_and_update(
            {"_id": ObjectId(setting_id)},
            {"$set": self.model_dump()},
            return_document=True,
        )
        return to_json_serializable(updated_setting)

    @staticmethod
    def delete_setting(setting_id: str) -> DeleteResult:
        deleted_setting = db.settings.delete_one({"_id": ObjectId(setting_id)})
        return deleted_setting
