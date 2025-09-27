from pydantic import BaseModel, Field, model_validator
from typing import List, Literal, Union, Dict
from pymongo.results import InsertOneResult, DeleteResult
from pymongo import ReturnDocument
from bson import ObjectId
from datetime import datetime

from src.utils.models_helpers import Ingredient, to_json_serializable
from src.services.db_service import db


# Campos únicos: "name". Está configurado en MongoDB Atlas.
# Índices: "category", "ingredients.name". Está configurado en MongoDB Atlas.
class DishModel(BaseModel, extra="forbid"):
    name: str = Field(..., min_length=1, max_length=100)
    category: Literal["starter", "main", "dessert"] = Field(...)
    description: str = Field(..., min_length=1, max_length=200)
    ingredients: List[Ingredient] = Field(..., min_length=1)
    custom: Union[Dict[str, bool], None] = None
    price: float = Field(..., gt=0)
    available: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)

    @model_validator(mode="after")
    def validate_model(self) -> "DishModel":
        ingredients_names = [ingredient["name"] for ingredient in self.ingredients]
        checked_ingredients = list(
            db.products.find(
                {"name": {"$in": ingredients_names}},
                {"name": 1, "_id": 0, "allergens": 1},
            )
        )

        difference_between = set(ingredients_names).difference(
            set([value["name"] for value in checked_ingredients])
        )
        if difference_between:
            raise ValueError(
                f"""El ingrediente {', '.join([f"'{ingredient}'" for ingredient in list(difference_between)])} no existe."""
            )

        for product in checked_ingredients:
            for ingredient in self.ingredients:
                if ingredient["name"] == product["name"]:
                    product["waste"] = ingredient["waste"]

        self.ingredients = checked_ingredients

        if not self.custom:
            self.custom = {ingredient: True for ingredient in ingredients_names}

        return self

    # Solicitudes a la colección "dish"
    def insert_dish(self) -> InsertOneResult:
        new_dish = db.dishes.insert_one(self.model_dump())
        return new_dish

    @staticmethod
    def get_dishes(skip: int, per_page: int) -> List[dict]:
        dishes = db.dishes.find().skip(skip).limit(per_page)
        return to_json_serializable(dishes)

    @staticmethod
    def get_dishes_by_category(category: str) -> List[dict]:
        dishes_by_category = db.dishes.find({"category": category})
        return to_json_serializable(dishes_by_category)

    @staticmethod
    def get_dish(dish_id: str) -> dict:
        dish = db.dishes.find_one({"_id": ObjectId(dish_id)}, {"_id": 0})
        return to_json_serializable(dish)

    def update_dish(self, dish_id: str) -> dict:
        updated_dish = db.dishes.find_one_and_update(
            {"_id": ObjectId(dish_id)},
            {"$set": self.model_dump()},
            return_document=ReturnDocument.AFTER,
        )
        return to_json_serializable(updated_dish)

    @staticmethod
    def update_dishes_availability(ingredient: str, value: bool, session=None) -> dict:
        updated_dishes = db.dishes.update_many(
            {"ingredients": {"$elemMatch": {"name": ingredient}}},
            {"$set": {"available": value}},
            session=session,
        )
        return to_json_serializable(updated_dishes)

    @staticmethod
    def delete_dish(dish_id: str) -> DeleteResult:
        deleted_dish = db.dishes.delete_one({"_id": ObjectId(dish_id)})
        return deleted_dish
