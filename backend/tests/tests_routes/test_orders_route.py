import pytest
import json
from pymongo.errors import PyMongoError

from src.models.order_model import OrderModel
from src.models.product_model import ProductModel
from tests.test_helpers import app, client, auth_header


ID = "507f1f77bcf86cd799439011"
VALID_ORDER_DATA = {
    "user_id": ID,
    "items": [
        {
            "name": "pizza",
            "qty": 2,
            "price": 10.0,
            "ingredients": [
                {"name": "tomato", "waste": 0},
            ],
        }
    ],
    "type_order": "local",
    "payment": "card",
    "total_price": 20.0,
}


@pytest.fixture
def mock_get_jwt(mocker):
    return mocker.patch("src.routes.orders_route.get_jwt")


@pytest.fixture
def mock_get_order(mocker):
    return mocker.patch.object(OrderModel, "get_order")


@pytest.fixture
def mock_update_order(mocker):
    return mocker.patch.object(OrderModel, "update_order")


@pytest.fixture
def mock_delete_order(mocker):
    return mocker.patch.object(OrderModel, "delete_order")


@pytest.mark.parametrize(
    "url, method, mock",
    [
        ("/orders/", "get", False),
        ("/orders/user/507f1f77bcf86cd799439011", "get", False),
        ("/orders/507f1f77bcf86cd799439011", "put", True),
        ("/orders/507f1f77bcf86cd799439011", "get", True),
        ("/orders/507f1f77bcf86cd799439011", "delete", False),
    ],
)
def test_not_authorized_error(
    mock_get_jwt, mock_get_order, client, auth_header, url, method, mock
):
    mock_get_jwt.return_value = {"role": 3, "sub": "507f1f77bcf86cd799439012"}
    if mock:
        mock_get_order.return_value = VALID_ORDER_DATA

    if method == "get":
        response = client.get(url, headers=auth_header)
    elif method == "put":
        response = client.put(url, json={"state": "cooking"}, headers=auth_header)
    elif method == "delete":
        response = client.delete(url, headers=auth_header)

    assert response.status_code == 403
    assert response.json["err"] == "not_auth"
    mock_get_jwt.assert_called_once()
    mock_get_order.assert_called_once() if mock else None


@pytest.mark.parametrize(
    "url, method",
    [
        ("/orders/", "post"),
        ("/orders/507f1f77bcf86cd799439011", "put"),
    ],
)
def test_not_authorized_to_set_error(
    mocker, client, auth_header, mock_get_jwt, mock_get_order, url, method
):
    if method == "post":
        mock_manual_closure = mocker.patch(
            "src.routes.orders_route.check_manual_closure", return_value=True
        )
        mock_schedule = mocker.patch(
            "src.routes.orders_route.check_schedule_bar", return_value=True
        )

        response = client.post(
            url,
            json={**VALID_ORDER_DATA, "created_at": "2025-06-10T20:11:10+02:00"},
            headers=auth_header,
        )

        mock_manual_closure.assert_called_once()
        mock_schedule.assert_called_once()
    elif method == "put":
        mock_get_jwt.return_value = {"role": 1}
        mock_get_order.return_value = {
            **VALID_ORDER_DATA,
            "created_at": "2025-06-09T20:11:10+02:00",
        }

        response = client.put(
            url,
            json={"created_at": "2025-06-10T20:11:10+02:00"},
            headers=auth_header,
        )

        mock_get_jwt.assert_called_once()
        mock_get_order.assert_called_once()

    assert response.status_code == 403
    assert response.json["err"] == "not_auth_set"


@pytest.mark.parametrize(
    "url, method",
    [
        ("/orders/507f1f77bcf86cd799439011", "put"),
        ("/orders/507f1f77bcf86cd799439011", "get"),
        ("/orders/507f1f77bcf86cd799439011", "delete"),
    ],
)
def test_order_not_found_error(
    mocker,
    client,
    auth_header,
    mock_get_jwt,
    mock_get_order,
    mock_delete_order,
    url,
    method,
):
    mock_get_jwt.return_value = {"role": 1}

    if method in ["get", "put"]:
        mock_get_order.return_value = None
    else:
        mock_delete_order.return_value = mocker.MagicMock(deleted_count=0)

    if method == "put":
        response = client.put(
            f"/orders/{ID}", json={"state": "cooking"}, headers=auth_header
        )
    elif method == "get":
        response = client.get(f"/orders/{ID}", headers=auth_header)
    elif method == "delete":
        response = client.delete(f"/orders/{ID}", headers=auth_header)

    assert response.status_code == 404
    assert response.json["err"] == "not_found"
    mock_get_jwt.assert_called_once()
    (
        mock_get_order.assert_called_once()
        if method != "delete"
        else mock_delete_order.assert_called_once()
    )


