from flask import Blueprint, request, Response
from flask_jwt_extended import jwt_required, get_jwt

from src.models.user_model import UserModel
from src.services.security_service import delete_active_token, delete_refresh_token
from src.utils.exception_handlers import ValueCustomError
from src.utils.json_responses import success_json_response, db_json_response

USERS_RESOURCE = "usuario"

users_route = Blueprint("users", __name__)


@users_route.route("/", methods=["POST"])
@jwt_required()
def add_user() -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    if token_role != 1:
        raise ValueCustomError("not_auth")
    not_authorized_to_set = (
        "created_at",
        "expires_at",
        "confirmed",
        "auth_provider",
    )
    user_data = request.get_json()
    for field in not_authorized_to_set:
        if field in user_data.keys():
            raise ValueCustomError("not_auth_set", field)
    user_object = UserModel(**user_data)
    user_object.insert_user()
    return success_json_response(USERS_RESOURCE, "añadido", 201)


@users_route.route("/", methods=["GET"])
@jwt_required()
def get_users() -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    if token_role != 1:
        raise ValueCustomError("not_auth")
    page = request.args.get("page", 1)
    per_page = request.args.get("per-page", 10)
    skip = (page - 1) * per_page
    users = UserModel.get_users(skip, per_page)
    return db_json_response(users)


@users_route.route("/<user_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_user(user_id: str) -> tuple[Response, int]:
    token = get_jwt()
    token_user_id = token["sub"]
    token_role = token["role"]
    if not any([token_user_id == user_id, token_role == 1]):
        raise ValueCustomError("not_auth")

    if request.method == "GET":
        user = UserModel.get_user_by_user_id_without_id(user_id)
        if not user:
            raise ValueCustomError("not_found", USERS_RESOURCE)
        return db_json_response(user)

    if request.method == "PUT":
        user = UserModel.get_user_by_user_id_without_id(user_id)
        if not user:
            raise ValueCustomError("not_found", USERS_RESOURCE)
        not_authorized_to_update = (
            "email",
            "created_at",
            "expires_at",
            "confirmed",
            "auth_provider",
            "role",
        )
        user_new_data = request.get_json()
        for field in not_authorized_to_update:
            if field in user_new_data.keys() and user_new_data[field] != user.get(
                field
            ):
                if field == "role" and token_role == 1:
                    continue
                raise ValueCustomError("not_auth_set", field)
        combined_data = {**user, **user_new_data}
        user_object = UserModel(**combined_data)
        updated_user = user_object.update_user(user_id)
        return db_json_response(updated_user)

    if request.method == "DELETE":
        deleted_user = UserModel.delete_user(user_id)
        if not deleted_user.deleted_count > 0:
            raise ValueCustomError("not_found", USERS_RESOURCE)
        delete_active_token(token)
        delete_refresh_token(user_id)
        return success_json_response(USERS_RESOURCE, "eliminado")
