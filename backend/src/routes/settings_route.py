from flask import Blueprint, request, Response
from flask_jwt_extended import jwt_required, get_jwt

from src.models.setting_model import SettingModel
from src.utils.exception_handlers import ValueCustomError
from src.utils.json_responses import success_json_response, db_json_response

SETTINGS_RESOURCE = "configuración"

settings_route = Blueprint("settings", __name__)


@settings_route.route("/", methods=["POST"])
@jwt_required()
def add_setting() -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    if token_role > 1:
        raise ValueCustomError("not_auth")
    setting_data = request.get_json()
    if setting_data.get("updated_at"):
        raise ValueCustomError("not_auth_set", "updated_at")
    setting_object = SettingModel(**setting_data)
    setting_object.insert_setting()
    return success_json_response(SETTINGS_RESOURCE, "añadida", 201)


@settings_route.route("/", methods=["GET"])
@jwt_required()
def get_settings() -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    if token_role > 1:
        raise ValueCustomError("not_auth")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per-page", 10))
    skip = (page - 1) * per_page
    settings = SettingModel.get_settings(skip, per_page)
    return db_json_response(settings)


@settings_route.route("/<setting_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_setting(setting_id: str) -> tuple[Response, int]:
    token = get_jwt()
    token_role = token.get("role")
    if token_role > 1:
        raise ValueCustomError("not_auth")

    if request.method == "GET":
        setting = SettingModel.get_setting(setting_id)
        if not setting:
            raise ValueCustomError("not_found", SETTINGS_RESOURCE)
        return db_json_response(setting)

    if request.method == "PUT":
        setting = SettingModel.get_setting(setting_id)
        if not setting:
            raise ValueCustomError("not_found", SETTINGS_RESOURCE)
        setting_new_data = request.get_json()
        mixed_data = {**setting, **setting_new_data}
        mixed_data.pop("updated_at", None)
        setting_object = SettingModel(**mixed_data)
        updated_setting = setting_object.update_setting(setting_id)
        return db_json_response(updated_setting)

    if request.method == "DELETE":
        deleted_setting = SettingModel.delete_setting(setting_id)
        if not deleted_setting.deleted_count > 0:
            raise ValueCustomError("not_found", SETTINGS_RESOURCE)
        return success_json_response(SETTINGS_RESOURCE, "eliminada")