def test_bar_is_closed_manually_error(mocker, client, auth_header):
    mock_manual_closure = mocker.patch(
        "src.routes.orders_route.check_manual_closure", return_value=False
    )

    response = client.post("/orders/", json=VALID_ORDER_DATA, headers=auth_header)

    assert response.status_code == 503
    assert response.json["err"] == "bar_closed_manually"
    mock_manual_closure.assert_called_once()


def test_bar_is_closed_error(mocker, client, auth_header):
    mock_manual_closure = mocker.patch(
        "src.routes.orders_route.check_manual_closure", return_value=True
    )
    mock_schedule = mocker.patch(
        "src.routes.orders_route.check_schedule_bar", return_value=False
    )

    response = client.post("/orders/", json=VALID_ORDER_DATA, headers=auth_header)

    assert response.status_code == 503
    assert response.json["err"] == "bar_closed_schedule"
    mock_manual_closure.assert_called_once()
    mock_schedule.assert_called_once()


def test_add_order_success(mocker, client, auth_header):
    mock_manual_closure = mocker.patch(
        "src.routes.orders_route.check_manual_closure", return_value=True
    )
    mock_schedule = mocker.patch(
        "src.routes.orders_route.check_schedule_bar", return_value=True
    )
    mock_db = mocker.patch.object(
        OrderModel,
        "insert_order",
        return_value=mocker.MagicMock(inserted_id=ID),
    )

    response = client.post("/orders/", json=VALID_ORDER_DATA, headers=auth_header)

    assert response.status_code == 201
    assert response.json["msg"] == f"Orden añadida de forma satisfactoria"
    mock_db.assert_called_once()
    mock_manual_closure.assert_called_once()
    mock_schedule.assert_called_once()


def test_get_orders_success(mocker, client, auth_header, mock_get_jwt):
    mock_get_jwt.return_value = {"role": 1}
    mock_db = mocker.patch.object(
        OrderModel, "get_orders", return_value=[VALID_ORDER_DATA]
    )

    response = client.get("/orders/", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == [VALID_ORDER_DATA]
    mock_db.assert_called_once()


def test_get_user_orders_success(mocker, client, auth_header):
    mock_db = mocker.patch.object(
        OrderModel, "get_orders_by_user_id", return_value=[VALID_ORDER_DATA]
    )

    response = client.get(f"/orders/user/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == [VALID_ORDER_DATA]
    mock_db.assert_called_once()


def test_update_order_success(
    mocker, mock_get_jwt, client, auth_header, mock_get_order, mock_update_order
):
    mock_get_jwt.return_value = {"role": 1}
    mock_get_order.return_value = {**VALID_ORDER_DATA, "state": "cooking"}
    mock_update_order.return_value = {**VALID_ORDER_DATA, "state": "ready"}
    mock_update_product = mocker.patch.object(
        ProductModel,
        "update_product_stock_by_name",
        return_value=[
            {
                "name": "Cacahuetes",
                "stock": 345,
                "categories": ["snack", "otro"],
                "allergens": ["cacahuete"],
                "brand": "marca",
                "notes": "notas",
            }
        ],
    )

    response = client.put(f"/orders/{ID}", json={"state": "ready"}, headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == {**VALID_ORDER_DATA, "state": "ready"}
    mock_get_order.assert_called_once()
    mock_update_order.assert_called_once()
    mock_update_product.assert_called_once()


def test_update_order_exception(
    client, auth_header, mock_get_jwt, mock_get_order, mock_update_order
):
    mock_get_jwt.return_value = {"role": 1}
    mock_get_order.return_value = {**VALID_ORDER_DATA, "state": "cooking"}
    mock_update_order.side_effect = PyMongoError("Database error")

    response = client.put(f"/orders/{ID}", json={"state": "ready"}, headers=auth_header)

    assert response.status_code == 500
    assert response.json["err"] == "db_generic"
    mock_get_order.assert_called_once()
    mock_update_order.assert_called_once()


def test_get_order_success(client, auth_header, mock_get_order):
    mock_get_order.return_value = VALID_ORDER_DATA

    response = client.get(f"/orders/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == VALID_ORDER_DATA
    mock_get_order.assert_called_once()


def test_delete_order_success(
    mocker, mock_get_jwt, client, auth_header, mock_delete_order
):
    mock_get_jwt.return_value = {"role": 1}
    mock_delete_order.return_value = mocker.MagicMock(deleted_count=1)

    response = client.delete(f"/orders/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert response.json["msg"] == f"Orden eliminada de forma satisfactoria"
    mock_delete_order.assert_called_once()
