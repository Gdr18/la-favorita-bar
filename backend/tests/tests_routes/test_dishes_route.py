import pytest
import json

from src.models.dish_model import DishModel
from tests.test_helpers import app, client, auth_header


VALID_DISH_DATA = {
    "name": "Pizza",
    "description": "Delicious pizza",
    "category": "main",
    "ingredients": [{"name": "Huevo", "waste": 0}],
    "price": 10.99,
}
ID = "507f1f77bcf86cd799439011"


@pytest.fixture
def mock_get_jwt(mocker):
    return mocker.patch("src.routes.dishes_route.get_jwt")


@pytest.fixture
def mock_get_dish(mocker):
    return mocker.patch.object(DishModel, "get_dish")


@pytest.fixture
def mock_delete_dish(mocker):
    return mocker.patch.object(DishModel, "delete_dish")


@pytest.mark.parametrize(
    "url, method",
    [
        ("/dishes/", "post"),
        ("/dishes/507f1f77bcf86cd799439011", "put"),
        ("/dishes/507f1f77bcf86cd799439011", "delete"),
    ],
)
def test_token_not_authorized_error(mock_get_jwt, client, auth_header, url, method):
    mock_get_jwt.return_value = {"role": 2}

    if method == "put":
        response = client.put(url, json=VALID_DISH_DATA, headers=auth_header)
    elif method == "delete":
        response = client.delete(url, headers=auth_header)
    elif method == "post":
        response = client.post(url, json=VALID_DISH_DATA, headers=auth_header)

    assert response.status_code == 403
    assert response.json["err"] == "not_auth"
    mock_get_jwt.assert_called_once()


@pytest.mark.parametrize(
    "url, method",
    [
        ("/dishes/", "post"),
        ("/dishes/507f1f77bcf86cd799439011", "put"),
    ],
)
def test_token_not_authorized_to_set_error(
    mock_get_jwt, mock_get_dish, client, auth_header, url, method
):
    mock_get_jwt.return_value = {"role": 1}
    mock_get_dish.return_value = {
        **VALID_DISH_DATA,
        "created_at": "2025-06-10T20:11:10+02:00",
    }

    if method == "put":
        response = client.put(
            url,
            json={**VALID_DISH_DATA, "created_at": "2025-06-12T20:11:10+02:00"},
            headers=auth_header,
        )
    elif method == "post":
        response = client.post(
            url,
            json={**VALID_DISH_DATA, "created_at": "2025-06-12T20:11:10+02:00"},
            headers=auth_header,
        )

    assert response.status_code == 403
    assert response.json["err"] == "not_auth_set"
    mock_get_jwt.assert_called_once()


@pytest.mark.parametrize(
    "url, method",
    [
        ("/dishes/category/snacks", "get"),
        ("/dishes/507f1f77bcf86cd799439011", "get"),
        ("/dishes/507f1f77bcf86cd799439011", "put"),
        ("/dishes/507f1f77bcf86cd799439011", "delete"),
    ],
)
def test_dish_not_found_error(
    mocker,
    mock_get_jwt,
    mock_get_dish,
    mock_delete_dish,
    client,
    auth_header,
    url,
    method,
):
    mock_get_category_dishes = mocker.patch.object(DishModel, "get_dishes_by_category")
    mock_get_jwt.return_value = {"role": 1}

    if method == "get" and "category" in url:
        mock_get_category_dishes.return_value = None
    elif method in ["put", "get"]:
        mock_get_dish.return_value = None
    else:
        mock_delete_dish.return_value = mocker.MagicMock(deleted_count=0)

    if method == "get":
        response = client.get(url)
    elif method == "put":
        response = client.put(url, json=VALID_DISH_DATA, headers=auth_header)
    elif method == "delete":
        response = client.delete(url, headers=auth_header)

    assert response.status_code == 404
    assert response.json["err"] == "not_found"

    mock_get_jwt.assert_called_once() if method != "get" else None
    if "category" in url:
        mock_get_category_dishes.assert_called_once() if method == "get" else None
    elif method in ["put", "get"]:
        mock_get_dish.assert_called_once()
    else:
        mock_delete_dish.assert_called_once()


def test_add_dish_success(mocker, client, auth_header, mock_get_jwt):
    mock_get_jwt.return_value = {"role": 1}
    mock_db = mocker.patch.object(
        DishModel, "insert_dish", return_value=mocker.MagicMock(inserted_id=ID)
    )

    response = client.post("/dishes/", json=VALID_DISH_DATA, headers=auth_header)

    assert response.status_code == 201
    assert response.json["msg"] == f"Plato añadido de forma satisfactoria"
    mock_get_jwt.assert_called_once()
    mock_db.assert_called_once()


def test_get_dishes_success(mocker, client):
    mock_db = mocker.patch.object(
        DishModel, "get_dishes", return_value=[VALID_DISH_DATA]
    )

    response = client.get("/dishes/")

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == [VALID_DISH_DATA]
    mock_db.assert_called_once()


def test_get_dishes_by_category_success(mocker, client):
    mock_db = mocker.patch.object(
        DishModel, "get_dishes_by_category", return_value=[VALID_DISH_DATA]
    )

    response = client.get("/dishes/category/main")

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == [VALID_DISH_DATA]
    mock_db.assert_called_once()


def test_get_dish_success(client, mock_get_dish):
    mock_get_dish.return_value = VALID_DISH_DATA

    response = client.get(f"/dishes/{ID}")

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == VALID_DISH_DATA
    mock_get_dish.assert_called_once()


def test_update_dish_success(mocker, client, mock_get_dish, auth_header, mock_get_jwt):
    mock_get_jwt.return_value = {"role": 1}
    mock_get_dish.return_value = VALID_DISH_DATA
    mock_update_dish = mocker.patch.object(
        DishModel,
        "update_dish",
        return_value={**VALID_DISH_DATA, "name": "Updated " "Pizza"},
    )

    response = client.put(
        f"/dishes/{ID}", json={"name": "Updated Pizza"}, headers=auth_header
    )

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == {
        **VALID_DISH_DATA,
        "name": "Updated Pizza",
    }
    mock_get_jwt.assert_called_once()
    mock_get_dish.assert_called_once()
    mock_update_dish.assert_called_once()


def test_delete_dish_success(
    mocker, client, mock_delete_dish, auth_header, mock_get_jwt
):
    mock_get_jwt.return_value = {"role": 1}
    mock_delete_dish.return_value = mocker.MagicMock(deleted_count=1)

    response = client.delete(f"/dishes/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert response.json["msg"] == f"Plato eliminado de forma satisfactoria"
    mock_get_jwt.assert_called_once()
    mock_delete_dish.assert_called_once()
