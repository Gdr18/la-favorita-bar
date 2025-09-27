import pytest
from datetime import datetime
from bson import ObjectId

from src.utils.models_helpers import to_json_serializable


def test_to_json_serializable_datetime():
    dt = datetime(2023, 10, 1, 12, 0, 0)
    assert to_json_serializable(dt) == "2023-10-01T12:00:00"


def test_to_json_serializable_objectid():
    obj_id = ObjectId("507f1f77bcf86cd799439011")
    assert to_json_serializable(obj_id) == "507f1f77bcf86cd799439011"
