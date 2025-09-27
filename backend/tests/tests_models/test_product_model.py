import pytest
from pydantic import ValidationError
from flask_jwt_extended import create_access_token

from src.models.product_model import (
    ProductModel,
    get_allowed_values,
)
from tests.test_helpers import (
    assert_insert_document_template,
    assert_get_all_documents_template,
    assert_get_document_template,
    assert_update_document_template,
    assert_delete_document_template,
)

USER_ID = "507f1f77bcf86cd799439011"
VALID_DATA = {
    "name": "Cacahuetes",
    "stock": 345,
    "categories": ["snack", "otro"],
    "allergens": ["cacahuete"],
    "brand": "marca",
    "notes": "notas",
}

ALLERGENS = [
    "cereal",
    "huevo",
    "crustáceo",
    "pescado",
    "cacahuete",
    "soja",
    "lácteo",
    "fruto de cáscara",
    "apio",
    "mostaza",
    "sésamo",
    "sulfito",
    "altramuz",
    "molusco",
]
CATEGORIES = [
    "snack",
    "marisco",
    "dulce",
    "fruta",
    "verdura",
    "carne",
    "pescado",
    "lácteo",
    "pan",
    "pasta",
    "arroz",
    "legumbre",
    "huevo",
    "fruto seco",
    "salsa",
    "condimento",
    "especia",
    "aceite",
    "vinagre",
    "bebida alcohólica",
    "bebida no alcohólica",
    "bebida con gas",
    "bebida sin gas",
    "bebida alcohólica fermentada",
    "bebida energética",
    "bebida isotónica",
    "limpieza",
    "otro",
]


@pytest.fixture
def mock_db_settings(mocker):
    mock_db = mocker.MagicMock()
    mocker.patch("src.services.db_service.db.settings", new=mock_db)
    return mock_db


@pytest.fixture
def mock_db_products(mocker):
    mock_db = mocker.MagicMock()
    mocker.patch("src.services.db_service.db.products", new=mock_db)
    return mock_db


def test_get_allowed_values(mock_db_settings):
    mock_db_settings.find_one.return_value = {"value": ["value1", "value2"]}
    result = get_allowed_values("test_name")
    assert result == ["value1", "value2"]
    mock_db_settings.find_one.assert_called_once_with(
        {"name": "test_name"}, {"name": 0, "_id": 0}
    )


def test_product_validate_allergens_none():
    product = ProductModel(**{**VALID_DATA, "allergens": None})
    assert product.allergens is None


def test_product_valid_data():
    product = ProductModel(**VALID_DATA)
    assert isinstance(product.name, str) and 1 <= len(product.name) <= 50
    assert (
        all(isinstance(item, str) for item in product.categories)
        and isinstance(product.categories, list)
        and len(product.categories) >= 1
    )
    assert (
        all(isinstance(item, str) for item in product.allergens)
        and isinstance(product.allergens, list)
        and len(product.allergens) >= 1
    )
    assert all(
        category in get_allowed_values("categories") for category in product.categories
    )
    assert all(
        allergen in get_allowed_values("allergens") for allergen in product.allergens
    )
    assert isinstance(product.stock, int) and product.stock >= 0
    assert product.brand is None or (
        isinstance(product.brand, str) and 1 <= len(product.brand) <= 50
    )
    assert product.notes is None or (
        isinstance(product.notes, str) and 1 <= len(product.notes) <= 500
    )


