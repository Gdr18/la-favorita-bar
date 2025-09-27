import pytest

from flask_jwt_extended import create_access_token, create_refresh_token
from src.app import run_app
from config import config

ID = "507f1f77bcf86cd799439011"


@pytest.fixture
def app():
    app = run_app(config)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_header(app):
    with app.app_context():
        access_token = create_access_token(
            identity="507f1f77bcf86cd799439011",
            additional_claims={"role": 0},
            fresh=True,
        )
        return {"Authorization": f"Bearer {access_token}"}


def assert_insert_document_template(mock_db, method):
    mock_db.insert_one.return_value.inserted_id = ID
    result = method()
    assert result.inserted_id == ID
    mock_db.insert_one.assert_called_once()


def assert_get_all_documents_template(mock_db, method, expected_result):
    mock_cursor = mock_db.find.return_value
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = expected_result
    result = method(1, 10)
    assert result == expected_result
    mock_db.find.assert_called_once()


def assert_get_document_template(mock_db, method, expected_result):
    mock_db.find_one.return_value = expected_result
    result = method(ID)
    assert result == expected_result
    mock_db.find_one.assert_called()


def assert_update_document_template(mock_db, method, expected_result):
    mock_db.find_one_and_update.return_value = expected_result
    result = method(ID)
    assert result == expected_result
    mock_db.find_one_and_update.assert_called_once()


def assert_delete_document_template(mock_db, method):
    mock_db.delete_one.return_value.deleted_count = 1
    result = method(ID)
    assert result.deleted_count == 1
    mock_db.delete_one.assert_called_once()
