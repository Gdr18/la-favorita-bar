import pytest
import re
from pydantic import ValidationError
from email_validator import validate_email
from datetime import datetime

from src.models.user_model import UserModel
from tests.test_helpers import (
    assert_update_document_template,
    assert_delete_document_template,
    assert_get_document_template,
    assert_get_all_documents_template,
    assert_insert_document_template,
)


ID = "507f1f77bcf86cd799439011"
BCRYPT_PATTERN = re.compile(r"^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$")
PASSWORD_PATTERN = re.compile(
    r"^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[!@#$%^&*_-]).{8,}$"
)
PHONE_PATTERN = re.compile(r"^\+\d{9,15}$")

VALID_DATA_EMAIL = {
    "name": "John Doe",
    "email": "john.doe@outlook.com",
    "password": "ValidPass123!",
    "role": 1,
    "phone": "+34666666666",
    "basket": [
        {
            "name": "galletas",
            "qty": 1,
            "price": 3.33,
            "custom": {"chocolate": True, "nuts": True},
        }
    ],
    "addresses": [{"line_one": "Calle Falsa 123", "postal_code": "03001"}],
}

VALID_DATA_GOOGLE = {
    "name": "John Doe",
    "email": "john.doe@google.com",
    "auth_provider": "google",
    "role": 1,
    "phone": "+34666666666",
    "basket": [
        {
            "name": "galletas",
            "qty": 1,
            "price": 3.33,
            "custom": {"chocolate": False, "nuts": True},
        }
    ],
    "addresses": [{"line_one": "Calle Falsa 123", "postal_code": "03001"}],
}


@pytest.fixture
def mock_db(mocker):
    mock_db = mocker.MagicMock()
    mocker.patch("src.services.db_service.db.users", new=mock_db)
    return mock_db


def test_user_valid_data_email():
    user = UserModel(**VALID_DATA_EMAIL)
    assert isinstance(user.name, str) and 1 <= len(user.name) <= 50
    assert (
        isinstance(user.email, str)
        and 5 <= len(user.email) <= 100
        and validate_email(user.email)
    )
    assert BCRYPT_PATTERN.match(user.password) or PASSWORD_PATTERN.match(user.password)
    assert user.phone is None or PHONE_PATTERN.match(user.phone)
    assert user.basket is None or (
        isinstance(user.basket, list)
        and all(isinstance(item, dict) for item in user.basket)
    )
    assert user.basket[0]["custom"] is None or isinstance(
        user.basket[0]["custom"], dict
    )
    assert user.addresses is None or (
        isinstance(user.addresses, list)
        and all(isinstance(item, dict) for item in user.addresses)
    )
    assert 0 <= user.role <= 3
    assert user.confirmed is False
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.expires_at, datetime)


def test_user_valid_data_google():
    user = UserModel(**VALID_DATA_GOOGLE)
    assert isinstance(user.name, str) and 1 <= len(user.name) <= 50
    assert (
        isinstance(user.email, str)
        and 5 <= len(user.email) <= 100
        and validate_email(user.email)
    )
    assert user.password is None
    assert user.phone is None or PHONE_PATTERN.match(user.phone)
    assert user.basket is None or (
        isinstance(user.basket, list)
        and all(isinstance(item, dict) for item in user.basket)
    )
    assert user.addresses is None or (
        isinstance(user.addresses, list)
        and all(isinstance(item, dict) for item in user.addresses)
    )
    assert 0 <= user.role <= 3
    assert user.confirmed is True
    assert isinstance(user.created_at, datetime)
    assert user.expires_at is None


def test_user_validate_password_bcrypt():
    user = UserModel(
        name=VALID_DATA_EMAIL["name"],
        email=VALID_DATA_EMAIL["email"],
        password="$2a$10$JN3FJiqzSy22GplwwrCbuuf/EwUj3Oa3yhi3r.1HyRL7FxOAcvSGu",
    )
    assert BCRYPT_PATTERN.match(user.password)


