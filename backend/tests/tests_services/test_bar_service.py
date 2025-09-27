import pytest
from datetime import datetime

from src.services.bar_service import check_manual_closure, check_schedule_bar
from src.models.setting_model import SettingModel


@pytest.mark.parametrize(
    "mocked_datetime, expected_result",
    [
        (datetime(2025, 5, 10, 13, 30), True),
        (datetime(2025, 5, 10, 16, 30), False),
        (datetime(2025, 5, 10, 21, 0), True),
        (datetime(2025, 5, 11, 1, 0), False),
        (datetime(2025, 5, 12, 14, 0), False),
    ],
)
def test_check_schedule_bar(mocker, mocked_datetime, expected_result):
    mocker.patch("src.services.bar_service.datetime", autospec=True)
    mocker_datetime = mocker.MagicMock()
    mocker_datetime.now.return_value = mocked_datetime
    mocker_datetime.time.return_value = mocked_datetime.time()
    mocker_datetime.strftime.return_value = mocked_datetime.strftime("%A").lower()
    mocker.patch("src.services.bar_service.datetime", mocker_datetime)

    result = check_schedule_bar()

    assert result == expected_result


@pytest.mark.parametrize(
    "closing_time, mocked_datetime, manual_closure_value, expected_result",
    [
        (
            datetime(2025, 5, 9, 23, 30),
            datetime(2025, 5, 10, 13, 30),
            True,
            True,
        ),
        (datetime(2025, 5, 10, 15, 0), datetime(2025, 5, 10, 15, 30), True, False),
        (
            datetime(2025, 5, 10, 15, 0),
            datetime(2025, 5, 10, 21, 0),
            True,
            True,
        ),
        (datetime(2025, 5, 11, 23, 0), datetime(2025, 5, 11, 23, 30), True, False),
        (datetime(2025, 5, 11, 23, 0), datetime(2025, 5, 12, 14, 0), False, True),
    ],
)
def test_check_manual_closure(
    mocker, closing_time, mocked_datetime, manual_closure_value, expected_result
):
    mock_get = mocker.patch.object(
        SettingModel,
        "get_setting_by_name",
        return_value={
            "value": manual_closure_value,
            "updated_at": closing_time.isoformat(),
            "_id": "some_id",
        },
    )

    mock_update = mocker.patch.object(SettingModel, "update_setting")

    mocker.patch("src.services.bar_service.datetime", wraps=datetime)
    mocker.patch("src.services.bar_service.datetime.now", return_value=mocked_datetime)

    result = check_manual_closure()

    assert result == expected_result
    mock_get.assert_called_once()

    if expected_result and manual_closure_value:
        mock_update.assert_called_once()
