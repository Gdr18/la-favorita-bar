import pytest
import re

from src.models.order_model import OrderModel
from tests.test_helpers import (
    assert_get_document_template,
    assert_insert_document_template,
    assert_get_all_documents_template,
    assert_delete_document_template,
    assert_update_document_template,
)


USER_ID_PATTERN = re.compile(r"^[a-f0-9]{24}$")
VALID_DATA = {
    "user_id": "507f1f77bcf86cd799439011",
    "items": [
        {
            "name": "Plato 1",
            "qty": 2,
            "ingredients": [
                {"name": "Huevo", "allergens": ["huevo"], "waste": 0.1},
                {"name": "Tomate", "waste": 0.2},
            ],
            "custom": {"Huevo": True, "Tomate": False},
            "price": 5.0,
        }
    ],
    "type_order": "delivery",
    "address": {
        "name": "Casa",
        "line_one": "Calle de la Libertad 5",
        "postal_code": "03001",
    },
    "payment": "cash",
    "total_price": 10.0,
    "state": "pending",
}


@pytest.fixture
def mock_db(mocker):
    mock_db = mocker.MagicMock()
    mocker.patch("src.services.db_service.db.orders", new=mock_db)
    return mock_db


def test_order_valid_data():
    order = OrderModel(**VALID_DATA)
    VALID_DATA["items"][0]["custom"] = {"Huevo": True, "Tomate": True}
    order_two = OrderModel(**{**VALID_DATA, "type_order": "local"})
    assert isinstance(order.user_id, str) and USER_ID_PATTERN.match(order.user_id)
    assert isinstance(order.items, list) and all(
        isinstance(item, dict) for item in order.items
    )
    assert order.type_order in ["delivery", "collect", "take_away"]
    assert order.address is None or isinstance(order.address, dict)
    assert order.payment in ["cash", "card", "paypal"]
    assert isinstance(order.total_price, float) and order.total_price > 0
    assert order.state in [
        "pending",
        "accepted",
        "cooking",
        "canceled",
        "ready",
        "sent",
        "delivered",
    ]
    assert order_two.state == "accepted"
    assert order_two.items[0]["custom"] is None


