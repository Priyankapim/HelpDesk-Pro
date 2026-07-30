from notifications.email_service import send_email


def send_ticket_email(subject, message, recipient):

    html_content = f"""
    <html>
    <body style="font-family: Arial, Helvetica, sans-serif; font-size:15px; color:#333333; line-height:1.7;">
        <p>{message}</p>
    </body>
    </html>
    """

    send_email(
        to_email=recipient,
        subject=subject,
        html_content=html_content,
    )