from datetime import timedelta, datetime
from typing import Union

from authlib.integrations.flask_client import OAuth
from flask import jsonify, Response
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    JWTManager,
    decode_token,
)
from pymongo.results import InsertOneResult, DeleteResult

from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, config
from src.models.token_model import TokenModel

bcrypt = Bcrypt()

jwt = JWTManager()
oauth = OAuth()

google = oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


def verify_password(db_password: str, password: str) -> bool:
    return bcrypt.check_password_hash(db_password, password)


def verify_google_identity(
    google_token: str, user_email: str
) -> Union[bool, Exception]:
    token_info = google.parse_id_token(google_token)
    return token_info["email"] == user_email


def generate_access_token(user_data: dict, session=None) -> str:
    user_role = user_data.get("role")
    user_identity = user_data.get("_id")
    token_info = {
        "identity": str(user_identity),
        "additional_claims": {"role": user_role},
        "expires_delta": get_expiration_time_access_token(user_role),
    }
    access_token = create_access_token(**token_info)

    access_token_decoded = decode_token(access_token)
    data_access_token = {
        "user_id": access_token_decoded.get("sub"),
        "jti": access_token_decoded.get("jti"),
        "expires_at": access_token_decoded.get("exp"),
        "created_at": datetime.now(),
    }
    TokenModel(**data_access_token).update_or_insert_active_token_by_user_id(
        data_access_token["user_id"], session
    )
    return access_token


def generate_refresh_token(
    user_data: dict, session
) -> Union[str, tuple[Response, int]]:
    user_role = user_data.get("role")
    user_identity = user_data.get("_id")
    token_info = {
        "identity": str(user_identity),
        "expires_delta": get_expiration_time_refresh_token(user_role),
    }
    refresh_token = create_refresh_token(**token_info)

    refresh_token_decoded = decode_token(refresh_token)
    data_refresh_token = {
        "user_id": refresh_token_decoded.get("sub"),
        "jti": refresh_token_decoded.get("jti"),
        "expires_at": refresh_token_decoded.get("exp"),
        "created_at": datetime.now(),
    }
    TokenModel(**data_refresh_token).update_or_insert_refresh_token_by_user_id(
        data_refresh_token["user_id"], session
    )
    return refresh_token


def generate_email_token(user_data: dict) -> tuple:
    user_identity = user_data.get("_id")
    token_info = {"identity": str(user_identity), "expires_delta": timedelta(days=1)}
    email_token = create_access_token(**token_info)
    decoded_token_email = decode_token(email_token)
    data_email_token_db = {
        "user_id": decoded_token_email.get("sub"),
        "jti": decoded_token_email.get("jti"),
        "expires_at": decoded_token_email.get("exp"),
    }
    return email_token, data_email_token_db


def get_expiration_time_access_token(role: int) -> timedelta:
    if role == 1:
        return timedelta(minutes=15)
    elif role == 2:
        return timedelta(hours=3)
    else:
        return timedelta(days=1)


def get_expiration_time_refresh_token(role: int) -> timedelta:
    if role == 1:
        return timedelta(hours=3)
    elif role == 2:
        return timedelta(hours=6)
    else:
        return timedelta(days=30)


def delete_active_token(user_id: str) -> DeleteResult:
    deleted_active_token = TokenModel.delete_active_token_by_user_id(user_id)
    return deleted_active_token


def delete_refresh_token(user_id: str) -> DeleteResult:
    deleted_refresh_token = TokenModel.delete_refresh_token_by_user_id(user_id)
    return deleted_refresh_token


@jwt.token_in_blocklist_loader
def check_if_token_active_callback(
    jwt_header: dict, jwt_payload: dict
) -> Union[bool, None]:
    if config == "config.DevelopmentConfig":
        return False
    check_token = TokenModel.get_active_token_by_user_id(jwt_payload["sub"])
    return True if not check_token else False


@jwt.revoked_token_loader
def revoked_token_callback(jwt_header: dict, jwt_payload: dict) -> tuple[Response, int]:
    return jsonify(err="revoked_token", msg="El token ha sido revocado"), 401


@jwt.expired_token_loader
def expired_token_callback(jwt_header: dict, wt_payload: dict) -> tuple[Response, int]:
    return jsonify(err="expired_token", msg="El token ha expirado"), 401


@jwt.unauthorized_loader
def unauthorized_callback(error_message: str) -> tuple[Response, int]:
    return (
        jsonify(
            err="invalid_token", msg="Necesita un token válido para acceder a esta ruta"
        ),
        401,
    )
