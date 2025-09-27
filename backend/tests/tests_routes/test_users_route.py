import pytest
import json

from src.models.user_model import UserModel
from tests.test_helpers import app, client, auth_header

VALID_USER_DATA = {
    "name": "John Doe",
    "email": "john.doe@hotmail.com",
    "password": "ValidPass123!",
}
ID = "507f1f77bcf86cd799439011"


@pytest.fixture
def mock_get_jwt(mocker):
    return mocker.patch("src.routes.users_route.get_jwt")


@pytest.fixture
def mock_get_user(mocker):
    return mocker.patch.object(UserModel, "get_user_by_user_id_without_id")


@pytest.fixture
def mock_delete_user(mocker):
    return mocker.patch.object(UserModel, "delete_user")


@pytest.mark.parametrize(
    "url, method",
    [
        ("/users/", "post"),
        ("/users/", "get"),
        ("/users/507f1f77bcf86cd799439012", "get"),
        ("/users/507f1f77bcf86cd799439012", "delete"),
        ("/users/507f1f77bcf86cd799439012", "put"),
    ],
)
def test_token_not_authorized_error(mock_get_jwt, client, auth_header, url, method):
    mock_get_jwt.return_value = {"role": 3, "sub": ID}

    if method == "post":
        response = client.post(url, json=VALID_USER_DATA, headers=auth_header)
    elif method == "get":
        response = client.get(url, headers=auth_header)
    elif method == "delete":
        response = client.delete(url, headers=auth_header)
    elif method == "put":
        response = client.put(url, json=VALID_USER_DATA, headers=auth_header)

    assert response.status_code == 403
    assert response.json["err"] == "not_auth"
    mock_get_jwt.assert_called_once()


@pytest.mark.parametrize(
    "url, method",
    [
        ("/users/507f1f77bcf86cd799439011", "get"),
        ("/users/507f1f77bcf86cd799439011", "delete"),
        ("/users/507f1f77bcf86cd799439011", "put"),
    ],
)
def test_user_not_found_error(
    mocker,
    mock_get_jwt,
    mock_get_user,
    mock_delete_user,
    client,
    auth_header,
    url,
    method,
):
    mock_get_jwt.return_value = {"role": 0, "sub": ID}

    if method in ["get", "put"]:
        mock_get_user.return_value = None
    else:
        mock_delete_user.return_value = mocker.MagicMock(deleted_count=0)

    if method == "get":
        response = client.get(url, headers=auth_header)
    elif method == "put":
        response = client.put(url, json=VALID_USER_DATA, headers=auth_header)
    elif method == "delete":
        response = client.delete(url, headers=auth_header)

    assert response.status_code == 404
    assert response.json["err"] == "not_found"
    mock_get_jwt.assert_called_once()
    (
        mock_get_user.assert_called_once()
        if method != "delete"
        else mock_delete_user.assert_called_once()
    )


@pytest.mark.parametrize(
    "url, method", [("/users/507f1f77bcf86cd799439011", "put"), ("/users/", "post")]
)
def test_not_authorized_to_set_error(
    mock_get_jwt, mock_get_user, client, auth_header, url, method
):
    mock_get_jwt.return_value = {"role": 1, "sub": ID}
    if method == "post":
        response = client.post(
            url,
            json={**VALID_USER_DATA, "auth_provider": "google"},
            headers=auth_header,
        )
    elif method == "put":
        mock_get_user.return_value = {**VALID_USER_DATA, "confirmed": False}
        response = client.put(
            url,
            json={**VALID_USER_DATA, "confirmed": True},
            headers=auth_header,
        )

    assert response.status_code == 403
    assert response.json["err"] == "not_auth_set"
    mock_get_jwt.assert_called_once()
    mock_get_user.assert_called_once() if method == "put" else None


def test_add_user_success(mocker, client, mock_get_jwt, auth_header):
    mock_get_jwt.return_value = {"role": 1}
    mock_db = mocker.patch.object(
        UserModel, "insert_user", return_value=mocker.MagicMock(inserted_id=ID)
    )

    response = client.post("/users/", json=VALID_USER_DATA, headers=auth_header)

    assert response.status_code == 201
    assert response.json["msg"] == f"Usuario añadido de forma satisfactoria"
    mock_get_jwt.assert_called_once()
    mock_db.assert_called_once()


def test_get_users_success(mocker, client, auth_header, mock_get_jwt):
    mock_get_jwt.return_value = {"role": 1}
    mock_db = mocker.patch.object(
        UserModel, "get_users", return_value=[VALID_USER_DATA]
    )

    response = client.get("/users/", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == [VALID_USER_DATA]
    mock_get_jwt.assert_called_once()
    mock_db.assert_called_once()


def test_get_user_success(mock_get_user, client, auth_header, mock_get_jwt):
    mock_get_jwt.return_value = {"role": 0, "sub": ID}
    mock_get_user.return_value = VALID_USER_DATA

    response = client.get(f"/users/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == VALID_USER_DATA
    mock_get_jwt.assert_called_once()
    mock_get_user.assert_called_once()


def test_update_user_success(mocker, mock_get_user, client, auth_header, mock_get_jwt):
    mock_get_jwt.return_value = {
        "role": 1,
        "sub": ID,
        "jti": "bb53e637-8627-457c-840f-6cae52a12e8b",
    }
    mock_get_user.return_value = VALID_USER_DATA
    mock_update_user = mocker.patch.object(
        UserModel,
        "update_user",
        return_value={**VALID_USER_DATA, "role": 0},
    )

    response = client.put(f"/users/{ID}", json={"role": 0}, headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == {
        **VALID_USER_DATA,
        "role": 0,
    }
    mock_get_jwt.assert_called_once()
    mock_get_user.assert_called_once()
    mock_update_user.assert_called_once()


def test_delete_user_success(
    mocker, mock_delete_user, client, auth_header, mock_get_jwt
):
    mock_get_jwt.return_value = {"role": 0, "sub": ID}
    mock_delete_user.return_value = mocker.MagicMock(deleted_count=1)
    mock_revoke_access_token = mocker.patch(
        "src.routes.users_route.delete_active_token"
    )
    mock_delete_refresh_token = mocker.patch(
        "src.routes.users_route.delete_refresh_token"
    )

    response = client.delete(f"/users/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert response.json["msg"] == f"Usuario eliminado de forma satisfactoria"
    mock_get_jwt.assert_called_once()
    mock_delete_user.assert_called_once()
    mock_revoke_access_token.assert_called_once()
    mock_delete_refresh_token.assert_called_once()
