import pytest
from pymongo.errors import ConnectionFailure
from pymongo.database import Database
from flask import Response

from src.services.db_service import db_connection
from tests.test_helpers import app


def test_db_connection_success(mocker):
    mock_client = mocker.patch("src.services.db_service.client")
    mock_database = mocker.MagicMock(spec=Database)
    mock_client.__getitem__.return_value = mock_database

    result = db_connection()

    assert result == mock_database
    assert isinstance(result, Database)
    mock_client.__getitem__.assert_called_once()


def test_db_connection_error(mocker, app):
    with app.app_context():
        mock_client = mocker.patch(
            "src.services.db_service.client",
        )
        error = ConnectionFailure("Connection error")
        mock_client.__getitem__.side_effect = error

        result, status_code = db_connection()

        assert status_code == 500
        assert result.json["err"] == "db_connection"
        mock_client.__getitem__.assert_called_once()
