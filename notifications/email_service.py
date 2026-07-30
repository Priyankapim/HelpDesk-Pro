import os
import requests
from django.conf import settings


def send_email(to_email, subject, html_content):
    """
    Sends email via Brevo's HTTP API instead of SMTP.
    Render blocks outbound SMTP, so this replaces send_mail everywhere.
    Never raises - if it fails, just logs and returns False.
    """

    api_key = os.getenv("BREVO_API_KEY")

    if not api_key:
        print("BREVO_API_KEY not set, skipping email to", to_email)
        return False

    try:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={
                "sender": {
                    "name": "ServiceDesk Pro",
                    "email": settings.DEFAULT_FROM_EMAIL,
                },
                "to": [{"email": to_email}],
                "subject": subject,
                "htmlContent": html_content,
            },
            timeout=8,
        )

        if response.status_code >= 300:
            print("Brevo email failed:", response.status_code, response.text)
            return False

        return True

    except Exception as e:
        print("Email send failed:", e)
        return False