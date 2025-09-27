from flask import Blueprint, request, Response
from flask_jwt_extended import jwt_required, get_jwt

from src.models.token_model import TokenModel
from src.utils.exception_handlers import ValueCustomError
from src.utils.json_responses import success_json_response, db_json_response

ACTIVE_TOKENS_RESOURCE = "token activo"

active_tokens_route = Blueprint("active_tokens", __name__)


@active_tokens_route.route("/", methods=["POST"])
@jwt_required()
def add_active_token() -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    if not token_role == 0:
        raise ValueCustomError("not_auth")
    active_token_data = request.get_json()
    if active_token_data.get("created_at"):
        raise ValueCustomError("not_auth_set", "created_at")
    active_token = TokenModel(**active_token_data)
    active_token.insert_active_token()
    return success_json_response(ACTIVE_TOKENS_RESOURCE, "añadido", 201)


@active_tokens_route.route("/", methods=["GET"])
@jwt_required()
def get_active_tokens() -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    if not token_role == 0:
        raise ValueCustomError("not_auth")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per-page", 10))
    skip = (page - 1) * per_page
    active_tokens = TokenModel.get_active_tokens(skip, per_page)
    return db_json_response(active_tokens)


@active_tokens_route.route("/<active_token_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_active_token(active_token_id: str) -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    if not token_role == 0:
        raise ValueCustomError("not_auth")

    if request.method == "GET":
        active_token = TokenModel.get_active_token_by_token_id(active_token_id)
        if not active_token:
            raise ValueCustomError("not_found", ACTIVE_TOKENS_RESOURCE)
        return db_json_response(active_token)

    if request.method == "PUT":
        active_token = TokenModel.get_active_token_by_token_id(active_token_id)
        if not active_token:
            raise ValueCustomError("not_found", ACTIVE_TOKENS_RESOURCE)
        active_token_new_data = request.get_json()
        if (
            active_token_new_data.get("created_at")
            and active_token_new_data["created_at"] != active_token["created_at"]
        ):
            raise ValueCustomError("not_auth_set", "created_at")
        mixed_data = {**active_token, **active_token_new_data}
        active_token_object = TokenModel(**mixed_data)
        active_token_updated = active_token_object.update_active_token(active_token_id)
        return db_json_response(active_token_updated)

    if request.method == "DELETE":
        active_token_deleted = TokenModel.delete_active_token_by_token_id(
            active_token_id
        )
        if not active_token_deleted.deleted_count > 0:
            raise ValueCustomError("not_found", ACTIVE_TOKENS_RESOURCE)
        return success_json_response(ACTIVE_TOKENS_RESOURCE, "eliminado")
