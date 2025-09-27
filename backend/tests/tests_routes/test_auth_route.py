import pytest
from pymongo.errors import PyMongoError
from flask_jwt_extended import create_access_token, create_refresh_token
from flask import Response

from tests.test_helpers import app, client, auth_header
from src.models.user_model import UserModel
from src.models.token_model import TokenModel


VALID_USER_DATA = {
    "name": "TestUser",
    "email": "test_user@outlook.com",
    "password": "_Test1234",
}
INVALID_USER_DATA = {
    "name": "TestUser",
    "email": "test_user@outlook.com",
    "password": "wrong_password",
}
ID = "507f1f77bcf86cd799439011"
VALID_TOKEN_DATA = {
    "user_id": ID,
    "jti": "123e4567-e89b-42d3-a456-426614174000",
    "created_at": "2025-10-10T12:00:00Z",
    "expires_at": "2025-12-10T12:00:00Z",
}


@pytest.fixture
def auth_header_refresh(app):
    with app.app_context():
        refresh_token = create_refresh_token(
            identity="507f1f77bcf86cd799439011", additional_claims={"role": 1}
        )
        return {"Authorization": f"Bearer {refresh_token}"}


@pytest.fixture
def mock_get_jwt(mocker):
    return mocker.patch("src.routes.auth_route.get_jwt")


@pytest.fixture
def mock_send_email(mocker):
    return mocker.patch("src.routes.auth_route.send_email")


@pytest.fixture
def mock_generate_access_token(mocker):
    return mocker.patch("src.routes.auth_route.generate_access_token")


@pytest.fixture
def mock_generate_refresh_token(mocker):
    return mocker.patch("src.routes.auth_route.generate_refresh_token")


@pytest.fixture
def mock_decode_token(mocker):
    return mocker.patch("src.routes.auth_route.decode_token")


@pytest.fixture
def mock_verify_password(mocker):
    return mocker.patch("src.routes.auth_route.verify_password")


@pytest.fixture
def mock_db_get_email_tokens(mocker):
    return mocker.patch.object(
        TokenModel,
        "get_email_tokens_by_user_id",
        return_value=[
            {
                "user_id": ID,
                "jti": "123e4567-e89b-12d3-a456-426614174000",
                "created_at": "2025-10-10T12:00:00Z",
                "expires_at": "2025-12-10T12:00:00Z",
            }
        ],
    )


@pytest.fixture
def mock_db_get_user_by_user_id(mocker):
    return mocker.patch.object(UserModel, "get_user_by_user_id")


@pytest.fixture
def mock_db_get_user_by_user_id_without_id(mocker):
    return mocker.patch.object(UserModel, "get_user_by_user_id_without_id")


@pytest.fixture
def mock_db_get_user_by_email(mocker):
    return mocker.patch.object(UserModel, "get_user_by_email")


@pytest.fixture
def mock_db_insert_user(mocker):
    return mocker.patch.object(UserModel, "insert_user")


@pytest.fixture
def mock_db_update_user(mocker):
    return mocker.patch.object(UserModel, "update_user")


@pytest.fixture
def mock_db_get_refresh_token_by_user_id(mocker):
    return mocker.patch.object(TokenModel, "get_refresh_token_by_user_id")


@pytest.fixture
def mock_google_access(mocker):
    return mocker.patch("src.routes.auth_route.google.authorize_access_token")


@pytest.fixture
def mock_google_parse(mocker):
    return mocker.patch(
        "src.routes.auth_route.google.parse_id_token",
        return_value={"name": "test_user", "email": "test_user@google.com"},
    )


@pytest.fixture
def insert_or_update_call_db(mocker):
    return mocker.patch.object(
        UserModel,
        "insert_or_update_user_by_email",
        return_value={**VALID_USER_DATA, "_id": ID},
    )


