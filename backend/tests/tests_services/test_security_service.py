import pytest
from datetime import timedelta

from src.models.token_model import TokenModel
from src.services.security_service import (
    google,
    verify_password,
    verify_google_identity,
    generate_access_token,
    generate_refresh_token,
    generate_email_token,
    get_expiration_time_access_token,
    get_expiration_time_refresh_token,
    delete_active_token,
    delete_refresh_token,
    check_if_token_active_callback,
    revoked_token_callback,
    expired_token_callback,
    unauthorized_callback,
)
from tests.test_helpers import app

ID = "507f1f77bcf86cd799439011"
JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
VALID_JWT = {
    "sub": ID,
    "jti": "bb53e637-8627-457c-840f-6cae52a12e8b",
    "exp": 1919068218,
}
VALID_USER_DATA = {
    "_id": ID,
    "name": "John Doe",
    "email": "john.doe@outlook.com",
    "password": "ValidPass123!",
    "role": 1,
    "phone": "+34666666666",
    "basket": [{"name": "galletas", "qty": 1, "price": 3.33}],
    "addresses": [{"line_one": "Calle Falsa 123", "postal_code": "12345"}],
}


def test_verify_password(mocker):
    mock_check_password = mocker.patch(
        "src.services.security_service.bcrypt.check_password_hash", return_value=True
    )
    db_password = "hashed_password"
    password = "plain_password"
    result = verify_password(db_password, password)
    assert result is True
    mock_check_password.assert_called_once_with(db_password, password)


def test_verify_google_identity(mocker, app):
    google_token = "fake_google_token"
    user_email = "user@example.com"
    with app.app_context():
        mock_google = mocker.patch.object(
            google, "parse_id_token", return_value={"email": user_email}
        )
        result = verify_google_identity(google_token, user_email)
        assert result is True
        mock_google.assert_called_once_with(google_token)


@pytest.mark.parametrize(
    "function_creation_token, method_db, function_name, jwt_decoded",
    [
        (
            "create_access_token",
            "update_or_insert_active_token_by_user_id",
            generate_access_token,
            {
                "identity": ID,
                "expires_delta": timedelta(minutes=15),
                "additional_claims": {"role": VALID_USER_DATA["role"]},
            },
        ),
        (
            "create_refresh_token",
            "update_or_insert_refresh_token_by_user_id",
            generate_refresh_token,
            {"identity": ID, "expires_delta": timedelta(hours=3)},
        ),
        (
            "create_access_token",
            None,
            generate_email_token,
            {"identity": ID, "expires_delta": timedelta(days=1)},
        ),
    ],
)
def test_generation_tokens(
    mocker, function_creation_token, method_db, function_name, jwt_decoded
):
    mock_session = mocker.patch("src.services.db_service.client.start_session")
    mock_creation_token = mocker.patch(
        f"src.services.security_service.{function_creation_token}", return_value=JWT
    )
    mock_decode_token = mocker.patch(
        "src.services.security_service.decode_token", return_value=VALID_JWT
    )
    mock_call_db = mocker.patch.object(TokenModel, method_db) if method_db else None
    result = (
        function_name(VALID_USER_DATA, mock_session)
        if method_db
        else function_name(VALID_USER_DATA)
    )

    assert result == JWT if method_db else isinstance(result, tuple)
    mock_creation_token.assert_called_once_with(**jwt_decoded)
    mock_call_db.assert_called_once() if method_db else None
    mock_decode_token.assert_called_once_with(JWT)


@pytest.mark.parametrize(
    "function_name, role, time",
    [
        (get_expiration_time_access_token, 1, timedelta(minutes=15)),
        (get_expiration_time_access_token, 2, timedelta(hours=3)),
        (get_expiration_time_access_token, 3, timedelta(days=1)),
        (get_expiration_time_refresh_token, 1, timedelta(hours=3)),
        (get_expiration_time_refresh_token, 2, timedelta(hours=6)),
        (get_expiration_time_refresh_token, 3, timedelta(days=30)),
    ],
)
def test_expiration_time_token_functions(function_name, role, time):
    result = function_name(role)
    assert isinstance(result, timedelta) and result == time


@pytest.mark.parametrize(
    "function_name, class_method",
    [
        (
            delete_active_token,
            "delete_active_token_by_user_id",
        ),
        (
            delete_refresh_token,
            "delete_refresh_token_by_user_id",
        ),
    ],
)
def test_revoke_tokens_functions(mocker, function_name, class_method):
    mock_db_call = mocker.patch.object(
        TokenModel, class_method, return_value={"deleted_count": 1}
    )
    result = function_name(ID)
    assert result == {"deleted_count": 1}
    mock_db_call.assert_called_once()


def test_check_if_token_active_callback(mocker, app):
    mocker.patch("src.services.security_service.config", "config")
    mock_db_call = mocker.patch.object(
        TokenModel, "get_active_token_by_user_id", return_value=VALID_JWT
    )
    result = check_if_token_active_callback(None, VALID_JWT)
    assert result is False
    mock_db_call.assert_called_once()


def test_check_if_token_active_callback_mode_dev(mocker, app):
    mocker.patch("src.services.security_service.config", "config.DevelopmentConfig")
    result = check_if_token_active_callback(None, VALID_JWT)
    assert result is False


@pytest.mark.parametrize(
    "function_name, args, msg",
    [
        (revoked_token_callback, (None, None), "El token ha sido revocado"),
        (expired_token_callback, (None, None), "El token ha expirado"),
        (
            unauthorized_callback,
            ("error_message",),
            "Necesita un token válido para acceder a esta ruta",
        ),
    ],
)
def test_auto_response_jwt_functions(app, function_name, args, msg):
    with app.app_context():
        response, status_code = function_name(*args)
        assert status_code == 401
        assert response.json["msg"] == msg
