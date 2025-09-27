import pytest
import json

from src.models.setting_model import SettingModel
from tests.test_helpers import app, client, auth_header

ID = "507f1f77bcf86cd799439011"
VALID_SETTING_DATA = {"name": "test", "value": ["value1", "value2"]}


@pytest.fixture
def mock_get_jwt(mocker):
    return mocker.patch("src.routes.settings_route.get_jwt")


@pytest.fixture
def mock_get_setting(mocker):
    return mocker.patch.object(SettingModel, "get_setting")


@pytest.fixture
def mock_delete_setting(mocker):
    return mocker.patch.object(SettingModel, "delete_setting")


@pytest.mark.parametrize(
    "url, method",
    [
        ("/settings/", "post"),
        ("/settings/", "get"),
        ("/settings/507f1f77bcf86cd799439011", "delete"),
        ("/settings/507f1f77bcf86cd799439011", "put"),
        ("/settings/507f1f77bcf86cd799439011", "get"),
    ],
)
def test_token_not_authorized_error(mock_get_jwt, client, auth_header, url, method):
    mock_get_jwt.return_value = {"role": 3}

    if method == "post":
        response = client.post(url, json=VALID_SETTING_DATA, headers=auth_header)
    elif method == "get" or method == "delete":
        response = client.get(url, headers=auth_header)
    elif method == "delete":
        response = client.delete(url, headers=auth_header)
    elif method == "put":
        response = client.put(url, json=VALID_SETTING_DATA, headers=auth_header)

    assert response.status_code == 403
    assert response.json["err"] == "not_auth"
    mock_get_jwt.assert_called_once()


def test_not_authorized_to_set(mock_get_jwt, client, auth_header):
    mock_get_jwt.return_value = {"role": 1}

    response = client.post(
        "/settings/",
        json={**VALID_SETTING_DATA, "updated_at": "2023-10-01T00:00:00Z"},
        headers=auth_header,
    )

    assert response.status_code == 403
    assert response.json["err"] == "not_auth_set"
    mock_get_jwt.assert_called_once()


@pytest.mark.parametrize(
    "url, method",
    [
        ("/settings/507f1f77bcf86cd799439011", "get"),
        ("/settings/507f1f77bcf86cd799439011", "delete"),
        ("/settings/507f1f77bcf86cd799439011", "put"),
    ],
)
def test_setting_not_found_error(
    mocker,
    mock_get_jwt,
    mock_get_setting,
    mock_delete_setting,
    client,
    auth_header,
    url,
    method,
):
    mock_get_jwt.return_value = {"role": 1}

    if method in ["get", "put"]:
        mock_get_setting.return_value = None
    else:
        mock_delete_setting.return_value = mocker.MagicMock(deleted_count=0)

    if method == "get":
        response = client.get(url, headers=auth_header)
    elif method == "delete":
        response = client.delete(url, headers=auth_header)
    elif method == "put":
        response = client.put(url, json=VALID_SETTING_DATA, headers=auth_header)

    assert response.status_code == 404
    assert response.json["err"] == "not_found"
    mock_get_jwt.assert_called_once()
    (
        mock_get_setting.assert_called_once()
        if method != "delete"
        else mock_delete_setting.assert_called_once()
    )


def test_add_setting_success(mock_get_jwt, mocker, client, auth_header):
    mock_get_jwt.return_value = {"role": 1}
    mock_db = mocker.patch.object(
        SettingModel,
        "insert_setting",
        return_value=mocker.MagicMock(inserted_id=ID),
    )

    response = client.post("/settings/", json=VALID_SETTING_DATA, headers=auth_header)

    assert response.status_code == 201
    assert response.json["msg"] == f"Configuración añadida de forma satisfactoria"
    mock_get_jwt.assert_called_once()
    mock_db.assert_called_once()


def test_get_settings_success(mocker, client, auth_header, mock_get_jwt):
    mock_get_jwt.return_value = {"role": 0}
    mock_db = mocker.patch.object(
        SettingModel, "get_settings", return_value=[VALID_SETTING_DATA]
    )

    response = client.get("/settings/", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == [VALID_SETTING_DATA]
    mock_get_jwt.assert_called_once()
    mock_db.assert_called_once()


def test_get_setting_success(client, auth_header, mock_get_jwt, mock_get_setting):
    mock_get_jwt.return_value = {"role": 1}
    mock_get_setting.return_value = VALID_SETTING_DATA

    response = client.get(f"/settings/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == VALID_SETTING_DATA
    mock_get_jwt.assert_called_once()
    mock_get_setting.assert_called_once()


def test_update_setting_success(
    mocker, client, auth_header, mock_get_jwt, mock_get_setting
):
    mock_get_jwt.return_value = {"role": 1}
    mock_get_setting.return_value = VALID_SETTING_DATA
    mock_update_setting = mocker.patch.object(
        SettingModel,
        "update_setting",
        return_value={**VALID_SETTING_DATA, "name": "new_value"},
    )

    response = client.put(
        f"/settings/{ID}", json={"name": "new_value"}, headers=auth_header
    )

    assert response.status_code == 200
    assert json.loads(response.data.decode()) == {
        **VALID_SETTING_DATA,
        "name": "new_value",
    }
    mock_get_jwt.assert_called_once()
    mock_get_setting.assert_called_once()
    mock_update_setting.assert_called_once()


def test_delete_setting_success(
    mocker, client, auth_header, mock_get_jwt, mock_delete_setting
):
    mock_get_jwt.return_value = {"role": 1}
    mock_delete_setting.return_value = mocker.MagicMock(deleted_count=1)

    response = client.delete(f"/settings/{ID}", headers=auth_header)

    assert response.status_code == 200
    assert response.json["msg"] == f"Configuración eliminada de forma satisfactoria"
    mock_get_jwt.assert_called_once()
    mock_delete_setting.assert_called_once()
