import pytest
from sendgrid import Mail
from flask import Response

from src.services.email_service import send_email
from src.utils.exception_handlers import EmailCustomError
from tests.test_helpers import app
from src.models.token_model import TokenModel

USER_INFO = {
    "name": "Test User",
    "email": "test@example.com",
    "_id": "60d21b4667d0d8992e610c85",
}


def test_send_email(app, mocker):
    with app.app_context():
        token_email = "mocked_token"
        confirmation_link = f"http://localhost:5000/auth/confirm-email/{token_email}"
        email_template = "<html><body>Confirm your email: <a href='{{ confirmation_link }}'>here</a></body></html>"
        data_db = {
            "user_id": USER_INFO["_id"],
            "jti": "bb53e637-8627-457c-840f-6cae52a12e8b",
            "expires_at": 1900757341,
        }
        mock_generate_email_token = mocker.patch(
            "src.services.email_service.generate_email_token",
            return_value=("mocked_token", data_db),
        )

        mock_open_patch = mocker.patch(
            "builtins.open", mocker.mock_open(read_data=email_template)
        )

        mock_sendgrid_client = mocker.patch(
            "src.services.email_service.SendGridAPIClient", autospec=True
        )
        mock_instance = mock_sendgrid_client.return_value
        mock_response = mocker.MagicMock()
        mock_response.status_code = 202
        mock_instance.send.return_value = mock_response
        mock_db = mocker.patch.object(TokenModel, "insert_email_token")

        response = send_email(USER_INFO)

        sent_email = mock_instance.send.call_args[0][0]
        assert isinstance(sent_email, Mail)
        assert sent_email.personalizations[0].tos[0].get("email") == USER_INFO["email"]
        assert sent_email.subject.subject == "Confirmación de Registro La Favorita"
        assert confirmation_link in sent_email.contents[0].content
        assert response.status_code == 202
        mock_generate_email_token.assert_called_once()
        mock_sendgrid_client.assert_called_once()
        mock_open_patch.assert_called_once()
        mock_db.assert_called_once()


def test_send_email_error(app, mocker):
    with app.app_context():
        token_email = "mocked_token"
        confirmation_link = f"http://localhost:5000/auth/confirm-email/{token_email}"
        email_template = "<html><body>Confirm your email: <a href='{{ confirmation_link }}'>here</a></body></html>"
        data_db = {
            "user_id": USER_INFO["_id"],
            "jti": "bb53e637-8627-457c-840f-6cae52a12e8b",
            "expires_at": 1900757341,
        }
        mock_generate_email_token = mocker.patch(
            "src.services.email_service.generate_email_token",
            return_value=("mocked_token", data_db),
        )

        mock_open_patch = mocker.patch(
            "builtins.open", mocker.mock_open(read_data=email_template)
        )

        mock_sendgrid_client = mocker.patch(
            "src.services.email_service.SendGridAPIClient", autospec=True
        )
        mock_instance = mock_sendgrid_client.return_value
        mock_instance.send.side_effect = Exception("SendGrid API error")

        with pytest.raises(EmailCustomError) as error:
            send_email(USER_INFO)

        assert "SendGrid API error" in str(error.value)
        mock_generate_email_token.assert_called_once()
        mock_sendgrid_client.assert_called_once()
        mock_open_patch.assert_called_once()
