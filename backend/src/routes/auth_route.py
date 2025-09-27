from flask import Blueprint, request, url_for, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt, decode_token
from pymongo.errors import PyMongoError

from src.models.token_model import TokenModel
from src.models.user_model import UserModel
from src.services.email_service import send_email
from src.services.security_service import (
    generate_access_token,
    generate_refresh_token,
    delete_active_token,
    delete_refresh_token,
    google,
    verify_password,
)
from src.utils.exception_handlers import ValueCustomError
from src.utils.json_responses import success_json_response
from src.services.db_service import client

auth_route = Blueprint("auth", __name__)


@auth_route.route("/register", methods=["POST"])
def register() -> tuple[Response, int]:
    session = client.start_session()
    not_authorized_to_set = (
        "created_at",
        "expires_at",
        "confirmed",
        "auth_provider",
        "role",
    )
    user_data = request.get_json()
    for field in not_authorized_to_set:
        if field in user_data.keys():
            raise ValueCustomError("not_auth_set", field)
    user_object = UserModel(**user_data)
    try:
        session.start_transaction()
        new_user = user_object.insert_user(session=session)
        send_email({**user_object.model_dump(), "_id": new_user.inserted_id})
        session.commit_transaction()
        return success_json_response("usuario", "añadido", 201)
    except Exception as e:
        session.abort_transaction()
        raise e
    finally:
        session.end_session()


# Se precisa de un login previo gestionado por el frontend
@auth_route.route("/change-email", methods=["POST"])
@jwt_required()
def change_email() -> tuple[Response, int]:
    user_data = request.get_json()
    user_id = get_jwt().get("sub")
    user_requested = UserModel.get_user_by_user_id_without_id(user_id)
    if not user_requested:
        raise ValueCustomError("not_found", "usuario")
    if user_requested["auth_provider"] == "google":
        user_requested["auth_provider"] = "email"
        user_requested["confirmed"] = False
        if not user_data.get("password"):
            raise ValueCustomError("resource_required", "password")
        user_requested["password"] = user_data["password"]
    user_requested["email"] = user_data["email"]
    user_object = UserModel(**user_requested)
    updated_user = user_object.update_user(user_id)
    send_email(updated_user)
    return success_json_response("email del usuario", "actualizado")


@auth_route.route("/login", methods=["POST"])
def login() -> tuple[Response, int]:
    session = client.start_session()
    user_data = request.get_json()
    user_requested = UserModel.get_user_by_email(user_data.get("email"))
    if not user_requested:
        raise ValueCustomError("not_found", "usuario")
    if not verify_password(user_requested.get("password"), user_data.get("password")):
        raise ValueCustomError("password_not_match")
    if not user_requested.get("confirmed"):
        raise ValueCustomError("email_not_confirmed")
    try:
        session.start_transaction()
        access_token = generate_access_token(user_requested, session)
        refresh_token = generate_refresh_token(user_requested, session)
        session.commit_transaction()
        return (
            jsonify(
                msg=f"Usuario ha iniciado sesión manualmente de forma satisfactoria",
                access_token=access_token,
                refresh_token=refresh_token,
            ),
            200,
        )
    except Exception as e:
        session.abort_transaction()
        raise e
    finally:
        session.end_session()


@auth_route.route("/logout", methods=["POST"])
@jwt_required()
def logout() -> tuple[Response, int]:
    user_id = get_jwt().get("sub")
    delete_active_token(user_id)
    delete_refresh_token(user_id)
    return success_json_response("logout del usuario", "realizado")


@auth_route.route("/login/google")
def login_google() -> tuple[Response, int]:
    redirect_uri = url_for("auth.authorize_google", _external=True)
    return google.authorize_redirect(redirect_uri)


@auth_route.route("/callback/google")
def authorize_google() -> tuple[Response, int]:
    session = client.start_session()
    google_token = google.authorize_access_token()
    nonce = request.args.get("nonce")
    google_user_info = google.parse_id_token(google_token, nonce=nonce)

    user_data = {
        "name": google_user_info.get("name"),
        "email": google_user_info.get("email"),
        "auth_provider": "google",
    }
    user_object = UserModel(**user_data)
    user = user_object.insert_or_update_user_by_email()
    try:
        session.start_transaction()
        access_token = generate_access_token(user, session)
        refresh_token = generate_refresh_token(user, session)
        session.commit_transaction()
        return (
            jsonify(
                {
                    "msg": "El usuario ha iniciado sesión con Google de forma satisfactoria",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                }
            ),
            200,
        )
    except Exception as e:
        session.abort_transaction()
        raise e
    finally:
        session.end_session()


@auth_route.route("/refresh-token")
@jwt_required(refresh=True)
def refresh_user_token():
    user_id = get_jwt().get("sub")
    check_refresh_token = TokenModel.get_refresh_token_by_user_id(user_id)
    if not check_refresh_token:
        raise ValueCustomError("not_found", "refresh token")
    user_data = UserModel.get_user_by_user_id(user_id)
    access_token = generate_access_token(user_data)
    return (
        jsonify(
            access_token=access_token,
            msg="Token de acceso generado de forma satisfactoria",
        ),
        200,
    )


@auth_route.route("/confirm-email/<token>", methods=["GET"])
def confirm_email(token: str) -> tuple[Response, int]:
    session = client.start_session()
    user_identity = decode_token(token)
    user_id = user_identity.get("sub")
    user_requested = UserModel.get_user_by_user_id_without_id(user_id)
    if not user_requested:
        raise ValueCustomError("not_found", "usuario")
    if user_requested["confirmed"]:
        raise ValueCustomError("email_already_confirmed")
    user_requested["confirmed"] = True
    user_object = UserModel(**user_requested)
    try:
        session.start_transaction()
        user_object.update_user(user_id, session=session)
        TokenModel.delete_email_tokens_by_user_id(user_id, session=session)
        session.commit_transaction()
        return success_json_response("usuario", "confirmado")
    except Exception as e:
        session.abort_transaction()
        raise e
    finally:
        session.end_session()


@auth_route.route("/resend-email", methods=["POST"])
def resend_email() -> tuple[Response, int]:
    email = request.get_json().get("email")
    if not email:
        raise ValueCustomError("resource_required", "email")
    user = UserModel.get_user_by_email(email)
    if not user:
        raise ValueCustomError("not_found", "usuario")
    user_tokens = TokenModel.get_email_tokens_by_user_id(user["_id"])
    if not len(user_tokens) < 5:
        raise ValueCustomError("too_many_requests")
    send_email(user)
    return success_json_response("email de confirmación", "reenviado")
