import pytest
import json

from src.utils.json_responses import success_json_response, db_json_response
from tests.test_helpers import app


def test_resource_msg(app):
    with app.app_context():
        response, status_code = success_json_response("usuario", "añadido", 201)
        assert response.json["msg"] == "Usuario añadido de forma satisfactoria"
        assert status_code == 201


def test_db_json_response(app):
    with app.app_context():
        data = {
            "name": "John Doe",
            "email": "johndoe@doe.com",
            "password": "ValidPass!9",
            "role": 1,
        }
        response, status_code = db_json_response(data)
        assert status_code == 200
        assert json.loads(response.data.decode()) == data
