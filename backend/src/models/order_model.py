from pydantic import BaseModel, Field, model_validator
from typing import List, Literal, Optional
from pymongo.results import InsertOneResult, DeleteResult
from pymongo import ReturnDocument
from bson import ObjectId
from datetime import datetime

from src.services.db_service import db
from src.utils.models_helpers import Address, ItemOrder, to_json_serializable


# Índices: "user_id". Está configurado en MongoDB Atlas.
class OrderModel(BaseModel, extra="forbid"):
    user_id: str = Field(..., pattern=r"^[a-f0-9]{24}$")
    items: List[ItemOrder] = Field(..., min_length=1)
    type_order: Literal["delivery", "local", "take_away"] = Field(...)
    address: Optional[Address] = None
    payment: Literal["cash", "card", "paypal"] = Field(...)
    total_price: float = Field(..., ge=0)
    state: Literal[
        "pending", "accepted", "cooking", "canceled", "ready", "sent", "delivered"
    ] = Field(default="pending")
    created_at: datetime = Field(default_factory=datetime.now)

    @model_validator(mode="after")
    def validate_model(self) -> "OrderModel":
        if self.type_order == "delivery" and self.address is None:
            raise ValueError(
                "Cuando el campo 'type_order' tiene el valor 'delivery' el campo 'address' debe tener un valor de tipo diccionario"
            )
        if self.type_order == "local" and self.state == "pending":
            self.state = "accepted"
        for item in self.items:
            if item.get("custom"):
                if False in item["custom"].values():
                    item["custom"] = {
                        key: value
                        for key, value in item["custom"].items()
                        if value is False
                    }
                else:
                    item["custom"] = None
        return self

    @staticmethod
    def check_level_state(new_state: str, old_state: str) -> None:
        allowed_transitions = {
            "pending": ("accepted", "canceled"),
            "accepted": ("cooking", "canceled"),
            "cooking": ("canceled", "ready"),
            "ready": ("sent", "delivered", "canceled"),
            "sent": ("delivered", "canceled"),
        }

        if new_state not in allowed_transitions.get(old_state):
            raise ValueError(
                f"""El campo 'state' sólo puede tener los siguientes valores: {', '.join([f"'{word}'" for word in allowed_transitions.get(old_state)])}."""
            )

    # Solicitudes a la colección "order"
    def insert_order(self) -> InsertOneResult:
        new_order = db.orders.insert_one(self.model_dump())
        return new_order

    @staticmethod
    def get_orders(skip: int, per_page: int) -> List[dict]:
        orders = db.orders.find().skip(skip).limit(per_page)
        return to_json_serializable(orders)

    @staticmethod
    def get_orders_by_user_id(user_id: str, skip: int, per_page: int) -> List[dict]:
        user_orders = db.orders.find({"user_id": user_id}).skip(skip).limit(per_page)
        return to_json_serializable(user_orders)

    @staticmethod
    def get_order(order_id: str) -> dict:
        order = db.orders.find_one({"_id": ObjectId(order_id)}, {"_id": 0})
        return to_json_serializable(order)

    def update_order(self, order_id: str, session=None) -> dict:
        updated_order = db.orders.find_one_and_update(
            {"_id": ObjectId(order_id)},
            {"$set": self.model_dump()},
            return_document=ReturnDocument.AFTER,
            session=session,
        )
        return to_json_serializable(updated_order)

    @staticmethod
    def delete_order(order_id: str) -> DeleteResult:
        deleted_order = db.orders.delete_one({"_id": ObjectId(order_id)})
        return deleted_order