@pytest.mark.parametrize(
    "url, method",
    [
        ("/auth/resend-email", "post"),
        ("/auth/login", "post"),
        ("/auth/confirm-email/test_token", "get"),
        ("/auth/change-email", "post"),
    ],
)
def test_user_not_found_error(
    client,
    auth_header,
    mock_decode_token,
    mock_db_get_email_tokens,
    mock_db_get_user_by_user_id,
    mock_db_get_user_by_email,
    mock_db_get_user_by_user_id_without_id,
    mock_get_jwt,
    url,
    method,
):
    if ("login" in url) or ("resend-email" in url):
        mock_db_get_user_by_email.return_value = None
        get_user_call_db = mock_db_get_user_by_email
    else:
        if "confirm-email" in url:
            mock_decode_token.return_value = {"sub": ID}
        else:
            mock_get_jwt.return_value = VALID_TOKEN_DATA
        mock_db_get_user_by_user_id_without_id.return_value = None
        get_user_call_db = mock_db_get_user_by_user_id_without_id

    if method == "post":
        response = client.post(url, json=VALID_USER_DATA, headers=auth_header)
    elif method == "get":
        response = client.get(url)

    assert response.status_code == 404
    assert response.json["err"] == "not_found"
    get_user_call_db.assert_called_once()
    mock_decode_token.assert_called_once() if "confirm-email" in url else None


def test_register_success(mocker, client, mock_send_email, mock_db_insert_user):
    mock_db_insert_user.return_value = mocker.MagicMock(inserted_id=ID)
    mock_send_email

    response = client.post(
        "/auth/register",
        json=VALID_USER_DATA,
    )

    assert response.status_code == 201
    assert response.json["msg"] == f"Usuario añadido de forma satisfactoria"
    mock_db_insert_user.assert_called_once()
    mock_send_email.assert_called_once()


def test_register_with_role_error(client):
    response = client.post(
        "/auth/register",
        json={**VALID_USER_DATA, "role": 3},
    )

    assert response.status_code == 403
    assert response.json["err"] == "not_auth_set"


def test_register_exception_error(client, mock_db_insert_user):
    mock_db_insert_user.side_effect = PyMongoError("Database error")

    response = client.post(
        "/auth/register",
        json=VALID_USER_DATA,
    )

    assert response.status_code == 500
    assert response.json["err"] == "db_generic"
    mock_db_insert_user.assert_called_once()


def test_change_email_auth_provider_email_success(
    client,
    auth_header,
    mock_get_jwt,
    mock_send_email,
    mock_db_get_user_by_user_id_without_id,
    mock_db_update_user,
):
    mock_get_jwt.return_value = {"role": 3, "sub": ID}
    mock_db_get_user_by_user_id_without_id.return_value = {
        **VALID_USER_DATA,
        "auth_provider": "email",
        "confirmed": True,
    }
    mock_db_update_user.return_value = (
        {
            **VALID_USER_DATA,
            "email": "testuser2@outlook.com",
            "auth_provider": "email",
            "confirmed": True,
        },
    )
    mock_send_email

    response = client.post(
        "/auth/change-email",
        json={
            "password": VALID_USER_DATA["password"],
            "email": "testuser2@outlook.com",
        },
        headers=auth_header,
    )

    assert response.status_code == 200
    assert (
        response.json["msg"] == f"Email del usuario actualizado de forma satisfactoria"
    )
    mock_db_get_user_by_user_id_without_id.assert_called_once()
    mock_db_update_user.assert_called_once()
    mock_send_email.assert_called_once()


