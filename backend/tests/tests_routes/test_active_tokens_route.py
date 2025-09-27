import pytest
import json

from tests.test_helpers import app, client, auth_header
from src.models.token_model import TokenModel


ID = "507f1f77bcf86cd799439011"
VALID_ACTIVE_TOKEN_DATA = {
    "user_id": ID,
    "jti": "bb53e637-8627-457c-840f-6cae52a12e8b",
    "expires_at": "2025-10-01T00:00:00Z",
}


@pytest.fixture
def mock_get_jwt(mocker):
    return mocker.patch("src.routes.active_tokens_route.get_jwt")


@pytest.fixture
def mock_get_active_token(mocker):
    return mocker.patch.object(TokenModel, "get_active_token_by_token_id")


@pytest.fixture
def mock_delete_active_token(mocker):
    return mocker.patch.object(TokenModel, "delete_active_token_by_token_id")


@pytest.mark.parametrize(
    "url, method",
    [
        ("/active-tokens/", "post"),
        ("/active-tokens/", "get"),
        ("/active-tokens/507f1f77bcf86cd799439011", "delete"),
        ("/active-tokens/507f1f77bcf86cd799439011", "put"),
        ("/active-tokens/507f1f77bcf86cd799439011", "get"),
    ],
)
def test_token_not_authorized_error(mock_get_jwt, client, auth_header, url, method):
    mock_get_jwt.return_value = {"role": 1}

    if method == "post":
        response = client.post(url, json=VALID_ACTIVE_TOKEN_DATA, headers=auth_header)
    elif method == "get":
        response = client.get(url, headers=auth_header)
    elif method == "delete":
        response = client.delete(url, headers=auth_header)
    elif method == "put":
        response = client.put(url, json=VALID_ACTIVE_TOKEN_DATA, headers=auth_header)

    assert response.status_code == 403
    assert response.json["err"] == "not_auth"
    mock_get_jwt.assert_called_once()


@pytest.mark.parametrize(
    "url, method",
    [("/active-tokens/", "post"), ("/active-tokens/507f1f77bcf86cd799439011", "put")],
)
def test_not_authorized_to_set_error(
    client, auth_header, mock_get_jwt, mock_get_active_token, url, method
):
    mock_get_jwt.return_value = {"role": 0}

    if method == "post":
        response = client.post(
            url,
            json={**VALID_ACTIVE_TOKEN_DATA, "created_at": "2030-10-01T00:00:00Z"},
            headers=auth_header,
        )
    elif method == "put":
        mock_get_active_token.return_value = {
            **VALID_ACTIVE_TOKEN_DATA,
            "created_at": "2031-10-01T00:00:00Z",
        }
        response = client.put(
            url,
            json={**VALID_ACTIVE_TOKEN_DATA, "created_at": "2030-10-01T00:00:00Z"},
            headers=auth_header,
        )
    assert response.status_code == 403
    assert response.json["err"] == "not_auth_set"
    mock_get_jwt.assert_called_once()
    mock_get_active_token.assert_called_once() if method == "put" else None


@pytest.mark.parametrize(
    "url, method",
    [
        ("/active-tokens/507f1f77bcf86cd799439011", "get"),
        ("/active-tokens/507f1f77bcf86cd799439011", "delete"),
        ("/active-tokens/507f1f77bcf86cd799439011", "put"),
    ],
)
def test_active_token_not_found_error(
    mocker,
    client,
    auth_header,
    mock_get_jwt,
    mock_get_active_token,
    mock_delete_active_token,
    url,
    method,
):
    mock_get_jwt.return_value = {"role": 0}

    if method in ["get", "put"]:
        mock_get_active_token.return_value = None
    else:
        mock_delete_active_token.return_value = mocker.MagicMock(deleted_count=0)

    if method == "get":
        response = client.get(url, headers=auth_header)
    elif method == "delete":
        response = client.delete(url, headers=auth_header)
    elif method == "put":
        response = client.put(url, json=VALID_ACTIVE_TOKEN_DATA, headers=auth_header)

    assert response.status_code == 404
    assert response.json["err"] == "not_found"
    mock_get_jwt.assert_called_once()
    (
        mock_get_active_token.assert_called_once()
        if method != "delete"
        else mock_delete_active_token.assert_called_once()
    )


def test_add_active_token_success(mocker, client, mock_get_jwt, auth_header):
    mock_get_jwt.return_value = {"role": 0}
    mock_db = mocker.patch.object(
        TokenModel,
        "insert_active_token",
        return_value=mocker.MagicMock(inserted_id=ID),
    )

    response = client.post(
        "/active-tokens/", json=VALID_ACTIVE_TOKEN_DATA, headers=auth_header
    )

    assert response.status_code == 201
    assert response.json["msg"] == "Token activo añadido de forma satisfactoria"
    mock_get_jwt.assert_called_once()
    mock_db.assert_called_once()


def test_get_active_tokens_success(mocker, mock_get_jwt, client, auth_header):
    mock_get_jwt.return_value = {"role": 0}
    mock_db = mocker.patch.object(
        TokenModel, "get_active_tokens", return_value=[VALID_ACTIVE_TOKEN_DATA]
    )

    response = client.get("/active-tokens/", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == [VALID_ACTIVE_TOKEN_DATA]
    mock_get_jwt.assert_called_once()
    mock_db.assert_called_once()


def test_get_active_token_success(
    client, auth_header, mock_get_jwt, mock_get_active_token
):
    mock_get_jwt.return_value = {"role": 0}
    mock_get_active_token.return_value = VALID_ACTIVE_TOKEN_DATA

    response = client.get(f"/active-tokens/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == VALID_ACTIVE_TOKEN_DATA
    mock_get_jwt.assert_called_once()
    mock_get_active_token.assert_called_once()


def test_update_active_token_success(
    mocker, mock_get_jwt, mock_get_active_token, client, auth_header
):
    mock_get_jwt.return_value = {"role": 0}
    mock_get_active_token.return_value = VALID_ACTIVE_TOKEN_DATA
    mocker.patch.object(
        TokenModel,
        "update_active_token",
        return_value={**VALID_ACTIVE_TOKEN_DATA, "expires_at": "2025-10-01T00:00:00Z"},
    )

    response = client.put(
        f"/active-tokens/{ID}",
        json={"expires_at": "2025-10-01T00:00:00Z"},
        headers=auth_header,
    )

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == {
        **VALID_ACTIVE_TOKEN_DATA,
        "expires_at": "2025-10-01T00:00:00Z",
    }
    mock_get_jwt.assert_called_once()
    mock_get_active_token.assert_called_once()


def test_delete_active_token_success(
    mocker, client, auth_header, mock_get_jwt, mock_delete_active_token
):
    mock_get_jwt.return_value = {"role": 0}
    mock_delete_active_token.return_value = mocker.MagicMock(deleted_count=1)

    response = client.delete(f"/active-tokens/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert response.json["msg"] == "Token activo eliminado de forma satisfactoria"
    mock_get_jwt.assert_called_once()
    mock_delete_active_token.assert_called_once()
