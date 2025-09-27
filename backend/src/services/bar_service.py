from datetime import datetime, time

from src.models.setting_model import SettingModel

OPEN_LUNCH = time(13, 0, 0)
CLOSE_LUNCH = time(15, 59, 59)
OPEN_DINNER = time(20, 0, 0)
CLOSE_DINNER = time(23, 59, 59)


def check_schedule_bar():
    now = datetime.now()
    now_time = now.time()
    day_of_week = now.strftime("%A").lower()

    if (
        OPEN_LUNCH <= now_time <= CLOSE_LUNCH or OPEN_DINNER <= now_time <= CLOSE_DINNER
    ) and day_of_week != "monday":
        return True

    return False


def check_manual_closure():
    manual_closure = SettingModel.get_setting_by_name("manual_closure")

    if manual_closure["value"]:
        closing_time = datetime.fromisoformat(manual_closure["updated_at"]).time()
        now_time = datetime.now().time()

        close_in_lunch_time = OPEN_LUNCH <= closing_time <= CLOSE_LUNCH
        close_in_dinner_time = OPEN_DINNER <= closing_time <= CLOSE_DINNER

        in_lunch_time = OPEN_LUNCH <= now_time <= CLOSE_LUNCH
        in_dinner_time = OPEN_DINNER <= now_time <= CLOSE_DINNER

        if (close_in_lunch_time and in_dinner_time) or (
            close_in_dinner_time and in_lunch_time
        ):
            SettingModel(value=False, name="manual_closure").update_setting(
                manual_closure["_id"]
            )
            return True
        return False

    return True