def test_change_email_auth_provider_google_success(
    client,
    auth_header,
    mock_get_jwt,
    mock_send_email,
    mock_db_get_user_by_user_id_without_id,
    mock_db_update_user,
):
    mock_get_jwt.return_value = {"role": 3, "sub": ID}
    mock_db_get_user_by_user_id_without_id.return_value = {
        **VALID_USER_DATA,
        "auth_provider": "google",
        "confirmed": True,
    }
    mock_db_update_user.return_value = {
        **VALID_USER_DATA,
        "email": "testuser2@outlook.com",
        "auth_provider": "email",
        "confirmed": False,
    }
    mock_send_email

    response = client.post(
        "/auth/change-email",
        json={
            "email": "testuser2@outlook.com",
            "password": VALID_USER_DATA["password"],
        },
        headers=auth_header,
    )

    assert response.status_code == 200
    assert (
        response.json["msg"] == "Email del usuario actualizado de forma satisfactoria"
    )
    mock_db_get_user_by_user_id_without_id.assert_called_once()
    mock_db_update_user.assert_called_once()
    mock_send_email.assert_called_once()


def test_change_email_without_password_error(
    client, auth_header, mock_get_jwt, mock_db_get_user_by_user_id_without_id
):
    mock_get_jwt.return_value({"role": 3, "sub": ID})
    mock_db_get_user_by_user_id_without_id.return_value = {
        **VALID_USER_DATA,
        "auth_provider": "google",
    }

    response = client.post(
        "/auth/change-email",
        json={"email": "testuser2@outlook.com"},
        headers=auth_header,
    )

    assert response.status_code == 400
    assert response.json["err"] == "resource_required"
    mock_db_get_user_by_user_id_without_id.assert_called_once()


def test_login_success(
    client,
    mock_db_get_user_by_email,
    mock_generate_access_token,
    mock_generate_refresh_token,
    mock_verify_password,
):
    mock_db_get_user_by_email.return_value = {
        **VALID_USER_DATA,
        "_id": ID,
        "confirmed": True,
    }

    mock_verify_password.return_value = True
    mock_generate_access_token.return_value = "access_token"
    mock_generate_refresh_token.return_value = "refresh_token"

    response = client.post("/auth/login", json=VALID_USER_DATA)

    assert response.status_code == 200
    assert (
        response.json["msg"]
        == f"Usuario ha iniciado sesión manualmente de forma satisfactoria"
    )
    assert response.json["access_token"] == "access_token"
    assert response.json["refresh_token"] == "refresh_token"
    mock_db_get_user_by_email.assert_called_once()
    mock_verify_password.assert_called_once()
    mock_generate_access_token.assert_called_once()
    mock_generate_refresh_token.assert_called_once()


def test_login_password_not_match_error(
    client, mock_db_get_user_by_email, mock_verify_password
):
    mock_db_get_user_by_email.return_value = INVALID_USER_DATA
    mock_verify_password.return_value = False

    response = client.post("/auth/login", json=INVALID_USER_DATA)

    assert response.status_code == 401
    assert response.json["err"] == "password_not_match"
    mock_db_get_user_by_email.assert_called_once()
    mock_verify_password.assert_called_once()


def test_login_user_not_confirmed_error(
    client, mock_db_get_user_by_email, mock_verify_password
):
    mock_db_get_user_by_email.return_value = {**INVALID_USER_DATA, "confirmed": False}
    mock_verify_password.return_value = True

    response = client.post("/auth/login", json=INVALID_USER_DATA)

    assert response.status_code == 401
    assert response.json["err"] == "email_not_confirmed"
    mock_db_get_user_by_email.assert_called_once()
    mock_verify_password.assert_called_once()


def test_login_db_error(
    client,
    mock_db_get_user_by_email,
    mock_verify_password,
    mock_generate_access_token,
):
    mock_db_get_user_by_email.return_value = {**VALID_USER_DATA, "confirmed": True}
    mock_verify_password.return_value = True
    mock_generate_access_token.side_effect = PyMongoError("Database error")

    response = client.post(
        "/auth/login",
        json={
            "email": VALID_USER_DATA["email"],
            "password": VALID_USER_DATA["password"],
        },
    )

    assert response.status_code == 500
    assert response.json["err"] == "db_generic"
    mock_db_get_user_by_email.assert_called_once()
    mock_verify_password.assert_called_once()
    mock_generate_access_token.assert_called_once()


