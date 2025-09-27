import pytest
from pymongo.errors import PyMongoError, DuplicateKeyError, ConnectionFailure
from bson.errors import InvalidId
from pydantic import ValidationError
from sendgrid import SendGridException
from flask import abort

from src.utils.exception_handlers import (
    ValueCustomError,
    handle_custom_value_error,
    handle_field_required_error,
    handle_length_value_error,
    handle_extra_inputs_forbidden_error,
    handle_value_type_error,
    handle_literal_value_error,
    handle_pattern_value_error,
    handle_mongodb_exception,
    EmailCustomError,
)
from src.models.token_model import TokenModel
from tests.test_helpers import app

MONGODB_ERRORS = {
    "duplicate_key": DuplicateKeyError(
        "Duplicate key error", 11000, {"keyValue": "value"}
    ),
    "connection_failure": ConnectionFailure("Connection failed"),
    "generic_error": PyMongoError("Generic error"),
}
VALUE_CUSTOM_ERRORS = {
    "value_custom1": {"error_type": "not_found", "resource": "usuario"},
    "value_custom2": {"error_type": "password_not_match", "resource": None},
    "value_custom3": {"error_type": "email_not_confirmed", "resource": None},
    "value_custom4": {"error_type": "too_many_requests", "resource": None},
    "value_custom5": {"error_type": "not_auth", "resource": None},
    "value_custom6": {"error_type": "not_auth_set", "resource": "role"},
    "value_custom7": {"error_type": "email_already_confirmed", "resource": None},
    "value_custom8": {"error_type": "resource_required", "resource": "resource1"},
    "value_custom9": {"error_type": "bar_closed_manually", "resource": None},
    "value_custom10": {"error_type": "bar_closed_schedule", "resource": None},
}
VALUE_TYPE_ERRORS = {
    "value_type1": [{"loc": ["field1"], "type": "int_"}],
    "value_type2": [{"loc": ["field1", 0], "type": "int_"}],
    "value_type3": [{"loc": ["field1", 0, "field2"], "type": "int_"}],
    "value_type4": [{"loc": ["field1", 0, "field2", 0, "field3"], "type": "int_"}],
}
LENGTH_VALUE_ERRORS = {
    "too_short": [{"loc": ["field1"], "type": "too_short", "ctx": {"min_length": 7}}],
    "too_long": [{"loc": ["field1"], "type": "too_long", "ctx": {"max_length": 5}}],
}
LITERAL_VALUE_ERROR = [
    {"loc": ["field1"], "ctx": {"expected": "main, starter or dessert"}}
]
EXTRA_INPUT_AND_FIELD_REQUIRED_ERRORS = [
    {"loc": ["field1"]},
    {"loc": ["field2"]},
]
PATTERN_ERROR = [{"loc": ["field1"]}]


@pytest.mark.parametrize(
    "error_type, expected_message",
    [
        (
            "sender identity",
            "El remitente del correo no está verificado. Revisa tu configuración en SendGrid.",
        ),
        ("to field is required", "Falta el destinatario del correo."),
        (
            "permission denied",
            "Permisos insuficientes. Verifica tu API key o autenticación.",
        ),
        (
            "invalid email address",
            "La dirección de correo electrónico no es válida.",
        ),
        ("unauthorized", "No estás autorizado. Revisa tu clave API de SendGrid."),
        ("api key", "No estás autorizado. Revisa tu clave API de SendGrid."),
        ("403", "Acceso denegado por SendGrid (403 Forbidden)."),
        ("401", "No autorizado (401). Verifica tu clave API o autenticación."),
        ("timeout", "Tiempo de espera agotado al conectar con SendGrid."),
        ("unexpected", "Error desconocido al enviar el correo con SendGrid."),
    ],
)
def test_email_custom_error(app, error_type, expected_message):
    with app.app_context():
        err = EmailCustomError(Exception(error_type))
        response, status_code = err.response

        assert response.json["msg"] == expected_message


