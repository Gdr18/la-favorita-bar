import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Literal

from bson import ObjectId
from email_validator import validate_email, EmailNotValidError
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
    ValidationInfo,
    model_validator,
)
from pymongo import ReturnDocument
from pymongo.results import InsertOneResult, DeleteResult

from src.services.db_service import db
from src.services.security_service import bcrypt
from src.utils.models_helpers import Address, ItemBasket, to_json_serializable


# Campos únicos: "email". Está configurado en MongoDB Atlas.
# Campos TTL: "expires_at". Está configurado en MongoDB Atlas. El documento se eliminará automáticamente cuando
# expire la fecha. Si el usuario no ha confirmado su email, se eliminará automáticamente a los 7 días.
class UserModel(BaseModel, extra="forbid"):
    name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr = Field(..., min_length=5, max_length=100)
    password: Optional[str] = Field(default=None, min_length=8, max_length=60)
    auth_provider: Literal["email", "google"] = Field(default="email")
    role: int = Field(default=3, ge=0, le=3)
    phone: Optional[str] = Field(None, pattern=r"^(?:\+34)?\d{9}$")
    addresses: Optional[List[Address]] = None
    basket: Optional[List[ItemBasket]] = None
    confirmed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=7)
    )

    @model_validator(mode="after")
    def validate_model(self) -> "UserModel":
        if self.auth_provider == "google":
            self.confirmed = True
        elif self.auth_provider == "email":
            self.password = self.validate_password(self.password)
        if self.confirmed:
            self.expires_at = None
        return self

    @field_validator("email", mode="after")
    @classmethod
    def validate_email(cls, v) -> EmailStr:
        try:
            validate_email(v)
            return v
        except EmailNotValidError as e:
            raise ValueError(f"El campo 'email' no es válido: {str(e)}")

    @staticmethod
    def validate_password(password: str) -> str:
        if password is None:
            raise ValueError("El campo 'password' es obligatorio.")
        bcrypt_pattern = re.compile(r"^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$")
        password_pattern = re.compile(
            r"^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[?!@#$%^&*_-]).{8,}$"
        )
        if bcrypt_pattern.match(password):
            return password
        if re.match(password_pattern, password):
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            return hashed_password
        else:
            raise ValueError(
                "El campo 'password' debe tener al menos 8 caracteres, contener al menos una mayúscula, "
                "una minúscula, un número y un carácter especial (!@#$%^&*_-)"
            )

    @field_validator("addresses", "basket", mode="before")
    @classmethod
    def validate_addresses_and_basket(cls, v, field: ValidationInfo):
        if v is None:
            return v
        if isinstance(v, list) and all(isinstance(i, dict) for i in v):
            if field.field_name == "basket":
                for item in v:
                    if item.get("custom"):
                        if False in item["custom"].values():
                            item["custom"] = {
                                key: value
                                for key, value in item["custom"].items()
                                if value is False
                            }
                        else:
                            item["custom"] = None
                return v
            return v
        else:
            raise ValueError(
                f"El campo '{field.field_name}' debe ser una lista de diccionarios o None."
            )

    # Solicitudes a la colección "users"
    def insert_user(self, session=None) -> InsertOneResult:
        user = db.users.insert_one(self.model_dump(), session=session)
        return user

    def insert_or_update_user_by_email(self) -> dict:
        user = db.users.find_one_and_update(
            {"email": self.email},
            {"$set": self.model_dump()},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return to_json_serializable(user)

    @staticmethod
    def get_users(skip: int, per_page: int) -> list[dict]:
        users = db.users.find().skip(skip).limit(per_page)
        return to_json_serializable(users)

    @staticmethod
    def get_user_by_user_id_without_id(user_id: str) -> dict:
        user = db.users.find_one({"_id": ObjectId(user_id)}, {"_id": 0})
        return to_json_serializable(user)

    @staticmethod
    def get_user_by_user_id(user_id: str) -> dict:
        user = db.users.find_one({"_id": ObjectId(user_id)})
        return to_json_serializable(user)

    @staticmethod
    def get_user_by_email(email: str) -> dict:
        user = db.users.find_one({"email": email})
        return to_json_serializable(user)

    def update_user(self, user_id: str, session=None) -> dict:
        updated_user = db.users.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": self.model_dump()},
            return_document=ReturnDocument.AFTER,
            session=session,
        )
        return to_json_serializable(updated_user)

    @staticmethod
    def delete_user(user_id: str) -> DeleteResult:
        deleted_user = db.users.delete_one({"_id": ObjectId(user_id)})
        return deleted_user