@pytest.mark.parametrize(
    "name, email, password, role, auth_provider, phone, basket, addresses",
    [
        (
            None,
            VALID_DATA_EMAIL["email"],
            VALID_DATA_EMAIL["password"],
            VALID_DATA_EMAIL["role"],
            "email",
            None,
            None,
            None,
        ),
        (
            "",
            VALID_DATA_EMAIL["email"],
            VALID_DATA_EMAIL["password"],
            VALID_DATA_EMAIL["role"],
            "email",
            None,
            None,
            None,
        ),
        (
            VALID_DATA_EMAIL["name"],
            None,
            VALID_DATA_EMAIL["password"],
            VALID_DATA_EMAIL["role"],
            "email",
            None,
            None,
            None,
        ),
        (
            VALID_DATA_EMAIL["name"],
            "gador@e.eu",
            VALID_DATA_EMAIL["password"],
            VALID_DATA_EMAIL["role"],
            "email",
            None,
            None,
            None,
        ),
        (
            VALID_DATA_EMAIL["name"],
            VALID_DATA_EMAIL["email"],
            None,
            VALID_DATA_EMAIL["role"],
            "email",
            None,
            None,
            None,
        ),
        (
            VALID_DATA_EMAIL["name"],
            VALID_DATA_EMAIL["email"],
            "short1!",
            VALID_DATA_EMAIL["role"],
            "email",
            None,
            None,
            None,
        ),
        (
            VALID_DATA_EMAIL["name"],
            VALID_DATA_EMAIL["email"],
            "nouppercase1!",
            VALID_DATA_EMAIL["role"],
            "email",
            None,
            None,
            None,
        ),
        (
            VALID_DATA_EMAIL["name"],
            VALID_DATA_EMAIL["email"],
            "NOLOWERCASE1!",
            VALID_DATA_EMAIL["role"],
            "email",
            None,
            None,
            None,
        ),
        (
            VALID_DATA_EMAIL["name"],
            VALID_DATA_EMAIL["email"],
            "NoDigitPass!",
            VALID_DATA_EMAIL["role"],
            "email",
            None,
            None,
            None,
        ),
        (
            VALID_DATA_EMAIL["name"],
            VALID_DATA_EMAIL["email"],
            "NoSpecialChar1",
            VALID_DATA_EMAIL["role"],
            "email",
            None,
            None,
            None,
        ),
        (
            VALID_DATA_EMAIL["name"],
            VALID_DATA_EMAIL["email"],
            VALID_DATA_EMAIL["password"],
            4,
            "email",
            None,
            None,
            None,
        ),
        (
            VALID_DATA_EMAIL["name"],
            VALID_DATA_EMAIL["email"],
            VALID_DATA_EMAIL["password"],
            VALID_DATA_EMAIL["role"],
            "hola",
            None,
            None,
            None,
        ),
        (
            VALID_DATA_EMAIL["name"],
            VALID_DATA_EMAIL["email"],
            VALID_DATA_EMAIL["password"],
            VALID_DATA_EMAIL["role"],
            "email",
            "+1234567890",
            None,
            None,
        ),
        (
            VALID_DATA_EMAIL["name"],
            VALID_DATA_EMAIL["email"],
            VALID_DATA_EMAIL["password"],
            VALID_DATA_EMAIL["role"],
            "email",
            None,
            ["hola"],
            None,
        ),
        (
            VALID_DATA_EMAIL["name"],
            VALID_DATA_EMAIL["email"],
            VALID_DATA_EMAIL["password"],
            VALID_DATA_EMAIL["role"],
            "email",
            None,
            "hola",
            None,
        ),
        (
            VALID_DATA_EMAIL["name"],
            VALID_DATA_EMAIL["email"],
            VALID_DATA_EMAIL["password"],
            VALID_DATA_EMAIL["role"],
            "email",
            None,
            None,
            [123456],
        ),
        (
            VALID_DATA_EMAIL["name"],
            VALID_DATA_EMAIL["email"],
            VALID_DATA_EMAIL["password"],
            VALID_DATA_EMAIL["role"],
            "email",
            None,
            None,
            "hola",
        ),
    ],
)
def test_user_validation_error(
    name, email, password, role, auth_provider, phone, basket, addresses
):
    with pytest.raises(ValidationError):
        UserModel(
            name=name,
            email=email,
            password=password,
            role=role,
            auth_provider=auth_provider,
            phone=phone,
            basket=basket,
            addresses=addresses,
        )


def test_insert_user(mock_db):
    return assert_insert_document_template(
        mock_db, UserModel(**VALID_DATA_EMAIL).insert_user
    )


def test_insert_or_update_user_by_email(mock_db):
    mock_db.find_one_and_update.return_value = VALID_DATA_EMAIL
    result = UserModel(**VALID_DATA_EMAIL).insert_or_update_user_by_email()
    assert result == VALID_DATA_EMAIL
    mock_db.find_one_and_update.assert_called_once()


def test_get_users(mock_db):
    return assert_get_all_documents_template(
        mock_db, UserModel.get_users, [VALID_DATA_EMAIL]
    )


@pytest.mark.parametrize(
    "method, expected_result",
    [
        (UserModel.get_user_by_user_id, {**VALID_DATA_EMAIL, "_id": ID}),
        (UserModel.get_user_by_user_id_without_id, VALID_DATA_EMAIL),
    ],
)
def test_get_user_by_user_id_with_and_without_id(mock_db, method, expected_result):
    return assert_get_document_template(mock_db, method, expected_result)


def test_get_user_by_email(mock_db):
    mock_db.find_one.return_value = VALID_DATA_EMAIL
    result = UserModel.get_user_by_email(VALID_DATA_EMAIL["email"])
    assert result == VALID_DATA_EMAIL
    mock_db.find_one.assert_called_once()


def test_update_user(mock_db):
    new_data = {**VALID_DATA_EMAIL, "name": "Jane Doe"}
    user_object = UserModel(**new_data)
    return assert_update_document_template(mock_db, user_object.update_user, new_data)


def test_delete_user(mock_db):
    return assert_delete_document_template(mock_db, UserModel.delete_user)
