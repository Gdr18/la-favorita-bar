from sendgrid import SendGridAPIClient, Mail
from flask import Response, jsonify

from config import email_confirmation_link, SENDGRID_API_KEY, DEFAULT_SENDER_EMAIL
from src.services.security_service import generate_email_token
from src.models.token_model import TokenModel
from src.utils.exception_handlers import EmailCustomError


def send_email(user_info: dict) -> Response:
    token_email, token_data_db = generate_email_token(user_info)
    user_name = user_info.get("name")
    user_email = user_info.get("email")
    confirmation_link = email_confirmation_link + token_email
    with open("src/templates/email_template.html", encoding="utf-8") as file:
        email_template = file.read()
        email_template = email_template.replace(
            "{{ confirmation_link }}", confirmation_link
        ).replace("{{ user_name }}", user_name)
    email = Mail(
        from_email=DEFAULT_SENDER_EMAIL,
        to_emails=user_email,
        subject="Confirmación de Registro La Favorita",
        html_content=email_template,
    )
    try:
        sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)
        response = sg.send(email)
    except Exception as e:
        raise EmailCustomError(e)
    else:
        TokenModel(**token_data_db).insert_email_token()
        return response
