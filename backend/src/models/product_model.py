from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from pymongo import ReturnDocument
from pymongo.results import InsertOneResult, DeleteResult
from datetime import datetime

from src.services.db_service import db
from src.utils.models_helpers import to_json_serializable


# Funciones para obtener y actualizar los valores permitidos para categorías y alérgenos de productos
def get_allowed_values(name: str) -> list[str]:
    settings_request = db.settings.find_one({"name": name}, {"name": 0, "_id": 0})
    return settings_request.get("value") if settings_request else []


# Campos únicos: "name". Está configurado en MongoDB Atlas.
# Índices: "categories". Está configurado en MongoDB Atlas.
class ProductModel(BaseModel, extra="forbid"):
    name: str = Field(..., min_length=1, max_length=50)
    categories: List[str] = Field(..., min_length=1)
    stock: int = Field(..., ge=0)
    brand: Optional[str] = Field(None, min_length=1, max_length=50)
    allergens: Optional[List[str]] = Field(None, min_length=1)
    notes: Optional[str] = Field(None, min_length=1, max_length=500)
    created_at: datetime = Field(..., default_factory=datetime.now)

    @field_validator("categories", "allergens", mode="after")
    @classmethod
    def __validate_categories_and_allergens(cls, v, field: ValidationInfo):
        field = field.field_name
        if field == "allergens":
            if v is None:
                return v
        checked_values = cls.checking_in_list(field, v, get_allowed_values(field))
        return checked_values

    @staticmethod
    def checking_in_list(
        name_field: str, value: list[str], allowed_values: list[str]
    ) -> list[str]:
        invalid_values = [item for item in value if item not in allowed_values]
        if invalid_values:
            raise ValueError(
                f"Los valores válidos en la lista del campo '{name_field}' son: {', '.join(allowed_values)}."
            )
        return value

    # Solicitudes a la colección "products"
    def insert_product(self) -> InsertOneResult:
        new_product = db.products.insert_one(self.model_dump())
        return new_product

    @staticmethod
    def get_products(skip: int, per_page: int) -> List[dict]:
        products = db.products.find().skip(skip).limit(per_page)
        return to_json_serializable(products)

    @staticmethod
    def get_product(product_id: str) -> dict:
        product = db.products.find_one({"_id": ObjectId(product_id)}, {"_id": 0})
        return to_json_serializable(product)

    def update_product(self, product_id: str, session=None) -> dict:
        updated_product = db.products.find_one_and_update(
            {"_id": ObjectId(product_id)},
            {"$set": self.model_dump()},
            return_document=ReturnDocument.AFTER,
            session=session,
        )
        return to_json_serializable(updated_product)

    @staticmethod
    def update_product_stock_by_name(items_order: list, session=None) -> list[dict]:
        updated_products = []
        for dish in items_order:
            for ingredient in dish.get("ingredients"):
                waste = ingredient.get("waste") * dish.get("qty")
                updated_product = db.products.find_one_and_update(
                    {"name": ingredient.get("name")},
                    {"$inc": {"stock": -waste}},
                    return_document=ReturnDocument.AFTER,
                    session=session,
                )
                updated_products.append(updated_product)
        return to_json_serializable(updated_products)

    @staticmethod
    def delete_product(product_id: str) -> DeleteResult:
        deleted_product = db.products.delete_one({"_id": ObjectId(product_id)})
        return deleted_product
