import pytest
from datetime import datetime

from src.models.dish_model import DishModel
from tests.test_helpers import (
    assert_insert_document_template,
    assert_get_all_documents_template,
    assert_get_document_template,
    assert_update_document_template,
    assert_delete_document_template,
)

ID = "507f1f77bcf86cd799439011"
VALID_DATA = {
    "name": "Tarta de queso",
    "category": "dessert",
    "description": "Tarta de queso casera",
    "ingredients": [{"name": "Huevo", "allergens": ["huevo"], "waste": 0.1}],
    "custom": {"mermelada": False},
    "price": 5.5,
}


@pytest.fixture
def mock_db(mocker):
    mock_db = mocker.MagicMock()
    mocker.patch("src.services.db_service.db.dishes", new=mock_db)
    return mock_db


def test_dish_valid_data(mock_db):
    dish = DishModel(**VALID_DATA)
    assert isinstance(dish.name, str) and 0 < len(dish.name) < 101
    assert dish.category in ["starter", "main", "dessert"]
    assert isinstance(dish.description, str) and 0 < len(dish.description) < 201
    assert isinstance(dish.ingredients, list) and all(
        isinstance(item, dict) for item in dish.ingredients
    )
    assert dish.custom is None or isinstance(dish.custom, dict)
    assert isinstance(dish.price, float) and dish.price > 0
    assert isinstance(dish.available, bool)
    assert isinstance(dish.created_at, datetime)


@pytest.mark.parametrize(
    "name, category, description, ingredients, custom, price",
    [
        (
            None,
            VALID_DATA["category"],
            VALID_DATA["description"],
            VALID_DATA["ingredients"],
            VALID_DATA["custom"],
            VALID_DATA["price"],
        ),
        (
            "",
            VALID_DATA["category"],
            VALID_DATA["description"],
            VALID_DATA["ingredients"],
            VALID_DATA["custom"],
            VALID_DATA["price"],
        ),
        (
            1234,
            VALID_DATA["category"],
            VALID_DATA["description"],
            VALID_DATA["ingredients"],
            VALID_DATA["custom"],
            VALID_DATA["price"],
        ),
        (
            VALID_DATA["name"],
            None,
            VALID_DATA["description"],
            VALID_DATA["ingredients"],
            VALID_DATA["custom"],
            VALID_DATA["price"],
        ),
        (
            VALID_DATA["name"],
            "hola",
            VALID_DATA["description"],
            VALID_DATA["ingredients"],
            VALID_DATA["custom"],
            VALID_DATA["price"],
        ),
        (
            VALID_DATA["name"],
            1234,
            VALID_DATA["description"],
            VALID_DATA["ingredients"],
            VALID_DATA["custom"],
            VALID_DATA["price"],
        ),
        (
            VALID_DATA["name"],
            VALID_DATA["category"],
            None,
            VALID_DATA["ingredients"],
            VALID_DATA["custom"],
            VALID_DATA["price"],
        ),
        (
            VALID_DATA["name"],
            VALID_DATA["category"],
            "",
            VALID_DATA["ingredients"],
            VALID_DATA["custom"],
            VALID_DATA["price"],
        ),
        (
            VALID_DATA["name"],
            VALID_DATA["category"],
            1234,
            VALID_DATA["ingredients"],
            VALID_DATA["custom"],
            VALID_DATA["price"],
        ),
        (
            VALID_DATA["name"],
            VALID_DATA["category"],
            VALID_DATA["description"],
            None,
            VALID_DATA["custom"],
            VALID_DATA["price"],
        ),
        (
            VALID_DATA["name"],
            VALID_DATA["category"],
            VALID_DATA["description"],
            [],
            VALID_DATA["custom"],
            VALID_DATA["price"],
        ),
        (
            VALID_DATA["name"],
            VALID_DATA["category"],
            VALID_DATA["description"],
            1234,
            VALID_DATA["custom"],
            VALID_DATA["price"],
        ),
        (
            VALID_DATA["name"],
            VALID_DATA["category"],
            VALID_DATA["description"],
            [{"name": "producto inventado", "waste": 0.1}],
            VALID_DATA["custom"],
            VALID_DATA["price"],
        ),
        (
            VALID_DATA["name"],
            VALID_DATA["category"],
            VALID_DATA["description"],
            VALID_DATA["ingredients"],
            1234,
            VALID_DATA["price"],
        ),
        (
            VALID_DATA["name"],
            VALID_DATA["category"],
            VALID_DATA["description"],
            VALID_DATA["ingredients"],
            VALID_DATA["custom"],
            None,
        ),
        (
            VALID_DATA["name"],
            VALID_DATA["category"],
            VALID_DATA["description"],
            VALID_DATA["ingredients"],
            VALID_DATA["custom"],
            0,
        ),
        (
            VALID_DATA["name"],
            VALID_DATA["category"],
            VALID_DATA["description"],
            VALID_DATA["ingredients"],
            VALID_DATA["custom"],
            "hola",
        ),
    ],
)
def test_dish_validation_errors(
    name, category, description, ingredients, custom, price
):
    with pytest.raises(ValueError):
        DishModel(
            name=name,
            category=category,
            description=description,
            ingredients=ingredients,
            custom=custom,
            price=price,
        )


def test_insert_dish(mock_db):
    return assert_insert_document_template(mock_db, DishModel(**VALID_DATA).insert_dish)


def test_get_dishes(mock_db):
    return assert_get_all_documents_template(
        mock_db, DishModel.get_dishes, [VALID_DATA]
    )


def test_get_dishes_by_category(mock_db):
    mock_db.find.return_value = [VALID_DATA]
    result = DishModel.get_dishes_by_category(VALID_DATA["category"])
    assert result[0]["category"] == VALID_DATA["category"]
    assert result == [VALID_DATA]
    mock_db.find.assert_called_once()


def test_get_dish(mock_db):
    return assert_get_document_template(mock_db, DishModel.get_dish, VALID_DATA)


def test_update_dish(mock_db):
    new_data = {**VALID_DATA, "name": "new_value"}
    dish_object = DishModel(**new_data)
    return assert_update_document_template(mock_db, dish_object.update_dish, new_data)


def test_update_dishes_availability(mock_db):
    mock_db.update_many.return_value.modified_count = 1
    result = DishModel.update_dishes_availability("Producto 1", False)
    assert result.modified_count >= 1
    mock_db.update_many.assert_called_once()


def test_delete_dish(mock_db):
    return assert_delete_document_template(mock_db, DishModel.delete_dish)
