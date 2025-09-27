from typing import List, NotRequired, Literal, Dict, Union
from typing_extensions import TypedDict
from datetime import datetime
from pymongo.cursor import Cursor
from bson import ObjectId


class Ingredient(TypedDict):
    name: str
    allergens: NotRequired[List[str]]
    waste: float


class ItemOrder(TypedDict):
    name: str
    qty: int
    ingredients: List[Ingredient]
    custom: NotRequired[Union[Dict[str, bool], None]]
    price: float


class ItemBasket(TypedDict):
    name: str
    qty: int
    price: float
    custom: NotRequired[Union[Dict[str, bool], None]]


class Address(TypedDict):
    name: NotRequired[str]
    line_one: str
    line_two: NotRequired[str]
    postal_code: Literal[
        "03001",
        "03002",
        "03003",
        "03004",
        "03005",
        "03006",
        "03007",
        "03008",
        "03009",
        "03010",
        "03011",
        "03012",
        "03013",
        "03014",
        "03015",
        "03016",
    ]


def to_json_serializable(obj):
    if isinstance(obj, Cursor):
        obj = list(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, list):
        return [to_json_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: to_json_serializable(v) for k, v in obj.items()}
    else:
        return obj
