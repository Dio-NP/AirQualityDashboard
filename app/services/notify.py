from __future__ import annotations
import os
from config import settings


def send_email(to_email: str, subject: str, body: str) -> None:
    api_key = os.getenv("SENDGRID_API_KEY")
    sender = os.getenv("EMAIL_FROM", "no-reply@example.com")
    if not api_key:
        raise RuntimeError("SENDGRID_API_KEY not set")
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
    except Exception as e:
        raise RuntimeError("sendgrid not installed") from e
    message = Mail(from_email=sender, to_emails=to_email, subject=subject, html_content=body)
    sg = SendGridAPIClient(api_key)
    sg.send(message)


def send_sms(to_phone: str, body: str) -> None:
    sid = os.getenv("TWILIO_SID")
    token = os.getenv("TWILIO_TOKEN")
    from_number = os.getenv("TWILIO_FROM")
    if not (sid and token and from_number):
        raise RuntimeError("Twilio credentials not set")
    try:
        from twilio.rest import Client
    except Exception as e:
        raise RuntimeError("twilio not installed") from e
    client = Client(sid, token)
    client.messages.create(to=to_phone, from_=from_number, body=body)
