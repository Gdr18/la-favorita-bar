from flask import Blueprint, request, Response
from flask_jwt_extended import jwt_required, get_jwt

from src.models.token_model import TokenModel
from src.utils.exception_handlers import ValueCustomError
from src.utils.json_responses import success_json_response, db_json_response

REFRESH_TOKENS_RESOURCE = "token de refresco"

refresh_tokens_route = Blueprint("refresh_tokens", __name__)


@refresh_tokens_route.route("/", methods=["POST"])
@jwt_required()
def add_refresh_token() -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    if token_role != 0:
        raise ValueCustomError("not_auth")
    token_data = request.get_json()
    if token_data.get("created_at"):
        raise ValueCustomError("not_auth_set", "created_at")
    refresh_token = TokenModel(**token_data)
    refresh_token.insert_refresh_token()
    return success_json_response(REFRESH_TOKENS_RESOURCE, "añadido", 201)


@refresh_tokens_route.route("/", methods=["GET"])
@jwt_required()
def get_refresh_tokens() -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    if token_role != 0:
        raise ValueCustomError("not_auth")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per-page", 10))
    skip = (page - 1) * per_page
    refresh_tokens = TokenModel.get_refresh_tokens(skip, per_page)
    return db_json_response(refresh_tokens)


@refresh_tokens_route.route("/<refresh_token_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_refresh_token(refresh_token_id: str) -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    if token_role != 0:
        raise ValueCustomError("not_auth")

    if request.method == "GET":
        refresh_token = TokenModel.get_refresh_token_by_token_id(refresh_token_id)
        if not refresh_token:
            raise ValueCustomError("not_found", REFRESH_TOKENS_RESOURCE)
        return db_json_response(refresh_token)

    if request.method == "PUT":
        refresh_token = TokenModel.get_refresh_token_by_token_id(refresh_token_id)
        if not refresh_token:
            raise ValueCustomError("not_found", REFRESH_TOKENS_RESOURCE)
        token_new_data = request.get_json()
        if (
            token_new_data.get("created_at")
            and token_new_data["created_at"] != refresh_token["created_at"]
        ):
            raise ValueCustomError("not_auth_set", "created_at")
        mixed_data = {**refresh_token, **token_new_data}
        refresh_token_object = TokenModel(**mixed_data)
        refresh_token_updated = refresh_token_object.update_refresh_token(
            refresh_token_id
        )
        return db_json_response(refresh_token_updated)

    if request.method == "DELETE":
        refresh_token_deleted = TokenModel.delete_refresh_token_by_token_id(
            refresh_token_id
        )
        if not refresh_token_deleted.deleted_count > 0:
            raise ValueCustomError("not_found", REFRESH_TOKENS_RESOURCE)
        return success_json_response(REFRESH_TOKENS_RESOURCE, "eliminado")
