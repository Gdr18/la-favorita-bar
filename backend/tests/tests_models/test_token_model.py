import pytest
import re
from pydantic import ValidationError
from datetime import datetime

from src.models.token_model import TokenModel
from tests.test_helpers import (
    assert_insert_document_template,
    assert_get_all_documents_template,
    assert_get_document_template,
    assert_delete_document_template,
    assert_update_document_template,
)

ID = "507f1f77bcf86cd799439011"
VALID_DATA = {
    "user_id": ID,
    "jti": "bb53e637-8627-457c-840f-6cae52a12e8b",
    "expires_at": 1900757341,
}
INVALID_DATA = {
    "user_id": "507f1f77bcf86cd79943901122",
    "jti": "bb53e637dd-8627-457c-840f-6cae52a12e8b",
    "expires_at": 1729684113900,
}

TOKEN_OBJECT = TokenModel(**VALID_DATA)
TOKEN_OBJECT_UPDATED = TokenModel(
    **{**VALID_DATA, "expires_at": "2030-03-22T14:22:05+01:00"}
)

USER_ID_PATTERN = re.compile("^[a-f0-9]{24}$")
JTI_PATTERN = re.compile(
    "^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$"
)


@pytest.fixture
def mock_db(mocker):
    mock_db = mocker.MagicMock()
    mocker.patch("src.services.db_service.db.refresh_tokens", new=mock_db)
    mocker.patch("src.services.db_service.db.active_tokens", new=mock_db)
    mocker.patch("src.services.db_service.db.email_tokens", new=mock_db)
    return mock_db


def test_token_model_valid_data():
    assert isinstance(TOKEN_OBJECT.user_id, str) and USER_ID_PATTERN.match(
        TOKEN_OBJECT.user_id
    )
    assert isinstance(TOKEN_OBJECT.jti, str) and JTI_PATTERN.match(TOKEN_OBJECT.jti)
    assert isinstance(TOKEN_OBJECT.expires_at, datetime)
    assert isinstance(TOKEN_OBJECT.created_at, datetime)


def test_token_model_valid_expires_at_iso8601():
    token = TokenModel(**{**VALID_DATA, "expires_at": "2030-03-22T14:22:05+01:00"})
    assert isinstance(token.expires_at, datetime)


@pytest.mark.parametrize(
    "user_id, jti, expires_at",
    [
        (VALID_DATA["user_id"], INVALID_DATA["jti"], VALID_DATA["expires_at"]),
        (INVALID_DATA["user_id"], VALID_DATA["jti"], VALID_DATA["expires_at"]),
        (VALID_DATA["user_id"], VALID_DATA["jti"], INVALID_DATA["expires_at"]),
        (VALID_DATA["user_id"], VALID_DATA["jti"], "2025-03-20T14:29:00+01:00"),
        (VALID_DATA["user_id"], VALID_DATA["jti"], ""),
        ("", VALID_DATA["jti"], VALID_DATA["expires_at"]),
        (VALID_DATA["user_id"], "", VALID_DATA["expires_at"]),
        (None, VALID_DATA["jti"], VALID_DATA["expires_at"]),
        (VALID_DATA["user_id"], None, VALID_DATA["expires_at"]),
        (VALID_DATA["user_id"], VALID_DATA["jti"], None),
    ],
)
def test_token_validation_errors(user_id, jti, expires_at):
    with pytest.raises(ValidationError):
        TokenModel(user_id=user_id, jti=jti, expires_at=expires_at)


@pytest.mark.parametrize(
    "insert_token_function",
    [
        TOKEN_OBJECT.insert_refresh_token,
        TOKEN_OBJECT.insert_email_token,
        TOKEN_OBJECT.insert_active_token,
    ],
)
def test_insert_token(mock_db, insert_token_function):
    return assert_insert_document_template(mock_db, insert_token_function)


@pytest.mark.parametrize(
    "get_tokens_function, expected_result",
    [
        (TokenModel.get_refresh_tokens, [VALID_DATA]),
        (TokenModel.get_email_tokens, [VALID_DATA]),
        (TokenModel.get_active_tokens, [VALID_DATA]),
    ],
)
def test_get_all_tokens(mock_db, get_tokens_function, expected_result):
    return assert_get_all_documents_template(
        mock_db, get_tokens_function, expected_result
    )


@pytest.mark.parametrize(
    "get_token_function, expected_result",
    [
        (TokenModel.get_refresh_token_by_user_id, VALID_DATA),
        (TokenModel.get_active_token_by_user_id, VALID_DATA),
        (TokenModel.get_email_token, VALID_DATA),
        (TokenModel.get_active_token_by_token_id, VALID_DATA),
        (TokenModel.get_refresh_token_by_token_id, VALID_DATA),
    ],
)
def test_get_token(mock_db, get_token_function, expected_result):
    return assert_get_document_template(mock_db, get_token_function, expected_result)


@pytest.mark.parametrize(
    "update_token_function, expected_result",
    [
        (
            TOKEN_OBJECT_UPDATED.update_refresh_token,
            {**VALID_DATA, "expires_at": "2030-03-22T14:22:05+01:00"},
        ),
        (
            TOKEN_OBJECT_UPDATED.update_email_token,
            {**VALID_DATA, "expires_at": "2030-03-22T14:22:05+01:00"},
        ),
        (
            TOKEN_OBJECT_UPDATED.update_active_token,
            {**VALID_DATA, "expires_at": "2030-03-22T14:22:05+01:00"},
        ),
    ],
)
def test_update_token(mock_db, update_token_function, expected_result):
    return assert_update_document_template(
        mock_db, update_token_function, expected_result
    )


@pytest.mark.parametrize(
    "delete_token_function",
    [
        TokenModel.delete_refresh_token_by_token_id,
        TokenModel.delete_email_token,
        TokenModel.delete_active_token_by_token_id,
        TokenModel.delete_refresh_token_by_user_id,
        TokenModel.delete_active_token_by_user_id,
    ],
)
def test_delete_token(mock_db, delete_token_function):
    return assert_delete_document_template(mock_db, delete_token_function)


@pytest.mark.parametrize(
    "update_or_insert_token_function",
    [
        TOKEN_OBJECT.update_or_insert_refresh_token_by_user_id,
        TOKEN_OBJECT.update_or_insert_active_token_by_user_id,
    ],
)
def test_update_or_insert_token(mock_db, update_or_insert_token_function):
    mock_db.find_one_and_update.return_value = VALID_DATA
    result = update_or_insert_token_function(ID)
    assert result == VALID_DATA
    mock_db.find_one_and_update.assert_called_once()


def test_get_email_tokens_by_user_id(mock_db):
    mock_db.find.return_value = [VALID_DATA]
    result = TokenModel.get_email_tokens_by_user_id(ID)
    assert result == [VALID_DATA]
    mock_db.find.assert_called_once()