def test_logout_success(client, auth_header, mock_get_jwt, mocker):
    mock_get_jwt.return_value = {"sub": ID}
    mock_delete_active_token = mocker.patch("src.routes.auth_route.delete_active_token")
    mock_delete_refresh_token = mocker.patch(
        "src.routes.auth_route.delete_refresh_token"
    )

    response = client.post("/auth/logout", headers=auth_header)

    assert response.status_code == 200
    assert response.json["msg"] == "Logout del usuario realizado de forma satisfactoria"
    mock_delete_active_token.assert_called_once()
    mock_delete_refresh_token.assert_called_once()


def test_login_google_success(client, mocker):
    mock_google_redirect = mocker.patch(
        "src.routes.auth_route.google.authorize_redirect",
        side_effect=lambda uri: Response(status=302, headers={"Location": uri}),
    )

    response = client.get("/auth/login/google")

    assert response.status_code == 302
    assert response.headers["Location"] == "http://localhost/auth/callback/google"
    mock_google_redirect.assert_called_once()


def test_callback_google_success(
    client,
    mock_google_access,
    mock_google_parse,
    insert_or_update_call_db,
    mock_generate_access_token,
    mock_generate_refresh_token,
):
    mock_google_access
    mock_google_parse
    insert_or_update_call_db

    mock_generate_access_token.return_value = "access_token"
    mock_generate_refresh_token.return_value = "refresh_token"

    response = client.get("/auth/callback/google")

    assert response.status_code == 200
    assert (
        response.json["msg"]
        == "El usuario ha iniciado sesión con Google de forma satisfactoria"
    )
    assert response.json["access_token"] == "access_token"
    assert response.json["refresh_token"] == "refresh_token"
    mock_google_access.assert_called_once()
    mock_google_parse.assert_called_once()
    insert_or_update_call_db.assert_called_once()
    mock_generate_refresh_token.assert_called_once()
    mock_generate_access_token.assert_called_once()


def test_callback_google_db_error(
    client,
    mock_get_jwt,
    mock_google_parse,
    mock_google_access,
    insert_or_update_call_db,
    mock_generate_access_token,
):
    mock_google_access
    mock_google_parse
    insert_or_update_call_db
    mock_generate_access_token.side_effect = PyMongoError("Database error")

    response = client.get("/auth/callback/google")

    assert response.status_code == 500
    assert response.json["err"] == "db_generic"
    mock_google_access.assert_called_once()
    mock_google_parse.assert_called_once()
    insert_or_update_call_db.assert_called_once()
    mock_generate_access_token.assert_called_once()


def test_refresh_token_success(
    client,
    auth_header_refresh,
    mock_get_jwt,
    mock_generate_access_token,
    mock_db_get_user_by_user_id,
    mock_db_get_refresh_token_by_user_id,
):
    mock_get_jwt.return_value({"sub": ID})
    mock_db_get_refresh_token_by_user_id.return_value = VALID_TOKEN_DATA
    mock_db_get_user_by_user_id.return_value = VALID_USER_DATA
    mock_generate_access_token.return_value = "access_token"

    response = client.get("/auth/refresh-token", headers=auth_header_refresh)

    assert response.status_code == 200
    assert response.json["msg"] == "Token de acceso generado de forma satisfactoria"
    assert response.json["access_token"] == "access_token"
    mock_db_get_refresh_token_by_user_id.assert_called_once()
    mock_db_get_user_by_user_id.assert_called_once()
    mock_generate_access_token.assert_called_once()


def test_refresh_token_error(
    client, auth_header_refresh, mock_get_jwt, mock_db_get_refresh_token_by_user_id
):
    mock_get_jwt.return_value({"role": 3, "sub": ID})
    mock_db_get_refresh_token_by_user_id.return_value = None

    response = client.get("/auth/refresh-token", headers=auth_header_refresh)

    assert response.status_code == 404
    assert response.json["err"] == "not_found"
    mock_db_get_refresh_token_by_user_id.assert_called_once()


