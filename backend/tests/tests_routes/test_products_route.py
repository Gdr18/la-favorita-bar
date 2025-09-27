import pytest
import json
from pymongo.errors import PyMongoError

from tests.test_helpers import app, client, auth_header
from src.models.product_model import ProductModel
from src.models.dish_model import DishModel


VALID_PRODUCT_DATA = {
    "name": "Cacahuetes",
    "stock": 345,
    "categories": ["snack", "otro"],
    "allergens": ["cacahuete"],
    "brand": "marca",
    "notes": "notas",
}
ID = "507f1f77bcf86cd799439011"


@pytest.fixture
def mock_get_jwt(mocker):
    return mocker.patch("src.routes.products_route.get_jwt")


@pytest.fixture
def mock_get_product(mocker):
    return mocker.patch.object(ProductModel, "get_product")


@pytest.fixture
def mock_update_product(mocker):
    return mocker.patch.object(ProductModel, "update_product")


@pytest.fixture
def mock_delete_product(mocker):
    return mocker.patch.object(ProductModel, "delete_product")


@pytest.mark.parametrize(
    "url, method",
    [
        ("/products/", "post"),
        ("/products/507f1f77bcf86cd799439011", "put"),
        ("/products/507f1f77bcf86cd799439011", "get"),
        ("/products/507f1f77bcf86cd799439011", "delete"),
        ("/products/", "get"),
    ],
)
def test_token_not_authorized_error(mock_get_jwt, client, auth_header, url, method):
    mock_get_jwt.return_value = {"role": 3}

    if method == "post":
        response = client.post(
            "/products/", json=VALID_PRODUCT_DATA, headers=auth_header
        )
    elif method == "put":
        response = client.put(url, json=VALID_PRODUCT_DATA, headers=auth_header)
    elif method == "get":
        response = client.get(url, headers=auth_header)
    elif method == "delete":
        response = client.delete(url, headers=auth_header)

    assert response.status_code == 403
    assert response.json["err"] == "not_auth"
    mock_get_jwt.assert_called_once()


@pytest.mark.parametrize(
    "url, method",
    [("/products/", "post"), ("/products/507f1f77bcf86cd799439011", "put")],
)
def test_not_authorized_to_set_error(
    client, auth_header, mock_get_jwt, mock_get_product, url, method
):
    mock_get_jwt.return_value = {"role": 1}

    if method == "post":
        response = client.post(
            url,
            json={**VALID_PRODUCT_DATA, "created_at": "2030-10-01T00:00:00Z"},
            headers=auth_header,
        )
    elif method == "put":
        mock_get_product.return_value = {
            **VALID_PRODUCT_DATA,
            "created_at": "2031-10-01T00:00:00Z",
        }
        response = client.put(
            url,
            json={**VALID_PRODUCT_DATA, "created_at": "2030-10-01T00:00:00Z"},
            headers=auth_header,
        )
    assert response.status_code == 403
    assert response.json["err"] == "not_auth_set"
    mock_get_jwt.assert_called_once()
    mock_get_product.assert_called_once() if method == "put" else None


@pytest.mark.parametrize(
    "url, method",
    [
        ("/products/507f1f77bcf86cd799439011", "delete"),
        ("/products/507f1f77bcf86cd799439011", "put"),
        ("/products/507f1f77bcf86cd799439011", "get"),
    ],
)
def test_product_not_found_error(
    mocker,
    client,
    auth_header,
    mock_get_jwt,
    mock_get_product,
    mock_delete_product,
    url,
    method,
):
    mock_get_jwt.return_value = {"role": 1}

    if method in ["get", "put"]:
        mock_get_product.return_value = None
    else:
        mock_delete_product.return_value = mocker.MagicMock(deleted_count=0)

    if method == "put":
        response = client.put(
            f"/products/{ID}", json=VALID_PRODUCT_DATA, headers=auth_header
        )
    elif method == "get":
        response = client.get(f"/products/{ID}", headers=auth_header)
    elif method == "delete":
        response = client.delete(f"/products/{ID}", headers=auth_header)

    assert response.status_code == 404
    assert response.json["err"] == "not_found"
    (
        mock_get_product.assert_called_once()
        if method != "delete"
        else mock_delete_product.assert_called_once()
    )


def test_add_product_success(mocker, client, auth_header, mock_get_jwt):
    mock_get_jwt.return_value = {"role": 1}
    mock_db = mocker.patch.object(
        ProductModel,
        "insert_product",
        return_value=mocker.MagicMock(inserted_id=ID),
    )

    response = client.post("/products/", json=VALID_PRODUCT_DATA, headers=auth_header)

    assert response.status_code == 201
    assert response.json["msg"] == f"Producto añadido de forma satisfactoria"
    mock_get_jwt.assert_called_once()
    mock_db.assert_called_once()


def test_get_products_success(mocker, mock_get_jwt, client, auth_header):
    mock_get_jwt.return_value = {"role": 1}
    mock_db = mocker.patch.object(
        ProductModel, "get_products", return_value=[VALID_PRODUCT_DATA]
    )

    response = client.get("/products/", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == [VALID_PRODUCT_DATA]
    mock_get_jwt.assert_called_once()
    mock_db.assert_called_once()


def test_update_product_success(
    mocker, client, auth_header, mock_get_jwt, mock_get_product, mock_update_product
):
    mock_get_jwt.return_value = {"role": 1}
    mock_get_product.return_value = VALID_PRODUCT_DATA
    mock_update_product.return_value = {**VALID_PRODUCT_DATA, "stock": 0}
    mock_update_dishes = mocker.patch.object(
        DishModel,
        "update_dishes_availability",
        return_value=mocker.MagicMock(updated_id=ID),
    )

    response = client.put(f"/products/{ID}", json={"stock": 0}, headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == {**VALID_PRODUCT_DATA, "stock": 0}
    mock_get_jwt.assert_called_once()
    mock_get_product.assert_called_once()
    mock_update_product.assert_called_once()
    mock_update_dishes.assert_called_once()


def test_update_product_exception(
    client, auth_header, mock_get_jwt, mock_get_product, mock_update_product
):
    mock_get_jwt.return_value = {"role": 1}
    mock_get_product.return_value = {"name": "Cacahuetes", "stock": 10}
    mock_update_product.side_effect = PyMongoError("Database error")

    response = client.put(
        f"/products/{ID}", json=VALID_PRODUCT_DATA, headers=auth_header
    )

    assert response.status_code == 500
    assert response.json["err"] == "db_generic"
    mock_get_jwt.assert_called_once()
    mock_get_product.assert_called_once()
    mock_update_product.assert_called_once()


def test_get_product_success(client, auth_header, mock_get_jwt, mock_get_product):
    mock_get_jwt.return_value = {"role": 1}
    mock_get_product.return_value = VALID_PRODUCT_DATA

    response = client.get(f"/products/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == VALID_PRODUCT_DATA
    mock_get_jwt.assert_called_once()
    mock_get_product.assert_called_once()


def test_delete_product_success(
    mocker, client, auth_header, mock_get_jwt, mock_delete_product
):
    mock_get_jwt.return_value = {"role": 1}
    mock_delete_product.return_value = mocker.MagicMock(deleted_count=1)

    response = client.delete(f"/products/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert response.json["msg"] == f"Producto eliminado de forma satisfactoria"
    mock_get_jwt.assert_called_once()
    mock_delete_product.assert_called_once()
