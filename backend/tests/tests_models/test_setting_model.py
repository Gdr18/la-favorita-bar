import pytest
from pydantic import ValidationError
from datetime import datetime

from src.models.setting_model import SettingModel
from tests.test_helpers import (
    assert_insert_document_template,
    assert_get_all_documents_template,
    assert_get_document_template,
    assert_update_document_template,
    assert_delete_document_template,
)

ID = "507f1f77bcf86cd799439011"
VALID_DATA_LIST = {"name": "TestSetting", "value": ["value1", "value2"]}
VALID_DATA_BOOL = {"name": "TestSetting", "value": True}


@pytest.fixture
def mock_db(mocker):
    mock_db = mocker.MagicMock()
    mocker.patch("src.services.db_service.db.settings", new=mock_db)
    return mock_db


@pytest.mark.parametrize(
    "data",
    [
        VALID_DATA_LIST,
        VALID_DATA_BOOL,
    ],
)
def test_setting_valid(data):
    setting = SettingModel(**data)
    assert isinstance(setting.name, str) and 0 < len(setting.name) < 51
    assert isinstance(setting.value, list) or isinstance(setting.value, bool)
    if isinstance(setting.value, list):
        for item in setting.value:
            assert isinstance(item, str) and len(item) > 0
    assert isinstance(setting.updated_at, datetime)


@pytest.mark.parametrize(
    "name, value",
    [
        ("", VALID_DATA_LIST["value"]),
        ("a" * 51, VALID_DATA_LIST["value"]),
        (VALID_DATA_LIST["name"], "not_a_list"),
        (VALID_DATA_LIST["name"], [1, 2, 3]),
        (VALID_DATA_LIST["name"], ["", "", ""]),
        (VALID_DATA_LIST["name"], []),
    ],
)
def test_setting_validation_error(name, value):
    with pytest.raises(ValidationError):
        SettingModel(name=name, value=value)


def test_insert_setting(mock_db):
    return assert_insert_document_template(
        mock_db, SettingModel(**VALID_DATA_LIST).insert_setting
    )


def test_get_settings(mock_db):
    return assert_get_all_documents_template(
        mock_db, SettingModel.get_settings, [VALID_DATA_LIST]
    )


@pytest.mark.parametrize(
    "function",
    [
        SettingModel.get_setting,
        SettingModel.get_setting_by_name,
    ],
)
def test_get_setting(mock_db, function):
    return assert_get_document_template(mock_db, function, VALID_DATA_LIST)


def test_update_setting(mock_db):
    new_data = {**VALID_DATA_LIST, "name": "TestSetting2"}
    setting_object = SettingModel(**new_data)
    return assert_update_document_template(
        mock_db,
        setting_object.update_setting,
        new_data,
    )


def test_delete_setting(mock_db):
    return assert_delete_document_template(mock_db, SettingModel.delete_setting)