def test_confirm_email_success(
    client,
    mock_db_get_user_by_user_id_without_id,
    mock_db_update_user,
    mock_decode_token,
):
    mock_decode_token.return_value = {"sub": ID}
    mock_db_get_user_by_user_id_without_id.return_value = {
        **VALID_USER_DATA,
        "auth_provider": "email",
        "confirmed": False,
    }
    mock_db_update_user.return_value = {
        **VALID_USER_DATA,
        "auth_provider": "email",
        "confirmed": True,
    }

    response = client.get("/auth/confirm-email/test_token")

    assert response.status_code == 200
    assert response.json["msg"] == "Usuario confirmado de forma satisfactoria"
    mock_decode_token.assert_called_once()
    mock_db_get_user_by_user_id_without_id.assert_called_once()
    mock_db_update_user.assert_called_once()


def test_confirm_email_invalid_token_error(client, mock_decode_token):
    mock_decode_token.side_effect = Exception("Invalid token")

    response = client.get("/auth/confirm-email/test_token")

    assert response.status_code == 500
    assert response.json["err"] == "unexpected"
    mock_decode_token.assert_called_once()


def test_confirm_email_already_confirmed_error(
    client, mock_db_get_user_by_user_id_without_id, mock_decode_token
):
    mock_decode_token.return_value = {"sub": ID}
    mock_db_get_user_by_user_id_without_id.return_value = {
        **VALID_USER_DATA,
        "auth_provider": "email",
        "confirmed": True,
    }

    response = client.get("/auth/confirm-email/test_token")

    assert response.status_code == 401
    assert response.json["err"] == "email_already_confirmed"
    mock_decode_token.assert_called_once()
    mock_db_get_user_by_user_id_without_id.assert_called_once()


def test_confirm_email_mongodb_error(
    mock_db_update_user,
    client,
    mock_db_get_user_by_user_id_without_id,
    mock_decode_token,
):
    mock_decode_token.return_value = {"sub": ID}
    mock_db_get_user_by_user_id_without_id.return_value = {
        **VALID_USER_DATA,
        "auth_provider": "email",
        "confirmed": False,
    }
    mock_db_update_user.side_effect = PyMongoError("Database error")

    response = client.get("/auth/confirm-email/test_token")

    assert response.status_code == 500
    assert response.json["err"] == "db_generic"
    mock_decode_token.assert_called_once()
    mock_db_get_user_by_user_id_without_id.assert_called_once()
    mock_db_update_user.assert_called_once()


def test_resend_email_success(
    client, mock_db_get_user_by_email, mock_send_email, mock_db_get_email_tokens
):
    mock_db_get_user_by_email.return_value = {**VALID_USER_DATA, "_id": ID}
    mock_db_get_email_tokens
    mock_send_email

    response = client.post(
        f"/auth/resend-email", json={"email": VALID_USER_DATA["email"]}
    )

    assert response.status_code == 200
    assert (
        response.json["msg"] == "Email de confirmación reenviado de forma satisfactoria"
    )
    mock_db_get_email_tokens.assert_called_once()
    mock_db_get_user_by_email.assert_called_once()
    mock_send_email.assert_called_once()


def test_resend_email_too_many_requests_error(
    client, mock_db_get_email_tokens, mock_db_get_user_by_email
):
    mock_db_get_user_by_email.return_value = {**VALID_USER_DATA, "_id": ID}
    mock_db_get_email_tokens.return_value = mock_db_get_email_tokens.return_value * 5

    response = client.post(
        f"/auth/resend-email", json={"email": VALID_USER_DATA["email"]}
    )

    assert response.status_code == 429
    assert response.json["err"] == "too_many_requests"
    mock_db_get_email_tokens.assert_called_once()


def test_resend_email_resource_required_error(client):
    response = client.post("/auth/resend-email", json={})

    assert response.status_code == 400
    assert response.json["err"] == "resource_required"