@pytest.mark.parametrize(
    "name, stock, categories, allergens, brand, notes",
    [
        (
            123,
            VALID_DATA["stock"],
            VALID_DATA["categories"],
            VALID_DATA["allergens"],
            VALID_DATA["brand"],
            VALID_DATA["notes"],
        ),
        (
            "",
            VALID_DATA["stock"],
            VALID_DATA["categories"],
            VALID_DATA["allergens"],
            VALID_DATA["brand"],
            VALID_DATA["notes"],
        ),
        (
            "a" * 51,
            VALID_DATA["stock"],
            VALID_DATA["categories"],
            VALID_DATA["allergens"],
            VALID_DATA["brand"],
            VALID_DATA["notes"],
        ),
        (
            VALID_DATA["name"],
            -345,
            VALID_DATA["categories"],
            VALID_DATA["allergens"],
            VALID_DATA["brand"],
            VALID_DATA["notes"],
        ),
        (
            VALID_DATA["name"],
            "hola",
            VALID_DATA["categories"],
            VALID_DATA["allergens"],
            VALID_DATA["brand"],
            VALID_DATA["notes"],
        ),
        (
            VALID_DATA["name"],
            VALID_DATA["stock"],
            "bebida",
            None,
            VALID_DATA["brand"],
            VALID_DATA["notes"],
        ),
        (
            VALID_DATA["name"],
            VALID_DATA["stock"],
            [],
            VALID_DATA["allergens"],
            VALID_DATA["brand"],
            VALID_DATA["notes"],
        ),
        (
            VALID_DATA["name"],
            VALID_DATA["stock"],
            [1234],
            VALID_DATA["allergens"],
            VALID_DATA["brand"],
            VALID_DATA["notes"],
        ),
        (
            VALID_DATA["name"],
            VALID_DATA["stock"],
            [""],
            VALID_DATA["allergens"],
            VALID_DATA["brand"],
            VALID_DATA["notes"],
        ),
        (
            VALID_DATA["name"],
            VALID_DATA["stock"],
            VALID_DATA["categories"],
            "cacahuete",
            VALID_DATA["brand"],
            VALID_DATA["notes"],
        ),
        (
            VALID_DATA["name"],
            VALID_DATA["stock"],
            VALID_DATA["categories"],
            [],
            VALID_DATA["brand"],
            VALID_DATA["notes"],
        ),
        (
            VALID_DATA["name"],
            VALID_DATA["stock"],
            VALID_DATA["categories"],
            [1234],
            VALID_DATA["brand"],
            VALID_DATA["notes"],
        ),
        (
            VALID_DATA["name"],
            VALID_DATA["stock"],
            VALID_DATA["categories"],
            VALID_DATA["allergens"],
            "a" * 51,
            VALID_DATA["notes"],
        ),
        (
            VALID_DATA["name"],
            VALID_DATA["stock"],
            VALID_DATA["categories"],
            VALID_DATA["allergens"],
            234,
            VALID_DATA["notes"],
        ),
        (
            VALID_DATA["name"],
            VALID_DATA["stock"],
            VALID_DATA["categories"],
            VALID_DATA["allergens"],
            "",
            VALID_DATA["notes"],
        ),
        (
            VALID_DATA["name"],
            VALID_DATA["stock"],
            VALID_DATA["categories"],
            VALID_DATA["allergens"],
            VALID_DATA["brand"],
            "a" * 501,
        ),
        (
            VALID_DATA["name"],
            VALID_DATA["stock"],
            VALID_DATA["categories"],
            VALID_DATA["allergens"],
            VALID_DATA["brand"],
            "",
        ),
    ],
)
def test_product_validation_errors(name, stock, categories, allergens, brand, notes):
    with pytest.raises(ValidationError):
        ProductModel(
            name=name,
            stock=stock,
            categories=categories,
            allergens=allergens,
            brand=brand,
            notes=notes,
        )


def test_product_checking_in_list_invalid_values():
    with pytest.raises(ValueError):
        ProductModel.checking_in_list("categories", ["invalid1", "invalid2"], ["snack"])
    with pytest.raises(ValueError):
        ProductModel.checking_in_list(
            "allergens", ["invalid3", "invalid4"], ["cacahuete"]
        )


def test_insert_product(mock_db_products):
    return assert_insert_document_template(
        mock_db_products, ProductModel(**VALID_DATA).insert_product
    )


def test_get_products(mock_db_products):
    return assert_get_all_documents_template(
        mock_db_products, ProductModel.get_products, [VALID_DATA]
    )


def test_get_product(mock_db_products):
    return assert_get_document_template(
        mock_db_products, ProductModel.get_product, VALID_DATA
    )


def test_update_product(mock_db_products):
    new_data = {**VALID_DATA, "name": "new_value"}
    return assert_update_document_template(
        mock_db_products, ProductModel(**new_data).update_product, new_data
    )


def test_update_product_stock_by_name(mock_db_products):
    mock_db_products.find_one_and_update.return_value = {**VALID_DATA, "stock": 100}
    item_data = {
        "name": "Plato 1",
        "ingredients": [
            {"name": "Cacahuetes", "allergens": ["cereal", "huevo"], "waste": 10}
        ],
        "qty": 10,
        "price": 10.99,
    }
    result = ProductModel.update_product_stock_by_name([item_data])
    assert result[0]["stock"] == 100
    mock_db_products.find_one_and_update.assert_called_once()


def test_delete_product(mock_db_products):
    return assert_delete_document_template(
        mock_db_products, ProductModel.delete_product
    )