@pytest.mark.parametrize(
    "function, arguments, code, error",
    [
        (
            ValueCustomError,
            VALUE_CUSTOM_ERRORS["value_custom1"],
            404,
            "not_found",
        ),
        (
            ValueCustomError,
            VALUE_CUSTOM_ERRORS["value_custom2"],
            401,
            "password_not_match",
        ),
        (
            ValueCustomError,
            VALUE_CUSTOM_ERRORS["value_custom3"],
            401,
            "email_not_confirmed",
        ),
        (
            ValueCustomError,
            VALUE_CUSTOM_ERRORS["value_custom4"],
            429,
            "too_many_requests",
        ),
        (
            ValueCustomError,
            VALUE_CUSTOM_ERRORS["value_custom5"],
            403,
            "not_auth",
        ),
        (
            ValueCustomError,
            VALUE_CUSTOM_ERRORS["value_custom6"],
            403,
            "not_auth_set",
        ),
        (
            ValueCustomError,
            VALUE_CUSTOM_ERRORS["value_custom7"],
            401,
            "email_already_confirmed",
        ),
        (
            ValueCustomError,
            VALUE_CUSTOM_ERRORS["value_custom8"],
            400,
            "resource_required",
        ),
        (
            ValueCustomError,
            VALUE_CUSTOM_ERRORS["value_custom9"],
            503,
            "bar_closed_manually",
        ),
        (
            ValueCustomError,
            VALUE_CUSTOM_ERRORS["value_custom10"],
            503,
            "bar_closed_schedule",
        ),
        (
            handle_extra_inputs_forbidden_error,
            EXTRA_INPUT_AND_FIELD_REQUIRED_ERRORS,
            400,
            "extra_input",
        ),
        (
            handle_field_required_error,
            EXTRA_INPUT_AND_FIELD_REQUIRED_ERRORS,
            400,
            "field_required",
        ),
        (
            handle_length_value_error,
            LENGTH_VALUE_ERRORS["too_short"],
            400,
            "length_value",
        ),
        (
            handle_length_value_error,
            LENGTH_VALUE_ERRORS["too_long"],
            400,
            "length_value",
        ),
        (
            handle_literal_value_error,
            LITERAL_VALUE_ERROR,
            400,
            "literal_value",
        ),
        (
            handle_pattern_value_error,
            PATTERN_ERROR,
            400,
            "pattern_value",
        ),
        (
            handle_custom_value_error,
            [{"msg": ", El ingrediente 'garbanzo' no existe"}],
            400,
            "custom_value",
        ),
        (
            handle_value_type_error,
            VALUE_TYPE_ERRORS["value_type1"],
            400,
            "value_type",
        ),
        (
            handle_value_type_error,
            VALUE_TYPE_ERRORS["value_type2"],
            400,
            "value_type",
        ),
        (
            handle_value_type_error,
            VALUE_TYPE_ERRORS["value_type3"],
            400,
            "value_type",
        ),
        (
            handle_value_type_error,
            VALUE_TYPE_ERRORS["value_type4"],
            400,
            "value_type",
        ),
        (
            handle_mongodb_exception,
            MONGODB_ERRORS["duplicate_key"],
            409,
            "db_duplicate_key",
        ),
        (
            handle_mongodb_exception,
            MONGODB_ERRORS["connection_failure"],
            500,
            "db_connection",
        ),
        (
            handle_mongodb_exception,
            MONGODB_ERRORS["generic_error"],
            500,
            "db_generic",
        ),
    ],
)
def test_exceptions_handlers(app, function, arguments, code, error):
    with app.app_context():
        err = (
            function(**arguments)
            if function == ValueCustomError
            else function(arguments)
        )

        response, status_code = err.response if function == ValueCustomError else err

        assert status_code == code
        assert response.json["err"] == error


def test_mongodb_error_flask_handler(app):
    with app.test_client() as client:

        @app.route("/mongodb-error")
        def trigger_mongodb_error():
            raise PyMongoError("Error de conexión")

        response = client.get("/mongodb-error")
        assert response.status_code == 500
        assert response.json["err"] == "db_generic"


def test_mongodb_error_invalid_id_flask_handler(app):
    with app.test_client() as client:

        @app.route("/mongodb-error-invalid-id")
        def trigger_mongodb_error_invalid_id():
            raise InvalidId("Invalid ObjectId")

        response = client.get("/mongodb-error-invalid-id")
        assert response.status_code == 400
        assert response.json["err"] == "db_invalid_id"


def test_captured_validation_error_flask_handler(app):
    with app.test_client() as client:

        @app.route("/validation-error")
        def trigger_validation_error():
            TokenModel(
                user_id="507f1f77bcf86cd79943901133",
                jti="bb53e637dd-8627-457c-840f-6cae52a12e8b",
                expires_at=1729684113900,
            )

        response = client.get("/validation-error")

        assert response.status_code == 400
        assert response.json["err"] == "pattern_value"


def test_non_captured_validation_error_flask_handler(app, mocker):
    with app.test_client() as client:
        fake_errors = [
            {"type": "bool_parsing", "msg": "Error desconocido", "loc": ["field"]},
            {"type": "bool_parsing", "msg": "Error desconocido", "loc": ["field"]},
        ]

        validation_error = ValidationError.from_exception_data(TokenModel, fake_errors)
        mocker.patch.object(validation_error, "errors", return_value=fake_errors)

        @app.route("/validation-error")
        def trigger_validation_error():
            raise validation_error

        response = client.get("/validation-error")

        assert response.status_code == 400
        assert response.json["err"] == "validation"


def test_value_custom_error_flask_handler(app):
    with app.test_client() as client:

        @app.route("/value-custom-error")
        def trigger_value_custom_error():
            raise ValueCustomError("not_found", "usuario")

        response = client.get("/value-custom-error")
        assert response.status_code == 404
        assert response.json["err"] == "not_found"


def test_email_custom_error_flask_handler(app):
    with app.test_client() as client:

        @app.route("/email-custom-error")
        def trigger_email_custom_error():
            raise EmailCustomError(Exception("unexpected"))

        response = client.get("/email-custom-error")
        assert response.status_code == 500
        assert response.json["err"] == "send_email"


def test_not_found_error(app):
    with app.test_client() as client:
        with pytest.raises(ValueCustomError) as error:
            client.get("/resource-not-found")
        assert error.value.args == ("not_found", "recurso")


def test_generic_error_flask_handler(app):
    with app.test_client() as client:

        @app.route("/generic-error")
        def trigger_generic_error():
            raise Exception("Error inesperado")

        response = client.get("/generic-error")
        assert response.status_code == 500
        assert response.json["err"] == "unexpected"
