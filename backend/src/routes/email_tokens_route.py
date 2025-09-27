from flask import Blueprint, request, Response
from flask_jwt_extended import jwt_required, get_jwt

from src.models.token_model import TokenModel
from src.utils.exception_handlers import ValueCustomError
from src.utils.json_responses import success_json_response, db_json_response

EMAIL_TOKENS_RESOURCE = "token de email"

email_tokens_route = Blueprint("email_tokens", __name__)


@email_tokens_route.route("/", methods=["POST"])
@jwt_required()
def add_email_token() -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    if token_role != 0:
        raise ValueCustomError("not_auth")
    email_token_data = request.get_json()
    if email_token_data.get("created_at"):
        raise ValueCustomError("not_auth_set", "created_at")
    email_token = TokenModel(**email_token_data)
    email_token.insert_email_token()
    return success_json_response(EMAIL_TOKENS_RESOURCE, "añadido", 201)


@email_tokens_route.route("/", methods=["GET"])
@jwt_required()
def get_email_tokens() -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    if token_role != 0:
        raise ValueCustomError("not_auth")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per-page", 10))
    skip = (page - 1) * per_page
    email_tokens = TokenModel.get_email_tokens(skip, per_page)
    return db_json_response(email_tokens)


@email_tokens_route.route("/<email_token_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_email_token(email_token_id: str) -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    if token_role != 0:
        raise ValueCustomError("not_auth")

    if request.method == "GET":
        email_token = TokenModel.get_email_token(email_token_id)
        if not email_token:
            raise ValueCustomError("not_found", EMAIL_TOKENS_RESOURCE)
        return db_json_response(email_token)

    if request.method == "PUT":
        email_token = TokenModel.get_email_token(email_token_id)
        if not email_token:
            raise ValueCustomError("not_found", EMAIL_TOKENS_RESOURCE)
        email_token_new_data = request.get_json()
        if (
            email_token_new_data.get("created_at")
            and email_token_new_data["created_at"] != email_token["created_at"]
        ):
            raise ValueCustomError("not_auth_set", "created_at")
        mixed_data = {**email_token, **email_token_new_data}
        email_token_object = TokenModel(**mixed_data)
        email_token_updated = email_token_object.update_email_token(email_token_id)
        return db_json_response(email_token_updated)

    if request.method == "DELETE":
        email_token_deleted = TokenModel.delete_email_token(email_token_id)
        if not email_token_deleted.deleted_count > 0:
            raise ValueCustomError("not_found", EMAIL_TOKENS_RESOURCE)
        return success_json_response(EMAIL_TOKENS_RESOURCE, "eliminado")