@pytest.mark.parametrize(
    "user_id, items, type_order, address, payment, total_price, state",
    [
        (
            None,
            VALID_DATA["items"],
            VALID_DATA["type_order"],
            VALID_DATA["address"],
            VALID_DATA["payment"],
            VALID_DATA["total_price"],
            VALID_DATA["state"],
        ),
        (
            1234,
            VALID_DATA["items"],
            VALID_DATA["type_order"],
            VALID_DATA["address"],
            VALID_DATA["payment"],
            VALID_DATA["total_price"],
            VALID_DATA["state"],
        ),
        (
            VALID_DATA["user_id"],
            None,
            VALID_DATA["type_order"],
            VALID_DATA["address"],
            VALID_DATA["payment"],
            VALID_DATA["total_price"],
            VALID_DATA["state"],
        ),
        (
            VALID_DATA["user_id"],
            [],
            VALID_DATA["type_order"],
            VALID_DATA["address"],
            VALID_DATA["payment"],
            VALID_DATA["total_price"],
            VALID_DATA["state"],
        ),
        (
            VALID_DATA["user_id"],
            1234,
            VALID_DATA["type_order"],
            VALID_DATA["address"],
            VALID_DATA["payment"],
            VALID_DATA["total_price"],
            VALID_DATA["state"],
        ),
        (
            VALID_DATA["user_id"],
            [{"hola": "soy Merche"}],
            VALID_DATA["type_order"],
            VALID_DATA["address"],
            VALID_DATA["payment"],
            VALID_DATA["total_price"],
            VALID_DATA["state"],
        ),
        (
            VALID_DATA["user_id"],
            VALID_DATA["items"],
            None,
            VALID_DATA["address"],
            VALID_DATA["payment"],
            VALID_DATA["total_price"],
            VALID_DATA["state"],
        ),
        (
            VALID_DATA["user_id"],
            VALID_DATA["items"],
            "hola",
            VALID_DATA["address"],
            VALID_DATA["payment"],
            VALID_DATA["total_price"],
            VALID_DATA["state"],
        ),
        (
            VALID_DATA["user_id"],
            VALID_DATA["items"],
            1234,
            VALID_DATA["address"],
            VALID_DATA["payment"],
            VALID_DATA["total_price"],
            VALID_DATA["state"],
        ),
        (
            VALID_DATA["user_id"],
            VALID_DATA["items"],
            "delivery",
            None,
            VALID_DATA["payment"],
            VALID_DATA["total_price"],
            VALID_DATA["state"],
        ),
        (
            VALID_DATA["user_id"],
            VALID_DATA["items"],
            VALID_DATA["type_order"],
            1234,
            VALID_DATA["payment"],
            VALID_DATA["total_price"],
            VALID_DATA["state"],
        ),
        (
            VALID_DATA["user_id"],
            VALID_DATA["items"],
            VALID_DATA["type_order"],
            {"hola": "soy Merche"},
            VALID_DATA["payment"],
            VALID_DATA["total_price"],
            VALID_DATA["state"],
        ),
        (
            VALID_DATA["user_id"],
            VALID_DATA["items"],
            VALID_DATA["type_order"],
            {},
            VALID_DATA["payment"],
            VALID_DATA["total_price"],
            VALID_DATA["state"],
        ),
        (
            VALID_DATA["user_id"],
            VALID_DATA["items"],
            VALID_DATA["type_order"],
            VALID_DATA["address"],
            None,
            VALID_DATA["total_price"],
            VALID_DATA["state"],
        ),
        (
            VALID_DATA["user_id"],
            VALID_DATA["items"],
            VALID_DATA["type_order"],
            VALID_DATA["address"],
            "hola",
            VALID_DATA["total_price"],
            VALID_DATA["state"],
        ),
        (
            VALID_DATA["user_id"],
            VALID_DATA["items"],
            VALID_DATA["type_order"],
            VALID_DATA["address"],
            1234,
            VALID_DATA["total_price"],
            VALID_DATA["state"],
        ),
        (
            VALID_DATA["user_id"],
            VALID_DATA["items"],
            VALID_DATA["type_order"],
            VALID_DATA["address"],
            VALID_DATA["payment"],
            None,
            VALID_DATA["state"],
        ),
        (
            VALID_DATA["user_id"],
            VALID_DATA["items"],
            VALID_DATA["type_order"],
            VALID_DATA["address"],
            VALID_DATA["payment"],
            -12.0,
            VALID_DATA["state"],
        ),
        (
            VALID_DATA["user_id"],
            VALID_DATA["items"],
            VALID_DATA["type_order"],
            VALID_DATA["address"],
            VALID_DATA["payment"],
            VALID_DATA["total_price"],
            None,
        ),
        (
            VALID_DATA["user_id"],
            VALID_DATA["items"],
            VALID_DATA["type_order"],
            VALID_DATA["address"],
            VALID_DATA["payment"],
            VALID_DATA["total_price"],
            "hola",
        ),
        (
            VALID_DATA["user_id"],
            VALID_DATA["items"],
            VALID_DATA["type_order"],
            VALID_DATA["address"],
            VALID_DATA["payment"],
            VALID_DATA["total_price"],
            1234,
        ),
    ],
)
def test_order_validation_errors(
    user_id, items, type_order, address, payment, total_price, state
):
    with pytest.raises(ValueError):
        OrderModel(
            user_id=user_id,
            items=items,
            type_order=type_order,
            address=address,
            payment=payment,
            total_price=total_price,
            state=state,
        )


def test_check_level_state():
    with pytest.raises(ValueError):
        OrderModel.check_level_state("cooking", "ready")
        OrderModel.check_level_state("sent", "cooking")


def test_insert_order(mock_db):
    return assert_insert_document_template(
        mock_db, OrderModel(**VALID_DATA).insert_order
    )


def test_get_orders(mock_db):
    return assert_get_all_documents_template(
        mock_db, OrderModel.get_orders, [VALID_DATA]
    )


def test_get_orders_by_user_id(mock_db):
    mock_cursor = mock_db.find.return_value
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = [VALID_DATA]
    result = OrderModel.get_orders_by_user_id(VALID_DATA["user_id"], 1, 10)
    assert result[0]["user_id"] == VALID_DATA["user_id"]
    assert result == [VALID_DATA]
    mock_db.find.assert_called_once()


def test_get_order(mock_db):
    return assert_get_document_template(mock_db, OrderModel.get_order, VALID_DATA)


def test_update_order(mock_db):
    new_data = {**VALID_DATA, "type_order": "local"}
    order_object = OrderModel(**new_data)
    return assert_update_document_template(mock_db, order_object.update_order, new_data)


def test_delete_order(mock_db):
    return assert_delete_document_template(mock_db, OrderModel.delete_order)
